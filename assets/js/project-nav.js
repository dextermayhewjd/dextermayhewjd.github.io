(() => {
  document.querySelectorAll('.project-nav').forEach(nav => {
    const desktop = nav.querySelector('.project-nav__desktop');
    const mobile = nav.querySelector('.project-nav__mobile');
    const mobileContent = nav.querySelector('.project-nav__mobile-content');
    const panels = [
      {name: 'desktop', tree: desktop, container: nav},
      {name: 'mobile', tree: mobileContent, container: mobileContent},
    ].filter(panel => panel.tree && panel.container);
    let scheduled = false;

    const key = (panel, kind) => `project-nav:${nav.dataset.projectNav}:${panel.name}:${kind}`;
    const read = (panel, kind) => {
      try {
        return JSON.parse(sessionStorage.getItem(key(panel, kind)));
      } catch (_) {
        return null;
      }
    };
    const write = (panel, kind, value) => {
      try {
        sessionStorage.setItem(key(panel, kind), JSON.stringify(value));
      } catch (_) {
        // Revealing the current chapter still works without browser storage.
      }
    };
    const branchKey = branch => {
      const summary = branch.querySelector(':scope > summary');
      return branch.dataset.lessonGroup ||
        summary?.querySelector('a[href]')?.getAttribute('href') || summary?.textContent.trim();
    };
    const save = panel => {
      if (panel.restored) write(panel, 'scroll', panel.container.scrollTop);
    };

    panels.forEach(panel => {
      const branches = [...panel.tree.querySelectorAll('.project-nav__branch')];
      const states = read(panel, 'branches');
      if (states && typeof states === 'object') {
        branches.forEach(branch => {
          const value = states[branchKey(branch)];
          if (typeof value === 'boolean') branch.open = value;
        });
      }
      const current = panel.tree.querySelector('[aria-current="page"]');
      if (current) {
        branches.forEach(branch => {
          if (branch.contains(current)) branch.open = true;
        });
      }
      panel.tree.addEventListener('toggle', event => {
        if (!event.target.matches('.project-nav__branch')) return;
        write(panel, 'branches', Object.fromEntries(
          branches.map(branch => [branchKey(branch), branch.open])
        ));
      }, true);
      panel.container.addEventListener('scroll', () => save(panel), {passive: true});
    });

    const follow = () => {
      scheduled = false;
      const useDesktop = desktop && getComputedStyle(desktop).display !== 'none';
      const panel = panels.find(item => item.name === (useDesktop ? 'desktop' : 'mobile'));
      if (!panel || (!useDesktop && !mobile?.open) || !panel.container.clientHeight) return;
      const container = panel.container;
      const restoring = !panel.restored;
      if (restoring) {
        const offset = read(panel, 'scroll');
        panel.hadPosition = Number.isFinite(offset) && offset >= 0;
        panel.restored = true;
        if (panel.hadPosition) container.scrollTop = offset;
      }
      const current = panel.tree.querySelector('.project-nav__link[aria-current="page"]');
      if (!current || !current.getClientRects().length) return;
      const viewport = container.getBoundingClientRect();
      const link = current.getBoundingClientRect();
      const top = viewport.top + container.clientTop;
      const bottom = top + container.clientHeight;
      if (link.top < top + 12 || link.bottom > bottom - 12) {
        // Change only the menu scroll position; leave the article and focus alone.
        if (restoring && !panel.hadPosition) {
          container.scrollTop += link.top - top - (container.clientHeight - link.height) / 2;
        } else {
          container.scrollTop += link.top < top + 12 ? link.top - top - 12 : link.bottom - bottom + 12;
        }
      }
    };
    const schedule = () => {
      if (scheduled) return;
      scheduled = true;
      requestAnimationFrame(follow);
    };
    const saveAll = () => panels.forEach(save);
    nav.addEventListener('click', event => {
      if (event.target.closest('a[href]')) saveAll();
    });
    window.addEventListener('pagehide', saveAll);
    window.addEventListener('pageshow', schedule);
    window.addEventListener('resize', schedule);
    if (mobile) mobile.addEventListener('toggle', schedule);
    if (document.fonts) document.fonts.ready.then(schedule);
    schedule();
  });
})();
