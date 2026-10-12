"""The progressive S16 lesson keeps the opening overview and exact source reader."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

import test_s08_explorer as shared

ROOT = Path(__file__).resolve().parents[1]

PROBE = r'''
<script>
window.addEventListener('load', async () => {
  const result={passed:false};
  const check=(ok,message)=>{if(!ok)throw Error(message)};
  const pause=()=>new Promise(resolve=>setTimeout(resolve,50));
  try {
    const root=document.getElementById('s16-overview-explorer');
    check(root?.dataset.ready==='true','Opening overview did not initialize');
    check(!document.getElementById('s16-workflow-explorer'),'Old lesson explorer is still present');
    const template=document.querySelector('[data-workflow-detail-template]');
    const templateHTML=template.innerHTML;
    const sourceLibrary=document.querySelector('[data-function-source-library]');
    check(sourceLibrary?.hidden,'Source reference library must stay out of the lesson flow');
    const svg=root.querySelector('svg');
    const canvas=root.querySelector('.architecture-diagram__canvas');
    check(svg.viewBox.baseVal.width===1400,'Unexpected overview geometry');
    check(root.querySelectorAll('[data-module-button]').length===5,'Expected five source entry points');
    check(!svg.querySelector('[data-evolution-legend]'),'Inline legend should be replaced by the adjacent Hugo legend');
    const legend=root.querySelector('[data-scheme="workflow"]');
    check(legend?.textContent.includes('异常向外传播'),'Missing exception legend');
    check(!legend.textContent.includes('职责迁移'),'Workflow orange must not mean an architectural modification');
    check(document.getElementById('workflow-map').compareDocumentPosition(root)&Node.DOCUMENT_POSITION_FOLLOWING,'Overview is outside the opening map section');
    check(root.compareDocumentPosition(document.getElementById('workflow-first-call'))&Node.DOCUMENT_POSITION_FOLLOWING,'Overview must precede the progressive lesson');
    const reveal=node=>{node.scrollIntoView({block:'center',behavior:'instant'});};
    const lookup=svg.querySelector('rect[data-stage="lookup"]');
    reveal(lookup);await pause();
    const b=lookup.getBoundingClientRect();
    svg.dispatchEvent(new PointerEvent('pointermove',{pointerType:'mouse',clientX:b.left+b.width/2,clientY:b.top+b.height/2,bubbles:true}));
    check(svg.dataset.connectionSelection==='lookup','Hover selected a group instead of the lookup node');
    check(svg.querySelector('[data-from="lookup"][data-to="cached"]').classList.contains('is-related'),'Cache hit path missing from hover');
    check(svg.querySelector('[data-from="lookup"][data-to="request"]').classList.contains('is-related'),'Cache miss path missing from hover');
    svg.dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'}));
    check(!svg.querySelector('.is-related, .is-unrelated'),'Hover did not clear');
    const expected={entry:'run_workflow',script:'sample_workflow',agent:'agent',journal:'key',finish:'_call_locked'};
    for(const [key,fn] of Object.entries(expected)){
      const node=svg.querySelector('a[data-module="'+key+'"]');
      check(node,'Missing module link '+key);reveal(node);await pause();
      const scroll=scrollY;
      node.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));await pause();
      const card=root.querySelector('[data-module-card="'+key+'"]');
      check(card.open,'Keyboard did not open '+key);
      const code=card.querySelector('[data-function-code="'+fn+'"]');
      check(code,'Source is missing for '+key);
      const canonical=sourceLibrary.querySelector('[data-function-source="'+fn+'"] pre code');
      check(canonical&&code.querySelector('pre code').textContent===canonical.textContent,'Detail reader differs from the pinned full method');
      if(key==='script')check(code.textContent.includes('ctx.pipeline(DIMENSIONS, audit, verify)'),'Full sample workflow is missing');
      if(key==='agent')check(code.textContent.includes('self._limits.claim_agent()')&&code.textContent.includes('self.journal.cached(key)'),'Full agent implementation is missing');
      check(root.querySelectorAll('[data-module-card][open]').length===1,'More than one detail is open');
      check(scrollY===scroll,'Opening details scrolled the page');
      const panel=root.querySelector('[data-explorer-panel]');
      const p=panel.getBoundingClientRect(), a=node.getBoundingClientRect();
      check(p.left>=0&&p.top>=0&&p.right<=innerWidth+1&&p.bottom<=innerHeight+1,'Panel outside viewport');
      check(!(p.left<a.right&&p.right>a.left&&p.top<a.bottom&&p.bottom>a.top),'Panel covers selected source entry');
      const before=p.width;
      root.querySelector('[data-panel-enlarge]').click();await pause();
      check(panel.getBoundingClientRect().width>=before,'Enlarge did not expand the reader');
      root.querySelector('[data-panel-size-reset]').click();await pause();
      document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));await pause();
      check(panel.hidden&&!card.open,'Escape did not close the reader');
    }
    const complete=document.querySelector('#workflow-complete-script a[data-function="sample_workflow"]');
    check(complete,'Missing complete workflow entry after the gradual example');
    reveal(complete);await pause();
    const sourceScroll=scrollY;
    complete.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));await pause();
    const full=root.querySelector('[data-module-card="script"][open] [data-function-code="sample_workflow"]');
    check(full?.classList.contains('is-function-selected'),'Direct entry did not select the full workflow');
    check(full.querySelector('pre code').textContent===sourceLibrary.querySelector('[data-function-source="sample_workflow"] pre code').textContent,'Direct entry showed a different workflow');
    check(scrollY===sourceScroll,'Direct source entry moved the article');
    document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));await pause();
    check(template.innerHTML===templateHTML,'Interaction changed the hidden detail source');
    const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);
    check(ids.length===new Set(ids).size,'Duplicate element IDs');
    check(document.documentElement.scrollWidth<=innerWidth,'Page has horizontal overflow');
    check(canvas.scrollWidth>=1400,'Narrow view shrank the text instead of allowing scrolling');
    result.passed=true;
  }catch(error){result.error=error.message}
  const report=document.createElement('pre');report.id='s08-test-result';report.textContent=JSON.stringify(result);document.body.append(report);
});
</script>
'''

class ClosingOverviewBehavior(shared.ExplorerBehavior):
    chapter='s16'
    probe=PROBE
    test_without_enhancement=None

class ClosingOverviewSource(unittest.TestCase):
    def test_inline_svgs_use_distinct_ids(self):
        base=ROOT/'content/projects/learn-claude-code/s16/images'
        names=['workflow-step-01-agent.svg','workflow-step-02-schema.svg',
               'workflow-step-03-verdict.svg','workflow-step-04-loop-filter.svg',
               'workflow-runtime-overview.svg','workflow-core.svg']
        seen=set()
        for name in names:
            root=ET.parse(base/name).getroot()
            ids=[node.get('id') for node in root.iter() if node.get('id')]
            self.assertEqual(len(ids),len(set(ids)),name)
            self.assertFalse(seen.intersection(ids),f'Duplicate inline IDs in {name}')
            seen.update(ids)

    def test_graph_contract_and_scoped_styles(self):
        path=ROOT/'content/projects/learn-claude-code/s16/images/workflow-runtime-overview.svg'
        svg=ET.parse(path).getroot()
        ns={'s':'http://www.w3.org/2000/svg'}
        stages=[node.get('data-stage') for node in svg.findall('.//s:rect[@data-stage]',ns)]
        self.assertEqual(len(stages),len(set(stages)))
        for edge in svg.findall('.//s:path[@data-from]',ns):
            self.assertIn(edge.get('data-from'),stages)
            self.assertIn(edge.get('data-to'),stages)
            self.assertTrue(edge.get('data-label'))
            self.assertTrue(edge.get('stroke'))
            self.assertTrue(edge.get('marker-end'))
        for selector in re.findall(r'([^{}]+)\{',svg.find('s:style',ns).text):
            self.assertTrue(all(part.strip().startswith('.workflow-runtime-overview ') for part in selector.split(',')))
        page=(ROOT/'content/projects/learn-claude-code/s16/_index.md').read_text()
        self.assertLess(page.index('## 整体过程'),page.index('{{< architecture-explorer'))
        self.assertLess(page.index('{{< architecture-explorer'),page.index('## 1. '))
        self.assertEqual(page.count('{{< architecture-explorer'),1)
        self.assertIn('对照[开篇总图](#workflow-map)',page)

if __name__=='__main__':
    unittest.main()
