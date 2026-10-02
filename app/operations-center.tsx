'use client';

import {useEffect, useMemo, useState} from 'react';
import type {ReactNode} from 'react';
import {ArrowUpRight, Boxes, ChevronRight, CircleAlert, MapPin, PackageSearch, RefreshCw, Search, ShoppingBasket, Undo2} from 'lucide-react';
import './operations-center.css';
import GeographyMap, {trCity, trCountry} from './geography-map';

export type OperationsModule='geography'|'purchasing_balance'|'cross_sell'|'returns_analysis';
type Kpi=[string,number,string];
type GenericRow=Record<string,string|number|null|undefined>;
type Dataset={status:string;module:OperationsModule;title:string;analysisDate:string;currency?:string;kpis:Kpi[];rows:GenericRow[];note?:string;demoStock?:boolean;
  quality?:{incompleteRows:number;rowCount:number};countries?:GenericRow[];thresholds?:Record<string,number>;definitions?:Record<string,string>;
  products?:GenericRow[];customers?:GenericRow[];summary?:Record<string,number|null>;scenario?:Record<string,number|null>};

const money=(value:number)=>value.toLocaleString('de-DE',{style:'currency',currency:'EUR',maximumFractionDigits:0});
const number=(value:number,digits=1)=>value.toLocaleString('tr-TR',{maximumFractionDigits:digits});
const display=(value:unknown,unit?:string)=>value==null?'—':unit==='EUR'?money(Number(value)):unit==='%'?`%${number(Number(value))}`:unit==='adet'?number(Number(value),0):number(Number(value));
const moduleIcon={geography:MapPin,purchasing_balance:Boxes,cross_sell:ShoppingBasket,returns_analysis:Undo2};

function Skeleton(){return <div className="ops-skeleton" aria-label="Analiz hazırlanıyor"><span/><span/><span/><div/></div>}
function Empty(){return <div className="ops-empty"><PackageSearch/><strong>Bu görünüm için yeterli kayıt yok</strong><p>Kaynak kapsamını ve seçilen analiz tarihini kontrol edin.</p></div>}

export default function OperationsCenter({module,analysisDate,onOpenProduct,onOpenStock}:{module:OperationsModule;analysisDate:string;onOpenProduct?:(code:string)=>void;onOpenStock?:(code:string)=>void}){
  const [data,setData]=useState<Dataset|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState(''),[query,setQuery]=useState('');
  const [geoFilter,setGeoFilter]=useState<{country:string;city:string;cityList?:string[]}>({country:'',city:''});
  useEffect(()=>{setGeoFilter({country:'',city:''});setQuery('')},[module,analysisDate]);
  const [returnView,setReturnView]=useState<'products'|'customers'>('products');
  useEffect(()=>{let live=true;setLoading(true);setError('');fetch('/api/data',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'opportunity_analytics',module,analysisDate})})
    .then(r=>r.json()).then(r=>{if(!r.ok)throw new Error(r.error||'Analiz yüklenemedi.');if(live)setData(r.data)}).catch(e=>live&&setError(e.message)).finally(()=>live&&setLoading(false));return()=>{live=false}},[module,analysisDate]);
  const sourceRows=useMemo(()=>module==='returns_analysis'&&data?(returnView==='products'?data.products:data.customers)||[]:data?.rows||[],[data,module,returnView]);
  const rows=useMemo(()=>{
    const filtered=sourceRows.filter(r=>{
      if(module!=='geography')return true;
      if(geoFilter.country && r.country!==geoFilter.country && r.countryCode!==geoFilter.country)return false;
      if(geoFilter.cityList && geoFilter.cityList.length>0)return geoFilter.cityList.includes(String(r.city));
      if(geoFilter.city && r.city!==geoFilter.city)return false;
      return true;
    });
    const q=query.toLocaleLowerCase('tr-TR').trim();
    if(!q)return filtered;
    return filtered.filter(row=>{
      if(module==='geography'){
        const trC=trCity(row.city).toLocaleLowerCase('tr-TR');
        const trCo=trCountry(String(row.country||'')).toLocaleLowerCase('tr-TR');
        if(trC.includes(q)||trCo.includes(q))return true;
      }
      return Object.values(row).some(value=>String(value??'').toLocaleLowerCase('tr-TR').includes(q));
    });
  },[sourceRows,query,module,geoFilter]);
  const Icon=moduleIcon[module];
  if(loading)return <section className="ops-workspace"><Skeleton/></section>;
  if(error)return <section className="ops-workspace"><div className="ops-error"><CircleAlert/><div><strong>Operasyon analizi hazırlanamadı</strong><p>{error}</p></div><button onClick={()=>location.reload()}><RefreshCw size={15}/> Yenile</button></div></section>;
  if(!data||data.status==='no_data')return <section className="ops-workspace"><Empty/></section>;
  return <section className="ops-workspace" aria-labelledby="ops-title">
    <header className="ops-header"><div className="ops-title"><span><Icon size={19}/></span><div><h2 id="ops-title">{data.title}</h2><p>{data.note}</p></div></div><div className="ops-date"><span>Analiz tarihi</span><strong>{new Date(`${data.analysisDate}T12:00:00`).toLocaleDateString('tr-TR')}</strong></div></header>
    {module==='geography'&&<GeographyMap key={analysisDate} rows={data.rows} onFilter={(country,city,cityList)=>setGeoFilter({country,city:city||'',cityList})}/>}
    <div className="ops-kpis">{data.kpis.map(([label,value,unit])=><div key={label}><span>{label}</span><strong>{display(value,unit)}</strong><small>{unit==='EUR'?'Net ticari etki':unit==='%'?'Oransal gösterge':unit}</small></div>)}</div>
    <div className="ops-commandbar">
      {module==='returns_analysis'&&<div className="ops-segmented" role="tablist"><button className={returnView==='products'?'active':''} onClick={()=>setReturnView('products')} role="tab">Ürünler</button><button className={returnView==='customers'?'active':''} onClick={()=>setReturnView('customers')} role="tab">Müşteriler</button></div>}
      <label className="ops-search"><Search size={16}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Tabloda ara" aria-label="Operasyon tablosunda ara"/></label><span>{rows.length} sonuç</span>
    </div>
    {module==='geography'&&<GeographyTable rows={rows}/>} 
    {module==='purchasing_balance'&&<PurchasingTable rows={rows} onOpenStock={onOpenStock}/>} 
    {module==='cross_sell'&&<BasketTable rows={rows} onOpenProduct={onOpenProduct}/>} 
    {module==='returns_analysis'&&<ReturnsTable rows={rows} entity={returnView} onOpenProduct={onOpenProduct}/>} 
    <footer className="ops-method"><strong>Hesap notu</strong><p>{methodCopy(data,module)}</p></footer>
  </section>
}

function GeographyTable({rows}:{rows:GenericRow[]}){return <Table headers={['Şehir / Ülke','Net Satış','Pay','Kâr / Marj','Müşteri','İade']} rows={rows} render={r=><><td><strong>{trCity(r.city)}</strong><small>{trCountry(String(r.country||''))} · {r.postalCount} posta alanı</small></td><td className="numeric">{money(Number(r.sales))}</td><td className="numeric">%{number(Number(r.share))}</td><td className="numeric"><strong>{money(Number(r.profit))}</strong><small>{r.margin==null?'—':`%${number(Number(r.margin))}`}</small></td><td className="numeric">{number(Number(r.customers),0)}</td><td className="numeric ops-negative">{money(Number(r.returns))}</td></>}/>}
function PurchasingTable({rows,onOpenStock}:{rows:GenericRow[];onOpenStock?:(code:string)=>void}){return <Table headers={['Ürün','Alış fiyatı değişimi','Önerilen alım','Tahmini alım bedeli','Karar','']} rows={rows} render={r=><><td><strong>{r.name}</strong><small>{r.code} · {r.category}</small></td><td className="numeric"><strong>{r.currentUnitCost==null?'—':money(Number(r.currentUnitCost))}</strong><small>{r.costChange==null?'Önceki dönem yok':`%${number(Number(r.costChange))} değişim`}</small></td><td>{r.suggestedCases==null?'Talep verisi yetersiz':`${number(Number(r.suggestedCases),0)} koli`}<small>Hedef: {r.targetCoverageDays==null?'—':String(r.targetCoverageDays)} gün</small></td><td>{r.suggestedCost==null?'Birim/maliyet doğrulanmalı':money(Number(r.suggestedCost))}</td><td><span className="ops-status">{r.recommendation}</span></td><td>{onOpenStock&&<button className="ops-row-action" onClick={()=>onOpenStock(String(r.code))} aria-label={`${r.name} stok detayını aç`}>Stok detayı<ChevronRight/></button>}</td></>}/>}

function BasketTable({rows,onOpenProduct}:{rows:GenericRow[];onOpenProduct?:((code:string)=>void)}){return <Table headers={['Öneri akışı','Birlikte sepet','Support','Confidence','Lift','Güven']} rows={rows} render={r=><><td><button className="ops-link" onClick={()=>onOpenProduct?.(String(r.antecedentCode))}><strong>{r.antecedent}</strong><ArrowUpRight size={13}/><span>{r.consequent}</span></button></td><td className="numeric">{number(Number(r.together),0)}</td><td className="numeric">%{number(Number(r.support),2)}</td><td className="numeric">%{number(Number(r.confidence))}</td><td className="numeric"><strong>{number(Number(r.lift),2)}×</strong></td><td><span className={`ops-status ${r.strength==='Güçlü'?'strong':'watch'}`}>{r.strength}</span></td></>}/>}
function ReturnsTable({rows,entity,onOpenProduct}:{rows:GenericRow[];entity:'products'|'customers';onOpenProduct?:((code:string)=>void)}){return <Table headers={[entity==='products'?'Ürün':'Müşteri','İade tutarı','Miktar','Kâr etkisi','Yerine koyma','Yayılım']} rows={rows} render={r=><><td>{entity==='products'?<button className="ops-link" onClick={()=>onOpenProduct?.(String(r.code))}><strong>{r.name}</strong><small>{r.code}</small></button>:<><strong>{r.name}</strong><small>{r.code}</small></>}</td><td className="numeric ops-negative">{money(Number(r.returns))}</td><td className="numeric">{number(Number(r.quantity))}</td><td className="numeric ops-negative">{money(Number(r.profitImpact))}</td><td className="numeric">{money(Number(r.replacementImpact))}</td><td className="numeric">{entity==='products'?`${r.customers} müşteri`:`${r.products} ürün`}</td></>}/>}

function Table({headers,rows,render}:{headers:string[];rows:GenericRow[];render:(row:GenericRow)=>ReactNode}){if(!rows.length)return <Empty/>;return <div className="ops-table-wrap"><table className="ops-table"><thead><tr>{headers.map((h,i)=><th key={`${h}-${i}`}>{h}</th>)}</tr></thead><tbody>{rows.slice(0,150).map((row,i)=><tr key={`${row.code||row.name||'row'}-${i}`}>{render(row)}</tr>)}</tbody></table></div>}
function methodCopy(data:Dataset,module:OperationsModule){if(module==='cross_sell')return `En az ${data.thresholds?.minimumPairBaskets} ortak sepet ve ürün başına ${data.thresholds?.minimumProductBaskets} sepet şartı uygulanır. Düşük örneklem sonuçları karar listesinden çıkarılır.`;if(module==='purchasing_balance')return 'Fiyat değişimi iki ardışık 90 günlük medyan alış fiyatını karşılaştırır. Sipariş ve eritme adayları demo stok ile son 30 günlük net tüketimden hesaplanır.';if(module==='returns_analysis')return `Son 30 gün iade tutarı ${money(Number(data.scenario?.last30||0))}; aynı hız sürerse gelecek 90 gün senaryosu ${money(Number(data.scenario?.next90At30DayPace||0))}.`;return 'Satış iadeleri net satıştan düşülür; satın alma ve satın alma iadeleri coğrafi satış görünümüne alınmaz.'}
