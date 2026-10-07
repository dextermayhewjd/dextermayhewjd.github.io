"""One approved launch sample: stable context, navigation and manual understanding."""
import functools,html,http.server,json,re,shutil,subprocess,tempfile,threading,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
READER_PROBE=r'''<script>window.addEventListener('load',async()=>{
 const out={passed:false},check=(v,m)=>{if(!v)throw new Error(m)},pause=()=>new Promise(r=>setTimeout(r,35));
 try{
  const root=document.querySelector('[data-agent-flow]');check(root?.dataset.ready==='true','Launch sample missing');
  const data=JSON.parse(root.querySelector('[data-flow-data]').textContent),byId=new Map(data.nodes.map(n=>[n.id,n]));
  const mode=new URLSearchParams(location.search).get('record-test');
  if(mode){const cb=root.querySelector('[data-flow-current="run_agent"] [data-flow-understood]');
   if(mode==='save'){cb.click();await pause();check(cb.checked,'Manual mark not saved');}
   else{check(cb.checked,'New page load did not restore explanation mark');check(root.dataset.currentNode==='run_agent','Browsing focus was persisted');cb.click();}
   const result=document.createElement('pre');result.id='flow-result';result.textContent=JSON.stringify({passed:true});document.body.append(result);return;
  }
  const skeleton=root.querySelector('[data-business-skeleton]'),initial=skeleton.innerHTML;
  check(root.dataset.currentNode==='run_agent','Wrong default function');
  check(skeleton.querySelectorAll('[data-business-stage]').length===5,'Business context missing');
  const key=root.dataset.storageKey;check(localStorage.getItem(key)===null,'Opening marked understanding');
  const tree=root.querySelector('[data-flow-tree]'),treeHTML=tree.querySelector('[data-function-id="launch"]');
  check(tree.querySelector('[data-flow-folder="slime/agent/harness"]').closest('[data-flow-folder="slime/agent"]'),'Harness folder not nested under agent');
  check(tree.querySelector('[data-flow-folder="slime/agent"]').closest('[data-flow-folder="slime"]'),'Agent folder not nested under slime');
  check(parseFloat(getComputedStyle(root.querySelector('[data-flow-current="run_agent"] .flow-code code')).fontSize)>=13,'Source code too small');
  const inputs=root.querySelector('[data-flow-current="run_agent"] [data-flow-understood]');inputs.click();await pause();
  const saved=localStorage.getItem(key);check(JSON.parse(saved).understood.includes(byId.get('run_agent').progressKey),'Manual understanding not stored');
  const button=root.querySelector('[data-flow-current="run_agent"] [data-flow-target="exec_and_wait"]');button.click();await pause();
  check(root.dataset.currentNode==='exec_and_wait','Downstream click did not change function');
  const heading=root.querySelector('[data-flow-current="exec_and_wait"] h2'),context=root.querySelector('.flow-context').getBoundingClientRect();
  check(heading.getBoundingClientRect().top>=context.bottom && heading.getBoundingClientRect().top<context.bottom+90,'New function heading not readable below sticky context');
  check(document.activeElement===heading,'New function heading did not receive focus');
  check(root.querySelector('[data-flow-path]').textContent.includes('sandbox.py'),'Path did not change');
  check(tree.querySelector('[data-function-id="exec_and_wait"]').getAttribute('aria-current')==='location','Tree did not highlight function');
  check(tree.querySelector('[data-flow-file="slime/agent/sandbox.py"]').classList.contains('is-current-file'),'Tree did not highlight sandbox file');
  check(tree.querySelector('[data-flow-folder="slime/agent"]').classList.contains('is-current-folder'),'Tree did not highlight agent folder');
  check(tree.querySelector('[data-flow-folder="slime"]').classList.contains('is-current-folder'),'Tree did not highlight all path ancestors');
  check(localStorage.getItem(key)===saved,'Navigation changed understanding');
  root.querySelector('[data-flow-back]').click();await pause();check(root.dataset.currentNode==='run_agent','Back did not restore focus');
  const toggle=tree.querySelector('.flow-tree-toggle');if(!toggle.open){toggle.querySelector('summary').click();await pause();check(toggle.open,'Mobile tree did not expand');}
  const launchFile=treeHTML.closest('[data-flow-file]');if(!launchFile.open)launchFile.querySelector('summary').click();
  check(treeHTML.getBoundingClientRect().height>0,'Tree function is hidden');treeHTML.click();await pause();check(root.dataset.currentNode==='launch','Tree click did not change function');
  check(tree.querySelector('[data-function-id="launch"]')===treeHTML,'Tree DOM was rebuilt');
  check(root.querySelector('[data-flow-path]').textContent.includes('codex.py'),'Tree navigation path wrong');
  check(!root.querySelector('[data-flow-current="launch"] [data-flow-understood]').checked,'Looked-at function marked understood');
  check(tree.querySelector('[data-function-id="launch"] [data-function-status]').textContent.includes('看过'),'Browsing status not separate');
  root.querySelector('[data-flow-entry]').click();await pause();check(root.dataset.currentNode===data.entryNodeId,'Cannot find chain entry');
  root.querySelector('[data-flow-back]').click();await pause();check(root.dataset.currentNode==='launch','Entry back failed');
  check(skeleton.innerHTML===initial,'Business skeleton changed during browsing');
  const run=tree.querySelector('[data-function-id="run_agent"]');run.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));run.click();await pause();
  root.querySelector('[data-flow-current="run_agent"] [data-flow-understood]').click();await pause();
  check(JSON.parse(localStorage.getItem(key)).understood.length===0,'Unchecking did not revoke manual record');
  check(document.documentElement.scrollWidth<=innerWidth,'Launch page overflows');
  out.viewport=innerWidth;out.passed=true;
 }catch(e){out.error=e.message}
 const p=document.createElement('pre');p.id='flow-result';p.textContent=JSON.stringify(out);document.body.append(p);
});</script>'''
PROBE=r'''<script>window.addEventListener('load',async()=>{
 const out={passed:false},check=(v,m)=>{if(!v)throw new Error(m)},pause=()=>new Promise(r=>setTimeout(r,35));
 try{
  const root=document.querySelector('[data-agent-flow]');check(root?.dataset.ready==='true','Model page missing');
  const data=JSON.parse(root.querySelector('[data-flow-data]').textContent),steps=new Map(data.mentalModel.steps.map(s=>[s.id,s]));
  const mode=new URLSearchParams(location.search).get('record-test');
  if(mode){
   root.querySelector('[data-model-source="context"]').click();await pause();
   const node=steps.get('context').nodeId,cb=root.querySelector('[data-flow-current="'+node+'"] [data-flow-understood]');
   if(mode==='save'){cb.click();await pause();check(cb.checked,'Manual record not saved');}
   else{check(cb.checked,'Manual explanation not restored');check(root.dataset.currentStep==='context','Graph visit restored wrong path');cb.click();}
   const p=document.createElement('pre');p.id='flow-result';p.textContent=JSON.stringify({passed:true});document.body.append(p);return;
  }
  check(root.dataset.view==='model','Initial page entered source automatically');
  const layer=root.querySelector('[data-model-layer="'+data.mentalModel.rootId+'"]');
  check(!layer.hidden && layer.querySelectorAll('[data-model-step]').length===8,'Root diagram not 0–7');
  check(layer.querySelectorAll('svg path[data-model-link]').length>=7,'Root diagram has no real arrows');
  check([...root.querySelectorAll('[data-flow-current]')].every(p=>p.hidden),'Long source visible on initial graph');
  const key=root.dataset.storageKey;check(localStorage.getItem(key)===null,'Graph opening marked understanding');
  root.querySelector('[data-model-step="harness"]').click();await pause();
  const h=root.querySelector('[data-model-layer="harness"]');check(!h.hidden && h.querySelectorAll('[data-model-step]').length===3,'Harness children missing');
  check(h.textContent.includes('3.1')&&h.textContent.includes('3.2')&&h.textContent.includes('3.3'),'Numbered parent/child frame missing');
  root.querySelector('[data-model-step="harness-user"]').click();await pause();
  check(root.dataset.currentStep==='harness-user' && root.querySelector('[data-model-trail]').textContent.includes('3.1'),'Model position lost');
  root.querySelector('[data-model-layer="harness-user"] [data-model-open-source]').click();await pause();
  check(root.dataset.view==='source' && root.dataset.currentNode==='ensure_user' && root.dataset.currentStep==='harness-user','Source changed 3.1 into 2.1');
  check(root.querySelector('[data-model-trail]').textContent.includes('3.1'),'Full numbered trail not retained');
  root.querySelector('[data-flow-map-return]').click();await pause();check(!root.querySelector('[data-model-layer="harness-user"]').hidden,'Return to graph lost layer');
  root.querySelector('[data-flow-map-root]').click();await pause();root.querySelector('[data-model-step="workspace"]').click();await pause();
  root.querySelector('[data-model-step="workspace-user"]').click();await pause();
  root.querySelector('[data-model-layer="workspace-user"] [data-model-open-source]').click();await pause();
  check(root.dataset.currentNode==='ensure_user' && root.dataset.currentStep==='workspace-user' && root.querySelector('[data-model-trail]').textContent.includes('2.1'),'Repeated function merged distinct flow positions');
  check(localStorage.getItem(key)===null,'Model/source navigation recorded explanation');
  root.querySelector('[data-flow-map-root]').click();await pause();root.querySelector('[data-model-step="result"]').click();await pause();
  const choice=root.querySelector('[data-model-layer="result"]');check(choice.dataset.layout==='choice','Result not a choice');
  const arrows=[...choice.querySelectorAll('svg path[data-model-link]')];check(arrows.length===2 && arrows.every(p=>p.dataset.kind==='branch'),'Train/eval presented in serial');
  check(choice.textContent.includes('evaluation=False') && choice.textContent.includes('evaluation=True'),'Choice conditions missing');
  check(document.documentElement.scrollWidth<=innerWidth,'Model page overflows');
  out.viewport=innerWidth;out.passed=true;
 }catch(e){out.error=e.message}
 const p=document.createElement('pre');p.id='flow-result';p.textContent=JSON.stringify(out);document.body.append(p);
});</script>'''
class LaunchFlow(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.chrome=shutil.which('google-chrome') or shutil.which('chromium')
  if not cls.chrome:raise unittest.SkipTest('Chrome required')
  cls.temp=tempfile.TemporaryDirectory(prefix='launch-flow-');cls.output=Path(cls.temp.name)
  import tomllib
  config=tomllib.loads((ROOT/'hugo.toml').read_text())
  config['ignoreFiles']=config.get('ignoreFiles',[])+[r'(^|/)courses/cs285/']
  configPath=cls.output/'isolated-flow-config.json';configPath.write_text(json.dumps(config))
  cls.build=subprocess.run(['hugo','--buildDrafts','--config',str(configPath),'--destination',str(cls.output)],cwd=ROOT,capture_output=True,text=True)
  if cls.build.returncode:return
  p=cls.output/'projects/slime/agent-launch/index.html';p.write_text(p.read_text().replace('</body>',PROBE+'</body>'))
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
  target=f'http://127.0.0.1:{self.server.server_port}/projects/slime/agent-launch/'
  if width==390:
   wrapper='''<html><body style="margin:0"><iframe id="mobile" style="width:390px;height:1000px;border:0" src="/projects/slime/agent-launch/"></iframe><script>
   const timer=setInterval(()=>{const result=document.getElementById('mobile').contentDocument?.getElementById('flow-result');if(result){clearInterval(timer);const out=document.createElement('pre');out.id='flow-result';out.textContent=result.textContent;document.body.append(out);}},30);
   </script></body></html>'''
   (self.output/'narrow-flow.html').write_text(wrapper);target=f'http://127.0.0.1:{self.server.server_port}/narrow-flow.html'
  r=subprocess.run([self.chrome,'--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
   '--virtual-time-budget=4000',f'--window-size={1180 if width==390 else width},1000','--dump-dom',target],capture_output=True,text=True,timeout=30)
  self.assertEqual(r.returncode,0);m=re.search(r'<pre id="flow-result">(.*?)</pre>',r.stdout,re.S)
  self.assertIsNotNone(m,'Browser result missing');d=json.loads(html.unescape(m[1]));self.assertTrue(d['passed'],d.get('error'))
  self.assertEqual(d['viewport'],width,'Viewport does not match reported width')
 def test_desktop(self):self.browser(1180)
 def test_mobile(self):self.browser(390)
 def test_reload_restores_only_manual_explanation(self):
  self.assertEqual(self.build.returncode,0)
  with tempfile.TemporaryDirectory(prefix='launch-profile-') as profile:
   for mode in ['save','restore']:
    r=subprocess.run([self.chrome,'--headless','--no-sandbox','--disable-gpu','--virtual-time-budget=1500',
     '--user-data-dir='+profile,'--dump-dom',f'http://127.0.0.1:{self.server.server_port}/projects/slime/agent-launch/?record-test={mode}'],capture_output=True,text=True,timeout=30)
    self.assertEqual(r.returncode,0);m=re.search(r'<pre id="flow-result">(.*?)</pre>',r.stdout,re.S);self.assertIsNotNone(m)
    d=json.loads(html.unescape(m[1]));self.assertTrue(d['passed'],d.get('error'))
if __name__=='__main__':unittest.main()
