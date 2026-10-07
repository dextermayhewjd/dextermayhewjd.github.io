/* Small lesson self-checks. Visiting or expanding content does not save progress. */
(() => {
  'use strict';
  document.querySelectorAll('[data-agent-course]').forEach(root => {
    if(root.dataset.ready==='true')return;
    const course=JSON.parse(root.querySelector('[data-agent-course-data]').textContent);
    const key='agent-course:v1:'+course.repository+':'+course.revision+':'+course.id;
    const byId=new Map(course.lessons.map(l=>[l.id,l]));
    const valid=new Set(course.lessons.map(l=>l.progressKey));let checked=new Set(),problem=false;
    root.dataset.storageKey=key;
    function read(){
      try{const record=JSON.parse(localStorage.getItem(key)||'null');
        checked=new Set(record?.version===1&&Array.isArray(record.checked)?record.checked.filter(k=>valid.has(k)):[]);problem=false;
      }catch(_){checked=new Set();problem=true;}
    }
    const done=id=>checked.has(byId.get(id)?.progressKey);
    const svgEl=(name,attrs={})=>{const e=document.createElementNS('http://www.w3.org/2000/svg',name);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,String(v));return e;};
    function diagram(){
      const target=root.querySelector('[data-agent-learned-map]');if(!target)return;
      target.replaceChildren();const nodes=course.modules.filter(m=>m.lessonIds.some(done));
      if(!nodes.length){const p=document.createElement('p');p.textContent='从第一课开始。显式勾选后，这里显示你已学的模块。';target.append(p);return;}
      const w=760,h=Math.ceil(nodes.length/2)*100+22,svg=svgEl('svg',{viewBox:'0 0 '+w+' '+h,role:'img','aria-label':'已学模块与先后阅读关系'});
      const positions=new Map(nodes.map((m,i)=>[m.path,{x:16+(i%2)*376,y:16+Math.floor(i/2)*100}]));
      const relations=new Set();
      for(const l of course.lessons.filter(l=>done(l.id)))for(const p of l.prerequisites||[]){
        if(!done(p))continue;
        const from=nodes.find(m=>m.lessonIds.includes(p)),to=nodes.find(m=>m.lessonIds.includes(l.id));
        if(!from||!to||from===to)continue;const id=from.path+'→'+to.path;if(relations.has(id))continue;relations.add(id);
        const a=positions.get(from.path),b=positions.get(to.path),path=svgEl('path',{d:'M'+(a.x+166)+' '+(a.y+68)+' V'+(a.y+82)+' H'+(b.x+166)+' V'+b.y,fill:'none',stroke:'var(--secondary)','stroke-width':1.2});
        const title=svgEl('title');title.textContent='先修关系：'+from.label+' → '+to.label;path.append(title);svg.append(path);
      }
      for(const m of nodes){const p=positions.get(m.path),g=svgEl('g',{'data-module-node':m.path});
        g.append(svgEl('rect',{x:p.x,y:p.y,width:332,height:68,rx:7,fill:'var(--code-bg)',stroke:'var(--border)'}));
        const label=svgEl('text',{x:p.x+12,y:p.y+27,fill:'var(--primary)','font-size':14});label.textContent=m.label;g.append(label);
        const count=svgEl('text',{x:p.x+12,y:p.y+49,fill:'var(--secondary)','font-size':11});count.textContent=m.lessonIds.filter(done).length+'/'+m.lessonIds.length+' 个课程目标已勾选（自报）';g.append(count);svg.append(g);
      }target.append(svg);
    }
    function render(){
      root.querySelectorAll('[data-lesson-status]').forEach(e=>e.textContent=done(e.dataset.lessonStatus)?'已学':'未学');
      const lesson=byId.get(root.dataset.lessonId),input=root.querySelector('[data-agent-confirm]');if(input&&lesson)input.checked=done(lesson.id);
      const message=root.querySelector('[data-agent-save-status]');if(message)message.textContent=problem?'本机保存不可用，本次暂存。':'';
      root.querySelectorAll('[data-module-progress]').forEach(e=>{
        const m=course.modules.find(m=>m.path===e.dataset.moduleProgress),n=m.lessonIds.filter(done).length;
        e.querySelector('[data-module-status]').textContent=!n?'未学':n===m.lessonIds.length?'本课程目标完成':'部分完成 '+n+'/'+m.lessonIds.length;
        e.querySelector('[data-module-remaining]').textContent='待学：'+m.lessonIds.filter(id=>!done(id)).map(id=>byId.get(id)?.title||id).join('、');
      });diagram();
    }
    read();
    const input=root.querySelector('[data-agent-confirm]');if(input)input.addEventListener('change',()=>{
      const lesson=byId.get(root.dataset.lessonId);if(input.checked)checked.add(lesson.progressKey);else checked.delete(lesson.progressKey);
      try{localStorage.setItem(key,JSON.stringify({version:1,checked:[...checked]}));problem=false;}catch(_){problem=true;}render();
    });
    window.addEventListener('storage',event=>{if(event.key===key){read();render();}});
    window.addEventListener('focus',()=>{read();render();});root.dataset.ready='true';render();
  });
})();
