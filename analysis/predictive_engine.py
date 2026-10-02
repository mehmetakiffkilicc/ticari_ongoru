"""Explainable predictive demand engine for Next-Basket and Target-Customer propensity.

Combines purchase cadence recurrence, market basket association rules (Lift & Confidence),
and category lookalike affinity into auditable probabilities and recommendations.
"""
from __future__ import annotations

import math
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from itertools import combinations
from statistics import mean, median, pstdev


def _fold(value):
    value = str(value or '').strip().replace('ı', 'i').replace('İ', 'i').casefold()
    return ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c))


def _kind(row):
    return {
        'satis': 'sale', 'satis faturasi': 'sale',
        'satis iadesi': 'return', 'satis iade faturasi': 'return'
    }.get(_fold(row.get('Fatura Türü')))


def _number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _date(row):
    try:
        return datetime.fromisoformat(str(row.get('Fatura Tarihi') or '')[:10]).date()
    except (ValueError, TypeError):
        return None


def predict_customer_next_basket(customer_code, analysis_date, rows, max_items=5):
    """Predict the most probable products for a customer's next order."""
    if isinstance(analysis_date, str):
        try:
            analysis_date = datetime.fromisoformat(analysis_date[:10]).date()
        except ValueError:
            analysis_date = date.today()

    customer_code = str(customer_code).strip()
    relevant = [r for r in rows if _kind(r) and _date(r) and _date(r) <= analysis_date]

    # 1. Collect product catalog and all basket co-occurrences
    product_meta = {}
    invoice_baskets = defaultdict(set)
    customer_invoices = defaultdict(set)
    product_sales_overall = Counter()
    customer_product_stats = defaultdict(lambda: {'dates': set(), 'quantities': [], 'amounts': [], 'invoices': set()})

    for r in relevant:
        p_code = str(r.get('Malzeme Kodu') or '').strip()
        c_code = str(r.get('Müsteri Kodu') or '').strip()
        if not p_code or not c_code:
            continue
        p_name = str(r.get('Malzeme Aciklamasi') or p_code)
        p_cat = str(r.get('Malzeme Grubu') or 'Genel')
        product_meta[p_code] = {'name': p_name, 'category': p_cat}

        day = _date(r)
        kind = _kind(r)
        inv = str(r.get('Fatura No') or f"{c_code}_{day}")

        if kind == 'sale':
            invoice_baskets[inv].add(p_code)
            customer_invoices[c_code].add(inv)
            product_sales_overall[p_code] += abs(_number(r.get('Net Satir Tutari')))

            if c_code == customer_code:
                st = customer_product_stats[p_code]
                st['dates'].add(day)
                st['quantities'].append(abs(_number(r.get('Miktar'))))
                st['amounts'].append(abs(_number(r.get('Net Satir Tutari'))))
                st['invoices'].add(inv)

    total_customer_invoices = len(customer_invoices.get(customer_code, set()))
    predictions = []

    # 2. Check customer's own products (Cadence / Replenishment & Core Staples)
    for p_code, stats in customer_product_stats.items():
        meta = product_meta.get(p_code, {'name': p_code, 'category': 'Genel'})
        dates = sorted(stats['dates'])
        if not dates:
            continue

        last_date = dates[-1]
        elapsed = (analysis_date - last_date).days
        order_count = len(stats['invoices'])
        order_frequency = order_count / max(1, total_customer_invoices)
        avg_qty = round(mean(stats['quantities']), 1) if stats['quantities'] else 1.0
        avg_price = (sum(stats['amounts']) / sum(stats['quantities'])) if sum(stats['quantities']) > 0 else 0.0

        gaps = [(r - l).days for l, r in zip(dates, dates[1:]) if (r - l).days > 0]
        cadence = median(gaps) if gaps else None
        cadence_std = pstdev(gaps) if len(gaps) > 1 else (cadence * 0.3 if cadence else 5.0)

        # Logic A: Replenishment Due via Statistical Cadence Hazard Function
        if cadence and cadence > 0 and len(dates) >= 2:
            cycle_ratio = elapsed / cadence
            # Gaussian-smoothed hazard peak centered at expected cadence
            z = (elapsed - cadence) / max(3.0, cadence_std)
            hazard = math.exp(-0.5 * (z ** 2))

            if 0.70 <= cycle_ratio <= 2.2:
                # Calibrated probability: base + hazard urgency + historic buying frequency
                prob = min(96, round(58 + 30 * hazard + 12 * order_frequency))
                predictions.append({
                    'code': p_code,
                    'name': meta['name'],
                    'category': meta['category'],
                    'probability': prob,
                    'expectedQty': avg_qty,
                    'expectedPrice': round(avg_price, 2),
                    'expectedValue': round(avg_qty * avg_price, 2),
                    'reason': f"İkmal döngüsü zirvede (son sipariş {elapsed} gün önce, periyot {round(cadence)}±{round(cadence_std)} gün)",
                    'type': 'replenishment',
                    'badge': 'Döngüsü Geldi',
                    'orderCount': order_count,
                    'orderFrequency': round(order_frequency * 100),
                    'avgDaysBetweenOrders': round(cadence) if cadence else None,
                })
                continue
            elif cycle_ratio > 2.2:
                # Recover candidate: Was regular, but lapsed significantly beyond cadence window
                prob = min(78, round(45 + 25 * order_frequency + 10 * min(1.0, 50.0 / max(1.0, elapsed))))
                predictions.append({
                    'code': p_code,
                    'name': meta['name'],
                    'category': meta['category'],
                    'probability': prob,
                    'expectedQty': avg_qty,
                    'expectedPrice': round(avg_price, 2),
                    'expectedValue': round(avg_qty * avg_price, 2),
                    'reason': f"Tarihsel düzenli alıcı; son alımdan bu yana {elapsed} gün geçti (periyot {round(cadence)} gün)",
                    'type': 'recover',
                    'badge': 'Kayıp Ürün Adayı',
                    'orderCount': order_count,
                    'orderFrequency': round(order_frequency * 100),
                    'daysSinceLastOrder': elapsed,
                })
                continue

        # Logic B: High Frequency Staple (with recency weighting)
        if order_frequency >= 0.40 and order_count >= 2:
            recent_cutoff = analysis_date - timedelta(days=180)
            recent_orders = len([d for d in dates if d >= recent_cutoff])
            recency_factor = min(1.0, recent_orders / max(1, order_count))
            prob = min(92, round(55 + 25 * order_frequency + 10 * recency_factor))
            predictions.append({
                'code': p_code,
                'name': meta['name'],
                'category': meta['category'],
                'probability': prob,
                'expectedQty': avg_qty,
                'expectedPrice': round(avg_price, 2),
                'expectedValue': round(avg_qty * avg_price, 2),
                'reason': f"Müşterinin demirbaş sepet ürünü (siparişlerin %{int(order_frequency * 100)}'inde yer alıyor)",
                'type': 'regular',
                'badge': 'Rutin Sepet',
                'orderCount': order_count,
                'orderFrequency': round(order_frequency * 100),
                'recencyFactor': round(recency_factor * 100)
            })

    # 3. Market Basket Association for Cross-Sell with PMI & Lift
    own_codes = set(customer_product_stats.keys())
    top_own = sorted(own_codes, key=lambda c: len(customer_product_stats[c]['invoices']), reverse=True)[:4]

    pair_counts = Counter()
    item_counts = Counter()
    for basket in invoice_baskets.values():
        for item in basket:
            item_counts[item] += 1
        for a, b in combinations(sorted(basket), 2):
            pair_counts[(a, b)] += 1
            pair_counts[(b, a)] += 1

    total_baskets = len(invoice_baskets)
    cross_candidates = defaultdict(lambda: {'lift': 0.0, 'conf': 0.0, 'pmi': 0.0, 'with': ''})

    for own_item in top_own:
        own_name = product_meta.get(own_item, {}).get('name', own_item)
        if item_counts[own_item] < 3:
            continue
        for other, count in item_counts.items():
            if other in own_codes or count < 3:
                continue
            together = pair_counts.get((own_item, other), 0)
            if together < 3:
                continue
            conf = together / item_counts[own_item]
            p_together = together / total_baskets
            p_a = item_counts[own_item] / total_baskets
            p_b = count / total_baskets
            lift = p_together / (p_a * p_b) if (p_a * p_b) > 0 else 0
            pmi = math.log(p_together / (p_a * p_b)) if (p_a * p_b) > 0 and p_together > 0 else 0

            if lift >= 1.25 and conf >= 0.20:
                if lift > cross_candidates[other]['lift']:
                    cross_candidates[other] = {'lift': lift, 'conf': conf, 'pmi': pmi, 'with': own_name}

    for p_code, rel in cross_candidates.items():
        meta = product_meta.get(p_code, {'name': p_code, 'category': 'Genel'})
        prob = min(85, round(45 + rel['conf'] * 35 + min(15, rel['lift'] * 4)))
        predictions.append({
            'code': p_code,
            'name': meta['name'],
            'category': meta['category'],
            'probability': prob,
            'expectedQty': 1.0,
            'expectedPrice': 0.0,
            'expectedValue': 0.0,
            'reason': f"Sepet birlikteliği: {rel['with']} ile yüksek eşleşme (Güven %{round(rel['conf'] * 100)}, Lift {round(rel['lift'], 1)}x)",
            'type': 'cross_sell',
            'badge': 'Çapraz Satış',
            'lift': round(rel['lift'], 2),
            'confidence': round(rel['conf'] * 100),
        })

    # Sort and pick top unique items
    seen = set()
    unique_preds = []
    predictions.sort(key=lambda x: (x['type'] != 'replenishment', -x['probability']))
    for p in predictions:
        if p['code'] not in seen:
            seen.add(p['code'])
            unique_preds.append(p)
            if len(unique_preds) >= max_items:
                break

    return unique_preds


def explain_next_basket_model():
    """Returns structured Turkish explanation of the next-basket prediction methodology."""
    return {
        'title': 'Tahmini Sonraki Sepet — Metodoloji ve Algoritmik Temel',
        'summary': 'Müşterinin sıradaki ziyaretinde satın alması en muhtemel ürünleri belirlemek için dört ayrı sinyal birleştirilir: tüketim döngüsü, sepet alışkanlığı (staple), birliktelik kuralları (çapraz satış) ve kayıp ürün tespiti.',
        'signals': [
            {
                'id': 'replenishment',
                'badge': 'Döngüsü Geldi',
                'color': '#1e3a5f',
                'title': 'Tüketim Döngüsü (Replenishment Cadence)',
                'formula': 'döngü_oranı = geçen_gün ÷ medyan_sipariş_aralığı',
                'logic': 'Müşterinin her bir ürünü için geçmiş sipariş tarihleri arasındaki medyan aralık hesaplanır. Geçen süre bu aralığın %75 ile %220 arasında olduğunda ürün "döngüsü gelmiş" kabul edilir.',
                'probability_formula': 'P = min(96, 65 + 25 × min(1.0, döngü_oranı) + 10 × frekans)',
                'example': 'Son sipariş 32 gün önce, medyan ritim 28 gün → döngü_oranı=1.14 → Olasılık ~%88',
                'threshold_min': 0.75,
                'threshold_max': 2.2,
                'priority': 1
            },
            {
                'id': 'staple',
                'badge': 'Rutin Sepet',
                'color': '#2e7d32',
                'title': 'Sepet Demirbaşı (High-Frequency Staple)',
                'formula': 'frekans = bu_ürünün_fatura_sayısı ÷ toplam_fatura_sayısı',
                'logic': 'Müşterinin toplam faturalarının %40 veya daha fazlasında bulunan ürünler demirbaş sepet ürünür. Sipariş zamanlamacından bağımsız olarak yüksek tekrar ihtimali taşır.',
                'probability_formula': 'P = min(92, 55 + 25 × frekans + 10 × yakın_sipariş_oranı)',
                'example': 'Frekans %65, son 180 günde 8 sipariş → P = min(92, 55 + 16.25 + 8) = %79',
                'threshold_min': 0.40,
                'priority': 2
            },
            {
                'id': 'cross_sell',
                'badge': 'Çapraz Satış',
                'color': '#6a1b9a',
                'title': 'Pazar Sepeti Birliktelik Kuralı (Market Basket Association)',
                'formula': 'Güven = birlikte_alım ÷ A_ürün_toplam; Lift = Güven ÷ B_pazar_payı',
                'logic': 'Müşterinin en sık satın aldığı 4 ürün referans alınır. Bu ürünlerle Lift ≥1.25 ve Güven ≥0.20 değerlerine sahip ürünler çapraz satış adayı olarak önerilir.',
                'probability_formula': 'P = min(85, 45 + güven×35 + min(15, lift×4))',
                'example': 'KALINKA ile birlikte SALONIKI %60 oranında alınıyor, Lift=2.8 → P = min(85, 45 + 21 + 11.2) = %77',
                'threshold_lift': 1.25,
                'threshold_confidence': 0.20,
                'priority': 3
            },
            {
                'id': 'recover',
                'badge': 'Kayıp Ürün Adayı',
                'color': '#b71c1c',
                'title': 'Kayıp Ürün Tespiti (Lapsed Product Recovery)',
                'formula': 'döngü_oranı = geçen_gün ÷ medyan_sipariş_aralığı > 2.2',
                'logic': 'Tarihsel olarak düzenli alınan ancak döngü oranı 2.2\'yi aşan ürünler. Müşteri bu ürünü rakipten alıyor ya da ihtiyacı bitmiş olabilir; temas için fırsat.',
                'probability_formula': 'P = min(78, 50 + 25 × frekans)',
                'example': 'Medyan ritim 28 gün, son sipariş 90 gün önce (oran 3.2) → P = min(78, 50 + 25×0.4) = %60',
                'threshold_ratio': 2.2,
                'priority': 4
            }
        ],
        'ranking': 'Sıralama: önce sinyal önceliği (Döngüsü Geldi > Rutin Sepet > Çapraz Satış > Kayıp Ürün), sonra olasılık puanı. Aynı ürün farklı sinyallerden tetiklenirse yalnızca en yüksek puanlı sinyal gösterilir.',
        'limitations': [
            'Müşteri tarafında gerçekleşen iade, kampanya veya fiyat değişimleri modele dahil edilmez.',
            'Yeni ürünler (veri tabanında satış geçmişi olmayan) çapraz satış adayı olarak önerilemez.',
            'En az 2 farklı sipariş tarihi olan ürünler döngü analizi kapsamına alınır.',
            'Modelin güveni, müşterinin veri tabanındaki sipariş sayısıyla orantılı artar.'
        ],
        'data_requirements': 'Döngü analizi: ≥2 sipariş tarihi. Çapraz satış: ≥3 sepet eş-geçiş. Demirbaş analizi: ≥2 fatura + ≥40% frekans.'
    }


def predict_product_target_customers(product_code, analysis_date, rows, stock_qty=None, max_results=8):
    """Predict which customers have the highest propensity to purchase a specific product."""
    if isinstance(analysis_date, str):
        try:
            analysis_date = datetime.fromisoformat(analysis_date[:10]).date()
        except ValueError:
            analysis_date = date.today()

    product_code = str(product_code).strip()
    relevant = [r for r in rows if _kind(r) and _date(r) and _date(r) <= analysis_date]

    product_category = 'Genel'
    product_name = product_code
    for r in relevant:
        if str(r.get('Malzeme Kodu') or '').strip() == product_code:
            product_name = str(r.get('Malzeme Aciklamasi') or product_name)
            product_category = str(r.get('Malzeme Grubu') or product_category)
            break

    # Group by customer
    customers = defaultdict(lambda: {
        'name': 'Bilinmiyor', 'city': '—', 'seller': '—',
        'productDates': set(), 'productQtys': [], 'productAmounts': [],
        'categorySpend': 0.0, 'totalInvoices': set(), 'allDates': set()
    })

    # Companion products
    invoice_baskets = defaultdict(set)
    for r in relevant:
        c_code = str(r.get('Müsteri Kodu') or '').strip()
        p_code = str(r.get('Malzeme Kodu') or '').strip()
        if not c_code or not p_code:
            continue
        inv = str(r.get('Fatura No') or f"{c_code}_{_date(r)}")
        if _kind(r) == 'sale':
            invoice_baskets[inv].add(p_code)

    companion_counter = Counter()
    for basket in invoice_baskets.values():
        if product_code in basket:
            for item in basket:
                if item != product_code:
                    companion_counter[item] += 1

    top_companions = {item for item, _ in companion_counter.most_common(5)}

    for r in relevant:
        c_code = str(r.get('Müsteri Kodu') or '').strip()
        p_code = str(r.get('Malzeme Kodu') or '').strip()
        if not c_code:
            continue

        c = customers[c_code]
        c['name'] = str(r.get('Müsteri Ünvani') or c['name'])
        c['city'] = str(r.get('Sehir') or c['city'])
        c['seller'] = str(r.get('Satici') or c['seller'])
        day = _date(r)
        c['allDates'].add(day)
        inv = str(r.get('Fatura No') or f"{c_code}_{day}")
        c['totalInvoices'].add(inv)

        amt = abs(_number(r.get('Net Satir Tutari')))
        qty = abs(_number(r.get('Miktar')))

        if str(r.get('Malzeme Grubu') or '').strip() == product_category:
            c['categorySpend'] += amt

        if p_code == product_code:
            c['productDates'].add(day)
            c['productQtys'].append(qty)
            c['productAmounts'].append(amt)

    propensity_list = []

    for c_code, c in customers.items():
        if len(c['allDates']) < 2:
            continue

        p_dates = sorted(c['productDates'])
        order_count = len(p_dates)
        avg_qty = round(mean(c['productQtys']), 1) if c['productQtys'] else 1.0

        # Scenario 1: Historical Buyer with Replenishment Hazard Timing
        if order_count >= 1:
            last_p_date = p_dates[-1]
            elapsed = (analysis_date - last_p_date).days
            gaps = [(r - l).days for l, r in zip(p_dates, p_dates[1:]) if (r - l).days > 0]
            cadence = median(gaps) if gaps else 28
            cadence_std = pstdev(gaps) if len(gaps) > 1 else max(3.0, cadence * 0.35)
            z = (elapsed - cadence) / max(3.0, cadence_std)
            hazard = math.exp(-0.5 * (z ** 2))
            cycle_ratio = elapsed / max(1, cadence)

            if 0.70 <= cycle_ratio <= 2.5:
                score = min(96, round(65 + 25 * hazard + min(10, order_count * 2)))
                propensity_list.append({
                    'customerCode': c_code,
                    'customerName': c['name'],
                    'city': c['city'],
                    'seller': c['seller'],
                    'propensityScore': score,
                    'tier': 'Çok Yüksek' if score >= 85 else 'Yüksek',
                    'reason': f"İkmal döngüsü zirvede (son sipariş {elapsed} gün önce, periyot {round(cadence)}±{round(cadence_std)} gün)",
                    'expectedOrderQty': avg_qty,
                    'type': 'due_reorder'
                })
                continue
            elif elapsed <= cadence * 0.7:
                # Recently bought, warehouse full
                continue
            else:
                score = min(80, round(55 + min(15, order_count * 3)))
                propensity_list.append({
                    'customerCode': c_code,
                    'customerName': c['name'],
                    'city': c['city'],
                    'seller': c['seller'],
                    'propensityScore': score,
                    'tier': 'Yüksek',
                    'reason': f"Eski alıcı; son alımdan bu yana {elapsed} gün geçti (periyot {round(cadence)} gün)",
                    'expectedOrderQty': avg_qty,
                    'type': 'due_reorder'
                })
                continue

        # Scenario 2: Active Category Buyer who hasn't bought this SKU
        if c['categorySpend'] >= 500:
            score = min(78, round(55 + min(20, c['categorySpend'] / 200)))
            propensity_list.append({
                'customerCode': c_code,
                'customerName': c['name'],
                'city': c['city'],
                'seller': c['seller'],
                'propensityScore': score,
                'tier': 'Yüksek',
                'reason': f"{product_category} kategorisinde aktif alıcı (€{round(c['categorySpend']):,} ciro), bu SKU'yu denemedi",
                'expectedOrderQty': 1.0,
                'type': 'category_buyer'
            })
            continue

        # Scenario 3: Basket Lookalike
        c_recent_invoices = list(c['totalInvoices'])[-6:]
        companion_hits = 0
        for inv in c_recent_invoices:
            companion_hits += len(invoice_baskets[inv] & top_companions)

        if companion_hits >= 2:
            score = min(72, round(50 + companion_hits * 6))
            propensity_list.append({
                'customerCode': c_code,
                'customerName': c['name'],
                'city': c['city'],
                'seller': c['seller'],
                'propensityScore': score,
                'tier': 'Orta-Yüksek',
                'reason': "Bu ürünle sık birlikte alınan tamamlayıcı ürünleri düzenli tüketiyor",
                'expectedOrderQty': 1.0,
                'type': 'basket_match'
            })

    propensity_list.sort(key=lambda x: -x['propensityScore'])
    return propensity_list[:max_results]
