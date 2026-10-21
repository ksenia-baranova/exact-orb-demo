// Real application HTML/main/session/facts; only the HTTP leaf is controlled.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { createHash } = require('node:crypto');
const { chromium } = require(process.env.WHEEL_PLAYWRIGHT ||
  'C:/Users/KateUser/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = path.resolve(__dirname, '../../../../../../..');
const ui = path.join(root, 'src/exact_orb/http_api/ui');
const chart = JSON.parse(fs.readFileSync(path.join(root, 'tests/ui/fixtures/natal_1985_chart_dto.json'), 'utf8'));
const initial = JSON.parse(fs.readFileSync(path.join(root, 'tests/http_api/golden/session_view.json'), 'utf8')).known_ready;
initial.chart = chart;
const output = { subject: 'TASK-D-007 CH-02/03, actual application; no SVG claim', cases: [] };

async function main() {
  const server = http.createServer((request, response) => {
    const name = request.url === '/' ? 'index.html' : request.url.slice('/ui/'.length);
    if (!request.url.startsWith('/ui/') && request.url !== '/' || !/^[a-z_]+\.(?:html|mjs|css)$/.test(name)) {
      response.writeHead(404); response.end(); return;
    }
    response.setHeader('content-type', name.endsWith('.css') ? 'text/css' : name.endsWith('.mjs') ? 'text/javascript' : 'text/html');
    response.end(fs.readFileSync(path.join(ui, name)));
  });
  let browser;
  try {
    await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
    browser = await chromium.launch({ headless: true,
      executablePath: process.env.WHEEL_BROWSER || 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
    output.browser = browser.version();
    for (const width of [1440, 768, 360]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      let current = structuredClone(initial), calls = [];
      const errors = []; page.on('pageerror', (error) => errors.push(String(error)));
      await page.route('**/session/bootstrap', (route) => {
        calls.push('bootstrap'); return route.fulfill({ json: { status: 'ready', state_version: 1 } });
      });
      await page.route('**/charts/current', (route) => {
        calls.push('current'); return route.fulfill({ json: current });
      });
      await page.route('**/charts/natal', () => { throw new Error('HTML actions must never build'); });
      await page.addInitScript(() => {
        window.programmaticFocus = 0; window.trackingActivation = false;
        const focus = HTMLElement.prototype.focus;
        HTMLElement.prototype.focus = function (...args) {
          if (window.trackingActivation) window.programmaticFocus++;
          return focus.apply(this, args);
        };
      });
      await page.goto('http://127.0.0.1:' + server.address().port + '/');
      await page.waitForSelector('#chart-result:not([hidden])');
      const count = () => page.locator('#aspects-table tbody tr:visible').count();
      assert.equal(await count(), 5); assert.equal(await page.locator('#houses-table tbody tr:visible').count(), 5);
      await page.locator('#aspects-show-all').click(); assert.equal(await count(), chart.aspects.length);
      const moon = page.locator('[data-point-id="moon"]');
      await moon.focus(); await moon.scrollIntoViewIfNeeded();
      await page.evaluate(() => {
        window.savedMoon = document.querySelector('[data-point-id="moon"]');
        window.startScroll = scrollY; window.trackingActivation = true;
      });
      await page.keyboard.press('Enter');
      assert.equal(await count(), chart.aspects.filter((row) => row.from === 'moon' || row.to === 'moon').length);
      assert.deepEqual(await page.evaluate(() => ({ same: document.activeElement === window.savedMoon,
        programmaticFocus: window.programmaticFocus, scroll: scrollY === window.startScroll })),
      { same: true, programmaticFocus: 0, scroll: true });
      await page.evaluate(() => { window.trackingActivation = false; });
      const contactSizes = await page.locator('.fact-select:visible').evaluateAll((buttons) => buttons.map((button) => {
        const r = button.getBoundingClientRect(); return { width: r.width, height: r.height, right: r.right, left: r.left };
      }));
      assert.ok(contactSizes.length > chart.points.length);
      assert.ok(contactSizes.every((r) => r.width >= 44 && r.height >= 44 && r.left >= 0 && r.right <= width));
      const requestCount = calls.length;
      await page.setViewportSize({ width: width === 360 ? 768 : 360, height: 900 });
      assert.equal(await moon.getAttribute('aria-pressed'), 'true');
      assert.equal(await page.evaluate(() => document.activeElement === window.savedMoon), true);
      assert.equal(calls.length, requestCount);
      await page.setViewportSize({ width, height: 900 });
      const selected = page.locator('#aspects-table tbody tr:visible button:not(:disabled)').first();
      const sourceIndex = await selected.evaluate((button) => Array.from(button.closest('tbody').children).indexOf(button.closest('tr')));
      await selected.focus(); await selected.scrollIntoViewIfNeeded();
      await page.evaluate(() => { window.savedAspect = document.activeElement; });
      await page.keyboard.press('Space'); assert.equal(await count(), 1);
      assert.equal(await page.evaluate(() => document.activeElement === window.savedAspect), true);
      current = structuredClone(current); current.chart.chart_identity += '-automatic';
      const source = current.chart.aspects[sourceIndex];
      [source.from, source.to] = [source.to, source.from]; source.category = 'background'; source.orb = 1.025;
      // Move the focused canonical row in source order as well as updating its facts.
      if (sourceIndex > 0) current.chart.aspects = [source, ...current.chart.aspects.filter((_, i) => i !== sourceIndex)];
      await page.evaluate(() => window.dispatchEvent(new Event('online')));
      await page.waitForFunction((identity) => document.getElementById('chart-result').dataset.chartIdentity === identity, current.chart.chart_identity);
      assert.equal(await count(), 1);
      assert.equal(await page.evaluate(() => document.activeElement === window.savedAspect), true);
      assert.equal(await page.locator('#aspects-table tbody tr:visible td').nth(2).textContent(), 'Фоновый');
      assert.equal(await page.locator('#aspects-table tbody tr:visible td').nth(3).textContent(), '1°02′');
      current = structuredClone(current); current.chart.chart_identity += '-ambiguous';
      current.chart.aspects.push({ ...source, category: 'working' });
      await page.evaluate(() => window.dispatchEvent(new Event('online')));
      await page.waitForFunction((identity) => document.getElementById('chart-result').dataset.chartIdentity === identity, current.chart.chart_identity);
      assert.equal(await count(), current.chart.aspects.length);
      assert.equal(await page.locator('#aspect-warnings').isVisible(), true);
      assert.equal(await page.locator('#aspects-table tbody button:disabled').count(), 2);
      assert.equal(await page.locator('#aspects-table tbody button[aria-pressed="true"]').count(), 0);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      assert.equal(overflow, false); assert.deepEqual(errors, []);
      await page.screenshot({ path: path.join(__dirname, 'html-' + width + '.png'), fullPage: true });
      output.cases.push({ width, initial_aspects: 5, initial_houses: 5, source_points: chart.points.length,
        native_enter_space: true, retained_focus_and_node: true, no_programmatic_focus_or_scroll: true,
        html_Q44: contactSizes.length, resize_preserved: true, automatic_reconcile: true,
        full_source_S1: true, no_horizontal_overflow: true, requests: calls, page_errors: errors });
      await page.close();
    }
    output.status = 'PASS';
    output.input_sha = '502589dbadd382fbe39e3cf1fd763abb52ffc620';
    const sources = fs.readdirSync(ui).filter((name) => /\.(?:mjs|css|html)$/.test(name))
      .map((name) => path.join(ui, name));
    sources.push(__filename, path.join(root, 'tests/ui/fixtures/natal_1985_chart_dto.json'),
      path.join(root, 'tests/http_api/golden/session_view.json'));
    output.source_sha256 = Object.fromEntries(sources.map((file) => [path.relative(root, file).replaceAll('\\', '/'),
      createHash('sha256').update(fs.readFileSync(file)).digest('hex')]));
    output.source_lf_sha256 = Object.fromEntries(sources.map((file) => [path.relative(root, file).replaceAll('\\', '/'),
      createHash('sha256').update(fs.readFileSync(file, 'utf8').replaceAll('\r\n', '\n')).digest('hex')]));
    fs.writeFileSync(path.join(__dirname, 'actual.json'), JSON.stringify(output, null, 2) + '\n');
    console.log('D007_HTML_BROWSER_OK widths=1440/768/360 native_keyboard=true retained_focus=true HTML_Q44=true S1=true no_activation_HTTP=true');
  } finally {
    await browser?.close(); await new Promise((resolve) => server.close(resolve));
  }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
