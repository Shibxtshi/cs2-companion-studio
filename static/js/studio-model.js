/* Configuration-only Studio operations. No transport, storage or live data. */
(() => {
  'use strict';
  const contract = CCSDraftContract;
  const MAX_ROWS = 4096;
  const overlaps = (a, b) => a.x < b.x + b.width && b.x < a.x + a.width
    && a.y < b.y + b.height && b.y < a.y + a.height;
  function placement(layout, id, rectangle) {
    const previous = layout.widgets.find(widget => widget.id === id);
    if (!previous) return {valid: false, code: 'widget_missing'};
    const next = {...previous, ...rectangle};
    if (['x', 'y', 'width', 'height'].some(key => !Number.isInteger(next[key]))
        || next.x < 0 || next.y < 0 || next.width < 1 || next.height < 1
        || next.x + next.width > layout.columns || next.y + next.height > MAX_ROWS) {
      return {valid: false, code: 'geometry_bounds'};
    }
    const collisions = layout.widgets.filter(widget => widget.id !== id && overlaps(next, widget));
    return {valid: collisions.length === 0, code: collisions.length ? 'collision' : 'ready',
      collisions: collisions.map(widget => widget.id), rectangle: next};
  }
  function changeWidget(content, id, changes, {geometry = false} = {}) {
    const next = contract.content(content);
    const layout = next.configuration.layout;
    const index = layout.widgets.findIndex(widget => widget.id === id);
    if (index < 0) contract.fail('widget_missing');
    if (geometry) {
      const result = placement(layout, id, changes);
      if (!result.valid) contract.fail(result.code);
    }
    layout.widgets[index] = {...layout.widgets[index], ...changes};
    return contract.content(next);
  }
  function add(content, kind, source = null) {
    if (!Object.hasOwn(CS2WidgetCatalog, kind)) contract.fail('invalid_widget');
    const next = contract.content(content);
    const layout = next.configuration.layout;
    if (layout.widgets.length >= 60) contract.fail('widget_limit');
    const [minimumWidth, minimumHeight] = CCSWidgetPresentation.minimum(kind, source?.variant || 'standard');
    const widget = source ? {...source, id: contract.uuid()} : {
      id: contract.uuid(), kind, x: 0, y: 0,
      width: Math.min(layout.columns, Math.max(6, Math.ceil((minimumWidth + 8) / 40))),
      height: Math.max(4, Math.ceil((minimumHeight + 8) / 40)),
      variant: 'standard', style: 'solid', title: '', color: '', background: '', opacity: 100,
    };
    widget.x = Math.min(widget.x, layout.columns - widget.width);
    // Jump below intersecting rectangles; at most one step per existing widget.
    for (let attempt = 0; attempt <= layout.widgets.length; attempt++) {
      const hits = layout.widgets.filter(other => overlaps(widget, other));
      if (!hits.length) {
        layout.widgets.push(widget);
        return {content: contract.content(next), id: widget.id};
      }
      widget.y = Math.max(...hits.map(other => other.y + other.height));
      if (widget.y + widget.height > MAX_ROWS) break;
    }
    contract.fail('geometry_bounds');
  }
  function remove(content, id) {
    const next = contract.content(content);
    next.configuration.layout.widgets = next.configuration.layout.widgets.filter(widget => widget.id !== id);
    return contract.content(next);
  }
  window.CCSStudioModel = Object.freeze({placement, changeWidget, add, remove, overlaps});
})();
