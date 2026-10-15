/* Persistent review data, independent of the page and the browser storage API. */
(function (root) {
  'use strict';
  const day = 86400000;
  const intervals = { review: 1, explain: 3, apply: 7 };
  const fail = () => { throw new Error('备份格式不正确，请选择本页导出的 JSON 文件。'); };
  const validId = id => typeof id === 'string' && /^[a-z][a-z0-9-]{0,63}$/.test(id);
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const date = value => Number.isSafeInteger(value) && value >= 0 && value <= 8640000000000000;
  const string = (value, max = 6000) => typeof value === 'string' && value.length <= max;

  function empty() {
    return { schema_version: 1, selected: null, records: Object.create(null) };
  }

  function record(state, id) {
    if (!validId(id)) fail();
    if (!state.records[id]) {
      state.records[id] = {
        level: null, reviewedAt: null, dueAt: null, updatedAt: 0,
        recall: '', note: '', lastAttempt: null,
      };
    }
    return state.records[id];
  }

  function select(state, id) {
    if (!validId(id)) fail();
    state.selected = id;
  }

  function touch(item, now) {
    // A backup may have come from a device whose clock is ahead of this one.
    item.updatedAt = Math.min(8640000000000000, Math.max(now, item.updatedAt + 1));
  }

  function write(state, id, field, value, now) {
    if (!['recall', 'note'].includes(field) || !string(value) || !date(now)) fail();
    const item = record(state, id);
    item[field] = value;
    touch(item, now);
  }

  function attempt(state, id, choice, correct, now) {
    if (!string(choice, 80) || typeof correct !== 'boolean' || !date(now)) fail();
    const item = record(state, id);
    item.lastAttempt = { choice, correct, at: now };
    if (!correct) item.dueAt = now;
    touch(item, now);
  }

  function grade(state, id, level, now) {
    if (!Object.hasOwn(intervals, level) || !date(now)) fail();
    const item = record(state, id);
    item.level = level;
    item.reviewedAt = now;
    item.dueAt = now + intervals[level] * day;
    touch(item, now);
  }

  function due(state, now) {
    return Object.keys(state.records)
      .filter(id => state.records[id].dueAt !== null && state.records[id].dueAt <= now)
      .sort((a, b) => state.records[a].dueAt - state.records[b].dueAt);
  }

  function parse(text) {
    if (!string(text, 1048576)) fail();
    let input;
    try { input = JSON.parse(text); } catch (_) { fail(); }
    if (!object(input) || input.schema_version !== 1 || !object(input.records)) fail();
    if (input.selected !== null && !validId(input.selected)) fail();
    const state = empty();
    state.selected = input.selected;
    for (const [id, item] of Object.entries(input.records)) {
      if (!validId(id) || !object(item)) fail();
      if (item.level !== null && !Object.hasOwn(intervals, item.level)) fail();
      if (!date(item.updatedAt) || !string(item.recall) || !string(item.note)) fail();
      if (item.reviewedAt !== null && !date(item.reviewedAt)) fail();
      if (item.dueAt !== null && !date(item.dueAt)) fail();
      const last = item.lastAttempt;
      if (last !== null && (!object(last) || !string(last.choice, 80) || typeof last.correct !== 'boolean' || !date(last.at))) fail();
      state.records[id] = {
        level: item.level, reviewedAt: item.reviewedAt, dueAt: item.dueAt,
        updatedAt: item.updatedAt, recall: item.recall, note: item.note,
        lastAttempt: last === null ? null : { choice: last.choice, correct: last.correct, at: last.at },
      };
    }
    return state;
  }

  function serialize(state) { return JSON.stringify(state, null, 2); }

  function merge(state, incoming) {
    let changed = 0;
    for (const [id, item] of Object.entries(incoming.records)) {
      if (!state.records[id] || item.updatedAt > state.records[id].updatedAt) {
        state.records[id] = item;
        changed++;
      }
    }
    return changed;
  }

  root.AsyncKnowledgeState = { empty, select, write, attempt, grade, due, parse, serialize, merge };
})(globalThis);
