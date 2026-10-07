"""Lecture 10: complete algorithm groups and two trust-region implementation routes."""
import test_cs285_lecture as shared

PROBE = r'''<script>
window.addEventListener('load', () => {
 const result={passed:false};
 const check=(value,why)=>{if(!value)throw new Error(why)};
 try {
  const root=document.querySelector('[data-lecture-flow]');
  check(root?.dataset.ready==='true','Lecture 10 flow did not initialize');
  const chain=['starting-loop','shortcuts','telescoping','conditional-advantage','identity','nested','action-integral','insert-action-ratio','match-action-expectation','old-action-expectation','surrogate','tv','coupling','no-divergence','state-distance','bounded-expectation','return-bound','tv-constraint','pinsker','uniform-kl','average-kl'];
  for(let i=1;i<chain.length;i++)check(root.querySelector('[data-from="'+chain[i-1]+'"][data-to="'+chain[i]+'"]'),'Missing reasoning step '+chain[i]);
  for(const route of [
   ['average-kl','lagrangian','kl-likelihood','penalty-sample','ppo-kl-loop'],
   ['average-kl','linearize','gradient-match','euclidean','kl-zero','fisher','quadratic','natural-direction','natural-step','cg','line-search','trpo-loop']
  ])for(let i=1;i<route.length;i++)check(root.querySelector('[data-from="'+route[i-1]+'"][data-to="'+route[i]+'"]'),'Missing implementation route '+route[i]);
  check(!root.querySelector('[data-from="ppo-kl-loop"][data-to="linearize"]'),'PPO and TRPO should be separate branches');
  for(let i=1;i<=20;i++)check(document.getElementById('formula-'+i),'Missing original formula '+i);
  for(const id of ['starting-loop','coupling-detail','tv-kl-detail','jensen-detail','pinsker-detail','pinsker-recall','fisher-detail','natural-detail','trpo-detail','implementation-loop'])check(document.getElementById(id),'Missing detailed note '+id);
  const groups=[['starting-loop',8],['ppo-kl-loop',8],['trpo-loop',7]];
  check(root.querySelectorAll('a[data-flow-loop]').length===groups.length,'Algorithm steps should be grouped into three frames');
  for(const [key,count] of groups){
   check(root.querySelector('[data-flow-node="'+key+'"][data-flow-loop]'),'Algorithm not grouped '+key);
   check(root.querySelector('[data-from="'+key+'"][data-to="'+key+'"]'),'No sampling return for '+key);
   const formula=root.querySelector('[data-inline-formula="'+key+'"]');
   for(let i=1;i<=count;i++)check(formula.textContent.includes(i+'.'),'Missing algorithm formula '+i+' in '+key);
  }
  const nodes=[...root.querySelectorAll('[data-flow-node]')];
  for(const node of nodes){
   const formula=root.querySelector('[data-inline-formula="'+node.dataset.flowNode+'"]');
   check(formula?.getBoundingClientRect().height>0,'Missing adjacent formula '+node.dataset.flowNode);
   check(node.hasAttribute('data-flow-loop')||!formula.textContent.includes('begin{aligned}'),'Individual formula should remain on one line');
   check(document.querySelector(node.getAttribute('href')),'Broken diagram chapter route');
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
  check(root.querySelector('[data-to="starting-loop-formula"].is-related'),'Keyboard formula trace missing');
  first.blur();
  for(const link of document.querySelectorAll('.post-content a[href^="#"]')){
   check(document.getElementById(decodeURIComponent(link.getAttribute('href').slice(1))),'Broken page anchor');
  }
  for(const lecture of ['02','05','09','10'])check(document.querySelector('.project-nav a[href="/courses/cs285/lecture-'+lecture+'/"]'),'Missing course navigation '+lecture);
  const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);check(ids.length===new Set(ids).size,'Duplicate IDs');
  check(document.documentElement.scrollWidth<=innerWidth,'Page overflows');
  const rect=first.querySelector('rect'),light=getComputedStyle(rect).fill;
  document.documentElement.dataset.theme='dark';check(getComputedStyle(rect).fill!==light,'Dark theme missing');
  result.passed=true;
 }catch(error){result.error=error.message}
 const out=document.createElement('pre');out.id='lecture-test-result';out.textContent=JSON.stringify(result);document.body.append(out);
});</script>'''

class TrustRegionReading(shared.LectureReading):
    route='courses/cs285/lecture-10'
    probe=PROBE

    def test_proof_fragment(self):
        self.browser_check(1600,'#pinsker-detail')
