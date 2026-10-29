/* Same-origin preview window. No framing exception, transport or persistence. */
(() => {
  'use strict';
  window.CCSStudioPreview = () => {
    let payload = null;
    let child = null;
    function receive(event) {
      if (event.origin !== location.origin || event.source !== child
          || event.data?.type !== 'studio_preview_ready' || !payload) return;
      child.postMessage(payload, location.origin);
    }
    window.addEventListener('message', receive);
    return Object.freeze({
      open(content, data) {
        if (!content) CCSDraftContract.fail('draft_required');
        payload = {type: 'studio_preview', content: CCSDraftContract.content(content),
          state: data ? structuredClone(data.state) : null, demo: data?.demo === true, locale: CS2I18N.locale()};
        child?.close();
        child = window.open('/__studio_preview__', '_blank');
        if (!child) { payload = null; CCSDraftContract.fail('preview_blocked'); }
      },
      dispose() { payload = null; child?.close(); window.removeEventListener('message', receive); },
    });
  };
})();
