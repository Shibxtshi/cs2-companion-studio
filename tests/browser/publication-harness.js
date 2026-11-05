/* Synthetic host exercises the real P1 transport and dormant P3/P4/P5 chain. */
(() => {
  'use strict';
  const contract = CCSDraftContract;
  let pin = '';
  let store = null;
  let session = null;
  let controller = null;
  let connectResolve = null;
  let connectReject = null;
  let ackMode = null;
  const held = [];
  const sent = [];
  const errors = [];
  const states = [];
  const profiles = CCSPublishedProfiles({send: command => client.send(command)});
  const client = CS2DashboardClient({version: '1.1.0', getPin: () => pin, isDemo: () => false,
    onConnecting() {}, onHealthError: () => connectReject?.(new Error('Synthetic health failure')),
    onNetworkError() {},
    onClose() { profiles.disconnected(); controller?.disconnected(); },
    onMessage(message) {
      try {
        profiles.receive(message);
        if (message.type === 'profiles_catalog' && connectResolve) {
          const resolve = connectResolve; connectResolve = null;
          resolve();
        }
        if (message.type === 'profile_operation_ack' && ackMode) {
          if (ackMode === 'hold') held.push(message);
          return;
        }
        controller?.receive(message).catch(error => errors.push(error.code || error.message));
      } catch (error) { errors.push(error.code || error.message); }
    },
  });
  function assert(value, message) { if (!value) throw new Error(message); }
  function capture(draft, token) {
    return {draftId: draft.draftId, localRevision: draft.localRevision, baseRevision: draft.baseRevision, token};
  }
  async function connect(value) {
    pin = value;
    const ready = new Promise((resolve, reject) => { connectResolve = resolve; connectReject = reject; });
    await client.connect(() => true);
    await ready;
    if (!store || store.context.storeId !== profiles.context.storeId) store = await CCSDraftStore.open({context: profiles.context});
    return {storeId: profiles.context.storeId, accessId: profiles.context.accessId};
  }
  function buildController(profileId) {
    controller?.dispose();
    controller = CCSProfilePublication({store, profiles, session, profileId, timeoutMs: 2000,
      send(command) { sent.push(structuredClone(command)); client.send(command); },
      onStatus: state => states.push(state)});
  }
  async function edit(profileId, name, choice = 'new') {
    session?.dispose();
    session = await CCSDraftSession.start({store, published: profiles.profile(profileId), choice, debounceMs: 1000});
    if (name) session.edit({...session.preview, name});
    await session.flush();
    buildController(profileId);
    profiles.select(profileId);
  }
  function begin() { window.publicationResult = controller.publish(); return controller.state; }
  async function reopen(profileId) {
    session = null;
    buildController(profileId);
    return controller.restorePending();
  }
  async function retry() { window.publicationResult = controller.retry(); }
  async function release() {
    ackMode = null;
    for (const message of held.splice(0)) await controller.receive(message);
  }
  async function preserveNewer(name) {
    controller.keepDraft();
    session.edit({...session.preview, name});
    await session.flush();
  }
  async function newerTabEdit(profileId, name) {
    const result = await store.read(profileId);
    await store.save({...result.draft, name, updatedAt: Date.now()}, result.token);
  }
  let cleanupAbort = false;
  const originalDelete = IDBObjectStore.prototype.delete;
  IDBObjectStore.prototype.delete = function(...args) {
    const result = originalDelete.apply(this, args);
    if (cleanupAbort && this.name === 'publications') result.addEventListener('success', () => this.transaction.abort());
    return result;
  };
  let queueQuota = false;
  const originalPut = IDBObjectStore.prototype.put;
  IDBObjectStore.prototype.put = function(...args) {
    if (queueQuota && this.name === 'publications') throw new DOMException('Synthetic journal quota', 'QuotaExceededError');
    return originalPut.apply(this, args);
  };
  async function inspectStorage() {
    const database = await new Promise((resolve, reject) => {
      const request = indexedDB.open('ccs-local-drafts', 2);
      request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error);
    });
    try {
      const data = await new Promise((resolve, reject) => {
        const tx = database.transaction(['drafts', 'publications'], 'readonly');
        const drafts = tx.objectStore('drafts').getAll(), publications = tx.objectStore('publications').getAll();
        tx.oncomplete = () => resolve({drafts: drafts.result, publications: publications.result});
        tx.onabort = () => reject(tx.error);
      });
      const serialized = JSON.stringify(data);
      assert(!serialized.includes(pin) && !serialized.includes('synthetic-publication-gsi-token'), 'Secret persisted');
      for (const record of data.drafts) contract.validateDraft(record.draft);
      for (const record of data.publications) contract.validateOperation(record.operation);
      return {drafts: data.drafts.length, publications: data.publications.length};
    } finally { database.close(); }
  }
  async function benchmark(profileId) {
    const profile = profiles.profile(profileId);
    const widget = profile.configuration.layout.widgets[0];
    profile.configuration.layout.widgets = Array.from({length: 60}, (_, index) => ({...widget, id: 'measured-' + index, y: index * 2}));
    // The benchmark edits an existing target draft; it does not change published state until explicit publish.
    await edit(profileId, 'Measured 60 widgets');
    session.edit({name: 'Measured 60 widgets', configuration: profile.configuration});
    await session.flush();
    const started = performance.now();
    await controller.publish();
    return {widgets: 60, elapsedMs: performance.now() - started, status: controller.state.code};
  }
  window.publicationHarness = {
    connect, edit, begin, reopen, retry, release, preserveNewer, newerTabEdit, inspectStorage, benchmark,
    setAckMode: mode => { ackMode = mode; }, setCleanupAbort: value => { cleanupAbort = value; },
    setQueueQuota: value => { queueQuota = value; },
    useLocal: options => { window.publicationResult = controller.useLocal(options).catch(error => ({error: error.code})); },
    useServer: options => controller.useServer(options),
    discard: () => session.discard(),
    inspect: profileId => CCSDraftSession.inspect({store, profileId, published: profiles.profile(profileId)}),
    rawRetry: () => client.send({type: 'profile_operation', operation: controller.pendingOperation}),
    read: profileId => store.read(profileId),
    pending: profileId => store.pendingPublication(profileId),
    snapshot: () => ({catalog: profiles.catalog, selected: profiles.selectedProfileId,
      controller: controller?.state, session: session?.state, sent: sent.map(command => command.operation), errors: [...errors]}),
    tryEdit() { try { session.edit({...session.preview, name: 'Must be blocked'}); return null; } catch (error) { return error.code; } },
    create(profileId, content) { session = null; buildController(profileId); window.publicationResult = controller.createProfile(content); },
    remove(profileId, revision) { session = null; buildController(profileId); window.publicationResult = controller.deleteProfile(revision); },
    select: profileId => profiles.select(profileId),
    async logout() {
      await CCSDraftSession.logout({store, confirmed: true});
      controller?.dispose(); session?.dispose(); store?.close(); store = null; client.close(); profiles.clear(); pin = '';
    },
    close() { controller?.dispose(); session?.dispose(); store?.close(); client.close(); },
  };
})();
