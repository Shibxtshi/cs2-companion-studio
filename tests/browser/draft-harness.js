/* Synthetic-only harness loaded by the browser runner, never by the application. */
(() => {
  'use strict';
  const contract = CCSDraftContract;
  const copy = value => structuredClone(value);
  const context = () => contract.access({storeId: '1'.repeat(32), accessId: '3'.repeat(32), authenticated: true});
  const assert = (value, message) => { if (!value) throw new Error(message); };
  async function rejects(promise, code) {
    try { await promise; } catch (error) { assert(error.code === code, 'Expected ' + code + ', got ' + error.code); return; }
    throw new Error('Expected rejection ' + code);
  }
  let profile;
  let store;
  const faults = {mode: null, puts: 0, commits: 0};
  function proxy(target, override) {
    return new Proxy(target, {
      get(object, key) {
        if (Object.hasOwn(override, key)) return override[key];
        const value = Reflect.get(object, key, object);
        return typeof value === 'function' ? value.bind(object) : value;
      },
      set(object, key, value) { return Reflect.set(object, key, value, object); },
    });
  }
  const factory = {
    open(...args) {
      const request = indexedDB.open(...args);
      let wrapped;
      return new Proxy(request, {
        get(object, key) {
          if (key === 'result' && object.result) {
            wrapped ||= proxy(object.result, {
              transaction(...args) {
                const tx = object.result.transaction(...args);
                let touched = false;
                tx.addEventListener('complete', () => { if (touched) faults.commits++; });
                return proxy(tx, {
                  objectStore(name) {
                    const native = tx.objectStore(name);
                    return proxy(native, {
                      put(value) {
                        if (name === 'drafts') {
                          touched = true;
                          faults.puts++;
                          if (faults.mode === 'quota') throw new DOMException('Synthetic quota failure', 'QuotaExceededError');
                        }
                        const result = native.put(value);
                        if ((name === 'drafts' && faults.mode === 'abort-put')
                            || (name === 'contexts' && faults.mode === 'abort-clear')) result.addEventListener('success', () => tx.abort());
                        return result;
                      },
                      delete(key) {
                        const result = native.delete(key);
                        if (faults.mode === 'abort-delete') result.addEventListener('success', () => tx.abort());
                        return result;
                      },
                      openCursor(...args) {
                        const cursorRequest = native.openCursor(...args);
                        return cursorRequest;
                      },
                    });
                  },
                });
              },
            });
            return wrapped;
          }
          const value = Reflect.get(object, key, object);
          return typeof value === 'function' ? value.bind(object) : value;
        },
        set(object, key, value) { return Reflect.set(object, key, value, object); },
      });
    },
  };
  async function raw(action) {
    const database = await new Promise((resolve, reject) => {
      const request = indexedDB.open('ccs-local-drafts', 1);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    try {
      return await new Promise((resolve, reject) => {
        const tx = database.transaction(['drafts', 'contexts'], 'readwrite');
        let result;
        action(tx, value => { result = value; });
        tx.oncomplete = () => resolve(result);
        tx.onabort = () => reject(tx.error);
      });
    } finally { database.close(); }
  }
  async function initialize(value) {
    profile = copy(value);
    store = await CCSDraftStore.open({context: context(), indexedDB: factory});
  }
  function draftFor(value = profile) {
    return {format: 'ccs-dashboard-draft', version: 1, storeId: '1'.repeat(32),
      profileId: value.id, draftId: contract.uuid(), baseRevision: value.revision,
      localRevision: 0, updatedAt: Date.now(), name: value.name, configuration: copy(value.configuration)};
  }
  async function create() {
    const session = await CCSDraftSession.start({store, published: profile, choice: 'new', debounceMs: 1000});
    const value = session.preview;
    value.name = 'Persistent draft';
    session.edit(value);
    assert(profile.name === 'Competitive', 'Published state mutated');
    await session.keepAndLeave();
    assert(session.state.status === 'kept', 'Exit confirmed too early');
    return session.state;
  }
  async function restore() {
    const found = await CCSDraftSession.inspect({store, profileId: profile.id, published: profile});
    assert(found.status === 'available', 'Draft missing after reload/reopen');
    assert(found.draft.name === 'Persistent draft', 'Wrong restored content');
    const session = await CCSDraftSession.start({store, published: profile, choice: 'resume'});
    assert(!session.state.canUndo && session.state.history.entries === 0, 'History persisted');
    session.dispose();
    return found.draft.localRevision;
  }
  async function failureCases() {
    const before = await store.read(profile.id);
    for (const mode of ['quota', 'abort-put']) {
      faults.mode = mode;
      const session = await CCSDraftSession.start({store, published: profile, choice: 'resume', debounceMs: 1000});
      session.edit({...session.preview, name: 'Must not commit'});
      await rejects(session.keepAndLeave(), mode === 'quota' ? 'quota_exceeded' : 'transaction_aborted');
      assert(session.state.status === 'error' && !session.state.closed && session.state.dirty, 'Failed persistence falsely confirmed exit');
      session.dispose();
      const after = await store.read(profile.id);
      assert(after.token === before.token && after.draft.name === before.draft.name, 'Failed transaction replaced valid data');
    }
    faults.mode = 'abort-delete';
    await rejects(store.remove(profile.id, before.token), 'transaction_aborted');
    assert((await store.read(profile.id)).token === before.token, 'Failed delete lost draft');
    faults.mode = 'abort-clear';
    await rejects(CCSDraftSession.logout({store, confirmed: true}), 'transaction_aborted');
    assert((await store.read(profile.id)).token === before.token, 'Failed logout lost draft');
    faults.mode = null;
    const unavailable = await CCSDraftStore.open({context: context(), indexedDB: null}).catch(error => error.code);
    assert(unavailable === 'storage_unavailable', 'Unavailable storage not classified');
    const denied = await CCSDraftStore.open({context: context(), indexedDB: {open() { throw new DOMException('Synthetic denied', 'SecurityError'); }}}).catch(error => error.code);
    assert(denied === 'storage_unavailable', 'Denied storage not classified');
  }
  async function corruptionCases() {
    const before = await store.read(profile.id);
    const key = JSON.stringify(['1'.repeat(32), '3'.repeat(32), 1, profile.id]);
    let original;
    await raw((tx, done) => {
      const request = tx.objectStore('drafts').get(key);
      request.onsuccess = () => { original = copy(request.result); done(true); };
    });
    for (const version of [2, 'corrupt']) {
      const altered = copy(original);
      if (version === 2) altered.draft.version = 2; else altered.draft.configuration.layout.widgets[0].width = -1;
      await raw(tx => tx.objectStore('drafts').put(altered));
      const result = await CCSDraftSession.inspect({store, profileId: profile.id, published: profile});
      assert(result.status === (version === 2 ? 'incompatible' : 'corrupt'), 'Bad draft was offered for resume');
      await rejects(store.save(before.draft, before.token), 'local_conflict');
    }
    await raw(tx => tx.objectStore('drafts').put(original));
    assert((await CCSDraftSession.inspect({store, profileId: profile.id, published: {...profile, revision: 8}})).status === 'remote_newer', 'Stale base accepted');
    assert((await CCSDraftSession.inspect({store, profileId: profile.id, published: {...profile, revision: 6}})).status === 'revision_mismatch', 'Rewound server accepted');
    assert((await CCSDraftSession.inspect({store, profileId: profile.id, published: null})).status === 'profile_deleted', 'Deleted profile accepted');
    const bad = copy(before.draft);
    bad.gsi = {player: 'synthetic-live-packet'};
    await rejects(store.save(bad, before.token), 'invalid_document');
    assert((await store.read(profile.id)).token === before.token, 'Invalid write changed draft');
  }
  let stale;
  async function readForRace() { stale = await store.read(profile.id); return stale.token; }
  async function winRace() {
    const current = await store.read(profile.id);
    await store.save({...current.draft, name: 'Winner'}, current.token);
  }
  async function loseRace() {
    await rejects(store.save({...stale.draft, name: 'Stale writer'}, stale.token), 'local_conflict');
    assert((await store.read(profile.id)).draft.name === 'Winner', 'Stale tab overwrote winner');
    await rejects(store.remove(profile.id, stale.token), 'local_conflict');
  }
  async function distinctProfile() {
    const other = {...copy(profile), id: 'p-second', name: 'Second Screen'};
    await store.save(draftFor(other), null);
    assert((await store.read(profile.id)).draft.name === 'Winner', 'Distinct profile overwritten');
    assert((await store.read(other.id)).draft.name === other.name, 'Distinct profile not stored');
  }
  async function isolation() {
    for (const fields of [{storeId: '4'.repeat(32), accessId: '3'.repeat(32)}, {storeId: '1'.repeat(32), accessId: '5'.repeat(32)}]) {
      const isolated = await CCSDraftStore.open({context: contract.access({...fields, authenticated: true})});
      assert((await isolated.read(profile.id)).status === 'none', 'Other context reused draft');
      const value = draftFor();
      value.storeId = fields.storeId;
      await isolated.save(value, null);
      isolated.close();
    }
  }
  async function cancelledLogout() {
    assert((await CCSDraftSession.logout({store, confirmed: false})).status === 'cancelled', 'Logout not cancelled');
    assert((await store.read(profile.id)).status === 'valid', 'Cancelled logout erased draft');
  }
  async function logout() {
    const pending = await store.read(profile.id);
    const queued = store.save({...pending.draft, name: 'Queued before logout'}, pending.token);
    const cleared = CCSDraftSession.logout({store, confirmed: true});
    await Promise.all([queued, cleared]);
    await rejects(store.save(pending.draft, pending.token), 'context_revoked');
    return true;
  }
  async function revoked() { await rejects(store.save({...stale.draft, name: 'Resurrection'}, stale.token), 'context_revoked'); }
  async function afterLogout() {
    store.close();
    store = await CCSDraftStore.open({context: context()});
    assert((await store.read(profile.id)).status === 'none', 'Logout did not erase drafts');
    assert((await store.read('p-second')).status === 'none', 'Logout did not erase all context profiles');
    for (const fields of [{storeId: '4'.repeat(32), accessId: '3'.repeat(32)}, {storeId: '1'.repeat(32), accessId: '5'.repeat(32)}]) {
      const isolated = await CCSDraftStore.open({context: contract.access({...fields, authenticated: true})});
      assert((await isolated.read(profile.id)).status === 'valid', 'Logout erased unrelated context');
      isolated.close();
    }
  }
  async function aba() {
    const temporary = {...copy(profile), id: 'p-aba'};
    const first = await store.save(draftFor(temporary), null);
    await store.remove(temporary.id, first.token);
    const second = await store.save(draftFor(temporary), null);
    await rejects(store.save(first.draft, first.token), 'local_conflict');
    await rejects(store.remove(temporary.id, first.token), 'local_conflict');
    assert((await store.read(temporary.id)).token === second.token, 'Deleted draft identity reused silently');
  }
  async function corruptSecondaryMetadata() {
    const key = JSON.stringify(['1'.repeat(32), '3'.repeat(32), 1, 'p-second']);
    await raw(tx => {
      const drafts = tx.objectStore('drafts');
      const request = drafts.get(key);
      request.onsuccess = () => {
        drafts.put({...request.result, contextKey: 'corrupt-index-metadata'});
        drafts.put({...request.result, key: JSON.stringify(['1'.repeat(32), '3'.repeat(32), 2, 'future-draft']), draft: {...request.result.draft, version: 2}});
      };
    });
  }
  async function futureDatabase() {
    store.close();
    await new Promise((resolve, reject) => {
      const request = indexedDB.open('ccs-local-drafts', 2);
      request.onsuccess = () => { request.result.close(); resolve(); };
      request.onerror = () => reject(request.error);
    });
    await rejects(CCSDraftStore.open({context: context()}), 'database_incompatible');
  }
  async function inspectSecrets(pin, token) {
    const records = await raw((tx, done) => {
      const request = tx.objectStore('drafts').getAll();
      request.onsuccess = () => done(request.result);
    });
    const serialized = JSON.stringify(records);
    for (const forbidden of [pin, token, 'synthetic-live-packet', 'DASHBOARD_PIN', 'GSI_TOKEN', 'diagnostics']) {
      assert(!serialized.includes(forbidden), 'Forbidden data in IndexedDB');
    }
    assert(records.every(record => contract.validateDraft(record.draft)), 'Unexpected persisted fields');
    assert(!records.some(record => record.key.startsWith(JSON.stringify(['1'.repeat(32), '3'.repeat(32)]).slice(0, -1) + ',')), 'Logout retained an unknown-version context draft');
  }
  async function benchmark() {
    const large = copy(profile);
    large.id = 'p-benchmark';
    large.configuration.layout.widgets = Array.from({length: 60}, (_, index) => ({
      ...large.configuration.layout.widgets[index % 29], id: 'large-' + index, y: index * 2}));
    const session = await CCSDraftSession.start({store, published: large, choice: 'new', debounceMs: 1000});
    const beforeWrites = faults.puts;
    const started = performance.now();
    const edits = [];
    for (let index = 0; index < 100; index++) {
      const start = performance.now();
      const next = session.preview;
      next.name = 'Measured edit ' + index;
      session.edit(next);
      edits.push(performance.now() - start);
    }
    const editLoopMs = performance.now() - started;
    const flushStart = performance.now();
    await session.flush();
    const flushMs = performance.now() - flushStart;
    assert(faults.puts - beforeWrites === 1, 'Burst was not coalesced');
    const history = session.state.history;
    assert(history.entries <= 50 && history.bytes <= history.maxBytes, 'History unbounded');
    const gestureWrites = faults.puts;
    const gestureStart = performance.now();
    session.beginGesture();
    for (let index = 0; index < 100; index++) {
      const next = session.preview;
      next.configuration.layout.widgets[0].x = index % 10;
      session.previewGesture(next);
    }
    session.endGesture();
    const gestureMs = performance.now() - gestureStart;
    await session.flush();
    assert(faults.puts - gestureWrites === 1, 'Gesture wrote intermediate states');
    session.dispose();
    const restoreSamples = [];
    for (let repeat = 0; repeat < 7; repeat++) {
      const start = performance.now();
      const resumed = await CCSDraftSession.start({store, published: large, choice: 'resume'});
      restoreSamples.push(performance.now() - start);
      resumed.dispose();
    }
    return {widgets: 60, edits, editLoopMs, flushMs, writesFor100Edits: 1,
      writesFor100GestureMoves: 1, gestureMs, restoreSamples, retainedHistory: history};
  }
  window.draftHarness = {initialize, create, restore, failureCases, corruptionCases, readForRace,
    winRace, loseRace, distinctProfile, isolation, cancelledLogout, logout, revoked, afterLogout,
    inspectSecrets, benchmark, aba, corruptSecondaryMetadata, futureDatabase, close: () => store.close()};
})();
