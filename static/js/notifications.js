/* One bounded notification surface; errors wait for acknowledgement or resolution. */
(() => {
  'use strict';
  const KINDS = ['info', 'success', 'warning', 'error', 'loading', 'pending'];
  let timer = null;
  let current = null;
  function dismiss() {
    clearTimeout(timer);
    current = null;
    document.getElementById('toast')?.classList.add('hidden');
  }
  function paint() {
    const host = document.getElementById('toast');
    if (!host || !current) return;
    host.replaceChildren();
    host.setAttribute('translate', 'no');
    host.setAttribute('role', current.kind === 'error' ? 'alert' : 'status');
    host.dataset.kind = current.kind;
    const message = document.createElement('span');
    const kind = CCSExperienceCopy.text('notification_' + current.kind);
    message.textContent = kind + ' · ' + (current.key ? CCSExperienceCopy.text(current.key) : CS2I18N.translate(current.message));
    const close = document.createElement('button');
    close.type = 'button'; close.className = 'btn small ghost';
    close.textContent = '×'; close.setAttribute('aria-label', CCSExperienceCopy.text('dismiss'));
    close.addEventListener('click', dismiss);
    host.append(message, close);
    host.classList.remove('hidden');
  }
  window.CCSNotifications = Object.freeze({
    show({message = '', key = null, kind = 'info'}) {
      if (!KINDS.includes(kind)) kind = 'error';
      // An unrelated success cannot silently erase an unresolved error.
      if (current && ['error', 'warning'].includes(current.kind) && !['error', 'warning'].includes(kind)) return;
      clearTimeout(timer);
      current = {message, key, kind}; paint();
      if (['info', 'success'].includes(kind)) timer = setTimeout(dismiss, 5000);
    },
    dismiss,
  });
  document.addEventListener('cs2:locale-changed', paint);
  document.addEventListener('cs2:logout', dismiss);
  window.addEventListener('pagehide', () => clearTimeout(timer));
})();
