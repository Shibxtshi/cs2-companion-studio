/* Authenticated read-only import validation; mutation remains a P4 draft / P5 publication. */
(() => {
  'use strict';
  const MAX_EXPORT_BYTES = 70000;
  window.CCSProfileTransfer = ({send}) => {
    const pending = new Map();
    async function validateFile(file) {
      if (!file || file.size > MAX_EXPORT_BYTES) CCSDraftContract.fail('size_limit');
      const raw = await file.text();
      if (new TextEncoder().encode(raw).length > MAX_EXPORT_BYTES) CCSDraftContract.fail('size_limit');
      const requestId = CCSDraftContract.uuid();
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => { pending.delete(requestId); reject({code: 'network_error'}); }, 10000);
        pending.set(requestId, {resolve, reject, timer});
        try { send({type: 'profile_import_validate', requestId, document: raw}); }
        catch { clearTimeout(timer); pending.delete(requestId); reject({code: 'network_error'}); }
      });
    }
    function receive(message) {
      if (!['profile_import_validated', 'profile_import_error'].includes(message.type)) return false;
      const request = pending.get(message.requestId);
      if (!request) return true;
      clearTimeout(request.timer); pending.delete(message.requestId);
      if (message.type === 'profile_import_error') request.reject({code: message.code || 'invalid_document'});
      else {
        try { request.resolve(CCSDraftContract.content(message.content)); }
        catch (error) { request.reject(error); }
      }
      return true;
    }
    function exportProfile(profile) {
      if (!profile) CCSDraftContract.fail('profile_missing');
      const content = CCSDraftContract.content({name: profile.name, configuration: profile.configuration});
      const raw = CCSDraftContract.canonical({format: 'ccs-dashboard-export', version: 1, ...content});
      if (new TextEncoder().encode(raw).length > MAX_EXPORT_BYTES) CCSDraftContract.fail('size_limit');
      let url;
      try {
        url = URL.createObjectURL(new Blob([raw], {type: 'application/json'}));
        const link = document.createElement('a');
        link.href = url;
        link.download = 'CCS_' + content.name.replace(/[^a-z0-9_-]+/gi, '_') + '.json';
        link.click();
        CCSNotifications.show({key: 'exportPrepared', kind: 'info'});
      } catch { CCSNotifications.show({key: 'exportFailed', kind: 'error'}); }
      finally { if (url) setTimeout(() => URL.revokeObjectURL(url), 1000); }
    }
    function cancel() {
      for (const request of pending.values()) { clearTimeout(request.timer); request.reject({code: 'network_error'}); }
      pending.clear();
    }
    return Object.freeze({validateFile, receive, exportProfile, cancel});
  };
})();
