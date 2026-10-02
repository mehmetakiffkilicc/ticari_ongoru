'use client';

import {useEffect,useMemo,useState} from 'react';
import {AlertTriangle,ArrowUpRight,Search,ShieldCheck} from 'lucide-react';

type KPI=[string,number,string];
type Row={name:string;code?:string;sales?:number;profit?:number;margin?:number|null;returns?:number;returnRate?:number|null;invoices?:number;customers?:number;products?:number;quantity?:number;support?:number;forecast?:number;price?:number;cost?:number;replacementCost?:number;replacementMargin?:number|null;recency?:number;cadence?:number|null;basket?:number;segment?:string};
type Data={status:string;title:string;range:string[];demo:boolean;kpis:KPI[];rows:Row[];rowLabel:string;note?:string};
const fold=(s:string)=>s.toLocaleLowerCase('tr-TR').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replaceAll('ı','i');
const fmt=(v:number,u?:string)=>u==='EUR'?v.toLocaleString('de-DE',{style:'currency',currency:'EUR',maximumFractionDigits:0}):u==='%'?`%${v.toLocaleString('tr-TR',{maximumFractionDigits:1})}`:v.toLocaleString('tr-TR',{maximumFractionDigits:1});

export default function InsightModule({module,onProduct}:{module:string;onProduct?:(code:string)=>void}){
  const [data,setData]=useState<Data|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState(''),[query,setQuery]=useState('');
  useEffect(()=>{let live=true;setLoading(true);setError('');fetch('/api/data',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'module_analytics',module})}).then(r=>r.json()).then(r=>{if(!r.ok)throw new Error(r.error);if(live)setData(r.data)}).catch(e=>live&&setError(e.message)).finally(()=>live&&setLoading(false));return()=>{live=false}},[module]);
  const rows=useMemo(()=>data?.rows.filter(r=>!query||fold(`${r.name} ${r.code||''}`).includes(fold(query)))||[],[data,query]);
  if(loading)return <section className="surface insight-state">Analiz hazırlanıyor…</section>;
  if(error)return <section className="surface insight-state error"><AlertTriangle/> {error}</section>;
  if(!data||data.status==='no_data')return <section className="surface insight-state">Bu analiz için kullanılabilir hareket verisi yok.</section>;
  const purchasing=module==='purchasing_balance',returns=module==='returns_analysis',cross=module==='cross_sell',forecast=module==='forecasting';
  return <div className="insight-module">
    <div className="insight-context"><div><h2>{data.title}</h2><p>{new Date(data.range[0]+'T12:00:00').toLocaleDateString('tr-TR')} – {new Date(data.range[1]+'T12:00:00').toLocaleDateString('tr-TR')}</p></div><span className={data.demo?'demo':''}>{data.demo?'Referans tahmin':'Kaynak veriden hesaplandı'}</span></div>
    <div className="insight-kpis">{data.kpis.map(([label,value,unit])=><div key={label}><span>{label}</span><strong>{fmt(value,unit)}</strong><small>{unit==='hayır'?'Doğrulama bekliyor':unit}</small></div>)}</div>
    {data.note&&<div className="insight-note"><ShieldCheck size={17}/><p>{data.note}</p></div>}
    <section className="surface insight-table-card"><header><div><h3>{data.rowLabel} kırılımı</h3><p>{rows.length} kayıt · tüm değerler aynı veri kapsamından</p></div><label><Search size={15}/><input aria-label={`${data.rowLabel} kırılımında ara`} value={query} onChange={e=>setQuery(e.target.value)} placeholder={`${data.rowLabel} ara`}/></label></header>
      <div className="insight-table"><table><thead><tr><th>{data.rowLabel}</th><th>{purchasing?'Alım tutarı':returns?'İade tutarı':forecast?'Tahmin':cross?'Eşleşme':'Ciro / değer'}</th><th>{purchasing?'Miktar':returns?'Net satış':cross?'Destek':'Kâr'}</th><th>{purchasing?'Ürün':returns?'İade oranı':cross?'Ürün':'Marj'}</th><th>Fatura</th><th>{purchasing?'Tedarikçi':'Müşteri'}</th><th/></tr></thead><tbody>{rows.slice(0,150).map((r,i)=><tr key={`${r.name}-${i}`} onClick={()=>module==='pricing_costs'&&r.code&&onProduct?.(r.code)} className={module==='pricing_costs'&&r.code?'clickable':''}><td><strong>{r.name}</strong>{r.code&&<small>{r.code}</small>}</td><td>{returns?fmt(r.returns||0,'EUR'):r.forecast!=null?fmt(r.forecast):r.sales!=null?fmt(r.sales,'EUR'):fmt(r.quantity||0)}</td><td>{purchasing?fmt(r.quantity||0):returns?fmt(r.sales||0,'EUR'):r.support!=null?`%${fmt(r.support)}`:r.profit!=null?fmt(r.profit,'EUR'):'—'}</td><td>{purchasing?r.products??'—':returns?r.returnRate!=null?fmt(r.returnRate,'%'):'—':r.replacementMargin!=null?fmt(r.replacementMargin,'%'):r.margin!=null?fmt(r.margin,'%'):cross?r.products??'—':'—'}</td><td>{r.invoices??'—'}</td><td>{r.customers??'—'}</td><td>{module==='pricing_costs'&&r.code&&<ArrowUpRight size={15}/>}</td></tr>)}</tbody></table></div>
    </section>
  </div>;
}
