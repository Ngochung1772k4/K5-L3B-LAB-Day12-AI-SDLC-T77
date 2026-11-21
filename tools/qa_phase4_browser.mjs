// Real Chrome/Canvas audit. No injected snapshots or fabricated frame results.
// Usage: node tools/qa_phase4_browser.mjs <python.exe> <new-proof-dir>
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn, execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const [python, proofArg] = process.argv.slice(2);
if (!python || !proofArg) throw new Error('Usage: node tools/qa_phase4_browser.mjs <python> <new-proof-dir>');
const proof = path.resolve(proofArg);
fs.mkdirSync(proof, { recursive: false });
const root = process.cwd();
const chromePath = process.env.CHROME_PATH || (process.platform === 'win32'
  ? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' : 'google-chrome');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 't77-p4-browser-'));
const children = [], connections = [];
const report = { browser: chromePath, snapshots: [], checks: [], errors: [], pageErrors: [],
  measurement: 'Headless Chrome, software rendering (--disable-gpu); not a desktop GPU measurement' };
report.revision = execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
report.sourceHashes = Object.fromEntries(['chonoi/web/index.html', 'chonoi/live.py', 'tools/qa_phase4_browser.mjs'].map(
  name => [name, createHash('sha256').update(fs.readFileSync(name)).digest('hex')]));
let browserCDP;
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const save = (name, data) => fs.writeFileSync(path.join(proof, name), data, { flag: 'wx' });
const check = (condition, description, fatal = true) => {
  report.checks.push({ description, status: condition ? 'PASS' : 'FAIL' });
  if (!condition && fatal) throw new Error(description);
};

async function until(callback, timeout = 15000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const value = await callback();
    if (value) return value;
    await delay(50);
  }
  throw new Error('Timed out waiting for browser/server');
}

function launch(executable, args) {
  const child = spawn(executable, args, {
    cwd: root, windowsHide: true,
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONUTF8: '1' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  child.output = ''; child.errorOutput = '';
  child.stdout.on('data', data => { child.output += data; });
  child.stderr.on('data', data => { child.errorOutput += data; });
  child.on('error', error => { child.errorOutput += String(error); });
  children.push(child);
  return child;
}

async function live(mode, scenario, label) {
  const fixture = path.join(temp, label + '.json');
  fs.writeFileSync(fixture, JSON.stringify(scenario));
  const args = ['-B', '-m', 'chonoi.live', '--mode', mode, '--seed', '42', '--port', '0', '--scenario', fixture];
  const child = launch(python, args);
  const url = await until(() => child.output.match(/http:\/\/127\.0\.0\.1:\d+\//)?.[0]);
  report.snapshots.push({ label, argv: [python, ...args], scenario, url });
  return { child, url };
}

async function connect(url) {
  const ws = new WebSocket(url);
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
  let next = 0;
  const pending = new Map();
  ws.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.method === 'Runtime.exceptionThrown') report.pageErrors.push(message.params);
    if (message.id && pending.has(message.id)) {
      const { resolve, reject, timer } = pending.get(message.id); pending.delete(message.id); clearTimeout(timer);
      message.error ? reject(new Error(JSON.stringify(message.error))) : resolve(message.result);
    }
  };
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++next;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error('CDP timeout: ' + method)); }, 15000);
    pending.set(id, { resolve, reject, timer }); ws.send(JSON.stringify({ id, method, params }));
  });
  const evaluate = async expression => {
    const result = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const connection = { ws, send, evaluate }; connections.push(connection); return connection;
}

async function page(port, url) {
  const { targetId } = await browserCDP.send('Target.createTarget', { url: 'about:blank' });
  const cdp = await connect(`ws://127.0.0.1:${port}/devtools/page/${targetId}`);
  await cdp.send('Page.enable'); await cdp.send('Runtime.enable');
  await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false });
  await cdp.send('Page.navigate', { url });
  await until(() => cdp.evaluate('typeof alerts === "function" && snap !== null'));
  // Observe actual Canvas draw calls; preserve and invoke the original drawing
  // implementation. Snapshots still come exclusively from the live server.
  await cdp.evaluate(`window.__drawn=[]; const actualFillText=ctx.fillText.bind(ctx);
    ctx.fillText=function(...args){__drawn.push({text:String(args[0]),color:ctx.fillStyle,font:ctx.font});
      if(__drawn.length>1000)__drawn.splice(0,500);return actualFillText(...args)};`);
  return cdp;
}

async function capture(cdp, name) {
  await delay(150);
  const details = await cdp.evaluate('({HC, mode:snap.mode, phase:snap.phase, state:snap.state, canvas:[cv.width,cv.height], snapshot:snap, drawn:__drawn})');
  const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
  save(name + '.png', Buffer.from(shot.data, 'base64'));
  save(name + '.json', JSON.stringify(details, null, 2));
  return details;
}

async function key(cdp, keyName, code) {
  await cdp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: keyName, code });
  await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: keyName, code });
}

async function state(url) { return (await fetch(url + 'state')).json(); }

try {
  const profile = path.join(temp, 'chrome'); fs.mkdirSync(profile);
  const chrome = launch(chromePath, ['--headless=new', '--no-first-run', '--no-default-browser-check',
    '--disable-background-networking', '--disable-extensions', '--disable-gpu',
    '--remote-debugging-port=0', '--user-data-dir=' + profile, '--window-size=1280,720', 'about:blank']);
  const port = await until(() => {
    const file = path.join(profile, 'DevToolsActivePort');
    return fs.existsSync(file) && fs.readFileSync(file, 'utf8').split('\n')[0];
  });
  report.browserVersion = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
  browserCDP = await connect(report.browserVersion.webSocketDebuggerUrl);
  const g = await live('gather', { gather: {
    player: { pos: [60, 24], oxygen_ticks: 400, invuln_ticks: 90 }, hold: [], nodes: [], fish: [],
    random_fish: false, time_left_ticks: 600,
    monsters: [{ id: 'M1', kind: 'ca_sau', pos: [64, 24], waypoints: [[64, 24], [65, 24]] }],
  } }, 'gather-warnings');
  const gp = await page(port, g.url + '?contrast=high');
  const gs = await capture(gp, 'ui-gather-high-contrast');
  check(gs.HC, 'Gather high contrast enabled through query parameter');
  check(gs.drawn.some(d => d.text.includes('THỦY QUÁI GẦN')), 'Actual canvas displays nearby-monster text');
  check(gs.drawn.some(d => d.text.includes('OXY SẮP HẾT')), 'Actual canvas displays low-oxygen text');
  check(gs.drawn.some(d => d.text.includes('🐊')) && gs.drawn.some(d => d.text.includes('🫧')),
        'Monster and oxygen warnings include icons as well as words');
  check(gs.drawn.some(d => d.text.includes('OXY SẮP HẾT') && d.color === '#ffff00' && d.font.includes('28px')),
        'High contrast changes warning text to yellow 28px');
  await gp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'h', code: 'KeyH' });
  await gp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'h', code: 'KeyH' });
  check(await gp.evaluate('HC === false'), 'H toggles high contrast off');
  await capture(gp, 'ui-gather-normal');
  await gp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'h', code: 'KeyH' });
  await gp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'h', code: 'KeyH' });
  check(await gp.evaluate('HC === true && localStorage.getItem("chonoi-hc") === "1"'), 'H toggles on and persists preference');

  const q = await live('quan', { quan: { stock: [], random_customers: false, time_left_ticks: 600,
    customers: [{ id: 'C1', table_id: 'T1', dish_id: 'ca_loc_nuong_trui', order_status: 'unfulfillable',
      reserved: [], patience_ticks_left: 800 }] } }, 'quan-warning');
  const qp = await page(port, q.url + '?contrast=high');
  const qs = await capture(qp, 'ui-quan-high-contrast');
  check(qs.drawn.some(d => d.text.includes('KHÁCH SẮP GIẬN') && d.text.includes('T1')), 'Actual canvas displays impatient-customer warning');
  check(qs.drawn.some(d => d.text.includes('KHÁCH SẮP GIẬN') && d.color === '#ffff00'), 'Customer warning uses high contrast');
  check(qs.drawn.some(d => d.text.includes('😠')), 'Customer warning has an icon');

  await key(qp, 'h', 'KeyH');
  await key(qp, 'h', 'KeyH');
  await qp.send('Page.navigate', { url: q.url });
  await until(() => qp.evaluate('snap !== null && HC === true'));
  check(await qp.evaluate('HC'), 'High contrast remains enabled after reload');

  // These are validated server fixtures, never snapshots injected into JS.
  const quiet = await live('quan', { quan: { stock: [], customers: [], random_customers: false } }, 'no-customer');
  const quietPage = await page(port, quiet.url + '?contrast=high');
  const quietShot = await capture(quietPage, 'ui-no-customer');
  check(!quietShot.drawn.some(d => d.text.includes('KHÁCH SẮP GIẬN')), 'No customer warning for an empty restaurant');
  const safe = await live('gather', { gather: { fish: [], nodes: [], monsters: [], random_fish: false } }, 'safe-gather');
  const safePage = await page(port, safe.url + '?contrast=high');
  const safeShot = await capture(safePage, 'ui-safe-gather');
  check(!safeShot.drawn.some(d => /THỦY QUÁI GẦN|OXY SẮP HẾT|HẾT HƠI/.test(d.text)), 'No danger warnings at the safe surface');

  const day = await live('day', {
    day: { money: 1000, earned: 1000 },
    gather: { hold: [{id:'I7',kind:'ca_loc',fresh:80}], time_left_ticks: 600,
      nodes: [], fish: [], monsters: [], random_fish: false },
    quan: { time_left_ticks: 120, random_customers: false },
  }, 'live-day');
  const dp = await page(port, day.url + '?contrast=high');
  const dg = await capture(dp, 'ui-day-gather');
  check(dg.mode === 'day' && dg.phase === 'gather', 'Day starts in Gather');
  await key(dp, 'p', 'KeyP');
  await until(async () => (await state(day.url)).state === 'paused');
  const paused = await state(day.url); await delay(200); const stillPaused = await state(day.url);
  check(paused.sim_tick === stillPaused.sim_tick && paused.time_left_ticks === stillPaused.time_left_ticks
    && JSON.stringify(paused.hold) === JSON.stringify(stillPaused.hold), 'P pauses timer, simulation and freshness through real HTTP input');
  await key(dp, 'p', 'KeyP');
  await until(async () => (await state(day.url)).state === 'playing');
  await dp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'w', code: 'KeyW' });
  await key(dp, 'e', 'KeyE');
  await until(() => dp.evaluate('snap.phase === "quan"'));
  const dq = await capture(dp, 'ui-day-quan');
  // W means up in Gather and north (+z) in Quán, including a key held at transition.
  const north = dq.snapshot.player.pos[1] > dq.snapshot.meta.start_pos[1];
  report.heldMovementAtTransition = { actual: dq.snapshot.player.pos,
    expected: 'Quán z > ' + dq.snapshot.meta.start_pos[1] + ' while W remains held', snapshot: dq.snapshot };
  check(north, 'Holding W across Gather → Quán continues north (+z)', false);
  await dp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'w', code: 'KeyW' });
  check(dq.snapshot.stock[0].id === 'I7', 'Day Quán keeps Gather physical item identity');
  const ge = dq.snapshot.events.find(e => e.name === 'gather_end');
  check(ge?.data.inventory.items[0].id === 'I7' && dq.snapshot.stock[0].fresh <= ge.data.inventory.items[0].fresh,
    'Real day handoff inventory is present; Quán freshness continues decaying');
  await until(() => dp.evaluate('snap.phase === "shop"'));
  const ds = await capture(dp, 'ui-day-shop');
  check(ds.drawn.some(d => d.text.includes('SHOP cuối Ngày')), 'Browser renders the Shop screen');
  await key(dp, '1', 'Digit1');
  await until(async () => (await state(day.url)).upgrades.oxygen === 1);
  const bought = await state(day.url);
  check(bought.money === 1000 - bought.shop_upgrades.oxygen[0].price && bought.earned === 1000
    && !bought.active_upgrades.oxygen, 'Shop key buys once, keeps earned and defers active level');
  await key(dp, 'Enter', 'Enter');
  await until(async () => { const s = await state(day.url); return s.day === 2 && s.phase === 'gather'; });
  const next = await state(day.url);
  check(next.active_upgrades.oxygen === 1 && next.hold[0].id !== 'I7', 'Enter starts next day with active upgrade and a new item ID');
  await key(dp, 'r', 'KeyR');
  await until(async () => { const s = await state(day.url); return s.day === 1 && s.money === 1000 && !s.upgrades.oxygen; });
  report.liveDay = { gather: dg.snapshot, quan: dq.snapshot, shop: ds.snapshot, bought, next,
    restarted: await state(day.url) };

  // A completed one-day run must remain finished until explicit restart.
  const one = await live('day', { gather: { time_left_ticks: 1, monsters: [], random_fish: false },
    quan: { time_left_ticks: 1, random_customers: false } }, 'live-finished');
  for (let i = 0; i < 5; i++) {
    await until(async () => (await state(one.url)).phase === 'shop');
    await fetch(one.url + 'input', {method:'POST',body:JSON.stringify({shop_done:true})});
    await delay(100);
    await fetch(one.url + 'input', {method:'POST',body:JSON.stringify({shop_done:false})});
  }
  const finished = await until(async () => { const s = await state(one.url); return s.finished && s; });
  check(finished.reason === 'days_complete' && finished.day === 5, 'Live default five-day run reaches days_complete after final Shop');
  report.liveFinished = finished;

  const b = await live('gather', { gather: {} }, 'browser-benchmark');
  const bp = await page(port, b.url);
  await bp.evaluate(`window.__timestamps=[];const realRAF=requestAnimationFrame.bind(window);
    window.requestAnimationFrame=callback=>realRAF(t=>{callback(t);__timestamps.push(t)});`);
  await delay(3000);
  const start = await bp.evaluate('performance.now()');
  await delay(30000);
  const timing = await bp.evaluate(`({end:performance.now(),timestamps:__timestamps,
    first_contentful_paint:performance.getEntriesByName('first-contentful-paint')[0]?.startTime ?? null,
    canvas:[cv.width,cv.height],position:snap.player.pos})`);
  const times = timing.timestamps.filter(t => t >= start && t <= timing.end);
  const intervals = times.slice(1).map((t, i) => (t - times[i]) / 1000).sort((a, b) => b - a);
  const k = Math.max(1, Math.ceil(intervals.length / 100));
  report.browserBenchmark = { seed: 42, warmup_s: 3, requested_s: 30, frames: times.length,
    measured_s: (timing.end - start) / 1000, avg_fps: times.length / ((timing.end - start) / 1000),
    p1_low_fps: k / intervals.slice(0, k).reduce((a, b) => a + b, 0),
    first_contentful_paint_ms: timing.first_contentful_paint, canvas: timing.canvas,
    position: timing.position, frame_timestamps_ms: times,
    note: 'Independent real browser RAF measurement; not the production bench_cmd software-framebuffer metric.' };
  check(times.length > 1 && intervals.length > 0, 'Benchmark observed completed animation callbacks');
  check(report.browserBenchmark.measured_s >= 30 && [report.browserBenchmark.avg_fps, report.browserBenchmark.p1_low_fps].every(x => Number.isFinite(x) && x > 0),
    'Browser timing is finite, positive and measured for 30 seconds');
  check(report.pageErrors.length === 0, 'No uncaught JavaScript exceptions');
  await capture(bp, 'ui-browser-benchmark');
  report.status = report.checks.some(c => c.status === 'FAIL') ? 'FAIL' : 'PASS';
  if (report.status === 'FAIL') process.exitCode = 1;
  console.log(JSON.stringify({ checks: report.checks, browserBenchmark: { ...report.browserBenchmark, frame_timestamps_ms: undefined } }));
} catch (error) {
  report.status = report.checks.some(c => c.status === 'FAIL') ? 'FAIL' : 'ERROR';
  report.errors.push(String(error.stack || error), String(error.cause || ''));
  console.error(String(error.stack || error)); process.exitCode = 1;
} finally {
  report.processes = children.map(c => ({argv:c.spawnargs, exit_code:c.exitCode, stdout:c.output, stderr:c.errorOutput}));
  save('browser-audit.json', JSON.stringify(report, null, 2));
  for (const connection of connections) connection.ws.close();
  for (const child of children) if (child.exitCode === null) child.kill();
  await delay(500);
  // The resolved target is the exact generated directory beneath OS temp.
  const resolved = path.resolve(temp), base = path.resolve(os.tmpdir()) + path.sep;
  if (resolved.startsWith(base) && path.basename(resolved).startsWith('t77-p4-browser-')) {
    try { fs.rmSync(resolved, { recursive: true, force: true }); } catch { /* Chrome may still hold profile locks. */ }
  }
}
