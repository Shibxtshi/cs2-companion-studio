/* Studio panels and translated controls, independent of persistence and transport. */
(() => {
  'use strict';
  const COPY = {
    preview_blocked: ['Preview window blocked. Allow pop-ups for this local CCS origin.', 'Fenêtre d’aperçu bloquée. Autorise les fenêtres pour cette origine locale CCS.'],
    disk: ['Disk write failed · published data unchanged. Retry the same operation.', 'Échec d’écriture disque · version publiée inchangée. Réessaie la même opération.'],
    manage: ['Manage', 'Gérer'], newProfile: ['New profile', 'Nouveau profil'], copyProfile: ['Duplicate profile', 'Dupliquer le profil'],
    deleteProfile: ['Delete published profile…', 'Supprimer le profil publié…'], drafts: ['Local drafts', 'Brouillons locaux'],
    retry: ['Verify / retry', 'Vérifier / réessayer'], discardDraft: ['Discard local draft…', 'Abandonner le brouillon…'],
    recoverCopy: ['Recover as a new profile', 'Récupérer dans un nouveau profil'], compare: ['Compare local / published', 'Comparer le local et le publié'],
    openPreview: ['Open preview', 'Ouvrir l’aperçu'], closePreview: ['Close preview', 'Fermer l’aperçu'],
    draft_ready: ['Ready to edit', 'Prêt à modifier'], draft_kept: ['Draft retained · operation may still complete', 'Brouillon conservé · l’opération peut encore aboutir'],
    server_kept: ['Server version retained', 'Version serveur conservée'],
    context_revoked: ['Access revoked by logout in another tab. Authenticate again.', 'Accès révoqué par la déconnexion d’un autre onglet. Reconnecte-toi.'],
    publication_pending: ['Resolve the pending publication first.', 'Résous d’abord la publication en attente.'],
    profile_limit: ['Maximum 12 published or newly drafted profiles.', 'Maximum de 12 profils publiés ou nouveaux brouillons.'],
    storage_unavailable: ['Local storage unavailable · work is not confirmed saved', 'Stockage local indisponible · conservation non confirmée'],
    quota_exceeded: ['Local storage quota exceeded · work retained in memory', 'Quota local dépassé · travail conservé en mémoire'],
    transaction_aborted: ['Local transaction interrupted · retry required', 'Transaction locale interrompue · nouvelle tentative nécessaire'],
    draft_required: ['Open or resume a draft before editing.', 'Ouvre ou reprends un brouillon avant de modifier.'],
    session_closed: ['This edit session is closed.', 'Cette session d’édition est fermée.'],
    invalid_document: ['Invalid configuration · published data unchanged', 'Configuration invalide · version publiée inchangée'],
    available: ['Draft available', 'Brouillon disponible'],
    remote_newer: ['A newer server version exists. Review it before publishing.', 'Une version serveur plus récente existe. Examine-la avant publication.'],
    revision_mismatch: ['Draft revision is incompatible. Keep it for recovery.', 'Révision du brouillon incompatible. Conserve-le pour récupération.'],
    incompatible: ['Draft format is not supported. The original remains stored.', 'Format du brouillon non pris en charge. L’original reste conservé.'],
    corrupt: ['Draft is invalid. No automatic deletion was performed.', 'Brouillon invalide. Aucune suppression automatique effectuée.'],
    corrupt_journal: ['Pending publication is invalid. Keep local data and review recovery.', 'Intention de publication invalide. Conserve les données locales et examine la récupération.'],
    last_profile: ['The last published profile cannot be deleted.', 'Le dernier profil publié ne peut pas être supprimé.'],
    draft_list_limit: ['Too many local records to list safely. No record was deleted.', 'Trop d’enregistrements locaux à afficher. Aucun enregistrement supprimé.'],
    remote_changed: ['The reviewed server version changed again. Review the latest one.', 'La version serveur examinée a encore changé. Examine la dernière version.'],
    intro: ['Your layout. Your way to read the match.', 'Ta disposition. Ta lecture de la partie.'],
    isolated: ['Isolated target · synthetic profiles', 'Parcours cible isolé · profils synthétiques'],
    profile: ['Profile', 'Profil'], keep: ['Keep draft and leave', 'Conserver et quitter'],
    publish: ['Save and apply', 'Enregistrer et appliquer'], library: ['Widget library', 'Bibliothèque'],
    canvas: ['Canvas', 'Canevas'], properties: ['Properties', 'Propriétés'], search: ['Search widgets', 'Rechercher un widget'],
    preview: ['View', 'Vue'], synthetic: ['Synthetic data · not live GSI', 'Données synthétiques · pas de GSI réel'],
    localOnly: ['Local edits only', 'Modifications locales uniquement'], widget: ['Widget', 'Widget'],
    title: ['Custom title', 'Titre personnalisé'], presentation: ['Widget presentation', 'Présentation du widget'],
    geometry: ['Dimensions & position · cells', 'Dimensions et position · cellules'], width: ['Width', 'Largeur'], height: ['Height', 'Hauteur'],
    appearance: ['Appearance', 'Apparence'], accent: ['Accent · automatic when empty', 'Accent · automatique si vide'],
    background: ['Background · automatic when empty', 'Fond · automatique si vide'], opacity: ['Opacity', 'Opacité'],
    surface: ['Card surface', 'Style de surface'], duplicate: ['Duplicate', 'Dupliquer'], remove: ['Remove…', 'Supprimer…'],
    profileName: ['Profile name', 'Nom du profil'], theme: ['Profile theme', 'Thème du profil'],
    density: ['Dashboard density', 'Densité du dashboard'],
    densityHelp: ['Global spacing, independent of widget presentation and cell dimensions.', 'Espacement global, indépendant de la présentation et des dimensions des widgets.'],
    navigation: ['Navigation', 'Navigation'], floating: ['Floating navigation button', 'Bouton flottant de navigation'],
    fullscreenStatus: ['Connection status in fullscreen', 'Statut de connexion en plein écran'],
    profileLocal: ['These settings remain local until Save and apply.', 'Ces réglages restent locaux avant Enregistrer et appliquer.'],
    gestureHelp: ['Snap to grid · Escape cancels · No neighbour is pushed', 'Magnétisme à la cellule · Échap annule · Aucun voisin déplacé'],
    empty: ['Make room for your game.', 'Place à ta partie.'], emptyHelp: ['Add a widget from the library to get started.', 'Ajoute un widget depuis la bibliothèque pour commencer.'],
    loginHelp: ['Authenticate to access isolated target profiles.', 'Connecte-toi pour accéder aux profils cibles isolés.'],
    connect: ['Connect', 'Se connecter'], conflictTitle: ['A newer version is published', 'Une version plus récente est publiée'],
    keepDraft: ['Keep my draft', 'Conserver mon brouillon'], server: ['Use server version', 'Utiliser la version serveur'],
    replace: ['Publish my version…', 'Publier ma version…'],
    pristine: ['Published baseline · no local changes', 'Base publiée · aucune modification locale'],
    pending: ['Local changes · not published', 'Modifications locales · non publiées'], saving: ['Saving local draft…', 'Enregistrement local…'],
    saved: ['Draft kept locally · not published', 'Brouillon conservé · non publié'], editing: ['Editing gesture · not saved yet', 'Geste en cours · pas encore conservé'],
    publication_locked: ['Publishing · editing temporarily locked', 'Publication · édition temporairement bloquée'],
    published: ['Published version up to date', 'Version publiée à jour'], publishing: ['Publishing… awaiting server', 'Publication… attente du serveur'],
    validating: ['Validating and keeping draft…', 'Validation et conservation du brouillon…'],
    error: ['Local persistence failed · work retained in memory', 'Échec de conservation locale · travail gardé en mémoire'],
    local_error: ['Local storage error · not published', 'Erreur de stockage local · non publié'],
    local_conflict: ['Another tab changed this draft · no overwrite', 'Un autre onglet a modifié ce brouillon · aucun écrasement'],
    revision_conflict: ['Server version changed · your draft is kept', 'Version serveur modifiée · ton brouillon est conservé'],
    network_error: ['Disconnected · your draft is kept locally', 'Déconnecté · ton brouillon local est conservé'],
    publication_uncertain: ['Reply missing · publication outcome uncertain', 'Réponse absente · résultat de publication incertain'],
    reconciliation_required: ['Pending operation · reconcile before editing', 'Opération en attente · vérifier avant de reprendre'],
    profile_deleted: ['Published profile deleted · draft retained', 'Profil publié supprimé · brouillon conservé'],
    store_changed: ['Storage generation changed · draft not applied', 'Génération du stockage modifiée · brouillon non appliqué'],
    published_cleanup_error: ['Published · local cleanup failed', 'Publié · nettoyage local échoué'],
    published_draft_retained: ['Published snapshot confirmed · newer draft retained', 'Instantané publié confirmé · brouillon plus récent conservé'],
    server_error: ['Server refused publication · draft retained', 'Publication refusée par le serveur · brouillon conservé'],
    collision: ['Occupied cells · operation cancelled', 'Cellules occupées · opération annulée'],
    geometry_bounds: ['Outside grid bounds · operation cancelled', 'Limites de grille dépassées · opération annulée'],
    gesture_cancelled: ['Gesture cancelled', 'Geste annulé'],
    precise_controls: ['Use position fields or arrow controls at this width.', 'Utilise les champs de position ou les flèches à cette largeur.'],
    widget_limit: ['Maximum 60 widgets per profile.', 'Maximum de 60 widgets par profil.'],
    select: ['Select a widget to edit its properties.', 'Sélectionne un widget pour modifier ses propriétés.'],
    all: ['All categories', 'Toutes les catégories'], cancel: ['Cancel', 'Annuler'],
  };
  const DESCRIPTIONS = {
    score: ['CT/T score and match context', 'Score CT/T et contexte de partie'], map: ['Current map and game mode', 'Carte et mode de jeu'],
    round: ['Round number and reported phase', 'Numéro et phase de manche'], score_split: ['Detailed team score', 'Score détaillé des équipes'],
    match_phase: ['Match and round phases', 'Phases du match et de la manche'], round_history: ['Received round results', 'Résultats de manches reçus'],
    weapon: ['Active weapon and ammunition', 'Arme active et munitions'], ammo: ['Clip, reserve and ammo bar', 'Chargeur, réserve et jauge'],
    inventory: ['Personal received inventory', 'Inventaire personnel reçu'], grenades: ['Received personal grenades', 'Grenades personnelles reçues'],
    equip_value: ['Equipment value reported by CS2', 'Valeur d’équipement rapportée par CS2'], gear: ['Helmet, armor and defuse kit', 'Casque, armure et kit'],
    economy: ['Money and qualified projections', 'Argent et projections estimées'], cash: ['Available money', 'Argent disponible'],
    forecast: ['Estimated next-round economy', 'Économie estimée de la prochaine manche'], stats: ['Kills, assists and deaths', 'Éliminations, assistances et morts'],
    kd: ['Personal kill/death ratio', 'Ratio personnel éliminations/morts'], mvp: ['Reported MVP count', 'Nombre de MVP rapporté'],
    personal_score: ['Reported personal score', 'Score personnel rapporté'], round_stats: ['Reported round statistics', 'Statistiques de manche reçues'],
    health: ['Health points and meter', 'Points de vie et jauge'], armor: ['Armor value and meter', 'Valeur d’armure et jauge'],
    effects: ['Reported player effect levels', 'Niveaux des effets du joueur'], player: ['Player identity and activity', 'Identité et activité du joueur'],
    bomb: ['Bomb state and qualified estimate', 'État de bombe et estimation signalée'], bomb_state: ['Reported bomb state', 'État de bombe reçu'],
    events: ['Local inferred event journal', 'Journal local d’événements déduits'], connection: ['Data connection and freshness', 'Connexion et fraîcheur des données'],
    provider: ['Received GSI provider metadata', 'Métadonnées du fournisseur GSI'],
  };
  const byId = id => document.getElementById(id);
  const french = () => CS2I18N.locale() === 'FR';
  const text = key => COPY[key]?.[french() ? 1 : 0] || (french() ? 'Action impossible · ' : 'Action unavailable · ') + key;
  function choose(title, message, choices, {name = null, review = null} = {}) {
    const dialog = byId('studio-dialog');
    if (dialog.open) CCSDraftContract.fail('dialog_busy');
    for (const node of dialog.querySelectorAll('.studio-dialog-extra')) node.remove();
    if (name !== null) {
      const input = document.createElement('input'); input.id = 'studio-dialog-name'; input.className = 'studio-dialog-extra';
      input.value = name; input.maxLength = 32; input.required = true; input.setAttribute('aria-label', french() ? 'Nom du profil' : 'Profile name');
      byId('studio-dialog-message').after(input);
    }
    if (review) {
      const pre = document.createElement('pre'); pre.className = 'studio-dialog-extra'; pre.tabIndex = 0; pre.textContent = review;
      byId('studio-dialog-message').after(pre);
    }
    byId('studio-dialog-title').textContent = title;
    byId('studio-dialog-message').textContent = message;
    const actions = byId('studio-dialog-actions'); actions.replaceChildren();
    return new Promise(resolve => {
      function close() { dialog.removeEventListener('close', close); resolve(dialog.returnValue || 'cancel'); }
      dialog.addEventListener('close', close);
      for (const [value, label] of choices) {
        const button = document.createElement('button'); button.type = 'submit'; button.value = value; button.formNoValidate = value === 'cancel';
        button.textContent = label; button.setAttribute('translate', 'no'); actions.append(button);
      }
      dialog.returnValue = ''; dialog.showModal();
    });
  }
  window.CCSStudioWorkspace = ({edit, add, remove, duplicate, undo, redo, selectProfile, publish, leave, logout,
                               resolveConflict, profileAction, retry, discardDraft, recoverCopy, openPreview, gesture}) => {
    let content = null;
    let selectedId = null;
    let paintedSelection = null;
    let sessionState = null;
    let saveCode = 'published';
    let publicationCode = null;
    let inspectorMode = 'widget';
    const canvas = CCSStudioCanvas({board: byId('studio-board'),
      select(id) { selectedId = id; paintSelection(); }, gesture,
      report: issue,
      onGeometry(rectangle, code) {
        byId('studio-geometry-state').textContent = code === 'ready'
          ? `X ${rectangle.x} · Y ${rectangle.y} · ${rectangle.width} × ${rectangle.height}` : text(code);
      },
    });
    function issue(code) {
      byId('studio-alert').dataset.code = code;
      byId('studio-alert').textContent = text(code);
      byId('studio-alert').hidden = false;
    }
    function attempt(action) {
      try { const result = action(); result?.catch(error => issue(error.code || 'error')); }
      catch (error) { issue(error.code || 'error'); paintSelection(); }
    }
    function setValue(id, value) {
      const node = byId(id);
      if (document.activeElement === node && selectedId === paintedSelection) return;
      if (node.type === 'checkbox') node.checked = !!value;
      else node.value = value;
    }
    function selected() { return content?.configuration.layout.widgets.find(widget => widget.id === selectedId); }
    function paintSelection() {
      if (!content) return;
      const widget = selected();
      byId('studio-widget-fields').hidden = !widget;
      byId('studio-selection-label').textContent = widget ? CS2I18N.translate(CS2WidgetCatalog[widget.kind].title) + ' / ' + widget.kind : text('select');
      if (widget) {
        for (const key of ['title', 'variant', 'x', 'y', 'width', 'height', 'color', 'background', 'opacity', 'style']) setValue('studio-' + key, widget[key]);
        byId('studio-opacity-value').textContent = widget.opacity + '%';
        const [width, height] = CCSWidgetPresentation.minimum(widget.kind, widget.variant);
        byId('studio-minimum').textContent = (french() ? 'Minimum de lecture : ' : 'Reading minimum: ') + width + ' × ' + height + ' px. '
          + (french() ? 'La hauteur affichée peut grandir pour préserver le contenu.' : 'Displayed height may grow to preserve content.');
        byId('studio-geometry-state').textContent = `X ${widget.x} · Y ${widget.y} · ${widget.width} × ${widget.height}`;
      }
      const config = content.configuration;
      for (const [id, value] of [['profile-name', content.name], ['theme', config.theme], ['density', config.appearance.density],
        ['navigation', config.navigation.mode], ['floating', config.navigation.floatingButton], ['connection', config.fullscreen.showConnectionStatus]]) setValue('studio-' + id, value);
      paintedSelection = selectedId;
      canvas.update(content, selectedId, sessionState?.publicationLocked || sessionState?.closed || false);
    }
    function changeWidget(key, value) {
      const widget = selected(); if (!widget) return;
      attempt(() => edit(CCSStudioModel.changeWidget(content, widget.id, {[key]: value},
        {geometry: ['x', 'y', 'width', 'height'].includes(key)})));
      byId('studio-' + key).value = selected()?.[key] ?? '';
    }
    function changeProfile(change) {
      if (!content) return;
      const next = structuredClone(content); change(next); attempt(() => edit(next));
    }
    function library() {
      const list = byId('studio-library-items'); list.replaceChildren();
      const query = byId('studio-search').value.trim().toLocaleLowerCase();
      const category = byId('studio-category').value;
      let previous = null;
      for (const [kind, definition] of Object.entries(CS2WidgetCatalog)) {
        const title = CS2I18N.translate(definition.title);
        const description = DESCRIPTIONS[kind][french() ? 1 : 0];
        if ((category && category !== definition.cat) || !`${title} ${kind} ${description}`.toLocaleLowerCase().includes(query)) continue;
        if (previous !== definition.cat) {
          const label = document.createElement('h3'); label.className = 'studio-library-group';
          label.textContent = CS2I18N.translate(definition.cat); list.append(label); previous = definition.cat;
        }
        const row = document.createElement('div'); row.className = 'studio-library-item'; row.dataset.kind = kind;
        const info = document.createElement('div'); const heading = document.createElement('h3'); const detail = document.createElement('p');
        heading.textContent = title; detail.textContent = description; info.append(heading, detail);
        const button = document.createElement('button'); button.type = 'button'; button.textContent = '+';
        button.setAttribute('aria-label', (french() ? 'Ajouter ' : 'Add ') + title);
        button.addEventListener('click', () => attempt(() => add(kind)));
        row.append(info, button); list.append(row);
      }
    }
    function locale() {
      for (const node of document.querySelectorAll('[data-copy]')) { node.setAttribute('translate', 'no'); node.textContent = text(node.dataset.copy); }
      byId('studio-search').placeholder = text('search');
      byId('studio-logout').textContent = french() ? 'Déconnexion' : 'Log out';
      byId('studio-undo').setAttribute('aria-label', french() ? 'Annuler' : 'Undo');
      byId('studio-redo').setAttribute('aria-label', french() ? 'Rétablir' : 'Redo');
      const selectedCategory = byId('studio-category').value;
      byId('studio-category').replaceChildren(new Option(text('all'), ''), ...[...new Set(Object.values(CS2WidgetCatalog).map(widget => widget.cat))].map(cat => new Option(CS2I18N.translate(cat), cat)));
      byId('studio-category').value = selectedCategory;
      for (const [id, labels] of [['studio-density', french() ? ['Normale', 'Espacement compact'] : ['Normal', 'Compact spacing']],
        ['studio-navigation', french() ? ['Complète', 'Compacte', 'Masquée'] : ['Full', 'Compact', 'Hidden']],
        ['studio-preview-mode', french() ? ['Édition', 'Dashboard'] : ['Edit', 'Dashboard']],
        ['studio-style', french() ? ['Solide', 'Verre', 'Contour'] : ['Solid', 'Glass', 'Outline']]]) {
        [...byId(id).options].forEach((option, index) => { option.textContent = labels[index]; });
      }
      library(); paintSelection(); status(saveCode, publicationCode);
    }
    function status(localCode, remoteCode = null) {
      saveCode = localCode; publicationCode = remoteCode;
      const code = remoteCode || localCode;
      byId('studio-save-state').textContent = text(code);
      byId('studio-save-state').parentElement.dataset.state = localCode;
      const locked = !content || !!sessionState?.publicationLocked || !!sessionState?.closed;
      byId('studio-publish').disabled = locked;
      for (const node of document.querySelectorAll('.studio-inspector input,.studio-inspector select,#studio-duplicate,#studio-remove,.studio-nudge button,#studio-library-items button')) node.disabled = locked;
      byId('studio-undo').disabled = !sessionState?.canUndo || !!sessionState?.publicationLocked;
      byId('studio-redo').disabled = !sessionState?.canRedo || !!sessionState?.publicationLocked;
    }
    for (const key of ['title', 'variant', 'x', 'y', 'width', 'height', 'color', 'background', 'opacity', 'style']) {
      byId('studio-' + key).addEventListener('change', event => changeWidget(key,
        ['x','y','width','height','opacity'].includes(key) ? Number(event.target.value) : event.target.value));
    }
    byId('studio-profile-name').addEventListener('change', event => changeProfile(next => { next.name = event.target.value.trim(); }));
    byId('studio-theme').addEventListener('change', event => changeProfile(next => { next.configuration.theme = event.target.value; }));
    byId('studio-density').addEventListener('change', event => changeProfile(next => { next.configuration.appearance.density = event.target.value; }));
    byId('studio-navigation').addEventListener('change', event => changeProfile(next => { next.configuration.navigation.mode = event.target.value; }));
    byId('studio-floating').addEventListener('change', event => changeProfile(next => { next.configuration.navigation.floatingButton = event.target.checked; }));
    byId('studio-connection').addEventListener('change', event => changeProfile(next => { next.configuration.fullscreen.showConnectionStatus = event.target.checked; }));
    for (const button of document.querySelectorAll('[data-nudge]')) button.addEventListener('click', () => {
      const widget = selected(); if (!widget) return;
      const [x,y] = button.dataset.nudge.split(',').map(Number);
      attempt(() => edit(CCSStudioModel.changeWidget(content, widget.id, {x: widget.x + x, y: widget.y + y}, {geometry: true})));
    });
    byId('studio-remove').addEventListener('click', () => attempt(() => remove(selectedId)));
    byId('studio-duplicate').addEventListener('click', () => attempt(() => duplicate(selectedId)));
    byId('studio-undo').addEventListener('click', () => attempt(undo)); byId('studio-redo').addEventListener('click', () => attempt(redo));
    byId('studio-profile').addEventListener('change', event => attempt(() => selectProfile(event.target.value)));
    for (const [id, action] of [['studio-create','create'], ['studio-copy-profile','copy'], ['studio-delete-profile','delete'], ['studio-local-drafts','drafts']]) {
      byId(id).addEventListener('click', () => { document.querySelector('.studio-profile-actions').open = false; attempt(() => profileAction(action)); });
    }
    byId('studio-retry').addEventListener('click', () => attempt(retry));
    byId('studio-discard-draft').addEventListener('click', () => attempt(discardDraft));
    byId('studio-recover-copy').addEventListener('click', () => attempt(recoverCopy));
    byId('studio-open-preview').addEventListener('click', () => attempt(openPreview));
    byId('studio-publish').addEventListener('click', () => attempt(publish));
    byId('studio-leave').addEventListener('click', () => attempt(leave)); byId('studio-logout').addEventListener('click', () => attempt(logout));
    for (const action of ['keep','server','local']) byId('studio-conflict-' + action).addEventListener('click', () => attempt(() => resolveConflict(action)));
    byId('studio-search').addEventListener('input', library); byId('studio-category').addEventListener('change', library);
    byId('studio-preview-mode').addEventListener('change', event => canvas.setPreview(event.target.value === 'dashboard'));
    for (const button of document.querySelectorAll('.studio-panel-tabs button[data-panel]')) button.addEventListener('click', () => {
      document.querySelector('.studio-workspace').dataset.panel = button.dataset.panel;
      for (const item of document.querySelectorAll('.studio-panel-tabs button')) item.setAttribute('aria-pressed', String(item === button));
      canvas.refresh();
    });
    function inspector(mode) {
      inspectorMode = mode;
      byId('studio-widget-properties').hidden = mode !== 'widget'; byId('studio-profile-properties').hidden = mode !== 'profile';
      byId('studio-widget-tab').setAttribute('aria-pressed', String(mode === 'widget'));
      byId('studio-profile-tab').setAttribute('aria-pressed', String(mode === 'profile'));
    }
    byId('studio-widget-tab').addEventListener('click', () => inspector('widget'));
    byId('studio-profile-tab').addEventListener('click', () => inspector('profile'));
    const closeMenu = event => {
      const menu = document.querySelector('.studio-profile-actions');
      if (menu.open && !event.target.closest('.studio-profile-actions')) menu.open = false;
    };
    document.addEventListener('pointerdown', closeMenu);
    const keyboard = event => {
      const menu = document.querySelector('.studio-profile-actions');
      if (event.key === 'Escape' && menu.open) { menu.open = false; menu.querySelector('summary').focus(); return; }
      if (event.target.closest('input,textarea,select,[contenteditable="true"]') || byId('studio-dialog').open) return;
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') { event.preventDefault(); attempt(event.shiftKey ? redo : undo); }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y') { event.preventDefault(); attempt(redo); }
    };
    document.addEventListener('keydown', keyboard);
    document.addEventListener('cs2:locale-changed', locale);
    locale();
    return Object.freeze({canvas, issue, status, choose, text,
      clearIssue(code = null) { if (code === null || byId('studio-alert').dataset.code === code) byId('studio-alert').hidden = true; },
      get selectedId() { return selectedId; },
      select(id) { selectedId = id; inspector('widget'); paintSelection(); },
      paint(next, currentState) {
        content = CCSDraftContract.content({name: next.name, configuration: next.configuration}); sessionState = currentState;
        if (!content.configuration.layout.widgets.some(widget => widget.id === selectedId)) selectedId = null;
        document.documentElement.dataset.theme = content.configuration.theme;
        document.documentElement.style.setProperty('--profile-accent', content.configuration.appearance.accent || 'var(--ccs-accent)');
        byId('studio-grid-caption').textContent = content.configuration.layout.columns + (french() ? ' colonnes · 32 px / ligne' : ' columns · 32 px / row');
        byId('studio-empty').hidden = content.configuration.layout.widgets.length > 0;
        paintSelection(); status(saveCode, publicationCode);
      },
      recovery({retry = false, discard = false, copy = false, cleanup = false} = {}) {
        byId('studio-retry').hidden = !retry; byId('studio-discard-draft').hidden = !discard; byId('studio-recover-copy').hidden = !copy;
        byId('studio-retry').textContent = cleanup ? french() ? 'Terminer le nettoyage local' : 'Finish local cleanup' : text('retry');
      },
      async name(title, initial = '') {
        const result = await choose(title, french() ? 'Ce profil restera local avant publication.' : 'This profile stays local until publication.',
          [['confirm', french() ? 'Continuer' : 'Continue'], ['cancel', text('cancel')]], {name: initial});
        return result === 'confirm' ? byId('studio-dialog-name').value.trim() : null;
      },
      catalog(catalog, profileId, drafts = []) {
        const menu = byId('studio-profile');
        menu.replaceChildren(...catalog.profiles.map(profile => new Option(profile.name, profile.id)),
          ...drafts.filter(record => !catalog.profiles.some(profile => profile.id === record.profileId)).map(record =>
            new Option((record.draft?.name || record.profileId) + (french() ? ' · brouillon local' : ' · local draft'), record.profileId)));
        menu.value = profileId;
      },
      review(local, published) { byId('studio-remote-review').textContent = JSON.stringify({local, published}, null, 2); },
      conflict(value, message = '') { byId('studio-conflict').hidden = !value; byId('studio-conflict-description').textContent = message; },
      dispose() { canvas.dispose(); document.removeEventListener('pointerdown', closeMenu); document.removeEventListener('keydown', keyboard); document.removeEventListener('cs2:locale-changed', locale); },
    });
  };
})();
