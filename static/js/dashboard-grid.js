/* Target X/Y adapter. Layout updates are separate from live widget value updates. */
(() => {
  'use strict';
  window.CCSDashboardGrid = ({board, onStatus = () => {}}) => {
    let layout = null;
    let frame = null;
    let previousWidth = -1;
    const originalStyles = new Map();
    function apply() {
      frame = null;
      if (!layout || board.clientWidth <= 0) return;
      const projection = window.CCSDashboardLayout.project(layout, board.clientWidth);
      board.classList.add('xy-board');
      board.style.setProperty('--grid-columns', projection.columns);
      board.dataset.layoutMode = projection.mode;
      let renderIndex = 0;
      const cards = new Map([...board.children].map(card => [card.dataset.id, card]));
      for (const item of projection.items) {
        const card = cards.get(item.id);
        if (!card) continue;
        if (!originalStyles.has(card)) originalStyles.set(card, card.getAttribute('style'));
        card.style.gridColumn = (item.x + 1) + ' / span ' + item.width;
        card.style.gridRow = (item.y + 1) + ' / span ' + item.height;
        card.classList.remove('layout-fallback');
        const body = card.querySelector('.widget-body');
        if (body) { body.setAttribute('role', 'region'); body.setAttribute('aria-label', card.querySelector('.widget-heading')?.textContent || item.id); }
        const expected = board.children[renderIndex++];
        if (expected !== card) board.insertBefore(card, expected || null);
      }
      let fallbackY = Math.max(0, ...projection.items.map(item => item.y + item.height));
      for (const item of projection.fallback) {
        const card = cards.get(item.id);
        if (!card) continue;
        card.classList.add('layout-fallback');
        card.style.gridColumn = '1 / -1';
        const minimumHeight = window.CCSDashboardLayout.minimum(card.dataset.kind)[1];
        const fallbackRows = Math.max(5, Math.ceil((minimumHeight + 8) / 40));
        card.style.gridRow = (fallbackY + 1) + ' / span ' + fallbackRows;
        fallbackY += fallbackRows;
        const expected = board.children[renderIndex++];
        if (expected !== card) board.insertBefore(card, expected || null);
      }
      refreshContent();
      onStatus(projection.fallback.length ? 'layout_overflow' : 'layout_ready');
    }
    function refreshContent() {
      for (const body of board.querySelectorAll('.widget-body')) {
        if (body.scrollHeight > body.clientHeight + 1 || body.scrollWidth > body.clientWidth + 1) body.tabIndex = 0;
        else body.removeAttribute('tabindex');
      }
    }
    const observer = new ResizeObserver(entries => {
      const width = Math.round(entries[0].contentRect.width);
      if (width === previousWidth) return;
      previousWidth = width;
      if (frame === null) frame = requestAnimationFrame(apply);
    });
    observer.observe(board);
    return Object.freeze({
      setLayout(next) {
        for (const card of originalStyles.keys()) if (!board.contains(card)) originalStyles.delete(card);
        layout = structuredClone(next); apply();
      },
      refresh: apply, refreshContent,
      dispose() {
        observer.disconnect();
        if (frame !== null) cancelAnimationFrame(frame);
        for (const [card, style] of originalStyles) {
          if (style === null) card.removeAttribute('style'); else card.setAttribute('style', style);
        }
        board.classList.remove('xy-board');
        board.style.removeProperty('--grid-columns');
        delete board.dataset.layoutMode;
        layout = null;
      },
    });
  };
})();
