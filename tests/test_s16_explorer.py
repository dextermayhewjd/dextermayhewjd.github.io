"""S16 source, full-call return boundary, journal replay and chapter diagrams."""
import ast,contextlib,importlib.util,io,json,re,sys,tempfile,unittest,asyncio,copy
from pathlib import Path
import test_s08_explorer as shared

PROBE=r"""<script>window.addEventListener('load',async()=>{
 const result={passed:false},check=(v,m)=>{if(!v)throw new Error(m)};
 try{
  const root=document.getElementById('s16-overview-explorer');check(root?.dataset.ready==='true','Workflow explorer missing');
  const outline=document.getElementById('s16-workflow-outline');
  const headings=[...document.querySelectorAll('.post-content > h2[id]')];
  const sections=headings.filter(heading=>/^\d+\./.test(heading.textContent));
  const links=[...outline.querySelectorAll('#TableOfContents>ul>li>a')];
  check(sections.length===23&&headings.length===25&&links.length===25,'Expected the opening map and all 23 progressive sections');
  check(links.every((link,index)=>link.hash==='#'+headings[index].id),'Outline order differs from the lesson');
  for(const link of outline.querySelectorAll('a'))check(document.getElementById(link.hash.slice(1)),'Broken outline '+link.hash);
  for(const id of ['workflow-first-call','workflow-agent','workflow-journal','workflow-adapter','workflow-resume','workflow-overview'])check(document.getElementById(id),'Missing stable anchor '+id);
  const library=document.querySelector('[data-function-source-library]');
  check(library?.hidden&&library.dataset.sourceRevision==='ce8f9f186058939da54c9d6fead78dfb5d0fd6c3','Missing pinned source library');
  const figures=[...document.querySelectorAll('figure.architecture-diagram')].filter(f=>!f.closest('[data-workflow-detail-template]'));
  check(figures.length===5,'Expected four local SVGs and the closing overview');
  for(const figure of figures)check(figure.querySelector('figcaption').textContent.trim(),'Missing adjacent figure explanation');
  check(sections[0].textContent.includes('ctx.agent()'),'First section no longer starts with a single model call');
  check(sections[5].textContent.includes('ctx.parallel()')&&sections[6].textContent.includes('ctx.pipeline()'),'Concurrency progression changed');
  check(sections[11].textContent.includes('journal')&&sections[13].textContent.includes('resume'),'Recovery progression changed');
  check(sections[22].id==='workflow-overview','Overall diagram moved out of the closing section');
  check(!document.querySelector('#s16-workflow-explorer'),'Old article content is still present');
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
  pack=json.loads((base/'workflow-sources.json').read_text())
  for record in pack['functions']:
   n=ast.parse(record['code']).body[0]
   self.assertIn(normalized(n),expected.get(n.name,[]),f'{record["symbol"]} differs from source');found.add(n.name)
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
