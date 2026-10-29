/* Non-secret profile preference: per-tab selection plus a last-used new-tab hint. */
(() => {
  'use strict';
  const key = context => 'ccs-profile-selection:' + context.storeId + ':' + context.accessId;
  window.CCSProfileSelection = Object.freeze({
    read(context) {
      try { return sessionStorage.getItem(key(context)) || localStorage.getItem(key(context)); }
      catch { return null; }
    },
    remember(context, profileId) {
      CCSDraftContract.profileId(profileId);
      try {
        sessionStorage.setItem(key(context), profileId);
        localStorage.setItem(key(context), profileId);
      } catch {}
    },
  });
})();
