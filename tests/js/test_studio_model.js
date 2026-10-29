/* P8 saved-geometry operations, with no DOM, storage or network. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
globalThis.window = globalThis;
Object.defineProperty(globalThis, 'crypto', {value: require('node:crypto').webcrypto, configurable: true});
for (const name of ['draft-schema', 'draft-contract', 'widgets', 'widget-presentation', 'studio-model']) {
  require('../../static/js/' + name + '.js');
}
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, '../browser/fixtures/draft-contracts.json'), 'utf8'));
const content = {name: fixture.profile.name, configuration: structuredClone(fixture.profile.configuration)};
const base = content.configuration.layout.widgets[0];
content.configuration.layout = {columns: 24, widgets: [
  {...base, id: 'a', x: 0, y: 0, width: 6, height: 4},
  {...base, id: 'b', x: 6, y: 0, width: 6, height: 4},
]};
const original = JSON.stringify(content);
const layout = content.configuration.layout;
assert.equal(CCSStudioModel.placement(layout, 'a', {x: 6}).code, 'collision');
assert.equal(CCSStudioModel.placement(layout, 'a', {x: -1}).code, 'geometry_bounds');
assert.equal(CCSStudioModel.placement(layout, 'a', {height: 4097}).code, 'geometry_bounds');
assert.equal(CCSStudioModel.placement(layout, 'a', {x: .5}).valid, false);
assert.equal(CCSStudioModel.placement(layout, 'a', {y: 4}).valid, true);
assert.throws(() => CCSStudioModel.changeWidget(content, 'a', {x: 6}, {geometry: true}), error => error.code === 'collision');
const moved = CCSStudioModel.changeWidget(content, 'a', {y: 4}, {geometry: true});
assert.equal(moved.configuration.layout.widgets[1].x, 6);
assert.equal(moved.configuration.layout.widgets[1].y, 0);
assert.equal(JSON.stringify(content), original);
for (const kind of Object.keys(CS2WidgetCatalog)) {
  const result = CCSStudioModel.add(content, kind);
  const widget = result.content.configuration.layout.widgets.at(-1);
  assert.equal(widget.kind, kind);
  assert.equal(widget.variant, 'standard');
  for (const other of layout.widgets) assert.equal(CCSStudioModel.overlaps(widget, other), false);
  assert.equal(CCSStudioModel.remove(result.content, result.id).configuration.layout.widgets.length, 2);
}
const duplicate = CCSStudioModel.add(content, base.kind, {...layout.widgets[0], variant: 'minimal', color: '#123456'});
assert.notEqual(duplicate.id, 'a');
assert.equal(duplicate.content.configuration.layout.widgets.at(-1).variant, 'minimal');
assert.equal(duplicate.content.configuration.layout.widgets.at(-1).color, '#123456');
const crowded = structuredClone(content);
crowded.configuration.layout.widgets = Array.from({length: 59}, (_, i) => ({...base, id: 'crowded-' + i, x: 0, y: i * 4, width: 24, height: 4}));
const sixty = CCSStudioModel.add(crowded, 'health');
assert.equal(sixty.content.configuration.layout.widgets.length, 60);
assert.throws(() => CCSStudioModel.add(sixty.content, 'health'), error => error.code === 'widget_limit');
const inherited = structuredClone(content);
inherited.configuration.layout.widgets[1].x = 0;
assert.equal(CCSStudioModel.placement(inherited.configuration.layout, 'a', {y: 4}).valid, true);
assert.equal(JSON.stringify(content), original);
console.log('OK: snap-cell bounds, rejected collisions, unchanged neighbours, 29 additions, duplication, 60-instance limit and immutable inputs');
