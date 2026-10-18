"""Exercise active-chapter following in Chrome with real page navigation."""

import functools
import http.server
import json
import os
from pathlib import Path
import queue
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIRST = 'projects/python-async-concurrency/20-running-loop/index.html'
SECOND = 'projects/python-async-concurrency/20-future-result/index.html'
NEXT_URL = '/projects/python-async-concurrency/20-future-result/'
PRELUDE = """
const check = (condition, message) => { if (!condition) throw new Error(message); };
const settled = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
const visible = (container, link) => {
  const box = container.getBoundingClientRect(), item = link.getBoundingClientRect();
  return item.top >= box.top - 1 && item.bottom <= box.bottom + 1;
};
const report = result => {
  fetch('/__project_nav_result', {method: 'POST', body: JSON.stringify(result)});
};
"""


def probe(body):
    return '<script>window.addEventListener("load", async () => {' + PRELUDE + """
try {
  await settled();
""" + body + """
} catch (error) { report({passed: false, error: error.message}); }
});</script>
"""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        if self.path != '/__project_nav_result':
            self.send_error(404)
            return
        report = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.reports.put(report)
        self.send_response(204)
        self.end_headers()


class ProjectNavFollowing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chrome = shutil.which('google-chrome') or shutil.which('chromium')
        if not cls.chrome:
            raise unittest.SkipTest('Chrome is required for sidebar behavior checks')
        cls.temp = tempfile.TemporaryDirectory(prefix='project-nav-follow-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output = Path(cls.temp.name)
        subprocess.run(['hugo', '--quiet', '--destination', str(cls.output),
                        '--cacheDir', str(cls.output / 'cache')], cwd=ROOT, check=True)
        cls.original = {}
        for relative in (FIRST, SECOND):
            page = cls.output / relative
            text = re.sub(r'<script\b[^>]*src=["\x27]https?://[^>]*>.*?</script>', '',
                          page.read_text(), flags=re.S)
            cls.original[relative] = text
        handler = functools.partial(QuietHandler, directory=str(cls.output))
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        cls.server.reports = queue.Queue()
        cls.addClassCleanup(cls.server.server_close)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.addClassCleanup(cls.stop_server)

    @classmethod
    def stop_server(cls):
        cls.server.shutdown()
        cls.thread.join()

    def browser_check(self, body, width=1280, second=None):
        for relative in (FIRST, SECOND):
            injected = body if relative == FIRST else second
            page = self.output / relative
            page.write_text(self.original[relative].replace('</body>',
                            (probe(injected) if injected else '') + '</body>'))
        with tempfile.TemporaryDirectory(prefix='project-nav-chrome-', ignore_cleanup_errors=True) as profile:
            with tempfile.TemporaryFile() as errors:
                browser = subprocess.Popen([
                    self.chrome, '--headless=new', '--no-sandbox', '--disable-gpu',
                    '--disable-dev-shm-usage', '--no-first-run', '--remote-debugging-port=0',
                    f'--user-data-dir={profile}', f'--window-size={width},900',
                    f'http://127.0.0.1:{self.server.server_port}/' + FIRST.removesuffix('index.html'),
                ], stdout=subprocess.DEVNULL, stderr=errors, start_new_session=True)
                try:
                    # Real animation frames matter: virtual-time dump-dom can finish
                    # before the menu's frame callback, despite advancing its timers.
                    result = self.server.reports.get(timeout=20)
                except queue.Empty:
                    errors.seek(0)
                    self.fail('Browser did not report: ' + errors.read().decode(errors='replace')[-2000:])
                finally:
                    try:
                        os.killpg(browser.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    try:
                        browser.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        browser.kill()
                        browser.wait()
        self.assertTrue(result['passed'], result.get('error'))

    def test_current_chapter_is_visible_after_a_direct_desktop_visit(self):
        self.browser_check("""
const sidebar = document.querySelector('.project-nav');
const current = sidebar.querySelector('.project-nav__desktop [aria-current="page"]');
check(sidebar.scrollHeight > sidebar.clientHeight, 'Test needs a scrollable sidebar');
check(visible(sidebar, current), 'Current chapter is below the visible sidebar');
check(scrollY === 0, 'Revealing the chapter moved the article');
check(document.activeElement === document.body, 'Revealing the chapter stole keyboard focus');
report({passed: true});
""")

    def test_teaching_links_are_visible_after_unit_38(self):
        self.browser_check("""
const desktop = document.querySelector('.project-nav__desktop');
const links = [...desktop.querySelectorAll('a.project-nav__link')];
const unit38 = links.find(link => link.pathname.endsWith('/38-popen-communicate/'));
const soon = links.find(link => link.pathname.endsWith('/loop-call-soon/'));
const later = links.find(link => link.pathname.endsWith('/loop-call-later/'));
check(unit38 && soon && later, 'Missing unit 38 or callback comparison links');
check(links.indexOf(soon) > links.indexOf(unit38), 'call_soon must follow unit 38');
check(links.indexOf(later) > links.indexOf(soon), 'call_later comparison must follow call_soon');
check(soon.getClientRects().length && later.getClientRects().length,
      'Callback teaching pages are hidden inside a collapsed group');
check(!soon.closest('.project-nav__comparisons') && !later.closest('.project-nav__comparisons'),
      'Full teaching pages must be outside the relationship summary group');
const summary = links.find(link => link.pathname.endsWith('/comparisons/call-soon-vs-call-later/'));
check(summary && summary.closest('.project-nav__comparisons'),
      'Relationship summary must remain inside the comparison group');
const folder = summary.closest('.project-nav__comparisons').querySelector(':scope > details');
check(folder && !folder.open, 'Relationship summaries must form a collapsible folder');
folder.querySelector('summary').click();
await settled();
check(folder.open && summary.getClientRects().length,
      'Opening the summary folder must reveal its children');
report({passed: true});
""")

    def test_switching_chapters_preserves_the_sidebar_position(self):
        self.browser_check("""
const sidebar = document.querySelector('.project-nav');
const current = sidebar.querySelector('.project-nav__desktop [aria-current="page"]');
check(visible(sidebar, current), 'Initial chapter is not visible');
const extra = sidebar.querySelector('.project-nav__desktop [data-lesson-group="33"]');
extra.open = true;
await settled();
sidebar.scrollTop += 40;
sessionStorage.setItem('nav-test-before', String(sidebar.scrollTop));
[...sidebar.querySelectorAll('.project-nav__desktop a')]
  .find(link => link.getAttribute('href') === '""" + NEXT_URL + """').click();
""", second="""
const sidebar = document.querySelector('.project-nav');
const current = sidebar.querySelector('.project-nav__desktop [aria-current="page"]');
check(current.getAttribute('href') === '""" + NEXT_URL + """', 'Did not navigate to the next chapter');
check(visible(sidebar, current), 'Next chapter is not visible');
check(sidebar.querySelector('.project-nav__desktop [data-lesson-group="33"]').open,
      'Previously expanded chapter group was collapsed');
const before = Number(sessionStorage.getItem('nav-test-before'));
check(before > 0 && Math.abs(sidebar.scrollTop - before) < 5, 'Sidebar reset instead of preserving its position');
check(scrollY === 0, 'Restoring the sidebar scrolled the article');
report({passed: true});
""")

    def test_mobile_menu_reveals_the_current_chapter_when_opened(self):
        self.browser_check("""
const menu = document.querySelector('.project-nav__mobile');
const summary = menu.querySelector('summary');
const content = menu.querySelector('.project-nav__mobile-content');
check(getComputedStyle(menu).display !== 'none', 'Expected mobile navigation');
check(!menu.open, 'Mobile menu should stay closed until requested');
summary.focus();
summary.click();
await settled();
const current = content.querySelector('[aria-current="page"]');
check(content.scrollHeight > content.clientHeight, 'Mobile menu is not bounded and scrollable');
check(visible(content, current), 'Current chapter is outside the mobile menu viewport');
check(document.activeElement === summary, 'Opening the menu stole summary focus');
check(document.documentElement.scrollWidth <= innerWidth + 1, 'Mobile page overflows horizontally');
report({passed: true});
""", width=390)

    def test_blocked_storage_does_not_prevent_chapter_following(self):
        # Install before the defer script executes, as happens when browser storage is denied.
        guard = "<script>Storage.prototype.getItem = Storage.prototype.setItem = () => { throw new Error('denied'); };</script>"
        original = self.original[FIRST]
        self.original[FIRST] = original.replace('<head>', '<head>' + guard)
        try:
            self.browser_check("""
const sidebar = document.querySelector('.project-nav');
const current = sidebar.querySelector('.project-nav__desktop [aria-current="page"]');
check(visible(sidebar, current), 'Blocked storage prevented current-chapter following');
report({passed: true});
""")
        finally:
            self.original[FIRST] = original


if __name__ == '__main__':
    unittest.main()
