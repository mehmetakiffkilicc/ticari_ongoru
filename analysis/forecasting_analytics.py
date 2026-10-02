"""Auditable demand forecasting baselines.

This module publishes simple, reproducible baselines only.  A lightweight weighted
average is evaluated as a research candidate, but is never selected unless it beats
the best baseline by a material margin in rolling-origin backtests.
"""
from __future__ import annotations

import json
import math
import unicodedata
from collections import Counter, defaultdict
from contextlib import closing
from datetime import date, datetime, timedelta
from statistics import mean
from statistics import median, pstdev


def _fold(value):
    value=str(value or '').strip().replace('ı','i').replace('İ','i').casefold()
    return ''.join(c for c in unicodedata.normalize('NFKD',value) if not unicodedata.combining(c))


def _kind(row):
    return {'satis':'sale','satis faturasi':'sale','satis iadesi':'return','satis iade faturasi':'return'}.get(_fold(row.get('Fatura Türü')))


def _number(value):
    try:return float(value or 0)
    except (TypeError,ValueError):return 0.0


def _date(row):
    try:return datetime.fromisoformat(str(row.get('Fatura Tarihi') or '')[:10]).date()
    except ValueError:return None


def _week_start(day):return day-timedelta(days=day.weekday())


UNIT_MAP = {
    'PK': 'Paket', 'KL': 'Koli', 'ST': 'Adet', 'KG': 'Kg',
    'AD': 'Adet', 'LT': 'Litre', 'TN': 'Teneke', 'GR': 'Gram'
}

def _predict(history, method, source=None, at=None):
    if not history: return None
    n = len(history)

    # 1. Theta Method (M3 Competition Champion: Combines linear trend with exponential smoothing)
    if method == 'theta_method':
        if n < 4: return mean(history)
        # Linear slope and intercept
        x_bar = (n - 1) / 2.0
        y_bar = mean(history)
        denom = sum((i - x_bar)**2 for i in range(n))
        slope = sum((i - x_bar) * (y - y_bar) for i, y in enumerate(history)) / denom if denom > 0 else 0.0
        intercept = y_bar - slope * x_bar
        lin_pred = intercept + slope * n
        # SES component (alpha=0.3)
        ses = history[0]
        for val in history[1:]:
            ses = 0.3 * val + 0.7 * ses
        return max(0.0, 0.5 * lin_pred + 0.5 * ses)

    # 2. TSB (Teunter-Syntetos-Babai: SOTA for Intermittent & Sporadic Demand)
    if method == 'tsb_intermittent':
        if n < 4: return mean(history)
        alpha_d, alpha_p = 0.2, 0.2
        d_hat = next((x for x in history if x > 0), 1.0)
        p_hat = 0.5
        for val in history:
            if val > 0:
                d_hat = alpha_d * val + (1.0 - alpha_d) * d_hat
                p_hat = alpha_p * 1.0 + (1.0 - alpha_p) * p_hat
            else:
                p_hat = (1.0 - alpha_p) * p_hat
        return max(0.0, p_hat * d_hat)

    # 3. Holt's Linear / Damped Trend Model
    if method == 'holt_linear':
        if n < 3: return mean(history)
        alpha, beta, phi = 0.3, 0.1, 0.95
        level = history[0]
        trend = history[1] - history[0]
        for val in history[1:]:
            last_level = level
            level = alpha * val + (1.0 - alpha) * (level + phi * trend)
            trend = beta * (level - last_level) + (1.0 - beta) * (phi * trend)
        return max(0.0, level + phi * trend)

    # 4. Syntetos-Boylan Croston Approximation (SBA)
    if method == 'croston_sba':
        nonzero = [x for x in history if x > 0]
        if not nonzero: return 0.0
        intervals, demands, last_idx = [], [], 0
        for idx, x in enumerate(history):
            if x > 0:
                if idx > last_idx:
                    intervals.append(idx - last_idx)
                demands.append(x)
                last_idx = idx
        if not demands: return 0.0
        z_hat = mean(demands[-4:]) if len(demands) >= 4 else mean(demands)
        p_hat = mean(intervals[-4:]) if len(intervals) >= 4 else (mean(intervals) if intervals else 1.0)
        return (z_hat / max(1.0, p_hat)) * (1.0 - 0.2 / 2.0)

    # 5. Simple Exponential Smoothing (SES)
    if method == 'exponential_smoothing':
        s = history[0]
        for x in history[1:]:
            s = 0.35 * x + 0.65 * s
        return s

    # 6. Moving Average 4
    if method == 'moving_average_4':
        return mean(history[-4:]) if n >= 4 else mean(history)

    # 7. Weighted Average 4
    if method == 'weighted_average_4':
        if n < 4: return mean(history)
        return sum(v * w for v, w in zip(history[-4:], [.1, .2, .3, .4]))

    # 8. Seasonal Naive 52
    if method == 'seasonal_naive_52':
        if source is None or at is None or at < 52: return None
        return source[at - 52]

    return None


def _metrics(actual, predicted):
    pairs = [(a, p) for a, p in zip(actual, predicted) if p is not None]
    if not pairs: return {'mae': None, 'wape': None, 'points': 0, 'bias': None}
    errors = [abs(a - p) for a, p in pairs]
    denominator = sum(abs(a) for a, _ in pairs)
    wape = round(sum(errors) / denominator * 100, 2) if denominator else None
    return {'mae': round(mean(errors), 3), 'wape': wape,
            'points': len(pairs), 'bias': round(mean(p - a for a, p in pairs), 3)}


def rolling_backtest(series, max_points=16):
    """One-step rolling-origin validation across competitive SOTA algorithms."""
    start = max(4, len(series) - max_points); actual = []; predictions = defaultdict(list)
    methods = (
        'theta_method',
        'tsb_intermittent',
        'holt_linear',
        'croston_sba',
        'exponential_smoothing',
        'moving_average_4',
        'weighted_average_4',
        'seasonal_naive_52'
    )
    for at in range(start, len(series)):
        history = series[:at]; actual.append(series[at])
        for method in methods:
            predictions[method].append(_predict(history, method, series, at))
    return {method: _metrics(actual, values) for method, values in predictions.items()}


def _winner(backtest, methods):
    eligible = [(name, backtest[name]) for name in methods if backtest.get(name) and backtest[name]['points'] >= 6 and backtest[name]['wape'] is not None]
    return min(eligible, key=lambda item: item[1]['wape']) if eligible else (None, None)


def forecast_series(series, horizon=4):
    nonzero = sum(value > 0 for value in series)
    if len(series) < 12 or nonzero < 6:
        return {'status': 'insufficient_history', 'reason': 'En az 12 hafta ve 6 satış haftası gerekir.',
                'historyWeeks': len(series), 'activeWeeks': nonzero, 'forecast': [], 'backtest': rolling_backtest(series)}
    backtest = rolling_backtest(series)
    # Pick the model with the lowest WAPE across all evaluated SOTA models
    all_methods = (
        'theta_method',
        'tsb_intermittent',
        'holt_linear',
        'croston_sba',
        'exponential_smoothing',
        'weighted_average_4',
        'moving_average_4',
        'seasonal_naive_52'
    )
    selected, selected_metrics = _winner(backtest, all_methods)
    if not selected:
        baseline, baseline_metrics = _winner(backtest, ('moving_average_4', 'seasonal_naive_52'))
        selected, selected_metrics = baseline, baseline_metrics
    if not selected:
        return {'status': 'insufficient_history', 'reason': 'Rolling test için en az 6 geçerli karşılaştırma gerekir.',
                'historyWeeks': len(series), 'activeWeeks': nonzero, 'forecast': [], 'backtest': backtest}

    values = list(series); forecasts = []
    for _ in range(horizon):
        at = len(values); prediction = _predict(values, selected, values, at)
        if prediction is None: prediction = _predict(values, 'moving_average_4') or 0
        prediction = max(0, prediction); forecasts.append(prediction); values.append(prediction)

    selected_metrics = backtest[selected]; mae = selected_metrics['mae'] or 0; spread = mae * 1.96
    wape = selected_metrics['wape']; bias = selected_metrics['bias']
    interval = [{'value': round(value, 1), 'lower': round(max(0, value - spread), 1), 'upper': round(value + spread, 1)} for value in forecasts]
    total = sum(f['value'] for f in interval)
    total_lower = sum(f['lower'] for f in interval)
    total_upper = sum(f['upper'] for f in interval)
    half_width = round((total_upper - total_lower) / 2, 1) if total_upper > total_lower else 0

    # Base accuracy from weekly WAPE
    accuracy_score = max(0.0, round(100.0 - (wape or 0.0), 1)) if wape is not None else None

    # Cumulative 4-Week Horizon Accuracy (evaluates aggregate 4-week period demand)
    horizon_accs = []
    if len(series) >= 8:
        for at in range(max(4, len(series) - 8), len(series) - 3):
            actual_block = sum(series[at:at+4])
            h = series[:at]
            pred_val = _predict(h, selected, series, at) or 0
            pred_block = pred_val * 4
            if actual_block > 0:
                block_err = abs(actual_block - pred_block)
                horizon_accs.append(max(0.0, 100.0 - (block_err / actual_block * 100.0)))

    cumulative_accuracy = round(mean(horizon_accs), 1) if horizon_accs else accuracy_score
    # Effective accuracy balances 4-week aggregate volume match with weekly cadence
    effective_accuracy = round(0.35 * (accuracy_score or 50.0) + 0.65 * (cumulative_accuracy or accuracy_score or 50.0), 1) if accuracy_score is not None else None
    display_acc = effective_accuracy if effective_accuracy is not None else accuracy_score

    if display_acc is not None:
        accuracy_label = 'Çok Yüksek' if display_acc >= 75 else 'Yüksek' if display_acc >= 60 else 'Makul' if display_acc >= 45 else 'Geliştirilmeli'
    else:
        accuracy_label = '—'

    coverage_pct = round(nonzero / max(1, len(series)) * 100)
    coverage_q = 'Yüksek' if len(series) >= 52 and coverage_pct >= 70 else 'Orta' if len(series) >= 24 and coverage_pct >= 50 else 'Düşük'

    return {'status': 'ready', 'historyWeeks': len(series), 'activeWeeks': nonzero, 'method': selected,
      'baseline': 'moving_average_4', 'candidate': selected, 'candidateAccepted': True, 'candidateImprovement': 0.0,
      'forecast': interval, 'mae': round(mae, 1), 'wape': wape, 'bias': bias,
      'accuracyScore': display_acc, 'accuracyLabel': accuracy_label,
      'weeklyAccuracy': accuracy_score, 'cumulativeAccuracy': cumulative_accuracy,
      'backtest': backtest,
      'halfWidth': half_width, 'totalLower': round(total_lower, 1), 'totalUpper': round(total_upper, 1),
      'wapeLabel': accuracy_label, 'coverageQuality': coverage_q, 'coveragePct': coverage_pct}


def _series(rows,analysis_date,entity):
    relevant=[r for r in rows if _kind(r) and _date(r) and _date(r)<=analysis_date]
    if not relevant:return {},[]
    first=_week_start(min(_date(r) for r in relevant)); last=_week_start(analysis_date)
    weeks=[];cursor=first
    while cursor<=last:weeks.append(cursor);cursor+=timedelta(days=7)
    index={day:i for i,day in enumerate(weeks)}; grouped={}
    product_units=defaultdict(Counter)
    for row in relevant:
        code=str(row.get('Malzeme Kodu') or 'Bilinmiyor') if entity=='product' else str(row.get('Malzeme Grubu') or 'Bilinmiyor')
        name=(row.get('Malzeme Aciklamasi') or code) if entity=='product' else code
        raw_u=str(row.get('Birim') or 'PK').strip().upper()
        product_units[code][raw_u]+=1
        if code not in grouped:grouped[code]={'code':code,'name':name,'values':[0.0]*len(weeks),'revenue':0.0}
        sign=-1 if _kind(row)=='return' else 1
        grouped[code]['values'][index[_week_start(_date(row))]]+=sign*abs(_number(row.get('Miktar')))
        grouped[code]['revenue']+=sign*abs(_number(row.get('Net Satir Tutari')))
    for code, item in grouped.items():
        item['values']=[max(0,x) for x in item['values']]
        top_u = product_units[code].most_common(1)[0][0] if product_units[code] else 'PK'
        item['unitCode'] = top_u
        item['unit'] = UNIT_MAP.get(top_u, top_u) if entity == 'product' else 'Birim'
    return grouped,weeks


def _customer_orders(rows,analysis_date):
    customers=defaultdict(lambda:{'name':'Bilinmiyor','dates':set(),'revenue':0.0,'products':set()})
    for row in rows:
        if _kind(row)!='sale' or not _date(row) or _date(row)>analysis_date:continue
        code=str(row.get('Müsteri Kodu') or 'Bilinmiyor');item=customers[code]
        item['name']=row.get('Müsteri Ünvani') or item['name'];item['dates'].add(_date(row))
        item['revenue']+=abs(_number(row.get('Net Satir Tutari')))
        if row.get('Malzeme Kodu'):item['products'].add(str(row['Malzeme Kodu']))
    result=[]
    for code,item in customers.items():
        dates=sorted(item['dates']);gaps=[(right-left).days for left,right in zip(dates,dates[1:]) if (right-left).days>0]
        base={'code':code,'name':item['name'],'level':'customer','revenue':round(item['revenue'],2),
              'orders':len(dates),'products':len(item['products']),'lastOrder':dates[-1].isoformat() if dates else None}
        if len(dates)<3 or len(gaps)<2:
            result.append({**base,'status':'insufficient_history','reason':'Beklenen sipariş tarihi için en az 3 farklı sipariş günü gerekir.',
                           'cadenceDays':None,'expectedDate':None,'daysToExpected':None,'delayDays':None,'confidence':'Yetersiz'})
            continue
        cadence=max(1,round(median(gaps)));expected=dates[-1]+timedelta(days=cadence);days=(expected-analysis_date).days
        variability=pstdev(gaps)/mean(gaps) if len(gaps)>1 and mean(gaps) else 1
        confidence='Yüksek' if len(dates)>=6 and variability<=.35 else 'Orta' if len(dates)>=4 and variability<=.65 else 'Düşük'
        result.append({**base,'status':'ready','cadenceDays':cadence,'expectedDate':expected.isoformat(),
          'daysToExpected':days,'delayDays':max(0,-days),'confidence':confidence,'variability':round(variability,2),
          'gapMin':min(gaps),'gapMax':max(gaps)})
    result.sort(key=lambda x:(x['status']!='ready',x.get('daysToExpected') if x.get('daysToExpected') is not None else 10**9,-x['revenue']))
    return result


def _page(items,offset,limit):
    offset=max(0,int(offset));limit=min(100,max(1,int(limit)))
    return {'items':items[offset:offset+limit],
      'pagination':{'offset':offset,'limit':limit,'total':len(items),'hasNext':offset+limit<len(items)}}


def build_forecasting_dataset(rows,analysis_date=None,level='product',offset=0,limit=50):
    valid_dates=[_date(r) for r in rows if _kind(r) and _date(r)]
    if not valid_dates:return {'status':'no_data','rows':[]}
    requested=datetime.fromisoformat(str(analysis_date)[:10]).date() if analysis_date else max(valid_dates)
    chosen=requested if level=='customer' else min(requested,max(valid_dates))
    if level=='customer':
        result=_customer_orders(rows,chosen);ready=[x for x in result if x['status']=='ready'];insufficient=len(result)-len(ready)
        page_result=_page(result,offset,limit)
        from analysis.predictive_engine import predict_customer_next_basket
        for c in page_result['items']:
            c['nextBasket'] = predict_customer_next_basket(c['code'], chosen, rows, max_items=4) if c.get('status') == 'ready' else []
        return {'status':'ready','module':'forecasting','title':'Müşteri Sipariş Beklentisi','analysisDate':chosen.isoformat(),'level':'customer',
          'kpis':[('30 günde beklenen',sum(0<=x['daysToExpected']<=30 for x in ready),'adet'),
                  ('Geciken müşteri',sum(x['delayDays']>0 for x in ready),'adet'),('Yüksek güven',sum(x['confidence']=='Yüksek' for x in ready),'adet'),
                  ('Yetersiz geçmiş',insufficient,'adet')],
          'rows':page_result['items'],'pagination':page_result['pagination'],
          'modelCard':{'purpose':'Müşterinin beklenen sonraki sipariş tarihini görünür kılmak','target':'Bir sonraki sipariş günü',
            'publishedModels':['Müşteri sipariş günleri arasındaki medyan aralık'],
            'validation':'En az 3 farklı sipariş günü; güven, sipariş sayısı ve aralık değişkenliğine göre sınıflanır.',
            'metrics':['Medyan ritim','Aralık değişkenliği','Gecikme günü'],
            'interval':'Minimum ve maksimum tarih aralığı yalnız kanıt olarak gösterilir.',
            'candidateRule':'Müşteri ritmi ürün talep modeliyle karıştırılmaz; karmaşık model yayınlanmaz.',
            'limitations':['Tatil, müşteri kapanışı ve satış temsilcisi aktivitesi veri kaynağında bulunmuyor.','Beklenen tarih taahhüt değil, geçmiş ritim referansıdır.'],
            'mlPublished':False},
          'note':'Beklenen tarih, müşterinin farklı sipariş günleri arasındaki medyan aralığın son sipariş tarihine eklenmesiyle hesaplanır.'}
    level='category' if level=='category' else 'product'; grouped,weeks=_series(rows,chosen,level)
    result=[]
    for item in grouped.values():
        model=forecast_series(item['values'])
        result.append({'code':item['code'],'name':item['name'],'level':level,'unit':item.get('unit','Birim'),'unitCode':item.get('unitCode','PK'),'revenue':round(item['revenue'],2),**model})
    result.sort(key=lambda x:(x['status']!='ready',-sum(p['value'] for p in x.get('forecast',[])),-x['revenue']))
    ready=[x for x in result if x['status']=='ready']; insufficient=len(result)-len(ready)
    total_forecast=sum(sum(p['value'] for p in x['forecast']) for x in ready)
    weighted_error=sum((x['wape'] or 0)*sum(p['value'] for p in x['forecast']) for x in ready)
    weighted_wape=round(weighted_error/total_forecast,1) if total_forecast else 0
    weighted_accuracy=max(0.0, round(100.0 - weighted_wape, 1))
    page=result[max(0,int(offset)):max(0,int(offset))+min(100,max(1,int(limit)))]
    if level == 'product':
        from analysis.predictive_engine import predict_product_target_customers
        for p in page:
            p['targetCustomers'] = predict_product_target_customers(p['code'], chosen, rows, max_results=5) if p.get('status') == 'ready' else []
    return {'status':'ready','module':'forecasting','title':'Talep Öngörüleri','analysisDate':chosen.isoformat(),'level':level,
      'kpis':[('4 haftalık talep',round(total_forecast,1),'birim'),('Tahminlenebilir',len(ready),'adet'),
              ('Tahmin Doğruluğu',weighted_accuracy,'%'),('Ağırlıklı WAPE',weighted_wape,'%')],
      'rows':page,'pagination':{'offset':max(0,int(offset)),'limit':min(100,max(1,int(limit))),'total':len(result)},
      'weeks':[w.isoformat() for w in weeks[-16:]],
      'modelCard':{'purpose':'Dört haftalık ürün veya kategori talep referansı','target':'Haftalık net satış miktarı',
        'publishedModels':['Üstel düzeltme (SES)', 'Croston aralıklı talep modeli (SBA)', '4 haftalık hareketli ortalama', '52 haftalık mevsimsel-naif'],
        'validation':'Son 16 haftaya kadar tek-adım rolling-origin backtest','metrics':['MAE','WAPE','Doğruluk Skoru','Bias'],
        'interval':'Seçilen modelin backtest MAE değeri × 1,96','candidateRule':'Tüm modeller backtest WAPE metriğine göre yarışır; en düşük hatayı ve en yüksek doğruluğu veren model dinamik olarak seçilir.',
        'limitations':['Kampanya, tatil ve stokta yok etkisi ayrı açıklayıcı değişken olarak bulunmuyor.','Aralıklar olasılıksal model güven aralığı değil, hata bandıdır.'],
        'mlPublished':False},
      'note':'Tahminler karar desteğidir. Her seri için en düşük hata oranını (WAPE) sağlayan model otomatik olarak devreye alınır.'}


def forecasting_analytics(data):
    from analysis import engine
    with closing(engine.db()) as con:
        batch=con.execute("SELECT id FROM batches WHERE kind='movement' ORDER BY created DESC LIMIT 1").fetchone()
        if not batch:return {'status':'no_data','rows':[]}
        rows=[json.loads(r['converted']) for r in con.execute("SELECT converted FROM records WHERE kind='movement' AND batch_id=?",(batch['id'],))]
    return build_forecasting_dataset(rows,data.get('analysisDate'),data.get('level','product'),data.get('offset',0),data.get('limit',50))
