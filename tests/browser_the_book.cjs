/* Real-browser coverage for the optional reading workspace at a Pages subpath. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const {chromium} = require('playwright');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'tmp', 'the-book-2026-11-20', 'browser');
fs.mkdirSync(output, {recursive:true});
const prefix = '/ethiopian-bible-library/';
const mime = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.txt':'text/plain; charset=utf-8','.webmanifest':'application/manifest+json'};
const server = http.createServer((req,res)=>{
  const url = new URL(req.url,'http://localhost');
  if(!url.pathname.startsWith(prefix))return res.writeHead(404).end();
  const target = path.resolve(root,decodeURIComponent(url.pathname.slice(prefix.length)) || 'index.html');
  if(!target.startsWith(root+path.sep))return res.writeHead(403).end();
  fs.stat(target,(error,stat)=>{
    if(error || !stat.isFile())return res.writeHead(404).end();
    res.setHeader('Content-Type',mime[path.extname(target)] || 'application/octet-stream');
    fs.createReadStream(target).pipe(res);
  });
});
(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const base = `http://127.0.0.1:${server.address().port}${prefix}`;
  const browser = await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{})});
  const results=[];
  try {
    for(const width of [320,390,768,1440]) {
      const context=await browser.newContext({viewport:{width,height:950},acceptDownloads:true});
      const page=await context.newPage(); const errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      await context.route('**/*',route=>new URL(route.request().url()).origin===new URL(base).origin?route.continue():route.abort());
      await page.goto(base+'?reader=ruth-geez-dillmann-hacohen#reader');
      await page.waitForFunction(()=>document.querySelector('#reader-open').textContent==='Text loaded');
      assert.equal(await page.locator('#the-book-disclosure').evaluate(e=>e.open),false);
      await page.locator('#the-book-reader-link').click();
      await page.waitForFunction(()=>!document.querySelector('#the-book-map').hidden);
      assert.equal(await page.locator('#the-book-reader option').count(),759);
      assert.equal(await page.locator('#the-book-paths button').count(),4);
      assert(await page.locator('#the-book-context').innerText().then(t=>t.includes('Ruth')));
      await page.locator('#the-book-paths button[data-scope="C"]').click();
      assert((await page.locator('#the-book-path-description').innerText()).includes('81-entry'));
      await page.locator('#the-book-start').click();
      await page.locator('#the-book-observation').fill('My source observation, kept separate from interpretation.');
      await page.locator('#the-book-interpretation').fill('A present interpretation, not a rewritten past.');
      await page.locator('#the-book-standing').selectOption('WAS');
      await page.locator('#the-book-review').selectOption('IS');
      await page.locator('#the-book-form button[type="submit"]').click();
      await page.waitForFunction(()=>document.querySelector('#the-book-note-status').textContent.startsWith('Saved revision 1'));
      await page.locator('#reader-next').click();
      await page.waitForFunction(()=>document.querySelector('#reader-chapter').value==='2');
      assert((await page.locator('#the-book-context').innerText()).includes('position 2'));
      assert((await page.locator('#the-book-bound-context').innerText()).includes('position 1'));
      await page.locator('#the-book-interpretation').fill('A second view; earlier reading retained.');
      await page.locator('#the-book-form button[type="submit"]').click();
      await page.waitForFunction(()=>document.querySelector('#the-book-note-status').textContent.startsWith('Saved revision 2'));
      const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('ethiopian-bible-library-the-book-v1')).records);
      assert.equal(saved.length,2); assert.equal(saved[1].context.source_chapter,1);
      assert.equal(saved[0].fields.standing,'WAS'); assert.equal(saved[0].fields.review,'IS');
      assert.notEqual(saved[0].fields.interpretation,saved[1].fields.interpretation);
      const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#the-book-export').click()]);
      const destination=path.join(output,`notes-${width}.json`);await download.saveAs(destination);
      assert.equal(JSON.parse(fs.readFileSync(destination,'utf8')).records.length,2);
      await page.locator('#the-book-search').fill('NO SUCH WITNESS XXXXX');
      assert.equal(await page.locator('#the-book-reader option').count(),0);
      assert(await page.locator('#the-book-open-reader').isDisabled());
      await page.locator('#the-book-search').fill('WEBBE');
      assert(await page.locator('#the-book-reader option').count()>0);
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      await page.locator('#the-book').evaluate(element=>element.scrollIntoView({block:'start',behavior:'instant'}));
      await page.screenshot({path:path.join(output,`the-book-${width}.png`)});
      // The new shell, map and selected reader must work without the network.
      await page.evaluate(async()=>{await navigator.serviceWorker.ready;});
      await page.waitForFunction(()=>!!navigator.serviceWorker.controller);
      await context.setOffline(true); await page.reload();
      await page.waitForFunction(()=>!document.querySelector('#the-book-map').hidden);
      assert((await page.locator('#the-book-storage-status').innerText()).includes('2 saved revisions'));
      assert.equal(await page.locator('#the-book-reader option').count(),759);
      assert.deepEqual(errors,[]);
      results.push({width,checks:['all 759 indexed','four scope paths','source binding','revision history','export','search','separate temporal axes','no horizontal overflow','offline reload']});
      await context.close();
    }
    const context=await browser.newContext();const page=await context.newPage();
    await page.addInitScript(()=>{
      localStorage.setItem('ethiopian-bible-library-the-book-v1','{broken');
    });
    await page.goto(base+'#the-book');await page.waitForFunction(()=>!document.querySelector('#the-book-map').hidden);
    assert((await page.locator('#the-book-storage-status').innerText()).includes('not been overwritten'));
    assert.equal(await page.evaluate(()=>localStorage.getItem('ethiopian-bible-library-the-book-v1')),'{broken');
    await context.close();
    const quota=await browser.newContext();const quotaPage=await quota.newPage();
    await quotaPage.addInitScript(()=>{const original=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='ethiopian-bible-library-the-book-v1')throw new Error('Test storage quota');return original.call(this,k,v);};});
    await quotaPage.goto(base+'#the-book');await quotaPage.waitForFunction(()=>!document.querySelector('#the-book-map').hidden);
    await quotaPage.locator('#the-book-start').click();await quotaPage.locator('#the-book-observation').fill('An observation.');
    await quotaPage.locator('#the-book-form button[type="submit"]').click();
    await quotaPage.waitForFunction(()=>document.querySelector('#the-book-note-status').textContent.includes('Not saved: Test storage quota'));
    assert((await quotaPage.locator('#the-book-note-status').innerText()).includes('Not saved: Test storage quota'));
    assert.equal(await quotaPage.evaluate(()=>localStorage.getItem('ethiopian-bible-library-the-book-v1')),null);
    await quota.close();
    fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({results,failureChecks:['corrupt storage preserved','quota failure reports not saved']},null,2));
    console.log('The Book browser checks passed at four widths, offline, with corruption and quota failure.');
  } finally {await browser.close();server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});
