/* HTTP/WebSocket transport. UI text, profile synchronization and retry policy are callers. */
(() => {
  'use strict';

  window.CS2DashboardClient = ({
    version, getPin, isDemo, onConnecting, onHealthError,
    onMessage, onNetworkError, onClose
  }) => {
    let socket = null;

    async function checkHealth(isCurrent) {
      const response = await fetch('/health', {
        cache: 'no-store', signal: AbortSignal.timeout(5000)
      });
      if (!response.ok) throw Error('HTTP ' + response.status);
      const health = await response.json();
      if (!isCurrent()) return false;
      if (health.version !== version) {
        onHealthError(Error('version'), true);
        throw Error('version');
      }
      return true;
    }

    async function connect(isCurrent) {
      if (!isCurrent()) return;
      onConnecting();
      try {
        if (!await checkHealth(isCurrent)) return;
      } catch (error) {
        if (!isCurrent()) return;
        if (error.message !== 'version') onHealthError(error, false);
        throw error;
      }
      if (!isCurrent()) return;

      const url = (location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + location.host + '/ws';
      const currentSocket = new WebSocket(url);
      socket = currentSocket;
      let authorized = false;
      let failed = false;

      currentSocket.onopen = () => {
        if (isCurrent() && socket === currentSocket) {
          currentSocket.send(JSON.stringify({type: 'auth', pin: getPin()}));
        }
      };
      currentSocket.onmessage = event => {
        if (isDemo() || socket !== currentSocket || !isCurrent()) return;
        let message;
        try {
          message = JSON.parse(event.data);
        } catch {
          return;
        }
        if (message.type === 'auth_error') {
          failed = true;
          onMessage(message);
          return;
        }
        if (message.type === 'auth_ok') {
          authorized = true;
          onMessage(message);
          return;
        }
        if (authorized) onMessage(message);
      };
      currentSocket.onerror = () => {
        if (socket !== currentSocket || !isCurrent()) return;
        onNetworkError({failed});
      };
      currentSocket.onclose = () => {
        if (isDemo() || socket !== currentSocket) return;
        onClose({authorized, failed});
      };
    }

    function close() {
      if (!socket) return;
      socket.onclose = null;
      socket.close();
      socket = null;
    }

    return {
      connect,
      close,
      send: command => socket.send(JSON.stringify(command)),
      get isOpen() { return socket?.readyState === WebSocket.OPEN; }
    };
  };
})();
