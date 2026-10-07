(() => {
  'use strict';
  document.querySelectorAll('[data-lecture-flow]').forEach(root => {
    if (root.dataset.ready === 'true') return;
    const nodes = [...root.querySelectorAll('[data-flow-node]')];
    const edges = [...root.querySelectorAll('[data-flow-edge]')];
    function trace(key) {
      edges.forEach(edge => {
        const related = !!key && (edge.dataset.from === key || edge.dataset.to === key);
        edge.classList.toggle('is-related', related);
        edge.classList.toggle('is-unrelated', !!key && !related);
      });
    }
    nodes.forEach(node => {
      node.setAttribute('tabindex', '0');
      node.addEventListener('pointerenter', () => trace(node.dataset.flowNode));
      node.addEventListener('pointerleave', () => trace(''));
      node.addEventListener('focus', () => trace(node.dataset.flowNode));
      node.addEventListener('blur', () => trace(''));
    });
    root.dataset.ready = 'true';
  });
})();
