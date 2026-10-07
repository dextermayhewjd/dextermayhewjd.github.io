"""S11 background execution: chapter views, real functions and direct code links."""
import ast
import re
import unittest
import test_s08_explorer as shared

PROBE=r"""
<script>window.addEventListener('load',async()=>{
const result={passed:false};const check=(ok,m)=>{if(!ok)throw new Error(m)};
const pause=()=>new Promise(r=>setTimeout(r,40));
try{
 const root=document.getElementById('s11-background-explorer');check(root?.dataset.ready==='true','S11 overview missing');
 const baseline=document.querySelector('figure.architecture-diagram');const original=baseline.outerHTML;
 const core=document.getElementById('s11-background-core');
 const overview=root.querySelector('svg'),panel=root.querySelector('[data-explorer-panel]');
 check(overview.viewBox.baseVal.width===1200,'S11 lost the wide overview');
 const starter=overview.querySelector('[data-overview-stage="background-start"] rect').getBoundingClientRect();
 overview.dispatchEvent(new PointerEvent('pointermove',{pointerType:'mouse',clientX:starter.left+10,clientY:starter.top+10,bubbles:true}));await pause();
 check(overview.querySelector('[data-from="pre-event"][data-to="background-start"]').classList.contains('is-related'),'Background request bypasses the original permission entry');
 check(overview.querySelector('[data-from="background-start"][data-to="post-event"]').classList.contains('is-related'),'Started acknowledgement does not return to the old loop');
 overview.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'}));
 core.scrollIntoView({block:'start',behavior:'instant'});await pause();const before=scrollY;
 core.querySelector('a[data-function="start"]').dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await pause();
 const startCard=root.querySelector('[data-module-card="start"][open]');
 check(startCard && !panel.hidden && startCard.querySelector('[data-function-code="start"]').classList.contains('is-function-selected'),'Manager.start is not clickable');
 check(scrollY===before,'Viewing a background function scrolled the article');
 root.querySelector('[data-explorer-reset]').click();await pause();
 for(const key of ['select','start','worker','collect','inject','cleanup']){
  root.querySelector('[data-module-button="'+key+'"]').click();await pause();
  const card=root.querySelector('[data-module-card="'+key+'"][open]');check(card,'Missing detail '+key);
  const steps=[...card.querySelectorAll('[data-step-stage]')];check(steps.length===8,'Missing main/background lifecycle steps');
  for(const step of steps)for(const name of step.dataset.codeFunctions.split(' '))check(card.querySelector('[data-function-code="'+name+'"]'),'Missing '+name);
  for(const step of steps){const b=step.querySelector('rect').getBBox();for(const text of step.querySelectorAll('text[data-function]')){
    const p=text.getBBox();check(p.x>=b.x+3 && p.x+p.width<=b.x+b.width-3 && p.y>=b.y && p.y+p.height<=b.y+b.height,'Background function text overflows');}}
 }
 root.querySelector('[data-explorer-reset]').click();await pause();
 check(baseline.outerHTML===original,'S11 modified the S10 review');
 const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);check(ids.length===new Set(ids).size,'S11 duplicate IDs');
 check(document.documentElement.scrollWidth<=innerWidth,'S11 page overflow');result.passed=true;
}catch(e){result.error=e.message}const p=document.createElement('pre');p.id='s08-test-result';p.textContent=JSON.stringify(result);document.body.append(p);
});</script>
"""
class BackgroundBehavior(shared.ExplorerBehavior):
    chapter='s11'
    probe=PROBE
    test_without_enhancement=None

class BackgroundSource(unittest.TestCase):
    def test_functions_match_source(self):
        source=shared.Path('/home/fredkeira/projects/learn-claude-code/s11_background_tasks/code.py')
        if not source.exists():self.skipTest('Local teaching source required')
        expected={n.name:ast.dump(n) for n in ast.walk(ast.parse(source.read_text())) if isinstance(n,ast.FunctionDef)}
        text=(shared.REPO/'content/projects/learn-claude-code/s11/_index.md').read_text();found=set()
        for block in re.findall(r'```python\n(.*?)\n```',text,re.S):
            try:tree=ast.parse(block)
            except SyntaxError:continue
            for n in ast.walk(tree):
                if isinstance(n,ast.FunctionDef) and expected.get(n.name)==ast.dump(n):found.add(n.name)
        needed={'__init__','should_run_background','start','_run','collect','start_background_task',
                'collect_background_results','inject_background_results','execute_tool','call_tool',
                '_run_bash_process','_format_bash_result','_stop_process_group','agent_loop'}
        self.assertTrue(needed<=found,f'Missing source functions: {needed-found}')

if __name__=='__main__':unittest.main()
