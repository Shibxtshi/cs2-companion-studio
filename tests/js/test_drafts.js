/* Configuration-only validation, bounded history and controlled persistence races. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
Object.defineProperty(globalThis, 'crypto', {value: {getRandomValues: array => require('node:crypto').webcrypto.getRandomValues(array)}, configurable: true});
globalThis.window = globalThis;
const root = path.resolve(__dirname, '../..');
for (const file of ['draft-schema', 'draft-contract', 'edit-history', 'draft-session']) require(path.join(root, 'static/js/' + file + '.js'));
const contract = CCSDraftContract;
const corpus = JSON.parse(fs.readFileSync(path.join(root, 'tests/browser/fixtures/draft-contracts.json'), 'utf8'));
const clone = value => structuredClone(value);
corpus.draft = {...corpus.draftMetadata, name: corpus.profile.name, configuration: clone(corpus.profile.configuration)};
const content = profile => ({name: profile.name, configuration: clone(profile.configuration)});
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const errorCode = code => error => error.code === code;
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return {promise, resolve, reject};
}

for (const entry of corpus.cases) {
  const value = clone(corpus[entry.kind]);
  for (const change of entry.changes) {
    let parent = value;
    for (const key of change.path.slice(0, -1)) parent = parent[key];
    if (change.remove) delete parent[change.path.at(-1)];
    else if (change.repeatWidget) parent[change.path.at(-1)] = Array.from({length: change.repeatWidget}, (_, index) => ({...corpus.profile.configuration.layout.widgets[0], id: 'w' + index}));
    else parent[change.path.at(-1)] = clone(change.value);
  }
  const validate = () => entry.kind === 'draft' ? contract.validateDraft(value) : contract.validateProfile(value);
  if (entry.valid) assert.deepEqual(validate(), value, entry.name);
  else assert.throws(validate, errorCode('invalid_document'), entry.name);
}
const cyclic = clone(corpus.draft);
cyclic.configuration.loop = cyclic;
assert.throws(() => contract.validateDraft(cyclic), errorCode('invalid_document'));
for (const value of [NaN, Infinity, undefined, () => {}, '\ud800']) {
  assert.throws(() => contract.validateDraft({...corpus.draft, updatedAt: value}), errorCode('invalid_document'));
}
assert.throws(() => contract.access({storeId: corpus.draft.storeId, accessId: '3'.repeat(32), authenticated: false}), errorCode('access_required'));
assert.throws(() => contract.contextKey({storeId: corpus.draft.storeId, accessId: '3'.repeat(32)}), errorCode('access_required'));
const checked = contract.validateDraft(corpus.draft);
checked.configuration.layout.widgets[0].title = 'independent';
assert.equal(corpus.draft.configuration.layout.widgets[0].title, '');

for (const {id} of CCSDraftSchema.themes) {
  const themed = content(corpus.profile);
  const themeHistory = new CCSEditHistory(themed);
  themed.configuration.theme = id;
  contract.content(themed);
  if (id !== corpus.profile.configuration.theme) {
    themeHistory.commit(themed);
    assert.equal(themeHistory.value.configuration.theme, id);
    themeHistory.undo();
    assert.equal(themeHistory.value.configuration.theme, corpus.profile.configuration.theme);
    themeHistory.redo();
    assert.equal(themeHistory.value.configuration.theme, id);
  }
}
assert.throws(() => contract.content({...content(corpus.profile), configuration: {...corpus.profile.configuration, theme: 'unknown-theme'}}), errorCode('invalid_document'));

const history = new CCSEditHistory(content(corpus.profile));
const initial = history.value;
const states = [];
function edit(mutator) {
  const next = history.value;
  mutator(next);
  history.commit(next);
  states.push(history.value);
}
edit(next => next.configuration.layout.widgets.push({...next.configuration.layout.widgets[0], id: 'duplicate-instance'}));
edit(next => next.configuration.layout.widgets.splice(1, 1));
edit(next => { next.configuration.layout.widgets[0].x = 4; });
edit(next => { next.configuration.layout.widgets[0].width = 8; next.configuration.layout.widgets[0].height = 3; });
edit(next => { next.configuration.layout.widgets[0].title = 'Edited'; });
edit(next => { next.configuration.theme = 'creator-purple'; });
for (let index = states.length - 1; index >= 0; index--) {
  assert.deepEqual(history.value, states[index]);
  assert(history.undo());
}
assert.deepEqual(history.value, initial);
for (const state of states) { assert(history.redo()); assert.deepEqual(history.value, state); }
assert(!history.redo());
history.undo();
assert.equal(history.commit(history.value), false);
assert(history.canRedo);
edit(next => { next.name = 'New branch'; });
assert(!history.canRedo);
const beforeGesture = history.value;
const beforeCount = history.stats.entries;
history.beginGesture();
for (let step = 0; step < 100; step++) {
  const next = history.value;
  next.configuration.layout.widgets[0].x = step % 10;
  history.preview(next);
}
assert(!history.canUndo);
assert(history.endGesture());
assert.equal(history.stats.entries, beforeCount + 1);
history.undo();
assert.deepEqual(history.value, beforeGesture);
history.beginGesture();
const cancelled = history.value;
cancelled.name = 'Cancelled gesture';
history.preview(cancelled);
history.cancelGesture();
assert.deepEqual(history.value, beforeGesture);
for (let index = 0; index < 150; index++) edit(next => { next.name = 'Edit ' + index; });
assert.equal(history.stats.entries, 50);
assert(history.stats.bytes <= history.stats.maxBytes);
history.reset(initial);
history.beginGesture();
for (let index = 0; index < 100; index++) {
  const resized = history.value;
  resized.configuration.layout.widgets[0].width = 6 + index % 5;
  resized.configuration.layout.widgets[0].height = 2 + index % 3;
  history.preview(resized);
}
assert(history.endGesture());
assert.equal(history.stats.entries, 1);
history.undo();
assert.deepEqual(history.value, initial);
history.reset(initial);
assert.equal(history.stats.entries, 0);
assert(!history.canUndo && !history.canRedo);

class ControlledStore {
  constructor() {
    this.context = contract.access({storeId: corpus.draft.storeId, accessId: '3'.repeat(32), authenticated: true});
    this.records = new Map();
    this.writes = 0;
    this.clears = 0;
    this.failure = null;
    this.gate = null;
  }
  async read(id) { return clone(this.records.get(id) || {status: 'none', token: null}); }
  async save(value, token) {
    this.writes++;
    if (this.gate) await this.gate.promise;
    if (this.failure) throw new contract.DraftError(this.failure);
    const old = await this.read(value.profileId);
    if (old.token !== token) throw new contract.DraftError('local_conflict');
    const draft = contract.validateDraft({...value, localRevision: value.localRevision + 1});
    const stored = {status: 'valid', token: contract.uuid(), draft};
    this.records.set(value.profileId, stored);
    return clone(stored);
  }
  async remove(id, token) {
    if (this.failure) throw new contract.DraftError(this.failure);
    if ((await this.read(id)).token !== token) throw new contract.DraftError('local_conflict');
    this.records.delete(id);
  }
  async clearContext() {
    if (this.failure) throw new contract.DraftError(this.failure);
    this.clears++;
    this.records.clear();
  }
}
async function run() {
  const store = new ControlledStore();
  const published = clone(corpus.profile);
  const status = [];
  const session = await CCSDraftSession.start({store, published, choice: 'new', debounceMs: 1000, onStatus: state => status.push(state)});
  const preview = session.preview;
  preview.configuration.layout.widgets[0].title = 'Private edit';
  session.edit(preview);
  assert.equal(published.configuration.layout.widgets[0].title, '');
  preview.configuration.layout.widgets[0].title = 'External mutation';
  assert.equal(session.preview.configuration.layout.widgets[0].title, 'Private edit');
  store.gate = deferred();
  const saving = session.flush();
  assert.equal(session.flush(), saving);
  assert.equal(session.state.status, 'saving');
  assert(!status.some(state => state.code === 'saved'));
  const later = session.preview;
  later.name = 'Latest coherent state';
  session.edit(later);
  store.gate.resolve();
  await saving;
  store.gate = null;
  assert.equal(store.writes, 2);
  assert.equal((await store.read(published.id)).draft.name, 'Latest coherent state');
  assert.equal(session.state.status, 'saved');
  const baseline = session.draft;
  assert.equal(baseline.localRevision, 2);
  session.beginGesture();
  for (let step = 0; step < 100; step++) {
    const next = session.preview;
    next.configuration.layout.widgets[0].y = step;
    session.previewGesture(next);
  }
  assert(session.state.gestureActive && session.state.dirty);
  await assert.rejects(session.flush(), errorCode('gesture_active'));
  assert.equal(store.writes, 2);
  session.endGesture();
  await session.flush();
  assert.equal(store.writes, 3);
  session.undo();
  await session.flush();
  assert.equal((await store.read(published.id)).draft.configuration.layout.widgets[0].y, baseline.configuration.layout.widgets[0].y);
  session.redo();
  await session.flush();
  session.dispose();
  const found = await CCSDraftSession.inspect({store, profileId: published.id, published});
  assert.equal(found.status, 'available');
  const restored = await CCSDraftSession.start({store, published, choice: 'resume', debounceMs: 1000});
  assert.equal(restored.state.history.entries, 0);
  assert(!restored.state.canUndo);
  const snapshot = await restored.publicationSnapshot();
  assert.equal(snapshot.baseRevision, 7);
  assert.equal(await CCSDraftSession.inspect({store, profileId: published.id, published: {...published, revision: 8}}).then(result => result.status), 'remote_newer');
  assert.equal(await CCSDraftSession.inspect({store, profileId: published.id, published: null}).then(result => result.status), 'profile_deleted');
  await assert.rejects(CCSDraftSession.start({store, published: {...published, revision: 8}, choice: 'resume'}), errorCode('remote_newer'));
  assert.deepEqual(await CCSDraftSession.logout({store, confirmed: false}), {status: 'cancelled'});
  assert.equal(store.clears, 0);
  for (const code of ['quota_exceeded', 'transaction_aborted', 'local_conflict', 'storage_unavailable']) {
    store.failure = code;
    const next = restored.preview;
    next.name = code;
    restored.edit(next);
    await assert.rejects(restored.keepAndLeave(), errorCode(code));
    assert.equal(restored.state.status, 'error');
    assert(!restored.state.closed);
    assert.equal((await store.read(published.id)).draft.name, snapshot.name);
  }
  store.failure = 'transaction_aborted';
  await assert.rejects(restored.discard(), errorCode('transaction_aborted'));
  assert(!restored.state.closed);
  await assert.rejects(CCSDraftSession.logout({store, confirmed: true}), errorCode('transaction_aborted'));
  assert(store.records.size > 0);
  store.failure = null;
  await restored.keepAndLeave();
  assert.equal(restored.state.status, 'kept');
  assert(restored.state.closed);
  const resumed = await CCSDraftSession.start({store, published, choice: 'resume', debounceMs: 1000});
  await resumed.discard();
  assert.equal((await store.read(published.id)).status, 'none');
  await CCSDraftSession.logout({store, confirmed: true});
  assert.equal(store.clears, 1);

  const coalesced = new ControlledStore();
  const burst = await CCSDraftSession.start({store: coalesced, published, choice: 'new', debounceMs: 20});
  for (let index = 0; index < 100; index++) { const next = burst.preview; next.name = 'Burst ' + index; burst.edit(next); }
  await delay(60);
  await burst.flush();
  assert.equal(coalesced.writes, 1);
  await burst.keepAndLeave();
  const serialized = JSON.stringify([...coalesced.records]);
  for (const forbidden of ['synthetic-forbidden-secret', 'GSI_TOKEN', 'DASHBOARD_PIN', 'weapons', 'diagnostics']) assert(!serialized.includes(forbidden));
  const localCreation = new ControlledStore();
  const creation = {id: 'new-local-profile', name: 'Unpublished', configuration: structuredClone(published.configuration)};
  const created = await CCSDraftSession.start({store: localCreation, creation, choice: 'new'});
  await created.flush();
  assert.equal(created.draft.baseRevision, 0);
  await created.keepAndLeave();
  const creationResumed = await CCSDraftSession.start({store: localCreation, creation, choice: 'resume'});
  assert.equal(creationResumed.draft.baseRevision, 0);
  assert.equal(creationResumed.state.history.entries, 0);
  await creationResumed.discard();
  const deferredStore = new ControlledStore();
  const suspendedSession = await CCSDraftSession.start({store: deferredStore, published, choice: 'new', persistOnStart: false});
  await delay(250);
  assert.equal(deferredStore.writes, 0);
  assert.equal(suspendedSession.state.status, 'pristine');
  assert.equal(suspendedSession.state.hasPersistedDraft, false);
  const deferredSnapshot = await suspendedSession.publicationSnapshot();
  assert.equal(deferredStore.writes, 1);
  assert.equal(suspendedSession.state.hasPersistedDraft, true);
  assert.equal(deferredSnapshot.baseRevision, published.revision);
  suspendedSession.dispose();
  console.log('OK: P3 semantic corpus, all 29 kinds, history/gestures, isolated copies, ordered local persistence, quota/abort/conflict, resume/exit/logout and coalescing');
}
run().catch(error => { console.error(error); process.exitCode = 1; });
