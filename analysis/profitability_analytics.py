"""Sales profitability and executive decision snapshot.

All revenue metrics include only sales and sales returns. Purchase documents are
excluded by construction. Registered and replacement economics stay separate.
"""
import json
from collections import defaultdict
from contextlib import closing
from datetime import date, datetime, timedelta

from analysis import engine


def _num(value):
    try: return float(value or 0)
    except (TypeError, ValueError): return 0.0


def _load():
    with closing(engine.db()) as con:
        batch=con.execute("SELECT id FROM batches WHERE kind='movement' ORDER BY created DESC LIMIT 1").fetchone()
        if not batch:return []
        return [json.loads(x['converted']) for x in con.execute("SELECT converted FROM records WHERE kind='movement' AND batch_id=?",(batch['id'],))]


def _scope(data):
    rows=[]; sellers=set(data.get('sellers') or []); warehouses=set(data.get('warehouses') or []); groups=set(data.get('groups') or [])
    start=data.get('start'); end=data.get('end')
    for row in _load():
        kind=engine.invoice_kind(row); raw=row.get('Fatura Tarihi')
        if kind not in ('sale','return') or not raw:continue
        if start and raw<start or end and raw>end:continue
        if sellers and str(row.get('Satici') or 'Bilinmiyor') not in sellers:continue
        if warehouses and str(row.get('Ambar') or 'Bilinmiyor') not in warehouses:continue
        if groups and str(row.get('Malzeme Grubu') or 'Bilinmiyor') not in groups:continue
        rows.append(row)
    return rows


def _cost(row,replacement=False):
    field='Maliyet nach letzter EK RE' if replacement else 'Satir Maliyeti'
    value=abs(_num(row.get(field)))
    if value:return value
    return abs(_num(row.get('Miktar')))*abs(_num(row.get('Maliyet Fiyati')))


def _metrics(rows):
    sales=[r for r in rows if engine.invoice_kind(r)=='sale']; returns=[r for r in rows if engine.invoice_kind(r)=='return']
    invoiced=sum(abs(_num(r.get('Net Satir Tutari'))) for r in sales)
    discounts=sum(abs(_num(r.get('Indirim Tutari'))) for r in sales)
    gross=invoiced+discounts
    returned=sum(abs(_num(r.get('Net Satir Tutari'))) for r in returns)
    net=invoiced-returned
    cost=sum(_cost(r) for r in sales)-sum(_cost(r) for r in returns)
    replacement=sum(_cost(r,True) for r in sales)-sum(_cost(r,True) for r in returns)
    profit=net-cost; replacement_profit=net-replacement
    return {'grossSales':round(gross,2),'discounts':round(discounts,2),'returns':round(returned,2),'netSales':round(net,2),
      'cogs':round(cost,2),'grossProfit':round(profit,2),'margin':round(profit/net*100,1) if net else None,
      'replacementCogs':round(replacement,2),'replacementProfit':round(replacement_profit,2),
      'replacementMargin':round(replacement_profit/net*100,1) if net else None,
      'marginGap':round((profit-replacement_profit),2),'invoices':len({r.get('Fatura No') for r in rows if r.get('Fatura No')}),
      'customers':len({r.get('Müsteri Kodu') for r in rows if r.get('Müsteri Kodu')})}


def _breakdown(rows,key,name_key=None):
    groups=defaultdict(list)
    for row in rows:
        identifier=str(row.get(key) or 'Bilinmiyor')
        label=str(row.get(name_key) or identifier) if name_key else identifier
        groups[(identifier,label)].append(row)
    output=[]
    for (identifier,label),items in groups.items():
        value=_metrics(items)
        output.append({'id':identifier,'name':label,**value,'products':len({r.get('Malzeme Kodu') for r in items if r.get('Malzeme Kodu')})})
    return sorted(output,key=lambda x:x['netSales'],reverse=True)


def sales_profitability(data=None):
    data=data or {}; rows=_scope(data)
    if not rows:return {'status':'no_data','trend':[],'breakdowns':{},'signals':[]}
    dates=[datetime.fromisoformat(r['Fatura Tarihi']).date() for r in rows]
    start,end=min(dates),max(dates); days=(end-start).days+1; granularity='day' if days<90 else 'month'
    buckets=defaultdict(list)
    for row in rows:
        when=datetime.fromisoformat(row['Fatura Tarihi']).date()
        key=when.isoformat() if granularity=='day' else f'{when.year:04d}-{when.month:02d}'
        buckets[key].append(row)
    trend=[{'period':key,**_metrics(bucket)} for key,bucket in sorted(buckets.items())]
    metrics=_metrics(rows)
    waterfall=[{'key':'gross','label':'Brüt satış','value':metrics['grossSales'],'kind':'start'},
      {'key':'discount','label':'İndirimler','value':-metrics['discounts'],'kind':'decrease'},
      {'key':'returns','label':'İadeler','value':-metrics['returns'],'kind':'decrease'},
      {'key':'net','label':'Net satış','value':metrics['netSales'],'kind':'result'},
      {'key':'cogs','label':'COGS','value':-metrics['cogs'],'kind':'decrease'},
      {'key':'profit','label':'Brüt kâr','value':metrics['grossProfit'],'kind':'result'}]
    category=_breakdown(rows,'Malzeme Grubu'); customer=_breakdown(rows,'Müsteri Kodu','Müsteri Ünvani'); seller=_breakdown(rows,'Satici'); warehouse=_breakdown(rows,'Ambar')
    signals=[]
    if metrics['replacementMargin'] is not None and metrics['replacementMargin']<15:
        signals.append({'type':'risk','severity':'high','title':'Yerine koyma marjı kritik eşiğin altında','detail':f"Portföy marjı %{metrics['replacementMargin']}; kayıtlı ekonomi farkı €{metrics['marginGap']:,.0f}.",'impact':max(0,metrics['netSales']*.15-metrics['replacementProfit']),'target':'pricing_costs'})
    for item in category:
        if item['replacementMargin'] is not None and item['replacementMargin']<10:
            signals.append({'type':'risk','severity':'high','title':f"{item['name']} marj riski",'detail':f"Yerine koyma marjı %{item['replacementMargin']}; etki %15 hedefe göre hesaplandı.",'impact':max(0,item['netSales']*.15-item['replacementProfit']),'target':'pricing_costs'})
    opportunities=sorted((x for x in customer if (x['replacementMargin'] or -999)>=25),key=lambda x:x['replacementProfit'],reverse=True)
    if opportunities:
        top=opportunities[0];signals.append({'type':'opportunity','severity':'info','title':f"{top['name']} yüksek kaliteli büyüme",'detail':f"€{top['netSales']:,.0f} satışta %{top['replacementMargin']} yerine koyma marjı.",'impact':top['replacementProfit'],'target':'customers_360','entityId':top['id']})
    return {'status':'ready','range':[start.isoformat(),end.isoformat()],'days':days,'granularity':granularity,'currency':'EUR',
      'metrics':metrics,'waterfall':waterfall,'trend':trend,'breakdowns':{'category':category,'customer':customer,'seller':seller,'warehouse':warehouse},
      'signals':sorted(signals,key=lambda x:x['impact'],reverse=True),
      'options':{'sellers':sorted({str(r.get('Satici') or 'Bilinmiyor') for r in rows}),'warehouses':sorted({str(r.get('Ambar') or 'Bilinmiyor') for r in rows}),'groups':sorted({str(r.get('Malzeme Grubu') or 'Bilinmiyor') for r in rows})},
      'methodology':'Brüt satış = satış faturası net satırları + indirimler. Net satış = brüt satış − indirim − satış iadesi. Satın alma belgeleri hariçtir. 90 günden kısa seçimler günlük, diğer seçimler aylık gösterilir.'}


def executive_snapshot(data=None):
    result=sales_profitability(data or {})
    if result.get('status')!='ready':return {'status':'no_data','items':[],'openActions':0}
    items=list(result['signals'])
    with closing(engine.db()) as con:
        actions=[dict(x) for x in con.execute("SELECT id,title,priority,status,entity_type,entity_id,due_date FROM actions WHERE status IN ('open','in_progress') ORDER BY CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 ELSE 2 END, due_date LIMIT 3")]
    for action in actions:
        items.append({'type':'action','severity':action['priority'],'title':action['title'],'detail':f"{action['status']} · {action.get('due_date') or 'Tarih atanmamış'}",'impact':0,'target':'actions','entityId':action['id']})
    order={'risk':0,'opportunity':1,'action':2}
    items.sort(key=lambda x:(order.get(x['type'],9),-x.get('impact',0)))
    return {'status':'ready','items':items[:6],'openActions':len(actions),'metrics':result['metrics'],'range':result['range']}
