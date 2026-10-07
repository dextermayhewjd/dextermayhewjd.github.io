(() => {
  'use strict';
  document.querySelectorAll('[data-lecture-map]').forEach(root => {
    if (root.dataset.ready === 'true') return;
    const nodes = [...root.querySelectorAll('[data-lecture-node]')];
    const cards = [...root.querySelectorAll('[data-lecture-card]')];
    const edges = [...root.querySelectorAll('[data-lecture-edge]')];
    const buttons = [...root.querySelectorAll('[data-lecture-select]')];
    const relations = root.querySelector('[data-lecture-relations]');
    const labels = new Map(nodes.map(node => [node.dataset.lectureNode, node.getAttribute('aria-label')]));
    let selected = '';

    function trace(key) {
      const descriptions = [];
      edges.forEach(edge => {
        const related = !!key && (edge.dataset.from === key || edge.dataset.to === key);
        edge.classList.toggle('is-related', related);
        edge.classList.toggle('is-unrelated', !!key && !related);
        if (related) descriptions.push(labels.get(edge.dataset.from) + ' → ' + labels.get(edge.dataset.to) + '：' + edge.dataset.reason);
      });
      relations.textContent = descriptions.join('；');
      relations.hidden = !descriptions.length;
    }

    function synchronize() {
      nodes.forEach(node => {
        const active = node.dataset.lectureNode === selected;
        node.setAttribute('aria-expanded', String(active));
        node.classList.toggle('is-selected', active);
      });
      buttons.forEach(button => button.setAttribute('aria-expanded', String(button.dataset.lectureSelect === selected)));
      cards.forEach(card => { card.open = card.dataset.lectureCard === selected; });
      trace(selected);
    }

    function select(key) {
      selected = selected === key ? '' : key;
      synchronize();
    }

    nodes.forEach(node => {
      const key = node.dataset.lectureNode;
      node.setAttribute('role', 'button');
      node.setAttribute('tabindex', '0');
      node.setAttribute('aria-controls', root.id + '-' + key);
      node.addEventListener('pointerenter', () => trace(key));
      node.addEventListener('pointerleave', () => trace(selected));
      node.addEventListener('focus', () => trace(key));
      node.addEventListener('blur', () => trace(selected));
      node.addEventListener('click', event => { event.preventDefault(); select(key); });
      node.addEventListener('keydown', event => {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        event.preventDefault(); select(key);
      });
    });
    buttons.forEach(button => button.addEventListener('click', () => select(button.dataset.lectureSelect)));
    cards.forEach(card => card.addEventListener('toggle', () => {
      if (card.open && selected !== card.dataset.lectureCard) {
        selected = card.dataset.lectureCard;
        synchronize();
      } else if (!card.open && selected === card.dataset.lectureCard) {
        selected = '';
        synchronize();
      }
    }));
    root.querySelector('[data-lecture-reset]').addEventListener('click', () => { selected = ''; synchronize(); });
    root.addEventListener('keydown', event => {
      if (event.key === 'Escape') { selected = ''; synchronize(); }
    });
    root.querySelector('.lecture-map__controls').hidden = false;
    root.dataset.ready = 'true';
    synchronize();
  });
})();
