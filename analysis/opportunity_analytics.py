"""Operational opportunity analytics for phases E-H.

The module deliberately keeps calculation logic independent from the HTTP layer.  It
can be called with explicit rows in tests, or load the latest committed batches when
used by ``engine.py``.  Monetary values are EUR and all dates are ISO strings.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from contextlib import closing
from datetime import date, datetime, timedelta
from itertools import combinations
from statistics import median


def _fold(value):
    value = str(value or '').strip().replace('ı', 'i').replace('İ', 'i').casefold()
    return ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c))


def _number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _kind(row):
    value = _fold(row.get('Fatura Türü'))
    return {
        'satis': 'sale', 'satis faturasi': 'sale',
        'satis iadesi': 'return', 'satis iade faturasi': 'return',
        'satin alma': 'purchase', 'satin alma faturasi': 'purchase', 'satinalma faturasi': 'purchase',
        'alis faturasi': 'purchase', 'satin alma iadesi': 'purchase_return',
        'satin alma iade faturasi': 'purchase_return', 'satinalma iade faturasi': 'purchase_return',
        'alis iade faturasi': 'purchase_return',
    }.get(value)


COUNTRY_NAMES = {
    'de': 'Almanya', 'deu': 'Almanya', 'germany': 'Almanya', 'deutschland': 'Almanya', 'almanya': 'Almanya',
    'tr': 'Türkiye', 'tur': 'Türkiye', 'turkey': 'Türkiye', 'turkiye': 'Türkiye',
    'at': 'Avusturya', 'aut': 'Avusturya', 'austria': 'Avusturya', 'osterreich': 'Avusturya',
    'nl': 'Hollanda', 'nld': 'Hollanda', 'netherlands': 'Hollanda', 'niederlande': 'Hollanda',
    'be': 'Belçika', 'bel': 'Belçika', 'belgium': 'Belçika', 'belgie': 'Belçika',
    'fr': 'Fransa', 'fra': 'Fransa', 'france': 'Fransa',
}

CITY_NAMES = {
    'koln': 'Köln', 'koeln': 'Köln', 'cologne': 'Köln', 'munchen': 'München', 'muenchen': 'München',
    'nurnberg': 'Nürnberg', 'nuernberg': 'Nürnberg', 'dusseldorf': 'Düsseldorf',
    'duesseldorf': 'Düsseldorf', 'frankfurt am main': 'Frankfurt', 'istanbul': 'İstanbul',
}


def standardize_location(row):
    """Return display-safe location fields while preserving an explicit unknown state."""
    raw_country = re.sub(r'\s+', ' ', str(row.get('Ülke') or '')).strip()
    raw_city = re.sub(r'\s+', ' ', str(row.get('Sehir') or '')).strip()
    raw_postal = re.sub(r'\s+', '', str(row.get('Posta Kodu') or '')).strip()
    country = COUNTRY_NAMES.get(_fold(raw_country), raw_country.title() if raw_country else 'Bilinmiyor')
    city = CITY_NAMES.get(_fold(raw_city), raw_city.title() if raw_city else 'Bilinmiyor')
    postal = raw_postal or 'Bilinmiyor'
    return {'country': country, 'city': city, 'postalCode': postal,
            'complete': country != 'Bilinmiyor' and city != 'Bilinmiyor' and postal != 'Bilinmiyor'}


def _day(row):
    try:
        return datetime.fromisoformat(str(row.get('Fatura Tarihi') or '')[:10]).date()
    except ValueError:
        return None


def _filter_rows(rows, filters):
    filters = filters or {}
    start, end = filters.get('start'), filters.get('end')
    warehouses, sellers = set(filters.get('warehouses') or []), set(filters.get('sellers') or [])
    out = []
    for row in rows:
        day = _day(row)
        if not day or not _kind(row):
            continue
        if start and day.isoformat() < start or end and day.isoformat() > end:
            continue
        if warehouses and row.get('Ambar') not in warehouses or sellers and row.get('Satici') not in sellers:
            continue
        out.append(row)
    return out


def geography(rows, analysis_date):
    sales = [r for r in rows if _kind(r) in ('sale', 'return')]
    grouped = defaultdict(lambda: {'sales': 0.0, 'profit': 0.0, 'returns': 0.0, 'customers': set(),
                                   'invoices': set(), 'products': set(), 'postals': set()})
    unknown = 0
    countries = Counter()
    for row in sales:
        location = standardize_location(row)
        key = (location['country'], location['city'])
        g = grouped[key]
        sign = -1 if _kind(row) == 'return' else 1
        amount = abs(_number(row.get('Net Satir Tutari')))
        profit = _number(row.get('Satir Kari')) if sign > 0 else abs(_number(row.get('Satir Kari')))
        g['sales'] += sign * amount
        g['profit'] += sign * profit
        if sign < 0: g['returns'] += amount
        if row.get('Müsteri Kodu'): g['customers'].add(str(row['Müsteri Kodu']))
        if row.get('Fatura No'): g['invoices'].add(str(row['Fatura No']))
        if row.get('Malzeme Kodu'): g['products'].add(str(row['Malzeme Kodu']))
        if location['postalCode'] != 'Bilinmiyor': g['postals'].add(location['postalCode'])
        countries[location['country']] += amount
        unknown += not location['complete']
    result = []
    total = sum(g['sales'] for g in grouped.values())
    for (country, city), g in grouped.items():
        result.append({'country': country, 'city': city, 'name': f'{city}, {country}',
          'sales': round(g['sales'], 2), 'profit': round(g['profit'], 2),
          'margin': round(g['profit'] / g['sales'] * 100, 1) if g['sales'] else None,
          'returns': round(g['returns'], 2), 'customers': len(g['customers']), 'invoices': len(g['invoices']),
          'products': len(g['products']), 'postalCount': len(g['postals']),
          'share': round(g['sales'] / total * 100, 1) if total else 0})
    from analysis.geography_locations import locate
    for item in result:
        item.update(locate(item['country'], item['city']))
    result.sort(key=lambda x: x['sales'], reverse=True)
    return {'status': 'ready', 'module': 'geography', 'title': 'Coğrafi Analiz',
      'analysisDate': analysis_date.isoformat(), 'currency': 'EUR',
      'kpis': [('Net satış', round(total, 2), 'EUR'), ('Şehir', len(result), 'adet'),
               ('Ülke', len(countries), 'adet'), ('Eksik konum satırı', unknown, 'adet')],
      'rows': result, 'countries': [{'name': k, 'sales': round(v, 2)} for k, v in countries.most_common()],
      'quality': {'incompleteRows': unknown, 'rowCount': len(sales)},
      'note': 'Şehir, ülke ve posta kodundaki gereksiz boşluklar temizlendi; bilinemeyen değerler tahmin edilmedi.'}


def purchasing_balance(rows, stock_model, analysis_date):
    purchases = [r for r in rows if _kind(r) in ('purchase', 'purchase_return')]
    sale_rows = [r for r in rows if _kind(r) in ('sale', 'return')]
    stock_by_code = {str(x.get('code')): x for x in (stock_model or [])}
    products = defaultdict(lambda: {'name': 'Bilinmiyor', 'category': 'Bilinmiyor', 'buy': 0.0, 'buyQty': 0.0,
                                    'return': 0.0, 'invoices': set(), 'currentCost': [], 'previousCost': [],
                                    'sold30': 0.0})
    current_start, previous_start = analysis_date - timedelta(days=89), analysis_date - timedelta(days=179)
    for row in purchases:
        code = str(row.get('Malzeme Kodu') or 'Bilinmiyor'); p = products[code]
        p['name'] = row.get('Malzeme Aciklamasi') or p['name']; p['category'] = row.get('Malzeme Grubu') or p['category']
        sign = -1 if _kind(row) == 'purchase_return' else 1
        qty, amount = abs(_number(row.get('Miktar'))), abs(_number(row.get('Net Satir Tutari')))
        p['buy'] += sign * amount; p['buyQty'] += sign * qty
        if sign < 0: p['return'] += amount
        if row.get('Fatura No'): p['invoices'].add(str(row['Fatura No']))
        unit_cost = amount / qty if qty else _number(row.get('Birim Fiyati'))
        day = _day(row)
        if unit_cost and day and current_start <= day <= analysis_date: p['currentCost'].append(unit_cost)
        elif unit_cost and day and previous_start <= day < current_start: p['previousCost'].append(unit_cost)
    for row in sale_rows:
        day = _day(row)
        if not day or day < analysis_date - timedelta(days=29): continue
        code = str(row.get('Malzeme Kodu') or 'Bilinmiyor')
        sign = -1 if _kind(row) == 'return' else 1
        products[code]['sold30'] += sign * abs(_number(row.get('Miktar')))
        products[code]['name'] = row.get('Malzeme Aciklamasi') or products[code]['name']
        products[code]['category'] = row.get('Malzeme Grubu') or products[code]['category']
    result = []
    for code, p in products.items():
        stock = stock_by_code.get(code, {})
        quantity = _number(stock.get('quantity'))
        current = median(p['currentCost']) if p['currentCost'] else None
        previous = median(p['previousCost']) if p['previousCost'] else None
        change = (current / previous - 1) * 100 if current is not None and previous else None
        daily = _number(stock['dailySales']) if 'dailySales' in stock else max(0, p['sold30']) / 30
        coverage = quantity / daily if daily else None
        if coverage is None: recommendation = 'Talep geçmişi yetersiz'
        elif coverage < 14: recommendation = 'Sipariş adayı'
        elif coverage > 75: recommendation = 'Eritme adayı'
        else: recommendation = 'Dengeli'
        target = stock.get('targetCoverageDays') or 21
        suggested = math.ceil(max(0, target * daily - quantity)) if daily else None
        content = stock.get('content')
        suggested_cost = round(suggested * current * content, 2) if suggested is not None and current is not None and content else None
        result.append({'suggestedCases': suggested, 'suggestedCost': suggested_cost, 'targetCoverageDays': target, 'code': code, 'name': p['name'], 'category': p['category'], 'purchases': round(p['buy'], 2),
          'purchaseQuantity': round(p['buyQty'], 1), 'purchaseReturns': round(p['return'], 2),
          'invoices': len(p['invoices']), 'currentUnitCost': round(current, 4) if current is not None else None,
          'previousUnitCost': round(previous, 4) if previous is not None else None,
          'costChange': round(change, 1) if change is not None else None, 'stock': round(quantity),
          'consumption30': round(max(0, p['sold30']), 1), 'coverageDays': round(coverage, 1) if coverage is not None else None,
          'recommendation': recommendation, 'stockSource': stock.get('source', 'demo')})
    order = {'Sipariş adayı': 0, 'Eritme adayı': 1, 'Dengeli': 2, 'Talep geçmişi yetersiz': 3}
    result.sort(key=lambda x: (order[x['recommendation']], x['coverageDays'] or 10**9))
    net = sum(x['purchases'] for x in result); returned = sum(x['purchaseReturns'] for x in result)
    return {'status': 'ready', 'module': 'purchasing_balance', 'title': 'Satın Alma Planı',
      'analysisDate': analysis_date.isoformat(), 'currency': 'EUR', 'demoStock': True,
      'kpis': [('Net satın alma', round(net, 2), 'EUR'), ('Alım iadesi', round(returned, 2), 'EUR'),
               ('Sipariş adayı', sum(x['recommendation'] == 'Sipariş adayı' for x in result), 'adet'),
               ('Eritme adayı', sum(x['recommendation'] == 'Eritme adayı' for x in result), 'adet')],
      'rows': result, 'note': 'Alım ve fiyat değişimi hareket verisidir. Stok miktarı demo modelidir; karar öncesi fiziksel stok doğrulanmalıdır.',
      'definitions': {'current': 'Son 90 gündeki medyan alış birim fiyatı', 'previous': 'Önceki 90 gündeki medyan alış birim fiyatı',
                      'orderCandidate': '14 günden az kapsama', 'liquidationCandidate': '75 günden fazla kapsama'}}


def basket_analysis(rows, analysis_date, minimum_baskets=5, minimum_base=20):
    invoice_items, invoice_customers = defaultdict(set), defaultdict(set)
    names = {}
    for row in rows:
        if _kind(row) != 'sale' or not row.get('Fatura No') or not row.get('Malzeme Kodu'): continue
        invoice = f"{row.get('Müsteri Kodu') or '—'}|{row['Fatura No']}"
        code = str(row['Malzeme Kodu']); invoice_items[invoice].add(code)
        if row.get('Müsteri Kodu'): invoice_customers[invoice].add(str(row['Müsteri Kodu']))
        names[code] = row.get('Malzeme Aciklamasi') or code
    count = len(invoice_items); item_counts = Counter(); pair_counts = Counter(); pair_customers = defaultdict(set)
    for invoice, items in invoice_items.items():
        item_counts.update(items)
        for a, b in combinations(sorted(items), 2):
            pair_counts[(a, b)] += 1; pair_customers[(a, b)].update(invoice_customers[invoice])
    result, suppressed = [], 0
    for (a, b), together in pair_counts.items():
        if together < minimum_baskets or item_counts[a] < minimum_base or item_counts[b] < minimum_base:
            suppressed += 1; continue
        support = together / count if count else 0
        confidence_ab = together / item_counts[a]; confidence_ba = together / item_counts[b]
        lift = support / ((item_counts[a] / count) * (item_counts[b] / count)) if count else 0
        direction = (a, b, confidence_ab) if confidence_ab >= confidence_ba else (b, a, confidence_ba)
        result.append({'antecedentCode': direction[0], 'antecedent': names[direction[0]],
          'consequentCode': direction[1], 'consequent': names[direction[1]],
          'name': f'{names[direction[0]]} → {names[direction[1]]}', 'together': together,
          'support': round(support * 100, 2), 'confidence': round(direction[2] * 100, 1),
          'lift': round(lift, 2), 'customers': len(pair_customers[(a, b)]),
          'strength': 'Güçlü' if lift >= 1.2 and direction[2] >= .25 else 'İzlemeye değer'})
    result.sort(key=lambda x: (x['strength'] != 'Güçlü', -x['lift'], -x['confidence']))
    return {'status': 'ready', 'module': 'cross_sell', 'title': 'Sepet ve Çapraz Satış',
      'analysisDate': analysis_date.isoformat(),
      'kpis': [('Sepet', count, 'adet'), ('Birlikte ürün çifti', len(result), 'adet'),
               ('Güçlü fırsat', sum(x['strength'] == 'Güçlü' for x in result), 'adet'),
               ('Düşük örneklemde gizlenen', suppressed, 'adet')], 'rows': result,
      'thresholds': {'minimumPairBaskets': minimum_baskets, 'minimumProductBaskets': minimum_base},
      'note': 'Support birlikte görülme, confidence yönlü öneri olasılığı, lift ise tesadüfi beklentiye göre kuvvettir. Lift > 1 pozitif ilişkidir.'}


def returns_analysis(rows, analysis_date):
    sales = [r for r in rows if _kind(r) == 'sale']
    returns = [r for r in rows if _kind(r) == 'return']
    products = defaultdict(lambda: {'name': 'Bilinmiyor', 'amount': 0.0, 'quantity': 0.0, 'profit': 0.0,
                                    'replacement': 0.0, 'customers': set(), 'invoices': set()})
    customers = defaultdict(lambda: {'name': 'Bilinmiyor', 'amount': 0.0, 'quantity': 0.0, 'profit': 0.0,
                                     'replacement': 0.0, 'products': set(), 'invoices': set()})
    recent30 = recent90 = 0.0
    for row in returns:
        amount, qty = abs(_number(row.get('Net Satir Tutari'))), abs(_number(row.get('Miktar')))
        profit = abs(_number(row.get('Satir Kari')))
        replacement = abs(_number(row.get('Maliyet nach letzter EK RE')))
        code = str(row.get('Malzeme Kodu') or 'Bilinmiyor'); customer = str(row.get('Müsteri Kodu') or 'Bilinmiyor')
        p, c = products[code], customers[customer]
        p['name'] = row.get('Malzeme Aciklamasi') or p['name']; c['name'] = row.get('Müsteri Ünvani') or c['name']
        for target in (p, c):
            target['amount'] += amount; target['quantity'] += qty; target['profit'] += profit; target['replacement'] += replacement
            if row.get('Fatura No'): target['invoices'].add(str(row['Fatura No']))
        p['customers'].add(customer); c['products'].add(code)
        age = (analysis_date - _day(row)).days if _day(row) else 10**9
        if age < 90: recent90 += amount
        if age < 30: recent30 += amount
    def finalize(grouped, relation):
        output = []
        for code, g in grouped.items():
            output.append({'code': code, 'name': g['name'], 'returns': round(g['amount'], 2),
              'quantity': round(g['quantity'], 1), 'profitImpact': round(g['profit'], 2),
              'replacementImpact': round(g['replacement'], 2), 'invoices': len(g['invoices']),
              relation: len(g['customers'] if relation == 'customers' else g['products'])})
        return sorted(output, key=lambda x: x['returns'], reverse=True)
    product_rows, customer_rows = finalize(products, 'customers'), finalize(customers, 'products')
    gross_sales = sum(abs(_number(r.get('Net Satir Tutari'))) for r in sales)
    amount = sum(x['returns'] for x in product_rows); quantity = sum(x['quantity'] for x in product_rows)
    profit = sum(x['profitImpact'] for x in product_rows); replacement = sum(x['replacementImpact'] for x in product_rows)
    projection90 = recent30 * 3
    return {'status': 'ready', 'module': 'returns_analysis', 'title': 'İade Analizi',
      'analysisDate': analysis_date.isoformat(), 'currency': 'EUR',
      'kpis': [('İade tutarı', round(amount, 2), 'EUR'), ('İade miktarı', round(quantity, 1), 'birim'),
               ('Kâr etkisi', round(profit, 2), 'EUR'), ('Yerine koyma etkisi', round(replacement, 2), 'EUR')],
      'rows': product_rows, 'products': product_rows, 'customers': customer_rows,
      'summary': {'returnRate': round(amount / gross_sales * 100, 2) if gross_sales else None,
                  'returningCustomers': len(customers), 'affectedProducts': len(products)},
      'scenario': {'last30': round(recent30, 2), 'last90': round(recent90, 2),
                   'next90At30DayPace': round(projection90, 2),
                   'changeVs90DayPace': round((projection90 / recent90 - 1) * 100, 1) if recent90 else None},
      'note': 'Senaryo, son 30 günlük iade hızının 90 gün sürmesi halinde oluşacak tutarı gösterir; tahmin garantisi değildir.'}


def build_operations_dataset(module, movement_rows, stock_model=None, analysis_date=None, filters=None):
    rows = _filter_rows(movement_rows, filters)
    dated = [_day(r) for r in rows if _day(r)]
    chosen = min(datetime.fromisoformat(str(analysis_date)[:10]).date(), max(dated)) if analysis_date and dated else (max(dated) if dated else date.today())
    rows = [r for r in rows if _day(r) and _day(r) <= chosen]
    if module == 'geography': return geography(rows, chosen)
    if module == 'purchasing_balance': return purchasing_balance(rows, stock_model or [], chosen)
    if module == 'cross_sell': return basket_analysis(rows, chosen)
    if module == 'returns_analysis': return returns_analysis(rows, chosen)
    raise ValueError('Desteklenmeyen operasyon analizi.')


def opportunity_analytics(data):
    """Load the latest accepted source and return one E-H operational module."""
    from analysis import engine  # lazy import prevents a circular import during engine startup
    with closing(engine.db()) as con:
        movement = con.execute("SELECT id FROM batches WHERE kind='movement' ORDER BY created DESC LIMIT 1").fetchone()
        if not movement: return {'status': 'no_data', 'module': data.get('module'), 'rows': []}
        rows = [json.loads(r['converted']) for r in con.execute(
            "SELECT converted FROM records WHERE kind='movement' AND batch_id=?", (movement['id'],))]
    stock_model = []
    if data.get('module') == 'purchasing_balance':
        model = engine.stock_analysis({'analysisDate': data.get('analysisDate')})
        stock_model = model.get('products', [])
    return build_operations_dataset(str(data.get('module') or ''), rows, stock_model,
                                    data.get('analysisDate'), data.get('filters'))
