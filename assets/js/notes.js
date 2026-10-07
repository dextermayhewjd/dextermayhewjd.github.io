// 感悟检索：抽屉（全站）与 /notes/ 整页共用同一套界面。
// 数据是构建时生成的 notes.json，第一次打开时才去取。
(() => {
  const script = document.currentScript;
  const SRC = script.dataset.notesSrc;
  const PAGE = script.dataset.notesPage;

  let dataPromise = null;
  const loadNotes = () =>
    (dataPromise ??= fetch(SRC).then((r) => {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    }));

  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };

  // 分类按条目数从多到少
  const categoriesOf = (notes) => {
    const count = new Map();
    for (const n of notes) count.set(n.category, (count.get(n.category) || 0) + 1);
    return [...count].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "zh"));
  };

  // 空格分隔的多个词须全部命中（不区分大小写）
  const matches = (note, terms) => {
    if (!terms.length) return true;
    const hay = [note.title, note.source, note.category, note.text].join("\n").toLowerCase();
    return terms.every((t) => hay.includes(t));
  };

  function card(note) {
    const art = el("article", "note-card");
    const meta = el("div", "note-meta");
    meta.append(el("span", "note-cat", note.category), el("time", "note-date", note.date));
    art.append(meta);

    if (note.title) {
      const h = el("h3", "note-title");
      if (note.url) {
        const a = el("a", null, note.title);
        a.href = note.url;
        h.append(a);
      } else h.textContent = note.title;
      art.append(h);
    }

    const body = el("div", "note-body");
    body.innerHTML = note.html; // 构建时由 Hugo 从本仓库 Markdown 渲染
    art.append(body);

    const foot = el("div", "note-foot");
    if (note.source) {
      const src = note.sourceURL ? el("a", "note-source", "— " + note.source) : el("span", "note-source", "— " + note.source);
      if (note.sourceURL) {
        src.href = note.sourceURL;
        src.target = "_blank";
        src.rel = "noopener";
      }
      foot.append(src);
    }
    if (note.url) {
      const more = el("a", "note-more", "阅读全文 →");
      more.href = note.url;
      foot.append(more);
    }
    if (foot.childNodes.length) art.append(foot);
    return art;
  }

  function mount(root, { inDrawer, onClose }) {
    const head = el("div", "notes-head");
    const h = el("h2", "notes-heading", "感悟");
    const count = el("span", "notes-count");
    h.append(count);
    head.append(h);
    if (inDrawer) {
      const full = el("a", "notes-full", "整页浏览");
      full.href = PAGE;
      const close = el("button", "notes-close", "×");
      close.type = "button";
      close.setAttribute("aria-label", "关闭");
      close.addEventListener("click", onClose);
      head.append(full, close);
    }

    const search = el("input", "notes-search");
    search.type = "search";
    search.placeholder = "检索标题、内容、来源…";
    search.setAttribute("aria-label", "检索感悟");
    const chips = el("div", "notes-chips");
    chips.setAttribute("role", "tablist");
    const list = el("div", "notes-list");
    list.setAttribute("aria-live", "polite");
    root.append(head, search, chips, list);

    const state = { cat: new URLSearchParams(location.search).get("cat") || "", q: "" };
    let notes = [];

    function renderChips() {
      chips.replaceChildren();
      for (const [name, n] of [["", notes.length], ...categoriesOf(notes)]) {
        const b = el("button", "notes-chip");
        b.type = "button";
        b.setAttribute("role", "tab");
        b.setAttribute("aria-selected", String(state.cat === name));
        b.append(name || "全部", el("span", "notes-chip-n", String(n)));
        b.addEventListener("click", () => {
          state.cat = name;
          renderChips();
          renderList();
        });
        chips.append(b);
      }
    }

    function renderList() {
      const terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
      const shown = notes.filter((n) => (!state.cat || n.category === state.cat) && matches(n, terms));
      count.textContent = `${shown.length} / ${notes.length}`;
      list.replaceChildren(...shown.map(card));
      if (!shown.length) list.append(el("p", "notes-empty", notes.length ? "没有匹配的感悟" : "还没有感悟"));
      if (window.renderMathInElement) {
        renderMathInElement(list, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "\\[", right: "\\]", display: true },
            { left: "$", right: "$", display: false },
            { left: "\\(", right: "\\)", display: false },
          ],
          throwOnError: false,
        });
      }
    }

    search.addEventListener("input", () => {
      state.q = search.value.trim();
      renderList();
    });

    list.append(el("p", "notes-empty", "加载中…"));
    loadNotes()
      .then((d) => {
        notes = d;
        if (state.cat && !notes.some((n) => n.category === state.cat)) state.cat = "";
        renderChips();
        renderList();
      })
      .catch(() => list.replaceChildren(el("p", "notes-empty", "感悟加载失败")));

    return { focus: () => search.focus() };
  }

  function initDrawer() {
    const toggle = document.querySelector(".notes-toggle");
    const drawer = document.getElementById("notes-drawer");
    const backdrop = document.querySelector(".notes-backdrop");
    const root = drawer?.querySelector("[data-notes-mount]");
    if (!toggle || !root) return;
    // 在 /notes/ 整页上抽屉是多余的
    if (document.querySelector(".notes-root--page")) return;

    let ui = null;
    let lastFocus = null;

    const open = () => {
      ui ??= mount(root, { inDrawer: true, onClose: close });
      lastFocus = document.activeElement;
      drawer.hidden = backdrop.hidden = false;
      requestAnimationFrame(() => document.documentElement.classList.add("notes-open"));
      toggle.setAttribute("aria-expanded", "true");
      ui.focus();
    };
    function close() {
      document.documentElement.classList.remove("notes-open");
      toggle.setAttribute("aria-expanded", "false");
      setTimeout(() => {
        if (!document.documentElement.classList.contains("notes-open")) drawer.hidden = backdrop.hidden = true;
      }, 250);
      lastFocus?.focus?.();
    }

    toggle.hidden = false;
    toggle.addEventListener("click", () => (drawer.hidden ? open() : close()));
    backdrop.addEventListener("click", close);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !drawer.hidden) close();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    const page = document.querySelector(".notes-root--page");
    if (page) mount(page, { inDrawer: false });
    initDrawer();
  });
})();
