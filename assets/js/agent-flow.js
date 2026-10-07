/* Diagram first. Process positions and function identities are separate. */
(() => {
 'use strict';
 document.querySelectorAll('[data-agent-flow]').forEach(root=>{
  if(root.dataset.ready==='true')return;
  const flow=JSON.parse(root.querySelector('[data-flow-data]').textContent),model=flow.mentalModel;
  const nodes=new Map(flow.nodes.map(n=>[n.id,n])),steps=new Map(model.steps.map(s=>[s.id,s]));
  const seen=new Set(),history=[],valid=new Set(flow.nodes.map(n=>n.progressKey));
  let understood=new Set(),current=flow.defaultNodeId,stepId=model.rootId,levelId=model.rootId,view='model',problem=false;
  const key='agent-flow:v1:'+flow.repository+':'+flow.revision+':'+flow.id;root.dataset.storageKey=key;
  try{const stored=JSON.parse(localStorage.getItem(key)||'null');if(stored?.version===1&&Array.isArray(stored.understood))understood=new Set(stored.understood.filter(k=>valid.has(k)));}catch(_){problem=true;}
  function positionSource(){
   const h=root.querySelector('[data-flow-current="'+current+'"] h2');h.tabIndex=-1;h.focus({preventScroll:true});
   window.scrollTo({top:Math.max(0,scrollY+h.getBoundingClientRect().top-root.querySelector('.flow-context').getBoundingClientRect().height-12),behavior:'instant'});
  }
  function positionModel(){
   const h=root.querySelector('[data-model-layer="'+levelId+'"] h2');h.focus({preventScroll:true});
   window.scrollTo({top:Math.max(0,scrollY+h.getBoundingClientRect().top-root.querySelector('.flow-context').getBoundingClientRect().height-12),behavior:'instant'});
  }
  function chooseStepForNode(id){
   const trail=steps.get(stepId).trail,candidates=(nodes.get(id)?.modelStepIds||[]).map(k=>steps.get(k)).filter(Boolean);
   const prefix=t=>{let i=0;while(i<trail.length&&i<t.length&&trail[i]===t[i])i++;return i;};
   candidates.sort((a,b)=>prefix(b.trail)-prefix(a.trail)||a.trail.length-b.trail.length);
   return candidates[0]?.id||model.rootId;
  }
  function source(id,explicitStep){
   if(!nodes.has(id))return;
   const nextStep=explicitStep||chooseStepForNode(id);
   if(view==='source'&&(id!==current||nextStep!==stepId))history.push({current,stepId,levelId});
   current=id;stepId=nextStep;
   if(!explicitStep){const s=steps.get(stepId);levelId=s.childIds.length?s.id:s.parentId||model.rootId;}
   view='source';seen.add(id);render();positionSource();
  }
  function selectStep(id,locate=true){
   const s=steps.get(id);if(!s)return;
   stepId=id;levelId=s.childIds.length?s.id:s.parentId||model.rootId;view='model';render();if(locate)positionModel();
  }
  const svgEl=(name,attrs={})=>{const e=document.createElementNS('http://www.w3.org/2000/svg',name);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,String(v));return e;};
  function draw(){
   const layer=root.querySelector('[data-model-layer="'+levelId+'"]'),step=steps.get(levelId),box=layer.querySelector('.mental-diagram'),svg=box.querySelector('svg');
   const bounds=box.getBoundingClientRect();svg.replaceChildren();svg.setAttribute('viewBox','0 0 '+Math.max(1,bounds.width)+' '+Math.max(1,bounds.height));
   const defs=svgEl('defs'),marker=svgEl('marker',{id:'mental-arrow-'+levelId,viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:6,markerHeight:6,orient:'auto'});
   marker.append(svgEl('path',{d:'M0 0L10 5L0 10Z',fill:'var(--secondary)'}));defs.append(marker);svg.append(defs);
   const rect=id=>{const e=layer.querySelector('[data-model-box="'+id+'"]');if(!e)return null;const r=e.getBoundingClientRect();return{x:r.left-bounds.left,y:r.top-bounds.top,w:r.width,h:r.height};};
   for(const link of step.links){
    const a=rect(link.from),b=rect(link.to);if(!b)continue;
    let d;
    if(!a&&link.from===step.id)d='M'+(bounds.width/2)+' 8V24H'+(b.x+b.w/2)+'V'+b.y;
    else if(a&&Math.abs(a.y-b.y)<12)d='M'+(a.x+a.w)+' '+(a.y+a.h/2)+'H'+b.x;
    else if(a){const lane=a.y+a.h+18;d='M'+(a.x+a.w/2)+' '+(a.y+a.h)+'V'+lane+'H'+(b.x+b.w/2)+'V'+b.y;}
    else continue;
    const path=svgEl('path',{d,fill:'none',stroke:'var(--secondary)','stroke-width':1.5,'marker-end':'url(#mental-arrow-'+levelId+')','data-model-link':link.from+':'+link.to,'data-kind':link.kind});
    const title=svgEl('title');title.textContent=link.label||'下一步';path.append(title);svg.append(path);
    if(link.label&&link.kind==='branch'){const text=svgEl('text',{x:b.x+b.w/2,y:36,'text-anchor':'middle','font-size':11,fill:'var(--primary)'});text.textContent=link.label;svg.append(text);}
   }
  }
  function render(){
   const node=nodes.get(current),s=steps.get(stepId);root.dataset.view=view;root.dataset.currentNode=current;root.dataset.currentStep=stepId;root.dataset.currentLayer=levelId;
   root.querySelectorAll('[data-model-layer]').forEach(e=>e.hidden=e.dataset.modelLayer!==levelId);
   root.querySelector('[data-mental-model]').hidden=view!=='model';root.querySelector('.flow-layout').hidden=view!=='source';
   root.querySelector('[data-source-location]').hidden=view!=='source';
   root.querySelector('[data-flow-path]').textContent=node.source.path+' › '+node.source.symbol;root.querySelector('[data-flow-current-label]').textContent='当前：'+node.label;
   root.querySelector('[data-flow-back]').disabled=view!=='source'||!history.length;
   root.querySelector('[data-flow-map-return]').disabled=view==='model';
   const trail=root.querySelector('[data-model-trail]');trail.replaceChildren();
   for(const id of s.trail){const parent=steps.get(id),button=document.createElement('button');button.type='button';button.textContent=(parent.number?parent.number+' ':'')+parent.label;button.addEventListener('click',()=>selectStep(id));trail.append(button);}
   root.querySelectorAll('[data-model-step]').forEach(e=>e.setAttribute('aria-current',e.dataset.modelStep===stepId?'step':'false'));
   root.querySelectorAll('[data-flow-current]').forEach(e=>e.hidden=view!=='source'||e.dataset.flowCurrent!==current);
   root.querySelectorAll('[data-function-id]').forEach(button=>{const n=nodes.get(button.dataset.functionId);if(view==='source'&&n.id===current)button.setAttribute('aria-current','location');else button.removeAttribute('aria-current');button.querySelector('[data-function-status]').textContent=understood.has(n.progressKey)?'能解释':seen.has(n.id)?'看过':'未打开';});
   root.querySelectorAll('[data-flow-folder]').forEach(folder=>{const active=view==='source'&&node.source.path.startsWith(folder.dataset.flowFolder+'/');folder.classList.toggle('is-current-folder',active);if(active)folder.open=true;});
   root.querySelectorAll('[data-flow-file]').forEach(file=>{const active=view==='source'&&file.dataset.flowFile===node.source.path;file.classList.toggle('is-current-file',active);if(active)file.open=true;});
   root.querySelectorAll('[data-flow-understood]').forEach(input=>input.checked=understood.has(nodes.get(input.dataset.flowUnderstood).progressKey));root.querySelectorAll('[data-flow-save-status]').forEach(e=>e.textContent=problem?'本机保存不可用，本次暂存。':'');
   if(view==='model')draw();
  }
  root.querySelectorAll('[data-model-step]').forEach(button=>button.addEventListener('click',()=>selectStep(button.dataset.modelStep)));
  root.querySelectorAll('[data-model-source], [data-model-open-source]').forEach(button=>button.addEventListener('click',()=>{const id=button.dataset.modelSource||button.dataset.modelOpenSource,s=steps.get(id);if(s.nodeId){stepId=id;source(s.nodeId,id);}}));
  root.querySelectorAll('[data-flow-target]').forEach(button=>button.addEventListener('click',()=>source(button.dataset.flowTarget)));
  root.querySelectorAll('[data-function-id]').forEach(button=>button.addEventListener('click',()=>source(button.dataset.functionId)));
  root.querySelector('[data-flow-map-root]').addEventListener('click',()=>selectStep(model.rootId));
  root.querySelector('[data-flow-map-return]').addEventListener('click',()=>{view='model';render();positionModel();});
  root.querySelector('[data-flow-back]').addEventListener('click',()=>{if(!history.length)return;({current,stepId,levelId}=history.pop());view='source';render();positionSource();});
  root.querySelectorAll('[data-flow-understood]').forEach(input=>input.addEventListener('change',()=>{const k=nodes.get(input.dataset.flowUnderstood).progressKey;if(input.checked)understood.add(k);else understood.delete(k);try{localStorage.setItem(key,JSON.stringify({version:1,understood:[...understood]}));problem=false;}catch(_){problem=true;}render();}));
  window.addEventListener('resize',()=>{if(view==='model')draw();});
  if(matchMedia('(max-width:860px)').matches)root.querySelector('.flow-tree-toggle').open=false;
  root.dataset.ready='true';render();
 });
})();
