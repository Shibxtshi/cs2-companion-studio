/* Target catalog, explicit consent, immutable operations and draft finalization. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
globalThis.window = globalThis;
Object.defineProperty(globalThis, 'crypto', {value: {getRandomValues: array => require('node:crypto').webcrypto.getRandomValues(array)}, configurable: true});
for (const file of ['draft-schema', 'draft-contract', 'edit-history', 'draft-session', 'published-profiles', 'profile-publication']) require('../../static/js/' + file + '.js');
const contract = CCSDraftContract;
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, '../browser/fixtures/draft-contracts.json'), 'utf8'));
const clone = value => structuredClone(value);
const profile = fixture.profile;
const catalog = {format: 'ccs-dashboard-catalog', version: 1, storeId: '1'.repeat(32), accessId: '3'.repeat(32),
  catalogRevision: 7, profiles: [clone(profile), {...clone(profile), id: 'p-second'}], tombstones: []};
const content = value => ({name: value.name, configuration: clone(value.configuration)});
const code = expected => error => error.code === expected;
const tick = () => new Promise(resolve => setImmediate(resolve));
async function until(predicate) { for (let index = 0; index < 100; index++) { if (predicate()) return; await tick(); } assert.fail('Expected asynchronous state'); }
function sync(preferredProfile = profile.id) {
  const result = CCSPublishedProfiles({send: () => {}, preferredProfile});
  result.receive({type: 'auth_ok'});
  result.receive({type: 'profiles_catalog', catalog});
  return result;
}
function receipt(operation) {
  return {operationId: operation.operationId, requestDigest: 'a'.repeat(64), result: {
    kind: operation.kind, profileId: operation.profileId, revision: operation.expectedRevision + 1, catalogRevision: 20}};
}
class MemoryStore {
  constructor() {
    this.context = contract.access({storeId: catalog.storeId, accessId: catalog.accessId, authenticated: true});
    this.records = new Map(); this.journal = new Map(); this.failure = null;
  }
  async read(id) { return clone(this.records.get(id) || {status: 'none', token: null}); }
  async save(draft, token) {
    if ((await this.read(draft.profileId)).token !== token) contract.fail('local_conflict');
    const result = {status: 'valid', token: contract.uuid(), draft: {...clone(draft), localRevision: draft.localRevision + 1}};
    this.records.set(draft.profileId, result); return clone(result);
  }
  async pendingPublication(id) { return clone(this.journal.get(id) || {status: 'none', token: null}); }
  async queuePublication(operation, capture, {replaceToken = null} = {}) {
    if (this.failure) contract.fail(this.failure);
    contract.validateOperation(operation);
    const old = await this.pendingPublication(operation.profileId);
    if (old.token !== replaceToken) contract.fail('local_conflict');
    const next = {status: 'pending', token: contract.uuid(), operation: clone(operation), capture: clone(capture)};
    this.journal.set(operation.profileId, next); return clone(next);
  }
  async completePublication(id, token, ack, {preserveDraft = false} = {}) {
    if (this.failure) contract.fail(this.failure);
    const pending = await this.pendingPublication(id);
    if (pending.token !== token) contract.fail('local_conflict');
    contract.checkReceipt(pending.operation, ack);
    const draft = await this.read(id);
    const removed = !!pending.capture && draft.token === pending.capture.token && !preserveDraft;
    if (removed) this.records.delete(id);
    this.journal.delete(id);
    return {draftRemoved: removed, draftRetained: !!pending.capture && !removed};
  }
  async abandonPublication(id, token, capture) {
    if ((await this.pendingPublication(id)).token !== token || (capture && (await this.read(id)).token !== capture.token)) contract.fail('local_conflict');
    if (capture) this.records.delete(id);
    this.journal.delete(id);
  }
  async remove(id, token) { if ((await this.read(id)).token !== token) contract.fail('local_conflict'); this.records.delete(id); }
}
async function setup() {
  const store = new MemoryStore();
  const session = await CCSDraftSession.start({store, published: profile, choice: 'new', debounceMs: 1000});
  session.edit({...session.preview, name: 'My local draft'});
  const profiles = sync();
  const sent = [];
  const controller = CCSProfilePublication({store, profiles, session, profileId: profile.id,
    send: command => sent.push(clone(command)), timeoutMs: 1000});
  return {store, session, profiles, sent, controller};
}
async function acknowledge(test, index = 0) {
  const operation = test.sent[index].operation;
  await test.controller.receive({type: 'profile_operation_ack', storeId: operation.storeId, receipt: receipt(operation), replayed: false});
}
async function conflict(test, revision = 8) {
  const latest = {...clone(catalog), catalogRevision: revision,
    profiles: catalog.profiles.map(value => value.id === profile.id ? {...clone(value), revision, name: 'Server newer'} : clone(value))};
  const message = {type: 'profile_operation_error', operationId: test.sent.at(-1).operation.operationId, code: 'revision_conflict', catalog: latest};
  test.profiles.receive(message);
  await test.controller.receive(message);
}
async function run() {
  const a = sync(), b = sync('p-second');
  const next = {...clone(catalog), catalogRevision: 8,
    profiles: catalog.profiles.map(value => value.id === profile.id ? {...clone(value), revision: 8} : clone(value))};
  a.receive({type: 'profiles_catalog', catalog: next}); b.receive({type: 'profiles_catalog', catalog: next});
  assert.equal(a.selectedProfileId, profile.id); assert.equal(b.selectedProfileId, 'p-second');
  a.receive({type: 'profiles_catalog', catalog});
  assert.equal(a.profile(profile.id).revision, 8);
  const snapshot = a.catalog; snapshot.profiles[0].name = 'Outside mutation';
  assert.notEqual(a.profile(profile.id).name, 'Outside mutation');
  a.disconnected(); assert(!a.ready && a.context === null);
  const demo = CCSPublishedProfiles({send: () => assert.fail('Demo send'), isDemo: () => true});
  demo.receive({type: 'auth_ok'}); demo.receive({type: 'profiles_catalog', catalog}); assert(!demo.ready && demo.catalog === null);

  let publicDemo = false;
  const dynamicDemo = CCSPublishedProfiles({send: () => {}, isDemo: () => publicDemo});
  dynamicDemo.receive({type: 'auth_ok'}); dynamicDemo.receive({type: 'profiles_catalog', catalog});
  assert(dynamicDemo.catalog);
  publicDemo = true;
  assert.equal(dynamicDemo.catalog, null); assert.equal(dynamicDemo.context, null);
  assert.equal(dynamicDemo.profile(profile.id), null); assert.equal(dynamicDemo.selectedProfileId, null);
  assert.throws(() => dynamicDemo.request(), code('access_required'));

  const success = await setup();
  const first = success.controller.publish();
  success.controller.publish();
  await until(() => success.sent.length === 1);
  assert.equal(success.controller.state.code, 'publishing');
  assert.throws(() => success.session.edit({...success.session.preview, name: 'Blocked'}), code('publication_locked'));
  const original = success.controller.pendingOperation;
  original.profile.name = 'External mutation';
  assert.equal(success.sent[0].operation.profile.name, 'My local draft');
  await acknowledge(success); await first;
  assert.equal(success.controller.state.code, 'published');
  assert.equal((await success.store.read(profile.id)).status, 'none');
  assert.equal(success.session.state.history.entries, 0);
  success.controller.dispose();

  const keep = await setup();
  const waiting = keep.controller.publish(); await until(() => keep.sent.length === 1);
  keep.controller.keepDraft(); await waiting;
  assert(keep.controller.state.uncertain);
  keep.session.edit({...keep.session.preview, name: 'Newer local work'});
  await keep.session.flush();
  await acknowledge(keep);
  assert.equal(keep.controller.state.code, 'published_draft_retained');
  assert.equal((await keep.store.read(profile.id)).draft.name, 'Newer local work');
  assert.equal((await keep.store.read(profile.id)).draft.baseRevision, 7);
  keep.controller.dispose(); keep.session.dispose();

  const superseded = await setup();
  const supersededAttempt = superseded.controller.publish(); await until(() => superseded.sent.length === 1);
  superseded.profiles.receive({type: 'profiles_catalog', catalog: {...clone(catalog), catalogRevision: 21,
    profiles: catalog.profiles.map(value => value.id === profile.id ? {...clone(value), revision: 9} : clone(value))}});
  await acknowledge(superseded); await supersededAttempt;
  assert.equal(superseded.controller.state.code, 'published_draft_retained');
  assert(superseded.controller.state.superseded);
  assert.equal(superseded.controller.state.revision, 8);
  assert.equal(superseded.controller.state.currentRevision, 9);
  assert.equal((await superseded.store.pendingPublication(profile.id)).status, 'none');
  const reviewed = superseded.controller.useLocal({confirmed: true, reviewedRevision: 9});
  await until(() => superseded.sent.length === 2);
  const confirmedReceipt = receipt(superseded.sent[1].operation);
  confirmedReceipt.result.catalogRevision = 22;
  await superseded.controller.receive({type: 'profile_operation_ack', storeId: catalog.storeId, receipt: confirmedReceipt, replayed: false});
  await reviewed;
  assert.equal(superseded.controller.state.code, 'published'); superseded.controller.dispose();

  const lost = await setup();
  const abandoned = lost.controller.publish(); await until(() => lost.sent.length === 1);
  const operationId = lost.sent[0].operation.operationId;
  lost.controller.disconnected(); await abandoned;
  assert.equal(lost.controller.state.code, 'publication_uncertain');
  lost.controller.dispose(); lost.session.dispose();
  const reopened = CCSProfilePublication({store: lost.store, profiles: lost.profiles, profileId: profile.id,
    send: command => lost.sent.push(clone(command)), timeoutMs: 1000});
  await reopened.restorePending();
  const retry = reopened.retry(); await until(() => lost.sent.length === 2);
  assert.equal(lost.sent[1].operation.operationId, operationId);
  await reopened.receive({type: 'profile_operation_ack', storeId: catalog.storeId, receipt: receipt(lost.sent[1].operation), replayed: true});
  await retry;
  assert.equal(reopened.state.code, 'published'); reopened.dispose();

  const malformedAck = await setup();
  const malformedAttempt = malformedAck.controller.publish(); await until(() => malformedAck.sent.length === 1);
  const malformedReceipt = receipt(malformedAck.sent[0].operation);
  malformedReceipt.result.revision++;
  await malformedAck.controller.receive({type: 'profile_operation_ack', storeId: catalog.storeId, receipt: malformedReceipt, replayed: false});
  await malformedAttempt;
  assert.equal(malformedAck.controller.state.code, 'publication_uncertain');
  assert.equal((await malformedAck.store.read(profile.id)).status, 'valid');
  malformedAck.controller.dispose(); malformedAck.session.dispose();

  const evicted = await setup();
  const uncertainAttempt = evicted.controller.publish(); await until(() => evicted.sent.length === 1);
  evicted.controller.disconnected(); await uncertainAttempt;
  const uncertainRetry = evicted.controller.retry(); await until(() => evicted.sent.length === 2);
  await conflict(evicted); await uncertainRetry;
  assert.equal(evicted.controller.state.code, 'publication_uncertain');
  assert.equal((await evicted.store.read(profile.id)).status, 'valid');
  assert.equal((await evicted.store.pendingPublication(profile.id)).status, 'pending');
  evicted.controller.dispose(); evicted.session.dispose();

  const replace = await setup();
  const attempted = replace.controller.publish(); await until(() => replace.sent.length === 1);
  await conflict(replace); await attempted;
  assert.equal(replace.controller.state.code, 'revision_conflict');
  assert.equal((await replace.store.read(profile.id)).draft.baseRevision, 7);
  await assert.rejects(replace.controller.useLocal({confirmed: false, reviewedRevision: 8}), code('confirmation_required'));
  await assert.rejects(replace.controller.useLocal({confirmed: true, reviewedRevision: 7}), code('remote_changed'));
  const replacement = replace.controller.useLocal({confirmed: true, reviewedRevision: 8});
  await until(() => replace.sent.length === 2);
  assert.notEqual(replace.sent[1].operation.operationId, replace.sent[0].operation.operationId);
  assert.equal(replace.sent[1].operation.expectedRevision, 8);
  assert.equal((await replace.store.read(profile.id)).draft.baseRevision, 7);
  await acknowledge(replace, 1); await replacement;
  assert.equal(replace.controller.state.code, 'published'); replace.controller.dispose();

  const server = await setup();
  const stale = server.controller.publish(); await until(() => server.sent.length === 1);
  await conflict(server); await stale;
  await server.controller.useServer({confirmed: true, reviewedRevision: 8});
  assert.equal(server.controller.state.code, 'server_kept');
  assert.equal(server.sent.length, 1); assert.equal((await server.store.read(profile.id)).status, 'none'); server.controller.dispose();

  const cleanup = await setup();
  const cleanupAttempt = cleanup.controller.publish(); await until(() => cleanup.sent.length === 1);
  cleanup.store.failure = 'transaction_aborted';
  await acknowledge(cleanup); await cleanupAttempt;
  assert.equal(cleanup.controller.state.code, 'published_cleanup_error');
  assert(cleanup.controller.state.serverCommitted);
  assert.equal((await cleanup.store.read(profile.id)).status, 'valid');
  cleanup.store.failure = null; await cleanup.controller.retry();
  assert.equal(cleanup.sent.length, 1); assert.equal(cleanup.controller.state.code, 'published'); cleanup.controller.dispose();

  const quota = await setup(); quota.store.failure = 'quota_exceeded';
  await quota.controller.publish();
  assert.equal(quota.controller.state.code, 'local_error'); assert.equal(quota.sent.length, 0);
  assert.equal((await quota.store.read(profile.id)).status, 'valid'); quota.controller.dispose(); quota.session.dispose();

  const genericStore = new MemoryStore(), genericSent = [];
  const create = CCSProfilePublication({store: genericStore, profiles: sync(), profileId: 'p-new', send: value => genericSent.push(value)});
  const created = create.createProfile(content(profile)); await until(() => genericSent.length === 1);
  assert.equal(genericSent[0].operation.kind, 'create');
  await create.receive({type: 'profile_operation_ack', storeId: catalog.storeId, receipt: receipt(genericSent[0].operation), replayed: false}); await created; create.dispose();
  const remove = CCSProfilePublication({store: genericStore, profiles: sync(), profileId: 'p-second', send: value => genericSent.push(value)});
  const deleted = remove.deleteProfile(1); await until(() => genericSent.length === 2);
  assert.equal(genericSent[1].operation.kind, 'delete');
  await remove.receive({type: 'profile_operation_ack', storeId: catalog.storeId, receipt: receipt(genericSent[1].operation), replayed: false}); await deleted; remove.dispose();
  require('../../static/js/profile-selection.js');
  const sharedPreference = new Map();
  const tabA = new Map(), tabB = new Map();
  const storageFor = entries => ({getItem: key => entries.get(key) || null, setItem: (key, value) => entries.set(key, value)});
  globalThis.localStorage = storageFor(sharedPreference);
  globalThis.sessionStorage = storageFor(tabA);
  const realm = {storeId: '1'.repeat(32), accessId: '3'.repeat(32)};
  CCSProfileSelection.remember(realm, 'p-first');
  globalThis.sessionStorage = storageFor(tabB);
  assert.equal(CCSProfileSelection.read(realm), 'p-first');
  CCSProfileSelection.remember(realm, 'p-second');
  globalThis.sessionStorage = storageFor(tabA);
  assert.equal(CCSProfileSelection.read(realm), 'p-first');
  globalThis.sessionStorage = storageFor(new Map());
  assert.equal(CCSProfileSelection.read(realm), 'p-second');
  assert.equal(CCSProfileSelection.read({...realm, storeId: '2'.repeat(32)}), null);
  console.log('OK: explicit publication, stable retries, tab selection, immutable snapshots, consent conflicts, later edits, cleanup failures and local/server error separation');
}
run().catch(error => { console.error(error); process.exitCode = 1; });
