"""Explainable customer proposals from observed purchases, never automatic orders."""
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import median
from analysis import engine

def recommendations(rows, code, end):
    start=end-timedelta(days=89)
    history=defaultdict(lambda:{'dates':set(),'sales':0.,'returns':0.,'profit':0.,'customers':set(),'name':'','category':''})
    own=defaultdict(lambda:{'dates':set(),'sales':0.,'returns':0.})
    baskets=defaultdict(set)
    for r in rows:
        try: day=datetime.fromisoformat(str(r.get('Fatura Tarihi'))).date()
        except (ValueError,TypeError): continue
        kind=engine.invoice_kind(r)
        if day>end or kind not in ('sale','return'): continue
        p=str(r.get('Malzeme Kodu') or '').strip(); customer=str(r.get('Müsteri Kodu') or '').strip()
        if not p or not customer: continue
        amount=abs(float(r.get('Net Satir Tutari') or 0)); profit=float(r.get('Satir Kari') or 0)
        h=history[p]; h['name']=str(r.get('Malzeme Aciklamasi') or p);h['category']=str(r.get('Malzeme Grubu') or 'Bilinmiyor')
        if day>=start:
            h['sales']+=amount if kind=='sale' else -amount
            h['profit']+=profit if kind=='sale' else -abs(profit)
            if kind=='sale': h['customers'].add(customer);baskets[customer].add(p)
            else: h['returns']+=amount
        if customer==code:
            a=own[p]
            if kind=='sale': a['dates'].add(day);a['sales']+=amount
            else: a['returns']+=amount
    proposals=[]
    def add(p,kind,title,reason,sample,confidence):
        h=history[p]
        proposals.append({'code':p,'name':h['name'],'category':h['category'],'kind':kind,'title':title,'reason':reason,'sample':sample,'confidence':confidence,'caution':'Stok, güncel fiyat ve müşterinin ihtiyacı teklif öncesinde doğrulanmalı.','description':f"{h['name']}: {title}. Müşteriyle ihtiyacı doğrulayın. {reason}"})
    for p,a in own.items():
        dates=sorted(a['dates'])
        if not dates or a['returns']>=a['sales']*.3: continue
        elapsed=(end-dates[-1]).days
        if len(dates)>=3:
            cadence=median((b-a).days for a,b in zip(dates,dates[1:]))
            if cadence>0 and elapsed>=cadence*.8 and elapsed<=cadence*2:
                add(p,'replenish','Tekrar sipariş zamanı',f"Son alım {elapsed} gün önce; gözlenen medyan alım aralığı {cadence:g} gün.",f'{len(dates)} farklı alışveriş günü','Orta')
                continue
        if elapsed>90 and len(dates)>=2:
            add(p,'recover','Kaybolan ürünü geri kazanın',f"Geçmişte tekrar alınmış, son {elapsed} gündür alınmıyor.",f'{len(dates)} alışveriş günü','Orta')
    owned=set(own); categories={history[p]['category'] for p in owned if own[p]['dates']}
    active=baskets.get(code,set()) or owned
    peers=[items for c,items in baskets.items() if c!=code and items&active]
    for p,h in sorted(history.items(),key=lambda kv:kv[1]['sales'],reverse=True):
        if p in owned or h['sales']<=0 or h['profit']<=0 or h['returns']/(h['sales']+h['returns'] or 1)>=.3: continue
        buyers=sum(p in items for items in peers)
        if len(peers)<5 or buyers<3: continue
        same=h['category'] in categories
        add(p,'expand' if same else 'discover','Kategori içinde çeşitlendirin' if same else 'Yeni kategori deneyin',f"Ortak ürün aldığınız {len(peers)} müşterinin {buyers} tanesi bu ürünü de alıyor. {'Mevcut' if same else 'Portföyünüzde bulunmayan'} kategori: {h['category']}.",f'{buyers}/{len(peers)} benzer portföy · son 90 gün','Orta' if buyers/len(peers)>=.5 else 'Düşük')
    # At most three per rationale keeps the offer list useful and balanced.
    counts=defaultdict(int); result=[]
    for p in proposals:
        if counts[p['kind']]<3: result.append(p);counts[p['kind']]+=1
    return {'items':result,'peerCount':len(peers),'method':'Kural tabanlı öneriler; satın alma olasılığı veya kesin talep değildir. Benzer portföy: en az bir ortak ürün, en az 5 diğer müşteri ve aday ürün için en az 3 alıcı. Yüksek iade oranı (%30+) olan ürünler bastırılır. Ürün çeşitlendirme, muadil ürün iddiası değildir.'}
