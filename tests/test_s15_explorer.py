"""S15 local-source assembly, old/current/core diagrams, and actual loop inputs."""
import ast,contextlib,importlib.util,io,json,re,tempfile,types,unittest
from pathlib import Path
import test_s08_explorer as shared

PROBE=r"""<script>window.addEventListener('load',async()=>{
 const result={passed:false};const check=(v,m)=>{if(!v)throw new Error(m)};
 const pause=()=>new Promise(r=>setTimeout(r,40));
 try{
  const root=document.getElementById('s15-harness-explorer');check(root?.dataset.ready==='true','Harness explorer missing');
  const baseline=document.querySelector('figure.architecture-diagram'),original=baseline.outerHTML;
  const svg=root.querySelector('svg'),panel=root.querySelector('[data-explorer-panel]'),core=document.getElementById('s15-harness-core');
  check(svg.viewBox.baseVal.width===1200,'Harness overview not wide');
  const outline=document.getElementById('s15-chapter-outline');
  check(outline.querySelectorAll('#TableOfContents>ul>li').length===4,'Harness outline hierarchy missing');
  for(const link of outline.querySelectorAll('a'))check(document.getElementById(link.hash.slice(1)),'Broken outline '+link.hash);
  const previous=new DOMParser().parseFromString(await(await fetch('/projects/learn-claude-code/s14/')).text(),'text/html').querySelector('[data-diagram-explorer] svg');
  const geometry=s=>JSON.stringify([...s.querySelectorAll('rect[data-stage],path[stroke]')].map(n=>['data-stage','x','y','width','height','d'].map(a=>n.getAttribute(a))));
  check(geometry(baseline.querySelector('svg'))===geometry(previous),'Harness baseline differs from S14');
  check(baseline.querySelectorAll('rect[data-view="folded"]').length===4,'MCP fold cues missing');
  check(baseline.querySelectorAll('rect[data-view="modified"]').length===13,'Harness change cues missing');
  check(!svg.querySelector('[data-stage="mcp-call"]') && svg.querySelector('[data-stage="pool"]'),'MCP did not fold into actual pool');
  check(!svg.querySelector('[data-stage="recovery"]'),'Error recovery should stay out of this scope');
  check(!svg.querySelector('[data-from="stop-event"][data-to="history"]'),'Unimplemented Stop-feedback path retained');
  check(svg.querySelector('[data-from="prepare"][data-to="memory-recall"]'),'Memory is not refreshed per loop');
  const q=svg.querySelector('[data-overview-stage="event-bridge"] rect').getBoundingClientRect();
  svg.dispatchEvent(new PointerEvent('pointermove',{pointerType:'mouse',clientX:q.left+10,clientY:q.top+10,bubbles:true}));await pause();
  for(const [from,to] of [['background-collect','event-bridge'],['cron-interface','event-bridge'],['team-interface','event-bridge'],['event-bridge','history']])
   check(svg.querySelector('[data-from="'+from+'"][data-to="'+to+'"]').classList.contains('is-related'),'Missing event relation '+from+' -> '+to);
  check(panel.hidden,'Event hover opened details');svg.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'}));
  core.scrollIntoView({block:'start',behavior:'instant'});await pause();const before=scrollY;
  core.querySelector('a[data-function="assemble_tool_pool"]').dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await pause();
  const assembly=root.querySelector('[data-module-card="pool"][open]');
  check(assembly && !panel.hidden && assembly.querySelector('[data-function-code="assemble_tool_pool"]').classList.contains('is-function-selected'),'Cannot view exact assembly source');
  check(scrollY===before,'Harness code reading moved article');
  root.querySelector('[data-explorer-reset]').click();await pause();
  core.querySelector('a[data-function="agent_loop"]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));await pause();
  check(root.querySelector('[data-module-card="events"][open] [data-function-code="agent_loop"].is-function-selected'),'Collapsed full loop not available in reader');
  root.querySelector('[data-explorer-reset]').click();await pause();
  svg.querySelector('a[data-module="dispatch"]').dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await pause();
  check(root.querySelector('[data-module-card="dispatch"][open]'),'PreToolUse cannot open actual dispatch explanation');
  root.querySelector('[data-explorer-reset]').click();await pause();
  for(const key of ['assembly','pool','events','dispatch','background']){
   root.querySelector('[data-module-button="'+key+'"]').click();await pause();
   const card=root.querySelector('[data-module-card="'+key+'"][open]');check(card,'Missing module '+key);
   const steps=[...card.querySelectorAll('[data-step-stage]')];check(steps.length===8,'Missing integration stages');
   for(const step of steps){const b=step.querySelector('rect').getBBox();
    for(const name of step.dataset.codeFunctions.split(' '))check(card.querySelector('[data-function-code="'+name+'"]'),'Missing '+name);
    for(const text of step.querySelectorAll('text[data-function]')){const p=text.getBBox();check(p.x>=b.x+3 && p.x+p.width<=b.x+b.width-3 && p.y>=b.y && p.y+p.height<=b.y+b.height,'Harness function label overflows');}}
  }
  root.querySelector('[data-explorer-reset]').click();await pause();
  check(baseline.outerHTML===original,'Harness interactions changed S14 review');
  const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);check(ids.length===new Set(ids).size,'Duplicate Harness IDs');
  check(document.documentElement.scrollWidth<=innerWidth,'Harness page overflows');result.passed=true;
 }catch(e){result.error=e.message}
 const p=document.createElement('pre');p.id='s08-test-result';p.textContent=JSON.stringify(result);document.body.append(p);
});</script>"""

class HarnessBehavior(shared.ExplorerBehavior):
 chapter='s15';probe=PROBE;test_without_enhancement=None

class HarnessSource(unittest.TestCase):
 def test_excerpts_and_tool_count_match_local_source(self):
  source=Path('/home/fredkeira/projects/learn-claude-code/s15_integrated_harness/code.py')
  if not source.exists():self.skipTest('Local source required')
  tree=ast.parse(source.read_text());expected={}
  for n in ast.walk(tree):
   if isinstance(n,ast.FunctionDef):expected.setdefault(n.name,[]).append(ast.dump(n))
  base=shared.REPO/'content/projects/learn-claude-code/s15';found=set()
  for block in re.findall(r'```python\n(.*?)\n```',(base/'_index.md').read_text(),re.S):
   for n in ast.walk(ast.parse(block)):
    if isinstance(n,ast.FunctionDef):self.assertIn(ast.dump(n),expected.get(n.name,[]),f'{n.name} differs from source');found.add(n.name)
  roles=json.loads((base/'function-roles.json').read_text())
  self.assertTrue(set(roles)<=found,f'Missing functions: {set(roles)-found}')
  definitions={}
  for n in tree.body:
   if isinstance(n,ast.Assign):
    for target in n.targets:
     if isinstance(target,ast.Name):definitions[target.id]=n.value
  schemas=[ast.literal_eval(item)['name'] for item in definitions['BUILTIN_TOOLS'].elts]
  handlers={ast.literal_eval(key) for key in definitions['BUILTIN_HANDLERS'].keys}
  self.assertEqual(len(schemas),26);self.assertEqual(len(handlers),25);self.assertEqual(set(schemas)-handlers,{'compact'})
  prompt=(base/'system-prompt/_index.md').read_text()
  self.assertNotIn('def update_context',prompt)
  self.assertNotIn('def assemble_system_prompt',prompt)
  source_sections=definitions['PROMPT_SECTIONS']
  expected_sections={ast.literal_eval(k):ast.dump(v) for k,v in zip(source_sections.keys,source_sections.values)}
  selected=set()
  for block in re.findall(r'```python\n(.*?)\n```',prompt,re.S):
   for n in ast.walk(ast.parse(block)):
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROMPT_SECTIONS' for t in n.targets):
     for k,v in zip(n.value.keys,n.value.values):
      name=ast.literal_eval(k);self.assertEqual(ast.dump(v),expected_sections[name]);selected.add(name)
  self.assertEqual(selected,{'identity','workspace','tasks','memory','compaction'})
  self.assertTrue((shared.REPO/'static/examples/s15-repo/system-prompt-legacy.md').exists())
  original=source.parent/'images/system-architecture.svg'
  self.assertEqual((shared.REPO/'static/examples/s15-repo/system-architecture.svg').read_text(),original.read_text())

class HarnessRuntime(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  path=Path('/home/fredkeira/projects/learn-claude-code/tests/test_agent_teams_runtime.py')
  if not path.exists():raise unittest.SkipTest('Local source required')
  spec=importlib.util.spec_from_file_location('harness_blog_helpers',path);cls.helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.helpers)
  cls.lesson_path=path.parent.parent/'s15_integrated_harness/code.py'
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='s15-blog-runtime-');self.lesson=self.helpers.load_lesson(Path(self.temp.name),self.lesson_path)
  self.stdout=contextlib.redirect_stdout(io.StringIO());self.stdout.__enter__()
  self.lesson.MEMORY_RUNTIME.read_memory_index=lambda:''
  self.lesson.MEMORY_RUNTIME.load_memories=lambda history:''
  self.lesson.MEMORY_RUNTIME.extract_memories=lambda history:False
 def tearDown(self):self.stdout.__exit__(None,None,None);self.temp.cleanup()

 def test_refreshes_all_model_inputs_and_new_mcp_tools(self):
  l=self.lesson;seen=[];events=[]
  l.MEMORY_RUNTIME.read_memory_index=lambda:'catalog'
  l.MEMORY_RUNTIME.load_memories=lambda history:events.append('recall') or 'selected records'
  def create(**kwargs):
   seen.append(kwargs);events.append('model')
   self.assertIn('Skills catalog:',kwargs['system']);self.assertIn('Relevant memory records:',kwargs['system'])
   if len(seen)==1:
    b=types.SimpleNamespace(type='tool_use',id='connect',name='connect_mcp',input={'name':'docs'})
    return types.SimpleNamespace(content=[b],stop_reason='tool_use')
   return types.SimpleNamespace(content=[types.SimpleNamespace(type='text',text='done')],stop_reason='end_turn')
  l.client.messages.create=create;history=[{'role':'user','content':'connect docs'}]
  l.agent_loop(history,{},'connect docs')
  self.assertEqual([len(call['tools']) for call in seen],[26,28])
  self.assertEqual(events,['recall','model','recall','model'])
  self.assertIs(seen[0]['messages'],history)
  self.assertNotIn('Connected MCP servers:',seen[0]['system']);self.assertIn('Connected MCP servers: docs',seen[1]['system'])
  for call in seen:self.assertIn('catalog',call['system']);self.assertNotIn('handlers',call)

 def test_compact_is_special_and_runs_after_paired_batch(self):
  l=self.lesson;calls=[];hooks=[];summarized=[]
  old_hook=l.trigger_hooks
  def trigger(event,*args):
   if event in {'PreToolUse','PostToolUse'}:hooks.append((event,args[0].name))
   return old_hook(event,*args)
  l.trigger_hooks=trigger
  def compact(messages,active):
   summarized.append([b['tool_use_id'] for b in messages[-1]['content'] if b.get('type')=='tool_result']);return messages
  l.compact_history=compact
  def create(**kwargs):
   calls.append(kwargs)
   if len(calls)==1:
    bs=[types.SimpleNamespace(type='tool_use',id='compact',name='compact',input={}),types.SimpleNamespace(type='tool_use',id='skill',name='load_skill',input={'name':'missing'})]
    return types.SimpleNamespace(content=bs,stop_reason='tool_use')
   return types.SimpleNamespace(content=[types.SimpleNamespace(type='text',text='done')],stop_reason='end_turn')
  l.client.messages.create=create;l.agent_loop([{'role':'user','content':'compact'}],{},'compact')
  self.assertEqual(summarized,[['compact','skill']])
  self.assertEqual(hooks,[('PreToolUse','load_skill'),('PostToolUse','load_skill')])
  self.assertNotIn('compact',l.BUILTIN_HANDLERS)

if __name__=='__main__':unittest.main()
