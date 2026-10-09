"""Cross-file reading UI, using synthetic pack v1 mounted only in a temp build."""
import functools,html,http.server,json,re,shutil,subprocess,tempfile,threading,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROBE=r'''<script>window.addEventListener('load',async()=>{
 const out={passed:false},check=(v,m)=>{if(!v)throw new Error(m)},pause=()=>new Promise(r=>setTimeout(r,40));
 try{
  const root=document.getElementById('reading-fixture');check(root?.dataset.readingReady==='true','Reading UI missing');
  check(document.body.textContent.includes('不是 slime'),'Fixture masquerades as real source');
  const core=document.getElementById('reading-chain'),svg=core.querySelector('svg');
  const geometry=()=>JSON.stringify([...svg.querySelectorAll('rect,path[data-route]')].map(n=>['x','y','width','height','d'].map(a=>n.getAttribute(a))));const shape=geometry();
  const storageKey=root.dataset.readingStorageKey;check(storageKey,'Progress key missing');
  check(root.querySelector('[data-file-row="other.py"]').dataset.readingState==='out-of-scope','Empty target set marked complete');
  root.querySelector('[data-reading-view="execution"]').click();await pause();
  check(geometry()===shape && localStorage.getItem(storageKey)===null,'Changing stage changed geometry or learned status');
  root.querySelector('[data-reading-view="input"]').click();await pause();
  root.querySelector('[data-reading-goal="input:one"]').click();await pause();
  const saved=localStorage.getItem(storageKey);check(saved && JSON.parse(saved).checks.length===1,'Explicit self-check not saved');
  check(root.querySelector('[data-file-row="a.py"]').dataset.readingState==='partial','Partial scope promoted to complete');
  root.querySelector('[data-reading-goal="input:two"]').click();await pause();
  check(root.querySelector('[data-file-row="a.py"]').dataset.readingState==='scope-complete','Chapter scope not aggregated');
  check(root.querySelector('[data-file-row="a.py"]').textContent.includes('Worker.hidden'),'Uncovered definition lost');
  const before=localStorage.getItem(storageKey);
  core.scrollIntoView({block:'start',behavior:'instant'});await pause();const scroll=scrollY;
  for(const [source,file,expected] of [['run-a','a.py','return task'],['run-b','b.py','return str(task)'],['caller','entry.py','return Worker().run(task)']]){
   core.querySelector('a[data-function="'+source+'"]').dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await pause();
   const code=root.querySelector('[data-function-code="'+source+'"].is-function-selected');
   check(code && code.textContent.includes(file) && code.textContent.includes(expected),'Wrong cross-file snippet '+source);
   check(code.textContent.includes('1111111111111111111111111111111111111111'),'Full revision hidden');
   check(root.dataset.readingSelectedFile===file,'Function did not select owning file');
   check(scrollY===scroll,'Source reading scrolled article');
   check(localStorage.getItem(storageKey)===before,'Source click recorded learning');
   root.querySelector('[data-explorer-reset]').click();await pause();
  }
  root.querySelector('[data-reading-file="a.py"]').click();await pause();
  check(svg.querySelector('g[data-file-path="a.py"]').classList.contains('is-reading-file-selected'),'File did not select function container');
  check(localStorage.getItem(storageKey)===before,'File selection recorded learning');
  root.querySelector('[data-explorer-reset]').click();await pause();
  check(localStorage.getItem(storageKey)===before,'View reset cleared self-check');
  core.querySelector('a[data-function="run-b"]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));await pause();
  check(root.querySelector('[data-function-code="run-b"].is-function-selected'),'Keyboard source selection failed');
  root.querySelector('[data-explorer-reset]').click();await pause();
  root.querySelector('[data-reading-clear]').click();await pause();
  check(localStorage.getItem(storageKey)===null,'Explicit clear kept saved progress');
  check(root.querySelector('[data-file-row="a.py"]').dataset.readingState==='unread','Clear kept completed scope');
  check(geometry()===shape,'Reading interactions changed source graph');
  const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);check(ids.length===new Set(ids).size,'Duplicate source IDs');
  check(document.documentElement.scrollWidth<=innerWidth,'Reading page overflow');
  out.passed=true;
 }catch(e){out.error=e.message}
 const pre=document.createElement('pre');pre.id='reading-test-result';pre.textContent=JSON.stringify(out);document.body.append(pre);
});</script>'''

def build_fixture(output):
    import tomllib
    temporary=output/'fixture-content';dst=temporary/'reviews/reading-prototype';dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(ROOT/'tests/fixtures/reading-prototype',dst)
    config=tomllib.loads((ROOT/'hugo.toml').read_text())
    config.setdefault('module',{}).setdefault('mounts',[]).extend([
        {'source':'content','target':'content'},
        {'source':str(temporary),'target':'content'},
    ])
    config_path=output/'fixture-config.json';config_path.write_text(json.dumps(config))
    return subprocess.run(['hugo','--config',str(config_path),'--destination',str(output/'public')],cwd=ROOT,capture_output=True,text=True)

class ReadingExplorer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chrome=shutil.which('google-chrome') or shutil.which('chromium')
        if not cls.chrome:raise unittest.SkipTest('Chrome required')
        cls.temp=tempfile.TemporaryDirectory(prefix='reading-ui-');cls.output=Path(cls.temp.name)
        cls.build=build_fixture(cls.output)
        if cls.build.returncode:return
        page=cls.output/'public/reviews/reading-prototype/index.html'
        cls.original=page.read_text();page.write_text(cls.original.replace('</body>',PROBE+'</body>'))
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self,*args):pass
        cls.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(cls.output/'public')))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        if cls.build.returncode==0:cls.server.shutdown();cls.server.server_close();cls.thread.join()
        cls.temp.cleanup()
    def browser(self,width):
        self.assertEqual(self.build.returncode,0,(self.build.stderr+self.build.stdout)[-2400:])
        r=subprocess.run([self.chrome,'--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
            '--virtual-time-budget=3000',f'--window-size={width},1000','--dump-dom',
            f'http://127.0.0.1:{self.server.server_port}/reviews/reading-prototype/'],capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,0,r.stderr[-500:]);m=re.search(r'<pre id="reading-test-result">(.*?)</pre>',r.stdout,re.S)
        self.assertIsNotNone(m,'No browser report');report=json.loads(html.unescape(m[1]));self.assertTrue(report['passed'],report.get('error'))
    def test_desktop(self):self.browser(1180)
    def test_mobile(self):self.browser(390)
    def test_wide(self):self.browser(1600)

if __name__=='__main__':unittest.main()
