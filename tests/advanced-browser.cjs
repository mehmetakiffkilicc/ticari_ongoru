// Use tests.seed_advanced with an isolated DATA_DIR server first.
const {chromium}=require('C:/Users/Akif/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
const base=process.env.TEST_URL||'http://127.0.0.1:3014';
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});const page=await browser.newPage({viewport:{width:1440,height:1000}});page.setDefaultTimeout(30000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
const nav=name=>page.getByRole('navigation',{name:'Ana gezinme'}).getByRole('button',{name,exact:true});
const library=async()=>{await nav('Ticari İnceleme').click();await page.locator('.research-library').waitFor()};
try{
 await page.route('https://fonts.googleapis.com/**',r=>r.abort());await page.goto(base,{waitUntil:'domcontentloaded'});
 await library();await page.locator('.research-library-group button').filter({hasText:'Coğrafi analiz'}).click();await page.locator('.geo-map path').first().waitFor();
 assert.ok(await page.locator('.geo-map path').count()>170);await page.getByLabel('Harita ülkesi').selectOption('DEU');
 assert.equal(await page.locator('.ops-table tbody tr').count(),2);
 await page.getByLabel('Harita ölçütü').selectOption('profit');
 await page.getByRole('button',{name:/Berlin:/}).click();assert.equal(await page.locator('.ops-table tbody tr').count(),1);
 await page.getByRole('button',{name:'Şehir seçimini kaldır'}).click();
 const before=await page.locator('.geo-map').getAttribute('viewBox');await page.getByRole('button',{name:'Haritayı yakınlaştır',exact:true}).click();assert.notEqual(await page.locator('.geo-map').getAttribute('viewBox'),before);
 await page.locator('.geo-map').focus();await page.keyboard.press('ArrowRight');
 await page.waitForTimeout(250);await page.screenshot({path:'test-results/advanced-map-desktop.png',fullPage:true});
 await page.getByRole('button',{name:'Dünya görünümü',exact:true}).click();await page.getByText(/Haritada eşleşmeyen/).click();await page.getByText(/Hayalişehir, Türkiye/).waitFor();
 for(const width of [768,390]){await page.setViewportSize({width,height:900});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.waitForTimeout(250);await page.screenshot({path:`test-results/advanced-map-${width}.png`,fullPage:true})}
 await page.setViewportSize({width:1440,height:1000});await library();await page.getByRole('button',{name:'Müşteri 360',exact:true}).click();await page.getByLabel('Müşteri ara').fill('C1');await page.locator('.customer-table tbody tr').filter({hasText:'Müşteri C1'}).click();
 await page.getByRole('heading',{name:'Bir sonraki görüşmenin gündemi'}).waitFor();assert.equal(await page.locator('.recommendation-row').count(),4);
 await page.locator('.customer-recommendations').screenshot({path:'test-results/advanced-recommendations-desktop.png'});await page.getByRole('button',{name:/Yeni kategori 1/}).click();assert.equal(await page.locator('.recommendation-row').count(),1);
 await page.getByRole('button',{name:'Karara taşı',exact:true}).click();await page.getByLabel('Önerilen işlem',{exact:true}).waitFor();assert.ok((await page.getByLabel('Önerilen işlem',{exact:true}).inputValue()).includes('P3'));
 await page.getByLabel('Başarı ölçütü',{exact:true}).fill('30 gün içinde ürün denemesi ve müşteri geri bildirimi.');await page.getByRole('button',{name:'Kanıtla karar dosyası oluştur'}).click();await page.getByRole('button',{name:'Onayla ve görev oluştur'}).waitFor();
 assert.equal(await page.getByRole('button',{name:'Aksiyonu başlat',exact:true}).count(),0);
 await library();await page.getByRole('button',{name:'Ürün 360',exact:true}).click();await page.getByRole('button',{name:'Kategori stratejisi',exact:true}).click();await page.getByRole('button',{name:'Gıda →',exact:true}).click();await page.getByRole('region',{name:'Kategori ayrıntısı'}).waitFor();
 await page.waitForTimeout(250);await page.screenshot({path:'test-results/advanced-category-desktop.png',fullPage:true});await page.getByRole('button',{name:'Ürün P1 ↗',exact:true}).click();await page.getByRole('heading',{name:'Ticari dayanıklılık'}).waitFor();
 await page.getByRole('button',{name:'Bu ürünün stok detayını aç'}).click();await page.getByRole('heading',{name:'Tedarik senaryosu'}).waitFor();
 const value=()=>page.locator('.stock-scenario dd').first().innerText();const initial=await value();await page.getByLabel('Hedef kapsama (gün)').fill('365');assert.notEqual(await value(),initial);
 await page.waitForTimeout(250);await page.screenshot({path:'test-results/advanced-stock-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:900});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.waitForTimeout(250);await page.screenshot({path:'test-results/advanced-stock-mobile.png',fullPage:true});
 assert.deepEqual(errors,[]);console.log('PASS: map matching, metrics, zoom, keyboard, city/table selection, unknown locations, customer recommendations, proposal approval, category/product drilldown, stock scenarios, responsive layouts.');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
