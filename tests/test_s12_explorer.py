"""S12 scheduler chapter: source accuracy, inherited diagrams and code viewing."""
import ast,re,unittest
import test_s08_explorer as shared

PROBE=r"""<script>window.addEventListener('load',async()=>{
 const result={passed:false};const check=(v,m)=>{if(!v)throw new Error(m)};
 const pause=()=>new Promise(r=>setTimeout(r,40));
 try{
  const root=document.getElementById('s12-cron-explorer');check(root?.dataset.ready==='true','S12 explorer missing');
  const baseline=document.querySelector('figure.architecture-diagram');const original=baseline.outerHTML;
  const svg=root.querySelector('svg'),panel=root.querySelector('[data-explorer-panel]');
  const core=document.getElementById('s12-cron-core');
  check(svg.viewBox.baseVal.width===1200,'S12 overview not wide');
  const q=svg.querySelector('[data-overview-stage="cron-queue"] rect').getBoundingClientRect();
  svg.dispatchEvent(new PointerEvent('pointermove',{pointerType:'mouse',clientX:q.left+10,clientY:q.top+10,bubbles:true}));await pause();
  check(svg.querySelector('[data-from="cron-poll"][data-to="cron-queue"]').classList.contains('is-related'),'Missing due-to-queue input');
  check(svg.querySelector('[data-from="cron-queue"][data-to="cron-idle"]').classList.contains('is-related'),'Missing queue-to-idle delivery');
  svg.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'}));
  core.scrollIntoView({block:'start',behavior:'instant'});await pause();const before=scrollY;
  core.querySelector('a[data-function="poll_due_jobs"]').dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await pause();
  const polling=root.querySelector('[data-module-card="poll"][open]');
  check(polling && !panel.hidden && polling.querySelector('[data-function-code="poll_due_jobs"]').classList.contains('is-function-selected'),'Cannot view exact polling source');
  check(scrollY===before,'Scheduler code viewing moved the article');
  root.querySelector('[data-explorer-reset]').click();await pause();
  for(const key of ['schedule','match','poll','dispatch','ack','durable']){
   root.querySelector('[data-module-button="'+key+'"]').click();await pause();
   const card=root.querySelector('[data-module-card="'+key+'"][open]');check(card,'Missing module '+key);
   const steps=[...card.querySelectorAll('[data-step-stage]')];check(steps.length===8,'Missing scheduling/retry core steps');
   for(const step of steps){const b=step.querySelector('rect').getBBox();
    for(const name of step.dataset.codeFunctions.split(' '))check(card.querySelector('[data-function-code="'+name+'"]'),'Missing '+name);
    for(const text of step.querySelectorAll('text[data-function]')){const p=text.getBBox();check(p.x>=b.x+3 && p.x+p.width<=b.x+b.width-3 && p.y>=b.y && p.y+p.height<=b.y+b.height,'Cron function text overflows');}}
  }
  root.querySelector('[data-explorer-reset]').click();await pause();
  check(baseline.outerHTML===original,'S12 changed its S11 review');
  const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);check(ids.length===new Set(ids).size,'Duplicate S12 IDs');
  check(document.documentElement.scrollWidth<=innerWidth,'S12 page overflows');result.passed=true;
 }catch(e){result.error=e.message}
 const p=document.createElement('pre');p.id='s08-test-result';p.textContent=JSON.stringify(result);document.body.append(p);
});</script>"""
class SchedulerBehavior(shared.ExplorerBehavior):
 chapter='s12';probe=PROBE;test_without_enhancement=None

class SchedulerSource(unittest.TestCase):
 def test_functions_match_source(self):
  source=shared.Path('/home/fredkeira/projects/learn-claude-code/s12_cron_scheduler/code.py')
  if not source.exists():self.skipTest('Local teaching source required')
  expected={n.name:ast.dump(n) for n in ast.walk(ast.parse(source.read_text())) if isinstance(n,ast.FunctionDef)}
  text=(shared.REPO/'content/projects/learn-claude-code/s12/_index.md').read_text();found=set()
  for block in re.findall(r'```python\n(.*?)\n```',text,re.S):
   try:tree=ast.parse(block)
   except SyntaxError:continue
   for n in ast.walk(tree):
    if isinstance(n,ast.FunctionDef) and expected.get(n.name)==ast.dump(n):found.add(n.name)
  needed={'schedule_job','cancel_job','new_cron_id','validate_cron','_validate_cron_field',
          'cron_matches','_cron_field_matches','poll_due_jobs','_enqueue_due_job','consume_cron_queue',
          'acknowledge_cron_jobs','restore_cron_jobs','save_durable_jobs','load_durable_jobs',
          'cron_scheduler_loop','queue_processor_loop','run_agent_turn_locked','agent_loop',
          'start_runtime_threads','stop_runtime_threads','request_permission','has_cron_queue','execute_tool'}
  self.assertTrue(needed<=found,f'Missing source functions: {needed-found}')

if __name__=='__main__':unittest.main()
