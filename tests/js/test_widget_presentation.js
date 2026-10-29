/* Catalog-wide presentation coverage without a DOM dependency. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const context = {window:{}};
for(const name of ['widgets','widget-presentation']) vm.runInNewContext(fs.readFileSync('static/js/'+name+'.js','utf8'),context);
const presentation=context.window.CCSWidgetPresentation;
assert.equal(presentation.kinds.length,29);
assert.deepEqual([...presentation.kinds].sort(),Object.keys(context.window.CS2WidgetCatalog).sort());
for(const kind of presentation.kinds){
  for(const variant of presentation.variants){
    const dimensions=presentation.minimum(kind,variant);
    assert.equal(dimensions.length,2);
    assert.ok(dimensions.every(value=>Number.isInteger(value)&&value>0));
    assert.equal((dimensions[1]+8)%40,0);
    dimensions[0]=0;
    assert.ok(presentation.minimum(kind,variant)[0]>0);
  }
}
assert.equal(presentation.minimum('unknown'),null);
assert.equal(presentation.minimum('__proto__'),null);
assert.equal(presentation.roundLabel({round:1,winner:'__proto__'}),'#1 · __proto__');
assert.equal(presentation.roundLabel({round:12,winner:'ct_win'}),'#12 · CT');
assert.equal(presentation.roundLabel({round:13,winner:'t_win'}),'#13 · T');
console.log('OK: all 29 kinds × 3 variants, grid-aligned defensive minima and round labels');
