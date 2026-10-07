/* learning-pack v1: source identity and explicitly reported reading scopes. */
(() => {
  'use strict';
  const fail = message => { throw new Error('阅读合同：' + message); };
  const pathOK = path => typeof path === 'string' && path.length > 0
    && !path.startsWith('/') && !path.includes('\\')
    && !path.split('/').some(part => !part || part === '.' || part === '..');
  function validate(config) {
    if (config.schemaVersion !== 1 || !/^[a-f0-9]{40}$/.test(config.revision || '')) fail('版本或快照无效');
    if (typeof config.chapterId !== 'string' || !config.chapterId) fail('章节 ID 缺失');
    let repository;
    try { repository = new URL(config.repository); } catch (_) { fail('仓库地址无效'); }
    if (repository.protocol !== 'https:' || repository.search || repository.hash) fail('仓库必须使用 HTTPS 地址');
    if (!Array.isArray(config.inventory) || !Array.isArray(config.views) || !config.views.length) fail('文件目录或阶段缺失');
    const paths = new Set();
    for (const file of config.inventory) {
      if (!pathOK(file.path) || paths.has(file.path)) fail('目录含重复或无效路径');
      paths.add(file.path);
    }
    if (!config.files || !config.references) fail('文件或源码引用缺失');
    for (const [id, ref] of Object.entries(config.references)) {
      if (!id || typeof ref.available !== 'boolean') fail('引用标识无效');
      if (ref.revision && ref.revision !== config.revision) fail('引用快照不一致');
      if (!ref.available) {
        if (typeof ref.reason !== 'string' || !ref.reason) fail('边界引用缺少原因');
        continue;
      }
      if (!pathOK(ref.path) || !paths.has(ref.path) || !config.files[ref.path]) fail('引用路径无效');
      if (!ref.symbol || !Number.isInteger(ref.line) || !Number.isInteger(ref.endLine)
          || ref.line < 1 || ref.endLine < ref.line
          || ref.endLine > config.files[ref.path].totalLines || typeof ref.text !== 'string') fail('引用范围无效');
    }
    const viewIds = new Set();
    for (const view of config.views) {
      if (!view.id || viewIds.has(view.id) || !Array.isArray(view.steps) || !view.steps.length) fail('阶段标识无效');
      viewIds.add(view.id);
      const stepIds = new Set();
      for (const step of view.steps) {
        if (!step.id || stepIds.has(step.id) || !step.depth || !Array.isArray(step.files)) fail('阅读目标无效');
        stepIds.add(step.id);
        for (const path of step.files) if (!paths.has(path)) fail('目标文件不在目录中');
        for (const id of [step.caller, step.callee]) if (id && !config.references[id]) fail('目标引用不存在');
      }
    }
    return config;
  }
  function sourceURL(config, id) {
    const ref = config.references[id];
    if (!ref || !ref.available) return null;
    return config.repository.replace(/\/$/, '') + '/blob/' + config.revision + '/'
      + ref.path.split('/').map(encodeURIComponent).join('/') + '#L' + ref.line + '-L' + ref.endLine;
  }
  function create(config) {
    validate(config);
    const goals = config.views.flatMap(view => view.steps.map(step => ({...step, stepId:step.id,
      id:step.goalId || view.id + ':' + step.id, viewId:view.id})));
    const byId = new Map(goals.map(goal => [goal.id, goal]));
    const checked = new Set();
    let viewId = config.views[0].id, goalId = goals[0].id;
    const refIdentity = id => {
      const ref = config.references[id];
      return !ref ? null : ref.available ? [true,config.revision,ref.path,ref.symbol,ref.line,ref.endLine,ref.blobSha256 || '']
        : [false,ref.label || '',ref.reason];
    };
    const fingerprint = goal => JSON.stringify([config.repository,config.revision,config.chapterId,
      goal.viewId,goal.stepId,goal.depth,refIdentity(goal.caller),refIdentity(goal.callee),goal.progressKey || null]);
    const progressKey = goal => goal.progressKey || fingerprint(goal);
    const scopeStatus = selected => {
      const completed = selected.filter(goal => checked.has(goal.id)).length;
      return {status:!selected.length ? 'out-of-scope' : !completed ? 'unread'
        : completed === selected.length ? 'scope-complete' : 'partial', total:selected.length, completed};
    };
    return {
      config, goals, checked,
      get viewId() { return viewId; },
      get goalId() { return goalId; },
      selectView(id) {
        if (!config.views.some(view => view.id === id)) fail('阶段不存在');
        viewId = id; goalId = goals.find(goal => goal.viewId === id).id;
      },
      selectGoal(id) {
        const goal = byId.get(id); if (!goal) fail('目标不存在');
        viewId = goal.viewId; goalId = id;
      },
      checkGoal(id, done) {
        if (!byId.has(id) || typeof done !== 'boolean') fail('自检目标或状态无效');
        if (done) checked.add(id); else checked.delete(id);
      },
      clear() { checked.clear(); },
      sourceStatus(id) { return scopeStatus(goals.filter(goal => goal.caller === id || goal.callee === id)); },
      functionStatus(path, symbol) {
        return scopeStatus(goals.filter(goal => [goal.caller,goal.callee].some(id => {
          const ref = config.references[id]; return ref?.available && ref.path === path && ref.symbol === symbol;
        })));
      },
      fileStatus(path) {
        const selected = goals.filter(goal => goal.files.includes(path));
        const symbols = new Set(selected.flatMap(goal => [goal.caller,goal.callee])
          .map(id => config.references[id]).filter(ref => ref?.available && ref.path === path).map(ref => ref.symbol));
        return {...scopeStatus(selected), uncovered:(config.files[path]?.functions || []).filter(fn => !symbols.has(fn.symbol)),
          symbols:[...symbols], depths:[...new Set(selected.map(goal => goal.depth))]};
      },
      snapshot() {
        return {schemaVersion:1,repository:config.repository,revision:config.revision,chapterId:config.chapterId,
          checks:[...checked].map(id => ({progressKey:progressKey(byId.get(id)),fingerprint:fingerprint(byId.get(id))}))};
      },
      restore(record) {
        if (!record || record.schemaVersion !== 1 || record.repository !== config.repository
            || record.revision !== config.revision || record.chapterId !== config.chapterId || !Array.isArray(record.checks)) return;
        const byProgressKey = new Map(goals.map(goal => [progressKey(goal),goal]));
        for (const entry of record.checks) {
          const goal = byProgressKey.get(entry?.progressKey);
          if (goal && entry.fingerprint === fingerprint(goal)) checked.add(goal.id);
        }
      },
    };
  }
  window.ReadingProgress = {create, validate, sourceURL};
})();
