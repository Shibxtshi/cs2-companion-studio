/* Strict configuration-only validation for the inactive draft foundation. */
(() => {
  'use strict';
  const schema = window.CCSDraftSchema;
  const encoder = new TextEncoder();
  const HEX_ID = /^[a-f0-9]{32}$/;
  const ACCESS_CONTEXTS = new WeakSet();
  const IDENTIFIER = /^[a-zA-Z0-9_-]{1,64}$/;

  class DraftError extends Error {
    constructor(code) {
      super(code);
      this.name = 'DraftError';
      this.code = code;
    }
  }
  const fail = code => { throw new DraftError(code); };
  function bounded(value, depth = 0, budget = {nodes: 0}) {
    if (depth > schema.limits.depth || ++budget.nodes > schema.limits.nodes) fail('invalid_document');
    if (typeof value === 'string') {
      if (value.length > schema.limits.draftBytes) fail('size_limit');
      if (Array.from(value).some(char => {
        const code = char.codePointAt(0);
        return code >= 0xD800 && code <= 0xDFFF;
      })) fail('invalid_document');
    } else if (typeof value === 'number') {
      if (!Number.isFinite(value)) fail('invalid_document');
    } else if (Array.isArray(value)) {
      for (let index = 0; index < value.length; index++) bounded(value[index], depth + 1, budget);
    } else if (value && typeof value === 'object') {
      if (![Object.prototype, null].includes(Object.getPrototypeOf(value))) fail('invalid_document');
      for (const descriptor of Object.values(Object.getOwnPropertyDescriptors(value))) {
        if (!Object.hasOwn(descriptor, 'value')) fail('invalid_document');
        bounded(descriptor.value, depth + 1, budget);
      }
    } else if (value !== null && typeof value !== 'boolean') fail('invalid_document');
  }
  function canonical(value) {
    if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
    if (value && typeof value === 'object') {
      return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
    }
    return JSON.stringify(value);
  }
  function matches(value, rule, root) {
    if (rule.$ref) return matches(value, root.$defs[rule.$ref.split('/').pop()], root);
    if (rule.const !== undefined && value !== rule.const) return false;
    if (rule.enum && !rule.enum.includes(value)) return false;
    if (rule.type === 'object') {
      if (!value || Array.isArray(value) || typeof value !== 'object') return false;
      if ((rule.required || []).some(key => !Object.hasOwn(value, key))) return false;
      if (rule.additionalProperties === false && Object.keys(value).some(key => !Object.hasOwn(rule.properties, key))) return false;
      return Object.entries(value).every(([key, item]) => !rule.properties[key] || matches(item, rule.properties[key], root));
    }
    if (rule.type === 'array') {
      return Array.isArray(value) && value.length >= (rule.minItems || 0)
        && (rule.maxItems === undefined || value.length <= rule.maxItems)
        && value.every(item => matches(item, rule.items, root));
    }
    if (rule.type === 'integer') {
      return Number.isSafeInteger(value) && (rule.minimum === undefined || value >= rule.minimum)
        && (rule.maximum === undefined || value <= rule.maximum)
        && (rule.exclusiveMaximum === undefined || value < rule.exclusiveMaximum)
        && (rule.multipleOf === undefined || value % rule.multipleOf === 0);
    }
    if (rule.type === 'string') {
      if (typeof value !== 'string') return false;
      const length = Array.from(value).length;
      return length >= (rule.minLength || 0) && (rule.maxLength === undefined || length <= rule.maxLength)
        && (!rule.pattern || new RegExp(rule.pattern).exec(value)?.[0] === value);
    }
    if (rule.type === 'boolean') return typeof value === 'boolean';
    return false;
  }
  function printable(value) {
    return value === value.trim() && Array.from(value).every(char => char === ' ' || !/[\p{C}\p{Z}]/u.test(char));
  }
  function validate(value, kind) {
    bounded(value);
    const rule = schema[kind];
    if (!rule || !matches(value, rule, rule)) fail('invalid_document');
    const layout = value.configuration.layout;
    const ids = new Set();
    if (!printable(value.name)) fail('invalid_document');
    for (const widget of layout.widgets) {
      if (ids.has(widget.id) || widget.x + widget.width > layout.columns
          || widget.y + widget.height > schema.limits.rows || !printable(widget.title)) fail('invalid_document');
      ids.add(widget.id);
    }
    const bytes = encoder.encode(canonical(value)).length;
    if (bytes > (kind === 'draft' ? schema.limits.draftBytes : schema.limits.profileBytes)) fail('size_limit');
    if (encoder.encode(canonical({name: value.name, configuration: value.configuration})).length > schema.limits.profileBytes) fail('size_limit');
    return JSON.parse(canonical(value));
  }
  function content(value) {
    bounded(value);
    const checked = validate({id: 'content-check', revision: 1, ...value}, 'profile');
    if (Object.keys(value).some(key => !['name', 'configuration'].includes(key))) fail('invalid_document');
    return {name: checked.name, configuration: checked.configuration};
  }
  function access(value) {
    if (!value || value.authenticated !== true || typeof value.storeId !== 'string' || typeof value.accessId !== 'string'
        || value.storeId.length !== 32 || value.accessId.length !== 32
        || !HEX_ID.test(value.storeId) || !HEX_ID.test(value.accessId)
        || Object.keys(value).some(key => !['authenticated', 'storeId', 'accessId'].includes(key))) fail('access_required');
    const context = Object.freeze({storeId: value.storeId, accessId: value.accessId});
    ACCESS_CONTEXTS.add(context);
    return context;
  }
  function contextKey(context) {
    if (!context || !ACCESS_CONTEXTS.has(context) || typeof context.storeId !== 'string' || typeof context.accessId !== 'string'
        || context.storeId.length !== 32 || context.accessId.length !== 32
        || !HEX_ID.test(context.storeId) || !HEX_ID.test(context.accessId)) fail('access_required');
    return JSON.stringify([context.storeId, context.accessId]);
  }
  function profileId(value) {
    if (typeof value !== 'string' || IDENTIFIER.exec(value)?.[0] !== value) fail('invalid_profile_id');
    return value;
  }
  function uuid() {
    const bytes = crypto.getRandomValues(new Uint8Array(16));
    bytes[6] = (bytes[6] & 15) | 64;
    bytes[8] = (bytes[8] & 63) | 128;
    return Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
  }
  window.CCSDraftContract = Object.freeze({DraftError, fail, canonical, bounded, content, access, contextKey,
    profileId, uuid, validateDraft: value => validate(value, 'draft'), validateProfile: value => validate(value, 'profile')});
})();
