/* Run after starting Hugo: node tests/async_knowledge_browser.cjs [page URL] */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');
const base = process.argv[2] || 'http://127.0.0.1:1313/projects/python-async-concurrency/knowledge-map/';
const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'async-knowledge-browser-'));
const chrome = spawn(process.env.CHROME_BINARY || '/usr/bin/google-chrome', [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  '--remote-debugging-port=0', `--user-data-dir=${path.join(directory, 'profile')}`, 'about:blank',
], { stdio: 'ignore' });
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
let socket;
let secondSocket;

(async () => {
  const portFile = path.join(directory, 'profile', 'DevToolsActivePort');
  for (let i = 0; i < 100 && !fs.existsSync(portFile); i++) await pause(50);
  const port = fs.readFileSync(portFile, 'utf8').split('\n')[0];
  const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true });
    socket.addEventListener('error', reject, { once: true });
  });
  let nextId = 0;
  const requests = new Map();
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (!message.id) return;
    const request = requests.get(message.id);
    requests.delete(message.id);
    if (message.error) request.reject(new Error(JSON.stringify(message.error)));
    else request.resolve(message.result);
  });
  const call = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++nextId;
    requests.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
  const evaluate = async expression => {
    const result = await call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const ready = async () => {
    for (let i = 0; i < 100; i++) {
      if (await evaluate('document.readyState === "complete" && !!document.querySelector("[data-card-content]:not([hidden])")')) return;
      await pause(50);
    }
    throw new Error('Knowledge map did not initialize');
  };
  const reload = async () => { await call('Page.reload', { ignoreCache: true }); await pause(100); await ready(); };
  await call('Page.enable');
  await call('Runtime.enable');
  await call('Page.navigate', { url: base });
  await ready();
  await evaluate('localStorage.removeItem("python-async-knowledge-v1")');
  await reload();
  const config = await evaluate('JSON.parse(document.querySelector("[data-knowledge-config]").textContent)');
  assert.equal(config.nodes.length, 21);
  assert.equal(await evaluate('document.querySelectorAll("[data-select-node]").length'), 21);
  const state = () => evaluate('JSON.parse(localStorage.getItem("python-async-knowledge-v1"))');
  assert.deepEqual((await state()).records, {});

  const reports = [];
  for (const width of [1440, 390]) {
    await call('Emulation.setDeviceMetricsOverride', { width, height: 950, deviceScaleFactor: 1, mobile: width < 600 });
    await evaluate('document.querySelector("[data-select-node=event]").click()');
    assert.equal(await evaluate('document.getElementById("knowledge-explanation").hidden'), true);
    await evaluate('document.querySelector("[data-reveal]").focus()');
    await call('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, text: '\r' });
    await call('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
    assert.equal(await evaluate('document.getElementById("knowledge-explanation").hidden'), false);
    assert.deepEqual((await state()).records, {}, 'Opening answers must not grade');
    const layout = await evaluate(`({width: innerWidth, scrollWidth: document.documentElement.scrollWidth,
      nav: !!document.querySelector('.project-nav__desktop'),
      idsUnique: (() => { const ids = [...document.querySelectorAll('[id]')].map(el => el.id); return ids.length === new Set(ids).size; })(),
      focus: document.activeElement.hasAttribute('data-reveal')})`);
    assert.ok(layout.scrollWidth <= width + 1, JSON.stringify(layout));
    assert.ok(layout.nav && layout.idsUnique && layout.focus);
    await evaluate('document.getElementById("knowledge-card-title").scrollIntoView()');
    const screenshot = await call('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(`/tmp/async-knowledge-map-${width}.png`, Buffer.from(screenshot.data, 'base64'));
    reports.push({ width, overflow: false, keyboard: true });
  }

  await evaluate('document.documentElement.setAttribute("data-theme", "dark")');
  const contrast = await evaluate(`(() => {
    const styles = getComputedStyle(document.querySelector('.akm-review'));
    const luminance = color => {
      const rgb = color.match(/\\d+/g).slice(0, 3).map(Number).map(x => x / 255)
        .map(x => x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4);
      return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
    };
    const a = luminance(styles.color), b = luminance(styles.backgroundColor);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  })()`);
  assert.ok(contrast >= 4.5, 'Dark theme text contrast is too low: ' + contrast);
  await evaluate('document.documentElement.setAttribute("data-theme", "light")');

  const eventCard = config.nodes.find(node => node.id === 'event');
  const wrong = eventCard.exercise.options.find(option => option.id !== eventCard.exercise.answer).id;
  await evaluate(`document.querySelector('input[value="${wrong}"]').click(); document.querySelector('[data-exercise-form]').requestSubmit()`);
  assert.equal((await state()).records.event.level, null);
  assert.equal((await state()).records.event.lastAttempt.correct, false);
  assert.equal(await evaluate('document.querySelector("[data-review-links]").children.length'), 1);
  await evaluate(`document.querySelector('input[value="${eventCard.exercise.answer}"]').click(); document.querySelector('[data-exercise-form]').requestSubmit()`);
  assert.equal((await state()).records.event.level, null, 'Correct multiple choice does not prove mastery');
  await evaluate('document.querySelector("[data-grade=explain]").click()');
  assert.equal((await state()).records.event.level, 'explain');
  assert.equal(await evaluate('document.querySelector("[data-review-links]").children.length'), 0);
  const note = '我把通知理解成了释放锁；先判断是否在保护共享状态。';
  await evaluate(`document.querySelector('[data-note]').value = ${JSON.stringify(note)}; document.querySelector('[data-note]').dispatchEvent(new Event('input')); document.querySelector('[data-recall]').value = '标志为真才能通过'; document.querySelector('[data-recall]').dispatchEvent(new Event('input'))`);
  await reload();
  assert.equal(await evaluate('document.querySelector("[data-note]").value'), note);
  assert.equal(await evaluate('document.querySelector("[data-recall]").value'), '');
  assert.equal(await evaluate('document.querySelector("[data-previous-recall-panel]").open'), false);
  assert.equal(await evaluate('document.querySelector("[data-previous-recall]").textContent'), '标志为真才能通过');
  assert.equal(await evaluate('document.getElementById("knowledge-explanation").hidden'), true);

  await evaluate('document.querySelector("[data-reveal]").click(); [...document.querySelectorAll("[data-relations] button")].find(button => button.textContent.includes("Lock")).click()');
  assert.equal(await evaluate('location.hash'), '#lock');
  assert.equal(await evaluate('document.activeElement.id'), 'knowledge-card-title');
  assert.equal(await evaluate('document.getElementById("knowledge-explanation").hidden'), true);

  // Exercise real file input and browser download, not a mock of serialization.
  const downloadDirectory = path.join(directory, 'downloads');
  fs.mkdirSync(downloadDirectory);
  await call('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: downloadDirectory });
  await evaluate('document.querySelector("[data-export]").click()');
  let downloaded;
  for (let i = 0; i < 100; i++) {
    downloaded = fs.readdirSync(downloadDirectory).find(file => file.endsWith('.json'));
    if (downloaded) break;
    await pause(50);
  }
  assert.ok(downloaded, 'Backup download missing');
  const backup = JSON.parse(fs.readFileSync(path.join(downloadDirectory, downloaded), 'utf8'));
  assert.equal(backup.records.event.note, note);
  const importFile = path.join(directory, 'import.json');
  backup.records.event.note = '由备份恢复的记录';
  backup.records.event.updatedAt += 100000;
  fs.writeFileSync(importFile, JSON.stringify(backup));
  const doc = await call('DOM.getDocument');
  const input = await call('DOM.querySelector', { nodeId: doc.root.nodeId, selector: '[data-import]' });
  await call('DOM.setFileInputFiles', { nodeId: input.nodeId, files: [importFile] });
  for (let i = 0; i < 100 && (await state()).records.event.note !== '由备份恢复的记录'; i++) await pause(25);
  assert.equal((await state()).records.event.note, '由备份恢复的记录');
  const beforeBad = await state();
  fs.writeFileSync(importFile, '{bad');
  await call('DOM.setFileInputFiles', { nodeId: input.nodeId, files: [importFile] });
  await pause(150);
  assert.deepEqual(await state(), beforeBad);
  assert.ok(await evaluate('document.querySelector("[data-save-status]").textContent.includes("原有记录未被修改")'));

  // An older open tab must not overwrite a newer answer merely by selecting a card.
  const secondTarget = await (await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(base)}`, { method: 'PUT' })).json();
  secondSocket = new WebSocket(secondTarget.webSocketDebuggerUrl);
  await new Promise(resolve => secondSocket.addEventListener('open', resolve, { once: true }));
  let secondId = 0;
  const secondRequests = new Map();
  secondSocket.addEventListener('message', event => {
    const result = JSON.parse(event.data);
    if (result.id) {
      const pending = secondRequests.get(result.id);
      secondRequests.delete(result.id);
      pending(result.result);
    }
  });
  const secondEvaluate = expression => new Promise(resolve => {
    const id = ++secondId;
    secondRequests.set(id, result => resolve(result.result.value));
    secondSocket.send(JSON.stringify({ id, method: 'Runtime.evaluate', params: { expression, returnByValue: true } }));
  });
  for (let i = 0; i < 100; i++) {
    if (await secondEvaluate('!!document.querySelector("[data-card-content]:not([hidden])")')) break;
    await pause(50);
  }
  await evaluate('document.querySelector("[data-select-node=lock]").click(); document.querySelector("[data-note]").value="刚更新的共享状态记录"; document.querySelector("[data-note]").dispatchEvent(new Event("input"))');
  await secondEvaluate('document.querySelector("[data-select-node=event]").click()');
  assert.equal((await state()).records.lock.note, '刚更新的共享状态记录', 'A stale tab must preserve new records');

  // Every generated lesson target exists; local URLs use the current test origin.
  for (const lesson of config.nodes.flatMap(node => node.lessons)) {
    const response = await fetch(new URL(lesson.url, base));
    assert.equal(response.status, 200, lesson.url);
  }
  // Broken saved data must not be silently overwritten merely by viewing.
  await evaluate('localStorage.setItem("python-async-knowledge-v1", "broken backup")');
  await reload();
  assert.equal(await evaluate('localStorage.getItem("python-async-knowledge-v1")'), 'broken backup');
  assert.ok(await evaluate('document.querySelector("[data-save-status]").textContent.includes("原数据")'));
  fs.writeFileSync(importFile, JSON.stringify(backup));
  const brokenDoc = await call('DOM.getDocument');
  const recoveryInput = await call('DOM.querySelector', { nodeId: brokenDoc.root.nodeId, selector: '[data-import]' });
  await evaluate(`window.originalSetItem = Storage.prototype.setItem;
    Storage.prototype.setItem = function(key, value) {
      if (key.endsWith('-recovery')) throw new DOMException('Storage full', 'QuotaExceededError');
      return window.originalSetItem.call(this, key, value);
    }`);
  await call('DOM.setFileInputFiles', { nodeId: recoveryInput.nodeId, files: [importFile] });
  await pause(150);
  assert.equal(await evaluate('localStorage.getItem("python-async-knowledge-v1")'), 'broken backup');
  assert.ok(await evaluate('!!document.querySelector("[data-save-status] a")'),
    'A failed recovery save must leave the original download link usable');
  await evaluate('Storage.prototype.setItem = window.originalSetItem');
  await call('DOM.setFileInputFiles', { nodeId: recoveryInput.nodeId, files: [importFile] });
  await pause(150);
  await reload();
  assert.equal(await evaluate('document.querySelectorAll("[data-recovery-links] a").length'), 1,
    'Valid import must preserve the unreadable original across reload');
  assert.equal(await evaluate('fetch(document.querySelector("[data-recovery-links] a").href).then(response => response.text())'), 'broken backup');
  console.log(JSON.stringify({ reports, concepts: config.nodes.length, persistence: true, hiddenPreviousAnswer: true,
    relationNavigation: true, exportImport: true, invalidDataPreserved: true }, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; }).finally(async () => {
  if (socket) socket.close();
  if (secondSocket) secondSocket.close();
  const stopped = new Promise(resolve => {
    if (chrome.exitCode !== null) resolve();
    else chrome.once('exit', resolve);
  });
  chrome.kill('SIGTERM');
  await stopped;
  // Chromium helper processes can finish writing after its main process exits.
  for (let attempt = 0; attempt < 5; attempt++) {
    try {
      await fs.promises.rm(directory, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
      return;
    } catch (error) {
      if (attempt === 4) console.warn('Temporary browser profile could not be removed:', directory);
      else await pause(200);
    }
  }
});
