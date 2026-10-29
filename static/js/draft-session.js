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
  async function start({store, published = null, creation = null, choice, now = Date.now, randomId = contract.uuid,
                        debounceMs = 200, persistOnStart = true, onStatus = () => {}}) {
    if ((!published && !creation) || (published && creation)) contract.fail('profile_required');
    const profile = published ? contract.validateProfile(published)
      : {id: contract.profileId(creation.id), revision: 0, ...contract.content({name: creation.name, configuration: creation.configuration})};
    if (!Number.isInteger(debounceMs) || debounceMs < 0 || debounceMs > 1000) contract.fail('invalid_delay');
    if (typeof persistOnStart !== 'boolean') contract.fail('invalid_delay');
    const found = published ? await inspect({store, profileId: profile.id, published: profile})
      : await store.read(profile.id);
    if (!published && found.status === 'valid') {
      if (found.draft.baseRevision !== 0) contract.fail('revision_mismatch');
      found.status = 'available';
    }
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
    let generation = choice === 'new' && persistOnStart ? 1 : 0;
    let savedGeneration = 0;
    let timer = null;
    let inFlight = null;
    let closed = false;
    let leaving = false;
    let publicationLocked = false;
    let finalizing = false;
    let status = generation ? 'pending' : token ? 'saved' : 'pristine';
    let errorCode = null;

    function notify(code, error = null) {
      status = code;
      errorCode = error;
      // A UI observer cannot turn a committed transaction into a failed write.
      try { onStatus(Object.freeze({code, error, dirty: generation !== savedGeneration || history.activeGesture})); } catch {}
    }
    function editable() {
      if (closed || leaving) contract.fail('session_closed');
      if (publicationLocked || finalizing) contract.fail('publication_locked');
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
      if (generation === savedGeneration && token === null) generation++;
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
        closed, hasPersistedDraft: token !== null, publicationLocked: publicationLocked || finalizing, gestureActive: history.activeGesture, canUndo: history.canUndo, canRedo: history.canRedo, history: history.stats}; },
      edit(next) { editable(); if (history.commit(next)) changed(); },
      undo() { editable(); if (history.undo()) changed(); },
      redo() { editable(); if (history.redo()) changed(); },
      beginGesture() { editable(); clearTimeout(timer); timer = null; history.beginGesture(); notify('editing'); },
      previewGesture(next) { editable(); history.preview(next); notify('editing'); },
      endGesture() { editable(); if (history.endGesture()) changed(); else { notify(generation === savedGeneration ? token ? 'saved' : 'pristine' : 'pending'); schedule(); } },
      cancelGesture() { editable(); history.cancelGesture(); notify(generation === savedGeneration ? 'saved' : 'pending'); schedule(); },
      flush, keepAndLeave, discard,
      async publicationSnapshot() {
        editable();
        leaving = true;
        try { return await persisted(); } finally { leaving = false; }
      },
      holdPublication(value) {
        editable();
        const sent = contract.validateDraft(value);
        if (history.activeGesture || generation !== savedGeneration
            || contract.canonical(sent) !== contract.canonical(snapshot())) contract.fail('draft_changed');
        const capturedGeneration = generation;
        const capturedToken = token;
        publicationLocked = true;
        notify('publication_locked');
        return Object.freeze({
          capture: Object.freeze({draftId: sent.draftId, localRevision: sent.localRevision, baseRevision: sent.baseRevision, token: capturedToken}),
          release() {
            publicationLocked = false;
            if (!closed) { notify(generation === savedGeneration ? 'saved' : 'pending'); schedule(); }
          },
          async abandon(journalToken) {
            if (generation !== capturedGeneration || token !== capturedToken || finalizing) contract.fail('draft_changed');
            finalizing = true;
            try {
              await store.abandonPublication(profile.id, journalToken, {draftId: sent.draftId,
                localRevision: sent.localRevision, baseRevision: sent.baseRevision, token: capturedToken});
              closed = true;
              publicationLocked = false;
              history.reset(CONTENT(sent));
              notify('discarded');
            } finally { finalizing = false; }
          },
          async finish(journalToken, receipt, {preserveDraft: forcePreserve = false} = {}) {
            if (finalizing) contract.fail('publication_busy');
            finalizing = true;
            const preserveDraft = forcePreserve || generation !== capturedGeneration || token !== capturedToken;
            let result;
            try { result = await store.completePublication(profile.id, journalToken, receipt, {preserveDraft}); }
            finally { finalizing = false; }
            publicationLocked = false;
            if (result.draftRemoved && !preserveDraft) {
              closed = true;
              history.reset(CONTENT(sent));
              notify('published');
            } else {
              notify('published_draft_retained');
              schedule();
            }
            return result;
          },
        });
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
