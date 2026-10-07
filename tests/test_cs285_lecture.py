"""Read the course map by mouse/keyboard without losing the derivation below it."""
import functools
import html
import http.server
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTE = 'courses/cs285/lecture-02'

PROBE = r'''<script>
window.addEventListener('load', () => {
  const result = {passed: false};
  const check = (value, reason) => { if (!value) throw new Error(reason); };
  try {
    const flow = document.querySelector('[data-lecture-flow]');
    check(flow?.dataset.ready === 'true', 'Compact flowchart did not initialize');
    const main = ['shift', 'cost', 'local', 'trajectory', 'analysis'];
    for (let i = 1; i < main.length; i++) {
      check(flow.querySelector('[data-from="' + main[i - 1] + '"][data-to="' + main[i] + '"]'), 'Quantification order missing: ' + main[i]);
    }
    const analysisChain = ['analysis', 'mixture', 'distance', 'split'];
    for (let i = 1; i < analysisChain.length; i++) check(flow.querySelector('[data-from="' + analysisChain[i - 1] + '"][data-to="' + analysisChain[i] + '"]'), 'Event decomposition and distribution comparison are out of order');
    check(!flow.querySelector('[data-flow-node="first-error"],[data-flow-node="remaining"]'), 'Old first-error route still bypasses the distribution comparison');
    for (const term of ['base-error', 'shift-error']) {
      check(flow.querySelector('[data-from="split"][data-to="' + term + '"]'), 'Missing separate error term ' + term);
      check(flow.querySelector('[data-from="' + term + '"][data-to="per-step"]'), 'Term does not feed the per-step bound');
    }
    check(flow.querySelector('[data-from="per-step"][data-to="bound"]'), 'Per-step bound must precede the trajectory sum');
    const chart = flow.querySelector('svg');
    const links = [...flow.querySelectorAll('[data-flow-node]')];
    for (const link of links) {
      const key = link.dataset.flowNode;
      const formula = chart.querySelector('[data-inline-formula="' + key + '"]');
      check(formula && formula.getBoundingClientRect().height > 0, 'Formula is not directly visible beside ' + key);
      check(chart.querySelector('[data-from="' + key + '"][data-to="' + key + '-formula"]'), 'Missing right arrow to ' + key + ' formula');
      const node = chart.querySelector('[data-flow-node="' + key + '"]');
      check(formula.getBoundingClientRect().left > node.getBoundingClientRect().right, 'Formula should be to the right of its node');
    }
    for (const key of ['discrete', 'gaussian', 'regression']) check(chart.querySelector('[data-inline-formula="' + key + '"]'), 'Missing action distribution formula: ' + key);
    const regions = [...chart.querySelectorAll('foreignObject')].map(node => node.getBoundingClientRect());
    for (let i = 0; i < regions.length; i++) for (let j = i + 1; j < regions.length; j++) {
      const a = regions[i], b = regions[j];
      check(a.right <= b.left || b.right <= a.left || a.bottom <= b.top || b.bottom <= a.top, 'Formula regions overlap');
    }
    check(!flow.querySelector('[data-flow-inspector]'), 'The large chapter reader should not occupy the overview');
    check(chart.querySelector('[data-inline-formula="supervised"]').getBoundingClientRect().bottom <= chart.querySelector('[data-inline-formula="bc"]').getBoundingClientRect().top, 'The two formula rows overlap');
    for (const link of links) {
      check(document.querySelector(link.getAttribute('href')), 'Node has no direct chapter route');
    }
    const beforeURL = location.href, beforeScroll = scrollY;
    links[0].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
    check(location.hash === '#formula-1', 'Click should open the original chapter directly');
    history.replaceState(null, '', beforeURL);
    window.scrollTo({top: beforeScroll, behavior: 'instant'});
    links[0].focus({preventScroll: true});
    check(chart.querySelector('[data-to="supervised-formula"].is-related'), 'Keyboard focus does not trace the formula arrow');
    links[0].blur();
    const themeTarget = links[0].querySelector('rect');
    const lightBackground = getComputedStyle(themeTarget).fill;
    const maps = [...document.querySelectorAll('[data-lecture-map]')];
    check(maps.length === 1, 'Core proof map missing');
    for (const map of maps) {
      check(map.dataset.ready === 'true', 'Course map did not initialize');
      const links = [...map.querySelectorAll('[data-lecture-node]')];
      const cards = [...map.querySelectorAll('[data-lecture-card]')];
      const svg = map.querySelector('svg');
      const geometry = svg?.getAttribute('viewBox');
      check(links.length === cards.length && links.length >= 5, 'Missing formula explanations');
      check(cards.every(card => !card.open), 'Initial overview already expanded');
      const first = links[0];
      first.dispatchEvent(new Event('pointerenter'));
      check(map.querySelector('[data-lecture-edge].is-related'), 'Hover does not trace relationships');
      check(cards.every(card => !card.open), 'Hover opened a formula card');
      first.dispatchEvent(new Event('pointerleave'));
      check(!map.querySelector('.is-related'), 'Preview stayed pinned after leaving');
      first.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
      check(cards.filter(card => card.open).length === 1, 'Click does not select one explanation');
      check(first.getAttribute('aria-expanded') === 'true', 'Selection inaccessible');
      const second = links[1];
      second.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true, cancelable: true}));
      check(cards.filter(card => card.open).length === 1 && cards[1].open, 'Keyboard selection failed');
      check(first.getAttribute('aria-expanded') === 'false', 'Previous selection was not cleared');
      if (svg) check(svg.getAttribute('viewBox') === geometry, 'Interaction changed map geometry');
      map.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
      check(cards.every(card => !card.open), 'Escape did not return to overview');
      for (const link of links) {
        link.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
        const card = map.querySelector('[data-lecture-card="' + link.dataset.lectureNode + '"]');
        check(card.open && card.textContent.includes('这一步'), 'Missing formula purpose');
        check(card.querySelector('a[href^="#formula-"]'), 'No route from map to full formula');
      }
      map.querySelector('[data-lecture-reset]').click();
      check(cards.every(card => !card.open), 'Reset did not close explanation');
    }
    for (let i = 1; i <= 20; i++) check(document.getElementById('formula-' + i), 'Lost formula ' + i);
    for (const anchor of document.querySelectorAll('.post-content a[href^="#"]')) {
      const target = decodeURIComponent(anchor.getAttribute('href').slice(1));
      check(document.getElementById(target), 'Broken reading route #' + target);
    }
    if (location.hash === '#proof-route') {
      const heading = document.getElementById('proof-route').getBoundingClientRect();
      check(heading.top >= -10 && heading.top < innerHeight, 'Proof fragment did not reach its reading position');
      const graph = document.getElementById('lecture-proof-map').getBoundingClientRect();
      check(graph.top > heading.top && graph.top < innerHeight, 'Proof map is outside the viewport after navigation');
    }
    const ids = [...document.querySelectorAll('[id]')].map(node => node.id);
    check(ids.length === new Set(ids).size, 'Duplicate IDs');
    check(document.documentElement.scrollWidth <= innerWidth, 'Course page overflows horizontally');
    document.documentElement.dataset.theme = 'dark';
    check(getComputedStyle(themeTarget).fill !== lightBackground, 'Flowchart did not adapt to dark theme');
    result.passed = true;
  } catch (error) { result.error = error.message; }
  const report = document.createElement('pre');
  report.id = 'lecture-test-result'; report.textContent = JSON.stringify(result);
  document.body.append(report);
});</script>'''


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class LectureReading(unittest.TestCase):
    route = ROUTE
    probe = PROBE
    @classmethod
    def setUpClass(cls):
        cls.chrome = shutil.which('google-chrome') or shutil.which('chromium')
        if not cls.chrome:
            raise unittest.SkipTest('Chrome is required')
        cls.temp = tempfile.TemporaryDirectory(prefix='cs285-lecture-test-')
        cls.output = Path(cls.temp.name)
        source_root = Path(os.environ.get('CS285_TEST_SOURCE', str(ROOT)))
        subprocess.run(['hugo', '--quiet', '--destination', str(cls.output), '--cacheDir', str(cls.output / 'hugo-cache')], cwd=source_root, check=True)
        page = cls.output / cls.route / 'index.html'
        if not page.exists():
            cls.temp.cleanup()
            raise AssertionError('Missing course reading page: ' + cls.route)
        source = page.read_text()
        source = re.sub(r'<script\b[^>]*src=["\x27]https?://[^>]*>.*?</script>', '', source, flags=re.S)
        page.write_text(source.replace('</body>', cls.probe + '</body>'))
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(cls.output)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def browser_check(self, width, fragment=''):
        command = [
            self.chrome, '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
            '--virtual-time-budget=2000', f'--window-size={width},1000', '--dump-dom',
        ]
        command.append(f'http://127.0.0.1:{self.server.server_port}/{self.route}/{fragment}')
        run = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr[-1500:])
        match = re.search(r'<pre id="lecture-test-result">(.*?)</pre>', run.stdout, re.S)
        self.assertIsNotNone(match, 'Browser did not report checks')
        result = json.loads(html.unescape(match[1]))
        self.assertTrue(result['passed'], result.get('error'))

    def test_desktop(self):
        self.browser_check(1180)

    def test_mobile(self):
        self.browser_check(390)

    def test_proof_fragment(self):
        self.browser_check(1600, '#proof-route')


if __name__ == '__main__':
    unittest.main()
