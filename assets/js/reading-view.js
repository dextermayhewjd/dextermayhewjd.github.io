/* Optional DOM adapter for learning-pack v1. Selection never confirms learning. */
(() => {
  'use strict';
  const names = {unread:'未记录自检',partial:'部分完成', 'scope-complete':'本章范围完成（自报）','out-of-scope':'本章未纳入'};
  function attach(root, config) {
    if (root.dataset.readingReady === 'true') return;
    const model = window.ReadingProgress.create(config);
    const key = 'reading-progress:v1:' + config.repository + ':' + config.revision + ':' + config.chapterId;
    const saveStatus = root.querySelector('[data-reading-save-status]');
    let selectedFile = '', storageProblem = false, describedGoal = '';
    root.dataset.readingStorageKey = key;
    try {
      const value = localStorage.getItem(key);
      if (value) model.restore(JSON.parse(value));
    } catch (_) { storageProblem = true; }
    const figures = () => [root, ...[...document.querySelectorAll('[data-function-explorer]')]
      .filter(node => node.dataset.functionExplorer === root.id && !root.contains(node))];
    const currentGoal = () => model.goals.find(goal => goal.id === model.goalId);
    function save() {
      try { localStorage.setItem(key,JSON.stringify(model.snapshot())); storageProblem = false; }
      catch (_) { storageProblem = true; }
    }
    const button = (text, action, attr, value) => {
      const item = document.createElement('button');item.type='button';item.textContent=text;
      if (attr) item.setAttribute(attr,value);item.addEventListener('click',action);return item;
    };
    const views = root.querySelector('[data-reading-views]');
    for (const view of config.views) views.append(button(view.label, () => { model.selectView(view.id);sync(); },'data-reading-view',view.id));
    const steps = root.querySelector('[data-reading-steps]');
    for (const goal of model.goals) {
      const item = button(goal.label, () => { model.selectGoal(goal.id);sync(); },'data-reading-step',goal.id);
      item.dataset.viewId=goal.viewId;steps.append(item);
    }
    const checks = root.querySelector('[data-reading-checks]');
    for (const goal of model.goals) {
      const label = document.createElement('label');label.dataset.viewId=goal.viewId;
      const input = document.createElement('input');input.type='checkbox';input.dataset.readingGoal=goal.id;
      input.addEventListener('change', () => { model.checkGoal(goal.id,input.checked);save();sync(); });
      label.append(input,document.createTextNode(' 已理解本步（自报）：' + goal.label + ' · ' + goal.depth));checks.append(label);
    }
    root.querySelector('[data-reading-clear]').addEventListener('click', () => {
      model.clear();try { localStorage.removeItem(key);storageProblem=false; } catch (_) { storageProblem=true; }sync();
    });
    function chooseFile(path) {
      selectedFile=path;root.dataset.readingSelectedFile=path;sync();
    }
    root.querySelectorAll('[data-reading-file]').forEach(item => item.addEventListener('click', () => chooseFile(item.dataset.readingFile)));
    root.querySelector('[data-reading-file-search]').addEventListener('input', event => {
      const query=event.target.value.trim().toLocaleLowerCase();let count=0;
      root.querySelectorAll('[data-file-row]').forEach(row=>{
        row.hidden=!row.dataset.fileRow.toLocaleLowerCase().includes(query);if(!row.hidden)count++;
      });
      root.querySelector('[data-reading-file-count]').textContent=count+' / '+config.inventory.length+' 个路径；筛选不改变进度';
    });
    root.addEventListener('diagram:selection', event => {
      const node=[...root.querySelectorAll('a[data-module]')].find(link => link.dataset.module === event.detail.module);
      if (node) chooseFile(node.querySelector('[data-file-path]')?.dataset.filePath || '');
      else { selectedFile='';root.dataset.readingSelectedFile='';sync(); }
    });
    root.addEventListener('diagram:function-selected', event => {
      const ref=config.references[event.detail.name];if(ref?.available) chooseFile(ref.path);
    });
    root.addEventListener('diagram:populated', () => sync());
    function describe() {
      const goal=currentGoal();
      if(describedGoal===goal.id)return;
      describedGoal=goal.id;
      const box=root.querySelector('[data-reading-description]');box.replaceChildren();
      const title=document.createElement('strong');title.textContent=goal.label + ' · ' + goal.depth;box.append(title);
      for (const [name,value] of [['问题与作用',goal.summary],['输入',goal.inputs],['输出',goal.returns],['副作用',goal.effect],['条件',goal.condition]]) {
        const p=document.createElement('p');p.textContent=name + '：' + (typeof value==='string' ? value : JSON.stringify(value ?? ''));box.append(p);
      }
      for (const [name,id] of [['调用处',goal.caller],['实现处',goal.callee]]) {
        const ref=config.references[id];if(!ref)continue;
        const item=button(name + '：' + (ref.symbol || ref.label), event => root.openReadingSource?.(id,event.currentTarget), 'data-reading-source',id);
        if(!ref.available){item.disabled=true;item.title=ref.reason;}
        box.append(item);
        if(!ref.available){const p=document.createElement('p');p.textContent=ref.reason;box.append(p);}
      }
    }
    function sync() {
      const goal=currentGoal(),active=[goal.caller,goal.callee].map(id=>config.references[id]).filter(ref=>ref?.available);
      root.querySelectorAll('[data-reading-view]').forEach(item=>item.setAttribute('aria-pressed',String(item.dataset.readingView===model.viewId)));
      root.querySelectorAll('[data-reading-step]').forEach(item=>{
        item.hidden=item.dataset.viewId!==model.viewId;item.setAttribute('aria-pressed',String(item.dataset.readingStep===model.goalId));
      });
      root.querySelectorAll('[data-reading-checks] label').forEach(label=>label.hidden=label.dataset.viewId!==model.viewId);
      root.querySelectorAll('[data-reading-goal]').forEach(input=>input.checked=model.checked.has(input.dataset.readingGoal));
      root.querySelectorAll('[data-file-row]').forEach(row=>{
        const info=model.fileStatus(row.dataset.fileRow);row.dataset.readingState=info.status;
        row.querySelector('[data-file-progress]').textContent=names[info.status] + (info.total ? ' '+info.completed+'/'+info.total+' 个 trace 范围目标' : '');
        row.querySelector('[data-file-uncovered]').textContent=info.uncovered.length ? ' · 本章未覆盖定义：'+info.uncovered.map(fn=>fn.symbol).join('、') : '';
        row.querySelector('[data-reading-file]').setAttribute('aria-pressed',String(row.dataset.fileRow===selectedFile));
      });
      for (const figure of figures()) {
        figure.setAttribute('data-reading-mode','');
        figure.querySelectorAll('rect[data-stage][data-file-path]').forEach(node=>{
          const path=node.dataset.filePath;node.dataset.readingState=model.fileStatus(path).status;
          node.dataset.readingFocus=String(goal.files.includes(path));
        });
        figure.querySelectorAll('g[data-file-path]').forEach(group=>{
          group.classList.toggle('is-reading-file-selected',group.dataset.filePath===selectedFile);
          const relevant=model.goals.filter(g=>g.files.includes(group.dataset.filePath));
          group.setAttribute('aria-label',group.dataset.filePath+'：'+names[model.fileStatus(group.dataset.filePath).status]+'；'+relevant.length+'个本章目标');
        });
        figure.querySelectorAll('rect[data-source-ref]').forEach(node=>{
          const base=config.references[node.dataset.sourceRef];
          if(!base?.available){node.dataset.readingState='out-of-scope';node.dataset.readingFocus=String(goal.caller===node.dataset.sourceRef||goal.callee===node.dataset.sourceRef);return;}
          const ref=active.find(r=>r.path===base.path&&r.symbol===base.symbol);
          node.dataset.readingState=model.functionStatus(base.path,base.symbol).status;
          node.dataset.readingFocus=String(!!ref);
        });
      }
      for(const figure of figures())figure.querySelectorAll('path[data-goal-ids]').forEach(path=>{
        path.dataset.readingActive=String(path.dataset.goalIds.split(' ').includes(model.goalId));
      });
      saveStatus.textContent=storageProblem ? '本机记录不可用；仍可阅读，本次自检暂存在当前页面。'
        : '自检记录仅保存在本机，代表本章 trace 范围自报；点击、阶段切换和恢复视图不写记录。';
      describe();
    }
    root.querySelector('[data-reading-controls]').hidden=false;
    root.dataset.readingReady='true';root.readingController={model,sync};sync();
  }
  window.ReadingView={attach};
})();
