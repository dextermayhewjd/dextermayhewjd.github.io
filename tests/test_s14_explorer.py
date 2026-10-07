"""S14: source excerpts, tool-pool timing, inherited diagrams and code viewing."""
import ast,contextlib,importlib.util,io,json,re,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import test_s08_explorer as shared

PROBE=r"""<script>window.addEventListener('load',async()=>{
 const result={passed:false};const check=(v,m)=>{if(!v)throw new Error(m)};
 const pause=()=>new Promise(r=>setTimeout(r,40));
 try{
  const root=document.getElementById('s14-mcp-explorer');check(root?.dataset.ready==='true','MCP explorer missing');
  const baseline=document.querySelector('figure.architecture-diagram');const original=baseline.outerHTML;
  const svg=root.querySelector('svg'),panel=root.querySelector('[data-explorer-panel]');
  const core=document.getElementById('s14-mcp-core');
  check(svg.viewBox.baseVal.width===1200,'MCP overview not wide');
  const outline=document.getElementById('s14-chapter-outline');
  check(outline.querySelectorAll('#TableOfContents>ul>li').length===4,'MCP outline hierarchy missing');
  for(const link of outline.querySelectorAll('a'))check(document.getElementById(link.hash.slice(1)),'Broken outline '+link.hash);
  const previous=new DOMParser().parseFromString(await(await fetch('/projects/learn-claude-code/s13/')).text(),'text/html').querySelector('[data-diagram-explorer] svg');
  const geometry=s=>JSON.stringify([...s.querySelectorAll('rect[data-stage],path[stroke]')].map(n=>['data-stage','x','y','width','height','d'].map(a=>n.getAttribute(a))));
  check(geometry(baseline.querySelector('svg'))===geometry(previous),'MCP baseline differs from S13');
  check(baseline.querySelectorAll('rect[data-view="folded"]').length===5,'Team folding cues missing');
  check(baseline.querySelectorAll('rect[data-view="modified"]').length===5,'Dynamic pool change cues missing');
  check(!svg.querySelector('[data-stage="team-work"]') && svg.querySelector('[data-stage="team-interface"]'),'Team fold has no retained interface');
  const q=svg.querySelector('[data-overview-stage="mcp-pool"] rect').getBoundingClientRect();
  svg.dispatchEvent(new PointerEvent('pointermove',{pointerType:'mouse',clientX:q.left+10,clientY:q.top+10,bubbles:true}));await pause();
  for(const [from,to] of [['mcp-registry','mcp-pool'],['prepare','mcp-pool'],['mcp-pool','tools'],['mcp-pool','handler']])
   check(svg.querySelector('[data-from="'+from+'"][data-to="'+to+'"]').classList.contains('is-related'),'Missing pool relation '+from+' -> '+to);
  check(panel.hidden,'MCP hover opened details');
  svg.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'}));
  core.scrollIntoView({block:'start',behavior:'instant'});await pause();const before=scrollY;
  core.querySelector('a[data-function="assemble_tool_pool"]').dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await pause();
  const pool=root.querySelector('[data-module-card="pool"][open]');
  check(pool && !panel.hidden && pool.querySelector('[data-function-code="assemble_tool_pool"]').classList.contains('is-function-selected'),'Cannot view exact tool-pool source');
  check(scrollY===before,'MCP source viewing moved the article');
  check(pool.querySelector('[data-function-code="assemble_tool_pool"]').textContent.includes('Harness 每轮'),'Function role missing');
  root.querySelector('[data-explorer-reset]').click();await pause();
  core.querySelector('a[data-function="call_tool"]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));await pause();
  check(root.querySelector('[data-module-card="call"][open] [data-function-code="call_tool"].is-function-selected'),'Client keyboard source viewing failed');
  root.querySelector('[data-explorer-reset]').click();await pause();
  for(const key of ['connect','client','pool','permission','call']){
   root.querySelector('[data-module-button="'+key+'"]').click();await pause();
   const card=root.querySelector('[data-module-card="'+key+'"][open]');check(card,'Missing module '+key);
   const steps=[...card.querySelectorAll('[data-step-stage]')];check(steps.length===8,'MCP core missing discovery/call/error stages');
   for(const step of steps){const b=step.querySelector('rect').getBBox();
    for(const name of step.dataset.codeFunctions.split(' '))check(card.querySelector('[data-function-code="'+name+'"]'),'Missing '+name);
    for(const text of step.querySelectorAll('text[data-function]')){const p=text.getBBox();check(p.x>=b.x+3 && p.x+p.width<=b.x+b.width-3 && p.y>=b.y && p.y+p.height<=b.y+b.height,'MCP function label overflows');}}
  }
  root.querySelector('[data-explorer-reset]').click();await pause();
  check(baseline.outerHTML===original,'MCP interactions changed S13 review');
  const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);check(ids.length===new Set(ids).size,'Duplicate MCP IDs');
  check(document.documentElement.scrollWidth<=innerWidth,'MCP page overflows');result.passed=true;
 }catch(e){result.error=e.message}
 const p=document.createElement('pre');p.id='s08-test-result';p.textContent=JSON.stringify(result);document.body.append(p);
});</script>"""

class MCPBehavior(shared.ExplorerBehavior):
 chapter='s14';probe=PROBE;test_without_enhancement=None

class MCPSource(unittest.TestCase):
 def test_functions_match_source(self):
  source=Path('/home/fredkeira/projects/learn-claude-code/s14_mcp_plugin/code.py')
  if not source.exists():self.skipTest('Local teaching source required')
  expected={n.name:ast.dump(n) for n in ast.walk(ast.parse(source.read_text())) if isinstance(n,ast.FunctionDef)}
  base=shared.REPO/'content/projects/learn-claude-code/s14'
  found=set()
  for block in re.findall(r'```python\n(.*?)\n```',(base/'_index.md').read_text(),re.S):
   for n in ast.walk(ast.parse(block)):
    if isinstance(n,ast.FunctionDef):
     self.assertEqual(ast.dump(n),expected.get(n.name),f'{n.name} differs from source');found.add(n.name)
  required=set(json.loads((base/'function-roles.json').read_text()))|{'run_connect_mcp'}
  self.assertTrue(required<=found,f'Missing functions: {required-found}')

 def test_article_keeps_mock_and_error_boundaries(self):
  text=(shared.REPO/'content/projects/learn-claude-code/s14/_index.md').read_text()
  self.assertIn('/projects/learn-claude-code/s19/',text)
  self.assertNotIn('待填写',text)
  self.assertIn('没有发出 JSON-RPC 请求',text)
  self.assertIn('当前工具批次仍用旧 handlers',text)
  self.assertIn('没有按完整 JSON Schema',text)
  self.assertIn('组装或模型请求失败',text)

class MCPRuntime(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  tests=Path('/home/fredkeira/projects/learn-claude-code/tests/test_agent_teams_runtime.py')
  if not tests.exists():raise unittest.SkipTest('Local teaching source required')
  spec=importlib.util.spec_from_file_location('teaching_mcp_test_helpers',tests)
  cls.helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.helpers)
  cls.lesson_path=tests.parent.parent/'s14_mcp_plugin/code.py'

 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='s14-runtime-')
  self.lesson=self.helpers.load_lesson(Path(self.temp.name),self.lesson_path)
  self.stdout=contextlib.redirect_stdout(io.StringIO());self.stdout.__enter__()

 def tearDown(self):
  self.stdout.__exit__(None,None,None);self.temp.cleanup()

 def test_connect_is_visible_only_in_next_model_request(self):
  l=self.lesson;seen=[];calls=0
  # Tool helper uses a distinct argument name so the business `name` can pass through.
  def create(**kwargs):
   nonlocal calls
   seen.append({t['name'] for t in kwargs['tools']});calls+=1
   def tool(call_id,tool_name,args):return types.SimpleNamespace(type='tool_use',id=call_id,name=tool_name,input=args)
   if calls==1:return types.SimpleNamespace(content=[tool('c','connect_mcp',{'name':'docs'}),tool('early','mcp__docs__search',{'query':'hooks'})])
   if calls==2:return types.SimpleNamespace(content=[tool('s','mcp__docs__search',{'query':'hooks'})])
   return types.SimpleNamespace(content=[types.SimpleNamespace(type='text',text='done')])
  l.client.messages.create=create;history=[{'role':'user','content':'look up hooks'}]
  # An unavailable external name has no host policy yet, so permission comes first.
  with patch('builtins.input',return_value='yes') as approve:
   l.agent_loop(history)
  self.assertEqual(approve.call_count,1)
  self.assertEqual([len(x) for x in seen],[6,8,8])
  self.assertNotIn('mcp__docs__search',seen[0]);self.assertIn('mcp__docs__search',seen[1])
  results=[b for msg in history if isinstance(msg.get('content'),list) for b in msg['content'] if isinstance(b,dict) and b.get('type')=='tool_result']
  self.assertEqual([x['tool_use_id'] for x in results],['c','early','s'])
  self.assertIn('Unknown tool',results[1]['content']);self.assertEqual(results[2]['content'],"[docs] Found 3 results for 'hooks'")

 def test_generated_handlers_keep_server_and_original_tool(self):
  l=self.lesson;l.connect_mcp('docs');l.connect_mcp('deploy');tools,handlers=l.assemble_tool_pool()
  self.assertEqual(len(tools),10)
  self.assertEqual(handlers['mcp__docs__search'](query='loop'),"[docs] Found 3 results for 'loop'")
  self.assertEqual(handlers['mcp__docs__get_version'](),'[docs] API v2.1.0')
  self.assertEqual(handlers['mcp__deploy__status'](service='web'),'[deploy] web: running (v1.4.2)')
  self.assertEqual(handlers['mcp__deploy__trigger'](service='web'),'[deploy] Triggered: web')
  self.assertEqual(l.mcp_tool_policies['mcp__deploy__trigger'],'confirm')
  self.assertEqual(l.mcp_tool_policies['mcp__deploy__status'],'allow')

 def test_tool_failure_returns_text_but_pool_failure_ends_turn(self):
  l=self.lesson;l.connect_mcp('docs');_,handlers=l.assemble_tool_pool()
  block=types.SimpleNamespace(name='mcp__docs__search',input={})
  self.assertIn('MCP error: TypeError',l.execute_tool(block,handlers))
  a=l.MCPClient('docs.one');a.register([{'name':'get.version','inputSchema':{}}],{'get.version':lambda:'one'})
  b=l.MCPClient('docs_one');b.register([{'name':'get_version','inputSchema':{}}],{'get_version':lambda:'two'})
  l.mcp_clients.clear();l.mcp_clients.update({'docs.one':a,'docs_one':b})
  attempts=[];l.client.messages.create=lambda **kwargs:attempts.append(kwargs)
  history=[{'role':'user','content':'go'}];l.agent_loop(history)
  self.assertEqual(attempts,[])
  self.assertEqual(history[-1]['role'],'assistant')
  self.assertIn('collision',history[-1]['content'][0]['text'])

if __name__=='__main__':unittest.main()
