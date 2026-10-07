"""Short lessons: curriculum coverage, quiet defaults and explicit progress."""
import functools,html,http.server,json,re,shutil,subprocess,tempfile,threading,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

PROBE=r'''<script>window.addEventListener('load',async()=>{
 const out={passed:false},check=(v,m)=>{if(!v)throw new Error(m)},pause=()=>new Promise(r=>setTimeout(r,35));
 try{
  const root=document.querySelector('[data-agent-course]');check(root?.dataset.ready==='true','Short course missing');
  const data=JSON.parse(root.querySelector('[data-agent-course-data]').textContent);
  check(data.lessons.length===17 && data.groups.length===4,'Short course incomplete');
  const map=root.querySelector('[data-agent-learned-map]');check(map.querySelectorAll('[data-module-node]').length===0,'Future modules displayed before self-check');
  check(!document.querySelector('[data-reading-config]'),'Old 25-step board on default course');
  check(!document.querySelector('[data-file-row]'),'645-file directory on default course');
  const key=root.dataset.storageKey;check(localStorage.getItem(key)===null,'Initial course progress not empty');
  const links=root.querySelectorAll('[data-lesson-link]');check(links.length===17,'Course links missing');
  links[0].dispatchEvent(new Event('focus'));check(localStorage.getItem(key)===null,'Navigation focus marked learned');
  const url=links[0].href;const page=new DOMParser().parseFromString(await(await fetch(url)).text(),'text/html');
  check(page.querySelector('[data-agent-confirm]') && page.querySelector('.agent-source-snippet'),'Lesson has no real body');
  const iframe=document.createElement('iframe');iframe.src=url;document.body.append(iframe);
  await new Promise(r=>iframe.addEventListener('load',r,{once:true}));await pause();
  let cb=iframe.contentDocument.querySelector('[data-agent-confirm]');
  check(cb && !cb.checked,'Opening lesson counted mastery');cb.click();await pause();
  check(JSON.parse(localStorage.getItem(key)).checked.includes(data.lessons[0].progressKey),'Explicit lesson self-check not stored');
  window.dispatchEvent(new Event('focus'));await pause();
  const file=root.querySelector('[data-module-progress="slime/agent/sandbox.py"]');
  check(file.querySelector('[data-module-status]').textContent.includes('部分完成'),'One lesson marked whole sandbox module complete');
  check(file.querySelector('[data-module-remaining]').textContent.includes(data.lessons[1].title),'Other sandbox lesson disappeared from remaining list');
  const learned=map.querySelectorAll('[data-module-node]');check(learned.length>=1 && learned.length<data.modules.length,'Map did not restrict to learned modules');
  const reloaded=new Promise(r=>iframe.addEventListener('load',r,{once:true}));iframe.contentWindow.location.reload();await reloaded;await pause();
  cb=iframe.contentDocument.querySelector('[data-agent-confirm]');check(cb?.checked,'Actual lesson reload lost confirmed progress');
  cb.click();await pause();window.dispatchEvent(new Event('focus'));await pause();
  check(map.querySelectorAll('[data-module-node]').length===0,'Unchecking left mastered module');
  check(document.documentElement.scrollWidth<=innerWidth,'Short course overflows');out.passed=true;
 }catch(e){out.error=e.message}
 const el=document.createElement('pre');el.id='agent-course-result';el.textContent=JSON.stringify(out);document.body.append(el);
});</script>'''

class ShortCourse(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.chrome=shutil.which('google-chrome') or shutil.which('chromium')
  if not cls.chrome:raise unittest.SkipTest('Chrome required')
  cls.temp=tempfile.TemporaryDirectory(prefix='agent-lessons-');cls.output=Path(cls.temp.name)
  r=subprocess.run(['hugo','--buildDrafts','--destination',str(cls.output)],cwd=ROOT,capture_output=True,text=True)
  cls.build=r
  if r.returncode:return
  p=cls.output/'projects/slime/index.html';s=p.read_text();p.write_text(s.replace('</body>',PROBE+'</body>'))
  class Quiet(http.server.SimpleHTTPRequestHandler):
   def log_message(self,*args):pass
  cls.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(cls.output)))
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
 @classmethod
 def tearDownClass(cls):
  if cls.build.returncode==0:cls.server.shutdown();cls.server.server_close();cls.thread.join()
  cls.temp.cleanup()
 def browser(self,width):
  self.assertEqual(self.build.returncode,0,(self.build.stdout+self.build.stderr)[-1500:])
  r=subprocess.run([self.chrome,'--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
   '--virtual-time-budget=4000',f'--window-size={width},1000','--dump-dom',
   f'http://127.0.0.1:{self.server.server_port}/projects/slime/'],capture_output=True,text=True,timeout=30)
  self.assertEqual(r.returncode,0);m=re.search(r'<pre id="agent-course-result">(.*?)</pre>',r.stdout,re.S)
  self.assertIsNotNone(m,'Browser result missing');d=json.loads(html.unescape(m[1]));self.assertTrue(d['passed'],d.get('error'))
 def test_desktop(self):self.browser(1180)
 def test_mobile(self):self.browser(390)

if __name__=='__main__':unittest.main()
