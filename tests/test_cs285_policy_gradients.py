"""Lecture 5: the derivation, variance remedies and implementation are connected."""
import test_cs285_lecture as shared

PROBE = r'''<script>
window.addEventListener('load', () => {
  const result = {passed: false};
  const check = (value, why) => { if (!value) throw new Error(why); };
  try {
    const root = document.querySelector('[data-lecture-flow]');
    check(root?.dataset.ready === 'true', 'Policy gradient flow did not initialize');
    const chain = ['objective','trajectory','expand-expectation','differentiate','log-trick','substitute','match-expectation','expectation','log-trajectory','score','policy-gradient','reinforce','variance'];
    for (let i=1;i<chain.length;i++) check(root.querySelector('[data-from="'+chain[i-1]+'"][data-to="'+chain[i]+'"]'), 'Missing derivation link '+chain[i]);
    for (const key of ['baseline','causality']) check(root.querySelector('[data-from="variance"][data-to="'+key+'"]'), 'Missing variance remedy '+key);
    for (let i=1;i<=14;i++) check(document.getElementById('formula-'+i), 'Lost formula '+i);
    check(document.getElementById('log-derivative-detail'), 'Missing chain rule close reading');
    for (const id of ['expectation-to-integral','differentiate-integral','substitute-identity','match-expectation','back-to-expectation']) check(document.getElementById(id), 'Missing explicit conversion step '+id);
    check(!document.querySelector('.post-content').textContent.includes('u_t'), 'Unrequested gradient abbreviation remains');
    check(root.querySelector('[data-inline-formula="score"]').textContent.includes('log\\pi'), 'Per-step gradient should remain written in full');
    const nodes=[...root.querySelectorAll('[data-flow-node]')];
    for (const node of nodes) {
      const key=node.dataset.flowNode, formula=root.querySelector('[data-inline-formula="'+key+'"]');
      check(formula?.getBoundingClientRect().height>0, 'Formula is not visible: '+key);
      check(document.querySelector(node.getAttribute('href')), 'Missing detailed section: '+key);
    }
    const regions=[...root.querySelectorAll('foreignObject')].map(node=>node.getBoundingClientRect());
    for(let i=0;i<regions.length;i++) for(let j=i+1;j<regions.length;j++){
      const a=regions[i], b=regions[j];
      check(a.right<=b.left || b.right<=a.left || a.bottom<=b.top || b.bottom<=a.top, 'Formula regions overlap');
    }
    const url=location.href, y=scrollY;
    nodes[0].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
    check(location.hash==='#formula-1','Click does not open detailed formula');
    history.replaceState(null,'',url); window.scrollTo({top:y,behavior:'instant'});
    nodes[0].focus({preventScroll:true});
    check(root.querySelector('[data-to="objective-formula"].is-related'),'Keyboard cannot trace a formula');
    nodes[0].blur();
    for(const link of document.querySelectorAll('.post-content a[href^="#"]')) {
      const hash=link.getAttribute('href');
      check(document.getElementById(decodeURIComponent(hash.slice(1))), 'Broken anchor '+hash);
    }
    check(!root.textContent.includes('一次没错'),'Lecture 2 caption leaked into Lecture 5');
    check(document.querySelector('.project-nav a[href="/courses/cs285/lecture-02/"]'),'Lecture 2 navigation missing');
    check(document.querySelector('.project-nav a[href="/courses/cs285/lecture-05/"]'),'Lecture 5 navigation missing');
    const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);
    check(ids.length===new Set(ids).size,'Duplicate IDs');
    check(document.documentElement.scrollWidth<=innerWidth,'Whole page overflows');
    const shape=nodes[0].querySelector('rect'), light=getComputedStyle(shape).fill;
    document.documentElement.dataset.theme='dark';
    check(getComputedStyle(shape).fill!==light,'Flow does not adapt to dark theme');
    result.passed=true;
  } catch(error) { result.error=error.message; }
  const out=document.createElement('pre');out.id='lecture-test-result';out.textContent=JSON.stringify(result);document.body.append(out);
});</script>'''

class PolicyGradientReading(shared.LectureReading):
    route = 'courses/cs285/lecture-05'
    probe = PROBE

    def test_proof_fragment(self):
        self.browser_check(1600, '#baseline-proof')
