"""Latest snapshot chapter: real pack identity, source selection and scoped progress."""
import functools,hashlib,html,http.server,json,re,shutil,subprocess,tempfile,threading,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CHAPTER=ROOT/'content/projects/slime/01-agent-task'
REVISION='2f2318653f6f794dddd321eff7c9d4b7b174643f'
PROBE=r'''<script>window.addEventListener('load',async()=>{
 const out={passed:false},check=(v,m)=>{if(!v)throw new Error(m)},pause=()=>new Promise(r=>setTimeout(r,45));
 try{
  const root=document.getElementById('slime-task-reader');check(root?.dataset.readingReady==='true','Real reading page not ready');
  const p=JSON.parse(root.querySelector('[data-reading-config]').textContent);
  check(p.revision==='2f2318653f6f794dddd321eff7c9d4b7b174643f' && p.repository==='https://github.com/THUDM/slime','Wrong latest source');
  const mode=new URLSearchParams(location.search).get('record-test');
  if(mode){
   const first=p.views[0].steps[0],input=root.querySelector('[data-reading-goal="'+first.goalId+'"]');
   if(mode==='save'){input.click();await pause();check(input.checked,'Explicit record not saved');}
   else {check(input.checked && root.readingController.model.checked.size===1,'New browser did not restore self-check');root.querySelector('[data-reading-clear]').click();}
   const el=document.createElement('pre');el.id='slime-test-result';el.textContent=JSON.stringify({passed:true});document.body.append(el);return;
  }
  check(root.querySelectorAll('[data-file-row]').length===645,'Native inventory incomplete');
  check(root.querySelectorAll('[data-file-row][data-reading-state="out-of-scope"]').length===640,'Out-of-scope count wrong');
  check(root.querySelectorAll('[data-reading-goal]').length===25,'Learning objectives not preserved');
  check(root.querySelectorAll('[data-reading-view]').length===5,'Views not preserved');
  const key=root.dataset.readingStorageKey;check(localStorage.getItem(key)===null,'Initial learning state not empty');
  const goal=p.views[0].steps[0],id=goal.goalId;
  const search=root.querySelector('[data-reading-file-search]');search.value='agent/harness/common.py';search.dispatchEvent(new Event('input'));await pause();
  check([...root.querySelectorAll('[data-file-row]')].filter(n=>!n.hidden).length===1,'Native path search wrong');
  check(localStorage.getItem(key)===null,'Search recorded learning');search.value='';search.dispatchEvent(new Event('input'));
  root.querySelector('[data-reading-goal="'+id+'"]').click();await pause();
  const saved=localStorage.getItem(key);check(JSON.parse(saved).checks[0].progressKey===goal.progressKey,'Logical navigation ID used as persistent identity');
  check(root.querySelector('[data-file-row="examples/coding_agent_rl/generate.py"]').dataset.readingState==='partial','One trace step completed whole orchestrator file');
  const sourceButton=root.querySelector('[data-reading-source="'+goal.caller+'"]');
  sourceButton.scrollIntoView({block:'center',behavior:'instant'});sourceButton.focus({preventScroll:true});await pause();
  sourceButton.click();await pause();
  check(sourceButton.isConnected && root.querySelector('[data-reading-source="'+goal.caller+'"]')===sourceButton,'Real caller button lost its DOM anchor');
  const panel=root.querySelector('[data-explorer-panel]').getBoundingClientRect();
  check(panel.top>=0 && panel.left>=0 && panel.bottom<=innerHeight+1 && panel.right<=innerWidth+1,'Caller panel outside viewport');
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));await pause();
  check(document.activeElement===sourceButton,'Escape did not restore actual caller button focus');
  check(localStorage.getItem(key)===saved,'Actual caller button wrote learning');
  const core=document.getElementById('slime-task-chain');core.scrollIntoView({block:'start',behavior:'instant'});await pause();
  const before=scrollY;
  for(const rid of [goal.caller,goal.callee]){
   const ref=p.references[rid];root.openReadingSource(rid,core);await pause();
   const code=root.querySelector('[data-function-code="'+rid+'"].is-function-selected');
   check(code && code.textContent.includes(ref.path) && code.textContent.includes(ref.symbol),'Caller/callee reference mixed');
   check(code.textContent.includes(p.revision),'Source version hidden');
   const href=code.querySelector('a[href*="/blob/"]')?.getAttribute('href');
   check(href?.endsWith('#L'+ref.line+'-L'+ref.endLine),'Source range link wrong');
   check(localStorage.getItem(key)===saved,'Inspecting real source changed learning');
   root.querySelector('[data-explorer-reset]').click();await pause();
  }
  const rectangles=[...core.querySelectorAll('rect[data-source-ref]')].filter(n=>p.references[n.dataset.sourceRef]?.available).slice(0,3);
  for(const node of rectangles){
   const rid=node.dataset.sourceRef,ref=p.references[rid];
   const link=node.closest('a[data-function]') || node.parentElement.querySelector('a[data-function]');check(link?.dataset.function===rid,'Function link lost canonical definition');
   link.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await pause();
   const code=root.querySelector('[data-function-code="'+rid+'"].is-function-selected');
   check(code?.textContent.includes(ref.text.trim()),'Function click opened another source range');
   check(localStorage.getItem(key)===saved,'Canonical definition click recorded learning');
   root.querySelector('[data-explorer-reset]').click();await pause();
  }
  const previous=root.readingController.model.snapshot();
  root.readingController.model.clear();root.readingController.model.restore(JSON.parse(saved));root.readingController.sync();
  check(root.readingController.model.snapshot().checks.length===1,'Real exported self-check not restorable');
  root.querySelector('[data-reading-clear]').click();await pause();check(localStorage.getItem(key)===null,'Real learning clear failed');
  const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);check(ids.length===new Set(ids).size,'Duplicate real source IDs');
  check(document.documentElement.scrollWidth<=innerWidth,'Real chapter overflows');out.passed=true;
 }catch(e){out.error=e.message}
 const el=document.createElement('pre');el.id='slime-test-result';el.textContent=JSON.stringify(out);document.body.append(el);
});</script>'''

class LatestSource(unittest.TestCase):
    def test_pack_text_and_ranges_match_exported_blobs(self):
        p=json.loads((CHAPTER/'learning-pack.json').read_text());self.assertEqual(p['revision'],REVISION)
        self.assertEqual(sum(bool(i['inChapter']) for i in p['inventory']),5)
        for path,f in p['files'].items():self.assertEqual(hashlib.sha256(f['text'].encode()).hexdigest(),f['blobSha256'],path)
        for rid,r in p['references'].items():
            if not r['available']:self.assertTrue(r['reason']);continue
            self.assertEqual(r['revision'],REVISION)
            text=''.join(p['files'][r['path']]['text'].splitlines(keepends=True)[r['line']-1:r['endLine']])
            self.assertEqual(text,r['text'],rid)
        for v in p['views']:
            for s in v['steps']:self.assertEqual(s['depth'],'trace');self.assertTrue(s['progressKey'])

class LatestBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chrome=shutil.which('google-chrome') or shutil.which('chromium')
        if not cls.chrome:raise unittest.SkipTest('Chrome required')
        cls.temp=tempfile.TemporaryDirectory(prefix='slime-reading-');cls.output=Path(cls.temp.name)
        subprocess.run(['hugo','--quiet','--buildDrafts','--destination',str(cls.output)],cwd=ROOT,check=True)
        page=cls.output/'projects/slime/01-agent-task/index.html';s=page.read_text()
        s=re.sub(r'<script\b[^>]*src=["\x27]https?://[^>]*>.*?</script>','',s,flags=re.S)
        page.write_text(s.replace('</body>',PROBE+'</body>'))
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self,*args):pass
        cls.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(cls.output)))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.temp.cleanup()
    def browser(self,width):
        r=subprocess.run([self.chrome,'--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
            '--virtual-time-budget=3000',f'--window-size={width},1000','--dump-dom',
            f'http://127.0.0.1:{self.server.server_port}/projects/slime/01-agent-task/'],capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,0);m=re.search(r'<pre id="slime-test-result">(.*?)</pre>',r.stdout,re.S)
        self.assertIsNotNone(m,'No browser report');out=json.loads(html.unescape(m[1]));self.assertTrue(out['passed'],out.get('error'))
    def test_desktop(self):self.browser(1180)
    def test_mobile(self):self.browser(390)
    def test_wide(self):self.browser(1600)
    def test_refresh_restores_confirmed_scope(self):
        with tempfile.TemporaryDirectory(prefix='reading-browser-profile-') as profile:
            for mode in ['save','restore']:
                r=subprocess.run([self.chrome,'--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
                    '--virtual-time-budget=1500','--user-data-dir='+profile,'--dump-dom',
                    f'http://127.0.0.1:{self.server.server_port}/projects/slime/01-agent-task/?record-test={mode}'],
                    capture_output=True,text=True,timeout=30)
                self.assertEqual(r.returncode,0)
                m=re.search(r'<pre id="slime-test-result">(.*?)</pre>',r.stdout,re.S);self.assertIsNotNone(m)
                out=json.loads(html.unescape(m[1]));self.assertTrue(out['passed'],out.get('error'))

if __name__=='__main__':unittest.main()
