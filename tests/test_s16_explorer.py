"""S16 source, full-call return boundary, journal replay and chapter diagrams."""
import ast,contextlib,importlib.util,io,json,re,sys,tempfile,unittest,asyncio,copy
from pathlib import Path
import test_s08_explorer as shared

PROBE=r"""<script>window.addEventListener('load',async()=>{
 const result={passed:false};const check=(v,m)=>{if(!v)throw new Error(m)};
 const pause=()=>new Promise(r=>setTimeout(r,40));
 try{
  const root=document.getElementById('s16-workflow-explorer');check(root?.dataset.ready==='true','Workflow explorer missing');
  const baseline=document.querySelector('figure.architecture-diagram'),original=baseline.outerHTML;
  const svg=root.querySelector('svg'),panel=root.querySelector('[data-explorer-panel]'),core=document.getElementById('s16-workflow-core');
  check(svg.viewBox.baseVal.width===1200 && svg.viewBox.baseVal.height===1420,'Workflow did not expand only needed canvas height');
  const outline=document.getElementById('s16-workflow-outline');
  check(outline.querySelectorAll('#TableOfContents>ul>li').length===4,'Workflow outline hierarchy missing');
  for(const link of outline.querySelectorAll('a'))check(document.getElementById(link.hash.slice(1)),'Broken outline '+link.hash);
  const previous=new DOMParser().parseFromString(await(await fetch('/projects/learn-claude-code/s15/')).text(),'text/html').querySelector('[data-diagram-explorer] svg');
  const geometry=s=>JSON.stringify([...s.querySelectorAll('rect[data-stage],path[stroke]')].map(n=>['data-stage','x','y','width','height','d'].map(a=>n.getAttribute(a))));
  check(geometry(baseline.querySelector('svg'))===geometry(previous),'Workflow baseline differs from S15');
  check(baseline.querySelectorAll('rect[data-view="modified"]').length===3,'Only actual tool-pool interfaces should change');
  check(!baseline.querySelector('[data-stage="wf-entry"]'),'Workflow was added prematurely to baseline');
  const q=svg.querySelector('[data-overview-stage="wf-journal"] rect').getBoundingClientRect();
  svg.dispatchEvent(new PointerEvent('pointermove',{pointerType:'mouse',clientX:q.left+10,clientY:q.top+10,bubbles:true}));await pause();
  for(const [from,to] of [['wf-entry','wf-journal'],['wf-script','wf-journal'],['wf-journal','wf-script'],['wf-finish','wf-journal']])
   check(svg.querySelector('[data-from="'+from+'"][data-to="'+to+'"]').classList.contains('is-related'),'Missing journal relation '+from+' -> '+to);
  check(panel.hidden,'Journal hover opened details');svg.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'}));
  check(!svg.querySelector('[data-from^="wf-"][data-to="event-bridge"]'),'Workflow events wrongly wake parent asynchronously');
  core.scrollIntoView({block:'start',behavior:'instant'});await pause();const before=scrollY;
  const coreSvg=core.querySelector('svg');
  const coreShape=()=>JSON.stringify([...coreSvg.querySelectorAll('rect[data-stage],path[data-route]')].map(n=>['x','y','width','height','d','fill','stroke'].map(a=>n.getAttribute(a))));
  const originalCore=coreShape();
  const corePaths=[...coreSvg.querySelectorAll('path[data-route]')];
  const markers=corePaths.map(p=>p.getAttribute('marker-end'));
  const hoverCore=(stage,pointerType='mouse')=>{const b=coreSvg.querySelector('rect[data-stage="'+stage+'"]').getBoundingClientRect();coreSvg.dispatchEvent(new PointerEvent('pointermove',{pointerType,clientX:b.left+10,clientY:b.top+10,bubbles:true}));};
  const incoming=coreSvg.querySelector('[data-from="runner"][data-to="journal"]');const normalStroke=parseFloat(getComputedStyle(incoming).strokeWidth);
  hoverCore('journal');await pause();
  for(const [from,to] of [['agent','journal'],['runner','journal'],['journal','script']])
   check(coreSvg.querySelector('[data-from="'+from+'"][data-to="'+to+'"]').classList.contains('is-related'),'Core hover missed '+from+' -> '+to);
  const unrelated=coreSvg.querySelector('[data-from="launch"][data-to="runstate"]');
  check(parseFloat(getComputedStyle(incoming).strokeWidth)>normalStroke,'Core hover did not visibly thicken arrows');
  check(parseFloat(getComputedStyle(unrelated).opacity)<1,'Core hover did not fade unrelated arrows');
  const headId=incoming.getAttribute('marker-end').match(/url\(#([^)]+)\)/)[1];const head=coreSvg.querySelector('[id="'+headId+'"]');
  check(head.getAttribute('markerUnits')==='userSpaceOnUse' && Number(head.getAttribute('markerWidth'))<=12,'Core hover arrow heads grow too large');
  check(panel.hidden && root.dataset.selected==='' && scrollY===before && coreShape()===originalCore,'Core hover changed selection, article position or geometry/colors');
  hoverCore('agent','touch');await pause();check(incoming.classList.contains('is-related'),'Touch scrolling altered the mouse preview');
  coreSvg.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'}));await pause();
  check(!coreSvg.querySelector('.is-related,.is-unrelated'),'Core leave kept transient highlights');
  check(corePaths.every((p,i)=>p.getAttribute('marker-end')===markers[i]),'Core leave did not restore normal arrow heads');
  const codeLink=core.querySelector('a[data-function="key"]');codeLink.focus({preventScroll:true});await pause();
  check(incoming.classList.contains('is-related'),'Keyboard focus does not reveal core relationships');codeLink.blur();await pause();
  check(!coreSvg.querySelector('.is-related,.is-unrelated'),'Core blur kept focus preview');
  hoverCore('journal');await pause();
  core.querySelector('a[data-function="key"]').dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await pause();
  const journal=root.querySelector('[data-module-card="journal"][open]');
  check(journal && !panel.hidden && journal.querySelector('[data-function-code="key"]').classList.contains('is-function-selected'),'Cannot view exact Journal.key source');
  check(scrollY===before,'Journal source reading moved article');
  check(journal.querySelector('[data-function-code="key"]').textContent.includes('WorkflowJournal'),'Journal role missing');
  check(!journal.querySelector('[data-local-diagram] .is-related,[data-local-diagram] .is-unrelated'),'Core hover leaked into cloned reading diagram');
  const copiedSvg=journal.querySelector('[data-local-diagram] svg');
  const copiedBox=copiedSvg.querySelector('rect[data-stage="journal"]').getBoundingClientRect();
  copiedSvg.dispatchEvent(new PointerEvent('pointermove',{pointerType:'mouse',clientX:copiedBox.left+10,clientY:copiedBox.top+10,bubbles:true}));await pause();
  check(copiedSvg.querySelector('[data-from="runner"][data-to="journal"]').classList.contains('is-related'),'Copied core diagram cannot trace its own arrows');
  copiedSvg.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'}));await pause();
  check(!copiedSvg.querySelector('.is-related,.is-unrelated'),'Copied diagram kept transient preview');
  root.querySelector('[data-explorer-reset]').click();await pause();
  core.querySelector('a[data-function="call"]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));await pause();
  check(root.querySelector('[data-module-card="entry"][open] [data-function-code="call"].is-function-selected'),'Async method keyboard viewing failed');
  root.querySelector('[data-explorer-reset]').click();await pause();
  for(const key of ['entry','script','journal','finish']){
   root.querySelector('[data-module-button="'+key+'"]').click();await pause();
   const card=root.querySelector('[data-module-card="'+key+'"][open]');check(card,'Missing module '+key);
   const steps=[...card.querySelectorAll('[data-step-stage]')];check(steps.length===8,'Workflow core missing stages');
   for(const step of steps){const b=step.querySelector('rect').getBBox();
    for(const name of step.dataset.codeFunctions.split(' '))check(card.querySelector('[data-function-code="'+name+'"]'),'Missing '+name);
    for(const text of step.querySelectorAll('text[data-function]')){const p=text.getBBox();check(p.x>=b.x+3 && p.x+p.width<=b.x+b.width-3 && p.y>=b.y && p.y+p.height<=b.y+b.height,'Workflow function label overflows');}}
  }
  root.querySelector('[data-explorer-reset]').click();await pause();check(baseline.outerHTML===original,'Workflow interactions changed S15 review');
  const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);check(ids.length===new Set(ids).size,'Duplicate Workflow IDs');
  check(document.documentElement.scrollWidth<=innerWidth,'Workflow page overflows');result.passed=true;
 }catch(e){result.error=e.message}
 const p=document.createElement('pre');p.id='s08-test-result';p.textContent=JSON.stringify(result);document.body.append(p);
});</script>"""
class WorkflowBehavior(shared.ExplorerBehavior):
 chapter='s16';probe=PROBE;test_without_enhancement=None

class WorkflowSource(unittest.TestCase):
 def test_excerpts_match_local_code_and_original_diagram(self):
  path=Path('/home/fredkeira/projects/learn-claude-code/s16_workflow_runtime/code.py')
  if not path.exists():self.skipTest('Local source required')
  def normalized(node):
   node=copy.deepcopy(node)
   # Removing class indentation changes only indentation inside multiline docstrings.
   for child in ast.walk(node):
    if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)):
     doc=ast.get_docstring(child,clean=True)
     if doc is not None:child.body[0].value.value=doc
   return ast.dump(node)
  tree=ast.parse(path.read_text());expected={}
  for n in ast.walk(tree):
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):expected.setdefault(n.name,[]).append(normalized(n))
  base=shared.REPO/'content/projects/learn-claude-code/s16';found=set()
  for block in re.findall(r'```python\n(.*?)\n```',(base/'_index.md').read_text(),re.S):
   for n in ast.walk(ast.parse(block)):
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
     self.assertIn(normalized(n),expected.get(n.name,[]),f'{n.name} differs from source');found.add(n.name)
  roles=json.loads((base/'function-roles.json').read_text())
  self.assertTrue(set(roles)<=found,f'Missing source functions: {set(roles)-found}')
  original=path.parent/'images/workflow-runtime-overview.svg'
  self.assertEqual(original.read_bytes(),(shared.REPO/'static/examples/s16-repo/workflow-runtime-overview.svg').read_bytes())
  core=(base/'images/workflow-core.svg').read_text()
  self.assertNotIn('data-function="run_workflow_sync"',core)
  self.assertNotIn('data-function="run_workflow"',core)

class WorkflowRuntime(unittest.TestCase):
 def setUp(self):
  path=Path('/home/fredkeira/projects/learn-claude-code/s16_workflow_runtime/code.py')
  if not path.exists():self.skipTest('Local source required')
  spec=importlib.util.spec_from_file_location('workflow_blog_check',path)
  self.module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=self.module;spec.loader.exec_module(self.module)
  self.temp=tempfile.TemporaryDirectory(prefix='workflow-blog-');self.module.STORE=Path(self.temp.name)
  self.stdout=contextlib.redirect_stdout(io.StringIO());self.output=self.stdout.__enter__()
 def tearDown(self):self.stdout.__exit__(None,None,None);self.temp.cleanup()

 def test_final_result_and_resume_cache_use_one_run_boundary(self):
  m=self.module;calls=[];Original=m.MockAgentRunner
  class CountingRunner(Original):
   def run(self,prompt,schema=None,label=None):calls.append(label);return super().run(prompt,schema,label)
  m.RUNNER_FACTORY=CountingRunner
  first=json.loads(m.run_workflow_sync(name='review-changes',args={'changes':m.DEMO_CHANGES}))
  self.assertEqual(first['launched']['status'],'async_launched');self.assertEqual(first['task']['status'],'completed')
  self.assertTrue(calls);self.assertGreater(first['task']['usage']['agents'],0)
  events=self.output.getvalue();self.assertLess(events.index('async_launched'),events.index('task_notification'))
  run_id=first['task']['runId'];before=len(calls)
  resumed=json.loads(m.run_workflow_sync(name='review-changes',resume_from_run_id=run_id))
  self.assertEqual(len(calls),before);self.assertEqual(resumed['task']['usage'],{'agents':0,'tokens':0})
  self.assertEqual(resumed['result'],first['result']);self.assertEqual(resumed['task']['runId'],run_id)
  for suffix in ['.json','.output.json','.journal.jsonl','.lock']:self.assertTrue((m.STORE/(run_id+suffix)).exists())

 def test_resume_rejects_changed_args_before_artifact_overwrite(self):
  m=self.module
  result=asyncio.run(m.run_workflow('review-changes',{'changes':'sample'}));run_id=result['task']['runId']
  saved=(m.STORE/(run_id+'.output.json')).read_bytes()
  answer=m.run_workflow_sync(name='review-changes',args={'changes':'new input'},resume_from_run_id=run_id)
  self.assertIn('resume args do not match',answer)
  self.assertEqual(saved,(m.STORE/(run_id+'.output.json')).read_bytes())

if __name__=='__main__':unittest.main()
