"""Explainable pricing and seller analytics for the commercial demo.

This module deliberately consumes only canonical sales and sales-return rows.
Purchase documents never leak into turnover, margin, seller, or customer pricing.
"""
import json
from collections import defaultdict
from contextlib import closing
from datetime import datetime
from statistics import median

from analysis import engine


def _number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _round(value, digits=2):
    return round(value, digits) if value is not None else None


def _percentile(values, ratio):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    point = (len(values) - 1) * ratio
    lower, upper = int(point), min(int(point) + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (point - lower)


def _load_rows():
    with closing(engine.db()) as con:
        batch = con.execute("SELECT id FROM batches WHERE kind='movement' ORDER BY created DESC LIMIT 1").fetchone()
        if not batch:
            return []
        return [json.loads(row['converted']) for row in con.execute(
            "SELECT converted FROM records WHERE kind='movement' AND batch_id=?", (batch['id'],)
        )]


def _scope(rows, data):
    start, end = data.get('start'), data.get('end') or data.get('analysisDate')
    sellers = set(data.get('sellers') or [])
    groups = set(data.get('groups') or [])
    scoped = []
    for row in rows:
        kind = engine.invoice_kind(row)
        raw_date = row.get('Fatura Tarihi')
        if kind not in ('sale', 'return') or not raw_date:
            continue
        day = str(raw_date)[:10]
        if start and day < start or end and day > end:
            continue
        seller = str(row.get('Satici') or 'Bilinmiyor').strip() or 'Bilinmiyor'
        if sellers and seller not in sellers:
            continue
        if groups and row.get('Malzeme Grubu') not in groups:
            continue
        scoped.append(row)
    return scoped


def _sign(row):
    return -1 if engine.invoice_kind(row) == 'return' else 1


def _cost(row, replacement=False):
    field = 'Maliyet nach letzter EK RE' if replacement else 'Satir Maliyeti'
    value = abs(_number(row.get(field)))
    if value:
        return value
    qty = abs(_number(row.get('Miktar')))
    unit_field = 'Maliyet Fiyati'
    return qty * abs(_number(row.get(unit_field)))


def _unit_price(row):
    qty = abs(_number(row.get('Miktar')))
    return abs(_number(row.get('Net Satir Tutari'))) / qty if qty else None


def pricing_analytics(data=None):
    data = data or {}
    rows = _scope(_load_rows(), data)
    if not rows:
        return {'status': 'no_data', 'rows': [], 'customers': [], 'signals': [], 'options': {'groups': [], 'sellers': []}}

    products = defaultdict(lambda: {'name': 'Bilinmiyor', 'group': 'Bilinmiyor', 'sales': 0.0, 'gross': 0.0,
        'returns': 0.0, 'qty': 0.0, 'cost': 0.0, 'replacement': 0.0, 'saleQty': 0.0,
        'saleCost': 0.0, 'saleReplacement': 0.0, 'prices': [], 'customers': defaultdict(lambda: {'name': 'Bilinmiyor', 'sales': 0.0, 'qty': 0.0, 'invoices': set(), 'prices': []}), 'invoices': set()})
    for row in rows:
        code = str(row.get('Malzeme Kodu') or '').strip()
        if not code:
            continue
        item, sign = products[code], _sign(row)
        item['name'] = row.get('Malzeme Aciklamasi') or item['name']
        item['group'] = row.get('Malzeme Grubu') or item['group']
        amount, qty = abs(_number(row.get('Net Satir Tutari'))), abs(_number(row.get('Miktar')))
        cost, replacement = _cost(row), _cost(row, True)
        item['sales'] += sign * amount; item['qty'] += sign * qty
        item['cost'] += sign * cost; item['replacement'] += sign * replacement
        if engine.invoice_kind(row) == 'sale':
            item['gross'] += amount; item['saleQty'] += qty
            item['saleCost'] += cost; item['saleReplacement'] += replacement
            price = _unit_price(row)
            if price is not None:
                item['prices'].append(price)
            customer_code = str(row.get('Müsteri Kodu') or 'Bilinmiyor')
            customer = item['customers'][customer_code]
            customer['name'] = row.get('Müsteri Ünvani') or customer['name']
            customer['sales'] += amount; customer['qty'] += qty
            if price is not None: customer['prices'].append(price)
            if row.get('Fatura No'): customer['invoices'].add(row['Fatura No'])
        else:
            item['returns'] += amount
        if row.get('Fatura No'): item['invoices'].add(row['Fatura No'])

    raw_margins = [(x['sales'] - x['replacement']) / x['sales'] * 100 for x in products.values() if x['sales'] > 0 and x['replacement'] > 0]
    target_margin = min(35.0, max(20.0, median(raw_margins) if raw_margins else 25.0))
    result, customers, signals = [], [], []
    for code, item in products.items():
        price = item['gross'] / item['saleQty'] if item['saleQty'] else None
        recorded = item['saleCost'] / item['saleQty'] if item['saleQty'] else None
        replacement = item['saleReplacement'] / item['saleQty'] if item['saleQty'] else None
        profit = item['sales'] - item['cost']; replacement_profit = item['sales'] - item['replacement']
        margin = profit / item['sales'] * 100 if item['sales'] else None
        replacement_margin = replacement_profit / item['sales'] * 100 if item['sales'] else None
        p20, p50, p80 = (_percentile(item['prices'], point) for point in (.2, .5, .8))
        target_price = replacement / (1 - target_margin / 100) if replacement else None
        gap = target_price - price if price is not None and target_price is not None else None
        row = {'code': code, 'name': item['name'], 'group': item['group'], 'sales': _round(item['sales']),
            'grossSales': _round(item['gross']), 'returns': _round(item['returns']), 'returnRate': _round(item['returns'] / item['gross'] * 100 if item['gross'] else 0, 1),
            'quantity': _round(item['qty']), 'invoices': len(item['invoices']), 'customerCount': len(item['customers']),
            'unitPrice': _round(price, 4), 'recordedUnitCost': _round(recorded, 4), 'replacementUnitCost': _round(replacement, 4),
            'profit': _round(profit), 'margin': _round(margin, 1), 'replacementProfit': _round(replacement_profit),
            'replacementMargin': _round(replacement_margin, 1), 'corridorLow': _round(p20, 4), 'corridorMedian': _round(p50, 4),
            'corridorHigh': _round(p80, 4), 'targetMargin': _round(target_margin, 1), 'targetPrice': _round(target_price, 4),
            'priceGap': _round(gap, 4), 'priceGapValue': _round(max(0, gap or 0) * item['saleQty']), 'priceObservations': len(item['prices'])}
        result.append(row)
        if replacement_margin is not None and replacement_margin < 15:
            signals.append({'code': 'PRICE_REPLACEMENT_MARGIN_RISK', 'entityId': code, 'entityName': item['name'],
                'severity': 'critical' if replacement_margin < 0 else 'high', 'title': 'Yerine koyma marjı hedefin altında',
                'evidence': {'observed': _round(replacement_margin, 1), 'threshold': 15, 'unit': '%', 'impact': _round(max(0, -replacement_profit))}})
        if gap is not None and gap > 0:
            signals.append({'code': 'PRICE_BELOW_TARGET', 'entityId': code, 'entityName': item['name'], 'severity': 'attention',
                'title': 'Fiyat hedef marjın altında', 'evidence': {'observed': _round(price, 4), 'threshold': _round(target_price, 4), 'unit': 'EUR/birim', 'impact': _round(gap * item['saleQty'])}})
        if p20 is not None and p80 is not None and p20 and (p80 - p20) / p20 >= .2:
            signals.append({'code': 'PRICE_CORRIDOR_WIDE', 'entityId': code, 'entityName': item['name'], 'severity': 'attention',
                'title': 'Müşteri fiyat koridoru geniş', 'evidence': {'observed': _round((p80-p20)/p20*100, 1), 'threshold': 20, 'unit': '%', 'impact': _round(item['gross'])}})
        for customer_code, customer in item['customers'].items():
            customer_price = customer['sales'] / customer['qty'] if customer['qty'] else None
            deviation = (customer_price / p50 - 1) * 100 if customer_price is not None and p50 else None
            customers.append({'productCode': code, 'productName': item['name'], 'customerCode': customer_code,
                'customerName': customer['name'], 'sales': _round(customer['sales']), 'quantity': _round(customer['qty']),
                'unitPrice': _round(customer_price, 4), 'medianPrice': _round(p50, 4), 'deviation': _round(deviation, 1),
                'invoices': len(customer['invoices']), 'status': 'İskontolu' if deviation is not None and deviation <= -10 else 'Primli' if deviation is not None and deviation >= 10 else 'Koridorda'})

    result.sort(key=lambda x: ((x['priceGapValue'] or 0), x['sales']), reverse=True)
    customers.sort(key=lambda x: abs(x['deviation'] or 0), reverse=True)
    dates = [row['Fatura Tarihi'] for row in rows]
    return {'status': 'ready', 'range': [min(dates), max(dates)], 'currency': 'EUR',
        'summary': {'products': len(result), 'sales': _round(sum(x['sales'] for x in result)),
            'riskProducts': sum((x['replacementMargin'] or 999) < 15 for x in result),
            'priceGapValue': _round(sum(x['priceGapValue'] or 0 for x in result)), 'targetMargin': _round(target_margin, 1)},
        'rows': result, 'customers': customers, 'signals': sorted(signals, key=lambda x: x['evidence']['impact'] or 0, reverse=True),
        'options': {'groups': sorted({x['group'] for x in result}), 'sellers': sorted({str(r.get('Satici') or 'Bilinmiyor') for r in rows})},
        'methodology': 'Fiyat koridoru satış satırlarındaki müşteri birim fiyatlarının P20–medyan–P80 aralığıdır. Hedef fiyat, portföyün medyan yerine koyma marjı (%20–%35 sınırında) üzerinden hesaplanır.'}


def seller_analytics(data=None):
    data = data or {}
    rows = _scope(_load_rows(), data)
    if not rows:
        return {'status': 'no_data', 'rows': [], 'signals': [], 'options': {'sellers': []}}
    grouped = defaultdict(lambda: {'sales': 0.0, 'gross': 0.0, 'returns': 0.0, 'cost': 0.0, 'replacement': 0.0,
        'invoices': set(), 'customers': set(), 'products': defaultdict(lambda: {'sales': 0.0, 'replacement': 0.0}),
        'bonusSales': 0.0, 'discount': 0.0})
    for row in rows:
        seller = str(row.get('Satici') or 'Bilinmiyor').strip() or 'Bilinmiyor'
        item, sign = grouped[seller], _sign(row)
        amount = abs(_number(row.get('Net Satir Tutari')))
        item['sales'] += sign * amount; item['cost'] += sign * _cost(row); item['replacement'] += sign * _cost(row, True)
        item['discount'] += sign * abs(_number(row.get('Indirim Tutari')))
        if engine.invoice_kind(row) == 'sale':
            item['gross'] += amount
            if str(row.get('PrimVar') or '').strip().lower() not in ('', '0', 'hayır', 'hayir', 'false', 'yok'):
                item['bonusSales'] += amount
        else: item['returns'] += amount
        if row.get('Fatura No'): item['invoices'].add(row['Fatura No'])
        if row.get('Müsteri Kodu'): item['customers'].add(row['Müsteri Kodu'])
        code = str(row.get('Malzeme Kodu') or '')
        if code:
            item['products'][code]['sales'] += sign * amount
            item['products'][code]['replacement'] += sign * _cost(row, True)
    result, signals = [], []
    total_sales = sum(x['sales'] for x in grouped.values())
    for seller, item in grouped.items():
        profit = item['sales'] - item['cost']; replacement_profit = item['sales'] - item['replacement']
        margin = profit / item['sales'] * 100 if item['sales'] else None
        replacement_margin = replacement_profit / item['sales'] * 100 if item['sales'] else None
        risky = [p for p in item['products'].values() if p['sales'] and (p['sales']-p['replacement'])/p['sales']*100 < 15]
        top_product = max((p['sales'] for p in item['products'].values()), default=0)
        concentration = top_product / item['sales'] * 100 if item['sales'] else 0
        row = {'name': seller, 'sales': _round(item['sales']), 'share': _round(item['sales']/total_sales*100 if total_sales else 0, 1),
            'profit': _round(profit), 'margin': _round(margin, 1), 'replacementProfit': _round(replacement_profit),
            'replacementMargin': _round(replacement_margin, 1), 'returns': _round(item['returns']),
            'returnRate': _round(item['returns']/item['gross']*100 if item['gross'] else 0, 1), 'invoices': len(item['invoices']),
            'customers': len(item['customers']), 'products': len(item['products']), 'averageBasket': _round(item['sales']/len(item['invoices']) if item['invoices'] else 0),
            'bonusEligibleSales': _round(item['bonusSales']), 'bonusCoverage': _round(item['bonusSales']/item['gross']*100 if item['gross'] else 0, 1),
            'discount': _round(item['discount']), 'riskyProducts': len(risky), 'portfolioConcentration': _round(concentration, 1),
            'portfolioQuality': 'Riskli' if (replacement_margin is not None and replacement_margin < 15) or len(risky) >= max(3, len(item['products'])*.25) else 'Dengeli'}
        result.append(row)
        if seller == 'Bilinmiyor':
            signals.append({'code': 'SELLER_UNASSIGNED', 'seller': seller, 'severity': 'attention', 'title': 'Atanmamış satış hareketi', 'evidence': {'impact': _round(item['sales']), 'unit': 'EUR'}})
        if replacement_margin is not None and replacement_margin < 15:
            signals.append({'code': 'SELLER_MARGIN_COACHING', 'seller': seller, 'severity': 'high', 'title': 'Marj koçluğu gerekli', 'evidence': {'observed': _round(replacement_margin,1), 'threshold': 15, 'unit': '%', 'impact': _round(max(0,-replacement_profit))}})
        if row['returnRate'] >= 8:
            signals.append({'code': 'SELLER_RETURN_COACHING', 'seller': seller, 'severity': 'high', 'title': 'İade oranı yüksek', 'evidence': {'observed': row['returnRate'], 'threshold': 8, 'unit': '%', 'impact': row['returns']}})
        if concentration >= 50 and len(item['products']) >= 3:
            signals.append({'code': 'SELLER_PORTFOLIO_CONCENTRATION', 'seller': seller, 'severity': 'attention', 'title': 'Portföy tek üründe yoğunlaşıyor', 'evidence': {'observed': _round(concentration,1), 'threshold': 50, 'unit': '%', 'impact': row['sales']}})
    result.sort(key=lambda x: x['sales'], reverse=True)
    dates = [row['Fatura Tarihi'] for row in rows]
    return {'status':'ready', 'range':[min(dates),max(dates)], 'currency':'EUR', 'rows':result,
        'signals':sorted(signals,key=lambda x:x['evidence'].get('impact',0),reverse=True),
        'summary': {'sellers':len(result),'sales':_round(total_sales),'profit':_round(sum(x['profit'] for x in result)),
            'margin':_round(sum(x['profit'] for x in result)/total_sales*100 if total_sales else 0,1),
            'unassignedSales':next((x['sales'] for x in result if x['name']=='Bilinmiyor'),0),
            'coachingSignals':sum(x['code']!='SELLER_UNASSIGNED' for x in signals)},
        'options': {'sellers':[x['name'] for x in result]},
        'methodology':'Satış iadeleri ciro, adet ve kârdan düşülür; satın alma belgeleri hariçtir. Prim kapsaması PrimVar işaretli brüt satışların payıdır. Portföy kalitesi yerine koyma marjı ve riskli ürün yoğunluğuyla açıklanır.'}
