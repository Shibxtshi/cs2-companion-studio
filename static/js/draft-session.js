/* Local draft lifecycle; deliberately has no HTTP or WebSocket dependency. */
(() => {
  'use strict';
  const contract = window.CCSDraftContract;
  const History = window.CCSEditHistory;
  const CONTENT = draft => ({name: draft.name, configuration: draft.configuration});

  async function inspect({store, profileId, published}) {
    contract.profileId(profileId);
    const profile = published ? contract.validateProfile(published) : null;
    if (profile && profile.id !== profileId) contract.fail('profile_mismatch');
    try {
      const result = await store.read(profileId);
      if (result.status !== 'valid') return result;
      if (!profile) return {...result, status: 'profile_deleted'};
      if (result.draft.baseRevision < profile.revision) return {...result, status: 'remote_newer'};
      if (result.draft.baseRevision > profile.revision) return {...result, status: 'revision_mismatch'};
      return {...result, status: 'available'};
    } catch (error) {
      return {status: 'storage_unavailable', code: error.code || 'storage_unavailable', token: null};
    }
  }
  async function start({store, published, choice, now = Date.now, randomId = contract.uuid,
                        debounceMs = 200, onStatus = () => {}}) {
    const profile = contract.validateProfile(published);
    if (!Number.isInteger(debounceMs) || debounceMs < 0 || debounceMs > 1000) contract.fail('invalid_delay');
    const found = await inspect({store, profileId: profile.id, published: profile});
    let base;
    let token;
    if (choice === 'resume' && found.status === 'available') {
      base = contract.validateDraft(found.draft);
      token = found.token;
    } else if (choice === 'new' && found.status === 'none') {
      base = contract.validateDraft({format: 'ccs-dashboard-draft', version: 1,
        storeId: store.context.storeId, profileId: profile.id, draftId: randomId(),
        baseRevision: profile.revision, localRevision: 0, updatedAt: now(), ...CONTENT(profile)});
      token = null;
    } else contract.fail(found.status === 'none' ? 'draft_missing' : found.status === 'available' ? 'draft_exists' : found.status);
    const history = new History(CONTENT(base));
    let generation = choice === 'new' ? 1 : 0;
    let savedGeneration = 0;
    let timer = null;
    let inFlight = null;
    let closed = false;
    let leaving = false;
    let status = generation ? 'pending' : 'saved';
    let errorCode = null;

    function notify(code, error = null) {
      status = code;
      errorCode = error;
      // A UI observer cannot turn a committed transaction into a failed write.
      try { onStatus(Object.freeze({code, error, dirty: generation !== savedGeneration || history.activeGesture})); } catch {}
    }
    function editable() {
      if (closed || leaving) contract.fail('session_closed');
    }
    function snapshot() {
      return contract.validateDraft({...base, ...history.value});
    }
    function schedule() {
      clearTimeout(timer);
      timer = null;
      if (!closed && !leaving && !history.activeGesture && generation !== savedGeneration) {
        timer = setTimeout(() => { timer = null; flush().catch(() => {}); }, debounceMs);
      }
    }
    function changed() {
      generation++;
      base.updatedAt = Math.max(base.updatedAt, now());
      notify('pending');
      schedule();
    }
    function flush() {
      clearTimeout(timer);
      timer = null;
      if (closed) return Promise.reject(new contract.DraftError('session_closed'));
      if (history.activeGesture) return Promise.reject(new contract.DraftError('gesture_active'));
      if (inFlight) return inFlight;
      if (generation === savedGeneration) return Promise.resolve();
      inFlight = (async () => {
        try {
          while (!closed && generation !== savedGeneration) {
            const savingGeneration = generation;
            const draft = snapshot();
            notify('saving');
            const saved = await store.save(draft, token);
            token = saved.token;
            base.localRevision = saved.draft.localRevision;
            savedGeneration = savingGeneration;
            notify(history.activeGesture ? 'editing' : generation === savedGeneration ? 'saved' : 'pending');
            if (history.activeGesture) break;
          }
        } catch (error) {
          notify('error', error.code || 'storage_unavailable');
          throw error;
        } finally { inFlight = null; }
      })();
      return inFlight;
    }
    async function persisted() {
      await flush();
      const stored = await store.read(profile.id);
      if (stored.status !== 'valid' || stored.token !== token) contract.fail('local_conflict');
      return contract.validateDraft(stored.draft);
    }
    async function keepAndLeave() {
      editable();
      leaving = true;
      try {
        await persisted();
        closed = true;
        notify('kept');
        return {status: 'kept', profileId: profile.id};
      } catch (error) {
        leaving = false;
        notify('error', error.code || 'storage_unavailable');
        throw error;
      }
    }
    async function discard() {
      editable();
      leaving = true;
      clearTimeout(timer);
      timer = null;
      try {
        if (inFlight) await inFlight.catch(() => {});
        await store.remove(profile.id, token);
        closed = true;
        notify('discarded');
      } catch (error) {
        leaving = false;
        notify('error', error.code || 'storage_unavailable');
        throw error;
      }
    }
    const session = Object.freeze({
      get preview() { return history.value; },
      get draft() { return snapshot(); },
      get state() { return {status, error: errorCode, dirty: generation !== savedGeneration || history.activeGesture,
        closed, gestureActive: history.activeGesture, canUndo: history.canUndo, canRedo: history.canRedo, history: history.stats}; },
      edit(next) { editable(); if (history.commit(next)) changed(); },
      undo() { editable(); if (history.undo()) changed(); },
      redo() { editable(); if (history.redo()) changed(); },
      beginGesture() { editable(); clearTimeout(timer); timer = null; history.beginGesture(); notify('editing'); },
      previewGesture(next) { editable(); history.preview(next); notify('editing'); },
      endGesture() { editable(); if (history.endGesture()) changed(); else { notify(generation === savedGeneration ? 'saved' : 'pending'); schedule(); } },
      cancelGesture() { editable(); history.cancelGesture(); notify(generation === savedGeneration ? 'saved' : 'pending'); schedule(); },
      flush, keepAndLeave, discard,
      async publicationSnapshot() {
        editable();
        leaving = true;
        try { return await persisted(); } finally { leaving = false; }
      },
      inspectRemote: latest => inspect({store, profileId: profile.id, published: latest}),
      dispose() { clearTimeout(timer); timer = null; closed = true; },
    });
    notify(status);
    schedule();
    return session;
  }
  async function logout({store, confirmed}) {
    if (confirmed !== true) return {status: 'cancelled'};
    await store.clearContext();
    return {status: 'cleared'};
  }
  window.CCSDraftSession = Object.freeze({inspect, start, logout});
})();
