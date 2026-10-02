'use client';
import {ArrowRight,Users,PackageSearch,ChartNoAxesCombined,Search} from 'lucide-react';
import './entity-profiles.css';

const groups=[
  {title:'Müşteri ve pazar',description:'Kiminle çalışıyoruz, ne satın alıyor ve ilişki nasıl değişiyor?',items:[
    ['customers_360','Müşteri 360','Profil, RFM, alışveriş ritmi, ürün ilişkileri, kârlılık ve fatura geçmişi'],
    ['salespeople','Satıcı performansı','Temsilci portföyü, satış katkısı, indirim ve müşteri dağılımı'],
    ['geography','Coğrafi analiz','Şehir ve ülke kırılımında müşteri yoğunluğu ve ticari katkı'],
    ['cross_sell','Sepet ve çapraz satış','Birlikte alınan ürünler, ilişki gücü ve teklif fırsatları']]},
  {title:'Ürün ve tedarik',description:'Hangi ürün, hangi müşteride değer yaratıyor; stok ve alım kararı ne olmalı?',items:[
    ['products_categories','Ürün 360 ve kategori','ABC, kategori katkısı, fiyat/maliyet seyri, müşteri ve kaynak hareketleri'],
    ['stock_operations','Stok ve tüketim','Kapsama, tüketim hızı, stok modeli, miktar ve kaynak bilgisi'],
    ['purchasing_balance','Satın alma planı','Alım ihtiyacı, önerilen koli ve tahmini alım ekonomisi']]},
  {title:'Satış ve kârlılık',description:'Ciroyu, marjı ve kaybı oluşturan bileşenleri birlikte araştırın.',items:[
    ['sales_profit','Satış ve kârlılık','Ciro köprüsü, dönemsel değişim ve ürün/müşteri kâr katkısı'],
    ['pricing_costs','Fiyat ve maliyet','Fiyat koridoru, yerine koyma marjı ve müşteri fiyat sapmaları'],
    ['returns_analysis','İade analizi','İade kaybı, ürünler ve etkilenen müşteriler'],
    ['cockpit','Genel göstergeler','Satış, kâr, fatura ve performansın ayrıntılı yönetim görünümü']]},
  {title:'Öngörüler',description:'Gelecek dönem beklentisini geçmiş veri ve model güveniyle değerlendirin.',items:[
    ['forecasting','Talep ve sipariş öngörüleri','Ürün/kategori talebi, müşteri sipariş beklentisi ve model doğrulaması']]},
];
export function ResearchShortcuts({onNavigate}:{onNavigate:(target:string)=>void}){
  return <section className="research-shortcuts" aria-label="Detaylı analizlere hızlı erişim"><div><Search size={18}/><span><strong>Kararın arkasını araştırın</strong><small>Müşteriyi tanıyın, ürünü inceleyin, kanıttan karar hazırlayın.</small></span></div><button onClick={()=>onNavigate('customers_360')}><Users size={17}/>Müşteri 360</button><button onClick={()=>onNavigate('products_categories')}><PackageSearch size={17}/>Ürün 360</button><button onClick={()=>onNavigate('research')}>Tüm analizler<ArrowRight size={16}/></button></section>;
}
export default function ResearchLibrary({onNavigate}:{onNavigate:(target:string)=>void}){
  return <div className="research-library"><section className="research-intro"><ChartNoAxesCombined size={28}/><div><h2>Önce tanıyın. Sonra karar verin.</h2><p>Toplamlardan müşteri ve ürün profiline, profilden işlem kayıtlarına inin. Bulguyu karar dosyasına taşıdığınızda kaynak ve analiz tarihi birlikte korunur.</p><p className="research-source-note">Bu analizler yüklenmiş veriyi kullanır. Hazır karar demo örneklerinden ayrı değerlendirilir.</p></div></section><ResearchShortcuts onNavigate={onNavigate}/>{groups.map(group=><section className="research-library-group" key={group.title}><header><h3>{group.title}</h3><p>{group.description}</p></header><div>{group.items.map(([id,name,description])=><button key={id} onClick={()=>onNavigate(id)}><span><strong>{name}</strong><small>{description}</small></span><ArrowRight size={18}/></button>)}</div></section>)}</div>;
}
