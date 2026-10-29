/* Configuration-only publication journal in the same IndexedDB transaction domain. */
(() => {
  'use strict';
  const contract = window.CCSDraftContract;
  const isId = value => typeof value === 'string' && /^[a-f0-9]{32}$/.test(value) && value.length === 32;
  function capture(value) {
    if (value === null) return null;
    if (!value || Object.keys(value).sort().join(',') !== 'baseRevision,draftId,localRevision,token'
        || !isId(value.draftId) || !isId(value.token) || !Number.isSafeInteger(value.localRevision)
        || value.localRevision < 1 || !Number.isSafeInteger(value.baseRevision) || value.baseRevision < 0) contract.fail('invalid_capture');
    return {...value};
  }
  window.CCSDraftPublications = ({run, keyFor, contextKey, context, randomId}) => {
    function decode(raw, key) {
      if (!raw) return {status: 'none', token: null};
      try {
        if (Object.keys(raw).sort().join(',') !== 'capture,contextKey,key,operation,reviewedRevision,writeId'
            || raw.key !== key || raw.contextKey !== contextKey || !isId(raw.writeId)) contract.fail('corrupt_journal');
        const operation = contract.validateOperation(raw.operation);
        if (operation.storeId !== context.storeId || keyFor(operation.profileId) !== key) contract.fail('corrupt_journal');
        const captured = capture(raw.capture);
        if ((operation.kind === 'update' && !captured) || (operation.kind === 'delete' && captured)) contract.fail('corrupt_journal');
        if (raw.reviewedRevision !== null && (!Number.isSafeInteger(raw.reviewedRevision) || raw.reviewedRevision < 1
            || raw.reviewedRevision !== operation.expectedRevision || operation.kind !== 'update')) contract.fail('corrupt_journal');
        if (captured && operation.expectedRevision !== captured.baseRevision && raw.reviewedRevision !== operation.expectedRevision) contract.fail('corrupt_journal');
        return {status: 'pending', token: raw.writeId, operation, capture: captured, reviewedRevision: raw.reviewedRevision};
      } catch { return {status: 'corrupt', token: null}; }
    }
    function pendingPublication(profileId) {
      const key = keyFor(profileId);
      return run('readonly', (tx, done) => {
        const request = tx.objectStore('publications').get(key);
        request.onsuccess = () => done(decode(request.result, key));
      });
    }
    async function queuePublication(value, metadata = null, {replaceToken = null, reviewedRevision = null} = {}) {
      const operation = contract.validateOperation(value);
      const captured = capture(metadata);
      if (operation.storeId !== context.storeId) contract.fail('context_mismatch');
      if ((operation.kind === 'update' && !captured) || (operation.kind === 'delete' && captured)) contract.fail('invalid_capture');
      if (reviewedRevision !== null && (operation.kind !== 'update' || !captured || reviewedRevision !== operation.expectedRevision
          || reviewedRevision < captured.baseRevision)) contract.fail('invalid_resolution');
      const key = keyFor(operation.profileId);
      return run('readwrite', (tx, done, abort) => {
        const journal = tx.objectStore('publications');
        const request = journal.get(key);
        request.onsuccess = () => {
          try {
            const existing = decode(request.result, key);
            if (replaceToken) {
              if (existing.status !== 'pending' || existing.token !== replaceToken || reviewedRevision === null
                  || existing.operation.operationId === operation.operationId) contract.fail('local_conflict');
            } else if (existing.status !== 'none') {
              if (existing.status === 'pending' && contract.canonical(existing.operation) === contract.canonical(operation)
                  && contract.canonical(existing.capture) === contract.canonical(captured)) { done(existing); return; }
              contract.fail('publication_pending');
            }
            function write() {
              const writeId = randomId();
              if (!isId(writeId)) contract.fail('invalid_metadata');
              journal.put({key, contextKey, writeId, operation, capture: captured, reviewedRevision});
              done({status: 'pending', token: writeId, operation, capture: captured, reviewedRevision});
            }
            if (!captured) { write(); return; }
            const draftRequest = tx.objectStore('drafts').get(key);
            draftRequest.onsuccess = () => {
              try {
                const raw = draftRequest.result;
                const draft = contract.validateDraft(raw?.draft);
                if (raw.writeId !== captured.token || draft.draftId !== captured.draftId
                    || draft.localRevision !== captured.localRevision || draft.baseRevision !== captured.baseRevision
                    || (operation.expectedRevision !== draft.baseRevision && reviewedRevision !== operation.expectedRevision)
                    || draft.storeId !== operation.storeId || draft.profileId !== operation.profileId
                    || contract.canonical({name: draft.name, configuration: draft.configuration}) !== contract.canonical(operation.profile)) contract.fail('local_conflict');
                write();
              } catch (error) { abort(error); }
            };
          } catch (error) { abort(error); }
        };
      });
    }
    function completePublication(profileId, expectedToken, receipt, {preserveDraft = false} = {}) {
      const checkedReceipt = contract.validateReceipt(receipt);
      const key = keyFor(profileId);
      return run('readwrite', (tx, done, abort) => {
        const journal = tx.objectStore('publications');
        const request = journal.get(key);
        request.onsuccess = () => {
          try {
            const pending = decode(request.result, key);
            if (pending.status !== 'pending' || pending.token !== expectedToken) contract.fail('local_conflict');
            contract.checkReceipt(pending.operation, checkedReceipt);
            function finish(removed) {
              journal.delete(key);
              done({draftRemoved: removed, draftRetained: !!pending.capture && !removed});
            }
            if (!pending.capture || preserveDraft) { finish(false); return; }
            const drafts = tx.objectStore('drafts');
            const draftRequest = drafts.get(key);
            draftRequest.onsuccess = () => {
              try {
                const raw = draftRequest.result;
                let matching = false;
                try {
                  const draft = contract.validateDraft(raw?.draft);
                  matching = draft.storeId === context.storeId && draft.profileId === pending.operation.profileId
                    && raw.writeId === pending.capture.token && draft.draftId === pending.capture.draftId
                    && draft.localRevision === pending.capture.localRevision && draft.baseRevision === pending.capture.baseRevision
                    && contract.canonical({name: draft.name, configuration: draft.configuration}) === contract.canonical(pending.operation.profile);
                } catch {}
                if (matching) drafts.delete(key);
                finish(matching);
              } catch (error) { abort(error); }
            };
          } catch (error) { abort(error); }
        };
      });
    }
    function abandonPublication(profileId, expectedToken, metadata = null) {
      const captured = capture(metadata);
      const key = keyFor(profileId);
      return run('readwrite', (tx, done, abort) => {
        const journal = tx.objectStore('publications');
        const request = journal.get(key);
        request.onsuccess = () => {
          try {
            const pending = decode(request.result, key);
            if ((pending.status === 'none' && expectedToken !== null)
                || (pending.status !== 'none' && (pending.status !== 'pending' || pending.token !== expectedToken))) contract.fail('local_conflict');
            if (!captured) { journal.delete(key); done(true); return; }
            const drafts = tx.objectStore('drafts');
            const read = drafts.get(key);
            read.onsuccess = () => {
              try {
                const draft = contract.validateDraft(read.result?.draft);
                if (draft.storeId !== context.storeId || draft.profileId !== profileId
                    || read.result.writeId !== captured.token || draft.draftId !== captured.draftId
                    || draft.localRevision !== captured.localRevision) contract.fail('local_conflict');
                drafts.delete(key);
                journal.delete(key);
                done(true);
              } catch (error) { abort(error); }
            };
          } catch (error) { abort(error); }
        };
      });
    }
    return {pendingPublication, queuePublication, completePublication, abandonPublication};
  };
})();
