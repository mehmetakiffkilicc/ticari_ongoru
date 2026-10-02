'use client';

import {useCallback,useEffect,useRef,useState} from 'react';
import {ArrowLeft,ArrowRight,Check,ChevronRight,Clock3,Database,FileCheck2,Layers3,RefreshCw,Search,ShieldCheck,Sparkles,ShoppingBag,Target,TriangleAlert,Users,PlusCircle} from 'lucide-react';
import {caseApi,caseStates,categories,outcomes,type CaseList,type CaseScope,type DecisionCase,type Proposal,type PredictiveBasketItem,type TargetCustomerItem} from './decision-types';
import './decision-hub.css';
import './predictive.css';

export type HubView='decision_summary'|'insights'|'approvals'|'case_actions'|'results'|'tags';
const date=(s?:string|null)=>s?new Date(`${s.slice(0,10)}T12:00:00`).toLocaleDateString('tr-TR'):'—';
const value=(n:unknown)=>n==null?'Belirtilmedi':typeof n==='number'?n.toLocaleString('tr-TR',{maximumFractionDigits:2}):String(n);
const steps=['Veri','Etiket','Sinyal','İçgörü','Kullanıcı onayı','Aksiyon','Geri bildirim'];
const stage=(d:DecisionCase)=>d.state==='pending'||d.state==='rejected'?4:d.state==='approved'||d.state==='in_progress'?5:6;
const nextAction=(d:DecisionCase)=>d.state==='pending'?'Öneriyi incele':d.state==='approved'?'Aksiyonu başlat':d.state==='in_progress'?'Uygulamayı kaydet':d.state==='monitoring'?(d.followupReady?'Sonucu değerlendir':'Takibi görüntüle'):'Sonucu incele';

export default function DecisionHub({view,analysisDate,onNavigate,onSource}:{view:HubView;analysisDate:string;onNavigate:(target:string,id?:string,analysisDate?:string)=>void;onSource:(id:string)=>void}){
  const [scope,setScope]=useState<CaseScope>('demo'),[ready,setReady]=useState(false),[data,setData]=useState<CaseList|null>(null);
  const [selected,setSelected]=useState<string|null>(null),[query,setQuery]=useState(''),[category,setCategory]=useState('all'),[page,setPage]=useState(0);
  const [loading,setLoading]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[resetting,setResetting]=useState(false);
  const request=useRef(0),lock=useRef(false),heading=useRef<HTMLHeadingElement>(null);
  useEffect(()=>{try{setScope(sessionStorage.getItem('decision-scope')==='live'?'live':'demo');setSelected(sessionStorage.getItem(`decision-selected-${view}`));}catch{}setReady(true)},[view]);
  const load=useCallback(async()=>{const ticket=++request.current;setLoading(true);setError('');try{const result=await caseApi<CaseList>({action:'case_list',scope});if(ticket===request.current)setData(result)}catch(e){if(ticket===request.current)setError((e as Error).message)}finally{if(ticket===request.current)setLoading(false)}},[scope]);
  useEffect(()=>{if(ready)void load();return()=>{request.current++}},[ready,load]);
  function open(id:string|null){setSelected(id);setNotice('');setError('');try{if(id)sessionStorage.setItem(`decision-selected-${view}`,id);else sessionStorage.removeItem(`decision-selected-${view}`)}catch{}requestAnimationFrame(()=>heading.current?.focus())}
  function changeScope(next:CaseScope){setScope(next);setData(null);open(null);setResetting(false);try{sessionStorage.setItem('decision-scope',next)}catch{}}
  async function command(payload:Record<string,unknown>,message:string){if(lock.current)return;lock.current=true;setBusy(true);setError('');try{
    const result=await caseApi<DecisionCase|CaseList>({...payload,scope});
    if('cases' in result){setData(result);if(payload.action==='case_demo_prepare'){open(null);setResetting(false)}}
    else{setData(current=>current?{...current,cases:[...current.cases.filter(d=>d.id!==result.id),result]}:current);if(payload.operation==='reopen'){await load();open(result.id)}}
    setNotice(message);
  }catch(e){setError((e as Error).message)}finally{lock.current=false;setBusy(false)}}
  const doc=data?.cases.find(d=>d.id===selected);
  const all=data?.cases||[];
  const matching=all.filter(d=>(category==='all'||d.category===category)&&`${d.title} ${d.entity}`.toLocaleLowerCase('tr-TR').includes(query.toLocaleLowerCase('tr-TR')));
  const filtered=matching.filter(d=>view==='approvals'?d.state==='pending':view==='case_actions'?['approved','in_progress','monitoring'].includes(d.state):view==='results'?['monitoring','reviewed'].includes(d.state):true);
  const pageCount=Math.max(1,Math.ceil(filtered.length/25));
  const visible=filtered.slice(Math.min(page,pageCount-1)*25,(Math.min(page,pageCount-1)+1)*25);
  useEffect(()=>setPage(0),[query,category,scope,view]);
  const pending=all.filter(d=>d.state==='pending'),due=all.filter(d=>d.state==='monitoring'&&d.followupReady),overdue=all.filter(d=>d.overdue);
  const explore=(d:DecisionCase)=>onNavigate(d.category==='stock'?'stock_operations':d.category==='pricing'?'pricing_costs':d.category==='customer'?'customers_360':d.snapshot.sourceModule==='salespeople'?'salespeople':'products_categories',d.snapshot.entityId,d.snapshot.analysisDate);

  return <section className="case-hub" aria-busy={loading||busy}>
    <div className="case-toolbar"><div className="case-scope" role="group" aria-label="Karar veri alanı"><button aria-pressed={scope==='demo'} disabled={busy} onClick={()=>changeScope('demo')}>Demo senaryoları</button><button aria-pressed={scope==='live'} disabled={busy} onClick={()=>changeScope('live')}>Yüklenmiş veri</button></div><div className="case-tools"><button className="secondary" disabled={busy||loading} onClick={load} aria-label="Karar dosyalarını yenile"><RefreshCw size={15}/>Yenile</button>{scope==='demo'?<button className="secondary" disabled={busy} onClick={()=>setResetting(true)}>Demoyu sıfırla</button>:<button className="primary" disabled={busy} onClick={()=>command({action:'case_evaluate',analysisDate},'Kaynaklar değerlendirildi; yeni karar dosyaları oluşturuldu.')}><Layers3 size={15}/>Veriyi değerlendir</button>}</div></div>
    <div className={`case-context ${scope}`}><ShieldCheck size={17}/><p>{scope==='demo'?<>Hazır sunum örnekleri · Değerlendirme tarihi <strong>30 Aralık 2024</strong>. Bu alandaki değerler gerçek ticari toplamlara dahil değildir.</>:<>Yüklenmiş kaynaklar · Yeni değerlendirme: <strong>{date(analysisDate)}</strong>. Dosyaların kanıt tarihleri korunur; görev takibi bugünün tarihini kullanır.</>}</p></div>
    {resetting&&<div className="case-reset" role="group" aria-label="Demo sıfırlama"><p>Yalnız demo kararları başlangıçtaki dokuz örneğe dönecek. Bu alandaki değişiklikler silinecek.</p><button className="secondary" disabled={busy} onClick={()=>setResetting(false)}>Vazgeç</button><button className="primary" disabled={busy} onClick={()=>command({action:'case_demo_prepare',reset:true},'Dokuz demo dosyası başlangıç durumuna döndü.')}>Demo alanını sıfırla</button></div>}
    {error&&<div className="alert error" role="alert"><TriangleAlert size={18}/><span>{error}</span><button className="secondary" disabled={busy} onClick={load}>Güncel sürümü getir</button></div>}
    {notice&&<p className="case-notice" role="status"><Check size={16}/>{notice}</p>}
    {busy&&<p role="status">İşlem kaydediliyor…</p>}
    {loading?<div className="case-skeleton" aria-label="Karar dosyaları yükleniyor"><span/><span/><span/></div>:doc?<>
      <button className="case-back" onClick={()=>open(null)}><ArrowLeft size={16}/>Listeye dön</button>
      <h2 ref={heading} tabIndex={-1} className="case-file-heading">{doc.entity}<span>{doc.title}</span></h2>
      <CaseFile key={`${doc.id}-${doc.version}`} doc={doc} busy={busy} onSource={onSource} onExplore={()=>explore(doc)} onOpen={open} onCommand={(operation,payload={})=>command({action:'case_mutate',id:doc.id,version:doc.version,operation,...payload},'Karar dosyası güncellendi.')}/>
    </>:<>
      <h2 className="case-sr-heading" ref={heading} tabIndex={-1}>Karar dosyaları</h2>
      {!all.length?<div className="case-empty"><Layers3 size={34}/><h2>{scope==='demo'?'Veriden sonuca, üç ticari hikâye':'Karar dosyalarınız burada birikecek'}</h2><p>{scope==='demo'?'Stok, fiyat ve müşteri kararlarını; onay, uygulama ve geri bildirim aşamalarında inceleyin.':'Kaynak verilerinizi değerlendirin. İçgörüler kanıtlarıyla kaydedilir; yalnız onayladığınız öneriler göreve dönüşür.'}</p><button className="primary" disabled={busy} onClick={()=>command(scope==='demo'?{action:'case_demo_prepare'}:{action:'case_evaluate',analysisDate},scope==='demo'?'Dokuz demo örneği hazır.':'Değerlendirme tamamlandı.')} >{scope==='demo'?'Dokuz demo örneğini hazırla':'Veriyi değerlendir'}<ArrowRight size={16}/></button>{scope==='live'&&<button className="secondary" onClick={()=>onNavigate('data_center')}>Veri ve Etiketler’e git</button>}</div>:view==='decision_summary'?<>
        <div className="case-overview"><div className="case-lead"><span className="case-label">Karar gündemi</span><h2>Önce kararı netleştirin.<br/>Sonra etkisini izleyin.</h2><p>Kanıtı inceleyin, kapsamı onaylayın ve uygulama sonrasında ne değiştiğini aynı dosyada görün.</p><div className="case-counts"><button onClick={()=>onNavigate('approvals')}><strong>{pending.length}</strong><span>Onay bekleyen</span><ArrowRight size={16}/></button><button onClick={()=>onNavigate('results')}><strong>{due.length}</strong><span>Takip zamanı gelen</span><ArrowRight size={16}/></button><button onClick={()=>onNavigate('case_actions')}><strong>{overdue.length}</strong><span>Geciken aksiyon</span><ArrowRight size={16}/></button></div></div>
        <aside className="case-agenda"><h3>Sonraki adımlar</h3>{[...due,...overdue,...pending].slice(0,4).map(d=><button key={d.id} onClick={()=>open(d.id)}><span><small>{categories[d.category]}</small><strong>{d.entity}</strong><span>{nextAction(d)}</span></span><ChevronRight size={17}/></button>)}{!pending.length&&!due.length&&!overdue.length&&<p>Bekleyen karar yok. Aksiyonlar ve sonuçlardan devam edebilirsiniz.</p>}</aside></div>
        <div className="case-section-title"><h3>Karar portföyü</h3><span>{all.length} dosya · kaynak alanı: {scope==='demo'?'demo':'yüklenmiş veri'}</span></div>
        {Object.entries(categories).filter(([key])=>all.some(d=>d.category===key)).map(([key,label])=><section className="case-story" key={key}><div><h3>{label}</h3><p>{key==='stock'?'Satış sürekliliğini koruyun.':key==='pricing'?'Marjı ve hacmi birlikte değerlendirin.':key==='customer'?'Müşteriyle yeniden bağ kurun.':'Ticari bulguları kanıtla değerlendirin.'}</p></div><div>{all.filter(d=>d.category===key).slice(0,3).map(d=><button key={d.id} onClick={()=>open(d.id)}><Status doc={d}/><strong>{d.entity}</strong><span>{d.feedback?outcomes[d.feedback.outcome]:nextAction(d)}</span><ArrowRight size={17}/></button>)}</div></section>)}
      </>:<>
        <div className="case-filterbar"><label><Search size={17}/><input aria-label="Karar dosyalarında ara" placeholder="Varlık veya karar ara" value={query} onChange={e=>setQuery(e.target.value)}/></label><select aria-label="Karar alanı" value={category} onChange={e=>setCategory(e.target.value)}><option value="all">Tüm ticari alanlar</option>{Object.entries(categories).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select><span>{filtered.length} dosya</span></div>
        {view==='tags'?<div className="case-tags"><div className="case-section-title"><h3>Etiket sözlüğü ve oluşma gerekçeleri</h3><p>Etiket sınıflandırır; sinyal değişimi gösterir; içgörü önerinin nedenini açıklar.</p></div>{Array.from(new Map(visible.flatMap(d=>d.snapshot.tags.map(t=>[t.rule,{...t,doc:d}] as const))).values()).map(t=><article key={t.rule}><span className="case-tag">{t.name}</span><h3>{t.rule}</h3><p>{t.reason}</p><button className="case-link" onClick={()=>open(t.doc.id)}>Kanıtlı örneği aç<ArrowRight size={15}/></button></article>)}</div>:view==='results'?<div className="case-results">{visible.map(d=><article key={d.id}><div><Status doc={d}/><h3>{d.entity}</h3><p>{d.title}</p></div><div className="case-comparison"><span><small>Önce</small><strong>{value(d.feedback?d.feedback.before:d.snapshot.observed)}</strong></span><ArrowRight size={20}/><span><small>Sonra</small><strong>{d.feedback?.after==null?'Bekleniyor':value(d.feedback.after)}</strong></span><span><small>{d.feedback?.unit||d.snapshot.unit}</small><b>{d.feedback?outcomes[d.feedback.outcome]:`Takip: ${date(d.task?.followupDate)}`}</b></span></div><p>{d.feedback?.note||'Aksiyon uygulandı. Sonuç, takip tarihinden sonra değerlendirilecek.'}</p><button className="secondary" onClick={()=>open(d.id)}>{nextAction(d)}<ArrowRight size={15}/></button></article>)}</div>:<div className="case-table-scroll"><table className="case-table"><thead><tr><th>Karar / varlık</th>{view==='insights'?<><th>Kanıt</th><th>Güven</th></>:view==='approvals'?<><th>Önerilen işlem</th><th>Takip</th></>:<><th>Sorumlu / termin</th><th>Takip tarihi</th></>}<th>Durum</th><th><span className="sr-only">Dosya</span></th></tr></thead><tbody>{visible.map(d=><tr key={d.id}><td><small>{categories[d.category]}</small><button className="case-title-button" onClick={()=>open(d.id)}>{d.entity}</button><span>{d.title}</span></td>{view==='insights'?<><td>{value(d.snapshot.observed)} {d.snapshot.unit}<small>Referans: {value(d.snapshot.threshold)}</small></td><td>{d.snapshot.confidence}<small>{d.snapshot.score}/100 öncelik</small></td></>:view==='approvals'?<><td className="case-description">{d.proposal.description}<small>{d.proposal.owner}</small></td><td>{d.proposal.followupDays} gün<small>Termin: {date(d.proposal.dueDate)}</small></td></>:<><td>{d.task?.owner}<small>{date(d.task?.dueDate)}</small></td><td>{date(d.task?.followupDate)}</td></>}<td><Status doc={d}/></td><td><button className="case-open" onClick={()=>open(d.id)} aria-label={`${d.entity} karar dosyasını aç`}><ArrowRight size={18}/></button></td></tr>)}</tbody></table></div>}
        {filtered.length>25&&<div className="case-pagination"><span>Sayfa {Math.min(page,pageCount-1)+1} / {pageCount}</span><button className="secondary" disabled={page===0} onClick={()=>setPage(v=>Math.max(0,v-1))}>Önceki</button><button className="secondary" disabled={page>=pageCount-1} onClick={()=>setPage(v=>v+1)}>Sonraki</button></div>}
        {!visible.length&&<div className="case-empty"><Target size={28}/><h3>Bu görünümde dosya yok</h3><p>Filtreleri değiştirin veya diğer karar aşamalarını inceleyin.</p></div>}
      </>}
      {scope==='live'&&!!data?.legacy.length&&<details className="case-legacy"><summary>Önceki sistemden korunan {data.legacy.length} aksiyon</summary><p>Bu kayıtların geçmiş onay ve takip bilgileri bulunmuyor; yeni karar dosyası gibi değerlendirilmez.</p><table><thead><tr><th>Aksiyon</th><th>Sorumlu</th><th>Durum</th></tr></thead><tbody>{data.legacy.map(a=><tr key={a.id}><td>{a.title}</td><td>{a.owner}</td><td>{{open:'Açık',in_progress:'Devam ediyor',completed:'Tamamlandı',rejected:'Reddedildi'}[a.status]||a.status}</td></tr>)}</tbody></table></details>}
    </>}
  </section>;
}

function Status({doc}:{doc:DecisionCase}){return <span className={`case-status ${doc.overdue?'overdue':doc.state}`}><i/>{doc.overdue?'Geciken aksiyon':doc.state==='monitoring'&&doc.followupReady?'Değerlendirme zamanı':caseStates[doc.state]}</span>}

function CaseFile({doc,busy,onCommand,onSource,onExplore,onOpen}:{doc:DecisionCase;busy:boolean;onCommand:(op:string,payload?:Record<string,unknown>)=>Promise<void>;onSource:(id:string)=>void;onExplore:()=>void;onOpen:(id:string)=>void}){
  const [tab,setTab]=useState(stage(doc)),[editing,setEditing]=useState(false),[draft,setDraft]=useState<Proposal>(doc.proposal),[note,setNote]=useState('');
  const [result,setResult]=useState('unmeasurable'),[before,setBefore]=useState(''),[after,setAfter]=useState(''),[unit,setUnit]=useState(doc.snapshot.unit),[evidence,setEvidence]=useState('');
  const current=stage(doc),proof=doc.snapshot;
  const progress=useRef<HTMLElement>(null);
  useEffect(()=>{const rail=progress.current;const active=rail?.querySelector<HTMLElement>('[aria-current=step]');if(rail&&active)rail.scrollLeft=active.offsetLeft-rail.offsetLeft-(rail.clientWidth-active.offsetWidth)/2},[tab]);

  function appendToProposal(textToAppend: string) {
    if (!editing) {
      setEditing(true);
    }
    setDraft(prev => {
      const currentDesc = prev.description.trim();
      const updated = currentDesc ? `${currentDesc}\n• ${textToAppend}` : textToAppend;
      return { ...prev, description: updated };
    });
  }

  return <>
    <div className="case-file-meta"><Status doc={doc}/><span>{categories[doc.category]} · Öneri sürümü {doc.revision}</span><span>{doc.scope==='demo'?'Demo senaryosu':'Kaynak veriden üretildi'} · Kanıt: {date(proof.analysisDate)}</span></div>
    <nav ref={progress} className="case-progress" aria-label="Karar hattı">{steps.map((label,i)=><button key={label} onClick={()=>setTab(i)} aria-current={tab===i?'step':undefined} className={`${i<current?'done':''} ${tab===i?'selected':''}`}><span>{i<current?<Check size={14}/>:i+1}</span>{label}</button>)}</nav>
    <div className="case-file-layout"><div className="case-stage">
      <div className="case-section-title"><h3>{steps[tab]}</h3><span>{tab===current?'Mevcut aşama':tab<current?'Kararın dayanağı':'Sonraki aşama'}</span></div>
      {tab===0&&<><h4>Kaynak ve kapsam</h4><dl className="case-facts"><div><dt>Dönem</dt><dd>{proof.period.map(date).join(' – ')}</dd></div><div><dt>Veri niteliği</dt><dd>{proof.provenance==='demo'?'Hazır demo senaryosu':proof.provenance==='modeled'?'Tahmini stok modeli':'Kaynak kayıtları'}</dd></div><div><dt>Kalite</dt><dd>{proof.quality}</dd></div><div><dt>Filtre kapsamı</dt><dd>{Object.entries(proof.filters).map(([key,v])=>`${key==='analysisDate'?'Analiz tarihi':key==='scope'?'Kapsam':key}: ${value(v)}`).join(' · ')}</dd></div></dl>{proof.sources.map(s=><button className="case-source" key={s.id} onClick={()=>onSource(s.id)}><Database size={17}/>{s.name}<span>Kalite raporu</span><ArrowRight size={16}/></button>)}{!proof.sources.length&&<p className="case-muted">Bu sunum örneğinin gerçek CSV kaynağı yoktur.</p>}{proof.evidence?.source?.references?.map((ref,i)=><p className="case-source-row" key={i}>Kaynak satır {ref.sourceLine} · {ref.invoice||'Fatura belirtilmedi'} · {date(ref.date)} · {value(ref.amount)} €</p>)}</>}
      {tab===1&&<><p>Etiketler verinin ticari sınıfını açıklar. Onay veya uygulanmış işlem anlamına gelmez.</p>{proof.tags.map(t=><article className="case-tag-proof" key={t.rule}><span className="case-tag">{t.name}</span><h4>{t.rule}</h4><p>{t.reason}</p></article>)}</>}
      {tab===2&&<><h4>{doc.title}</h4><div className="case-signal-proof"><div><span>Gözlenen</span><strong>{value(proof.observed)} <small>{proof.unit}</small></strong></div><div><span>Eşik / referans</span><strong>{value(proof.threshold)}</strong></div></div><dl className="case-facts"><div><dt>Öncelik</dt><dd>{proof.score}/100</dd></div><div><dt>Güven</dt><dd>{proof.confidence}</dd></div></dl><p>{proof.uncertainty}</p><button className="secondary" onClick={()=>setTab(0)}>Kaynak kanıtını incele</button></>}
      {tab===3&&<><h4>Bu neden önemli?</h4><p className="case-insight-copy">{proof.insight}</p>
        
        {/* PREDICTIVE INSIGHT CARD: MÜŞTERİ VEYA STOK ÖNGÖRÜSÜ */}
        {doc.category==='customer'&&proof.predictiveBasket&&proof.predictiveBasket.length>0&&<div className="predictive-box">
          <div className="predictive-box-header">
            <h4><ShoppingBag size={16}/>Müşterinin Sıradaki Ziyaretinde Alması Beklenen Ürünler (Tahmini Sepet)</h4>
            <span>Yapay Zekâ Talep Modeli</span>
          </div>
          <p className="case-muted" style={{margin:'0 0 6px 0'}}>Müşterinin tüketim periyotları, rutin alışkanlıkları ve birliktelik kuralları (Cross-Sell Lift) analiz edilerek türetilmiştir.</p>
          <div className="predictive-grid">
            {proof.predictiveBasket.map(item=><div key={item.code} className="predictive-item-card">
              <div className="predictive-item-top">
                <span className="predictive-item-name">{item.name}</span>
                <span className={`predictive-badge ${item.badge==='Döngüsü Geldi'?'badge-cycle':item.badge==='Rutin Sepet'?'badge-staple':item.badge==='Çapraz Satış'?'badge-cross':'badge-lost'}`}>{item.badge}</span>
              </div>
              <div className="predictive-meter">
                <div className="predictive-meter-bar">
                  <div className="predictive-meter-fill" style={{width:`${Math.min(100,item.probability)}%`}}/>
                </div>
                <span>%{item.probability}</span>
              </div>
              <p className="predictive-reason">{item.reason}</p>
              <button type="button" className="predictive-btn-inject" onClick={()=>{appendToProposal(`Önerilen Teklif Ürünü: ${item.name} (${item.badge} - Alım Olasılığı %${item.probability})`);setTab(4);}}>
                <PlusCircle size={13}/>Aksiyona Dahil Et
              </button>
            </div>)}
          </div>
        </div>}

        {(doc.category==='stock'||doc.category==='pricing')&&proof.targetCustomers&&proof.targetCustomers.length>0&&<div className="predictive-box">
          <div className="predictive-box-header">
            <h4><Users size={16}/>Bu Stoğu Eritebilecek / Alım Potansiyeli En Yüksek Müşteriler</h4>
            <span>Hedef Müşteri Öngörüsü</span>
          </div>
          <p className="case-muted" style={{margin:'0 0 6px 0'}}>Stok devir hızını artırmak ve marjı korumak için bu ürünü satın alma eğilimi en yüksek müşteriler listelenmiştir.</p>
          <div style={{overflowX:'auto'}}>
            <table className="predictive-target-table">
              <thead><tr><th>Müşteri</th><th>Şehir</th><th>Temsilci</th><th>Skor</th><th>Öneri Gerekçesi</th><th>Aksiyon</th></tr></thead>
              <tbody>
                {proof.targetCustomers.map(tc=><tr key={tc.customerCode}>
                  <td><strong>{tc.customerName}</strong><br/><small style={{color:'#64748b'}}>{tc.customerCode}</small></td>
                  <td>{tc.city}</td>
                  <td>{tc.seller||'—'}</td>
                  <td><span className="predictive-badge badge-cycle">%{tc.propensityScore} {tc.tier}</span></td>
                  <td><span style={{fontSize:'11px',color:'#334155'}}>{tc.reason}</span></td>
                  <td>
                    <button type="button" className="predictive-btn-inject" onClick={()=>{appendToProposal(`Hedef Müşteri Teklifi: ${tc.customerName} (${tc.city}) - Alım Skoru %${tc.propensityScore} (${tc.tier})`);setTab(4);}}>
                      <PlusCircle size={13}/>Teklife Ekle
                    </button>
                  </td>
                </tr>)}
              </tbody>
            </table>
          </div>
        </div>}

        <h4>Beklenen sonuç</h4><p>{doc.proposal.successMetric}</p><h4>Önerilen işlem</h4><p>{doc.proposal.description}</p><p className="case-caution"><TriangleAlert size={18}/>{proof.uncertainty}</p>{proof.impact!=null&&<p>Tahmini ticari etki: {value(proof.impact)} € · gerçekleşmiş kazanç değildir.</p>}<button className="primary" onClick={()=>setTab(4)}>Onay kapsamını incele<ArrowRight size={16}/></button></>}
      {tab===4&&<>{editing?<form className="case-form" onSubmit={e=>{e.preventDefault();void onCommand('edit',{proposal:draft})}}>
        {/* EDITING FORM ICINDE HIZLI SECIM ONERILERI */}
        {doc.category==='customer'&&proof.predictiveBasket&&proof.predictiveBasket.length>0&&<div style={{background:'#f0f7ff',border:'1px solid #bfdbfe',borderRadius:'7px',padding:'12px',marginBottom:'4px'}}>
          <span style={{fontSize:'12px',fontWeight:700,color:'#1e40af',display:'flex',alignItems:'center',gap:'6px',marginBottom:'8px'}}>
            <Sparkles size={14}/>Tahmini Sepetten Hızlı Ekle:
          </span>
          <div style={{display:'flex',gap:'8px',flexWrap:'wrap'}}>
            {proof.predictiveBasket.map(p=><button key={p.code} type="button" className="predictive-btn-inject" onClick={()=>appendToProposal(`Teklif Edilecek Ürün: ${p.name} (%${p.probability} ihtimal, ${p.badge})`)}>
              <PlusCircle size={12}/>{p.name} (%{p.probability})
            </button>)}
          </div>
        </div>}

        {(doc.category==='stock'||doc.category==='pricing')&&proof.targetCustomers&&proof.targetCustomers.length>0&&<div style={{background:'#f0f7ff',border:'1px solid #bfdbfe',borderRadius:'7px',padding:'12px',marginBottom:'4px'}}>
          <span style={{fontSize:'12px',fontWeight:700,color:'#1e40af',display:'flex',alignItems:'center',gap:'6px',marginBottom:'8px'}}>
            <Sparkles size={14}/>Hedef Müşterilerden Hızlı Ekle:
          </span>
          <div style={{display:'flex',gap:'8px',flexWrap:'wrap'}}>
            {proof.targetCustomers.map(tc=><button key={tc.customerCode} type="button" className="predictive-btn-inject" onClick={()=>appendToProposal(`Hedef Müşteri: ${tc.customerName} (Skor %${tc.propensityScore})`)}>
              <PlusCircle size={12}/>{tc.customerName} (%{tc.propensityScore})
            </button>)}
          </div>
        </div>}

        <label>İşlem kapsamı<textarea required minLength={5} maxLength={2000} value={draft.description} onChange={e=>setDraft({...draft,description:e.target.value})}/></label><label>Sorumlu<input required value={draft.owner} onChange={e=>setDraft({...draft,owner:e.target.value})}/></label><div className="case-form-pair"><label>Termin<input required type="date" min={doc.effectiveDate} value={draft.dueDate} onChange={e=>setDraft({...draft,dueDate:e.target.value})}/></label><label>Takip süresi (gün)<input required type="number" min={1} max={365} step={1} value={draft.followupDays} onChange={e=>setDraft({...draft,followupDays:Number(e.target.value)})}/></label></div><label>Başarı ölçütü<textarea required minLength={5} value={draft.successMetric} onChange={e=>setDraft({...draft,successMetric:e.target.value})}/></label><p>Kapsam değişikliği yeni sürüm oluşturur ve yeniden onay gerektirir.</p><div className="case-form-actions"><button type="button" className="secondary" onClick={()=>setEditing(false)}>Vazgeç</button><button className="primary" disabled={busy}>Yeni sürümü kaydet</button></div></form>:<>
        <h4>{doc.proposal.description}</h4>

        {/* ONAY ONCESI PREDICTIVE LISTE */}
        {doc.category==='customer'&&proof.predictiveBasket&&proof.predictiveBasket.length>0&&<div style={{background:'#f8fafc',border:'1px solid #e2e8f0',borderRadius:'8px',padding:'14px',margin:'14px 0'}}>
          <h5 style={{margin:'0 0 8px 0',fontSize:'13px',fontWeight:700,color:'#1e293b',display:'flex',alignItems:'center',gap:'6px'}}><ShoppingBag size={15}/>Önerilen Tahmini Sepet:</h5>
          <div style={{display:'flex',flexWrap:'wrap',gap:'8px'}}>
            {proof.predictiveBasket.map(p=><span key={p.code} style={{background:'#fff',border:'1px solid #cbd5e1',borderRadius:'5px',padding:'4px 8px',fontSize:'12px',display:'inline-flex',alignItems:'center',gap:'6px'}}>
              <strong>{p.name}</strong> <span style={{color:'#0284c7',fontWeight:600}}>%{p.probability}</span> <small style={{color:'#64748b'}}>({p.badge})</small>
            </span>)}
          </div>
        </div>}

        {(doc.category==='stock'||doc.category==='pricing')&&proof.targetCustomers&&proof.targetCustomers.length>0&&<div style={{background:'#f8fafc',border:'1px solid #e2e8f0',borderRadius:'8px',padding:'14px',margin:'14px 0'}}>
          <h5 style={{margin:'0 0 8px 0',fontSize:'13px',fontWeight:700,color:'#1e293b',display:'flex',alignItems:'center',gap:'6px'}}><Users size={15}/>Hedef Alıcı Müşteri Önerileri:</h5>
          <div style={{display:'flex',flexWrap:'wrap',gap:'8px'}}>
            {proof.targetCustomers.map(tc=><span key={tc.customerCode} style={{background:'#fff',border:'1px solid #cbd5e1',borderRadius:'5px',padding:'4px 8px',fontSize:'12px',display:'inline-flex',alignItems:'center',gap:'6px'}}>
              <strong>{tc.customerName}</strong> <span style={{color:'#059669',fontWeight:600}}>%{tc.propensityScore}</span> <small style={{color:'#64748b'}}>({tc.city})</small>
            </span>)}
          </div>
        </div>}

        <dl className="case-facts"><div><dt>Sorumlu</dt><dd>{doc.proposal.owner}</dd></div><div><dt>Termin</dt><dd>{date(doc.proposal.dueDate)}</dd></div><div><dt>Takip</dt><dd>Uygulamadan {doc.proposal.followupDays} gün sonra</dd></div><div><dt>Başarı ölçütü</dt><dd>{doc.proposal.successMetric}</dd></div></dl>{!['monitoring','reviewed'].includes(doc.state)&&<button className="secondary" disabled={busy} onClick={()=>setEditing(true)}>Öneriyi düzenle</button>}{doc.state==='pending'&&<div className="case-approval-form"><label>Karar notu<textarea value={note} maxLength={2000} onChange={e=>setNote(e.target.value)} placeholder="Ret için en az 5 karakter gerekçe gerekir."/></label><div className="case-form-actions"><button className="secondary" disabled={busy||note.trim().length<5} onClick={()=>onCommand('reject',{note})}>Gerekçeyle reddet</button><button className="primary" disabled={busy} onClick={()=>onCommand('approve',{note})}><ShieldCheck size={16}/>Onayla ve görev oluştur</button></div><p>Bu onay uygulama içi görev oluşturur. Sinyal doğrulamasından ayrı bir karardır.</p></div>}{doc.approvals.map((a,i)=><div className="case-approval-record" key={i}><FileCheck2 size={18}/><span><strong>Sürüm {a.revision} · {a.decision==='approved'?'Onaylandı':'Reddedildi'}</strong><small>{a.actor} · {date(a.businessDate)}</small>{a.note&&<p>{a.note}</p>}</span></div>)}{doc.state==='rejected'&&<button className="secondary" disabled={busy} onClick={()=>onCommand('reopen')}>Yeni inceleme başlat</button>}</>}</>}
      {tab===5&&<>{!doc.task?<div className="case-empty"><ShieldCheck size={28}/><h4>Önce kullanıcı onayı gerekiyor</h4><p>Onaylanmış güncel sürüm olmadan aksiyon başlatılamaz.</p><button className="secondary" onClick={()=>setTab(4)}>Onay adımına git</button></div>:<><h4>{doc.proposal.description}</h4><dl className="case-facts"><div><dt>Sorumlu</dt><dd>{doc.task.owner}</dd></div><div><dt>Termin</dt><dd>{date(doc.task.dueDate)}</dd></div><div><dt>Uygulandı</dt><dd>{date(doc.task.appliedDate)}</dd></div><div><dt>Takip tarihi</dt><dd>{date(doc.task.followupDate)}</dd></div></dl>{doc.task.note&&<p>{doc.task.note}</p>}{doc.state==='approved'&&<button className="primary" disabled={busy} onClick={()=>onCommand('start')}>Aksiyonu başlat<ArrowRight size={16}/></button>}{doc.state==='in_progress'&&<form className="case-form" onSubmit={e=>{e.preventDefault();void onCommand('apply',{note})}}><label>Uygulama notu<textarea required minLength={5} maxLength={2000} value={note} onChange={e=>setNote(e.target.value)} placeholder="Yapılan işlemi ve kapsamını kaydedin."/></label><button className="primary" disabled={busy}>Uygulandı olarak kaydet</button></form>}<p className="case-caution"><Clock3 size={18}/>Uygulama kaydı başarı sonucu değildir. Etki ayrı bir takip değerlendirmesinde kaydedilir.</p></>}</>}
      {tab===6&&<>{doc.feedback?<><h4>{outcomes[doc.feedback.outcome]}</h4><div className="case-comparison large"><span><small>Önce</small><strong>{value(doc.feedback.before)}</strong></span><ArrowRight/><span><small>Sonra</small><strong>{value(doc.feedback.after)}</strong></span><span>{doc.feedback.unit}</span></div><p>{doc.feedback.note}</p><p className="case-muted">Kaynak: {doc.feedback.evidence} · {doc.feedback.source==='demo'?'Hazır demo sonucu':'Kullanıcının bildirdiği ölçüm'}</p><p className="case-caution"><TriangleAlert size={18}/>Öncesi–sonrası farkı tek başına aksiyonun kesin etkisini kanıtlamaz.</p><button className="secondary" disabled={busy} onClick={()=>doc.childId?onOpen(doc.childId):onCommand('reopen')}>{doc.childId?'Yeni incelemeyi aç':'Sonuçtan yeni inceleme başlat'}</button></>:doc.state==='monitoring'&&doc.followupReady?<form className="case-form" onSubmit={e=>{e.preventDefault();void onCommand('feedback',{outcome:result,before,after,unit,evidence,note})}}><label>Takip sonucu<select value={result} onChange={e=>setResult(e.target.value)}>{Object.entries(outcomes).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label>{result!=='unmeasurable'&&<><div className="case-form-pair"><label>Önce<input required type="number" step="any" value={before} onChange={e=>setBefore(e.target.value)}/></label><label>Sonra<input required type="number" step="any" value={after} onChange={e=>setAfter(e.target.value)}/></label></div><label>Birim<input required value={unit} onChange={e=>setUnit(e.target.value)}/></label><label>Ölçüm kaynağı<input required minLength={5} value={evidence} onChange={e=>setEvidence(e.target.value)} placeholder="Rapor, kaynak dönemi veya doğrulama kaydı"/></label></>}<label>Değerlendirme notu<textarea required minLength={5} value={note} onChange={e=>setNote(e.target.value)} placeholder="Ne değişti, ne öğrendiniz? Veri yoksa neden ölçülemedi?"/></label><button className="primary" disabled={busy}>Geri bildirimi kaydet</button></form>:<div className="case-empty"><Clock3 size={30}/><h4>{doc.state==='monitoring'?`${date(doc.task?.followupDate)} tarihinde değerlendirilecek`:'Takip uygulamadan sonra başlar'}</h4><p>Uygulamadan {doc.proposal.followupDays} gün sonra başarı ölçütüyle karşılaştırma yapılır. Henüz sonuç üretilmedi.</p></div>}</>}
      {tab<6&&<div className="case-stage-next"><button className="case-link" onClick={()=>setTab(tab+1)}>{steps[tab+1]}<ArrowRight size={15}/></button></div>}
    </div><aside className="case-file-side"><section><h3>Kararın özeti</h3><p>{proof.insight}</p><dl><dt>Başarı ölçütü</dt><dd>{doc.proposal.successMetric}</dd><dt>Takip süresi</dt><dd>{doc.proposal.followupDays} gün</dd></dl>{doc.scope==='live'&&<button className="case-link" onClick={onExplore}>Ticari incelemeyi aç<ArrowRight size={15}/></button>}{doc.parentId&&<button className="case-link" onClick={()=>onOpen(doc.parentId!)}>Önceki karar dosyası<ArrowRight size={15}/></button>}</section><section><h3>Karar geçmişi</h3><ol className="case-timeline">{doc.events.map(e=><li key={e.id}><span/ ><div><strong>{e.label}</strong><small>{date(e.businessDate)} · {e.actor}</small><details><summary>Kayıt zamanı</summary><small>{new Date(e.at).toLocaleString('tr-TR')}</small></details></div></li>)}</ol></section></aside></div>
    <details className="case-versions"><summary>Öneri sürümleri · {doc.revisions.length} kayıt</summary>{doc.revisions.map(r=><article key={r.revision}><h4>Sürüm {r.revision}</h4><p>{r.proposal.description}</p><small>{r.proposal.owner} · {date(r.proposal.dueDate)} · {r.proposal.followupDays} gün takip</small><p>{r.proposal.successMetric}</p></article>)}</details>
  </>;
}
