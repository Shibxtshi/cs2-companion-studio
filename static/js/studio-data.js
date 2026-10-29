/* Transient preview data and demo controls; never passed to draft persistence. */
(() => {
  'use strict';
  window.CCSStudioData = ({renderer, board}) => {
    let state = null;
    let demo = false;
    let anchor = null;
    let timer = null;
    function refresh() { if (state) renderer.updateValues(state, {modeDemo: demo, anchor}); }
    function update(next, isDemo = false) {
      state = structuredClone(next); demo = isDemo;
      clearInterval(timer); timer = null;
      anchor = state.bomb_timer?.status === 'active' && Number.isFinite(state.bomb_timer.remaining)
        ? {at: performance.now(), left: state.bomb_timer.remaining} : null;
      refresh();
      if (anchor) timer = setInterval(() => { if (!document.hidden) renderer.paintBomb(state, anchor); }, 100);
    }
    function click(event) {
      const control = event.target.closest('[data-demo]');
      if (!demo || !state || !control) return;
      const value = control.dataset.demo;
      if (!['40', '9', '4', 'stop'].includes(value)) return;
      const next = structuredClone(state);
      next.bomb_state = value === 'stop' ? 'defused' : 'planted';
      next.bomb_timer = value === 'stop' ? {status: 'idle', enabled: true, duration: 40}
        : {status: 'active', enabled: true, remaining: Number(value), duration: 40};
      update(next, true);
    }
    board.addEventListener('click', click);
    return Object.freeze({update, refresh,
      snapshot: () => state ? {state: structuredClone(state), demo} : null,
      dispose() { clearInterval(timer); board.removeEventListener('click', click); state = null; },
    });
  };
})();
