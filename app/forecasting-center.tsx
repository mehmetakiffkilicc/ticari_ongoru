'use client';

import {useEffect,useMemo,useState} from 'react';
import {AlertTriangle,BarChart3,ChevronLeft,ChevronRight,Info,Search,ShieldCheck,Sparkles,ShoppingBag,Users,ArrowRight} from 'lucide-react';
import type {PredictiveBasketItem, TargetCustomerItem} from './decision-types';
import './forecasting-center.css';
import './forecasting-customer.css';
import './predictive.css';

type Point={value:number;lower:number;upper:number};
type Metrics={mae:number|null;wape:number|null;points:number;bias:number|null};
type ForecastRow={code:string;name:string;level:'product'|'category';unit?:string;unitCode?:string;revenue:number;status:'ready'|'insufficient_history';reason?:string;historyWeeks:number;activeWeeks:number;method?:string;baseline?:string;candidate?:string;candidateAccepted?:boolean;candidateImprovement?:number;forecast:Point[];mae?:number;wape?:number;bias?:number;accuracyScore?:number;accuracyLabel?:string;halfWidth?:number;totalLower?:number;totalUpper?:number;coverageQuality?:string;coveragePct?:number;wapeLabel?:string;backtest:Record<string,Metrics>;targetCustomers?:TargetCustomerItem[]};
type CustomerRow={code:string;name:string;level:'customer';revenue:number;status:'ready'|'insufficient_history';reason?:string;orders:number;products:number;lastOrder:string|null;cadenceDays:number|null;expectedDate:string|null;daysToExpected:number|null;delayDays:number|null;confidence:string;variability?:number;gapMin?:number;gapMax?:number;nextBasket?:PredictiveBasketItem[]};
type Data={status:string;title:string;analysisDate:string;level:'product'|'category'|'customer';kpis:[string,number,string][];rows:(ForecastRow|CustomerRow)[];pagination:{offset:number;limit:number;total:number};modelCard:{purpose:string;target:string;publishedModels:string[];validation:string;metrics:string[];interval:string;candidateRule:string;limitations:string[];mlPublished:boolean};note:string};
const methodName:Record<string,string>={
  theta_method:'Theta yöntemi (M3 Şampiyonu)',
  tsb_intermittent:'TSB aralıklı talep modeli',
  holt_linear:'Holt sönümlü trend modeli',
  croston_sba:'Croston aralıklı talep modeli (SBA)',
  exponential_smoothing:'Üstel düzeltme (SES)',
  moving_average_4:'4 haftalık hareketli ortalama',
  weighted_average_4:'Ağırlıklı hareketli ortalama',
  seasonal_naive_52:'52 haftalık mevsimsel-naif'
};
const fmt=(value:number,unit?:string)=>unit==='%'?`%${value.toLocaleString('tr-TR',{maximumFractionDigits:1})}`:unit==='EUR'?value.toLocaleString('de-DE',{style:'currency',currency:'EUR',maximumFractionDigits:0}):value.toLocaleString('tr-TR',{maximumFractionDigits:1});

function ModelExplainer({ onClose }: { onClose: () => void }) {
  const signals = [
    { badge: 'Döngüsü Geldi', color: '#1e3a5f', icon: '\u21bb', title: 'Tüketim Döngüsü', formula: 'döngü_oranı = geçen_gün ÷ medyan_sipariş_aralığı', detail: 'Geçmiş siparişler arasındaki medyan aralık hesaplanır. Geçen süre bu aralığın %75-220\'i arasında ise ürün “döngüsü gelmiş” sayılır.', example: 'Son alım 32 gün önce, ritim 28 gün → oran 1.14 → ~%88 olasılık', prob: 'P = min(96, 65 + 25 × oran + 10 × frekans)' },
    { badge: 'Rutin Sepet', color: '#2e7d32', icon: '\u2713', title: 'Sepet Demirbaşı', formula: 'frekans = ürünlü fatura ÷ toplam fatura', detail: 'Faturaların %40+ unda yer alan ürünler demirbaş sepet ürünür. Yakın sipariş yoğunluğu (recency weighting) ekstra puan kaçırır.', example: 'Frekans %65, son 6 aydaki siparişler dahil → ~%79 olasılık', prob: 'P = min(92, 55 + 25 × frekans + 10 × yakın_oran)' },
    { badge: 'Çapraz Satış', color: '#6a1b9a', icon: '\u2194', title: 'Birliktelik Kuralı', formula: 'Lift = Güven ÷ B\'nin pazar payı', detail: 'Müşterinin en sık aldığı 4 ürün referans alınır. Bu ürünlerle Lift ≥1.25, Güven ≥0.20 olan ürünler önerilir.', example: 'A ile B %60 birlikte, Lift=2.8 → ~%77 olasılık', prob: 'P = min(85, 45 + güven×35 + min(15, lift×4))' },
    { badge: 'Kayıp Ürün Adayı', color: '#b71c1c', icon: '\u26a0', title: 'Kayıp Tespit', formula: 'döngü_oranı > 2.2', detail: 'Düzenli alınan ama 2.2× beklenen süreyi aşan ürünler. Rakip ürün kaybı veya ihtiyaç değişimi sinyali.', example: 'Ritim 28 gün, geçen 90 gün (oran 3.2) → temas fırsatı', prob: 'P = min(78, 50 + 25 × frekans)' },
  ];
  return (
    <div className="model-explainer" role="dialog" aria-modal="true" aria-label="Tahmini Sepet Metodolojisi">
      <div className="model-explainer-backdrop" onClick={onClose} />
      <div className="model-explainer-panel">
        <header className="model-explainer-header">
          <div>
            <h3>Tahmini Sonraki Sepet — Algoritma</h3>
            <p>Dört sinyal birleştirilerek müşterinin bir sonraki siparişinde yer alması en olası ürünler hesaplanır.</p>
          </div>
          <button className="model-explainer-close" onClick={onClose} aria-label="Kapat">×</button>
        </header>
        <div className="model-explainer-signals">
          {signals.map(s => (
            <div key={s.badge} className="model-signal-card">
              <div className="model-signal-header" style={{ borderLeftColor: s.color }}>
                <span className="model-signal-badge" style={{ background: s.color }}>{s.badge}</span>
                <strong>{s.title}</strong>
              </div>
              <div className="model-signal-body">
                <div className="model-signal-formula">
                  <span>Formül:</span><code>{s.formula}</code>
                </div>
                <p>{s.detail}</p>
                <div className="model-signal-example">
                  <span>Örnek:</span>{s.example}
                </div>
                <div className="model-signal-prob">
                  <span>Olasılık hesabı:</span><code>{s.prob}</code>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="model-explainer-notes">
          <strong>Sıralama Mantığı:</strong> Döngüsü Geldi › Rutin Sepet › Çapraz Satış › Kayıp Ürün. Eşit sinyal varsa olasılık puanı belirler.
          <br /><strong>Kısıtlar:</strong> Iadeler, kampanyalar ve dış fiyat değişimleri modele dahil edilmez. Yeni ürünler önerilemez. En az 2 sipariş kaydı gerekir.
        </div>
      </div>
    </div>
  );
}

export default function ForecastingCenter({analysisDate,onOpenProduct,onNavigate}:{analysisDate:string;onOpenProduct?:(code:string)=>void;onNavigate?:(target:string,id?:string)=>void}){
  const [level,setLevel]=useState<'product'|'category'|'customer'>('product'),[offset,setOffset]=useState(0),[data,setData]=useState<Data|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState(''),[query,setQuery]=useState(''),[expanded,setExpanded]=useState<string|null>(null);
  const [showModel, setShowModel] = useState(false);
  useEffect(()=>{let live=true;setLoading(true);setError('');setData(null);setExpanded(null);fetch('/api/data',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'forecasting_analytics',analysisDate,level,offset,limit:50})}).then(r=>r.json()).then(r=>{if(!r.ok)throw new Error(r.error||'Tahmin hazırlanamadı.');if(live)setData(r.data)}).catch(e=>live&&setError(e.message)).finally(()=>live&&setLoading(false));return()=>{live=false}},[analysisDate,level,offset]);
  const rows=useMemo(()=>{const q=query.toLocaleLowerCase('tr-TR');return data?.rows.filter(r=>!q||`${r.name} ${r.code}`.toLocaleLowerCase('tr-TR').includes(q))||[]},[data,query]);
  if(error)return <section className="fc-state error"><AlertTriangle/><div><strong>Öngörü hazırlanamadı</strong><p>{error}</p></div></section>;
  return <section className="fc-workspace" aria-labelledby="forecast-title">
    {showModel && <ModelExplainer onClose={() => setShowModel(false)} />}
    <header className="fc-header"><div><span className="fc-icon"><BarChart3/></span><div><h2 id="forecast-title">Talep Öngörüleri</h2><p>Geçmiş tüketim döngüleri, sepet birliktelikleri ve sepet tahminleriyle yapay zekâ destekli öngörüler.</p></div></div><span className="fc-trust"><ShieldCheck size={15}/> Doğrulanmış Yöntem & Açıklanabilir AI</span></header>
    {loading||!data?<ForecastSkeleton/>:<>
      <div className="fc-kpis">{data.kpis.map(([label,value,unit])=><div key={label}><span>{label}</span><strong>{fmt(value,unit)}</strong><small>{label==='Ağırlıklı WAPE'?'Daha düşük daha iyi':unit}</small></div>)}</div>
      <div className="fc-toolbar">
        <div className="fc-segment" role="tablist"><button className={level==='product'?'active':''} onClick={()=>{setLevel('product');setOffset(0)}}>Ürün</button><button className={level==='category'?'active':''} onClick={()=>{setLevel('category');setOffset(0)}}>Kategori</button><button className={level==='customer'?'active':''} onClick={()=>{setLevel('customer');setOffset(0)}}>Müşteri</button></div>
        <label><Search/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder={`${level==='product'?'Ürün':level==='category'?'Kategori':'Müşteri'} ara`}/></label>
        {level === 'customer' && <button className="model-info-btn" onClick={() => setShowModel(true)}>Tahmin algoritması hakkında</button>}
        <span>{data.pagination.total} seri</span>
      </div>
      <div className="fc-table-wrap"><table className="fc-table"><thead>{data.level==='customer'?<tr><th>Müşteri</th><th>Beklenen sipariş tarihi</th><th>Durum</th><th>Medyan sipariş ritmi</th><th>Tahmini Sonraki Sepet</th><th>Tahmin güveni</th><th/></tr>:<tr><th>{data.level==='product'?'Ürün':'Kategori'}</th><th>Sonraki 4 Hafta Talebi<small style={{display:'block',fontWeight:400,fontSize:'10px',color:'#94a3b8',marginTop:'2px'}}>Temel birim · 4 hafta toplamı</small></th><th>Güven Aralığı (%~90 CI)<small style={{display:'block',fontWeight:400,fontSize:'10px',color:'#94a3b8',marginTop:'2px'}}>±birim olarak tahmin belirsizliği</small></th><th>Tahmin Doğruluğu<small style={{display:'block',fontWeight:400,fontSize:'10px',color:'#94a3b8',marginTop:'2px'}}>WAPE · MAE (backtest sonucu)</small></th><th>{data.level==='product'?'Hedef Alıcılar':'Model'}</th><th>Veri Kalitesi<small style={{display:'block',fontWeight:400,fontSize:'10px',color:'#94a3b8',marginTop:'2px'}}>Aktiflik oranı ve geçmiş genişliği</small></th><th/></tr>}</thead><tbody>{data.level==='customer'?(rows as CustomerRow[]).map(row=><CustomerLine key={row.code} row={row} expanded={expanded===row.code} onExpand={()=>setExpanded(expanded===row.code?null:row.code)} onAction={()=>onNavigate?.('case_actions')}/>):(rows as ForecastRow[]).map(row=><ForecastLine key={row.code} row={row} expanded={expanded===row.code} onExpand={()=>setExpanded(expanded===row.code?null:row.code)} onOpenProduct={data.level==='product'?onOpenProduct:undefined} onAction={()=>onNavigate?.('case_actions')}/>)}</tbody></table></div>
      <div className="fc-pagination"><span>{data.pagination.offset+1}–{Math.min(data.pagination.offset+data.pagination.limit,data.pagination.total)} / {data.pagination.total}</span><button disabled={!offset} onClick={()=>setOffset(Math.max(0,offset-50))}><ChevronLeft/> Önceki</button><button disabled={offset+50>=data.pagination.total} onClick={()=>setOffset(offset+50)}>Sonraki <ChevronRight/></button></div>
      <details className="fc-model-card"><summary><Info/> Hesaplama yöntemi ve sınırlar <ChevronRight/></summary><div className="fc-model-content"><dl><div><dt>Amaç</dt><dd>{data.modelCard.purpose}</dd></div><div><dt>Hedef</dt><dd>{data.modelCard.target}</dd></div><div><dt>Doğrulama</dt><dd>{data.modelCard.validation}</dd></div><div><dt>Olası aralık</dt><dd>{data.modelCard.interval}</dd></div><div><dt>Daha iyi yöntem seçme kuralı</dt><dd>{data.modelCard.candidateRule}</dd></div></dl><div><strong>Kullanılan yöntemler</strong><ul>{data.modelCard.publishedModels.map(x=><li key={x}>{x}</li>)}</ul><strong>Sınırlamalar</strong><ul>{data.modelCard.limitations.map(x=><li key={x}>{x}</li>)}</ul></div></div></details>
    </>}
  </section>
}

function CustomerLine({row,expanded,onExpand,onAction}:{row:CustomerRow;expanded:boolean;onExpand:()=>void;onAction?:()=>void}){
  const expected=row.expectedDate?new Date(`${row.expectedDate}T12:00:00`).toLocaleDateString('tr-TR'):'—';
  const last=row.lastOrder?new Date(`${row.lastOrder}T12:00:00`).toLocaleDateString('tr-TR'):'—';
  const confidence=row.confidence||'Yetersiz';
  const state=row.status!=='ready'?'Yetersiz geçmiş':Number(row.delayDays)>0?`${row.delayDays} gün gecikti`:row.daysToExpected===0?'Bugün bekleniyor':`${row.daysToExpected} gün sonra`;
  const basket = row.nextBasket || [];

  return <>
    <tr className={row.status!=='ready'?'insufficient':''}>
      <td><span className="fc-name"><strong>{row.name}</strong><small>{row.code}</small></span></td>
      <td><strong>{expected}</strong><small>Son sipariş {last}</small></td>
      <td><span className={`fc-status ${Number(row.delayDays)>0?'late':''}`}>{state}</span></td>
      <td className="numeric">{row.cadenceDays==null?'—':`${row.cadenceDays} gün`}<small>{row.gapMin!=null&&row.gapMax!=null?`${row.gapMin}–${row.gapMax} gün aralık`:'—'}</small></td>
      <td>
        {basket.length > 0 ? (
          <div style={{display:'flex',gap:'4px',flexWrap:'wrap',maxWidth:'240px'}}>
            {basket.slice(0, 2).map(b => (
              <span key={b.code} style={{fontSize:'10px',padding:'2px 6px',background:'#eff6ff',border:'1px solid #bfdbfe',borderRadius:'4px',color:'#1e40af',whiteSpace:'nowrap'}}>
                {b.name.split(' ')[0]} (%{b.probability})
              </span>
            ))}
            {basket.length > 2 && <span style={{fontSize:'10px',color:'#64748b'}}>+{basket.length - 2} ürün</span>}
          </div>
        ) : <span className="fc-muted">—</span>}
      </td>
      <td><span className={`fc-confidence ${confidence.toLocaleLowerCase('tr-TR')}`}>{confidence}</span></td>
      <td><button className="fc-expand" onClick={onExpand} aria-expanded={expanded} aria-label={`${row.name} tahmin açıklamasını ${expanded?'kapat':'aç'}`}><ChevronRight/></button></td>
    </tr>
    {expanded && <tr className="fc-detail-row"><td colSpan={7}>
      <div style={{display:'flex',flexDirection:'column',gap:'14px',width:'100%'}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',flexWrap:'wrap',gap:'10px'}}>
          <div>
            <p style={{margin:'0 0 4px 0'}}>
              {row.status==='ready'?`Beklenen tarih, ${row.cadenceDays} günlük medyan ritmin son sipariş tarihine eklenmesiyle hesaplandı. Aralık değişkenliği ${row.variability}.`:row.reason}
            </p>
            <div style={{display:'flex',gap:'14px',marginTop:'6px',fontSize:'12px',color:'#475569'}}>
              <span><strong>Güven:</strong> {confidence}</span>
              <span><strong>Sipariş Sayısı:</strong> {row.orders}</span>
              <span><strong>Toplam Ciro:</strong> {fmt(row.revenue,'EUR')}</span>
            </div>
          </div>
          {onAction && <button className="predictive-btn-inject" onClick={onAction}>
            Aksiyon Merkezinde Yönet <ArrowRight size={13}/>
          </button>}
        </div>

        {basket.length > 0 && <div className="predictive-box" style={{margin:'0',padding:'14px'}}>
          <div className="predictive-box-header">
            <h4><ShoppingBag size={15}/>Müşterinin Sıradaki Ziyaretinde Alması Beklenen Ürünler (Tahmini Sepet)</h4>
            <span>{basket.length} Ürün Öngörüldü</span>
          </div>
          <div className="predictive-grid">
            {basket.map(item => (
              <div key={item.code} className="predictive-item-card">
                <div className="predictive-item-top">
                  <span className="predictive-item-name">{item.name}</span>
                  <span className={`predictive-badge ${item.badge==='Döngüsü Geldi'?'badge-cycle':item.badge==='Rutin Sepet'?'badge-staple':item.badge==='Çapraz Satış'?'badge-cross':'badge-lost'}`}>{item.badge}</span>
                </div>
                <div className="predictive-meter">
                  <div className="predictive-meter-bar">
                    <div className="predictive-meter-fill" style={{width:`${Math.min(100, item.probability)}%`}}/>
                  </div>
                  <span>%{item.probability}</span>
                </div>
                <p className="predictive-reason">{item.reason}</p>
              </div>
            ))}
          </div>
        </div>}
      </div>
    </td></tr>}
  </>;
}

function ForecastLine({row,expanded,onExpand,onOpenProduct,onAction}:{row:ForecastRow;expanded:boolean;onExpand:()=>void;onOpenProduct?:((code:string)=>void);onAction?:()=>void}){
  const points=Array.isArray(row.forecast)?row.forecast:[];
  const total=points.reduce((s,x)=>s+x.value,0);
  const unitLabel=row.unit||(row.level==='product'?'Paket':'Birim');
  const r=row as ForecastRow & {halfWidth?:number;totalLower?:number;totalUpper?:number;wapeLabel?:string;coverageQuality?:string;coveragePct?:number};
  const halfWidth=r.halfWidth??Math.round((points.reduce((s,x)=>s+x.upper,0)-points.reduce((s,x)=>s+x.lower,0))/2);
  const totalLower=r.totalLower??points.reduce((s,x)=>s+x.lower,0);
  const totalUpper=r.totalUpper??points.reduce((s,x)=>s+x.upper,0);

  // Accuracy calculation: 100 - WAPE
  const accuracy=row.accuracyScore??(row.wape!=null?Math.max(0,Math.round(100-row.wape)):null);
  const accGrade=accuracy==null?'—':accuracy>=75?'Çok Yüksek':accuracy>=60?'Yüksek':accuracy>=45?'Makul':'Geliştirilmeli';
  const accColor=accuracy==null?'#64748b':accuracy>=75?'#15803d':accuracy>=60?'#0369a1':accuracy>=45?'#b45309':'#b91c1c';
  const accBg=accuracy==null?'#f1f5f9':accuracy>=75?'#dcfce7':accuracy>=60?'#e0f2fe':accuracy>=45?'#fef3c7':'#fee2e2';

  const coverageQuality=r.coverageQuality??'—';
  const coveragePct=r.coveragePct??Math.round((row.activeWeeks/Math.max(1,row.historyWeeks))*100);
  const covColor=coverageQuality==='Yüksek'?'#1e40af':coverageQuality==='Orta'?'#92400e':'#6b7280';
  const targets=row.targetCustomers||[];

  return <>
    <tr className={row.status!=='ready'?'insufficient':''}>
      <td><button className="fc-name" onClick={()=>onOpenProduct?.(row.code)} disabled={!onOpenProduct}><strong>{row.name}</strong><small>{row.code}</small></button></td>

      {/* SÜTUN 2: Sonraki 4 Hafta */}
      <td>
        {row.status==='ready'?<>
          <strong style={{color:'#0f172a',fontSize:'13px'}}>{fmt(total)} {unitLabel}</strong>
          <small style={{color:'#64748b',display:'block',fontSize:'10px',marginTop:'2px',lineHeight:1.3}}>
            Ürün birimi: {unitLabel} (4 hafta toplamı)
          </small>
          <MiniForecast points={points} unit={unitLabel}/>
        </>:<span className="fc-muted">Yetersiz veri</span>}
      </td>

      {/* SÜTUN 3: Güven Aralığı */}
      <td>
        {row.status==='ready'?<>
          <strong style={{color:'#1e3a5f'}}>
            {halfWidth>0?`±${fmt(halfWidth)} ${unitLabel}`:'—'}
          </strong>
          <small style={{display:'block',fontSize:'10px',color:'#64748b',marginTop:'2px',lineHeight:1.4}}>
            {fmt(totalLower)}–{fmt(totalUpper)} {unitLabel}<br/>
            %~90 güven aralığı (MAE×1,96)
          </small>
        </>:<span className="fc-status">Yetersiz geçmiş</span>}
      </td>

      {/* SÜTUN 4: Tahmin Doğruluğu & WAPE */}
      <td className="numeric">
        {accuracy==null?<span className="fc-muted">—</span>:<>
          <div style={{display:'inline-flex',alignItems:'center',gap:'5px',background:accBg,color:accColor,padding:'3px 9px',borderRadius:'12px',fontWeight:700,fontSize:'11px',marginBottom:'3px'}}>
            <span>%{accuracy} Doğruluk</span>
            <small style={{fontWeight:500,opacity:0.85}}>({accGrade})</small>
          </div>
          <small style={{display:'block',fontSize:'10px',color:'#475569',lineHeight:1.4}}>
            WAPE %{fmt(row.wape??0)} · MAE {fmt(row.mae??0)} {unitLabel}<br/>
            <span style={{color:accuracy>=60?'#15803d':'#94a3b8'}}>
              {accuracy>=75?'Güçlü tahmin modeli':accuracy>=60?'Yüksek doğruluk performansı':accuracy>=45?'Dengeli tahmin':'Volatil talep serisi'}
            </span>
          </small>
        </>}
      </td>

      {/* SÜTUN 5: Hedef Alıcılar / Model */}
      <td>
        {row.level==='product'?(
          targets.length>0?(
            <span style={{fontSize:'12px',color:'#047857',fontWeight:600,display:'flex',alignItems:'center',gap:'4px'}}>
              <Users size={13}/>{targets.length} Hedef Alıcı
            </span>
          ):<span className="fc-muted">—</span>
        ):(
          <span className="fc-method">{row.method?methodName[row.method]:'—'}</span>
        )}
        {row.candidateAccepted&&<small className="accepted"><Sparkles/>En iyi model seçildi</small>}
      </td>

      {/* SÜTUN 6: Veri Kalitesi */}
      <td>
        <span style={{fontWeight:700,fontSize:'12px',color:covColor}}>{coverageQuality}</span>
        <small style={{display:'block',fontSize:'10px',color:'#64748b',marginTop:'2px',lineHeight:1.4}}>
          {row.activeWeeks} satışlı / {row.historyWeeks} toplam hafta<br/>
          Aktiflik oranı %{coveragePct}
        </small>
        <div style={{marginTop:'4px',height:'4px',background:'#e2e8f0',borderRadius:'2px',width:'80px'}}>
          <div style={{height:'4px',background:covColor,borderRadius:'2px',width:`${Math.min(100,coveragePct)}%`}}/>
        </div>
      </td>

      <td><button className="fc-expand" onClick={onExpand} aria-expanded={expanded} aria-label={`${row.name} detayını ${expanded?'kapat':'aç'}`}><ChevronRight/></button></td>
    </tr>

    {expanded&&<tr className="fc-detail-row"><td colSpan={7}>
      <div style={{display:'flex',flexDirection:'column',gap:'16px',width:'100%'}}>

        {/* Açıklama kutusu */}
        <div style={{background:'#f8fafc',border:'1px solid #e2e8f0',borderRadius:'8px',padding:'14px 16px'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',flexWrap:'wrap',gap:'10px',marginBottom:'10px'}}>
            <div>
              <p style={{margin:'0 0 6px',fontSize:'13px',fontWeight:600,color:'#1e3a5f'}}>
                {row.status==='ready'
                  ? `Seçilen model: ${row.method?methodName[row.method]:row.method} · Ölçüm birimi: ${unitLabel}`
                  : row.reason}
              </p>
              {row.status==='ready'&&<p style={{margin:'0 0 8px',fontSize:'12px',color:'#475569',lineHeight:1.6}}>
                Güven aralığı (±{fmt(halfWidth)} {unitLabel}), backtest MAE değerinin 1,96 katı uygulanarak hesaplanmıştır.
                Mevcut model için Doğruluk Skoru <strong>%{accuracy}</strong> (WAPE %{fmt(row.wape??0)}) olarak gerçekleşmiştir.
              </p>}
            </div>
            {onAction&&<button className="predictive-btn-inject" onClick={onAction} style={{whiteSpace:'nowrap'}}>
              Stok Aksiyonu Başlat <ArrowRight size={13}/>
            </button>}
          </div>

          {/* Backtest karşılaştırması */}
          {row.status==='ready'&&<div>
            <p style={{margin:'0 0 6px',fontSize:'11px',color:'#64748b',fontWeight:600,textTransform:'uppercase',letterSpacing:'0.5px'}}>
              Algoritma Karşılaştırması (Rolling Backtest)
            </p>
            <div style={{display:'flex',gap:'8px',flexWrap:'wrap'}}>
              {Object.entries(row.backtest||{}).map(([name,m])=>{
                const isSelected=name===row.method;
                const mAcc=m.wape!=null?Math.max(0,Math.round(100-m.wape)):null;
                return <div key={name} style={{
                  fontSize:'11px',padding:'6px 10px',borderRadius:'6px',lineHeight:1.5,
                  background:isSelected?'#dbeafe':'#f1f5f9',
                  border:isSelected?'1px solid #93c5fd':'1px solid #e2e8f0',
                  color:isSelected?'#1e40af':'#475569'
                }}>
                  <div style={{fontWeight:700}}>{isSelected?'✓ Seçilen: ':''}{methodName[name]??name}</div>
                  {m.wape==null
                    ?<div>Yetersiz geçmiş</div>
                    :<><div>Doğruluk: %{mAcc} (WAPE %{fmt(m.wape)})</div>
                      <div style={{color:'#64748b'}}>MAE {fmt(m.mae??0)} {unitLabel} · {m.points} test noktası</div>
                    </>
                  }
                </div>;
              })}
            </div>
          </div>}
        </div>

        {/* Hedef müşteri tablosu */}
        {targets.length>0&&<div className="predictive-box" style={{margin:'0',padding:'14px'}}>
          <div className="predictive-box-header">
            <h4><Users size={15}/>Bu Ürünü Satın Alma İhtimali En Yüksek Müşteriler</h4>
            <span>{targets.length} Müşteri Belirlendi</span>
          </div>
          <div style={{overflowX:'auto'}}>
            <table className="predictive-target-table">
              <thead><tr><th>Müşteri</th><th>Şehir</th><th>Temsilci</th><th>Alım İhtimali</th><th>Beklenen Alım</th><th>Gerekçe</th></tr></thead>
              <tbody>{targets.map(tc=>(
                <tr key={tc.customerCode}>
                  <td><strong>{tc.customerName}</strong><br/><small style={{color:'#64748b'}}>{tc.customerCode}</small></td>
                  <td>{tc.city}</td>
                  <td>{tc.seller||'—'}</td>
                  <td><span className="predictive-badge badge-cycle">%{tc.propensityScore} {tc.tier}</span></td>
                  <td><strong>{tc.expectedOrderQty} {unitLabel}</strong></td>
                  <td style={{fontSize:'11px',color:'#334155'}}>{tc.reason}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </div>}
      </div>
    </td></tr>}
  </>;
}

function MiniForecast({points, unit}:{points:Point[]; unit?:string}){
  const max=Math.max(...points.map(x=>x.upper),1);
  const u=unit||'Birim';
  return <span className="fc-mini" aria-label="Dört haftalık talep tahmini ve güven aralığı">
    {points.map((p,i)=><i key={i} style={{height:`${Math.max(8,p.value/max*30)}px`}} title={`H${i+1}: ${fmt(p.value)} ${u} (${fmt(p.lower)}–${fmt(p.upper)} ${u})`}>
      <b style={{height:`${Math.max(2,(p.upper-p.lower)/max*30)}px`}}/>
    </i>)}
  </span>;
}
function ForecastSkeleton(){return <div className="fc-skeleton"><span/><span/><span/><span/><div/></div>}

