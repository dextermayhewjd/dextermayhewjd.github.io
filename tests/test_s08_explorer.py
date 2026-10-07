"""Verify the S08 overview and module disclosure in a real local browser.

Uses Hugo, Chrome and the Python standard library; makes no external requests.
"""

import functools
import html
import http.server
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import unittest


REPO = Path(__file__).resolve().parents[1]
PROBE = r"""
<script>
window.addEventListener('load', async () => {
  const check = (ok, message) => { if (!ok) throw new Error(message); };
  const pause = () => new Promise(resolve => setTimeout(resolve, 40));
  const result = {passed: false};
  try {
    const root = document.querySelector('[data-diagram-explorer]');
    check(root, 'S08 interactive overview is missing');
    check(root.dataset.ready === 'true', 'Explorer did not initialize');
    const overview = root.querySelector('svg');
    const canvas = root.querySelector('.architecture-diagram__canvas');
    check(overview.viewBox.baseVal.width === 1200 && overview.getBoundingClientRect().width >= 1200,
      'The overview canvas was not widened without shrinking text');
    if (innerWidth >= 1180) check(canvas.clientWidth > 760, 'Actual article space is still limited to the old width');
    if (innerWidth < 760) check(canvas.scrollWidth > canvas.clientWidth, 'Narrow screens need scrolling inside the diagram');
    overview.scrollIntoView({block:'start',behavior:'instant'});
    await pause();
    const baseline = document.querySelector('figure.architecture-diagram');
    const originalBaseline = baseline.outerHTML;
    const shape = () => JSON.stringify([...overview.querySelectorAll('rect, path')]
      .map(node => [...['x','y','width','height','d','fill','stroke'].map(a => node.getAttribute(a)),
        getComputedStyle(node).fill, getComputedStyle(node).stroke]));
    const originalShape = shape();
    const bounds = () => { const b=overview.getBoundingClientRect(); return [b.x,b.y,b.width,b.height]; };
    const originalBounds = JSON.stringify(bounds());
    const button = key => root.querySelector('[data-module-button="'+key+'"]');
    const card = key => root.querySelector('[data-module-card="'+key+'"]');
    const opened = () => [...root.querySelectorAll('[data-module-card][open]')];
    check(root.querySelectorAll('[data-module-button]').length === 7, 'Expected seven bounded modules');
    check(opened().length === 0, 'Default overview should not open module details');

    const legend=root.querySelector('.architecture-diagram__legend-details');
    check(legend && !legend.open, 'Full color explanation should be collapsed by default');
    check(legend.querySelectorAll('summary .architecture-diagram__swatch').length >= 3,
      'The compact legend should keep the used color samples visible');

    const prepare=root.querySelector('a[data-module="prepare"]');
    const scrollBefore=scrollY;
    const hover = node => {
      const box=node.querySelector('rect').getBoundingClientRect();
      overview.dispatchEvent(new PointerEvent('pointermove',{pointerType:'mouse',
        clientX:box.left+box.width/2,clientY:box.top+box.height/2,bubbles:true}));
    };
    const leave = () => overview.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'}));
    hover(prepare); await pause();
    check(overview.dataset.connectionSelection==='prepare', 'Hover does not preview input/output arrows');
    check(overview.querySelector('[data-from="history"][data-to="prepare"]').classList.contains('is-related'),
      'Hover missed the incoming history arrow');
    check(overview.querySelector('[data-from="prepare"][data-to="summary"]').classList.contains('is-related'),
      'Hover missed the conditional summary output');
    check(root.dataset.selected==='' && opened().length===0 && root.querySelector('[data-explorer-panel]').hidden,
      'Hover must not select a module or open details');
    hover(overview.querySelector('[data-overview-stage="system"]')); await pause();
    check(overview.querySelector('[data-from="system"][data-to="model"]').classList.contains('is-related'),
      'Hover missed the SYSTEM reference arrow');
    leave(); await pause();
    check(!overview.querySelector('.is-related, .is-unrelated'), 'Mouse leave kept transient highlights');
    check(scrollY===scrollBefore && JSON.stringify(bounds())===originalBounds && shape()===originalShape,
      'Hover moved the diagram or changed its evolution colors');
    prepare.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); await pause();
    check(overview.dataset.connectionSelection==='prepare', 'The selected module has no input/output selection');
    const selectedRoutes=[...overview.querySelectorAll('path.is-related[data-from]')];
    check(selectedRoutes.some(p=>p.dataset.from==='history' && p.dataset.to==='prepare'),
      'The incoming history arrow was not highlighted');
    check(selectedRoutes.some(p=>p.dataset.from==='prepare' && p.dataset.to==='model'),
      'The normal output arrow was not highlighted');
    check(selectedRoutes.some(p=>p.dataset.from==='prepare' && p.dataset.to==='summary'),
      'The conditional summary output was not highlighted');
    check(overview.querySelector('path[data-from="model"][data-to="decision"]').classList.contains('is-unrelated'),
      'Unrelated arrows were not visually separated');
    check(root.querySelector('[data-connection-summary]').textContent.includes('对话历史'),
      'The arrow summary does not explain the input');
    const arrow=overview.querySelector('path[data-from="history"][data-to="prepare"]');
    check(Number.parseFloat(getComputedStyle(arrow).strokeWidth)>3 && arrow.hasAttribute('marker-end'),
      'The selected arrow and its head are not emphasized');
    const selectedHead=overview.querySelector('marker[id="'+arrow.getAttribute('marker-end').match(/#([^)]+)/)[1]+'"]');
    check(selectedHead && selectedHead.getAttribute('markerUnits')==='userSpaceOnUse' &&
      Number(selectedHead.getAttribute('markerWidth'))===12, 'Selected arrowheads overlap neighboring ports');
    const panel=root.querySelector('[data-explorer-panel]');
    check(panel && !panel.hidden,'Nearby detail panel is missing');
    hover(overview.querySelector('[data-overview-stage="system"]')); await pause();
    check(overview.dataset.connectionSelection==='system' && card('prepare').open,
      'Hover preview disturbed the clicked module details');
    leave(); await pause();
    check(overview.dataset.connectionSelection==='prepare' && card('prepare').open,
      'Leaving hover did not restore the clicked module');
    const touchBox=overview.querySelector('[data-overview-stage="system"] rect').getBoundingClientRect();
    overview.dispatchEvent(new PointerEvent('pointermove',{pointerType:'touch',
      clientX:touchBox.left+10,clientY:touchBox.top+10,bubbles:true}));
    check(overview.dataset.connectionSelection==='prepare', 'Touch scrolling left a false hover preview');
    const p=panel.getBoundingClientRect(), n=prepare.getBoundingClientRect();
    check(p.top>=0 && p.left>=0 && p.bottom<=innerHeight+1 && p.right<=innerWidth+1,
      'The detail panel is outside the current viewport');
    const dx=Math.max(p.left-n.right,n.left-p.right,0);
    const dy=Math.max(p.top-n.bottom,n.top-p.bottom,0);
    check(Math.hypot(dx,dy)<=26,'Details are too far from the clicked module');
    check(!(p.left<n.right && p.right>n.left && p.top<n.bottom && p.bottom>n.top),
      'Details cover the selected module');
    check(scrollY===scrollBefore,'Opening details scrolled the whole page');
    const reader=card('prepare').querySelector('[data-step-reader]');
    check(reader,'The local diagram and function code are not connected');
    for(const name of ['prepare','tool_result_budget','snip_compact','estimate_chars',
      'micro_compact','fit_tool_results','compact_history','agent_loop']) {
      check(reader.querySelector('[data-function-code="'+name+'"]'),'Missing step function: '+name);
    }
    const localStep=reader.querySelector('[data-step-stage="budget"]');
    check(localStep,'The diagram step cannot select its function');
    localStep.dispatchEvent(new PointerEvent('pointerenter',{bubbles:false}));
    check(reader.querySelector('[data-function-code="tool_result_budget"]').classList.contains('is-function-selected'),
      'Pointer selection did not highlight the matching function');
    localStep.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); await pause();
    const codeBox=reader.querySelector('[data-function-code="tool_result_budget"]');
    const codeViewport=reader.querySelector('[data-function-list]');
    check(codeBox.getBoundingClientRect().top>=codeViewport.getBoundingClientRect().top-2 &&
      codeBox.getBoundingClientRect().top<codeViewport.getBoundingClientRect().bottom,
      'Selected function did not enter the code viewport');
    check(scrollY===scrollBefore,'Step selection scrolled the whole page');
    const condition=reader.querySelector('[data-step-stage="size-first"]');
    condition.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));
    check(reader.querySelector('[data-function-code="estimate_chars"]').classList.contains('is-function-selected'),
      'Condition was not linked to its actual implementation');
    reader.querySelector('[data-function-code="fit_tool_results"] button').click(); await pause();
    const reverse=reader.querySelector('[data-step-stage="micro-fit"]');
    check(reverse.classList.contains('is-step-selected'),'Function title did not select its graph step');
    const graphView=reverse.closest('.architecture-diagram__canvas').getBoundingClientRect();
    const reverseBox=reverse.getBoundingClientRect();
    check(reverseBox.left>=graphView.left-2 && reverseBox.right<=graphView.right+2,
      'Reverse selection did not reveal the graph step');
    check(scrollY===scrollBefore,'Reverse selection scrolled the page');
    const enlarge=root.querySelector('[data-panel-enlarge]');
    const restore=root.querySelector('[data-panel-size-reset]');
    const grip=root.querySelector('[data-panel-resize]');
    check(enlarge && restore && grip,'Panel sizing controls are missing');
    enlarge.click(); await pause();
    const large=panel.getBoundingClientRect();
    check(large.width>=p.width && large.height>p.height,'Enlarge did not increase the reading area');
    check(large.left>=0 && large.top>=0 && large.right<=innerWidth+1 && large.bottom<=innerHeight+1,
      'Expanded panel is outside the viewport');
    check(shape()===originalShape && JSON.stringify(bounds())===originalBounds,
      'Panel sizing changed the overview');
    restore.click(); await pause();
    const restored=panel.getBoundingClientRect();
    check(Math.abs(restored.width-p.width)<2,'Restore did not recover the default width');
    grip.dispatchEvent(new PointerEvent('pointerdown',{pointerId:42,clientX:restored.right-8,
      clientY:restored.bottom-8,bubbles:true,cancelable:true}));
    window.dispatchEvent(new PointerEvent('pointermove',{pointerId:42,clientX:restored.right+100,
      clientY:restored.bottom+70,bubbles:true,cancelable:true}));
    window.dispatchEvent(new PointerEvent('pointerup',{pointerId:42,bubbles:true}));
    await pause();
    const dragged=panel.getBoundingClientRect();
    check(dragged.height>restored.height,'Dragging the corner did not resize the panel');
    check(dragged.left>=0 && dragged.top>=0 && dragged.right<=innerWidth+1 && dragged.bottom<=innerHeight+1,
      'Dragged panel escaped the viewport');
    const heightBeforeKey=dragged.height;
    grip.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowUp',bubbles:true,cancelable:true}));
    await pause();
    check(panel.getBoundingClientRect().height<heightBeforeKey,'Keyboard size adjustment failed');
    restore.click(); await pause();
    root.querySelector('[data-explorer-trace]').click(); await pause();
    check(panel.hidden && opened().length===0 && overview.dataset.connectionSelection==='prepare',
      'Trace-only mode did not remove the panel while keeping the arrows');
    prepare.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); await pause();
    check(card('prepare').open && !panel.hidden, 'Details cannot reopen from trace-only mode');
    root.querySelector('[data-explorer-close]').click(); await pause();
    check(opened().length===0 && panel.hidden,'The nearby close control did not close details');

    button('budget').click(); await pause();
    check(card('budget').open && opened().length === 1, 'Budget details did not open exclusively');
    check(card('budget').textContent.includes('def tool_result_budget'), 'Budget source excerpt is missing');
    check(card('budget').querySelector('svg'), 'Budget local diagram is missing');
    check(button('budget').getAttribute('aria-expanded') === 'true', 'Expanded state is not accessible');
    check(JSON.stringify(bounds()) === originalBounds, 'Opening details moved the overview');
    check(shape() === originalShape, 'Opening details changed the graph or evolution colors');

    const keyboard = root.querySelector('a[data-module="reactive"]');
    keyboard.focus();
    check(document.activeElement === keyboard, 'SVG module cannot receive keyboard focus');
    keyboard.dispatchEvent(new KeyboardEvent('keydown', {key:' ',bubbles:true,cancelable:true}));
    await pause();
    check(card('reactive').open && opened().length === 1, 'Keyboard disclosure failed');
    check(!card('budget').open, 'Previous module remained open');
    check(card('reactive').textContent.includes('def reactive_compact'), 'Reactive source excerpt is missing');
    keyboard.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter',bubbles:true,cancelable:true}));
    await pause();
    check(opened().length === 0, 'Enter should collapse the selected module');
    prepare.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); await pause();
    document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));
    await pause();
    check(opened().length===0 && panel.hidden,'Escape did not close the nearby panel');
    legend.querySelector('summary').click(); await pause();
    check(legend.open,'The full color explanation cannot be expanded');
    legend.querySelector('summary').click(); await pause();
    check(!legend.open,'The full color explanation cannot be collapsed');

    for (const key of ['prepare','snip','micro','summary','compact']) {
      button(key).click(); await pause();
      check(card(key).open && opened().length === 1, 'Only the selected module may be open: '+key);
      check(card(key).querySelector('pre'), 'Code is missing for '+key);
      for(const step of card(key).querySelectorAll('[data-step-stage]')) {
        for(const name of step.dataset.codeFunctions.split(' ')) {
          check(card(key).querySelector('[data-function-code="'+name+'"]'),
            'Diagram references missing function '+name+' in '+key);
        }
      }
    }
    const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);
    check(ids.length === new Set(ids).size, 'Cloned diagrams introduced duplicate IDs');
    button('summary').click(); await pause();
    card('summary').querySelector('summary').click(); await pause();
    check(opened().length === 0, 'Native detail collapse did not synchronize controls');
    check(button('summary').getAttribute('aria-expanded') === 'false', 'Collapsed state is stale');

    button('prepare').click(); await pause();
    root.querySelector('[data-explorer-reset]').click(); await pause();
    check(opened().length === 0, 'Reset did not restore the author default');
    check(root.dataset.selected === '', 'Reset kept a selected module');
    check(!overview.querySelector('.is-related, .is-unrelated, .is-connection-selected'), 'Reset left arrow selection behind');
    const system=overview.querySelector('[data-overview-stage="system"]');
    system.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true})); await pause();
    check(overview.querySelector('[data-from="system"][data-to="model"]').classList.contains('is-related'),
      'A retained node cannot highlight its reference arrow');
    check(root.querySelector('[data-connection-summary]').textContent.includes('引用'),
      'Reference arrows are not distinguished from control flow');
    check(overview.querySelector('[data-from="system"][data-to="model"]').hasAttribute('marker-end'),
      'A reference connection has no directional head');
    check(panel.hidden, 'Selecting a retained node should not invent a detail panel');
    document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true})); await pause();
    check(!overview.querySelector('.is-related, .is-unrelated'), 'Escape did not clear node-only selection');
    check(shape() === originalShape, 'Reset changed the default diagram');
    check(baseline.outerHTML === originalBaseline, 'Interaction modified figure 1');
    check(document.documentElement.scrollWidth <= innerWidth, 'The page overflows its viewport');
    result.passed=true;
    result.modules=7;
    result.stableOverview=true;
  } catch(error) { result.error=error.message; }
  const report=document.createElement('pre');
  report.id='s08-test-result'; report.textContent=JSON.stringify(result);
  document.body.append(report);
});
</script>
"""


FALLBACK_PROBE = r"""
<script>
window.addEventListener('load', async () => {
  const result={passed:false};
  const check=(ok,message)=>{if(!ok)throw new Error(message);};
  const pause=()=>new Promise(resolve=>setTimeout(resolve,40));
  try {
    const root=document.querySelector('[data-diagram-explorer]');
    check(root && !root.dataset.ready,'Enhancement was not removed');
    check(root.querySelector('.diagram-explorer__toolbar').hidden,'Inactive controls should be hidden');
    const cards=[...root.querySelectorAll('[data-module-card]')];
    cards[0].querySelector('summary').click();await pause();
    check(cards[0].open,'Native module details cannot open');
    cards[1].querySelector('summary').click();await pause();
    check(cards[1].open && !cards[0].open,'Native single-group disclosure failed');
    const link=cards[1].querySelector('.diagram-explorer__source a');
    check(link && document.getElementById(link.hash.slice(1)),'Source code navigation is missing');
    check(root.querySelector('a[data-module="prepare"]').getAttribute('href').endsWith('#compact-prepare'),
      'SVG source link fallback is missing');
    check(document.documentElement.scrollWidth<=innerWidth,'Fallback page overflows');
    result.passed=true;
  } catch(error) {result.error=error.message;}
  const out=document.createElement('pre');out.id='s08-test-result';out.textContent=JSON.stringify(result);
  document.body.append(out);
});
</script>
"""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class ExplorerBehavior(unittest.TestCase):
    chapter = 's08'
    probe = PROBE
    @classmethod
    def setUpClass(cls):
        cls.chrome = shutil.which('google-chrome') or shutil.which('chromium')
        if not cls.chrome:
            raise unittest.SkipTest('Chrome is required for the browser behavior check')
        cls.temp = tempfile.TemporaryDirectory(prefix='s08-explorer-test-')
        cls.output = Path(cls.temp.name)
        subprocess.run(['hugo', '--quiet', '--destination', str(cls.output)], cwd=REPO, check=True)
        page = cls.output / f'projects/learn-claude-code/{cls.chapter}/index.html'
        text = page.read_text()
        # The test concerns local diagram behavior, not third-party math scripts.
        text = re.sub(r'<script\b[^>]*src=["\x27]https?://[^>]*>.*?</script>', '', text, flags=re.S)
        page.write_text(text.replace('</body>', cls.probe + '</body>'))
        handler = functools.partial(QuietHandler, directory=str(cls.output))
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def browser_check(self, width):
        url = f'http://127.0.0.1:{self.server.server_port}/projects/learn-claude-code/{self.chapter}/'
        run = subprocess.run([
            self.chrome, '--headless', '--no-sandbox', '--disable-gpu',
            '--disable-dev-shm-usage', '--virtual-time-budget=2500',
            f'--window-size={width},1000', '--dump-dom', url,
        ], capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
        match = re.search(r'<pre id="s08-test-result">(.*?)</pre>', run.stdout, re.S)
        self.assertIsNotNone(match, 'Browser did not report its behavior checks')
        report = json.loads(html.unescape(match[1]))
        self.assertTrue(report['passed'], report.get('error'))

    def test_desktop_interaction(self):
        self.browser_check(1180)

    def test_mobile_interaction(self):
        self.browser_check(390)

    def test_wide_desktop_interaction(self):
        self.browser_check(1600)

    def test_without_enhancement(self):
        page = self.output / 'projects/learn-claude-code/s08/index.html'
        original = page.read_text()
        fallback = original.replace(PROBE, FALLBACK_PROBE)
        fallback = re.sub(
            r'<script\b[^>]*src="[^"]*architecture-explorer[^"]*"[^>]*>.*?</script>',
            '', fallback, flags=re.S,
        )
        try:
            page.write_text(fallback)
            self.browser_check(390)
        finally:
            page.write_text(original)


if __name__ == '__main__':
    unittest.main()
