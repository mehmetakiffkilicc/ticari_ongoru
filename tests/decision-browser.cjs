// Run on an isolated DATA_DIR server. This resets demo fixtures only.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/Akif/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const base=process.env.TEST_URL||'http://127.0.0.1:3011';
(async()=>{
  const browser=await chromium.launch({channel:'msedge',headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.setDefaultTimeout(15000);
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const nav=name=>page.getByRole('navigation',{name:'Ana gezinme'}).getByRole('button',{name,exact:true});
  const step=name=>page.getByRole('navigation',{name:'Karar hattı'}).getByRole('button',{name:new RegExp(name)});
  const settled=()=>page.locator('.case-hub[aria-busy="false"]').waitFor();
  async function api(data){const r=await page.request.post(base+'/api/data',{data});const out=await r.json();assert.equal(out.ok,true,JSON.stringify(out));return out.data}
  try{
    fs.mkdirSync('test-results',{recursive:true});
    await page.route('https://fonts.googleapis.com/**',route=>route.abort());
    await page.goto(base,{waitUntil:'domcontentloaded'});
    assert.equal(await page.getByRole('navigation',{name:'Ana gezinme'}).getByRole('button').count(),7);
    await settled();
    await api({action:'case_demo_prepare',scope:'demo',reset:true});
    await page.getByRole('button',{name:'Karar dosyalarını yenile'}).click();await settled();
    await page.getByRole('heading',{name:'Karar portföyü'}).waitFor();
    assert.equal(await page.locator('.case-story button').count(),9);
    await page.screenshot({path:'test-results/decision-summary-desktop.png',fullPage:true});

    for(const entity of ['Örnek Ürün A','Örnek Ürün B','Örnek Müşteri A']){
      await nav('Onay Kuyruğu').click();await settled();
      await page.getByRole('button',{name:entity,exact:true}).click();
      await page.getByRole('button',{name:'Onayla ve görev oluştur'}).waitFor();
      await step('Veri').click();await page.getByRole('heading',{name:'Kaynak ve kapsam'}).waitFor();
      await step('Etiket').click();await page.getByText('Etiketler verinin ticari sınıfını açıklar.',{exact:false}).waitFor();
      await step('Sinyal').click();await page.getByText('Gözlenen',{exact:true}).waitFor();
      await step('İçgörü').click();await page.getByRole('heading',{name:'Bu neden önemli?'}).waitFor();
      await page.getByRole('button',{name:'Onay kapsamını incele'}).click();
      if(entity==='Örnek Ürün A'){
        await page.screenshot({path:'test-results/decision-approval-desktop.png',fullPage:true});
        await page.getByRole('button',{name:'Öneriyi düzenle'}).click();
        await page.getByLabel('Sorumlu',{exact:true}).fill('Satın alma ekibi');
        await page.getByRole('button',{name:'Yeni sürümü kaydet'}).click();await settled();
        await page.getByText('Öneri sürümü 2',{exact:false}).waitFor();
      }
      await page.getByRole('button',{name:'Onayla ve görev oluştur'}).click();await settled();
      await page.getByRole('button',{name:'Aksiyonu başlat'}).click();await settled();
      await page.getByLabel('Uygulama notu').fill('İlgili görev kapsamı sorumlusu tarafından uygulandı.');
      await page.getByRole('button',{name:'Uygulandı olarak kaydet'}).click();await settled();
      await page.getByText(/tarihinde değerlendirilecek/).waitFor();
      assert.equal(await page.getByRole('button',{name:'Geri bildirimi kaydet'}).count(),0);
      await page.reload({waitUntil:'domcontentloaded'});await settled();
      await page.getByRole('heading',{name:new RegExp(entity.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'))}).first().waitFor();
      await page.getByRole('button',{name:'Listeye dön'}).click();
    }

    await nav('Sonuçlar ve Geri Bildirim').click();await settled();
    await page.getByRole('button',{name:'Sonucu değerlendir',exact:true}).click();
    await page.getByLabel('Değerlendirme notu').fill('Yeni stok sayımı henüz paylaşılmadığı için ölçülemedi.');
    await page.getByRole('button',{name:'Geri bildirimi kaydet'}).click();await settled();
    await page.getByRole('heading',{name:'Ölçülemedi',exact:true}).waitFor();
    await page.getByRole('button',{name:'Sonuçtan yeni inceleme başlat'}).click();await settled();
    await page.getByRole('button',{name:'Önceki karar dosyası'}).click();await settled();
    await page.getByRole('heading',{name:'Ölçülemedi',exact:true}).waitFor();
    await page.screenshot({path:'test-results/decision-feedback-desktop.png',fullPage:true});

    for(const width of [1024,768,390]){
      await page.setViewportSize({width,height:900});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`File overflow at ${width}`);
      await page.screenshot({path:`test-results/decision-file-${width}.png`,fullPage:true});
    }
    await page.setViewportSize({width:1440,height:1000});
    await nav('Ticari İnceleme').click();
    await page.locator('.research-library-group button').first().click();
    await page.getByRole('group',{name:'Ticari inceleme grupları'}).waitFor();
    for(const group of ['Satış ve Kârlılık','Müşteri ve Pazar','Ürün ve Tedarik','Öngörüler']){
      await page.getByRole('group',{name:'Ticari inceleme grupları'}).getByRole('button',{name:group,exact:true}).click();
      const modules=await page.getByRole('group',{name:'Uzman analizler'}).getByRole('button').all();
      for(const button of modules){await button.click();await page.locator('.page-heading h1').waitFor();}
    }
    await nav('Veri ve Etiketler').click();
    await page.getByRole('button',{name:'Etiket sözlüğü',exact:true}).click();await settled();
    await page.getByRole('heading',{name:'Etiket sözlüğü ve oluşma gerekçeleri'}).waitFor();
    await nav('Karar Özeti').click();await settled();
    await page.getByRole('button',{name:'Yüklenmiş veri',exact:true}).click();await settled();
    assert.equal((await api({action:'case_list',scope:'live'})).cases.some(d=>d.scope==='demo'),false);
    const before=await api({action:'case_list',scope:'live'});
    await page.getByRole('button',{name:'Demo senaryoları',exact:true}).click();await settled();
    await page.getByRole('button',{name:'Demoyu sıfırla',exact:true}).click();
    await page.getByRole('button',{name:'Demo alanını sıfırla',exact:true}).click();await settled();
    assert.equal(await page.locator('.case-story button').count(),9);
    assert.deepEqual(await api({action:'case_list',scope:'live'}),before);

    // A real imported source must remain navigable from its frozen decision.
    const schemas=await api({action:'schema'});
    const fields={'Ambar':'Merkez','Satici':'Ali','Fatura Türü':'Satış','Fatura Tarihi':'2024-12-20','Fatura No':'CASE-E2E-1',
      'Malzeme Kodu':'CASE-P1','Malzeme Aciklamasi':'Kanıt Ürünü','Malzeme Grubu':'Gıda','Birim':'ADET','Miktar':'10',
      'Net Satir Tutari':'100','Birim Fiyati':'10','Maliyet Fiyati':'20','Satis Fiyati':'10','Satir Maliyeti':'200',
      'Satir Kari':'-100','Satir Marji':'-100','Maliyet nach letzter EK RE':'220','Kar nach letzter EK RE':'-120',
      'Marj nach letzter EK RE':'-120','Icerik':'1','Müsteri Kodu':'CASE-C1','Müsteri Ünvani':'Kanıt Müşterisi','Ay':'12','Yil':'2024'};
    const csv=[schemas.movement,schemas.movement.map(k=>fields[k]||'')].map(row=>row.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\r\n');
    const inspectedResponse=await page.request.post(base+'/api/data',{multipart:{kind:'movement',encoding:'utf-8-sig',delimiter:'auto',file:{name:'karar-kanit.csv',mimeType:'text/csv',buffer:Buffer.from(csv)}}});
    const inspected=await inspectedResponse.json();
    if(inspected.ok){
      const report=await api({action:'analyze',id:inspected.data.id,mapping:inspected.data.mapping,decimal:'.',dateFormat:'iso',snapshot:''});
      assert.equal(report.accepted,1);
      await api({action:'commit',id:report.id,acknowledge:true});
    }else assert.match(inspected.error,/Aynı dosya/);
    const live=await api({action:'case_evaluate',scope:'live',analysisDate:'2024-12-30'});
    const linked=live.cases.find(d=>d.snapshot.entityId==='CASE-P1'&&d.category==='pricing');
    assert.ok(linked,'Imported negative margin should produce a pricing decision');
    await page.evaluate(id=>{sessionStorage.setItem('center-nav','insights');sessionStorage.setItem('decision-scope','live');sessionStorage.setItem('decision-selected-insights',id)},linked.id);
    await page.reload({waitUntil:'domcontentloaded'});await settled();
    await step('Veri').click();
    await page.getByRole('button',{name:/karar-kanit.csv/}).click();
    await page.getByRole('heading',{name:'Veri kalite raporu',exact:true}).waitFor();
    await page.getByRole('button',{name:'Karar dosyasına dön'}).click();await settled();
    await page.getByRole('button',{name:'Ticari incelemeyi aç'}).click();
    await page.getByLabel('Fiyat analizinde ara').waitFor();
    assert.equal(await page.getByLabel('Fiyat analizinde ara').inputValue(),'CASE-P1');
    assert.equal(await page.getByLabel('Demo analiz tarihi').inputValue(),linked.snapshot.analysisDate);
    await nav('Karar Özeti').click();await settled();
    await page.getByRole('button',{name:'Demo senaryoları',exact:true}).click();await settled();
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:'test-results/decision-summary-mobile.png',fullPage:true});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Summary mobile overflow');
    await page.emulateMedia({reducedMotion:'reduce'});
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(()=>document.activeElement!==document.body),true);
    assert.deepEqual(errors,[]);
    console.log('PASS: seven centers, nine isolated examples, three approval/application journeys, immutable revisions, follow-up gate, missing data, reopen, persistence, research navigation, CSV source proof/return, entity/date handoff, tags, reset isolation, responsive and keyboard checks.');
  }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
