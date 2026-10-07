(() => {
  'use strict';

  document.querySelectorAll('[data-diagram-explorer]').forEach(root => {
    if (root.dataset.ready === 'true') return;
    const cards = new Map([...root.querySelectorAll('[data-module-card]')]
      .map(card => [card.dataset.moduleCard, card]));
    const buttons = [...root.querySelectorAll('[data-module-button]')];
    const links = [...root.querySelectorAll('a[data-module]')];
    const overview = root.querySelector('svg');
    const status = root.querySelector('[data-explorer-status]');
    const panel = root.querySelector('[data-explorer-panel]');
    const panelTitle = root.querySelector('[data-explorer-panel-title]');
    const resizeHandle = root.querySelector('[data-panel-resize]');
    const connectionSummary = root.querySelector('[data-connection-summary]');
    const connectionPaths = [...overview.querySelectorAll('path[data-from][data-to]')];
    const overviewNodes = new Map();
    const nodeBounds = new Map();
    const nodeLabels = new Map();
    let overviewStage = '';
    let hoveredStage = '';
    let selected = '';
    let anchor = null;
    let manualBounds = null;
    let drag = null;
    const functionIndex = new Map();
    const readingElement = root.querySelector('[data-reading-config]');
    const readingPack = readingElement ? JSON.parse(readingElement.textContent) : null;
    document.querySelectorAll('.post-content .highlight, .post-content pre').forEach(block => {
      if (block.closest('[data-diagram-explorer]')) return;
      const match = block.textContent.match(/(?:^|\n)\s*(?:async\s+)?def\s+(\w+)\s*\(/);
      if (match && !functionIndex.has(match[1])) functionIndex.set(match[1], block);
    });
    if (readingPack) {
      document.querySelectorAll('section[data-source-ref]').forEach(block => {
        if (!block.closest('[data-diagram-explorer]') && readingPack.references[block.dataset.sourceRef]?.available)
          functionIndex.set(block.dataset.sourceRef, block);
      });
    }

    // Explicit endpoints express control/data/reference relationships; coordinates
    // alone cannot tell whether a crossing is a connection or a loop junction.
    overview.querySelectorAll('rect[data-stage]').forEach(rect => {
      const moduleLink = rect.closest('a[data-module]');
      let node = moduleLink;
      if (!node) {
        node = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        rect.parentNode.insertBefore(node, rect);
        node.append(rect);
        const x = Number(rect.getAttribute('x')), y = Number(rect.getAttribute('y'));
        const w = Number(rect.getAttribute('width')), h = Number(rect.getAttribute('height'));
        let next = node.nextElementSibling;
        // Chapter links remain siblings rather than nested interactive controls.
        while (next && next.tagName.toLowerCase() === 'text') {
          const tx = Number(next.getAttribute('x')), ty = Number(next.getAttribute('y'));
          if (tx < x || tx > x+w || ty < y || ty > y+h) break;
          const element = next; next = next.nextElementSibling; node.append(element);
        }
        node.setAttribute('role', 'button');
        node.setAttribute('tabindex', '0');
        node.addEventListener('click', event => {
          if (event.target.closest('a')) return; // Chapter links keep their navigation.
          selectOverviewNode(rect.dataset.stage, node);
        });
        node.addEventListener('keydown', event => {
          if (event.target !== node || !['Enter', ' '].includes(event.key)) return;
          event.preventDefault(); selectOverviewNode(rect.dataset.stage, node);
        });
      }
      node.dataset.overviewStage = rect.dataset.stage;
      const label = (node.querySelector('text')?.textContent || rect.dataset.stage).replace(/\s*▸\s*$/, '');
      nodeLabels.set(rect.dataset.stage, label);
      if (!moduleLink) node.setAttribute('aria-label', label + '：高亮输入、输出与引用关系');
      overviewNodes.set(rect.dataset.stage, node);
      nodeBounds.set(rect.dataset.stage, {
        x:Number(rect.getAttribute('x')), y:Number(rect.getAttribute('y')),
        width:Number(rect.getAttribute('width')), height:Number(rect.getAttribute('height')),
      });
      node.addEventListener('pointerenter', event => {
        if (event.pointerType !== 'touch') previewConnections(rect.dataset.stage);
      });
      node.addEventListener('pointerleave', previewAtPointer);
    });
    overview.addEventListener('pointermove', previewAtPointer);
    overview.addEventListener('pointerleave', event => {
      if (event.pointerType !== 'touch') previewConnections('');
    });
    overview.closest('.architecture-diagram__canvas').addEventListener('scroll', () => previewConnections(''), {passive:true});

    function pinnedConnectionStage() {
      const card = cards.get(selected);
      return card ? links.find(link => link.dataset.module === card.dataset.focusModule)?.dataset.overviewStage || '' : overviewStage;
    }

    function previewConnections(stage) {
      if (hoveredStage === stage) return;
      hoveredStage = stage;
      highlightConnections(hoveredStage || pinnedConnectionStage());
    }

    function previewAtPointer(event) {
      if (event.pointerType === 'touch') return;
      const matrix = overview.getScreenCTM();
      if (!matrix) return;
      const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
      // Hit the full node rectangle, including chapter links kept outside its
      // button group, so moving across a caption doesn't flicker the preview.
      const match = [...nodeBounds].find(([, box]) => point.x >= box.x && point.x <= box.x+box.width
        && point.y >= box.y && point.y <= box.y+box.height);
      previewConnections(match ? match[0] : '');
    }

    // Reference connections also need directional heads, with their existing hue.
    const referenceMarker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
    referenceMarker.id = root.id + '-reference-arrow';
    for (const [name, value] of Object.entries({viewBox:'0 0 10 10', refX:'9', refY:'5',
      markerWidth:'6', markerHeight:'6', orient:'auto'})) referenceMarker.setAttribute(name, value);
    const head = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    head.setAttribute('d', 'M0 0L10 5L0 10Z');
    head.setAttribute('fill', 'var(--diagram-muted, #58677b)');
    referenceMarker.append(head);
    overview.querySelector('defs').append(referenceMarker);
    connectionPaths.filter(path => path.dataset.kind === 'reference' && !path.hasAttribute('marker-end'))
      .forEach(path => path.setAttribute('marker-end', 'url(#' + referenceMarker.id + ')'));

    // Keep selected heads readable without letting thicker strokes inflate them
    // into nearby ports. Each clone retains the connected line's original hue.
    const selectedMarkers = new Map();
    connectionPaths.forEach(path => {
      const normal = path.getAttribute('marker-end');
      if (!normal) return;
      const id = normal.match(/url\(#([^)]+)\)/)?.[1];
      const marker = [...overview.querySelectorAll('marker')].find(node => node.id === id);
      if (!marker) return;
      const key = id + ':' + path.getAttribute('stroke');
      if (!selectedMarkers.has(key)) {
        const copy = marker.cloneNode(true);
        copy.id = root.id + '-selected-arrow-' + selectedMarkers.size;
        copy.setAttribute('markerUnits', 'userSpaceOnUse');
        copy.setAttribute('markerWidth', '12');
        copy.setAttribute('markerHeight', '12');
        copy.querySelectorAll('path').forEach(head => head.setAttribute('fill', path.getAttribute('stroke')));
        overview.querySelector('defs').append(copy);
        selectedMarkers.set(key, 'url(#' + copy.id + ')');
      }
      path.dataset.normalMarker = normal;
      path.dataset.selectedMarker = selectedMarkers.get(key);
    });

    function highlightConnections(stage) {
      overview.dataset.connectionSelection = stage;
      overview.dataset.connectionPreview = hoveredStage;
      const pinned = pinnedConnectionStage();
      overviewNodes.forEach((node, key) => {
        node.classList.toggle('is-connection-selected', key === stage);
        node.setAttribute('aria-pressed', String(key === pinned));
      });
      const incoming = [], outgoing = [], references = [];
      connectionPaths.forEach(path => {
        const related = !!stage && (path.dataset.from === stage || path.dataset.to === stage);
        path.classList.toggle('is-related', related);
        path.classList.toggle('is-unrelated', !!stage && !related);
        if (path.dataset.normalMarker) path.setAttribute('marker-end',
          related ? path.dataset.selectedMarker : path.dataset.normalMarker);
        if (!related) return;
        const from = nodeLabels.get(path.dataset.from), to = nodeLabels.get(path.dataset.to);
        const label = path.dataset.label;
        if (path.dataset.kind === 'reference') references.push(from + ' → ' + to + '（' + label + '）');
        else if (path.dataset.to === stage) incoming.push(from + '（' + label + '）');
        else outgoing.push(to + '（' + label + '）');
      });
      connectionSummary.replaceChildren();
      connectionSummary.hidden = !stage;
      if (!stage) return;
      for (const [label, entries] of [['输入／前序', incoming], ['输出／去向', outgoing], ['引用关系', references]]) {
        if (!entries.length) continue;
        const row = document.createElement('p'), title = document.createElement('strong');
        title.textContent = label + '：'; row.append(title, entries.join('；'));
        connectionSummary.append(row);
      }
    }

    function selectOverviewNode(stage, origin) {
      const closing = !selected && overviewStage === stage;
      closePanel();
      anchor = origin;
      overviewStage = closing ? '' : stage;
      synchronize();
    }

    function bindFunctionLink(link, activate) {
      link.setAttribute('role', 'button');
      link.setAttribute('tabindex', '0');
      link.setAttribute('aria-label', '查看 ' + link.textContent.trim() + ' 的实现');
      // Run before the theme's anchor scrolling and the parent step's click.
      const handle = event => {
        event.preventDefault();
        event.stopImmediatePropagation();
        activate();
      };
      link.addEventListener('click', handle, true);
      link.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') handle(event);
      }, true);
    }

    document.querySelectorAll('[data-function-explorer]').forEach(source => {
      if (source.dataset.functionExplorer !== root.id || root.contains(source)) return;
      source.querySelectorAll('a[data-function]').forEach(link => {
        const key = link.dataset.functionCard, name = link.dataset.function;
        const card = cards.get(key);
        if (!card || !functionIndex.has(name)) return;
        link.setAttribute('aria-controls', card.id);
        bindFunctionLink(link, () => {
          anchor = link;
          overviewStage = '';
          hoveredStage = '';
          selected = key;
          cards.forEach((candidate, candidateKey) => { candidate.open = candidateKey === key; });
          populate(card);
          synchronize();
          card.selectFunction(readingPack ? link.dataset.function : name);
        });
      });
    });

    function fitReader() {
      const card = cards.get(selected);
      const reader = card && card.querySelector('[data-step-reader]');
      if (!reader || panel.hidden) return;
      const body = root.querySelector('.diagram-explorer__panel-body');
      const offset = reader.getBoundingClientRect().top - body.getBoundingClientRect().top + body.scrollTop;
      reader.style.height = Math.max(350, body.clientHeight - offset - 12) + 'px';
    }

    function resizeTo(bounds) {
      const vw = document.documentElement.clientWidth;
      const vh = window.innerHeight;
      const clamp = (value, low, high) => Math.max(low, Math.min(value, high));
      const width = clamp(bounds.width, Math.min(320, vw - 24), vw - 24);
      const height = clamp(bounds.height, Math.min(180, vh - 24), vh - 24);
      manualBounds = {
        left: clamp(bounds.left, 12, vw - width - 12),
        top: clamp(bounds.top, 12, vh - height - 12), width, height,
      };
      panel.style.width = width + 'px';
      panel.style.height = height + 'px';
      panel.style.maxHeight = height + 'px';
      panel.style.left = manualBounds.left + 'px';
      panel.style.top = manualBounds.top + 'px';
      fitReader();
    }

    function positionPanel() {
      if (!selected || panel.hidden) return;
      if (manualBounds) { resizeTo(manualBounds); return; }
      panel.style.height = '';
      const vw = document.documentElement.clientWidth;
      const vh = window.innerHeight;
      const margin = 12;
      const width = Math.min(560, vw - margin * 2);
      panel.style.width = width + 'px';
      panel.style.maxHeight = Math.min(620, vh - margin * 2) + 'px';
      const card = cards.get(selected);
      const candidates = [anchor, links.find(link => link.dataset.module === card.dataset.focusModule)];
      const rect = candidates.filter(Boolean).map(node => node.getBoundingClientRect())
        .find(box => box.bottom > 0 && box.top < vh && box.right > 0 && box.left < vw);
      const height = Math.min(panel.scrollHeight, 620, vh - margin * 2);
      const clamp = (value, low, high) => Math.max(low, Math.min(value, high));
      let left, top;
      if (!rect) {
        left = (vw - width) / 2;
        top = (vh - height) / 2;
      } else if (rect.right + margin + width <= vw - margin) {
        left = rect.right + margin;
        top = clamp(rect.top, margin, vh - height - margin);
      } else if (rect.left - margin - width >= margin) {
        left = rect.left - margin - width;
        top = clamp(rect.top, margin, vh - height - margin);
      } else {
        left = clamp((rect.left + rect.right - width) / 2, margin, vw - width - margin);
        const below = vh - rect.bottom - margin * 2;
        const above = rect.top - margin * 2;
        if (below >= 220 || below >= above) {
          top = rect.bottom + margin;
          panel.style.maxHeight = Math.max(100, vh - top - margin) + 'px';
        } else {
          const space = Math.min(height, above);
          top = rect.top - margin - space;
          panel.style.maxHeight = Math.max(100, space) + 'px';
        }
      }
      panel.style.left = Math.max(margin, left) + 'px';
      panel.style.top = Math.max(margin, top) + 'px';
      fitReader();
    }

    // Copies remain local to a detail card; original diagrams and code stay intact.
    function namespaceIDs(copy, key) {
      const mapping = new Map();
      const nodes = [copy, ...copy.querySelectorAll('[id]')];
      nodes.forEach(node => {
        if (!node.id) return;
        const original = node.id;
        node.id = root.id + '-' + key + '-' + original;
        mapping.set(original, node.id);
      });
      [copy, ...copy.querySelectorAll('*')].forEach(node => {
        [...node.attributes].forEach(attribute => {
          let value = attribute.value;
          if (attribute.name === 'aria-labelledby' || attribute.name === 'aria-describedby') {
            value = value.split(/\s+/).map(id => mapping.get(id) || id).join(' ');
          }
          value = value.replace(/url\(#([^)]+)\)/g, (match, id) =>
            mapping.has(id) ? 'url(#' + mapping.get(id) + ')' : match);
          if ((attribute.name === 'href' || attribute.name === 'xlink:href') && value.startsWith('#')) {
            const mapped = mapping.get(value.slice(1));
            if (mapped) value = '#' + mapped;
          }
          if (value !== attribute.value) node.setAttribute(attribute.name, value);
        });
      });
      return copy;
    }

    function firstCodeAfter(id) {
      const marker = document.getElementById(id);
      if (!marker) return null;
      const markerBlock = marker.closest('p') || marker;
      let node = markerBlock.nextElementSibling;
      let headingSeen = false;
      while (node) {
        if (node.tagName === 'H2') {
          if (headingSeen) return null;
          headingSeen = true;
        }
        const block = node.matches('.highlight, pre') ? node : node.querySelector('.highlight, pre');
        if (block) return block;
        node = node.nextElementSibling;
      }
      return null;
    }

    function populate(card) {
      if (card.dataset.populated === 'true') return;
      const key = card.dataset.moduleCard;
      const figure = card.dataset.figureId && document.getElementById(card.dataset.figureId);
      if (figure) {
        const copy = figure.cloneNode(true);
        copy.removeAttribute('id');
        copy.querySelectorAll('.architecture-diagram__legend-details').forEach(legend => { legend.open = false; });
        card.querySelector('[data-local-diagram]').append(namespaceIDs(copy, key));
        enableDiagramTrace(copy);
      }
      const code = card.querySelector('[data-module-code]');
      const names = (card.dataset.codeFunctions || '').split(',').filter(Boolean);
      const roles = JSON.parse(card.dataset.functionRoles || '{}');
      names.forEach(name => {
        const block = functionIndex.get(name);
        if (!block) return;
        const section = document.createElement('section');
        section.className = 'diagram-explorer__function-code';
        section.dataset.functionCode = name;
        const title = document.createElement('button');
        title.type = 'button';
        title.className = 'diagram-explorer__function-title';
        const reference = readingPack?.references[name];
        title.textContent = reference ? reference.symbol : name + '()';
        if (roles[name]) {
          const role = document.createElement('span');
          role.className = 'diagram-explorer__function-role';
          role.textContent = ' · ' + roles[name];
          title.append(role);
        }
        section.append(title);
        const copy = block.cloneNode(true);
        copy.querySelectorAll('.copy-code').forEach(button => button.remove());
        section.append(namespaceIDs(copy, key + '-function-' + name));
        code.append(section);
      });
      if (!names.length || card.dataset.includeSnippets === 'true') {
      (card.dataset.codeSections || '').split(',').filter(Boolean).forEach(id => {
        const block = firstCodeAfter(id);
        if (block) {
          const copy = block.cloneNode(true);
          // Theme copy buttons own listeners that cloneNode cannot copy.
          copy.querySelectorAll('.copy-code').forEach(button => button.remove());
          code.append(namespaceIDs(copy, key + '-code-' + id));
        }
      });
      }
      connectSteps(card);
      if (readingPack) root.dispatchEvent(new CustomEvent('diagram:populated'));
      card.querySelector('.diagram-explorer__contract-details').addEventListener('toggle', fitReader);
      card.dataset.populated = 'true';
    }

    function connectSteps(card) {
      const reader = card.querySelector('[data-step-reader]');
      const code = reader.querySelector('[data-function-list]');
      const sections = [...code.querySelectorAll('[data-function-code]')];
      const mapping = JSON.parse(card.dataset.stageFunctions || '{}');
      const steps = [];
      let pinned = [(card.dataset.codeFunctions || '').split(',')[0]].filter(Boolean);
      function highlight(names, reveal) {
        sections.forEach(section => section.classList.toggle('is-function-selected', names.includes(section.dataset.functionCode)));
        steps.forEach(step => {
          const match = step.dataset.codeFunctions.split(' ').some(name => names.includes(name));
          step.classList.toggle('is-step-selected', match);
          step.setAttribute(step.getAttribute('role') === 'group' ? 'aria-current' : 'aria-pressed', String(match));
        });
        reader.querySelectorAll('a[data-function]').forEach(link =>
          link.classList.toggle('is-function-selected', names.includes(link.dataset.function)));
        reader.querySelector('[data-step-status]').textContent = (readingPack ? '对应源码：' : '对应函数：') + names.map(name => {
          const ref=readingPack?.references[name];
          return ref ? ref.symbol+' · '+ref.path+' L'+ref.line+'–L'+ref.endLine : name+'()';
        }).join('、');
        if (reveal) {
          const target = sections.find(section => section.dataset.functionCode === names[0]);
          if (target) code.scrollTop += target.getBoundingClientRect().top - code.getBoundingClientRect().top - 8;
        }
      }
      reader.querySelectorAll('svg rect[data-stage]').forEach(rect => {
        const names = mapping[rect.dataset.stage];
        if (!names || !names.every(name => sections.some(section => section.dataset.functionCode === name))) return;
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.dataset.stepStage = rect.dataset.stage;
        group.dataset.codeFunctions = names.join(' ');
        const currentNames = () => group.dataset.codeFunctions.split(' ').filter(Boolean);
        group.setAttribute('role', 'button');
        group.setAttribute('tabindex', '0');
        group.setAttribute('aria-label', '对照 ' + names.map(name => name + '()').join('、'));
        rect.parentNode.insertBefore(group, rect);
        group.append(rect);
        const x = Number(rect.getAttribute('x')), y = Number(rect.getAttribute('y'));
        const w = Number(rect.getAttribute('width')), h = Number(rect.getAttribute('height'));
        let next = group.nextElementSibling;
        while (next && ['text', 'a'].includes(next.tagName.toLowerCase())) {
          const texts = next.tagName.toLowerCase() === 'text' ? [next] : [...next.querySelectorAll('text')];
          if (!texts.length || texts.some(text => {
            const tx = Number(text.getAttribute('x')), ty = Number(text.getAttribute('y'));
            return tx < x || tx > x+w || ty < y || ty > y+h;
          })) break;
          const element = next; next = next.nextElementSibling; group.append(element);
        }
        if (group.querySelector('a[data-function]')) group.setAttribute('role', 'group');
        steps.push(group);
        group.addEventListener('pointerenter', () => highlight(currentNames(), false));
        group.addEventListener('pointerleave', () => highlight(pinned, false));
        group.addEventListener('focus', () => highlight(currentNames(), false));
        group.addEventListener('click', event => {
          if (event.target.closest('a')) return;
          pinned = currentNames(); highlight(pinned, true);
        });
        group.addEventListener('keydown', event => {
          if (event.target !== group) return;
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault(); pinned = currentNames(); highlight(pinned, true);
          }
        });
      });
      function selectFunction(name, revealCode) {
          if (!sections.some(section => section.dataset.functionCode === name)) return;
          pinned = [name]; highlight(pinned, revealCode);
          const step = steps.find(node => node.dataset.codeFunctions.split(' ').includes(pinned[0]));
          const canvas = step && step.closest('.architecture-diagram__canvas');
          if (canvas) {
            const node = step.getBoundingClientRect(), view = canvas.getBoundingClientRect();
            if (node.top < view.top+8) canvas.scrollTop += node.top-view.top-8;
            else if (node.bottom > view.bottom-8) canvas.scrollTop += node.bottom-view.bottom+8;
            if (node.left < view.left+8) canvas.scrollLeft += node.left-view.left-8;
            else if (node.right > view.right-8) canvas.scrollLeft += node.right-view.right+8;
          }
      }
      card.selectFunction = name => {
        selectFunction(name, true);
        if (readingPack) root.dispatchEvent(new CustomEvent('diagram:function-selected', {detail:{name}}));
      };
      reader.querySelectorAll('a[data-function]').forEach(link => {
        if (sections.some(section => section.dataset.functionCode === link.dataset.function))
          bindFunctionLink(link, () => card.selectFunction(link.dataset.function));
      });
      sections.forEach(section => {
        section.querySelector('button').addEventListener('click', () => {
          selectFunction(section.dataset.functionCode, false);
          if (readingPack) root.dispatchEvent(new CustomEvent('diagram:function-selected', {detail:{name:section.dataset.functionCode}}));
        });
      });
      highlight(pinned, false);
    }

    function synchronize() {
      const card = cards.get(selected);
      const focus = card ? card.dataset.focusModule : '';
      const focusNode = links.find(link => link.dataset.module === focus);
      const stage = card ? focusNode?.dataset.overviewStage || '' : overviewStage;
      const externalFunction = !!card && anchor && !root.contains(anchor)
        && anchor.closest('[data-function-explorer]');
      root.dataset.selected = selected;
      if (!externalFunction) status.textContent = card ? '正在查看：' + card.dataset.label + '。详情紧邻所选模块。'
        : stage ? '正在追踪：' + nodeLabels.get(stage) + '。' : '默认总览：尚未选择模块。';
      panel.hidden = !card;
      if (!card) {
        manualBounds = null;
        drag = null;
        panel.classList.remove('is-resizing');
      }
      panelTitle.textContent = card ? card.dataset.label : '模块详情';
      buttons.forEach(button => button.setAttribute('aria-expanded', String(button.dataset.moduleButton === selected)));
      links.forEach(link => {
        link.setAttribute('aria-expanded', String(link.dataset.module === selected));
        link.classList.toggle('is-selected', link.dataset.module === focus);
      });
      // A function opened from figure 3 must not expand figure 2's summary
      // above the reader and trigger document scroll anchoring.
      if (!externalFunction) highlightConnections(hoveredStage || stage);
      positionPanel();
      if (readingPack) root.dispatchEvent(new CustomEvent('diagram:selection', {detail:{module:selected}}));
    }

    function closePanel(restoreFocus = false) {
      const origin = anchor;
      selected = '';
      overviewStage = '';
      hoveredStage = '';
      cards.forEach(card => { card.open = false; });
      synchronize();
      if (restoreFocus && origin) origin.focus({preventScroll:true});
    }

    function select(key, origin) {
      const target = cards.get(key);
      if (!target) return;
      const closing = selected === key && target.open;
      overviewStage = '';
      hoveredStage = '';
      anchor = origin || anchor;
      selected = closing ? '' : key;
      cards.forEach((card, candidate) => { card.open = candidate === selected; });
      if (!closing) populate(target);
      synchronize();
    }

    buttons.forEach(button => button.addEventListener('click', () => select(button.dataset.moduleButton, button)));
    links.forEach(link => {
      link.setAttribute('role', 'button');
      link.setAttribute('tabindex', '0');
      link.setAttribute('aria-expanded', 'false');
      link.setAttribute('aria-controls', root.id + '-' + link.dataset.module);
      link.addEventListener('click', event => { event.preventDefault(); select(link.dataset.module, link); });
      link.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          select(link.dataset.module, link);
        }
      });
    });
    cards.forEach((card, key) => card.addEventListener('toggle', () => {
      if (card.open) {
        selected = key;
        cards.forEach((other, otherKey) => { if (otherKey !== key) other.open = false; });
        populate(card);
      } else if (selected === key) selected = '';
      synchronize();
    }));
    root.querySelector('[data-explorer-reset]').addEventListener('click', () => closePanel());
    root.querySelector('[data-explorer-close]').addEventListener('click', () => closePanel(true));
    root.querySelector('[data-explorer-trace]').addEventListener('click', () => {
      const card = cards.get(selected);
      const node = card && links.find(link => link.dataset.module === card.dataset.focusModule);
      if (node) selectOverviewNode(node.dataset.overviewStage, node);
    });
    root.querySelector('[data-panel-enlarge]').addEventListener('click', () => {
      resizeTo({left:12,top:12,width:document.documentElement.clientWidth-24,height:window.innerHeight-24});
    });
    root.querySelector('[data-panel-size-reset]').addEventListener('click', () => {
      manualBounds = null;
      positionPanel();
    });
    resizeHandle.addEventListener('pointerdown', event => {
      if (event.button > 0) return;
      event.preventDefault();
      const bounds = panel.getBoundingClientRect();
      drag = {id:event.pointerId,x:event.clientX,y:event.clientY,
        left:bounds.left,top:bounds.top,width:bounds.width,height:bounds.height};
      panel.classList.add('is-resizing');
      // Window listeners also cover browsers without pointer capture.
      try { resizeHandle.setPointerCapture(event.pointerId); } catch (_) { /* fall back */ }
    });
    window.addEventListener('pointermove', event => {
      if (!selected || panel.hidden || !drag || event.pointerId !== drag.id) return;
      resizeTo({...drag,width:drag.width+event.clientX-drag.x,height:drag.height+event.clientY-drag.y});
    });
    function stopResize(event) {
      if (!drag || event.pointerId !== drag.id) return;
      if (resizeHandle.hasPointerCapture(event.pointerId)) resizeHandle.releasePointerCapture(event.pointerId);
      drag = null;
      panel.classList.remove('is-resizing');
    }
    window.addEventListener('pointerup', stopResize);
    window.addEventListener('pointercancel', stopResize);
    resizeHandle.addEventListener('keydown', event => {
      const delta = {ArrowRight:[32,0],ArrowLeft:[-32,0],ArrowDown:[0,32],ArrowUp:[0,-32]}[event.key];
      if (!delta) return;
      event.preventDefault();
      const bounds = panel.getBoundingClientRect();
      resizeTo({left:bounds.left,top:bounds.top,width:bounds.width+delta[0],height:bounds.height+delta[1]});
    });
    document.addEventListener('keydown', event => {
      if ((selected || overviewStage || hoveredStage) && event.key === 'Escape') {
        event.preventDefault();
        closePanel(true);
      }
    });
    window.addEventListener('resize', positionPanel);
    window.addEventListener('scroll', positionPanel, {passive:true});
    root.classList.add('is-enhanced');
    resizeHandle.hidden = false;
    root.querySelector('.diagram-explorer__panel-header').hidden = false;
    root.querySelector('.diagram-explorer__toolbar').hidden = false;
    root.querySelector('.diagram-explorer__modules').hidden = false;
    if (readingPack) root.openReadingSource = (name, origin) => {
      const ref = readingPack.references[name];
      if (!ref?.available) return;
      const node = [...overview.querySelectorAll('rect[data-file-path]')].find(rect => rect.dataset.filePath === ref.path);
      const key = node?.closest('a[data-module]')?.dataset.module;
      const card = cards.get(key);
      if (!card || !functionIndex.has(name)) return;
      anchor = origin || node;
      selected = key; overviewStage = ''; hoveredStage = '';
      cards.forEach((candidate, candidateKey) => { candidate.open = candidateKey === key; });
      populate(card); synchronize(); card.selectFunction(name);
    };
    root.dataset.ready = 'true';
    if (readingPack && window.ReadingView) window.ReadingView.attach(root, readingPack);
    synchronize();
  });
  // Standalone figures opt in independently of the overview's selected module.
  // Only preview line emphasis; function-link activation keeps its existing role.
  function enableDiagramTrace(figure) {
    if (!figure.hasAttribute('data-diagram-trace') || figure.resetDiagramTrace) return;
    const svg = figure.querySelector('svg');
    if (!svg) return;
    const nodes = [...svg.querySelectorAll('rect[data-stage]')];
    const paths = [...svg.querySelectorAll('path[data-from][data-to]')];
    if (!nodes.length || !paths.length) return;
    const prefix = (svg.getAttribute('aria-labelledby') || figure.id).split(' ')[0] + '-trace';
    let defs = svg.querySelector('defs');
    if (!defs) { defs = document.createElementNS(svg.namespaceURI, 'defs'); svg.prepend(defs); }
    const markers = new Map();
    const findMarker = ref => {
      const id = ref?.match(/url\(#([^)]+)\)/)?.[1];
      return [...defs.querySelectorAll('marker')].find(marker => marker.id === id);
    };
    const arrow = (stroke, large) => {
      const key = stroke + ':' + large;
      if (markers.has(key)) return markers.get(key);
      const marker = document.createElementNS(svg.namespaceURI, 'marker');
      marker.id = prefix + '-arrow-' + markers.size;
      for (const [name, value] of Object.entries({viewBox:'0 0 10 10',refX:'9',refY:'5',
        markerWidth:large?'12':'6',markerHeight:large?'12':'6',orient:'auto'})) marker.setAttribute(name,value);
      if (large) marker.setAttribute('markerUnits','userSpaceOnUse');
      const head = document.createElementNS(svg.namespaceURI,'path');
      head.setAttribute('d','M0 0L10 5L0 10Z'); head.setAttribute('fill',stroke);
      marker.append(head); defs.append(marker);
      const ref = 'url(#' + marker.id + ')'; markers.set(key,ref); return ref;
    };
    paths.forEach(path => {
      // Namespaced reader clones reuse the original normal/hover heads.
      const normal = path.dataset.traceNormalMarker || path.getAttribute('marker-end');
      path.dataset.traceNormalMarker = findMarker(normal) ? normal : arrow(path.getAttribute('stroke'),false);
      const selected = path.dataset.traceSelectedMarker;
      path.dataset.traceSelectedMarker = findMarker(selected) ? selected : arrow(path.getAttribute('stroke'),true);
    });
    let pointerStage = '', focusStage = '';
    const paint = stage => {
      nodes.forEach(node => node.classList.toggle('is-trace-target',node.dataset.stage === stage));
      paths.forEach(path => {
        const related = !!stage && (path.dataset.from === stage || path.dataset.to === stage);
        path.classList.toggle('is-related',related);
        path.classList.toggle('is-unrelated',!!stage && !related);
        path.setAttribute('marker-end',related ? path.dataset.traceSelectedMarker : path.dataset.traceNormalMarker);
      });
    };
    const atPoint = point => nodes.find(node => {
      const b = node.getBBox();
      return point.x >= b.x && point.x <= b.x+b.width && point.y >= b.y && point.y <= b.y+b.height;
    })?.dataset.stage || '';
    const reset = () => { pointerStage = ''; focusStage = ''; paint(''); };
    figure.resetDiagramTrace = reset;
    reset(); // A copied reader must never inherit a transient preview.
    svg.addEventListener('pointermove',event => {
      if (event.pointerType === 'touch') return;
      const matrix = svg.getScreenCTM();
      if (!matrix) return;
      pointerStage = atPoint(new DOMPoint(event.clientX,event.clientY).matrixTransform(matrix.inverse()));
      paint(pointerStage || focusStage);
    });
    svg.addEventListener('pointerleave',event => {
      if (event.pointerType === 'touch') return;
      pointerStage = ''; paint(focusStage);
    });
    svg.addEventListener('focusin',event => {
      const link = event.target.closest('a[data-function]');
      if (!link) return;
      const b = link.getBBox(); focusStage = atPoint({x:b.x+b.width/2,y:b.y+b.height/2});
      paint(pointerStage || focusStage);
    });
    svg.addEventListener('focusout',() => { focusStage = ''; paint(pointerStage); });
    // Clear before the link's capture listener clones the source and opens code.
    figure.addEventListener('click',event => { if (event.target.closest('a[data-function]')) reset(); },true);
    figure.addEventListener('keydown',event => {
      if (['Enter',' '].includes(event.key) && event.target.closest('a[data-function]')) reset();
      if (event.key === 'Escape') reset();
    },true);
    figure.querySelector('.architecture-diagram__canvas')?.addEventListener('scroll',reset,{passive:true});
    window.addEventListener('scroll',reset,{passive:true});
    window.addEventListener('resize',reset);
  }
  document.querySelectorAll('figure[data-diagram-trace]').forEach(enableDiagramTrace);
})();
