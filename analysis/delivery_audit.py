"""Delivery checks shared by tests and the final demo acceptance run."""
from __future__ import annotations

import json
import math
import time
import unicodedata
from contextlib import closing


ERROR_CATALOG={
  'INVALID_REQUEST':(400,'İstek alanlarını kontrol edin.'),
  'NOT_FOUND':(404,'İstenen kayıt bulunamadı.'),
  'PAYLOAD_TOO_LARGE':(413,'İstek boyutu izin verilen sınırı aşıyor.'),
  'ANALYSIS_TIMEOUT':(504,'Analiz zaman sınırında tamamlanamadı.'),
  'INTERNAL_ERROR':(500,'İşlem tamamlanamadı.'),
}


def error_envelope(code,message=None,details=None,retryable=False,request_id=None):
    status,default=ERROR_CATALOG.get(code,ERROR_CATALOG['INTERNAL_ERROR'])
    return {'ok':False,'error':{'code':code,'message':str(message or default),'details':details,
      'retryable':bool(retryable),'requestId':request_id},'status':status}


def page(items,offset=0,limit=50):
    try:offset=max(0,int(offset));limit=min(100,max(1,int(limit)))
    except (TypeError,ValueError):raise ValueError('Sayfalama değerleri tam sayı olmalıdır.')
    total=len(items);return {'items':items[offset:offset+limit],
      'pagination':{'offset':offset,'limit':limit,'total':total,'hasNext':offset+limit<total}}


def _fold(value):
    value=str(value or '').strip().replace('ı','i').replace('İ','i').casefold()
    return ''.join(c for c in unicodedata.normalize('NFKD',value) if not unicodedata.combining(c))


def _kind(row):
    return {'satis':'sale','satis faturasi':'sale','satis iadesi':'return','satis iade faturasi':'return',
      'satin alma':'purchase','satin alma faturasi':'purchase','satinalma faturasi':'purchase',
      'satin alma iadesi':'purchase_return','satin alma iade faturasi':'purchase_return','satinalma iade faturasi':'purchase_return'}.get(_fold(row.get('Fatura Türü')))


def _number(value):
    try:
        number=float(value or 0);return number if math.isfinite(number) else 0
    except (TypeError,ValueError):return 0


def reconcile(rows):
    totals={'salesGross':0.0,'salesReturns':0.0,'netSales':0.0,'grossProfit':0.0,
      'purchaseGross':0.0,'purchaseReturns':0.0,'netPurchases':0.0}
    unknown=nonfinite=0
    for row in rows:
        kind=_kind(row)
        if not kind:unknown+=1;continue
        raw=row.get('Net Satir Tutari')
        try:
            if raw not in (None,'') and not math.isfinite(float(raw)):nonfinite+=1
        except (TypeError,ValueError):pass
        amount=abs(_number(raw));profit=abs(_number(row.get('Satir Kari')))
        if kind=='sale':totals['salesGross']+=amount;totals['grossProfit']+=profit
        elif kind=='return':totals['salesReturns']+=amount;totals['grossProfit']-=profit
        elif kind=='purchase':totals['purchaseGross']+=amount
        elif kind=='purchase_return':totals['purchaseReturns']+=amount
    totals['netSales']=totals['salesGross']-totals['salesReturns']
    totals['netPurchases']=totals['purchaseGross']-totals['purchaseReturns']
    totals={key:round(value,2) for key,value in totals.items()}
    checks=[
      {'code':'SALES_RECONCILIATION','label':'Net satış = brüt satış − satış iadesi',
       'expected':round(totals['salesGross']-totals['salesReturns'],2),'actual':totals['netSales']},
      {'code':'PURCHASE_RECONCILIATION','label':'Net satın alma = brüt alış − alış iadesi',
       'expected':round(totals['purchaseGross']-totals['purchaseReturns'],2),'actual':totals['netPurchases']},
    ]
    for check in checks:check['difference']=round(check['actual']-check['expected'],2);check['passed']=abs(check['difference'])<.01
    return {'totals':totals,'checks':checks,'passed':all(x['passed'] for x in checks),
      'quality':{'rows':len(rows),'unknownInvoiceKind':unknown,'nonFiniteAmount':nonfinite}}


def delivery_audit(_data):
    from analysis import engine
    started=time.perf_counter()
    with closing(engine.db()) as con:
        batch=con.execute("SELECT id,created FROM batches WHERE kind='movement' ORDER BY created DESC LIMIT 1").fetchone()
        if not batch:return {'status':'no_data'}
        rows=[json.loads(x['converted']) for x in con.execute("SELECT converted FROM records WHERE kind='movement' AND batch_id=?",(batch['id'],))]
    report=reconcile(rows);elapsed=(time.perf_counter()-started)*1000
    return {'status':'ready','sourceBatch':batch['id'],'sourceCreated':batch['created'],**report,
      'performance':{'loadAndReconcileMs':round(elapsed,1),'rowCount':len(rows)},
      'apiContract':{'errors':{key:{'status':value[0],'defaultMessage':value[1]} for key,value in ERROR_CATALOG.items()},
        'pagination':{'defaultLimit':50,'maximumLimit':100}}}
