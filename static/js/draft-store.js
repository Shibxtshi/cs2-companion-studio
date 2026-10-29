/* Native IndexedDB, atomic compare-and-swap and context-scoped erasure. */
(() => {
  'use strict';
  const contract = window.CCSDraftContract;
  const DB_NAME = 'ccs-local-drafts';
  const DB_VERSION = 2;
  const HEX_ID = /^[a-f0-9]{32}$/;
  const RECORD_KEYS = ['key', 'contextKey', 'writeId', 'createdAt', 'draft'];

  function storageError(error) {
    if (error instanceof contract.DraftError) return error;
    const codes = {QuotaExceededError: 'quota_exceeded', AbortError: 'transaction_aborted',
      VersionError: 'database_incompatible', InvalidStateError: 'storage_unavailable',
      SecurityError: 'storage_unavailable', UnknownError: 'storage_unavailable'};
    return new contract.DraftError(codes[error?.name] || 'storage_unavailable');
  }
  function decodeRecord(record, key, contextKey) {
    if (!record) return {status: 'none', token: null};
    const token = typeof record.writeId === 'string' && record.writeId.length === 32 && HEX_ID.test(record.writeId) ? record.writeId : null;
    try {
      contract.bounded(record);
      if (Object.keys(record).length !== RECORD_KEYS.length || RECORD_KEYS.some(field => !Object.hasOwn(record, field))
          || record.key !== key || record.contextKey !== contextKey || !token
          || !Number.isSafeInteger(record.createdAt) || record.createdAt < 0) contract.fail('corrupt_draft');
      if (!record.draft || typeof record.draft !== 'object' || Array.isArray(record.draft)
          || typeof record.draft.format !== 'string' || !Number.isSafeInteger(record.draft.version)
          || record.draft.version < 1) contract.fail('corrupt_draft');
      if (record.draft.format !== 'ccs-dashboard-draft' || record.draft.version !== 1) {
        return {status: 'incompatible', token};
      }
      const draft = contract.validateDraft(record.draft);
      const [storeId] = JSON.parse(contextKey);
      const profileId = JSON.parse(key).at(-1);
      if (draft.storeId !== storeId || draft.profileId !== profileId || draft.localRevision < 1) contract.fail('corrupt_draft');
      return {status: 'valid', token, createdAt: record.createdAt, draft};
    } catch {
      return {status: 'corrupt', token};
    }
  }
  function openDatabase(factory) {
    return new Promise((resolve, reject) => {
      if (!factory) return reject(new contract.DraftError('storage_unavailable'));
      let settled = false;
      let request;
      try { request = factory.open(DB_NAME, DB_VERSION); }
      catch (error) { reject(storageError(error)); return; }
      request.onupgradeneeded = () => {
        const database = request.result;
        for (const name of ['contexts', 'drafts', 'publications']) {
          if (!database.objectStoreNames.contains(name)) database.createObjectStore(name, {keyPath: 'key'});
        }
      };
      request.onerror = () => { settled = true; reject(storageError(request.error)); };
      request.onblocked = () => { settled = true; reject(new contract.DraftError('storage_blocked')); };
      request.onsuccess = () => {
        if (settled) { request.result.close(); return; }
        settled = true;
        request.result.onversionchange = () => request.result.close();
        resolve(request.result);
      };
    });
  }
  function transaction(database, mode, action) {
    return new Promise((resolve, reject) => {
      let result;
      let failure;
      let tx;
      try {
        tx = database.transaction(['contexts', 'drafts', 'publications'], mode);
        const abort = error => { failure = storageError(error); tx.abort(); };
        tx.oncomplete = () => resolve(result);
        tx.onabort = () => reject(failure || storageError(tx.error || {name: 'AbortError'}));
        tx.onerror = () => {};
        action(tx, value => { result = value; }, abort);
      } catch (error) {
        if (tx) {
          failure = storageError(error);
          try { tx.abort(); } catch { reject(failure); }
        } else reject(storageError(error));
      }
    });
  }
  async function open({context, indexedDB: factory, now = Date.now, randomId = contract.uuid}) {
    const contextKey = contract.contextKey(context);
    if (factory === undefined) {
      try { factory = window.indexedDB; } catch (error) { throw storageError(error); }
    }
    const database = await openDatabase(factory);
    let epoch;
    try {
      epoch = await transaction(database, 'readwrite', (tx, done, abort) => {
        const contexts = tx.objectStore('contexts');
        const request = contexts.get(contextKey);
        request.onsuccess = () => {
          const stored = request.result;
          if (stored && (Object.keys(stored).length !== 2 || stored.key !== contextKey
              || !Number.isSafeInteger(stored.epoch) || stored.epoch < 0)) {
            abort(new contract.DraftError('corrupt_context')); return;
          }
          const value = stored?.epoch ?? 0;
          if (!stored) contexts.add({key: contextKey, epoch: value});
          done(value);
        };
      });
    } catch (error) { database.close(); throw error; }
    const keyFor = profileId => JSON.stringify([...JSON.parse(contextKey), 1, contract.profileId(profileId)]);
    function run(mode, action) {
      return transaction(database, mode, (tx, done, abort) => {
        const request = tx.objectStore('contexts').get(contextKey);
        request.onsuccess = () => {
          if (request.result?.epoch !== epoch) { abort(new contract.DraftError('context_revoked')); return; }
          try { action(tx, done, abort); } catch (error) { abort(error); }
        };
      });
    }
    function read(profileId) {
      const key = keyFor(profileId);
      return run('readonly', (tx, done) => {
        const request = tx.objectStore('drafts').get(key);
        request.onsuccess = () => done(decodeRecord(request.result, key, contextKey));
      });
    }
    function list() {
      const prefix = contextKey.slice(0, -1) + ',';
      const range = window.IDBKeyRange.bound(prefix, prefix + '\uffff');
      return run('readonly', (tx, done, abort) => {
        const records = [];
        const request = tx.objectStore('drafts').openCursor(range);
        request.onsuccess = () => {
          try {
            const cursor = request.result;
            if (!cursor) { done(records); return; }
            if (records.length >= 128) contract.fail('draft_list_limit');
            const parts = JSON.parse(cursor.key);
            const profileId = contract.profileId(parts.at(-1));
            records.push({profileId, ...decodeRecord(cursor.value, cursor.key, contextKey)});
            cursor.continue();
          } catch (error) { abort(error); }
        };
      });
    }
    async function save(value, expectedToken) {
      const draft = contract.validateDraft(value);
      if (draft.storeId !== context.storeId) contract.fail('context_mismatch');
      const key = keyFor(draft.profileId);
      return run('readwrite', (tx, done, abort) => {
        const drafts = tx.objectStore('drafts');
        const request = drafts.get(key);
        request.onsuccess = () => {
          try {
            const old = decodeRecord(request.result, key, contextKey);
            if ((old.token !== expectedToken) || (old.status !== 'none' && old.status !== 'valid')) contract.fail('local_conflict');
            if (old.status === 'valid' && (old.draft.draftId !== draft.draftId
                || old.draft.localRevision !== draft.localRevision
                || old.draft.baseRevision !== draft.baseRevision)) contract.fail('local_conflict');
            if (old.status === 'none' && (expectedToken !== null || draft.localRevision !== 0)) contract.fail('local_conflict');
            if (draft.localRevision >= Number.MAX_SAFE_INTEGER) contract.fail('revision_limit');
            const next = contract.validateDraft({...draft, localRevision: draft.localRevision + 1});
            const writeId = randomId();
            const createdAt = old.createdAt ?? now();
            if (typeof writeId !== 'string' || writeId.length !== 32 || !HEX_ID.test(writeId)
                || !Number.isSafeInteger(createdAt) || createdAt < 0) contract.fail('invalid_metadata');
            drafts.put({key, contextKey, writeId, createdAt, draft: next});
            done({draft: next, token: writeId, createdAt});
          } catch (error) { abort(error); }
        };
      });
    }
    function remove(profileId, expectedToken) {
      const key = keyFor(profileId);
      return run('readwrite', (tx, done, abort) => {
        const drafts = tx.objectStore('drafts');
        const request = drafts.get(key);
        request.onsuccess = () => {
          const raw = request.result;
          if ((raw?.writeId ?? null) !== expectedToken) { abort(new contract.DraftError('local_conflict')); return; }
          drafts.delete(key);
          done(true);
        };
      });
    }
    function clearContext() {
      return run('readwrite', (tx, done, abort) => {
        if (epoch >= Number.MAX_SAFE_INTEGER) { abort(new contract.DraftError('revision_limit')); return; }
        const prefix = contextKey.slice(0, -1) + ',';
        const range = window.IDBKeyRange.bound(prefix, prefix + '\uffff');
        function erase(name, next) {
          const request = tx.objectStore(name).openCursor(range);
          request.onsuccess = () => {
            try {
              const cursor = request.result;
              if (cursor) { cursor.delete(); cursor.continue(); } else next();
            } catch (error) { abort(error); }
          };
        }
        erase('drafts', () => erase('publications', () => {
          tx.objectStore('contexts').put({key: contextKey, epoch: epoch + 1});
          done(true);
        }));
      });
    }
    return Object.freeze({read, list, save, remove, clearContext,
      ...window.CCSDraftPublications({run, keyFor, contextKey, context, randomId}), context: Object.freeze({...context}), close: () => database.close()});
  }
  window.CCSDraftStore = Object.freeze({open});
})();
