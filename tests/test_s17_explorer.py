"""Goal chapter: exact source, inherited geometry and core source/arrow interaction."""
import ast,copy,json,re,unittest
from pathlib import Path
import test_s08_explorer as shared

PROBE=r"""<script>window.addEventListener('load',async()=>{
 const result={passed:false},check=(v,m)=>{if(!v)throw new Error(m)};
 const pause=()=>new Promise(r=>setTimeout(r,40));
 try{
  const root=document.getElementById('s17-goal-explorer');check(root?.dataset.ready==='true','Goal reader not initialized');
  const baseline=document.querySelector('figure.architecture-diagram'),original=baseline.outerHTML;
  const previous=new DOMParser().parseFromString(await(await fetch('/projects/learn-claude-code/s16/')).text(),'text/html').querySelector('[data-diagram-explorer] svg');
  const geometry=s=>JSON.stringify([...s.querySelectorAll('rect[data-stage],path[stroke]')].map(n=>['data-stage','x','y','width','height','d'].map(a=>n.getAttribute(a))));
  check(geometry(baseline.querySelector('svg'))===geometry(previous),'Goal baseline changed S16 geometry');
  check(baseline.querySelectorAll('rect[data-view="modified"]').length===2,'Incorrect baseline modified interfaces');
  check(baseline.querySelectorAll('rect[data-view="folded"]').length===3,'Workflow folding hints missing');
  const outline=document.getElementById('s17-goal-outline');
  check(outline.querySelectorAll('#TableOfContents>ul>li').length===4,'Goal outline missing hierarchy');
  for(const link of outline.querySelectorAll('a'))check(document.getElementById(link.hash.slice(1)),'Broken outline '+link.hash);
  const svg=root.querySelector('svg'),panel=root.querySelector('[data-explorer-panel]');
  check(svg.viewBox.baseVal.width===1200,'Goal overview too narrow');
  check(!svg.querySelector('rect[data-stage="wf-journal"]'),'Folded Workflow detail retained');
  check(!svg.querySelector('[data-from="decision"][data-to="stop-event"]'),'Goal Gate can be bypassed');
  const hover=(s,stage)=>{const b=s.querySelector('rect[data-stage="'+stage+'"]').getBoundingClientRect();s.dispatchEvent(new PointerEvent('pointermove',{pointerType:'mouse',clientX:b.left+10,clientY:b.top+10,bubbles:true}));};
  const leave=s=>s.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'}));
  hover(svg,'goal-gate');await pause();
  for(const [from,to] of [['decision','goal-gate'],['goal-gate','goal-evaluator'],['goal-evaluator','goal-gate'],['goal-gate','goal-feedback'],['goal-gate','stop-event']])check(svg.querySelector('[data-from="'+from+'"][data-to="'+to+'"]').classList.contains('is-related'),'Missing gate route '+from+' -> '+to);
  check(panel.hidden,'Hover opened Goal details');leave(svg);
  const core=document.getElementById('s17-goal-core');core.scrollIntoView({block:'start',behavior:'instant'});await pause();
  const before=scrollY,cs=core.querySelector('svg'),originalCore=geometry(cs);
  const paths=[...cs.querySelectorAll('[data-route]')],markers=paths.map(p=>p.getAttribute('marker-end'));
  hover(cs,'gate');await pause();
  const judgment=cs.querySelector('[data-from="evaluator"][data-to="gate"]');
  check(judgment.classList.contains('is-related') && parseFloat(getComputedStyle(judgment).strokeWidth)>3,'Core evaluator return not highlighted');
  check(cs.querySelector('[data-from="gate"][data-to="return"]').classList.contains('is-related'),'Core return branch not highlighted');
  check(panel.hidden && scrollY===before && geometry(cs)===originalCore,'Core preview altered layout or scroll');leave(cs);await pause();
  check(paths.every((p,i)=>p.getAttribute('marker-end')===markers[i]),'Core arrowheads not restored');
  const link=core.querySelector('a[data-function="evaluate_after_turn"]');link.focus({preventScroll:true});await pause();
  check(judgment.classList.contains('is-related'),'Keyboard focus misses gate relation');link.blur();
  link.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await pause();
  const gate=root.querySelector('[data-module-card="gate"][open]');
  check(gate?.querySelector('[data-function-code="evaluate_after_turn"].is-function-selected'),'Gate function click cannot show source');
  check(gate.querySelector('[data-function-code="evaluate_after_turn"]').textContent.includes('GoalController'),'Gate role missing');
  check(scrollY===before,'Goal source reading moved whole article');
  check(!gate.querySelector('[data-local-diagram] .is-related'),'Hover state copied into reader');
  root.querySelector('[data-explorer-reset]').click();await pause();
  for(const key of ['command','gate','judge','loop','state','background']){
   root.querySelector('[data-module-button="'+key+'"]').click();await pause();const card=root.querySelector('[data-module-card="'+key+'"][open]');
   check(card,'Missing Goal module '+key);const steps=[...card.querySelectorAll('[data-step-stage]')];check(steps.length===8,'Goal core missing stages');
   for(const step of steps){const b=step.querySelector('rect').getBBox();
    for(const name of step.dataset.codeFunctions.split(' '))check(card.querySelector('[data-function-code="'+name+'"]'),'Missing Goal function '+name);
    for(const text of step.querySelectorAll('text[data-function]')){const p=text.getBBox();check(p.x>=b.x+3 && p.x+p.width<=b.x+b.width-3 && p.y>=b.y && p.y+p.height<=b.y+b.height,'Goal function label overflows '+text.textContent);}}
  }
  root.querySelector('[data-explorer-reset]').click();await pause();
  check(baseline.outerHTML===original,'Goal interactions changed baseline');
  const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);check(ids.length===new Set(ids).size,'Duplicate Goal IDs');
  check(document.documentElement.scrollWidth<=innerWidth,'Goal page overflows');result.passed=true;
 }catch(e){result.error=e.message}
 const p=document.createElement('pre');p.id='s08-test-result';p.textContent=JSON.stringify(result);document.body.append(p);
});</script>"""

class GoalBehavior(shared.ExplorerBehavior):
 chapter='s17';probe=PROBE;test_without_enhancement=None

class GoalSource(unittest.TestCase):
 def test_source_excerpts_and_original_figure(self):
  path=Path('/home/fredkeira/projects/learn-claude-code/s17_goal_loop/code.py')
  if not path.exists():self.skipTest('Local teaching source required')
  def normalized(node):
   node=copy.deepcopy(node)
   for child in ast.walk(node):
    if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)):
     doc=ast.get_docstring(child,clean=True)
     if doc is not None:child.body[0].value.value=doc
   return ast.dump(node)
  expected={}
  for n in ast.walk(ast.parse(path.read_text())):
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):expected.setdefault(n.name,[]).append(normalized(n))
  base=shared.REPO/'content/projects/learn-claude-code/s17';found=set()
  for block in re.findall(r'```python\n(.*?)\n```',(base/'_index.md').read_text(),re.S):
   for n in ast.walk(ast.parse(block)):
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
     self.assertIn(normalized(n),expected.get(n.name,[]),f'{n.name} differs from source');found.add(n.name)
  roles=json.loads((base/'function-roles.json').read_text());self.assertTrue(set(roles)<=found,f'Missing source {set(roles)-found}')
  self.assertEqual((path.parent/'images/goal-loop-overview.svg').read_bytes(),(shared.REPO/'static/examples/s17-repo/goal-loop-overview.svg').read_bytes())
  self.assertNotIn('CommandQueue',(base/'images/goal-core.svg').read_text())

if __name__=='__main__':unittest.main()
