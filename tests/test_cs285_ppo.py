"""Lecture 9: explicit change of measure, local approximation, and PPO clipping."""
import test_cs285_lecture as shared

PROBE = r'''<script>
window.addEventListener('load', () => {
 const result={passed:false};
 const check=(value,why)=>{if(!value)throw new Error(why)};
 try {
  const root=document.querySelector('[data-lecture-flow]');
  check(root?.dataset.ready==='true','Lecture 9 flow did not initialize');
  const chain=['old-policy','mismatch','is-integral','insert-ratio','match-q','is-identity','off-objective','trajectory-ratio','differentiate','corrected-gradient','causal-objective','product-risk','joint-ratio','state-bridge','local-surrogate','surrogate-gradient','off-policy-loop','weight-spread','clip','plain-clip','min'];
  for(let i=1;i<chain.length;i++)check(root.querySelector('[data-from="'+chain[i-1]+'"][data-to="'+chain[i]+'"]'),'Missing reasoning step '+chain[i]);
  const loops=[...root.querySelectorAll('a[data-flow-loop]')];
  check(loops.length===3,'Expected three complete algorithm groups');
  for(const key of ['old-policy','off-policy-loop','update']){
   check(root.querySelector('[data-flow-node="'+key+'"][data-flow-loop]'),'Complete algorithm is not grouped '+key);
   check(root.querySelector('[data-from="'+key+'"][data-to="'+key+'"]'),'Algorithm sampling loop missing '+key);
   const math=root.querySelector('[data-inline-formula="'+key+'"]').textContent;
   const steps=key==='old-policy'?6:8;
   for(let step=1;step<=steps;step++)check(math.includes(step+'.'),'Missing numbered formula '+step+' in '+key);
  }
  for(let step=1;step<=6;step++)check(document.getElementById('on-policy-step-'+step),'Missing original loop step '+step);
  for(const key of ['positive','negative']){
   check(root.querySelector('[data-from="min"][data-to="'+key+'"]'),'Missing advantage-sign branch '+key);
   check(root.querySelector('[data-from="'+key+'"][data-to="ppo"]'),'Sign branch does not join PPO');
  }
  check(root.querySelector('[data-from="ppo"][data-to="update"]'),'PPO update loop missing');
  for(const id of [...Array.from({length:13},(_,i)=>'formula-'+(i+1)),'formula-10b','score-detail','causality-detail','first-order-detail','clip-detail','clip-cases'])check(document.getElementById(id),'Missing note section '+id);
  const nodes=[...root.querySelectorAll('[data-flow-node]')];
  for(const node of nodes){
   const formula=root.querySelector('[data-inline-formula="'+node.dataset.flowNode+'"]');
   check(formula?.getBoundingClientRect().height>0,'No adjacent formula for '+node.dataset.flowNode);
   check(node.hasAttribute('data-flow-loop')||!formula.textContent.includes('begin{aligned}'),'Individual reasoning formula should stay on one line');
   check(document.querySelector(node.getAttribute('href')),'Broken chapter route');
  }
  const regions=[...root.querySelectorAll('foreignObject')].map(n=>n.getBoundingClientRect());
  for(let i=0;i<regions.length;i++)for(let j=i+1;j<regions.length;j++){
   const a=regions[i],b=regions[j];
   check(a.right<=b.left||b.right<=a.left||a.bottom<=b.top||b.bottom<=a.top,'Formula regions overlap');
  }
  check(!root.textContent.includes('u_t'),'Unexpected gradient shorthand');
  const first=nodes[0],url=location.href,y=scrollY;
  first.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
  check(location.hash===first.getAttribute('href'),'Node did not navigate to its detailed explanation');
  history.replaceState(null,'',url);window.scrollTo({top:y,behavior:'instant'});
  first.focus({preventScroll:true});
  check(root.querySelector('[data-to="old-policy-formula"].is-related'),'Keyboard formula trace missing');
  first.blur();
  for(const link of document.querySelectorAll('.post-content a[href^="#"]')){
   const hash=link.getAttribute('href');check(document.getElementById(decodeURIComponent(hash.slice(1))),'Missing anchor '+hash);
  }
  for(const lecture of ['02','05','09'])check(document.querySelector('.project-nav a[href="/courses/cs285/lecture-'+lecture+'/"]'),'Course navigation missing Lecture '+lecture);
  const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);check(ids.length===new Set(ids).size,'Duplicate IDs');
  check(document.documentElement.scrollWidth<=innerWidth,'Page overflows');
  const rect=first.querySelector('rect'),light=getComputedStyle(rect).fill;
  document.documentElement.dataset.theme='dark';check(getComputedStyle(rect).fill!==light,'Dark theme missing');
  result.passed=true;
 }catch(error){result.error=error.message}
 const out=document.createElement('pre');out.id='lecture-test-result';out.textContent=JSON.stringify(result);document.body.append(out);
});</script>'''

class PPOReading(shared.LectureReading):
    route='courses/cs285/lecture-09'
    probe=PROBE

    def test_proof_fragment(self):
        self.browser_check(1600,'#clip-cases')
