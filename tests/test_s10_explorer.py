"""Task diagrams retain the previous loop, show real source, and preview edges."""
import ast
import re
import unittest
import test_s08_explorer as shared

TASK_PROBE = r"""
<script>
window.addEventListener('load',async()=>{
 const result={passed:false};
 const check=(ok,message)=>{if(!ok)throw new Error(message);};
 const pause=()=>new Promise(resolve=>setTimeout(resolve,40));
 try {
  const root=document.getElementById('s10-task-explorer');
  check(root && root.dataset.ready==='true','Task overview did not initialize');
  const outline=document.getElementById('s10-chapter-outline');
  check(outline,'The folder-style chapter outline is missing');
  const groups=[...outline.querySelectorAll('nav > ul > li')];
  check(groups.length===4,'The outline should have four main folders');
  check(outline.querySelectorAll('a[href^="#"]').length===19,'The outline should contain only two heading levels');
  for(const [index,group] of groups.entries()) {
   const parent=group.querySelector(':scope > a');
   check(parent.textContent.startsWith((index+1)+'. '),'Main folder numbering is inconsistent');
   check(document.getElementById(parent.hash.slice(1)).tagName==='H2','A main folder should target H2');
   for(const link of group.querySelectorAll(':scope > ul > li > a'))
    check(link.textContent.startsWith((index+1)+'.') && document.getElementById(link.hash.slice(1)).tagName==='H3',
      'A child should keep its parent number and target H3');
  }
  for(const link of outline.querySelectorAll('a[href^="#"]')) {
   const target=document.getElementById(link.hash.slice(1));
   check(target,'An outline link has no heading');
   const copy=target.cloneNode(true);copy.querySelectorAll('a.anchor').forEach(a=>a.remove());
   check(copy.textContent.trim()===link.textContent.trim(),'Outline label differs from the actual heading');
  }
  outline.querySelector('a[href="#task-claim"]').click();await pause();
  check(location.hash==='#task-claim','The chapter outline cannot jump to a subsection');
  const baseline=document.querySelector('figure.architecture-diagram');
  const original=baseline.outerHTML;
  const svg=root.querySelector('svg');
  check(svg.viewBox.baseVal.width===1200,'Task overview lost the wide layout');
  const panel=root.querySelector('[data-explorer-panel]');
  const core=document.getElementById('s10-task-core');
  check(!core.querySelector('[data-function^="run_"]'),'The minimal core still shows tool entry wrappers');
  const createLink=core.querySelector('a[data-function="create_task"]');
  check(createLink,'The standalone core function is not clickable');
  core.scrollIntoView({block:'start',behavior:'instant'});await pause();
  const beforeFunctionClick=scrollY;
  createLink.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await pause();
  check(!panel.hidden,'Clicking a core function did not open nearby code');
  const createCard=root.querySelector('[data-module-card="tasks"][open]');
  check(createCard && createCard.querySelector('[data-function-code="create_task"]').classList.contains('is-function-selected'),
    'The function link did not select the exact implementation');
  check(scrollY===beforeFunctionClick,'Function viewing scrolled away from the core diagram');
  const localLoad=createCard.querySelector('a[data-function="load"]');
  localLoad.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await pause();
  check(createCard.querySelector('[data-function-code="load"]').classList.contains('is-function-selected') &&
    !createCard.querySelector('[data-function-code="save"]').classList.contains('is-function-selected'),
    'Clicking a specific storage function selected the entire storage group');
  root.querySelector('[data-explorer-close]').click();await pause();
  const listLink=core.querySelector('a[data-function="list"]');
  listLink.dispatchEvent(new KeyboardEvent('keydown',{key:' ',bubbles:true,cancelable:true}));await pause();
  check(!panel.hidden && root.querySelector('[data-module-card="store"][open]')
    .querySelector('[data-function-code="list"]').classList.contains('is-function-selected'),
    'The core function link cannot be used with the keyboard');
  root.querySelector('[data-explorer-reset]').click();await pause();
  const index=document.getElementById('task-core-functions');
  check(!index.querySelector('[data-function^="run_"]'),'The core index still shows tool entry wrappers');
  index.open=true;
  index.querySelector('a[data-function="_depends_on"]').dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));await pause();
  check(root.querySelector('[data-module-card="dependencies"][open]')
    .querySelector('[data-function-code="_depends_on"]').classList.contains('is-function-selected'),
    'The helper function index does not open its precise code');
  root.querySelector('[data-explorer-reset]').click();index.open=false;await pause();
  const tasks=svg.querySelector('[data-overview-stage="task-tools"] rect').getBoundingClientRect();
  svg.dispatchEvent(new PointerEvent('pointermove',{pointerType:'mouse',
    clientX:tasks.left+10,clientY:tasks.top+10,bubbles:true}));await pause();
  check(svg.querySelector('[data-from="pre-event"][data-to="task-tools"]').classList.contains('is-related'),
    'The task branch is not connected after PreToolUse');
  check(svg.querySelector('[data-from="task-tools"][data-to="task-store"]').classList.contains('is-related'),
    'The task storage/validation output is missing');
  check(panel.hidden,'Hover should not open task details');
  svg.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'}));await pause();
  check(root.querySelectorAll('[data-module-button]').length===6,'Task interfaces are missing');
  for(const key of ['tasks','dependencies','claim','complete','store','files']) {
   root.querySelector('[data-module-button="'+key+'"]').click();await pause();
   const card=root.querySelector('[data-module-card="'+key+'"][open]');
   check(card && !panel.hidden,'Task detail missing: '+key);
   for(const [name,role] of [['create_task','内部创建包装'],
     ['create','TaskStore 内部存储方法'],['execute_tool','Harness 统一执行入口']]) {
    const title=card.querySelector('[data-function-code="'+name+'"] .diagram-explorer__function-title');
    check(title && title.textContent.includes(role),'The reader does not identify the function layer: '+name);
   }
   check(root.querySelectorAll('[data-module-card][open]').length===1,'Multiple task details opened');
   const steps=[...card.querySelectorAll('[data-step-stage]')];
   check(steps.length===9,'Task lifecycle, errors, and storage are not all mapped');
   const createStep=steps.find(step=>step.dataset.stepStage==='create');
   check(createStep.querySelector('[data-function="create_task"]') &&
     !card.querySelector('[data-function-code^="run_"]'),'The core reader should keep internal functions only');
   const storeStep=steps.find(step=>step.dataset.stepStage==='store');
   for(const name of ['load','save','list'])
    check(storeStep.querySelector('[data-function="'+name+'"]'),'The storage diagram misses '+name);
   for(const step of steps) {
    const rect=step.querySelector('rect').getBBox();
    for(const label of step.querySelectorAll('text[data-function]')) {
     const box=label.getBBox();
     check(box.x>=rect.x+3 && box.x+box.width<=rect.x+rect.width-3 &&
       box.y>=rect.y && box.y+box.height<=rect.y+rect.height,'Function name escapes its core node');
     check(step.dataset.codeFunctions.split(' ').includes(label.dataset.function),
       'The visible function does not link to its code: '+label.dataset.function);
    }
   }
   for(const step of steps) for(const name of step.dataset.codeFunctions.split(' '))
    check(card.querySelector('[data-function-code="'+name+'"]'),'Missing source '+name);
   const claim=steps.find(step=>step.dataset.stepStage==='claim');
   claim.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
   check(card.querySelector('[data-function-code="claim_task"]').classList.contains('is-function-selected'),
     'Claim step and code are not connected');
  }
  root.querySelector('[data-explorer-trace]').click();await pause();
  check(panel.hidden && svg.dataset.connectionSelection==='task-files','Trace-only task storage lost selection');
  check(svg.querySelector('[data-from="task-store"][data-to="task-files"]').classList.contains('is-related'),
    'Task file writes are not highlighted');
  root.querySelector('[data-explorer-reset]').click();await pause();
  check(!svg.querySelector('.is-related, .is-unrelated'),'Task reset retained arrows');
  check(baseline.outerHTML===original,'Task interaction changed the S09 review');
  check(document.documentElement.scrollWidth<=innerWidth,'Task page overflows');
  const ids=[...document.querySelectorAll('[id]')].map(node=>node.id);
  check(ids.length===new Set(ids).size,'Task details have duplicate IDs');
  result.passed=true;
 }catch(error){result.error=error.message;}
 const out=document.createElement('pre');out.id='s08-test-result';out.textContent=JSON.stringify(result);document.body.append(out);
});
</script>
"""

class TaskBehavior(shared.ExplorerBehavior):
    chapter = 's10'
    probe = TASK_PROBE
    test_without_enhancement = None

class TaskExcerpts(unittest.TestCase):
    def test_core_functions_match_local_source(self):
        source = shared.Path('/home/fredkeira/projects/learn-claude-code/s10_task_system/code.py')
        if not source.exists():
            self.skipTest('Local teaching source is required for excerpt comparison')
        tree = ast.parse(source.read_text())
        expected = {node.name: ast.dump(node) for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        article = (shared.REPO/'content/projects/learn-claude-code/s10/_index.md').read_text()
        matches = set()
        for block in re.findall(r'```python\n(.*?)\n```',article,re.S):
            try:
                parsed = ast.parse(block)
            except SyntaxError:
                continue
            for node in ast.walk(parsed):
                if isinstance(node,ast.FunctionDef) and expected.get(node.name)==ast.dump(node):
                    matches.add(node.name)
        self.assertTrue({'create','update_dependencies','_depends_on','save','load','list',
                         'create_task','update_task','load_task','list_tasks','get_task',
                         'incomplete_dependencies','can_start','claim_task','complete_task',
                         'execute_tool','agent_loop'} <= matches, f'Missing exact source functions: {matches}')

if __name__ == '__main__':
    unittest.main()
