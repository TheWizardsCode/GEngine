(function () {
  "use strict";

  const STORAGE_KEY = 'ge-hch.ai-preferences';
  const DEFAULT_SCORE = 0.5;

  function safeParse(json) {
    try {
      return JSON.parse(json);
    } catch (_) {
      return null;
    }
  }

  // In-memory cache to avoid repeated JSON.parse on hot paths.
  // We still detect external changes to localStorage by comparing the raw string.
  let _cachedRaw = null;
  let _cachedState = null;

  function loadState() {
    if (typeof localStorage === 'undefined') return { events: [], totals: {} };
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      // If nothing stored, normalize to null for comparison
      const normRaw = raw || null;
      if (_cachedRaw === normRaw && _cachedState) return _cachedState;
      if (!raw) {
        _cachedRaw = null;
        _cachedState = { events: [], totals: {} };
        return _cachedState;
      }
      const parsed = safeParse(raw);
      if (!parsed || typeof parsed !== 'object') {
        _cachedRaw = null;
        _cachedState = { events: [], totals: {} };
        return _cachedState;
      }
      const events = Array.isArray(parsed.events) ? parsed.events : [];
      const totals = parsed.totals && typeof parsed.totals === 'object' ? parsed.totals : {};
      _cachedRaw = normRaw;
      _cachedState = { events, totals };
      return _cachedState;
    } catch (_) {
      _cachedRaw = null;
      _cachedState = { events: [], totals: {} };
      return _cachedState;
    }
  }

  function saveState(state) {
    if (typeof localStorage === 'undefined') return;
    try {
      const raw = JSON.stringify(state);
      localStorage.setItem(STORAGE_KEY, raw);
      _cachedRaw = raw || null;
      _cachedState = state;
    } catch (_) {
      // ignore write errors
    }
  }

  function clamp01(value) {
    if (!Number.isFinite(value)) return DEFAULT_SCORE;
    if (value < 0) return 0;
    if (value > 1) return 1;
    return value;
  }

  const PlayerPreference = {
    getPreference(branchType) {
      if (!branchType) return DEFAULT_SCORE;
      const { totals } = loadState();
      const entry = totals[branchType];
      if (!entry || !entry.total) return DEFAULT_SCORE;
      return clamp01(entry.accepted / entry.total);
    },

    recordOutcome(branchType, accepted) {
      if (!branchType || typeof branchType !== 'string') return DEFAULT_SCORE;
      const outcome = Boolean(accepted);
      const state = loadState();
      const now = new Date().toISOString();
      state.events.push({ branchType, accepted: outcome, timestamp: now });
      const current = state.totals[branchType] || { accepted: 0, total: 0 };
      const nextTotals = {
        accepted: current.accepted + (outcome ? 1 : 0),
        total: current.total + 1,
      };
      state.totals[branchType] = nextTotals;
      saveState(state);
      return clamp01(nextTotals.accepted / nextTotals.total);
    },

    _debugLoad() {
      // For tests only.
      return loadState();
    },
  };

  if (typeof window !== 'undefined') {
    window.PlayerPreference = PlayerPreference;
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = PlayerPreference;
  }
})();
