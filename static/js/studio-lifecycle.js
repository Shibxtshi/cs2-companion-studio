/* Studio workflow composition. Persistence/history/publication remain owned by P4/P5. */
(() => {
  'use strict';
  const contract = CCSDraftContract;
  const contentOf = value => contract.content({name: value.name, configuration: value.configuration});
  const fr = () => CS2I18N.locale() === 'FR';
  window.CCSStudioLifecycle = ({profiles, send, workspace, exit, disconnected, sharedSelection = false}) => {
    let store = null;
    let contextKey = null;
    let session = null;
    let publication = null;
    let editingId = null;
    let view = null;
    let records = [];
    let localCode = 'published';
    let remoteCode = null;
    let blocked = false;
    let journal = false;
    let readOnly = false;
    let recoverable = false;
    let opening = 0;
    let initializing = null;
    let waitingRevision = null;
    let operationKind = 'update';
    let confirmedPublication = null;
    let finalizedResult = null;
    const message = (en, french) => fr() ? french : en;
    function issue(error) {
      const code = typeof error === 'string' ? error : error.code || 'error';
      if (code === 'context_revoked') blocked = true;
      workspace.issue(code);
    }
    function paint() {
      const value = session?.preview || view;
      if (value) workspace.paint(value, {...session?.state,
        publicationLocked: blocked || readOnly || !!session?.state.publicationLocked,
        canUndo: session?.state.canUndo && !blocked && !readOnly,
        canRedo: session?.state.canRedo && !blocked && !readOnly});
      const published = profiles.profile(editingId);
      const unchanged = session && !session.state.dirty && published
        && session.draft.baseRevision === published.revision
        && contract.canonical(session.preview) === contract.canonical(contentOf(published));
      workspace.status(unchanged && ['saved', 'pristine'].includes(localCode) ? 'published' : localCode, remoteCode);
      const hasDraft = session ? session.state.dirty || session.state.hasPersistedDraft
        : records.some(record => record.profileId === editingId);
      workspace.recovery({retry: !!journal || blocked || localCode === 'error', discard: !!hasDraft,
        copy: !!hasDraft && (!!session || recoverable), cleanup: remoteCode === 'published_cleanup_error'});
      const publishButton = document.getElementById('studio-publish');
      publishButton.disabled ||= journal || blocked || readOnly || !!unchanged;
    }
    async function refreshRecords() {
      records = await store.list();
      if (!session) recoverable = records.some(record => record.profileId === editingId && record.status === 'valid');
      workspace.catalog(profiles.catalog, editingId || profiles.selectedProfileId, records);
    }
    function remember(id) {
      try {
        const key = 'ccs-studio-profile:' + store.context.storeId;
        sessionStorage.setItem(key, id);
        localStorage.setItem(key, id);
      } catch {}
    }
    function preferred() {
      try {
        const key = 'ccs-studio-profile:' + store.context.storeId;
        return sessionStorage.getItem(key) || localStorage.getItem(key);
      } catch { return null; }
    }
    function showConflict() {
      const published = profiles.profile(editingId);
      workspace.conflict(true, message('Your draft is retained. No version is overwritten automatically.',
        'Ton brouillon est conservé. Aucune version n’est écrasée automatiquement.'));
      workspace.review(session?.preview || view, published ? contentOf(published) : null);
    }
    function buildController() {
      publication?.dispose();
      publication = CCSProfilePublication({store, profiles, send, session, profileId: editingId,
        onStatus(state) {
          remoteCode = state.code === 'draft_ready' ? null : state.code;
          if (state.error) issue(state.error);
          if (['validating', 'publishing'].includes(state.code)) readOnly = true;
          if (state.code === 'publishing') journal = true;
          if (['local_error', 'local_conflict', 'server_error', 'network_error', 'revision_conflict',
            'publication_uncertain', 'profile_deleted', 'draft_kept'].includes(state.code)) readOnly = !session;
          if (state.code === 'store_changed') blocked = true;
          if (['revision_conflict', 'profile_deleted', 'publication_uncertain', 'reconciliation_required'].includes(state.code)) showConflict();
          if (state.serverCommitted) { confirmedPublication = {...state}; workspace.conflict(false); }
          paint();
        },
      });
    }
    async function startSession(profile, creation, choice) {
      const next = await CCSDraftSession.start({store, published: profile, creation, choice, persistOnStart: !profile,
        onStatus(state) { localCode = state.code; if (state.error) issue(state.error); else if (state.code === 'saved' && !blocked) workspace.clearIssue(); paint(); }});
      session = next; recoverable = choice === 'resume' || !profile;
      view = next.preview;
      readOnly = false;
      buildController();
      paint();
    }
    async function open(id, {resume = false} = {}) {
      const generation = ++opening;
      session?.dispose(); session = null;
      publication?.dispose(); publication = null;
      editingId = id;
      remoteCode = null; journal = false; readOnly = true;
      workspace.conflict(false);
      const published = profiles.profile(id);
      const stored = await store.read(id);
      const pending = await store.pendingPublication(id);
      if (generation !== opening) return;
      recoverable = stored.status === 'valid';
      view = stored.status === 'valid' ? contentOf(stored.draft) : published ? contentOf(published) : null;
      if (pending.status !== 'none') {
        journal = true;
        buildController();
        await publication.restorePending();
        if (pending.status === 'corrupt') issue('corrupt_journal');
        paint(); return;
      }
      const tombstoned = profiles.catalog.tombstones.some(item => item.id === id);
      const creation = !published && !tombstoned && stored.status === 'valid' && stored.draft.baseRevision === 0
        ? {id, ...contentOf(stored.draft)} : null;
      const found = published ? await CCSDraftSession.inspect({store, profileId: id, published})
        : creation ? {...stored, status: 'available'} : {...stored, status: stored.status === 'valid' ? 'profile_deleted' : stored.status};
      if (generation !== opening) return;
      if (found.status === 'none' && !published) { issue('profile_deleted'); paint(); return; }
      if (!['none', 'available'].includes(found.status)) {
        buildController(); showConflict(); issue(found.status); paint(); return;
      }
      if (found.status === 'available' && !resume) {
        paint();
        const answer = await workspace.choose(message('Resume local draft?', 'Reprendre le brouillon local ?'),
          message('The dashboard remains unchanged until you explicitly publish.', 'Le dashboard reste inchangé avant une publication explicite.'),
          [['resume', message('Resume', 'Reprendre')], ['discard', message('Discard…', 'Abandonner…')], ['cancel', workspace.text('cancel')]]);
        if (answer === 'discard') { await discardDraft(); return; }
        if (answer !== 'resume') { paint(); return; }
      }
      if (generation !== opening) return;
      await startSession(published, creation, found.status === 'available' ? 'resume' : 'new');
      remember(id);
      await refreshRecords();
    }
    async function initialize() {
      if (initializing) return initializing;
      initializing = (async () => {
        if (!profiles.ready) return;
        const key = JSON.stringify(profiles.context);
        if (store) {
          if (key !== contextKey) { blocked = true; issue('store_changed'); paint(); }
          return;
        }
        store = await CCSDraftStore.open({context: profiles.context});
        blocked = false; remoteCode = null;
        contextKey = key;
        await refreshRecords();
        const candidate = sharedSelection ? CCSProfileSelection.read(profiles.context) : preferred() || CCSProfileSelection.read(profiles.context);
        const id = profiles.profile(candidate) || records.some(record => record.profileId === candidate)
          ? candidate : profiles.selectedProfileId;
        if (profiles.profile(id)) profiles.select(id);
        await open(id);
      })();
      try { return await initializing; } finally { initializing = null; }
    }
    async function finishPublication(result) {
      const key = result.operationId + ':' + result.code;
      if (result.serverCommitted && finalizedResult === key) return;
      if (result.serverCommitted) finalizedResult = key;
      if (result.code !== 'published') {
        journal = (await store.pendingPublication(editingId)).status !== 'none';
        if (result.code === 'published_draft_retained') showConflict();
        paint(); return;
      }
      journal = false; workspace.clearIssue();
      await refreshRecords();
      if (operationKind === 'delete') {
        session?.dispose(); session = null; readOnly = true;
        remoteCode = 'profile_deleted'; showConflict(); paint(); return;
      }
      waitingRevision = result.revision;
      await settlePublished();
      if (waitingRevision) profiles.request();
    }
    async function settlePublished() {
      const latest = profiles.profile(editingId);
      if (!waitingRevision || !latest || latest.revision < waitingRevision) return;
      waitingRevision = null;
      profiles.select(editingId); CCSProfileSelection.remember(profiles.context, editingId);
      const stored = await store.read(editingId);
      if (stored.status !== 'none') { remoteCode = 'published_draft_retained'; readOnly = true; showConflict(); paint(); return; }
      session?.dispose(); session = null;
      await startSession(latest, null, 'new');
      remoteCode = 'published';
      paint();
    }
    async function publish() {
      if (blocked || readOnly || journal || !session) contract.fail(journal ? 'publication_pending' : 'draft_required');
      workspace.canvas.cancel();
      operationKind = session.draft.baseRevision === 0 ? 'create' : 'update';
      const result = await publication.publish();
      await finishPublication(result);
      return result;
    }
    async function retry() {
      if (blocked) {
        const answer = await workspace.choose(message('Authenticate again?', 'Se reconnecter ?'),
          message('The previous local access is no longer valid. Close this session and discard its unconfirmed in-memory changes? Existing recovery records are not deleted.',
            'L’ancien accès local n’est plus valide. Fermer cette session et abandonner ses changements non confirmés en mémoire ? Les copies de récupération existantes ne seront pas supprimées.'),
          [['confirm', message('Close and authenticate again', 'Fermer et se reconnecter')], ['cancel', workspace.text('cancel')]]);
        if (answer !== 'confirm') return;
        session?.dispose(); publication?.dispose(); store?.close();
        session = null; publication = null; store = null; contextKey = null; editingId = null; view = null; journal = false;
        disconnected(); return;
      }
      if (!journal) { await session?.flush(); paint(); return; }
      operationKind = publication.pendingOperation?.kind || (await store.pendingPublication(editingId)).operation?.kind || 'update';
      const result = await publication.retry();
      await finishPublication(result);
    }
    async function confirmLeave(action = null) {
      workspace.canvas.cancel();
      if (!session || session.state.closed) return true;
      const current = profiles.profile(editingId);
      if (!journal && !session.state.dirty && current
          && contract.canonical(session.preview) === contract.canonical(contentOf(current))) { session.dispose(); session = null; return true; }
      const chosen = action || await workspace.choose(message('Leave the Studio?', 'Quitter le Studio ?'),
        message('Local drafts are independent of the published dashboard. An operation already sent cannot be cancelled by leaving.',
          'Le brouillon est indépendant du dashboard publié. Quitter n’annule pas une opération déjà envoyée.'),
        [['publish', workspace.text('publish')], ['keep', workspace.text('keep')],
          ['discard', message('Discard changes', 'Abandonner les modifications')], ['cancel', message('Continue editing', 'Continuer l’édition')]]);
      if (chosen === 'cancel') return false;
      if (chosen === 'publish') return (await publish())?.code === 'published';
      if (chosen === 'discard') return discardDraft({reopen: false});
      if (journal) publication.keepDraft();
      await session.keepAndLeave();
      return true;
    }
    async function discardDraft({reopen = true} = {}) {
      if (journal) { issue('publication_pending'); return false; }
      const found = await store.read(editingId);
      const answer = await workspace.choose(message('Discard local draft?', 'Abandonner le brouillon local ?'),
        message('Only the reviewed local draft will be removed. Other tabs cannot be overwritten.',
          'Seul le brouillon local examiné sera supprimé. Aucun travail plus récent d’un autre onglet ne sera écrasé.'),
        [['discard', message('Discard', 'Abandonner')], ['cancel', workspace.text('cancel')]]);
      if (answer !== 'discard') return false;
      if (session && !session.state.closed) await session.discard();
      else await store.remove(editingId, found.token);
      session?.dispose(); session = null; workspace.clearIssue(); workspace.conflict(false);
      await refreshRecords();
      if (reopen) await open(profiles.profile(editingId) ? editingId : profiles.selectedProfileId);
      return true;
    }
    async function selectProfile(id) {
      if (id === editingId) return;
      if (!await confirmLeave()) { await refreshRecords(); return; }
      if (profiles.profile(id)) { profiles.select(id); CCSProfileSelection.remember(profiles.context, id); }
      await open(id);
    }
    async function createFrom(value, {recovering = false, imported = false} = {}) {
      await refreshRecords();
      const creations = records.filter(record => record.status === 'valid' && record.draft.baseRevision === 0
        && !profiles.profile(record.profileId));
      if (profiles.catalog.profiles.length + creations.length >= 12) contract.fail('profile_limit');
      const initial = value ? imported ? value.name : (value.name.slice(0, 24) + message(' copy', ' copie')) : '';
      const name = await workspace.name(message('New local profile', 'Nouveau profil local'), initial);
      if (!name) return;
      const configuration = value ? structuredClone(value.configuration) : {
        theme: 'tactical-blue', appearance: {accent: '', background: '', density: 'normal'},
        navigation: {mode: 'compact', floatingButton: true}, fullscreen: {showConnectionStatus: true},
        layout: {columns: 24, widgets: []},
      };
      const creation = {id: contract.uuid(), ...contract.content({name, configuration})};
      if (!recovering && !await confirmLeave()) return;
      // Commit the recovery copy before releasing potentially unsaved work in memory.
      const next = await CCSDraftSession.start({store, creation, choice: 'new'});
      try { await next.flush(); } catch (error) { next.dispose(); throw error; }
      next.dispose();
      session?.dispose(); session = null;
      await open(creation.id, {resume: true});
    }
    async function profileAction(action) {
      if (blocked) contract.fail('store_changed');
      if (action === 'create') return createFrom(null);
      if (action === 'copy') return createFrom(session?.preview || view);
      if (action === 'drafts') {
        await refreshRecords();
        const choices = records.map(record => [record.profileId, (record.draft?.name || record.profileId) + ' · ' + record.status]);
        const selected = await workspace.choose(workspace.text('drafts'),
          message('Drafts are local to this installation and browser. Invalid data is retained until explicit removal.',
            'Ces brouillons sont locaux à cette installation et à ce navigateur. Les données invalides restent conservées avant suppression explicite.'),
          [...choices, ['cancel', workspace.text('cancel')]]);
        if (selected !== 'cancel') { if (selected === editingId && !session) await open(selected); else await selectProfile(selected); }
        return;
      }
      const latest = profiles.profile(editingId);
      if (!latest) contract.fail('profile_deleted');
      if (profiles.catalog.profiles.length <= 1) contract.fail('last_profile');
      if (journal) contract.fail('publication_pending');
      const answer = await workspace.choose(message('Delete published profile?', 'Supprimer le profil publié ?'),
        message('This explicitly publishes a deletion. Local drafts on every device are retained for recovery.',
          'Cette action publie explicitement une suppression. Les brouillons locaux de tous les appareils restent récupérables.'),
        [['delete', message('Delete published profile', 'Supprimer le profil publié')], ['cancel', workspace.text('cancel')]]);
      if (answer !== 'delete') return;
      const revision = latest.revision;
      if (session && !session.state.closed) await session.keepAndLeave();
      session?.dispose(); session = null;
      buildController(); operationKind = 'delete';
      const result = await publication.deleteProfile(revision);
      await finishPublication(result);
    }
    async function resolveConflict(action) {
      if (action === 'keep') { publication?.keepDraft(); workspace.conflict(false); paint(); return; }
      const latest = profiles.profile(editingId);
      if (!latest) contract.fail('profile_deleted');
      const local = session?.preview || view;
      const stored = await store.read(editingId);
      const review = JSON.stringify({local, published: contentOf(latest)}, null, 2);
      const answer = await workspace.choose(action === 'local' ? workspace.text('replace') : workspace.text('server'),
        message('Review the complete configurations below. Published revision: ', 'Examine les configurations complètes ci-dessous. Révision publiée : ')
          + latest.revision + '.', [['confirm', message('Confirm', 'Confirmer')], ['cancel', workspace.text('cancel')]], {review});
      if (answer !== 'confirm') return;
      if (!publication) buildController();
      if (action === 'local') {
        operationKind = 'update';
        await finishPublication(await publication.useLocal({confirmed: true, reviewedRevision: latest.revision, reviewedDraftToken: stored.token}));
      } else {
        await publication.useServer({confirmed: true, reviewedRevision: latest.revision, reviewedDraftToken: stored.token});
        workspace.clearIssue();
        session?.dispose(); session = null; journal = false;
        await open(editingId);
      }
    }
    async function logout() {
      const answer = await workspace.choose(message('Log out of CCS?', 'Se déconnecter de CCS ?'),
        message('Erase local drafts and pending intents for this context? This does not cancel an operation already sent to the server.',
          'Effacer les brouillons et intentions de ce contexte ? Cela n’annule pas une opération déjà envoyée au serveur.'),
        [['logout', message('Erase and log out', 'Effacer et déconnecter')], ['cancel', workspace.text('cancel')]]);
      if (answer !== 'logout') return;
      workspace.canvas.cancel();
      await CCSDraftSession.logout({store, confirmed: true});
      session?.dispose(); publication?.dispose(); store.close();
      session = null; publication = null; store = null; contextKey = null; editingId = null; view = null;
      disconnected();
    }
    async function catalogChanged() {
      if (!profiles.ready) return;
      await initialize();
      if (!store) return;
      await refreshRecords();
      if (waitingRevision) await settlePublished();
      if (editingId && !profiles.profile(editingId) && session?.draft.baseRevision > 0) {
        remoteCode = 'profile_deleted'; showConflict();
      }
      paint();
    }
    function edit(next) {
      if (!session || blocked || readOnly) contract.fail('draft_required');
      session.edit(next);
      if (!journal) remoteCode = null;
      paint();
    }
    function releaseContext() {
      ++opening;
      publication?.dispose(); session?.dispose(); store?.close();
      publication = null; session = null; store = null; contextKey = null;
      editingId = null; view = null; records = []; localCode = 'published'; remoteCode = null;
      journal = false; blocked = false; readOnly = false; recoverable = false;
      waitingRevision = null; confirmedPublication = null; finalizedResult = null;
    }
    return Object.freeze({initialize, catalogChanged, edit, publish, retry, selectProfile, profileAction, resolveConflict,
      discardDraft, logout, issue,
      releaseContext,
      requestLeave: confirmLeave,
      async enter(id = profiles.selectedProfileId) {
        await initialize();
        if (!session || session.state.closed || editingId !== id) await open(id);
        else paint();
      },
      importProfile(value, replace = false) {
        const content = contract.content(value);
        return replace ? edit(content) : createFrom(content, {imported: true});
      },
      get preview() { return session?.preview || view; },
      get dirty() { return !!session?.state.dirty || !!session?.state.gestureActive; },
      snapshot: () => ({draft: session?.draft || null, state: session?.state || null,
        publication: remoteCode === 'published' ? confirmedPublication : publication?.state || null, selectedProfileId: editingId, readOnly, blocked}),
      async recoverCopy() { const value = session?.preview || view; if ((!session && !recoverable) || !value) contract.fail('corrupt_draft'); return createFrom(value, {recovering: true}); },
      async leave(action = null) { if (await confirmLeave(action)) exit(); },
      async receive(message) {
        const current = publication;
        const consumed = await current?.receive(message);
        if (consumed && current === publication && current.state.serverCommitted) await finishPublication(current.state);
      },
      networkLost() { publication?.disconnected(); workspace.issue('network_error'); },
      undo() { if (blocked || readOnly) contract.fail('draft_required'); session?.undo(); paint(); },
      redo() { if (blocked || readOnly) contract.fail('draft_required'); session?.redo(); paint(); },
      gesture: Object.freeze({
        begin() { if (blocked || readOnly) contract.fail('draft_required'); session.beginGesture(); },
        cancel() { if (session?.state.gestureActive) session.cancelGesture(); paint(); },
        commit(next) { session.previewGesture(next); session.endGesture(); paint(); }, edit,
      }),
      async checkContext() { if (store && editingId) { try { await store.read(editingId); } catch (error) { issue(error); paint(); } } },
      dispose: releaseContext,
    });
  };
})();
