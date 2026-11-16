/* Real-browser checks at a GitHub Pages-style subpath, with no external requests. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const prefix = '/ethiopian-bible-library/';
const output = path.join(root, 'tmp', 'browser');
fs.mkdirSync(output, { recursive: true });
const mime = {'.html':'text/html; charset=utf-8','.css':'text/css','.js':'application/javascript',
  '.json':'application/json','.webmanifest':'application/manifest+json','.png':'image/png',
  '.svg':'image/svg+xml','.txt':'text/plain; charset=utf-8'};
const server = http.createServer((req, res) => {
  let url;
  try { url = new URL(req.url, 'http://localhost'); } catch { res.writeHead(400).end(); return; }
  if (!url.pathname.startsWith(prefix)) { res.writeHead(404).end(); return; }
  const relative = decodeURIComponent(url.pathname.slice(prefix.length)) || 'index.html';
  const target = path.resolve(root, relative);
  if (!target.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
  fs.stat(target, (error, stat) => {
    if (error || !stat.isFile()) { res.writeHead(404).end(); return; }
    res.setHeader('Content-Type', mime[path.extname(target)] || 'application/octet-stream');
    res.setHeader('Cache-Control', 'no-cache');
    fs.createReadStream(target).pipe(res);
  });
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}${prefix}`;
  const browser = await chromium.launch({headless: true,
    ...(process.env.BROWSER_EXECUTABLE ? {executablePath:process.env.BROWSER_EXECUTABLE} : {})});
  const results = [];
  console.log('Browser launched; starting reader checks.');
  try {
    for (const width of [320, 390, 768, 1440]) {
      console.log('Opening viewport '+width);
      const context = await browser.newContext({viewport:{width,height:900}, acceptDownloads:true});
      context.setDefaultTimeout(15000);
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('response', response => {if(response.status() >= 400) errors.push(`${response.status()}: ${response.url()}`);});
      await context.route('**/*', route => new URL(route.request().url()).origin === new URL(base).origin
        ? route.continue() : route.abort());
      await page.goto(base + '?reader=ruth-geez-dillmann-hacohen#reader', {waitUntil:'networkidle'});
      console.log('Page opened: '+width);
      const initialWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      assert(initialWidth <= width, `Page overflows ${width}px: ${initialWidth}px`);
      await page.waitForFunction(() => document.querySelector('#reader-open').textContent === 'Text loaded');
      assert.equal(await page.locator('#reader-language').inputValue(), 'parallel', 'paired text opens in parallel by default');
      assert(await page.locator('#reader-audio-play').isVisible(), 'read-aloud controls are open by default');
      assert.equal(await page.locator('.section-disclosure[open]').count(), 0, 'secondary sections begin collapsed');
      assert.equal(await page.locator('#reader-notes').evaluate(element=>element.open), false, 'reader hash must not open optional notes');
      await page.screenshot({path:path.join(output, `warm-reader-${width}.png`)});
      await page.locator('#reader-language').selectOption('en');
      console.log('English selected: '+width);
      await page.waitForFunction(() => document.querySelector('#reader-text').innerText.includes('judges'));
      await page.locator('#reader-next').click();
      console.log('Next chapter selected: '+width);
      await page.waitForFunction(() => document.querySelector('#reader-chapter').value === '2');
      await page.locator('#reader-language').selectOption('parallel');
      assert(await page.locator('#reader-text').innerText(), 'Parallel view must contain text');
      await page.locator('#reader-tools > summary').click();
      await page.locator('#reader-lens').selectOption('language');
      await page.waitForFunction(() => !document.querySelector('#reader-study-panel').hidden);
      await page.locator('#reader-lens').selectOption('text');
      await page.locator('#reader-notes > summary').click();
      const [download] = await Promise.all([
        page.waitForEvent('download', {timeout:10000}),
        page.locator('#reader-download').click(),
      ]).catch(async error => {
        console.log(await page.evaluate(() => ({
          exportStatus:document.querySelector('#reader-export-status').textContent,
          notesOpen:document.querySelector('#reader-notes').open,
          downloadPosition:document.querySelector('#reader-download').getBoundingClientRect().toJSON(),
        })));
        await page.screenshot({path:path.join(output, 'reader-export-failure.png')});
        throw error;
      });
      const downloaded = path.join(output, `reader-${width}.json`);
      await download.saveAs(downloaded);
      console.log('Export saved: '+width);
      const exported = JSON.parse(fs.readFileSync(downloaded, 'utf8'));
      assert(exported, 'Reader export must be JSON');
      await page.locator('#reader-search').fill('Ruth');
      assert(await page.locator('#reader-book option').count() > 0, 'Search must retain matching readers');
      await page.waitForFunction(async () => Boolean((await navigator.serviceWorker.getRegistration())?.active), null, {timeout:30000})
        .catch(async error => {
          console.error('Service worker state:', await page.evaluate(async () => {
            const registration = await navigator.serviceWorker.getRegistration();
            return {active:registration?.active?.state, installing:registration?.installing?.state,
              waiting:registration?.waiting?.state, cacheNames:await caches.keys()};
          }), errors);
          throw error;
        });
      console.log('Service worker active: '+width);
      await page.reload({waitUntil:'networkidle'});
      await page.waitForFunction(() => document.querySelector('#reader-open').textContent === 'Text loaded');
      await page.waitForFunction(async () => {
        for (const name of await caches.keys()) {
          const cache = await caches.open(name);
          if (await cache.match(new URL('readers/ruth-geez.json', location.href))) return true;
        }
        return false;
      });
      await context.setOffline(true);
      await page.reload({waitUntil:'networkidle'});
      await page.waitForFunction(() => document.querySelector('#reader-open').textContent === 'Text loaded');
      const readerWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      assert(readerWidth <= width, `Reader overflows ${width}px: ${readerWidth}px`);
      await page.screenshot({path:path.join(output, `reader-${width}.png`)});
      assert.deepEqual(errors, [], `Browser errors at ${width}px`);
      results.push({width, initialWidth, readerWidth, reader:'Ruth',
        checks:['automatic text opening','default parallel view','visible read-aloud controls','collapsed secondary sections','English','parallel','chapter navigation','language lens','JSON export','search','offline reload']});
      await context.close();
      console.log('Viewport checks passed: '+width);
    }
    const homeContext = await browser.newContext({viewport:{width:1440,height:1000}});
    homeContext.setDefaultTimeout(15000);
    const home = await homeContext.newPage();
    await home.goto(base, {waitUntil:'networkidle'});
    await home.waitForFunction(() => document.querySelector('#reader-open').textContent === 'Text loaded');
    const readerTop = await home.locator('#reader').evaluate(element=>element.getBoundingClientRect().top);
    assert(readerTop < 500, 'reader must appear near the top, before the catalogue');
    assert.equal(await home.locator('#source-list article').count(), 0, 'secondary source cards are deferred');
    await home.screenshot({path:path.join(output,'warm-home-desktop.png')});
    await home.locator('.nav a[href="#sources"]').click();
    await home.waitForFunction(() => document.querySelector('#sources-disclosure').open && document.querySelectorAll('#source-list article').length > 0);
    await home.locator('.nav a[href="#reader"]').click();
    assert.equal(await home.locator('#reader-notes').evaluate(element=>element.open), false, 'returning to read must not unfold unrelated notes');
    await homeContext.close();
    console.log('Home and disclosure navigation checks passed.');

    // Deterministic speech-engine fixture checks browser wiring; it is not an audible-voice test.
    const audioContext = await browser.newContext({viewport:{width:1440,height:1000}});
    audioContext.setDefaultTimeout(15000);
    await audioContext.addInitScript(() => {
      // This fixture exercises the native fallback only; neural generation has
      // a separate worker/PCM check and must never download weights in CI.
      Object.defineProperty(window,'Worker',{configurable:true,value:undefined});
      window.__spoken = [];
      window.__speechCancelled = 0;
      const engine = {
        getVoices:()=>[{name:'Local test English',lang:'en-US',localService:true}],
        speak:utterance=>{window.__spoken.push({text:utterance.text,lang:utterance.lang,rate:utterance.rate});window.__lastUtterance=utterance;utterance.onstart?.();},
        cancel:()=>{window.__speechCancelled++;},
        resume:()=>{},
        addEventListener:()=>{},removeEventListener:()=>{},
      };
      Object.defineProperty(window,'speechSynthesis',{configurable:true,value:engine});
      Object.defineProperty(window,'SpeechSynthesisUtterance',{configurable:true,value:class {constructor(text){this.text=text;}}});
    });
    const audio = await audioContext.newPage();
    const audioErrors=[];
    audio.on('pageerror',error=>{audioErrors.push(error.message);console.error('Audio/reference page error:',error.message);});
    await audio.goto(base+'?reader=ruth-geez-dillmann-hacohen#reader',{waitUntil:'networkidle'});
    await audio.waitForFunction(()=>!document.querySelector('#reader-audio-play').disabled);
    assert.equal(await audio.evaluate(()=>window.__spoken.length),0,'opening never autoplays');
    await audio.locator('#reader-audio-play').click();
    assert.equal(await audio.evaluate(()=>window.__spoken[0].lang),'en-US');
    await audio.locator('#reader-audio-pause').click();
    assert.equal(await audio.locator('#reader-audio-pause').innerText(),'Resume');
    await audio.locator('#reader-audio-pause').click();
    await audio.locator('#reader-next').click();
    await audio.waitForFunction(()=>document.querySelector('#reader-chapter').value==='2');
    assert(await audio.locator('#reader-audio-pause').isDisabled(),'chapter change stops audio');
    const spokenBefore = await audio.evaluate(()=>window.__spoken.length);
    await audio.evaluate(()=>window.__lastUtterance.onend());
    assert.equal(await audio.evaluate(()=>window.__spoken.length),spokenBefore,'late speech events cannot leak into next chapter');
    await audio.locator('#reader-language').selectOption('gez');
    await audio.waitForFunction(()=>document.querySelector('#reader-audio-status').textContent.includes('No supported non-Microsoft local voice'));
    assert(await audio.locator('#reader-audio-play').isDisabled(),'unsupported Geʽez is not read with an English voice');
    await audio.locator('#reader-language').selectOption('parallel');
    const archive = JSON.parse(fs.readFileSync(path.join(root,'archive.json'),'utf8'));
    const pairs = archive.readers.filter(reader=>reader.parallel_translation);
    for(const reader of pairs) {
      console.log('Checking parallel player: '+reader.reader_id);
      await audio.locator('#reader-book').selectOption(reader.reader_id);
      await audio.waitForFunction(id => new URL(location.href).searchParams.get('reader') === id && document.querySelector('#reader-open').textContent === 'Text loaded',reader.reader_id);
      assert.equal(await audio.locator('#reader-language').inputValue(),'parallel',reader.reader_id+' defaults to parallel');
      assert(await audio.locator('.reader-parallel-row').count()>0);
      const headerCount=await audio.locator('#reader-chapter-count').innerText();
      assert(headerCount.includes(reader.unit_count.toLocaleString('en-US')));
      assert(headerCount.includes(reader.parallel_translation.unit_count.toLocaleString('en-US')));
      assert(!/observed\s+observed/i.test(headerCount),'observation labels must remain readable without duplication');
      await audio.locator('#reader-chapter').selectOption(String(reader.chapters.at(-1).chapter));
      assert(await audio.locator('.reader-parallel-row').count()>0);
      await audio.waitForFunction(()=>!document.querySelector('#reader-audio-play').disabled);
    }
    const languages=[...new Set(archive.readers.filter(reader=>reader.language_tag!=='en').map(reader=>reader.language_tag))];
    for(const language of languages) {
      const reader=archive.readers.find(item=>item.language_tag===language);
      console.log('Checking sourced English for '+language+': '+reader.reader_id);
      await audio.locator('#reader-book').selectOption(reader.reader_id);
      await audio.waitForFunction(id=>new URL(location.href).searchParams.get('reader')===id && document.querySelector('#reader-open').textContent==='Text loaded',reader.reader_id);
      await audio.locator('#reader-language').selectOption('reference');
      await audio.waitForFunction(()=>document.querySelector('#reader-english-text').textContent.trim().length>0 && !document.querySelector('#reader-audio-play').disabled)
        .catch(async error=>{console.error(await audio.evaluate(()=>({view:document.querySelector('#reader-language').value,
          status:document.querySelector('#reader-english-status').textContent,text:document.querySelector('#reader-english-text').textContent.slice(0,120),
          audio:document.querySelector('#reader-audio-status').textContent,book:document.querySelector('#reader-book').value})));
          await audio.screenshot({path:path.join(output,'english-reference-failure.png'),timeout:10000});throw error;});
      assert(await audio.locator('#reader-english-panel').isVisible());
      assert.equal(await audio.locator('#reader-audio-language').inputValue(),'en');
      assert.match(await audio.locator('#reader-english-status').innerText(),/not a translation of the exact/);
      await audio.locator('#reader-language').selectOption('reference-en');
      await audio.waitForFunction(()=>document.querySelector('#reader-text').hidden && document.querySelector('#reader-english-text').textContent.trim().length>0);
    }
    await audio.locator('#reader-book').selectOption('alaba-kabeena-1co-research');
    await audio.locator('#reader-language').selectOption('reference');
    await audio.waitForFunction(()=>document.querySelector('#reader-english-title').textContent.includes('1 Corinthians'));
    await audio.locator('#reader-english-chapter').selectOption('16');
    await audio.waitForFunction(()=>document.querySelector('#reader-english-title').textContent.includes('Chapter 16'));
    assert.equal(await audio.locator('#reader-chapter').inputValue(),'1','English chapter selection is independent of the source');
    const referenceDownload=audio.waitForEvent('download');
    await audio.locator('#reader-notes > summary').click();
    await audio.locator('#reader-download').click();
    const exportedReference=await referenceDownload;
    const exportPath=path.join(output,'sourced-english-export.json');await exportedReference.saveAs(exportPath);
    const referencePackage=JSON.parse(fs.readFileSync(exportPath,'utf8'));
    assert.equal(referencePackage.schema_version,2);assert.equal(referencePackage.text_layers.length,2);
    assert(referencePackage.comparison_reference);
    const unavailableContext=await browser.newContext({serviceWorkers:'block'});
    const unavailable=await unavailableContext.newPage();
    unavailable.setDefaultTimeout(15000);
    await unavailable.route('**/readers/webbe-2020-1co-research.json',route=>route.abort());
    await unavailable.goto(base+'?reader=alaba-kabeena-1co-research#reader',{waitUntil:'networkidle'});
    await unavailable.waitForFunction(()=>document.querySelector('#reader-english-status').textContent.includes('could not be loaded'));
    await unavailable.locator('#reader-language').selectOption('reference-en');
    await unavailable.waitForFunction(()=>document.querySelector('#reader-english-status').textContent.includes('could not be loaded'));
    assert.equal(await unavailable.locator('#reader-audio-language option').count(),0,'failed English-only view cannot switch to unseen source narration');
    assert(await unavailable.locator('#reader-audio-play').isDisabled());
    await unavailableContext.close();
    await audio.locator('#reader-book').selectOption('joel-geez-dillmann-hacohen-tau');
    await audio.waitForFunction(()=>document.querySelector('#reader-book').value==='joel-geez-dillmann-hacohen-tau' && document.querySelector('#reader-open').textContent==='Text loaded');
    await audio.locator('#reader-chapter').selectOption('4');
    await audio.locator('#reader-language').selectOption('reference');
    await audio.waitForFunction(()=>document.querySelector('#reader-english-status').textContent.includes('no English chapter'));
    assert(await audio.locator('#reader-audio-play').isDisabled(),'a missing reference chapter must not narrate a substituted chapter');
    await audio.locator('#reader-english-chapter').selectOption('3');
    await audio.waitForFunction(()=>document.querySelector('#reader-english-title').textContent.includes('Chapter 3') && !document.querySelector('#reader-audio-play').disabled);
    assert.equal(await audio.locator('#reader-chapter').inputValue(),'4');
    await audio.evaluate(()=>{
      window.Translator={availability:async()=> 'available',create:async()=>({translate:async text=>'Preview: '+text,destroy(){}})};
    });
    // Translator capability is captured at initialization, so reload with a fixture.
    await audioContext.addInitScript(()=>{window.Translator={availability:async()=> 'available',create:async()=>({translate:async text=>'Preview: '+text,destroy(){}})};});
    await audio.goto(base+'?reader=arb-vd-1ch-research#reader',{waitUntil:'networkidle'});
    await audio.locator('#reader-language').selectOption('machine');
    await audio.locator('#reader-translate').click();
    await audio.waitForFunction(()=>document.querySelector('#reader-english-status').textContent.includes('preview complete'));
    assert.match(await audio.locator('#reader-english-title').innerText(),/unreviewed/);
    assert(await audio.locator('#reader-download').isDisabled(),'generated preview is not exported as a sourced reader');
    await audio.goto(base+'?reader=alaba-kabeena-rev-research#reader',{waitUntil:'networkidle'});
    await audio.waitForFunction(()=>document.querySelector('#reader-english-text').textContent.includes('Laodicea'));
    const revelationText=await audio.locator('#reader-english-text').innerText();
    assert(revelationText.includes('What you see, write in a book and send to the seven assemblies:'));
    assert(!/\|(?:strong|lemma|srcloc)\s*=/i.test(revelationText),'nested dictionary metadata cannot leak into the English pane');
    await audio.locator('#reader-english-text .reader-verse').nth(10).evaluate(element=>element.scrollIntoView({block:'center'}));
    await audio.locator('#reader-english-panel').screenshot({path:path.join(output,'revelation-word-attributes-fixed.png')});
    assert.deepEqual(audioErrors,[],'reader navigation and audio controls must not throw browser errors');
    results.push({parallelBooks:pairs.length,checks:['all first/last chapter pairs','default parallel','speech controls','no autoplay','pause/resume','language mismatch','navigation cancellation']});
    results.push({referenceLanguages:languages.length,checks:['sourced English by language','separate English chapter navigation','English-only reference','versioned reference export','labeled on-device preview']});
    await audioContext.close();
    fs.writeFileSync(path.join(output,'results.json'), JSON.stringify(results,null,2));
    console.log(JSON.stringify(results));
  } catch (error) {
    console.error('Browser verification failed before cleanup:', error);
    throw error;
  } finally {
    const timeout = setTimeout(() => { console.error('Browser cleanup exceeded 15 seconds.'); process.exit(1); }, 15000);
    timeout.unref();
    await browser.close();
    clearTimeout(timeout);
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => {console.error(error); server.close(); process.exitCode=1;});
