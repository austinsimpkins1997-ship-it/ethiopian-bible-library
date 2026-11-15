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
  try {
    for (const width of [320, 390, 768, 1440]) {
      const context = await browser.newContext({viewport:{width,height:900}, acceptDownloads:true});
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('response', response => {if(response.status() >= 400) errors.push(`${response.status()}: ${response.url()}`);});
      await context.route('**/*', route => new URL(route.request().url()).origin === new URL(base).origin
        ? route.continue() : route.abort());
      await page.goto(base + '?reader=ruth-geez-dillmann-hacohen#reader', {waitUntil:'networkidle'});
      const initialWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      assert(initialWidth <= width, `Page overflows ${width}px: ${initialWidth}px`);
      await page.locator('#reader-open').click();
      await page.waitForFunction(() => document.querySelector('#reader-open').textContent === 'Text loaded');
      await page.locator('#reader-language').selectOption('en');
      await page.waitForFunction(() => document.querySelector('#reader-text').innerText.includes('judges'));
      await page.locator('#reader-next').click();
      await page.waitForFunction(() => document.querySelector('#reader-chapter').value === '2');
      await page.locator('#reader-language').selectOption('parallel');
      assert(await page.locator('#reader-text').innerText(), 'Parallel view must contain text');
      await page.locator('#reader-lens').selectOption('language');
      await page.waitForFunction(() => !document.querySelector('#reader-study-panel').hidden);
      await page.locator('#reader-lens').selectOption('text');
      const downloadEvent = page.waitForEvent('download');
      await page.locator('#reader-download').click();
      const download = await downloadEvent;
      const downloaded = path.join(output, `reader-${width}.json`);
      await download.saveAs(downloaded);
      const exported = JSON.parse(fs.readFileSync(downloaded, 'utf8'));
      assert(exported, 'Reader export must be JSON');
      await page.locator('#reader-search').fill('Ruth');
      assert(await page.locator('#reader-book option').count() > 0, 'Search must retain matching readers');
      await page.evaluate(async () => {await navigator.serviceWorker.ready;});
      await page.reload({waitUntil:'networkidle'});
      if (await page.locator('#reader-open').isEnabled()) await page.locator('#reader-open').click();
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
      if (await page.locator('#reader-open').isEnabled()) await page.locator('#reader-open').click();
      await page.waitForFunction(() => document.querySelector('#reader-open').textContent === 'Text loaded');
      const readerWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      assert(readerWidth <= width, `Reader overflows ${width}px: ${readerWidth}px`);
      await page.screenshot({path:path.join(output, `reader-${width}.png`)});
      assert.deepEqual(errors, [], `Browser errors at ${width}px`);
      results.push({width, initialWidth, readerWidth, reader:'Ruth',
        checks:['English','parallel','chapter navigation','language lens','JSON export','search','offline reload']});
      await context.close();
    }
    fs.writeFileSync(path.join(output,'results.json'), JSON.stringify(results,null,2));
    console.log(JSON.stringify(results));
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => {console.error(error); server.close(); process.exitCode=1;});
