/* Session-only bounded snapshots; gestures commit one coherent edit. */
(() => {
  'use strict';
  const contract = window.CCSDraftContract;
  const MAX_ENTRIES = 50;
  const MAX_BYTES = 2 * 1024 * 1024;
  const encoder = new TextEncoder();

  class EditHistory {
    #current;
    #past = [];
    #future = [];
    #gesture = null;
    #bytes = 0;

    constructor(initial) { this.reset(initial); }
    #snapshot(value) {
      const text = contract.canonical(contract.content(value));
      return {text, bytes: encoder.encode(text).length};
    }
    reset(initial) {
      const snapshot = this.#snapshot(initial);
      this.#current = snapshot;
      this.#past = [];
      this.#future = [];
      this.#gesture = null;
      this.#bytes = 0;
    }
    get value() { return JSON.parse(this.#current.text); }
    get activeGesture() { return this.#gesture !== null; }
    get canUndo() { return !this.activeGesture && this.#past.length > 0; }
    get canRedo() { return !this.activeGesture && this.#future.length > 0; }
    get stats() {
      return {entries: this.#past.length + this.#future.length, bytes: this.#bytes,
        maxEntries: MAX_ENTRIES, maxBytes: MAX_BYTES};
    }
    #trim() {
      while (this.stats.entries > MAX_ENTRIES || this.#bytes > MAX_BYTES) {
        const removed = this.#past.length ? this.#past.shift() : this.#future.shift();
        this.#bytes -= removed.bytes;
      }
    }
    #branch(previous) {
      this.#bytes -= this.#future.reduce((sum, entry) => sum + entry.bytes, 0);
      this.#future = [];
      this.#past.push(previous);
      this.#bytes += previous.bytes;
      this.#trim();
    }
    commit(next) {
      if (this.activeGesture) contract.fail('gesture_active');
      const snapshot = this.#snapshot(next);
      if (snapshot.text === this.#current.text) return false;
      const previous = this.#current;
      this.#current = snapshot;
      this.#branch(previous);
      return true;
    }
    beginGesture() {
      if (this.activeGesture) contract.fail('gesture_active');
      this.#gesture = this.#current;
    }
    preview(next) {
      if (!this.activeGesture) contract.fail('gesture_required');
      this.#current = this.#snapshot(next);
    }
    endGesture() {
      if (!this.activeGesture) contract.fail('gesture_required');
      const initial = this.#gesture;
      this.#gesture = null;
      if (initial.text === this.#current.text) return false;
      this.#branch(initial);
      return true;
    }
    cancelGesture() {
      if (!this.activeGesture) contract.fail('gesture_required');
      this.#current = this.#gesture;
      this.#gesture = null;
    }
    #travel(source, destination) {
      const next = source.pop();
      destination.push(this.#current);
      this.#bytes += this.#current.bytes - next.bytes;
      this.#current = next;
      this.#trim();
      return true;
    }
    undo() { return this.canUndo ? this.#travel(this.#past, this.#future) : false; }
    redo() { return this.canRedo ? this.#travel(this.#future, this.#past) : false; }
  }
  window.CCSEditHistory = EditHistory;
})();
