/* Pure display projection. Saved profile geometry is never mutated. */
(() => {
  'use strict';
  const ROW_HEIGHT = 32;
  const GAP = 8;
  const MAX_DISPLAY_ROWS = 8192;
  const MINIMUMS = Object.freeze({
    round: [200, 192], bomb: [280, 272], score: [280, 152], score_split: [280, 152],
    stats: [300, 192], round_stats: [280, 192], forecast: [300, 232],
    economy: [280, 192], inventory: [280, 192], events: [280, 232],
    weapon: [240, 192], gear: [240, 192], effects: [240, 192],
  });
  const minimum = kind => MINIMUMS[kind] || [200, 152];
  const intersects = (a, b) => a.x < b.x + b.width && a.x + a.width > b.x
    && a.y < b.y + b.height && a.y + a.height > b.y;
  const rows = height => Math.ceil((height + GAP) / (ROW_HEIGHT + GAP));

  function project(layout, availableWidth) {
    if (!Number.isFinite(availableWidth) || availableWidth <= 0) throw new Error('invalid_container');
    if (!Number.isInteger(layout.columns) || layout.columns < 1 || layout.columns > 64
        || !Array.isArray(layout.widgets) || layout.widgets.length > 60) throw new Error('invalid_layout');
    const columns = layout.columns;
    const desktop = availableWidth >= columns * 32 + (columns - 1) * GAP;
    const count = desktop ? columns : availableWidth >= 600 ? Math.min(12, columns) : 1;
    const cellWidth = (availableWidth - (count - 1) * GAP) / count;
    const placed = [];
    const fallback = [];
    const ordered = layout.widgets.map((widget, index) => ({...widget, index}))
      .sort((a, b) => a.y - b.y || a.x - b.x || a.index - b.index);
    for (const widget of ordered) {
      for (const key of ['x', 'y', 'width', 'height']) {
        if (!Number.isInteger(widget[key])) throw new Error('invalid_geometry');
      }
      if (widget.x < 0 || widget.y < 0 || widget.width < 1 || widget.height < 1
          || widget.x + widget.width > columns || widget.y + widget.height > 4096) {
        throw new Error('invalid_geometry');
      }
      const [minWidth, minHeight] = minimum(widget.kind);
      const minColumns = Math.min(count, Math.ceil((minWidth + GAP) / (cellWidth + GAP)));
      const width = Math.min(count, Math.max(minColumns, Math.ceil(widget.width * count / columns)));
      const height = Math.max(widget.height, rows(minHeight));
      const x = desktop ? Math.min(widget.x, count - width) : 0;
      const item = {id: widget.id, x, y: desktop ? widget.y : 0, width, height};
      let found = false;
      // Each collision jumps below at least one placed rectangle. The bound is independent of input Y.
      for (let attempt = 0; attempt <= placed.length; attempt++) {
        const collisions = placed.filter(other => intersects(item, other));
        if (!collisions.length && item.y + height <= MAX_DISPLAY_ROWS) { found = true; break; }
        if (desktop) {
          if (!collisions.length) break;
          item.y = Math.max(...collisions.map(other => other.y + other.height));
        } else {
          // Stable row-major packing never inserts a later widget before the previous one.
          const previous = placed.at(-1);
          item.y = Math.max(item.y, previous?.y || 0);
          let position = null;
          const candidates = [...new Set([item.y, ...placed.map(other => other.y + other.height)])]
            .filter(y => y >= item.y).sort((a, b) => a - b);
          for (const y of candidates) {
            for (let col = 0; col <= count - width; col++) {
              const candidate = {...item, x: col, y};
              if (previous && y === previous.y && col < previous.x) continue;
              if (!placed.some(other => intersects(candidate, other))) { position = candidate; break; }
            }
            if (position) break;
          }
          if (!position) break;
          Object.assign(item, position);
        }
      }
      if (found) placed.push(item);
      else fallback.push({...item, reason: 'layout_overflow'});
    }
    return {mode: desktop ? 'desktop' : count === 1 ? 'mobile' : 'intermediate',
      columns: count, rowHeight: ROW_HEIGHT, gap: GAP, items: placed, fallback};
  }

  window.CCSDashboardLayout = Object.freeze({project, minimum, ROW_HEIGHT, GAP, MAX_DISPLAY_ROWS});
})();
