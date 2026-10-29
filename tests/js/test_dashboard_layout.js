/* Pure layout characterization; no browser or private profiles. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const context = {window: {}};
vm.runInNewContext(fs.readFileSync('static/js/dashboard-layout.js', 'utf8'), context);
const engine = context.window.CCSDashboardLayout;
const widget = (id, x = 0, y = 0, width = 6, height = 4) => ({id, kind: 'health', x, y, width, height});
const layout = {columns: 24, widgets: [widget('a'), widget('b'), widget('c', 12)]};
const source = JSON.stringify(layout);
const desktop = engine.project(layout, 1600);
assert.equal(desktop.items.length, 3);
assert.equal(desktop.items[0].y, 0);
assert.equal(desktop.items[1].y, 4);
assert.equal(desktop.items[2].x, 12);
assert.equal(JSON.stringify(layout), source);
for (const width of [1600, 900, 768, 390, 320]) {
  const dense = {columns: 24, widgets: Array.from({length: 60}, (_, i) => widget(String(i), 0, 0))};
  const result = engine.project(dense, width);
  assert.equal(result.items.length + result.fallback.length, 60);
  assert.equal(result.fallback.length, 0);
  assert.equal(JSON.stringify(result), JSON.stringify(engine.project(dense, width)));
  for (const card of result.items) {
    assert.ok(card.x >= 0 && card.x + card.width <= result.columns);
    for (const other of result.items) {
      if (card === other) continue;
      assert.ok(card.x + card.width <= other.x || other.x + other.width <= card.x
        || card.y + card.height <= other.y || other.y + other.height <= card.y);
    }
  }
}
const extreme = engine.project({columns: 24, widgets: Array.from({length: 60}, (_, i) => widget(String(i), 0, 0, 24, 4096))}, 1600);
assert.equal(extreme.items.length + extreme.fallback.length, 60);
assert.ok(extreme.fallback.length > 0);
assert.equal(engine.project({columns: 24, widgets: []}, 320).items.length, 0);
assert.throws(() => engine.project({columns:24, widgets:[widget('x', -1)]},1600));
assert.equal(JSON.stringify(engine.project(layout,1600)), JSON.stringify(desktop));
console.log('Dashboard layout: deterministic collision, reflow, bounds and overflow checks passed');
