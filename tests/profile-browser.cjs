// Run after decision-browser.cjs on the same isolated server (CASE-P1/C1 fixtures).
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/Akif/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
const base=process.env.TEST_URL||'http://127.0.0.1:3013';
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});page.setDefaultTimeout(20000);
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const nav=name=>page.getByRole('navigation',{name:'Ana gezinme'}).getByRole('button',{name,exact:true});
 try{
  await page.route('https://fonts.googleapis.com/**',r=>r.abort());await page.goto(base,{waitUntil:'domcontentloaded'});
  await page.getByRole('button',{name:'Müşteri 360',exact:true}).click();
  await page.getByLabel('Müşteri ara').fill('CASE-C1');
  await page.locator('.customer-table tbody tr').filter({hasText:'CASE-C1'}).click();
  await page.getByRole('heading',{name:'Alışveriş zaman çizgisi'}).waitFor();
  assert.equal(await page.locator('.customer-backdrop').count(),0);
  assert.equal(await page.locator('.customer-detail').evaluate(e=>getComputedStyle(e).position),'static');
  await page.getByText('Tüm geçmişte net satış',{exact:true}).waitFor();
  await page.getByText('En büyük ürün payı',{exact:true}).waitFor();
  await page.screenshot({path:'test-results/customer-profile-desktop.png',fullPage:true});
  await page.locator('.customer-products button').filter({hasText:'CASE-P1'}).click();
  await page.getByRole('heading',{name:'Fiyat ve maliyet seyri'}).waitFor();
  assert.equal(await page.locator('.product-detail').evaluate(e=>getComputedStyle(e).position),'static');
  await page.locator('.profile-entity-link').filter({hasText:'Kanıt Müşterisi'}).click();
  await page.getByRole('heading',{name:'Alışveriş zaman çizgisi'}).waitFor();
  await page.locator('.entity-decision-panel').getByRole('button',{name:'Karar hazırla',exact:true}).click();
  await page.getByLabel('Önerilen işlem',{exact:true}).fill('Kanıt müşterisine tamamlayıcı ürün önerisi hazırlayın.');
  await page.getByLabel('Başarı ölçütü',{exact:true}).fill('14 gün içinde iki ürünlük deneme siparişi alın.');
  await page.getByRole('button',{name:'Kanıtla karar dosyası oluştur'}).click();
  await page.getByRole('button',{name:'Onayla ve görev oluştur'}).waitFor();
  await page.getByText('14 gün içinde iki ürünlük deneme siparişi alın.',{exact:true}).first().waitFor();
  assert.equal(await page.getByRole('button',{name:'Aksiyonu başlat',exact:true}).count(),0);
  await page.getByRole('button',{name:'Ticari incelemeyi aç'}).click();
  await page.getByRole('heading',{name:'Alışveriş zaman çizgisi'}).waitFor();
  await page.getByText(/İlişkili karar dosyaları/).waitFor();
  await page.locator('.customer-products button').filter({hasText:'CASE-P1'}).click();
  await page.getByRole('heading',{name:'Fiyat ve maliyet seyri'}).waitFor();
  for(const width of [1440,768,390]){
   await page.setViewportSize({width,height:900});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`Profile overflow at ${width}`);
   assert.equal(await page.locator('.product-detail-body').evaluate(e=>getComputedStyle(e).overflowY),'visible');
   await page.screenshot({path:`test-results/product-profile-${width}.png`,fullPage:true});
  }
  await page.locator('.entity-decision-panel').getByRole('button',{name:'Karar hazırla',exact:true}).click();
  await page.getByLabel('Önerilen işlem',{exact:true}).fill('Bu ürünün müşteri grubuna göre fiyatlarını değerlendirin.');
  await page.getByLabel('Başarı ölçütü',{exact:true}).fill('Marjı %22 düzeyine çıkarırken satış hacmini koruyun.');
  await page.getByRole('button',{name:'Kanıtla karar dosyası oluştur'}).click();
  await page.getByRole('button',{name:'Onayla ve görev oluştur'}).waitFor();
  await nav('Ticari İnceleme').click();await page.getByRole('heading',{name:'Önce tanıyın. Sonra karar verin.'}).waitFor();
  assert.equal(await page.locator('.research-library-group button').count(),12);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.setViewportSize({width:1440,height:1000});
  await page.screenshot({path:'test-results/research-library-desktop.png',fullPage:true});
  assert.deepEqual(errors,[]);
  console.log('PASS: analysis library, full-page customer/product profiles, bidirectional entity links, evidence-backed proposals, approval gate, related decisions, responsive layouts.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
