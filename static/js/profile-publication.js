/* Explicit publication controller; local persistence is never a server success. */
(() => {
  'use strict';
  const contract = window.CCSDraftContract;
  const SERVER_ERRORS = new Set(['invalid_document', 'size_limit', 'profile_size_limit', 'complexity_limit',
    'revision_conflict', 'profile_deleted', 'profile_missing', 'profile_exists', 'store_changed',
    'profile_limit', 'last_profile', 'tombstone_limit', 'revision_limit', 'operation_id_reused', 'disk']);
  window.CCSProfilePublication = ({store, profiles, send, session = null, profileId,
                                  timeoutMs = 8000, onStatus = () => {}}) => {
    contract.profileId(profileId);
    let pending = null;
    let lease = null;
    let ack = null;
    let flight = null;
    let settle = null;
    let timer = null;
    let preparing = false;
    let processingAck = false;
    let uncertain = false;
    let disposed = false;
    let state = {code: 'draft_ready', scope: null, serverCommitted: false};
    function notify(code, scope = null, details = {}) {
      state = {code, scope, serverCommitted: !!ack, ...details,
        operationId: pending?.operation.operationId || null};
      try { onStatus(Object.freeze({...state})); } catch {}
      return {...state};
    }
    function done(value) {
      clearTimeout(timer);
      timer = null;
      const resolve = settle;
      settle = null;
      flight = null;
      if (resolve) resolve(value);
      return value;
    }
    function ready() {
      if (disposed) contract.fail('controller_disposed');
      if (!profiles.ready) contract.fail('network_error');
      if (profiles.context.storeId !== store.context.storeId || profiles.context.accessId !== store.context.accessId) contract.fail('store_changed');
    }
    function request() {
      if (flight) return flight;
      flight = new Promise(resolve => { settle = resolve; });
      let attempted = false;
      try {
        ready();
        notify('publishing');
        timer = setTimeout(() => { uncertain = true; done(notify('publication_uncertain', 'network', {uncertain: true})); }, timeoutMs);
        attempted = true;
        send({type: 'profile_operation', operation: contract.validateOperation(pending.operation)});
      } catch (error) {
        uncertain ||= attempted;
        done(notify(error.code === 'store_changed' ? 'store_changed' : attempted ? 'publication_uncertain' : 'network_error',
          'network', {error: error.code || 'network_error', uncertain}));
      }
      return flight || Promise.resolve({...state});
    }
    async function loadPending() {
      const found = await store.pendingPublication(profileId);
      if (found.status === 'corrupt') contract.fail('corrupt_journal');
      if (found.status !== 'pending') contract.fail('publication_missing');
      pending = found;
      return found;
    }
    async function cleanup() {
      if (!pending || !ack || processingAck) return {...state};
      processingAck = true;
      try {
        const revision = ack.receipt.result.revision;
        const latest = profiles.profile(profileId);
        const currentKnown = profiles.catalog?.catalogRevision >= ack.receipt.result.catalogRevision;
        const superseded = currentKnown && pending.operation.kind !== 'delete' && (!latest || latest.revision > revision);
        const result = lease ? await lease.finish(pending.token, ack.receipt, {preserveDraft: superseded})
          : await store.completePublication(profileId, pending.token, ack.receipt, {preserveDraft: superseded});
        const code = result.draftRetained ? 'published_draft_retained' : 'published';
        lease?.release();
        lease = null;
        uncertain = false;
        const resultState = notify(code, null, {revision, serverCommitted: true, superseded, currentRevision: currentKnown ? latest?.revision || null : null});
        pending = null;
        ack = null;
        return done(resultState);
      } catch (error) {
        lease?.release();
        return done(notify('published_cleanup_error', 'local', {error: error.code || 'storage_unavailable'}));
      } finally { processingAck = false; }
    }
    async function prepare(build) {
      if (preparing || flight) return flight || {...state};
      preparing = true;
      notify('validating', 'local');
      try {
        ready();
        if ((await store.pendingPublication(profileId)).status !== 'none') contract.fail('publication_pending');
        const {operation, capture} = await build();
        pending = await store.queuePublication(operation, capture);
      } catch (error) {
        lease?.release(); lease = null;
        return notify(error.code === 'store_changed' ? 'store_changed' : error.code === 'network_error' ? 'network_error'
          : ['local_conflict', 'publication_pending'].includes(error.code) ? 'local_conflict'
            : ['quota_exceeded', 'transaction_aborted', 'storage_unavailable', 'context_revoked'].includes(error.code) ? 'local_error' : 'validation_error',
          error.code === 'network_error' ? 'network' : 'local', {error: error.code || 'storage_unavailable'});
      } finally { preparing = false; }
      return request();
    }
    function operation(kind, expectedRevision, content = null) {
      return contract.validateOperation({format: 'ccs-dashboard-operation', version: 1,
        storeId: store.context.storeId, operationId: contract.uuid(), profileId, kind, expectedRevision,
        ...(content ? {profile: content} : {})});
    }
    const controller = Object.freeze({
      get state() { return {...state}; },
      get pendingOperation() { return profiles.ready && pending ? contract.validateOperation(pending.operation) : null; },
      publish() {
        return prepare(async () => {
          if (!session) contract.fail('draft_required');
          const snapshot = await session.publicationSnapshot();
          if (snapshot.profileId !== profileId || snapshot.storeId !== store.context.storeId) contract.fail('profile_mismatch');
          lease = session.holdPublication(snapshot);
          return {operation: operation(snapshot.baseRevision === 0 ? 'create' : 'update', snapshot.baseRevision,
            {name: snapshot.name, configuration: snapshot.configuration}), capture: lease.capture};
        });
      },
      createProfile(content) { return prepare(async () => ({operation: operation('create', 0, contract.content(content)), capture: null})); },
      deleteProfile(expectedRevision) { return prepare(async () => ({operation: operation('delete', expectedRevision), capture: null})); },
      async restorePending() {
        if (preparing || flight || processingAck) contract.fail('publication_busy');
        preparing = true;
        try { ready(); await loadPending(); uncertain = true; return notify('reconciliation_required', null, {uncertain}); }
        catch (error) {
          return notify(error.code === 'network_error' ? 'network_error' : error.code === 'store_changed' ? 'store_changed' : 'local_error',
            error.code === 'network_error' ? 'network' : error.code === 'store_changed' ? 'server' : 'local', {error: error.code || 'storage_unavailable'});
        }
        finally { preparing = false; }
      },
      async retry() {
        if (flight) return flight;
        if (preparing) contract.fail('publication_busy');
        if (ack) return cleanup();
        try { ready(); if (!pending) await loadPending(); }
        catch (error) {
          return notify(error.code === 'network_error' ? 'network_error' : error.code === 'store_changed' ? 'store_changed' : 'local_error',
            error.code === 'network_error' ? 'network' : error.code === 'store_changed' ? 'server' : 'local', {error: error.code || 'storage_unavailable'});
        }
        return request();
      },
      disconnected() {
        if (pending && !ack) { uncertain = true; done(notify('publication_uncertain', 'network', {uncertain})); }
      },
      keepDraft() {
        if (!pending) return {...state};
        if (processingAck || preparing) contract.fail('publication_busy');
        lease?.release();
        uncertain ||= !!flight && !ack;
        return done(notify('draft_kept', null, {uncertain}));
      },
      async receive(message) {
        if (disposed || preparing || !profiles.ready || !pending || !['profile_operation_ack', 'profile_operation_error'].includes(message?.type)) return false;
        if (profiles.context.storeId !== pending.operation.storeId) {
          lease?.release();
          done(notify('store_changed', 'server', {uncertain}));
          return true;
        }
        if (message.type === 'profile_operation_error') {
          if (message.operationId !== pending.operation.operationId) return false;
          if (!SERVER_ERRORS.has(message.code) || Object.keys(message).some(key => !['type', 'operationId', 'code', 'catalog'].includes(key))) {
            uncertain = true;
            done(notify('publication_uncertain', 'server', {error: 'invalid_message', uncertain})); return true;
          }
          const codes = {revision_conflict: 'revision_conflict', profile_deleted: 'profile_deleted',
            profile_missing: 'profile_deleted', store_changed: 'store_changed'};
          lease?.release();
          done(notify(uncertain && ['revision_conflict', 'profile_deleted', 'profile_missing', 'profile_exists'].includes(message.code)
            ? 'publication_uncertain' : codes[message.code] || 'server_error', 'server', {error: message.code, uncertain}));
          return true;
        }
        if (message.receipt?.operationId !== pending.operation.operationId) return false;
        try {
          if (message.storeId !== pending.operation.storeId || typeof message.replayed !== 'boolean'
              || Object.keys(message).sort().join(',') !== 'receipt,replayed,storeId,type') contract.fail('invalid_receipt');
          const receipt = contract.checkReceipt(pending.operation, message.receipt);
          ack = {receipt};
          await cleanup();
        } catch (error) {
          uncertain = true;
          done(notify('publication_uncertain', 'server', {error: error.code || 'invalid_receipt', uncertain}));
        }
        return true;
      },
      async useLocal({confirmed, reviewedRevision, reviewedDraftToken = null}) {
        if (confirmed !== true || preparing || processingAck || flight) contract.fail('confirmation_required');
        preparing = true;
        try {
          ready();
          const latest = profiles.profile(profileId);
          if (!latest) contract.fail('profile_deleted');
          if (latest.revision !== reviewedRevision) contract.fail('remote_changed');
          if (!pending) {
            const existing = await store.pendingPublication(profileId);
            if (existing.status === 'pending') pending = existing;
            else if (existing.status !== 'none') contract.fail('corrupt_journal');
          }
          if (ack) contract.fail('publication_already_confirmed');
          lease?.release(); lease = null;
          let draft, captured;
          if (session && !session.state.closed) {
            draft = await session.publicationSnapshot();
            lease = session.holdPublication(draft);
            captured = lease.capture;
          } else {
            const stored = await store.read(profileId);
            if (stored.status !== 'valid' || stored.token !== reviewedDraftToken) contract.fail('local_conflict');
            draft = stored.draft;
            captured = {draftId: draft.draftId, localRevision: draft.localRevision, baseRevision: draft.baseRevision, token: stored.token};
          }
          const next = operation('update', reviewedRevision, {name: draft.name, configuration: draft.configuration});
          pending = await store.queuePublication(next, captured, {replaceToken: pending?.token || null, reviewedRevision});
          uncertain = false;
        } catch (error) { lease?.release(); throw error; }
        finally { preparing = false; }
        return request();
      },
      async useServer({confirmed, reviewedRevision, reviewedDraftToken = null}) {
        if (confirmed !== true || preparing || processingAck || flight) contract.fail('confirmation_required');
        preparing = true;
        try {
          ready();
          const latest = profiles.profile(profileId);
          if (!latest) contract.fail('profile_deleted');
          if (latest.revision !== reviewedRevision) contract.fail('remote_changed');
          if (!pending) {
            const existing = await store.pendingPublication(profileId);
            if (existing.status === 'pending') pending = existing;
            else if (existing.status !== 'none') contract.fail('corrupt_journal');
          }
          if (ack) contract.fail('publication_already_confirmed');
          lease?.release(); lease = null;
          if (session && !session.state.closed) {
            const draft = await session.publicationSnapshot();
            lease = session.holdPublication(draft);
            await lease.abandon(pending?.token || null);
          } else {
            const stored = await store.read(profileId);
            let captured = null;
            if (stored.status !== 'none') {
              if (stored.status !== 'valid' || stored.token !== reviewedDraftToken) contract.fail('local_conflict');
              captured = {draftId: stored.draft.draftId, localRevision: stored.draft.localRevision,
                baseRevision: stored.draft.baseRevision, token: stored.token};
            }
            await store.abandonPublication(profileId, pending?.token || null, captured);
          }
          pending = null;
          return notify('server_kept');
        } catch (error) { lease?.release(); throw error; }
        finally { preparing = false; }
      },
      dispose() { disposed = true; clearTimeout(timer); timer = null; lease?.release(); done({...state}); },
    });
    return controller;
  };
})();
