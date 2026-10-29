/* Authenticated catalog convergence and tab-owned profile selection, without UI. */
(() => {
  'use strict';
  const contract = window.CCSDraftContract;
  window.CCSPublishedProfiles = ({send, isDemo = () => false, onChange = () => {}, onStatus = () => {}, preferredProfile = null}) => {
    let authenticated = false;
    let catalog = null;
    let selected = preferredProfile;
    let context = null;
    function receive(message) {
      if (isDemo()) return false;
      if (message?.type === 'auth_ok') { authenticated = true; return true; }
      if (message?.type === 'auth_error') {
        authenticated = false; context = null; catalog = null; selected = preferredProfile;
        onChange({catalog: null, selectedProfileId: null, selectedProfileChanged: true});
        return true;
      }
      if (!authenticated || !['profiles_catalog', 'profile_operation_error'].includes(message?.type) || !message.catalog) return false;
      const next = contract.validateCatalog(message.catalog);
      if (catalog && next.storeId === catalog.storeId && next.catalogRevision < catalog.catalogRevision) return true;
      if (catalog && next.storeId === catalog.storeId && next.catalogRevision === catalog.catalogRevision
          && contract.canonical(next) !== contract.canonical(catalog)) contract.fail('invalid_catalog');
      if (catalog && next.storeId === catalog.storeId && next.catalogRevision === catalog.catalogRevision) {
        if (!context) {
          context = contract.access({storeId: next.storeId, accessId: next.accessId, authenticated: true});
          onStatus('synchronized');
        }
        return true;
      }
      const previousProfile = catalog?.profiles.find(profile => profile.id === selected);
      const changedGeneration = catalog && next.storeId !== catalog.storeId;
      const previous = selected;
      catalog = next;
      context = contract.access({storeId: next.storeId, accessId: next.accessId, authenticated: true});
      if (!catalog.profiles.some(profile => profile.id === selected)) selected = catalog.profiles[0].id;
      if (changedGeneration) onStatus('store_changed');
      else if (previous && previous !== selected) onStatus('profile_deleted');
      const selectedProfile = catalog.profiles.find(profile => profile.id === selected);
      onChange({catalog: structuredClone(catalog), selectedProfileId: selected,
        selectedProfileChanged: !!changedGeneration || !previousProfile || previousProfile.id !== selected
          || previousProfile.revision !== selectedProfile.revision});
      return true;
    }
    return Object.freeze({receive,
      disconnected() { authenticated = false; context = null; },
      clear() {
        authenticated = false; catalog = null; context = null; selected = preferredProfile;
        onChange({catalog: null, selectedProfileId: null, selectedProfileChanged: true});
      },
      select(profileId) {
        if (isDemo()) contract.fail('access_required');
        if (!catalog?.profiles.some(profile => profile.id === profileId)) contract.fail('profile_missing');
        if (selected === profileId) return;
        selected = profileId;
        onChange({catalog: structuredClone(catalog), selectedProfileId: selected, selectedProfileChanged: true});
      },
      request() {
        if (!authenticated || isDemo()) contract.fail('access_required');
        send({type: 'profile_catalog_request'});
      },
      get ready() { return authenticated && !!context && !isDemo(); },
      get context() { return authenticated && !isDemo() ? context : null; },
      get selectedProfileId() { return isDemo() ? null : selected; },
      get catalog() { return !isDemo() && catalog ? structuredClone(catalog) : null; },
      profile: profileId => !isDemo() && catalog?.profiles.find(profile => profile.id === profileId)
        ? contract.validateProfile(catalog.profiles.find(profile => profile.id === profileId)) : null,
    });
  };
})();
