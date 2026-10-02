'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ArrowDownToLine, ArrowLeft, ArrowRight, Award, BarChart3, Boxes, CalendarDays, Check,
  CheckCircle2, ChevronDown, ChevronRight, CircleHelp, ClipboardList, Clock3, Database,
  FileCheck2, FileSpreadsheet, FolderInput, Layers3, LayoutDashboard,
  LoaderCircle, LockKeyhole, MapPin, Package, Plus, ShieldCheck,
  ShoppingBag, Sparkles, Tag, Target, TrendingUp, TriangleAlert, Truck, RotateCcw,
  UploadCloud, Users, X, Zap
} from 'lucide-react';
import ManagementCockpit from './cockpit';
import DecisionHub, {type HubView} from './decision-hub';
import ProductCenter from './product-center';
import ResearchLibrary, {ResearchShortcuts} from './research-library';
import StockCenter from './stock-center';

import InsightModule from './insight-module';
import CustomerCenter from './customer-center';
import PricingCenter from './pricing-center';
import SellerCenter from './seller-center';
import OperationsCenter, {type OperationsModule} from './operations-center';
import ForecastingCenter from './forecasting-center';
import ProfitabilityCenter from './profitability-center';
import {useApplicationAccessibility} from './use-application-accessibility';

type Kind = 'stock' | 'movement';
type Inspection = { id: string; kind: Kind; name: string; headers: string[]; expected: string[]; mapping: number[]; preview: { line: number; values: string[] }[]; total: number; exactOrder: boolean; duplicateHeaders: string[]; previous: { name: string; created: string } | null; fields: { name: string; type: string; required: boolean }[] };
type Issue = { line: number; field: string; code: string; severity: string; message: string; raw: string };
type Report = { id: string; kind: Kind; name: string; total: number; accepted: number; rejected: number; affected: number; errors: number; warnings: number; groups: { code: string; severity: string; field: string; message: string; count: number }[]; issues: Issue[]; issueTotal: number; issueOffset: number; preview: { line: number; raw: Record<string,string>; converted: Record<string,string|null>; valid: boolean }[]; warehouses: string[]; range: string[]; snapshot: string; missing: Record<string,number>; created: string };
type Batch = Pick<Report,'id'|'kind'|'name'|'created'|'total'|'accepted'|'rejected'|'warnings'|'errors'|'affected'|'warehouses'|'snapshot'|'range'|'missing'>;
type QualityDimension = { key: string; label: string; score: number; affected: number; affectedLabel: string; description: string };
type QualityRule = { code: string; dimension: string; name: string; severity: string; modules: string[]; count: number; active: boolean };
type ModuleQuality = { name: string; status: 'ready'|'partial'|'missing'; label: string; coverage: number; note: string };
type Quality = { status: 'no_data'|'ready'|'partial'|'correction'; label: string; dimensions: QualityDimension[]; rules: QualityRule[]; missingFields?: {kind:Kind;field:string;count:number;rate:number;required:boolean;modules:string[]}[]; modules: ModuleQuality[]; freshness: {movementAgeDays?:number|null;stockAgeDays?:number|null;movementStatus?:string;stockStatus?:string}; coverage: {movementWarehouses?:string[];stockWarehouses?:string[];unknownWarehouses?:string[]}; scope?: {rows:number;files:number;latestOnly:boolean} };
type Dashboard = { batches: Batch[]; totals: Partial<Record<Kind,number>>; quality: Quality };

const fmt = (n: number) => n.toLocaleString('tr-TR');
const stamp = (s: string) => s ? new Date(s).toLocaleString('tr-TR', { dateStyle: 'short', timeStyle: 'short' }) : 'Belirtilmedi';
const kindLabel = (k: Kind) => k === 'stock' ? 'Stok' : 'Hareket';
const DEMO_ANALYSIS_DATE = '2024-12-30';
const DEMO_MIN_DATE = '2023-01-02';
const groupNames: Record<string,string> = {missing:'Boş alan',conversion:'Dönüşüm hatası',column_count:'Kolon sayısı',empty_row:'Boş satır',zero_cost:'Sıfır maliyet',invalid_content:'İçerik kontrolü',negative_stock:'Negatif stok',invoice_type:'Fatura türü',sign:'İşaret uyuşmazlığı',unit:'Birim kontrolü',date_mismatch:'Tarih uyuşmazlığı',duplicate_candidate:'Tekrar adayı',overlap:'Önceki aktarımla çakışma',extra_columns:'Ek kolon'};

async function api<T>(body?: Record<string,unknown> | FormData): Promise<T> {
  const response = await fetch('/api/data', body ? {method:'POST',headers: body instanceof FormData ? undefined : {'Content-Type':'application/json'},body:body instanceof FormData ? body : JSON.stringify(body)} : {cache:'no-store'});
  const result = await response.json();
  if (!result.ok) throw new Error(result.error || 'İşlem tamamlanamadı.');
  return result.data as T;
}

function download(text: string, name: string) {
  const url = URL.createObjectURL(new Blob([text], {type:'text/csv;charset=utf-8'}));
  const link = document.createElement('a'); link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function Page() {
  useApplicationAccessibility();
  const [dashboard,setDashboard] = useState<Dashboard>({batches:[],totals:{},quality:{status:'no_data',label:'Veri bekleniyor',dimensions:[],rules:[],modules:[],freshness:{},coverage:{}}});
  const [loaded,setLoaded] = useState(false),[error,setError] = useState(''),[busy,setBusy] = useState('');
  const [activeNav, setActiveNav] = useState<string>('cockpit');
  const [isDecisionGroupOpen, setIsDecisionGroupOpen] = useState(false);
  const [isResearchGroupOpen, setIsResearchGroupOpen] = useState(false);

  // Sync accordion expansion with current route
  useEffect(() => {
    const decisionList = ['insights', 'approvals', 'case_actions', 'results'];
    const researchList = ['sales_profit', 'products_categories', 'customers_360', 'salespeople', 'geography', 'returns_analysis', 'stock_operations', 'pricing_costs', 'purchasing_balance', 'cross_sell', 'forecasting'];

    if (decisionList.includes(activeNav)) {
      setIsDecisionGroupOpen(true);
      setIsResearchGroupOpen(false);
    } else if (researchList.includes(activeNav) || activeNav === 'research') {
      setIsResearchGroupOpen(true);
      setIsDecisionGroupOpen(false);
    }
  }, [activeNav]);

  // Guaranteed instant scroll to top on page navigation
  useEffect(() => {
    const mainEl = document.querySelector('.app-shell > main');
    if (mainEl) {
      mainEl.scrollTop = 0;
    }
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  }, [activeNav]);
  const [navReady,setNavReady] = useState(false);
  useEffect(()=>{try{const saved=sessionStorage.getItem('center-nav');if(saved)setActiveNav(saved==='anomalies'?'insights':saved==='actions'?'case_actions':saved)}catch{}setNavReady(true)},[]);
  useEffect(()=>{if(navReady){try{sessionStorage.setItem('center-nav',activeNav)}catch{}}},[activeNav,navReady]);
  const [linkedProduct,setLinkedProduct] = useState('');
  const [sourceReturn,setSourceReturn] = useState<string|null>(null);
  const [view,setView] = useState<'overview'|'import'|'history'|'report'>('overview');
  const [kind,setKind] = useState<Kind>('stock'),[file,setFile] = useState<File|null>(null),[encoding,setEncoding] = useState('utf-8-sig'),[delimiter,setDelimiter] = useState('auto');
  const [inspection,setInspection] = useState<Inspection|null>(null),[mapping,setMapping] = useState<number[]>([]);
  const [decimal,setDecimal] = useState(','),[dateFormat,setDateFormat] = useState('iso'),[snapshot,setSnapshot] = useState('');
  const [report,setReport] = useState<Report|null>(null),[step,setStep] = useState(1),[ack,setAck] = useState(false),[committed,setCommitted] = useState(false);
  const [issueCode,setIssueCode] = useState(''),[selected,setSelected] = useState<Issue|null>(null),[notice,setNotice] = useState('');
  const [analysisDate,setAnalysisDate] = useState(DEMO_ANALYSIS_DATE),[analysisMeta,setAnalysisMeta] = useState({defaultDate:DEMO_ANALYSIS_DATE,minDate:DEMO_MIN_DATE});
  const fileInput = useRef<HTMLInputElement>(null), dialog = useRef<HTMLDialogElement>(null);
  const receiveAnalysisMeta=useCallback((meta:{analysisDate:string;defaultDate:string;minDate:string;simulation:boolean})=>{
    setAnalysisMeta({defaultDate:DEMO_ANALYSIS_DATE,minDate:meta.minDate||DEMO_MIN_DATE});
  },[]);
  const navigateTo=useCallback((target:string,entityId?:string,sourceDate?:string)=>{
    setLinkedProduct(entityId||'');
    if(sourceDate)setAnalysisDate(sourceDate);
    setActiveNav(target==='anomalies'?'insights':target==='actions'?'case_actions':target);
  },[]);

  function openProfileDecision(id:string){try{sessionStorage.setItem('decision-scope','live');sessionStorage.setItem('decision-selected-insights',id)}catch{}setActiveNav('insights');}

  async function refresh(){ const d=await api<Dashboard>();setDashboard(d);setLoaded(true); }
  useEffect(()=>{refresh().catch(e=>{setError(e.message);setLoaded(true);});},[]);
  useEffect(()=>{ if(selected)dialog.current?.showModal();else dialog.current?.close(); },[selected]);
  async function run(label:string, fn:()=>Promise<void>){setBusy(label);setError('');try{await fn();}catch(e){setError((e as Error).message);}finally{setBusy('');}}
  function start(){setActiveNav('data_center');setView('import');setStep(1);setFile(null);setDelimiter('auto');setInspection(null);setReport(null);setCommitted(false);setAck(false);setError('');setNotice('');setIssueCode('');}
  function pick(f:File|undefined){ if(!f)return;if(!f.name.toLowerCase().endsWith('.csv')){setError('Lütfen .csv uzantılı bir dosya seçin.');return;}if(f.size>20*1024*1024){setError('Dosya en fazla 20 MB olabilir.');return;}setFile(f);setError(''); }
  async function inspectFile(){await run('Dosya okunuyor',async()=>{if(!file)throw new Error('Önce CSV dosyasını seçin.');const form=new FormData();form.set('file',file);form.set('kind',kind);form.set('encoding',encoding);form.set('delimiter',delimiter);const d=await api<Inspection>(form);setInspection(d);setMapping(d.mapping);setStep(2);});}
  async function analyzeFile(){await run('Kalite kontrolleri çalışıyor',async()=>{if(!inspection)return;const d=await api<Report>({action:'analyze',id:inspection.id,mapping,decimal,dateFormat,snapshot});setReport(d);setStep(3);setAck(false);setCommitted(false);setIssueCode('');});}
  async function commitFile(){await run('Veri aktarılıyor',async()=>{if(!report)return;await api({action:'commit',id:report.id,acknowledge:ack});setCommitted(true);setStep(4);await refresh();});}
  async function openReport(batch:Batch){await run('Kontrol sonucu açılıyor',async()=>{const d=await api<Report>({action:'report',id:batch.id});setReport(d);setCommitted(true);setActiveNav('data_center');setView('report');setIssueCode('');});}
  async function issuesPage(offset:number, code=issueCode){await run('Kayıtlar getiriliyor',async()=>{if(!report)return;const d=await api<Report>({action:'report',id:report.id,offset,code});setReport(d);setIssueCode(code);});}
  async function template(){await run('Şablon hazırlanıyor',async()=>{const schemas=await api<Record<Kind,string[]>>({action:'schema'});download('\ufeff'+schemas[kind].map(s=>'"'+s.replaceAll('"','""')+'"').join(',')+'\r\n',kind==='stock'?'stok-sablonu.csv':'hareket-sablonu.csv');});}

  const stock=dashboard.batches.find(b=>b.kind==='stock'), movement=dashboard.batches.find(b=>b.kind==='movement');
  const mapped=mapping.filter(i=>i>=0).length, mappingValid=inspection&&mapped===inspection.expected.length&&new Set(mapping).size===mapping.length;

  const TOP_NAV = [
    {
      id: 'cockpit',
      label: 'Anasayfa',
      icon: LayoutDashboard,
      description: 'Üst yönetim için anlık ticari özet, ciro köprüsü, net kârlılık ve kritik alarmlar.',
    },
    {
      id: 'decision_summary',
      label: 'Aksiyon Merkezi',
      icon: Target,
      description: 'Öncelikli kararlar, bekleyen onaylar ve izlenecek sonuçlar.',
    },
  ];

  const DECISION_PROCESS_NAV = [
    {
      id: 'insights',
      label: 'Sinyaller ve İçgörüler',
      icon: Zap,
      description: 'Ne değişti, neden önemli ve hangi karar öneriliyor?',
    },
    {
      id: 'approvals',
      label: 'Onay Kuyruğu',
      icon: ShieldCheck,
      description: 'İşlem kapsamını, sorumluyu ve başarı ölçütünü inceleyerek karar verin.',
    },
    {
      id: 'case_actions',
      label: 'Aksiyonlar',
      icon: ClipboardList,
      description: 'Onaylanmış görevleri uygulayın; yapılan işlemi ve takip tarihini kaydedin.',
    },
    {
      id: 'results',
      label: 'Sonuçlar ve Geri Bildirim',
      icon: CheckCircle2,
      description: 'Beklenen sonuçla gözlenen değişimi karşılaştırın; öğrenilenleri yeni karara taşıyın.',
    },
  ];

  const RESEARCH_NAV = [
    {
      id: 'sales_profit',
      label: 'Satış ve Kârlılık',
      icon: TrendingUp,
      description: 'Dönemsel satış hacmi, iadeler, brüt kâr, kâr marjı ve fiyat-miktar etki ayrıştırması.',
    },
    {
      id: 'products_categories',
      label: 'Ürün ve Kategori',
      icon: Package,
      description: 'En çok satanlar, ABC ürün sınıflandırması, yüksek ciro-düşük marj riski ve satışı duran ürünler.',
    },
    {
      id: 'customers_360',
      label: 'Müşteri 360',
      icon: Users,
      description: 'Müşteri yaşam süresi, sipariş alışveriş sıklığı, geciken müşteriler (churn riski) ve cari kârlılığı.',
    },
    {
      id: 'salespeople',
      label: 'Satıcı Performansı',
      icon: Award,
      description: 'Temsilci bazında net satış, kâr marjı, ortalama fatura büyüklüğü ve indirim alışkanlığı.',
    },
    {
      id: 'geography',
      label: 'Coğrafi Analiz',
      icon: MapPin,
      description: 'Şehir, posta kodu ve ülke kırılımında müşteri yoğunluğu, bölgesel ciro ve ürün yaygınlığı.',
    },
    {
      id: 'returns_analysis',
      label: 'İade Analizi',
      icon: RotateCcw,
      description: 'İade tutarı, oranı, etkilenen müşteri ve ürünlerle kaybedilen cironun ortak görünümü.',
    },
    {
      id: 'stock_operations',
      label: 'Stok Operasyonları',
      icon: Boxes,
      description: 'Satış hızına göre modellenen demo koli stoku, kapsama günü, kritik stok ve fazla stok senaryoları.',
    },
    {
      id: 'pricing_costs',
      label: 'Fiyat ve Maliyet',
      icon: Tag,
      description: 'Kayıtlı maliyet ile yerine koyma maliyeti farkı, hedef marj altında kalan ürünler ve fiyat açığı.',
    },
    {
      id: 'purchasing_balance',
      label: 'Satın Alma Planı',
      icon: Truck,
      description: 'Satın alma maliyetlerindeki değişim, eksik alım riski ve tedarik sonrası ürünlerin satış hızı.',
    },
    {
      id: 'cross_sell',
      label: 'Sepet ve Çapraz Satış',
      icon: ShoppingBag,
      description: 'Faturada birlikte satılan ürünler/kategoriler, sepet büyüklüğü trendi ve çapraz satış önerileri.',
    },
    {
      id: 'forecasting',
      label: 'Talep Öngörüleri',
      icon: Sparkles,
      description: 'Müşterinin sonraki sipariş tarihi tahmini, sipariş edilecek ürünler ve haftalık ürün talep projeksiyonu.',
    },
  ];

  const BOTTOM_NAV = [
    {
      id: 'data_center',
      label: 'Veri ve Etiketler',
      icon: Database,
      description: 'Kaynak, kalite ve etiket oluşma gerekçeleri.',
    },
  ];

  const ALL_NAV_ITEMS = [
    ...TOP_NAV,
    ...DECISION_PROCESS_NAV,
    ...RESEARCH_NAV,
    ...BOTTOM_NAV,
    { id: 'tags', label: 'Etiket Sözlüğü', icon: Tag, description: 'Verinin hangi kuralla sınıflandırıldığını ve kanıtını inceleyin.' },
    { id: 'research', label: 'Ticari İnceleme', icon: BarChart3, description: 'Kararları destekleyen uzman analizler.' },
  ];

  const decisionIds = ['insights', 'approvals', 'case_actions', 'results'];
  const researchIds = RESEARCH_NAV.map(i => i.id);
  const isDecisionGroupActive = decisionIds.includes(activeNav);
  const isResearchGroupActive = researchIds.includes(activeNav) || activeNav === 'research';
  const hubViews = ['decision_summary', 'insights', 'approvals', 'case_actions', 'results', 'tags'];

  const currentItem = ALL_NAV_ITEMS.find(i => i.id === activeNav) || ALL_NAV_ITEMS[0];
  const currentCategory = activeNav === 'cockpit' ? 'Genel Bakış'
    : activeNav === 'decision_summary' ? 'Aksiyon Merkezi'
    : isDecisionGroupActive ? 'Karar & Süreç'
    : isResearchGroupActive ? 'Ticari İnceleme'
    : (activeNav === 'data_center' || activeNav === 'tags') ? 'Veri ve Etiketler'
    : 'Yönetim';

  function qualityView(){
    const quality=dashboard.quality;
    if(!quality||quality.status==='no_data')return null;
    const tone=quality.status==='ready'?'success':quality.status==='correction'?'danger':'warning';
    const dimensionName:Record<string,string>={schema:'Şema',completeness:'Tamlık',validity:'Geçerlilik',consistency:'Tutarlılık'};
    return <section className="surface quality-center" aria-labelledby="quality-title">
      <div className="quality-heading"><div><div className="quality-title-line"><h2 id="quality-title">Veri sağlığı</h2><span className={'status '+tone}>{quality.label}</span></div><p className="subtle">Her boyut ayrı hesaplanır. Genel durum en düşük kalite kapısını ve veri güncelliğini dikkate alır.</p></div><ShieldCheck size={20}/></div>
      <div className="quality-grid"><div className="dimension-list">{quality.dimensions.map(d=><div className="dimension-row" key={d.key}><div className="dimension-top"><span><strong>{d.label}</strong><small>{d.description}</small><small className="dimension-evidence">{d.affected?d.affectedLabel:'Bulgu yok'}</small></span><b>{d.score.toLocaleString('tr-TR',{maximumFractionDigits:2})}%</b></div><div className="quality-track" role="progressbar" aria-label={`${d.label} ${d.score}%`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={d.score}><span className={d.score===100?'complete':d.score>=95?'mostly':'needs-work'} style={{width:`${d.score}%`}}/></div></div>)}</div>
      <div className="quality-context"><div><span>Hareket dönemi sonu</span><strong className={quality.freshness.movementStatus==='critical'?'red':''}>{quality.freshness.movementAgeDays==null?'Veri yok':quality.freshness.movementAgeDays===0?'Bugün':`${fmt(quality.freshness.movementAgeDays)} gün önce`}</strong><small>Son fatura tarihine göre</small></div><div><span>Stok güncelliği</span><strong className={quality.freshness.stockStatus==='critical'?'red':''}>{quality.freshness.stockAgeDays==null?'Veri yok':quality.freshness.stockAgeDays===0?'Bugün':`${fmt(quality.freshness.stockAgeDays)} gün önce`}</strong><small>Stok görüntü tarihine göre</small></div><div><span>Stoku bilinmeyen ambar</span><strong>{quality.coverage.unknownWarehouses?.length||0}</strong><small>{quality.coverage.unknownWarehouses?.join(', ')||'Hareket ve stok kapsamı eşleşiyor'}</small></div></div></div>
      <details className="quality-rules"><summary>Ölçüm parametreleri ve sonuçları</summary><div className="table-scroll"><table><thead><tr><th>Boyut</th><th>Kontrol</th><th>Etkilenen modül</th><th>Bulgu</th><th>Durum</th></tr></thead><tbody>{quality.rules.map(rule=><tr key={rule.code}><td>{dimensionName[rule.dimension]||rule.dimension}</td><td><strong>{rule.name}</strong><span className="cell-sub">{rule.code}</span></td><td>{rule.modules.join(', ')}</td><td className="numeric">{fmt(rule.count)}</td><td><span className={'status '+(rule.active?(rule.severity==='error'?'danger':'warning'):'success')}>{rule.active?'Bulgu var':'Geçti'}</span></td></tr>)}</tbody></table></div></details>
    </section>;
  }

  function issuesView(){if(!report)return null;return <>
    <div className="report-stats"><div><span>Kaynak satırı</span><strong>{fmt(report.total)}</strong></div><div><span>Aktarılabilir</span><strong className="green">{fmt(report.accepted)}</strong></div><div><span>Karantina</span><strong className={report.rejected?'red':''}>{fmt(report.rejected)}</strong></div><div><span>Uyarı bulgusu</span><strong>{fmt(report.warnings)}</strong></div></div>
    <p className="subtle explanation">Aktarılabilir satırlar uyarı içerebilir. Zorunlu alan, yapı veya dönüşüm hatalı satırlar karantinada kalır. Ham dosya korunur.</p>
    <div className="two-col report-columns"><section className="surface"><div className="section-head"><h2>Kontrol özeti</h2><ShieldCheck size={18}/></div>{!report.groups.length?<div className="all-good"><CheckCircle2/><p>Tanımlı kontrollerde sorun bulunmadı.</p></div>:<div className="control-list">{Object.entries(report.groups.reduce<Record<string,{count:number,severity:string}>>((a,g)=>{a[g.code]??={count:0,severity:g.severity};a[g.code].count+=g.count;if(g.severity==='error')a[g.code].severity='error';return a;},{})).map(([code,g])=><button key={code} className="control-item" onClick={()=>issuesPage(0,code)} disabled={!!busy}><span className={g.severity==='error'?'red':'amber'}>{g.severity==='error'?<TriangleAlert size={16}/>:<CircleHelp size={16}/>}</span><span>{groupNames[code]||code}</span><b>{fmt(g.count)}</b><ChevronRight size={15}/></button>)}</div>}<p className="footnote">Bulgular çakışabilir; toplamları etkilenen satır sayısı değildir.</p></section>
    <section className="surface"><div className="section-head"><h2>Kaynak kapsamı</h2><Layers3 size={18}/></div><dl className="facts"><div><dt>Dosya</dt><dd>{report.name}</dd></div><div><dt>Veri türü</dt><dd>{kindLabel(report.kind)}</dd></div><div><dt>{report.kind==='stock'?'Stok görüntüsü':'Fatura dönemi'}</dt><dd>{report.kind==='stock'?stamp(report.snapshot):report.range.length?report.range.map(d=>new Date(d+'T12:00:00').toLocaleDateString('tr-TR')).join(' — '):'Doğrulanamadı'}</dd></div><div><dt>Görünen ambarlar</dt><dd>{report.warehouses.join(', ')||'Yok'}</dd></div><div><dt>En az bir bulgusu olan satır</dt><dd>{fmt(report.affected)}</dd></div></dl><p className="footnote">Kapsam, karantinadaki satırları da içeren kaynak dosyayı gösterir. Ticari hesaplar henüz yapılmaz.</p></section></div>
    <section className="surface"><div className="section-head wrap"><div><h2>Kaynak satırı inceleme</h2><p className="subtle">Hücreyi ve hata nedenini birlikte inceleyin.</p></div><div className="inline-controls"><select aria-label="Kontrol filtresi" value={issueCode} onChange={e=>issuesPage(0,e.target.value)} disabled={!!busy}><option value="">Tüm kontroller</option>{Array.from(new Set(report.groups.map(g=>g.code))).map(c=><option key={c} value={c}>{groupNames[c]||c}</option>)}</select><button className="secondary small" disabled={!!busy||!report.groups.length} onClick={()=>run('Hata raporu hazırlanıyor',async()=>{const d=await api<{csv:string}>({action:'export',id:report.id});download(d.csv,'veri-kalite-raporu.csv');})}><ArrowDownToLine size={16}/> CSV indir</button></div></div>
    {!report.issueTotal?<div className="quiet-empty"><CheckCircle2 size={24}/><p>Bu görünümde kontrol bulgusu yok.</p></div>:<><div className="table-scroll"><table><thead><tr><th>Kaynak satır</th><th>Alan / ham değer</th><th>Kontrol</th><th>Durum</th><th><span className="sr-only">Detay</span></th></tr></thead><tbody>{report.issues.map((i,n)=><tr key={`${i.line}-${i.field}-${n}`}><td className="numeric">{i.line||'Başlık'}</td><td><strong>{i.field}</strong><span className="cell-sub">{i.raw||'Boş / satır kontrolü'}</span></td><td>{i.message}</td><td><span className={'status '+(i.severity==='error'?'danger':'warning')}>{i.severity==='error'?'Hata':'İncele'}</span></td><td><button aria-label={`${i.line}. satır ${i.field} detayını aç`} className="icon-button" onClick={()=>setSelected(i)}><ChevronRight size={18}/></button></td></tr>)}</tbody></table></div><div className="pagination"><span>{fmt(report.issueOffset+1)}–{fmt(Math.min(report.issueOffset+100,report.issueTotal))} / {fmt(report.issueTotal)} bulgu</span><div><button className="secondary small" disabled={!!busy||!report.issueOffset} onClick={()=>issuesPage(report.issueOffset-100)}>Önceki</button><button className="secondary small" disabled={!!busy||report.issueOffset+100>=report.issueTotal} onClick={()=>issuesPage(report.issueOffset+100)}>Sonraki</button></div></div></>}
    </section>
    <details className="surface preview-detail"><summary>Dönüşüm önizlemesi · ilk {report.preview.length} kayıt</summary><p className="subtle">Ham değer ile dönüştürülmüş değer yan yana. Boş değerler null olarak korunur; marjlar yüzde puandan orana çevrilir.</p>{report.preview.slice(0,3).map(r=><details key={r.line} className="record-preview"><summary>Kaynak satır {r.line} · {r.valid?'Aktarılabilir':'Karantina'}</summary><div className="table-scroll"><table><thead><tr><th>Alan</th><th>Ham değer</th><th>Dönüştürülen</th></tr></thead><tbody>{Object.keys(r.raw).map(h=><tr key={h}><td>{h}</td><td>{r.raw[h]||'Boş'}</td><td>{r.converted[h]??'null'}</td></tr>)}</tbody></table></div></details>)}</details>
  </>;}

  return <div className="app-shell" suppressHydrationWarning>
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="Ticari Öngörü ana sayfa">
        <span className="brand-icon"><Layers3 size={22}/></span>
        <span>öngörü<span className="brand-caption">Veriden ölçülen sonuca</span></span>
      </a>
      <div className="workspace">
        <span className="workspace-avatar">T</span>
        <span>Ticari çalışma alanı<small>Veri · Karar · Sonuç</small></span>
      </div>

      <nav aria-label="Ana gezinme">
        {/* Üst Menü: Anasayfa & Aksiyon Merkezi */}
        <div className="nav-group">
          {TOP_NAV.map(item => {
            const Icon = item.icon;
            const isActive = activeNav === item.id;
            return (
              <button
                key={item.id}
                className={'nav-sublink ' + (isActive ? 'active' : '')}
                aria-current={isActive ? 'page' : undefined}
                onClick={() => {
                  setActiveNav(item.id);
                  setLinkedProduct('');
                  setError('');
                  setIsDecisionGroupOpen(false);
                  setIsResearchGroupOpen(false);
                }}
              >
                <Icon size={16}/>
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Açılır / Kapanır 1: Karar & Süreç Yönetimi */}
        <div className="nav-group">
          <div className="nav-accordion">
            <button
              type="button"
              className={'nav-accordion-header ' + (isDecisionGroupActive ? 'active-parent' : '')}
              onClick={() => {
                if (!isDecisionGroupOpen || !isDecisionGroupActive) {
                  setIsDecisionGroupOpen(true);
                  setIsResearchGroupOpen(false);
                  if (!decisionIds.includes(activeNav)) {
                    setActiveNav('insights');
                    setLinkedProduct('');
                    setError('');
                  }
                } else {
                  setIsDecisionGroupOpen(false);
                }
              }}
              aria-expanded={isDecisionGroupOpen}
            >
              <span className="nav-accordion-title">
                <Zap size={16}/>
                <span>Karar & Süreç</span>
              </span>
              <span
                role="button"
                tabIndex={0}
                aria-label="Karar & Süreç menüsünü aç/kapat"
                className="chevron-hitbox"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsDecisionGroupOpen(v => !v);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.stopPropagation();
                    setIsDecisionGroupOpen(v => !v);
                  }
                }}
              >
                <ChevronDown
                  size={15}
                  className={'nav-accordion-chevron ' + (isDecisionGroupOpen ? 'expanded' : '')}
                />
              </span>
            </button>
            {isDecisionGroupOpen && (
              <div className="nav-accordion-body">
                {DECISION_PROCESS_NAV.map(item => {
                  const Icon = item.icon;
                  const isActive = activeNav === item.id;
                  return (
                    <button
                      key={item.id}
                      className={'nav-sublink-nested ' + (isActive ? 'active' : '')}
                      aria-current={isActive ? 'page' : undefined}
                      onClick={() => {
                        setActiveNav(item.id);
                        setLinkedProduct('');
                        setError('');
                      }}
                    >
                      <Icon size={15}/>
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Açılır / Kapanır 2: Ticari İnceleme */}
        <div className="nav-group">
          <div className="nav-accordion">
            <button
              type="button"
              className={'nav-accordion-header ' + (isResearchGroupActive ? 'active-parent' : '')}
              onClick={() => {
                if (!isResearchGroupOpen || !isResearchGroupActive) {
                  setIsResearchGroupOpen(true);
                  setIsDecisionGroupOpen(false);
                  if (!researchIds.includes(activeNav)) {
                    setActiveNav('sales_profit');
                    setLinkedProduct('');
                    setError('');
                  }
                } else {
                  setIsResearchGroupOpen(false);
                }
              }}
              aria-expanded={isResearchGroupOpen}
            >
              <span className="nav-accordion-title">
                <BarChart3 size={16}/>
                <span>Ticari İnceleme</span>
              </span>
              <span
                role="button"
                tabIndex={0}
                aria-label="Ticari İnceleme menüsünü aç/kapat"
                className="chevron-hitbox"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsResearchGroupOpen(v => !v);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.stopPropagation();
                    setIsResearchGroupOpen(v => !v);
                  }
                }}
              >
                <ChevronDown
                  size={15}
                  className={'nav-accordion-chevron ' + (isResearchGroupOpen ? 'expanded' : '')}
                />
              </span>
            </button>
            {isResearchGroupOpen && (
              <div className="nav-accordion-body">
                {RESEARCH_NAV.map(item => {
                  const Icon = item.icon;
                  const isActive = activeNav === item.id;
                  return (
                    <button
                      key={item.id}
                      className={'nav-sublink-nested ' + (isActive ? 'active' : '')}
                      aria-current={isActive ? 'page' : undefined}
                      onClick={() => {
                        setActiveNav(item.id);
                        setLinkedProduct('');
                        setError('');
                      }}
                    >
                      <Icon size={15}/>
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Alt Menü: Veri ve Etiketler */}
        <div className="nav-group">
          {BOTTOM_NAV.map(item => {
            const Icon = item.icon;
            const isActive = activeNav === item.id || activeNav === 'tags';
            return (
              <button
                key={item.id}
                className={'nav-sublink ' + (isActive ? 'active' : '')}
                aria-current={isActive ? 'page' : undefined}
                onClick={() => {
                  setActiveNav(item.id);
                  setLinkedProduct('');
                  setError('');
                  setView('overview');
                  setIsDecisionGroupOpen(false);
                  setIsResearchGroupOpen(false);
                }}
              >
                <Icon size={16}/>
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      <div className="sidebar-bottom">
        <ShieldCheck size={18}/>
        <div>Veri sizin kontrolünüzde<small>Dosyalar bu bilgisayarda saklanır.</small></div>
      </div>
    </aside>

    <main>
      <header className="topbar">
        <div className="breadcrumb">
          <button
            type="button"
            className="breadcrumb-btn"
            onClick={() => {
              setActiveNav('cockpit');
              setLinkedProduct('');
              setError('');
              setIsDecisionGroupOpen(false);
              setIsResearchGroupOpen(false);
            }}
          >
            Çalışma alanı
          </button>
          <ChevronRight size={14}/>
          {isDecisionGroupActive ? (
            <button
              type="button"
              className="breadcrumb-btn"
              onClick={() => {
                setActiveNav('insights');
                setIsDecisionGroupOpen(true);
                setIsResearchGroupOpen(false);
              }}
            >
              Karar & Süreç
            </button>
          ) : isResearchGroupActive ? (
            <button
              type="button"
              className="breadcrumb-btn"
              onClick={() => {
                setActiveNav('sales_profit');
                setIsResearchGroupOpen(true);
                setIsDecisionGroupOpen(false);
              }}
            >
              Ticari İnceleme
            </button>
          ) : (
            <span>{currentCategory}</span>
          )}
          <ChevronRight size={14}/>
          <strong>{currentItem.label}</strong>
        </div>
        <div className="top-meta">
          <label className="analysis-date-control" title="Dönemsel sinyal, gecikme ve tahmin hesaplarının değerlendirildiği demo tarihi">
            <CalendarDays size={15}/><span>Analiz tarihi</span>
            <input type="date" aria-label="Demo analiz tarihi" min={analysisMeta.minDate} max={analysisMeta.defaultDate} value={analysisDate} onChange={e=>setAnalysisDate(e.target.value||DEMO_ANALYSIS_DATE)}/>
            {analysisDate!==DEMO_ANALYSIS_DATE&&<b>Simülasyon</b>}
            {analysisDate!==DEMO_ANALYSIS_DATE&&<button type="button" onClick={()=>setAnalysisDate(DEMO_ANALYSIS_DATE)}>30.12.2024’e dön</button>}
          </label>
          <span className="local-dot"/>Güvenli çalışma alanı<span className="user-avatar">T</span>
        </div>
      </header>

      <div className="page-content">
        <div className="page-heading">
          <div>
            
            <h1>{activeNav === 'data_center' ? (view==='history'?'Aktarım geçmişi':view==='import'?'CSV veri aktarımı':view==='report'?'Veri kalite raporu':'Veri ve Etiketler') : currentItem.label}</h1>
            <p>{activeNav === 'data_center' ? (view==='overview'?'Güvenilir analizler, doğru hazırlanmış veriyle başlar.':view==='history'?'Kaynak dosyaları, aktarım sonuçları ve kalite kayıtları.':view==='report'?report?.name:'Dosyanızı eşleştirin, kontrol edin ve onaylayarak aktarın.') : currentItem.description}</p>
          </div>
          {activeNav === 'data_center' && view !== 'import' && (
            <button className="primary" onClick={start} disabled={!!busy}><Plus size={18}/>CSV ekle</button>
          )}
        </div>

        {error&&<div className="alert error" role="alert"><TriangleAlert size={20}/><span>{error}</span><button aria-label="Hata mesajını kapat" onClick={()=>setError('')}><X size={16}/></button></div>}
        {notice&&<div className="alert info" role="status">{notice}</div>}
        {busy&&<div className="working" role="status"><LoaderCircle className="spin" size={17}/>{busy}…</div>}

        {activeNav==='data_center'&&view==='report'&&sourceReturn&&<button className="secondary" onClick={()=>setActiveNav(sourceReturn)}>Karar dosyasına dön</button>}
        {activeNav==='decision_summary'&&<ResearchShortcuts onNavigate={navigateTo}/>}
        
        {['data_center','tags'].includes(activeNav)&&<div className="data-section-tabs" role="group" aria-label="Veri merkezi bölümleri"><button aria-pressed={activeNav==='data_center'} onClick={()=>{setActiveNav('data_center');setView('overview')}}>Kaynaklar ve kalite</button><button aria-pressed={activeNav==='tags'} onClick={()=>setActiveNav('tags')}>Etiket sözlüğü</button></div>}
        {!loaded ? (
          <div className="skeleton" aria-label="Yükleniyor"><div/><div/><div/></div>
        ) : activeNav === 'research' ? (
          <ResearchLibrary onNavigate={navigateTo}/>
        ) : hubViews.includes(activeNav) ? (
          <DecisionHub key={activeNav} view={activeNav as HubView} analysisDate={analysisDate} onNavigate={navigateTo} onSource={id=>{const batch=dashboard.batches.find(b=>b.id===id);if(batch){setSourceReturn(activeNav);void openReport(batch);}else setError('Kaynak raporu bulunamadı.')}}/>
        ) : activeNav === 'cockpit' ? (
          <ManagementCockpit onNavigate={navigateTo}/>
        ) : activeNav === 'products_categories' ? (
          <ProductCenter onDecision={openProfileDecision} onCustomer={code=>navigateTo('customers_360',code)} analysisDate={analysisDate} initialCode={linkedProduct} onStock={code=>{setLinkedProduct(code);setActiveNav('stock_operations')}}/>
        ) : activeNav === 'stock_operations' ? (
          <StockCenter analysisDate={analysisDate} initialCode={linkedProduct}/>
        ) : activeNav === 'customers_360' ? (
          <CustomerCenter onDecision={openProfileDecision} initialCode={linkedProduct} analysisDate={analysisDate} onProduct={code=>{setLinkedProduct(code);setActiveNav('products_categories')}}/>
        ) : activeNav === 'pricing_costs' ? (
          <PricingCenter analysisDate={analysisDate} initialCode={linkedProduct} onProduct={code=>{setLinkedProduct(code);setActiveNav('products_categories')}}/>
        ) : activeNav === 'salespeople' ? (
          <SellerCenter/>
        ) : ['returns_analysis','geography','purchasing_balance','cross_sell'].includes(activeNav) ? (
          <OperationsCenter onOpenStock={code=>{setLinkedProduct(code);setActiveNav('stock_operations')}} module={activeNav as OperationsModule} analysisDate={analysisDate} onOpenProduct={code=>{setLinkedProduct(code);setActiveNav('products_categories')}}/>
        ) : activeNav === 'forecasting' ? (
          <ForecastingCenter analysisDate={analysisDate} onOpenProduct={code=>{setLinkedProduct(code);setActiveNav('products_categories')}} onNavigate={navigateTo}/>
        ) : activeNav === 'sales_profit' ? (
          <ProfitabilityCenter onNavigate={navigateTo}/>
        ) : activeNav !== 'data_center' ? (
          <p>Gezinmeden bir merkez seçin.</p>
        ) : view === 'overview' ? (
          <>
            <div className="intro-strip">
              <span className="intro-icon"><ShieldCheck size={22}/></span>
              <div>
                <strong>{dashboard.batches.length?`Veri durumu: ${dashboard.quality.label}`:'Veri merkeziniz hazır'}</strong>
                <p>{dashboard.batches.length?'Son stok ve hareket kaynakları kalite kapılarına göre değerlendirildi.':'İlk CSV dosyanızı ekleyerek veri sağlığını görmeye başlayın.'}</p>
              </div>
              <span className={'status '+(dashboard.quality.status==='ready'?'success':dashboard.quality.status==='correction'?'danger':dashboard.quality.status==='partial'?'warning':'neutral')}>
                {dashboard.batches.length?'Son kaynaklar':'Henüz veri yok'}
              </span>
            </div>

            <div className="overview-metrics">
              <div><span><FileSpreadsheet size={16}/>Hareket kayıtları</span><strong>{fmt(dashboard.totals.movement||0)}</strong><small>Aktarılan geçerli satır</small></div>
              <div><span><Package size={16}/>Son stok görüntüsü</span><strong>{stock?fmt(stock.accepted):'—'}</strong><small>{stock?stamp(stock.snapshot):'Stok dosyası bekleniyor'}</small></div>
              <div><span><FolderInput size={16}/>Kaynak dosyalar</span><strong>{fmt(dashboard.batches.length)}</strong><small>Onaylanan aktarım</small></div>
              <div><span><TriangleAlert size={16}/>Karantina kayıtları</span><strong>{fmt(dashboard.batches.reduce((n,b)=>n+b.rejected,0))}</strong><small>Kaynak dosyada korunan satır</small></div>
            </div>

            {qualityView()}

            <div className="two-col overview-columns">
              <section className="surface">
                <div className="section-head">
                  <div><h2>Veri kaynakları</h2><p className="subtle">İki kaynak, ortak bir kontrol noktası.</p></div>
                  <Database size={19}/>
                </div>
                {(['stock','movement'] as Kind[]).map(k=>{
                  const b=k==='stock'?stock:movement;
                  const I=k==='stock'?Package:FileSpreadsheet;
                  return (
                    <div className="source-item" key={k}>
                      <div className="file-icon"><I size={22}/></div>
                      <div className="source-info">
                        <strong>{kindLabel(k)} verisi</strong>
                        <p>{b?b.name:`${k==='stock'?'10':'32'} kolon · CSV dosyası`}</p>
                        {b&&<small>{fmt(b.accepted)} kayıt · {stamp(b.created)}</small>}
                      </div>
                      {b?<button className="text-button" onClick={()=>openReport(b)} disabled={!!busy}>İncele<ChevronRight size={15}/></button>:<button className="secondary small" onClick={()=>{setKind(k);start();}}>Ekle<Plus size={14}/></button>}
                    </div>
                  );
                })}
                <div className="source-footer"><LockKeyhole size={14}/>Ham dosyalar değişmeden saklanır.</div>
              </section>

              <section className="surface">
                <div className="section-head">
                  <div><h2>Modül hazırlığı</h2><p className="subtle">Alan doluluğuna göre ölçülen kullanılabilirlik.</p></div>
                  <Layers3 size={19}/>
                </div>
                <div className="module-list">
                  {dashboard.quality.modules.map(module=>(
                    <div className="readiness" key={module.name}>
                      <div>
                        <span>{module.name}</span>
                        <span className={'status '+(module.status==='ready'?'success':module.status==='partial'?'warning':'neutral')}>{module.label} · %{module.coverage.toLocaleString('tr-TR')}</span>
                      </div>
                      <p>{module.note}</p>
                    </div>
                  ))}
                </div>
              </section>
            </div>

            <section className="surface">
              <div className="section-head">
                <div><h2>Son aktarımlar</h2><p className="subtle">Dosyadan kaynak satırına kadar izlenebilir.</p></div>
                {dashboard.batches.length>0&&<button className="text-button" onClick={()=>setView('history')}>Tümünü gör<ArrowRight size={16}/></button>}
              </div>
              {!dashboard.batches.length?(
                <div className="empty-upload">
                  <div className="empty-icon"><UploadCloud size={32}/></div>
                  <h3>İlk dosyanızla başlayalım</h3>
                  <p>Stok veya hareket CSV dosyanızı ekleyin.<br/>Kolonları ve kalite sonuçlarını aktarmadan önce göreceksiniz.</p>
                  <button className="primary" onClick={start}><Plus size={17}/>CSV dosyası ekle</button>
                  <small>Noktalı virgül (;) veya virgülle (,) ayrılmış CSV · En fazla 20 MB / 100.000 satır</small>
                </div>
              ):historyTable(dashboard.batches.slice(0,5))}
            </section>
          </>
        ) : view==='history' ? (
          <section className="surface">
            <div className="section-head">
              <h2>Onaylanan aktarımlar</h2>
              <span className="subtle">{dashboard.batches.length} dosya</span>
            </div>
            {dashboard.batches.length?historyTable(dashboard.batches):(
              <div className="quiet-empty">
                <Clock3 size={30}/>
                <h3>Henüz aktarım yapılmadı</h3>
                <p>Onayladığınız dosyalar burada listelenecek.</p>
                <button className="primary" onClick={start}>İlk CSV dosyasını ekle</button>
              </div>
            )}
          </section>
        ) : view==='report' ? (
          <>
            <button className="text-button back" onClick={()=>setView('history')}><ArrowLeft size={16}/>Aktarım geçmişine dön</button>
            {issuesView()}
          </>
        ) : (
          <>
            {step<4&&<button className="text-button back" disabled={!!busy} onClick={()=>{setView('overview');setError('');}}><ArrowLeft size={16}/>Veri Merkezi&apos;ne dön</button>}
            <ol className="stepper">{['Dosya seçimi','Kolon eşleştirme','Kalite kontrolü','Aktarım sonucu'].map((label,i)=><li className={step===i+1?'current':step>i+1?'done':''} key={label} aria-current={step===i+1?'step':undefined}><span>{step>i+1?<Check size={15}/>:i+1}</span>{label}</li>)}</ol>
            {step===1?(
              <section className="surface upload-section">
                <div className="section-head">
                  <div><h2>Hangi veriyi eklemek istiyorsunuz?</h2><p className="subtle">Dosya türüne göre kolon şablonu ve kontroller değişir.</p></div>
                </div>
                <div className="type-options">
                  {(['stock','movement'] as Kind[]).map(k=>(
                    <button className={kind===k?'selected':''} key={k} aria-pressed={kind===k} disabled={!!busy} onClick={()=>setKind(k)}>
                      {k==='stock'?<Package size={25}/>:<FileSpreadsheet size={25}/>}
                      <span><strong>{kindLabel(k)} verisi</strong><small>{k==='stock'?'Ambar, ürün ve anlık stok · 10 kolon':'Fatura, müşteri ve işlemler · 32 kolon'}</small></span>
                      <span className="radio-indicator">{kind===k&&<span/>}</span>
                    </button>
                  ))}
                </div>
                <div className={'dropzone '+(file?'has-file':'')} onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();if(!busy)pick(e.dataTransfer.files[0]);}}>
                  <UploadCloud size={34}/>
                  <h3>{file?file.name:'CSV dosyanızı buraya bırakın'}</h3>
                  <p>{file?`${(file.size/1024).toLocaleString('tr-TR',{maximumFractionDigits:1})} KB · Kontrol edilmeyi bekliyor`:'Noktalı virgül (;) veya virgülle (,) ayrılmış dosyalar desteklenir.'}</p>
                  <button className="secondary" disabled={!!busy} onClick={()=>fileInput.current?.click()}>{file?'Dosyayı değiştir':'Bilgisayardan seç'}</button>
                  <input ref={fileInput} className="sr-only" type="file" accept=".csv,text/csv" onChange={e=>pick(e.target.files?.[0])} disabled={!!busy}/>
                  <small>En fazla 20 MB ve 100.000 veri satırı</small>
                </div>
                <div className="upload-settings">
                  <label>Karakter kodlaması
                    <select value={encoding} onChange={e=>setEncoding(e.target.value)} disabled={!!busy}>
                      <option value="utf-8-sig">UTF-8 (BOM destekli)</option>
                      <option value="cp1254">Windows-1254 (Türkçe)</option>
                      <option value="utf-16">UTF-16</option>
                    </select>
                  </label>
                  <label>Kolon ayracı
                    <select value={delimiter} onChange={e=>setDelimiter(e.target.value)} disabled={!!busy}>
                      <option value="auto">Otomatik algıla (Önerilen)</option>
                      <option value=";">Noktalı virgül ( ; )</option>
                      <option value=",">Virgül ( , )</option>
                    </select>
                  </label>
                  <button className="text-button" onClick={template} disabled={!!busy}><ArrowDownToLine size={16}/>Boş {kindLabel(kind).toLocaleLowerCase('tr-TR')} şablonunu indir</button>
                </div>
                <div className="hint">
                  <CircleHelp size={17}/>
                  <p>Noktalı virgül (;) ve virgül (,) ayracı desteklenir. Ayraç içeren hücreler çift tırnak içinde olmalı (örn: <code>&quot;12,50&quot;</code>). Kodlardaki baştaki sıfırlar korunur.</p>
                </div>
                <div className="form-actions">
                  <span>Dosya bu bilgisayarda incelenir.</span>
                  <button className="primary" disabled={!file||!!busy} onClick={inspectFile}>Dosyayı önizle<ArrowRight size={17}/></button>
                </div>
              </section>
            ):step===2&&inspection?(
              <>
                {inspection.previous&&<div className="alert error"><TriangleAlert size={20}/><span>Bu dosya {stamp(inspection.previous.created)} tarihinde aktarıldı. Aynı dosya tekrar aktarılamaz.</span></div>}
                <section className="surface">
                  <div className="section-head wrap">
                    <div><h2>Kolonları doğrulayın</h2><p className="subtle">{inspection.name} · {fmt(inspection.total)} satır · {inspection.headers.length} kaynak kolon</p></div>
                    <span className={'status '+(mappingValid?'success':'warning')}>{mapped}/{inspection.expected.length} eşleşme</span>
                  </div>
                  <div className="hint">
                    <FileCheck2 size={18}/>
                    <p>{inspection.exactOrder?'Başlıklar ve sıraları paylaşılan şemayla birebir eşleşiyor.':inspection.duplicateHeaders.length?'Yinelenen kaynak başlıkları var. Kolon numaralarını kontrol ederek eşleştirmeleri tamamlayın.':'Kaynak başlıkları veya sıraları şemadan farklı. Önerilen eşleştirmeleri kontrol edin; konuma göre sessizce eşleştirme yapılmaz.'}</p>
                  </div>
                  <div className="table-scroll mapping-table">
                    <table>
                      <thead><tr><th>Sıra</th><th>Sistem alanı</th><th>Kaynak kolon</th><th>Tür</th></tr></thead>
                      <tbody>
                        {inspection.fields.map((f,i)=>(
                          <tr key={f.name}>
                            <td className="numeric">{i+1}</td>
                            <td><strong>{f.name}</strong>{f.required&&<span className="cell-sub">Zorunlu değer</span>}</td>
                            <td>
                              <select aria-label={`${f.name} kaynak kolonu`} value={mapping[i]} disabled={!!busy} onChange={e=>setMapping(m=>m.map((v,j)=>j===i?Number(e.target.value):v))}>
                                <option value={-1}>Kolon seçin</option>
                                {inspection.headers.map((h,j)=><option key={j} value={j}>{j+1}. {h||'(Boş başlık)'}</option>)}
                              </select>
                            </td>
                            <td><span className="type-tag">{f.type==='number'?'Sayı':f.type==='date'?'Tarih':'Metin'}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
                <section className="surface">
                  <h2>Dönüşüm ayarları</h2>
                  <div className="settings-grid">
                    <label>Ondalık ayracı
                      <select value={decimal} onChange={e=>setDecimal(e.target.value)} disabled={!!busy}>
                        <option value=",">Virgül · 1.234,56</option>
                        <option value=".">Nokta · 1,234.56</option>
                      </select>
                    </label>
                    {kind==='movement'?(
                      <label>Fatura tarihi biçimi
                        <select value={dateFormat} onChange={e=>setDateFormat(e.target.value)} disabled={!!busy}>
                          <option value="iso">Yıl-Ay-Gün · 2023-01-02 (2023-01-02 00:00:00.000 dahil)</option>
                          <option value="dmy">Gün.Ay.Yıl · 31.08.2026</option>
                          <option value="slash">Gün/Ay/Yıl · 31/08/2026</option>
                        </select>
                      </label>
                    ):(
                      <label>Stok görüntü tarihi ve saati (İsteğe bağlı)
                        <input type="datetime-local" value={snapshot} onChange={e=>setSnapshot(e.target.value)} disabled={!!busy}/>
                        <small>Belirtilmezse yükleme anı kullanılır.</small>
                      </label>
                    )}
                  </div>
                  <p className="footnote">Miktar ve içerik otomatik çarpılmaz. {kind==='movement'?'Marj alanları yüzde puan kabul edilir: 26,87 değeri 0,2687 olarak saklanır.':''} Kaynak değerler ayrıca korunur.</p>
                </section>
                <details className="surface preview-detail">
                  <summary>Ham veri önizlemesi · ilk {inspection.preview.length} satır</summary>
                  <div className="table-scroll">
                    <table>
                      <thead><tr><th>Satır</th>{inspection.headers.map((h,i)=><th key={i}>{h||'Boş başlık'}</th>)}</tr></thead>
                      <tbody>{inspection.preview.map(r=><tr key={r.line}><td>{r.line}</td>{r.values.map((v,i)=><td key={i}>{v||'Boş'}</td>)}</tr>)}</tbody>
                    </table>
                  </div>
                </details>
                <div className="form-actions">
                  <button className="secondary" disabled={!!busy} onClick={()=>setStep(1)}><ArrowLeft size={16}/>Dosya seçimine dön</button>
                  <button className="primary" disabled={!!busy||!mappingValid||!!inspection.previous} onClick={analyzeFile}>Kalite kontrollerini çalıştır<ArrowRight size={17}/></button>
                </div>
              </>
            ):step===3&&report?(
              <>
                {issuesView()}
                <section className="surface confirmation">
                  <h2>Aktarım onayı</h2>
                  <p><strong>{fmt(report.accepted)} satır</strong> aktarılacak. <strong>{fmt(report.rejected)} hatalı satır</strong> ham dosya ve kalite raporunda korunacak, veri tablosuna alınmayacak.</p>
                  {(report.warnings>0||report.rejected>0)&&<label className="checkbox"><input type="checkbox" checked={ack} onChange={e=>setAck(e.target.checked)} disabled={!!busy}/><span>Uyarıları ve karantina kapsamını inceledim. Uyarılı satırların aktarılmasını onaylıyorum.</span></label>}
                  <div className="form-actions">
                    <button className="secondary" disabled={!!busy} onClick={()=>setStep(2)}><ArrowLeft size={16}/>Eşleştirmeyi düzenle</button>
                    <button className="primary" disabled={!!busy||!report.accepted||((report.warnings>0||report.rejected>0)&&!ack)} onClick={commitFile}><Check size={17}/>Onayla ve aktar</button>
                  </div>
                </section>
              </>
            ):step===4&&committed&&report?(
              <section className="surface completed">
                <div className="success-icon"><CheckCircle2 size={36}/></div>
                <h2>Aktarım tamamlandı</h2>
                <p>{report.name}</p>
                <div className="completion-count">{fmt(report.accepted)} <span>kayıt aktarıldı</span></div>
                <p>{report.rejected?`${fmt(report.rejected)} satır karantinada. Kaynak dosya ve hata raporu korundu.`:'Ham dosya ve kontrol sonuçları kayıt altında.'}</p>
                <div className="inline-controls">
                  <button className="secondary" onClick={()=>{setView('report');setIssueCode('');}}>Kalite raporunu aç</button>
                  <button className="primary" onClick={()=>setView('overview')}>Veri Merkezi&apos;ne dön<ArrowRight size={17}/></button>
                </div>
              </section>
            ):null}
          </>
        )}

        <footer className="page-footer">
          <span>Ticari Öngörü Platformu · {currentCategory} &gt; {currentItem.label}</span>
          <span>Veriler cihazda güvenle saklanır · Euro bazlı karar desteği</span>
        </footer>
      </div>
    </main>

    <dialog ref={dialog} onCancel={()=>setSelected(null)} onClose={()=>setSelected(null)}>
      <div className="dialog-heading">
        <h2>Kaynak kayıt inceleme</h2>
        <button className="icon-button" aria-label="Detayı kapat" onClick={()=>setSelected(null)}><X size={20}/></button>
      </div>
      {selected&&(
        <>
          <span className={'status '+(selected.severity==='error'?'danger':'warning')}>{selected.severity==='error'?'Aktarımı engelleyen hata':'Doğrulama gerekli'}</span>
          <dl className="facts">
            <div><dt>Kaynak dosya</dt><dd>{report?.name}</dd></div>
            <div><dt>Fiziksel satır</dt><dd>{selected.line||'Başlık'} (çok satırlı hücrelerde son satır)</dd></div>
            <div><dt>Alan</dt><dd>{selected.field}</dd></div>
            <div><dt>Ham değer</dt><dd className="raw-value">{selected.raw||'Boş / satır kontrolü'}</dd></div>
            <div><dt>Bulgu</dt><dd>{selected.message}</dd></div>
          </dl>
          <div className="hint"><ShieldCheck size={17}/><p>Kaynak kayıt değiştirilmedi. Düzeltmeyi kaynak CSV üzerinde yapıp yeniden kontrol edin.</p></div>
        </>
      )}
    </dialog>
  </div>;

  function historyTable(batches:Batch[]){
    return (
      <div className="table-scroll">
        <table>
          <thead>
            <tr><th>Dosya / tür</th><th>Aktarım zamanı</th><th>Aktarılan</th><th>Karantina</th><th>Sonuç</th><th/></tr>
          </thead>
          <tbody>
            {batches.map(b=>(
              <tr key={b.id}>
                <td><strong>{b.name}</strong><span className="cell-sub">{kindLabel(b.kind)}</span></td>
                <td>{stamp(b.created)}</td>
                <td className="numeric">{fmt(b.accepted)}</td>
                <td className="numeric">{fmt(b.rejected)}</td>
                <td><span className={'status '+(b.rejected||b.warnings?'warning':'success')}>{b.rejected?'Kısmi aktarım':b.warnings?'Uyarıyla aktarıldı':'Tamamlandı'}</span></td>
                <td><button className="text-button" onClick={()=>openReport(b)} disabled={!!busy}>İncele<ChevronRight size={16}/></button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
}
