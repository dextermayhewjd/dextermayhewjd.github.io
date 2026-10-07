"""Check the Memory chapter's reused diagram/function reader in Chrome."""

import unittest
import test_s08_explorer as shared

MEMORY_PROBE = r"""
<script>
window.addEventListener('load',async()=>{
 const result={passed:false};
 const check=(ok,message)=>{if(!ok)throw new Error(message);};
 const pause=()=>new Promise(resolve=>setTimeout(resolve,40));
 try {
  const root=document.getElementById('s09-memory-explorer');
  check(root && root.dataset.ready==='true','Memory overview did not initialize');
  const baseline=document.querySelector('figure.architecture-diagram');
  const original=baseline.outerHTML;
  const main=root.querySelector('svg');
  check(main.viewBox.baseVal.width===1200 && main.getBoundingClientRect().width>=1200,
    'The Memory canvas did not inherit the wide layout');
  check(baseline.querySelector('svg').getBoundingClientRect().width>=1200,
    'The previous chapter view uses a different display width');
  const shape=()=>JSON.stringify([...main.querySelectorAll('rect,path')].map(n=>
    ['x','y','width','height','d','fill','stroke'].map(a=>n.getAttribute(a))));
  const initial=shape();
  check(root.querySelectorAll('[data-module-button]').length===5,'Memory interfaces are missing');
  const recall=main.querySelector('[data-overview-stage="memory-recall"] rect').getBoundingClientRect();
  main.dispatchEvent(new PointerEvent('pointermove',{pointerType:'mouse',
    clientX:recall.left+10,clientY:recall.top+10,bubbles:true}));await pause();
  check(main.dataset.connectionSelection==='memory-recall','Memory has no hover preview');
  check(main.querySelector('[data-from="memory-store"][data-to="memory-recall"]').classList.contains('is-related'),
    'Hover missed the memory storage input');
  check(main.querySelector('[data-from="memory-recall"][data-to="system"]').classList.contains('is-related'),
    'Hover missed the SYSTEM output');
  check(root.dataset.selected==='' && root.querySelector('[data-explorer-panel]').hidden,
    'Memory hover opened a detail panel');
  main.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'}));await pause();
  check(!main.querySelector('.is-related, .is-unrelated'),'Memory hover did not clear on leave');
  for(const key of ['recall','context','extract','save','consolidate']) {
   root.querySelector('[data-module-button="'+key+'"]').click();await pause();
   const card=root.querySelector('[data-module-card="'+key+'"][open]');
   check(card,'Memory interface did not open: '+key);
   const rect=root.querySelector('a[data-module="'+key+'"] rect');
   check(main.dataset.connectionSelection===rect.dataset.stage,'Selected memory node has no arrow selection');
   const related=[...main.querySelectorAll('path.is-related[data-from]')];
   check(related.length>0,'Memory input/output arrows did not highlight: '+key);
   check(related.every(p=>p.dataset.from===rect.dataset.stage || p.dataset.to===rect.dataset.stage),
     'Memory selection highlights unrelated arrows');
   if(key==='recall') {
    check(related.some(p=>p.dataset.from==='memory-store'),'Recall storage input is not highlighted');
    check(related.some(p=>p.dataset.to==='system'),'Recall SYSTEM output is not highlighted');
   }
   check(root.querySelectorAll('[data-module-card][open]').length===1,'Multiple memory views opened');
   check(card.querySelector('pre'),'Source code missing for '+key);
   const steps=[...card.querySelectorAll('[data-step-stage]')];
   check(steps.length===6,'Core memory steps are not fully mapped');
   for(const step of steps) for(const name of step.dataset.codeFunctions.split(' ')) {
    check(card.querySelector('[data-function-code="'+name+'"]'),'Missing mapped function '+name);
   }
   const step=steps.find(n=>n.dataset.stepStage==='extract');
   step.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
   check(card.querySelector('[data-function-code="extract_memories"]').classList.contains('is-function-selected'),
     'Memory step/code highlight failed');
   check(shape()===initial,'The Memory overview changed during exploration');
  }
  root.querySelector('[data-explorer-reset]').click();await pause();
  check(baseline.outerHTML===original,'The inherited S08 view changed');
  check(!main.querySelector('.is-related, .is-unrelated'),'Reset left Memory arrows selected');
  check(document.documentElement.scrollWidth<=innerWidth,'Memory page overflow');
  const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);
  check(ids.length===new Set(ids).size,'Memory detail views introduced duplicate IDs');
  result.passed=true;
 }catch(error){result.error=error.message;}
 const p=document.createElement('pre');p.id='s08-test-result';p.textContent=JSON.stringify(result);document.body.append(p);
});
</script>
"""


class MemoryBehavior(shared.ExplorerBehavior):
    chapter = 's09'
    probe = MEMORY_PROBE
    # The shared component fallback is covered by its S08 browser test.
    test_without_enhancement = None


if __name__ == '__main__':
    unittest.main()
