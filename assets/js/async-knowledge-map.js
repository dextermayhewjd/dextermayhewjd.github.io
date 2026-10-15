(function () {
  'use strict';
  const root = document.querySelector('[data-knowledge-map]');
  if (!root || !globalThis.AsyncKnowledgeState) return;
  const model = globalThis.AsyncKnowledgeState;
  const config = JSON.parse(root.querySelector('[data-knowledge-config]').textContent);
  const nodes = new Map(config.nodes.map(node => [node.id, node]));
  const storageKey = 'python-async-knowledge-v1';
  const recoveryKey = `${storageKey}-recovery`;
  const find = name => root.querySelector(`[data-${name}]`);
  const labels = { review: '需要提示', explain: '能独立解释', apply: '能判断代码' };
  const relationLabels = { prerequisite: '前置 → 后续', contrast: '对比', combine: '组合' };
  let state = model.empty();
  let selected;
  let downloadUrl;
  let storageWritable = true;
  let unreadableBackup = false;
  let backupUrl;
  let originalRaw = null;
  let recoveryUrls = [];

  try {
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      try { state = model.parse(saved); }
      catch (_) {
        // Preserve unreadable storage until the learner has downloaded it.
        unreadableBackup = true;
        originalRaw = saved;
        backupUrl = URL.createObjectURL(new Blob([saved], { type: 'application/json' }));
      }
    }
  } catch (_) { storageWritable = false; }

  function textElement(tag, text) {
    const element = document.createElement(tag);
    element.textContent = text;
    return element;
  }

  function readRecoveries() {
    const saved = localStorage.getItem(recoveryKey);
    if (!saved) return [];
    try {
      const items = JSON.parse(saved);
      if (Array.isArray(items) && items.every(item => typeof item === 'string')) return items;
    } catch (_) { /* Preserve a recovery store from an unrecognized format, too. */ }
    return [saved];
  }

  function showRecoveries() {
    const items = readRecoveries();
    const panel = find('recovery-links');
    panel.replaceChildren();
    recoveryUrls.forEach(url => URL.revokeObjectURL(url));
    recoveryUrls = [];
    panel.hidden = items.length === 0;
    if (!items.length) return;
    panel.append(textElement('p', '之前无法读取的原始记录已另外保留，不会因导入新备份而删除。'));
    items.forEach((raw, index) => {
      const url = URL.createObjectURL(new Blob([raw], { type: 'application/json' }));
      recoveryUrls.push(url);
      const link = textElement('a', `下载原始记录 ${index + 1}`);
      link.href = url;
      link.download = `async-review-original-${index + 1}.json`;
      panel.append(link, document.createElement('br'));
    });
  }

  function save(replaceStored = false) {
    if (!unreadableBackup && !replaceStored) {
      try {
        const saved = localStorage.getItem(storageKey);
        if (saved) {
          try { model.merge(state, model.parse(saved)); }
          catch (_) {
            unreadableBackup = true;
            originalRaw = saved;
            backupUrl = URL.createObjectURL(new Blob([saved], { type: 'application/json' }));
          }
        }
      } catch (_) { storageWritable = false; }
    }
    if (unreadableBackup) {
      find('save-status').replaceChildren(document.createTextNode('旧记录暂时无法读取，已保留原数据；本次修改先保存在内存中。'));
      const link = textElement('a', '下载原始记录备份');
      link.href = backupUrl;
      link.download = 'async-review-original.json';
      find('save-status').append(' ', link);
      return;
    }
    try {
      localStorage.setItem(storageKey, model.serialize(state));
      storageWritable = true;
    } catch (_) { storageWritable = false; }
    find('save-status').textContent = storageWritable
      ? '已保存在当前浏览器。重要记录请另行导出备份。'
      : '浏览器暂时无法保存。本次记录仍可使用，请在关闭页面前导出备份。';
    refresh();
  }

  function refresh() {
    for (const badge of root.querySelectorAll('[data-node-status]')) {
      const item = state.records[badge.dataset.nodeStatus];
      badge.textContent = item?.level ? labels[item.level] : '未自测';
    }
    const due = model.due(state, Date.now()).filter(id => nodes.has(id));
    const links = find('review-links');
    links.replaceChildren();
    find('review-summary').textContent = due.length
      ? `有 ${due.length} 个概念建议回忆。先选下面最多 3 个，其他的下一轮再看。`
      : '还没有到期或待回看的记录。可以从左侧选一个概念，不必一次复习全部。';
    for (const id of due.slice(0, 3)) {
      const button = textElement('button', nodes.get(id).title);
      button.type = 'button';
      button.addEventListener('click', () => select(id, true));
      links.append(button);
    }
    if (!selected) return;
    const item = state.records[selected.id];
    for (const button of root.querySelectorAll('[data-grade]')) {
      button.setAttribute('aria-pressed', String(item?.level === button.dataset.grade));
    }
    let status = '尚未记录自测表现。浏览和展开不会改变熟悉程度。';
    if (item?.dueAt !== null && item?.dueAt !== undefined) {
      status = item.level ? `上次记录：${labels[item.level]}。` : '';
      status += item.dueAt <= Date.now()
        ? '建议现在回看，再按本次表现记录。'
        : `下次建议回忆：${new Date(item.dueAt).toLocaleString('zh-CN', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}。`;
    }
    find('current-review').textContent = status;
  }

  function select(id, focus = false, replaceStored = false) {
    if (!nodes.has(id)) return;
    selected = nodes.get(id);
    model.select(state, id);
    history.replaceState(null, '', `#${id}`);
    const group = root.querySelector(`[data-knowledge-group="${selected.group}"]`);
    group.open = true;
    for (const button of root.querySelectorAll('[data-select-node]')) {
      if (button.dataset.selectNode === id) button.setAttribute('aria-current', 'true');
      else button.removeAttribute('aria-current');
    }
    document.getElementById('knowledge-card-title').textContent = selected.title;
    find('card-kind').textContent = `${selected.kind} · 回忆卡`;
    find('card-content').hidden = false;
    find('recall-question').textContent = selected.question;
    // An earlier answer is available on demand, never exposed as a fresh answer.
    find('recall').value = '';
    find('previous-recall').textContent = state.records[id]?.recall || '';
    find('previous-recall-panel').hidden = !state.records[id]?.recall;
    find('previous-recall-panel').open = false;
    find('note').value = state.records[id]?.note || '';
    find('explanation').replaceChildren(...selected.explanation.map(line => textElement('li', line)));
    find('misconception').textContent = selected.misconception;
    find('reveal').setAttribute('aria-expanded', 'false');
    find('reveal').textContent = '展开解释，核对我的回答';
    document.getElementById('knowledge-explanation').hidden = true;
    root.querySelector('.akm-lesson-links').open = false;
    const relationList = find('relations');
    relationList.replaceChildren();
    for (const edge of config.relations.filter(edge => edge.from === id || edge.to === id)) {
      const other = nodes.get(edge.from === id ? edge.to : edge.from);
      const li = document.createElement('li');
      const direction = edge.type === 'prerequisite'
        ? (edge.to === id ? '本概念的前置' : '从这里继续')
        : relationLabels[edge.type];
      li.append(textElement('span', `${direction}：`));
      const button = textElement('button', other.title);
      button.type = 'button';
      button.addEventListener('click', () => select(other.id, true));
      li.append(button, textElement('p', edge.text));
      relationList.append(li);
    }
    find('lesson-links').replaceChildren(...selected.lessons.map(lesson => {
      const li = document.createElement('li');
      const link = textElement('a', lesson.title);
      link.href = lesson.url;
      li.append(link);
      return li;
    }));
    find('exercise-code').textContent = selected.exercise.code;
    find('exercise-note').textContent = selected.exercise.note || '';
    find('exercise-note').hidden = !selected.exercise.note;
    find('exercise-options').replaceChildren(...selected.exercise.options.map(option => {
      const label = document.createElement('label');
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = 'knowledge-output';
      radio.value = option.id;
      label.append(radio, textElement('code', option.text));
      return label;
    }));
    find('exercise-feedback').hidden = true;
    find('exercise-feedback').textContent = '';
    if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    const code = 'import asyncio\nimport contextlib\nimport time\n\n\nasync def main():\n'
      + selected.exercise.code.split('\n').map(line => `    ${line}`).join('\n')
      + '\n\n\nif __name__ == "__main__":\n    asyncio.run(main())\n';
    downloadUrl = URL.createObjectURL(new Blob([code], { type: 'text/x-python;charset=utf-8' }));
    find('download-code').href = downloadUrl;
    find('download-code').download = `async-review-${id}.py`;
    refresh();
    save(replaceStored);
    if (focus) {
      const heading = document.getElementById('knowledge-card-title');
      heading.focus({ preventScroll: true });
      heading.scrollIntoView({ block: 'start' });
    }
  }

  for (const button of root.querySelectorAll('[data-select-node]')) {
    button.disabled = false;
    button.addEventListener('click', () => select(button.dataset.selectNode, true));
  }
  for (const field of ['recall', 'note']) {
    find(field).addEventListener('input', () => {
      model.write(state, selected.id, field, find(field).value, Date.now());
      save();
    });
  }
  find('reveal').addEventListener('click', () => {
    const panel = document.getElementById('knowledge-explanation');
    panel.hidden = !panel.hidden;
    find('reveal').setAttribute('aria-expanded', String(!panel.hidden));
    find('reveal').textContent = panel.hidden ? '展开解释，核对我的回答' : '收起解释，再试着回忆';
  });
  find('exercise-form').addEventListener('submit', event => {
    event.preventDefault();
    const radio = find('exercise-form').querySelector('input:checked');
    const feedback = find('exercise-feedback');
    feedback.hidden = false;
    if (!radio) {
      feedback.textContent = '先选一个输出，再核对判断。';
      return;
    }
    const correct = radio.value === selected.exercise.answer;
    model.attempt(state, selected.id, radio.value, correct, Date.now());
    feedback.dataset.correct = String(correct);
    feedback.textContent = (correct ? '本题判断正确。' : '这次判断需要再看一下。正确输出：\n')
      + (correct ? '' : `${selected.exercise.expected_output}\n`)
      + selected.exercise.explanation;
    refresh();
    save();
  });
  for (const button of root.querySelectorAll('[data-grade]')) {
    button.addEventListener('click', () => {
      model.grade(state, selected.id, button.dataset.grade, Date.now());
      refresh();
      save();
    });
  }
  find('export').addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([model.serialize(state)], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `async-review-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  find('import').addEventListener('change', async event => {
    const input = event.target;
    const file = input.files[0];
    if (!file) return;
    try {
      if (file.size > 1048576) throw new Error('备份文件超过 1 MB，请检查是否选错文件。');
      const incoming = model.parse(await file.text());
      if (originalRaw !== null) {
        try {
          const recovered = readRecoveries();
          if (!recovered.includes(originalRaw)) recovered.push(originalRaw);
          localStorage.setItem(recoveryKey, JSON.stringify(recovered));
          showRecoveries();
        } catch (_) {
          throw new Error('暂时无法另外保存原始记录；请先下载原始备份，本次没有替换它。');
        }
      }
      const count = model.merge(state, incoming);
      // Only replace unreadable storage after preserving its exact original bytes.
      unreadableBackup = false;
      originalRaw = null;
      if (backupUrl) { URL.revokeObjectURL(backupUrl); backupUrl = null; }
      select(selected.id, false, true);
      const prefix = storageWritable ? '已合并并保存' : '已合并到本次页面';
      find('save-status').textContent = `${prefix} ${count} 条较新的记录。`
        + (storageWritable ? '' : '浏览器无法保存，请关闭前导出备份。');
    } catch (error) {
      const message = `${error.message} 原有记录未被修改。`;
      if (unreadableBackup) {
        save();
        find('save-status').prepend(document.createTextNode(`${message} `));
      } else {
        find('save-status').textContent = message;
      }
    } finally { input.value = ''; }
  });
  window.addEventListener('hashchange', () => select(location.hash.slice(1), true));
  window.addEventListener('focus', refresh);
  window.addEventListener('storage', event => {
    if (event.key !== storageKey || !event.newValue) return;
    try {
      const previousNote = state.records[selected.id]?.note || '';
      model.merge(state, model.parse(event.newValue));
      if (document.activeElement !== find('note') && find('note').value === previousNote) {
        find('note').value = state.records[selected.id]?.note || '';
      }
      refresh();
    } catch (_) {
      // The next save preserves an unreadable external update for recovery.
    }
  });
  const initial = location.hash.slice(1);
  try { showRecoveries(); } catch (_) { /* Main save reports unavailable storage. */ }
  select(nodes.has(initial) ? initial : nodes.has(state.selected) ? state.selected : 'event');
})();
