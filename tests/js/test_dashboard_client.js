/* Transport behavior independent of DOM, profiles and real credentials. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function harness() {
  const sockets = [];
  const events = [];
  let health = async () => ({ok: true, json: async () => ({version: '1.0.0'})});
  let demo = false;
  class Socket {
    static OPEN = 1;
    constructor(url) {
      this.url = url;
      this.readyState = 0;
      this.sent = [];
      sockets.push(this);
    }
    send(raw) { this.sent.push(JSON.parse(raw)); }
    close() { this.readyState = 3; this.onclose?.(); }
    open() { this.readyState = 1; this.onopen(); }
    message(message) { this.onmessage({data: JSON.stringify(message)}); }
  }
  const context = vm.createContext({
    window: {}, WebSocket: Socket, location: {protocol: 'http:', host: 'fixture.local:8080'},
    AbortSignal: {timeout: value => ({timeout: value})},
    fetch: (...args) => health(...args)
  });
  vm.runInContext(fs.readFileSync('static/js/dashboard-client.js', 'utf8'), context);
  const client = context.window.CS2DashboardClient({
    version: '1.0.0', getPin: () => 'synthetic-client-pin', isDemo: () => demo,
    onConnecting: () => events.push(['connecting']),
    onHealthError: (error, mismatch) => events.push(['health', error.message, mismatch]),
    onMessage: message => events.push(['message', message.type]),
    onNetworkError: state => events.push(['network', state.failed]),
    onClose: state => events.push(['close', state.authorized, state.failed])
  });
  return {client, sockets, events, setHealth: value => {health = value;}, setDemo: value => {demo = value;}};
}

async function run() {
  {
    const h = harness();
    await h.client.connect(() => true);
    const socket = h.sockets[0];
    assert.equal(socket.url, 'ws://fixture.local:8080/ws');
    assert.equal(h.client.isOpen, false);
    socket.open();
    assert.equal(h.client.isOpen, true);
    assert.deepEqual(socket.sent, [{type: 'auth', pin: 'synthetic-client-pin'}]);
    socket.message({type: 'state'});
    socket.onmessage({data: 'invalid json'});
    assert.equal(h.events.filter(event => event[0] === 'message').length, 0);
    socket.message({type: 'auth_ok'});
    socket.message({type: 'profiles_state'});
    socket.message({type: 'diagnostics_data'});
    socket.message({type: 'state'});
    assert.deepEqual(h.events.filter(event => event[0] === 'message').map(event => event[1]),
      ['auth_ok', 'profiles_state', 'diagnostics_data', 'state']);
    h.client.send({type: 'diagnostics_request'});
    assert.deepEqual(socket.sent.at(-1), {type: 'diagnostics_request'});
    socket.onerror();
    socket.close();
    assert.deepEqual(h.events.slice(-2), [['network', false], ['close', true, false]]);
  }
  {
    const h = harness();
    h.setHealth(async () => ({ok: false, status: 503}));
    await assert.rejects(h.client.connect(() => true), /HTTP 503/);
    assert.deepEqual(h.events, [['connecting'], ['health', 'HTTP 503', false]]);
    assert.equal(h.sockets.length, 0);
  }
  {
    const h = harness();
    h.setHealth(async () => ({ok: true, json: async () => ({version: 'different'})}));
    await assert.rejects(h.client.connect(() => true), /version/);
    assert.deepEqual(h.events, [['connecting'], ['health', 'version', true]]);
    assert.equal(h.sockets.length, 0);
  }
  {
    const h = harness();
    let release;
    let current = true;
    h.setHealth(() => new Promise(resolve => {release = resolve;}));
    const attempt = h.client.connect(() => current);
    current = false;
    release({ok: false, status: 503});
    await attempt;
    assert.deepEqual(h.events, [['connecting']]);
    assert.equal(h.sockets.length, 0);
  }
  {
    const h = harness();
    await h.client.connect(() => true);
    const previous = h.sockets[0];
    await h.client.connect(() => true);
    previous.message({type: 'auth_ok'});
    previous.onerror();
    previous.close();
    assert.equal(h.events.filter(event => ['message', 'network', 'close'].includes(event[0])).length, 0);
    const current = h.sockets[1];
    current.open();
    current.message({type: 'auth_error'});
    current.close();
    assert.deepEqual(h.events.slice(-2), [['message', 'auth_error'], ['close', false, true]]);
  }
  {
    const h = harness();
    await h.client.connect(() => true);
    const socket = h.sockets[0];
    h.setDemo(true);
    socket.message({type: 'auth_ok'});
    socket.close();
    assert.deepEqual(h.events, [['connecting']]);
    h.client.close();
    assert.equal(h.client.isOpen, false);
  }
  {
    const h = harness();
    await h.client.connect(() => true);
    h.client.close();
    assert.deepEqual(h.events, [['connecting']]);
    assert.equal(h.client.isOpen, false);
  }
  console.log('OK: auth gating, JSON transport, health/version errors, stale attempts, demo and intentional close');
}
run().catch(error => {console.error(error); process.exitCode = 1;});
