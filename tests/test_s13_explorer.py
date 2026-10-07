"""S13 source excerpts, previous-stage geometry, diagram links and code reading."""
import ast,json,re,unittest
import xml.etree.ElementTree as ET
import test_s08_explorer as shared

PROBE=r"""<script>window.addEventListener('load',async()=>{
 const result={passed:false};const check=(v,m)=>{if(!v)throw new Error(m)};
 const pause=()=>new Promise(r=>setTimeout(r,40));
 try{
  const root=document.getElementById('s13-team-explorer');check(root?.dataset.ready==='true','S13 explorer missing');
  const baseline=document.querySelector('figure.architecture-diagram');const original=baseline.outerHTML;
  const svg=root.querySelector('svg'),panel=root.querySelector('[data-explorer-panel]');
  const core=document.getElementById('s13-team-core');
  check(svg.viewBox.baseVal.width===1200,'S13 overview not wide');
  const outline=document.getElementById('s13-chapter-outline');
  check(outline.querySelectorAll('#TableOfContents>ul>li').length===4,'S13 outline lost primary hierarchy');
  for(const link of outline.querySelectorAll('a'))check(document.getElementById(link.hash.slice(1)),'Broken outline '+link.hash);
  const previous=new DOMParser().parseFromString(await(await fetch('/projects/learn-claude-code/s12/')).text(),'text/html').querySelector('[data-diagram-explorer] svg');
  const geometry=s=>JSON.stringify([...s.querySelectorAll('rect[data-stage],path[stroke]')].map(n=>['data-stage','x','y','width','height','d'].map(a=>n.getAttribute(a))));
  check(geometry(baseline.querySelector('svg'))===geometry(previous),'S13 baseline differs from S12 geometry');
  check(baseline.querySelectorAll('rect[data-view="folded"]').length===6,'Cron folding cues missing');
  check(baseline.querySelectorAll('rect[data-view="modified"]').length===6,'Team change cues missing');
  check(!svg.querySelector('[data-stage="cron-poll"]') && svg.querySelector('[data-stage="cron-interface"]'),'Cron details not folded to explicit interface');
  const q=svg.querySelector('[data-overview-stage="team-mailbox"] rect').getBoundingClientRect();
  svg.dispatchEvent(new PointerEvent('pointermove',{pointerType:'mouse',clientX:q.left+10,clientY:q.top+10,bubbles:true}));await pause();
  check(svg.querySelector('[data-from="team-work"][data-to="team-mailbox"]').classList.contains('is-related'),'Missing teammate result input');
  check(svg.querySelector('[data-from="team-mailbox"][data-to="team-wake"]').classList.contains('is-related'),'Missing Lead wake output');
  check(svg.querySelector('[data-from="team-mailbox"][data-to="team-idle"]').classList.contains('is-related'),'Missing teammate inbox output');
  check(panel.hidden,'Hover opened a detail panel');
  svg.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'}));
  core.scrollIntoView({block:'start',behavior:'instant'});await pause();const before=scrollY;
  core.querySelector('a[data-function="wait_for_cli_event"]').dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await pause();
  const wake=root.querySelector('[data-module-card="wake"][open]');
  check(wake && !panel.hidden && wake.querySelector('[data-function-code="wait_for_cli_event"]').classList.contains('is-function-selected'),'Cannot view precise CLI source');
  check(scrollY===before,'Team source viewing moved the article');
  check(wake.querySelector('[data-function-code="wait_for_cli_event"]').textContent.includes('Harness CLI'),'Function role missing');
  root.querySelector('[data-explorer-reset]').click();await pause();
  core.querySelector('a[data-function="work"]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));await pause();
  check(root.querySelector('[data-module-card="work"][open] [data-function-code="work"].is-function-selected'),'Keyboard source selection failed');
  root.querySelector('[data-explorer-reset]').click();await pause();
  for(const key of ['spawn','work','mailbox','idle','wake']){
   root.querySelector('[data-module-button="'+key+'"]').click();await pause();
   const card=root.querySelector('[data-module-card="'+key+'"][open]');check(card,'Missing module '+key);
   const steps=[...card.querySelectorAll('[data-step-stage]')];check(steps.length===7,'Missing runtime/idle/exit core stages');
   for(const step of steps){const b=step.querySelector('rect').getBBox();
    for(const name of step.dataset.codeFunctions.split(' '))check(card.querySelector('[data-function-code="'+name+'"]'),'Missing '+name);
    for(const text of step.querySelectorAll('text[data-function]')){const p=text.getBBox();check(p.x>=b.x+3 && p.x+p.width<=b.x+b.width-3 && p.y>=b.y && p.y+p.height<=b.y+b.height,'Team function label overflows');}}
  }
  root.querySelector('[data-explorer-reset]').click();await pause();
  check(baseline.outerHTML===original,'Team interactions changed previous graph');
  const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);check(ids.length===new Set(ids).size,'Duplicate S13 IDs');
  check(document.documentElement.scrollWidth<=innerWidth,'S13 page overflows');result.passed=true;
 }catch(e){result.error=e.message}
 const p=document.createElement('pre');p.id='s08-test-result';p.textContent=JSON.stringify(result);document.body.append(p);
});</script>"""

class TeamsBehavior(shared.ExplorerBehavior):
 chapter='s13';probe=PROBE;test_without_enhancement=None

class TeamsSource(unittest.TestCase):
 def test_functions_match_source(self):
  source=shared.Path('/home/fredkeira/projects/learn-claude-code/s13_agent_teams/code.py')
  if not source.exists():self.skipTest('Local teaching source required')
  expected={}
  for n in ast.walk(ast.parse(source.read_text())):
   if isinstance(n,ast.FunctionDef):expected.setdefault(n.name,[]).append(ast.dump(n))
  base=shared.REPO/'content/projects/learn-claude-code/s13'
  roles=json.loads((base/'function-roles.json').read_text())
  counts={}
  for page in base.glob('*.md'):
   found=set()
   for block in re.findall(r'```python\n(.*?)\n```',page.read_text(),re.S):
    tree=ast.parse(block)
    for n in ast.walk(tree):
     if isinstance(n,ast.FunctionDef):
      self.assertIn(ast.dump(n),expected.get(n.name,[]),f'{page.name}: {n.name} differs from source')
      found.add(n.name)
   counts[page.name]=len(found)
   if page.name=='_index.md':self.assertTrue(set(roles)<=found,f'Missing main code: {set(roles)-found}')
  self.assertEqual(len(counts),5)
  self.assertGreaterEqual(counts['_index.md'],21)
  for page in counts:
   if page!='_index.md':self.assertGreaterEqual(counts[page],5,page)

 def test_subchapter_diagram_targets_and_metadata(self):
  base=shared.REPO/'content/projects/learn-claude-code/s13'
  pairs=[('01-team-messaging.md','team-messaging.svg'),('02-team-protocols.md','team-protocol.svg'),
         ('03-task-claiming.md','team-claiming.svg'),('04-worktree-isolation.md','team-worktree.svg')]
  for page,figure in pairs:
   text=(base/page).read_text();self.assertNotIn('待填写',text)
   anchors=set(re.findall(r'\{#([^}]+)\}',text))
   for a in ET.parse(base/'images'/figure).getroot().iter():
    if a.tag.endswith('a'):self.assertIn(a.get('href').lstrip('#'),anchors,f'{figure}: broken function target')
  self.assertIn('/projects/learn-claude-code/s18/',(base/'04-worktree-isolation.md').read_text())
  main=(base/'_index.md').read_text();self.assertIn('外层 CLI',main)
  self.assertIn('未合入 S11 后台任务、S12 Cron',main)

if __name__=='__main__':unittest.main()
