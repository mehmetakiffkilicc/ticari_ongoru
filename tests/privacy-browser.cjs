const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/Akif/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const base=process.env.TEST_URL||'http://127.0.0.1:3015';
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('https://fonts.googleapis.com/**',route=>route.abort());
  await page.goto(base,{waitUntil:'domcontentloaded'});
  await page.getByRole('complementary',{name:'Veri gizliliği'}).waitFor();
  const listing=await (await page.request.get(base+'/api/data')).json();
  assert.equal(listing.ok,true);
  assert.ok(listing.data.batches.every(b=>b.name.startsWith('ornek-')));
  for(const action of ['cockpit','stock_analysis','customer_analytics','sales_profitability']){
   const response=await page.request.post(base+'/api/data',{data:{action,analysisDate:'2024-12-30'}});
   assert.equal(response.headers()['cache-control'],'no-store');
   const result=await response.json();assert.equal(result.ok,true,action);
   console.log(action,'passed');
  }
  const upload=await page.request.post(base+'/api/data',{multipart:{file:{name:'private.csv',mimeType:'text/csv',buffer:Buffer.from('private,data')}}});
  assert.equal(upload.status(),403);
  for(const action of ['inspect','analyze','commit']){
   const out=await (await page.request.post(base+'/api/data',{data:{action}})).json();assert.equal(out.ok,false);
  }
  fs.mkdirSync('test-results',{recursive:true});
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:1000});
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   const box=await page.getByRole('complementary',{name:'Veri gizliliği'}).boundingBox();
   assert.ok(box.y>=0 && box.y+box.height<=1000);
   await page.screenshot({path:`test-results/privacy-${width}.png`,fullPage:true});
  }
  assert.deepEqual(errors,[]);
  console.log('Privacy API isolation, uploads, banner and responsive layout passed.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
