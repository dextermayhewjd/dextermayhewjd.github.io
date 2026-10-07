"""Complete algorithm frames, direct reading routes, and formula layout for Lectures 6/14."""
import json
import test_cs285_lecture as shared

TEMPLATE=r'''<script>
window.addEventListener('load',()=>{
 const config=CONFIG;
 const result={passed:false},check=(value,why)=>{if(!value)throw new Error(why)};
 try{
  const root=document.querySelector('[data-lecture-flow]');
  check(root?.dataset.ready==='true','Flow did not initialize');
  for(const chain of config.chains)for(let i=1;i<chain.length;i++)check(root.querySelector('[data-from="'+chain[i-1]+'"][data-to="'+chain[i]+'"]'),'Missing relation '+chain[i-1]+' -> '+chain[i]);
  for(let i=1;i<=config.formulas;i++)check(document.getElementById('formula-'+i),'Missing original formula '+i);
  for(const id of config.details)check(document.getElementById(id),'Missing detailed note '+id);
  check(root.querySelectorAll('a[data-flow-loop]').length===config.groups.length,'Algorithms should be grouped');
  for(const [key,count] of config.groups){
   check(root.querySelector('[data-flow-node="'+key+'"][data-flow-loop]'),'Algorithm is not one frame '+key);
   check(root.querySelector('[data-from="'+key+'"][data-to="'+key+'"]'),'Missing return in algorithm '+key);
   const text=root.querySelector('[data-inline-formula="'+key+'"]').textContent;
   for(let i=1;i<=count;i++)check(text.includes(i+'.'),'Missing step '+i+' in '+key);
  }
  const nodes=[...root.querySelectorAll('[data-flow-node]')];
  for(const node of nodes){
   const key=node.dataset.flowNode,formula=root.querySelector('[data-inline-formula="'+key+'"]');
   check(formula?.getBoundingClientRect().height>0,'Missing adjacent formula '+key);
   check(formula.getBoundingClientRect().left>node.getBoundingClientRect().right,'Formula must be to the right');
   check(document.querySelector(node.getAttribute('href')),'Broken reading route');
   check(node.hasAttribute('data-flow-loop')||!formula.textContent.includes('begin{aligned}'),'Single reasoning equation should stay on one line');
  }
  const regions=[...root.querySelectorAll('foreignObject')].map(n=>n.getBoundingClientRect());
  for(let i=0;i<regions.length;i++)for(let j=i+1;j<regions.length;j++){
   const a=regions[i],b=regions[j];
   check(a.right<=b.left||b.right<=a.left||a.bottom<=b.top||b.bottom<=a.top,'Formula regions overlap');
  }
  check(!root.textContent.includes('u_t'),'Unexpected gradient shorthand');
  const first=nodes[0],url=location.href,y=scrollY;
  first.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
  check(location.hash===first.getAttribute('href'),'Node did not navigate to chapter');
  history.replaceState(null,'',url);window.scrollTo({top:y,behavior:'instant'});
  first.focus({preventScroll:true});check(root.querySelector('[data-to="starting-loop-formula"].is-related'),'Keyboard trace missing');first.blur();
  for(const link of document.querySelectorAll('.post-content a[href^="#"]'))check(document.getElementById(decodeURIComponent(link.getAttribute('href').slice(1))),'Broken page anchor');
  for(const lecture of ['02','05','06','09','10','14'])check(document.querySelector('.project-nav a[href="/courses/cs285/lecture-'+lecture+'/"]'),'Course navigation missing '+lecture);
  const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);check(ids.length===new Set(ids).size,'Duplicate IDs');
  check(document.documentElement.scrollWidth<=innerWidth,'Page overflows');
  const rect=first.querySelector('rect'),light=getComputedStyle(rect).fill;
  document.documentElement.dataset.theme='dark';check(getComputedStyle(rect).fill!==light,'Dark mode missing');
  result.passed=true;
 }catch(error){result.error=error.message}
 const out=document.createElement('pre');out.id='lecture-test-result';out.textContent=JSON.stringify(result);document.body.append(out);
});</script>'''

def probe(config):
    return TEMPLATE.replace('CONFIG',json.dumps(config,ensure_ascii=False))

class ActorCriticReading(shared.LectureReading):
    route='courses/cs285/lecture-06'
    probe=probe({
        'formulas':21,
        'details':['starting-loop','bellman-detail','regression-detail','bias-detail','gae-detail','centering-detail','reparameterization-detail','distribution-detail'],
        'groups':[['starting-loop',3],['batch-loop',6],['online-loop',6],['gae-loop',6],['score-loop',5],['path-loop',5]],
        'chains':[
            ['starting-loop','return-noise','q','v','a','bellman','mc-label','regression','bootstrap','discount','batch-loop'],
            ['n-step','weights','td-sum','coefficient','gae','gae-loop'],
            ['replay','q-target','q-fit','actor-proxy'],
            ['actor-proxy','score-integral','score-identity','score-loop'],
            ['actor-proxy','gaussian','noise-expectation','path-gradient','chain-rule','path-loop']
        ]
    })
    def test_proof_fragment(self):
        self.browser_check(1600,'#gae-detail')

class SequencesReading(shared.LectureReading):
    route='courses/cs285/lecture-14'
    probe=probe({
        'formulas':22,
        'details':['irl-loop','llm-ppo-loop','partition-detail','reference-detail','group-detail'],
        'groups':[['starting-loop',6],['irl-loop',5],['rlhf-loop',4],['llm-ppo-loop',8]],
        'chains':[
            ['starting-loop','reward-question'],
            ['reward-question','optimality','irl-likelihood','partition-gradient','partition-density','two-expectations','proposal','cancel-dynamics','irl-loop'],
            ['reward-question','preference','sigmoid','preference-fit','rlhf-loop'],
            ['llm-policy','token-probability','token-gradient','completion-is','td','gae','reference','shaped-reward','clip','llm-ppo-loop'],
            ['token-probability','partial-observation','history']
        ]
    })
    def test_proof_fragment(self):
        self.browser_check(1600,'#reference-detail')
