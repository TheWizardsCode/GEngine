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

  function loadState() {
    if (typeof localStorage === 'undefined') return { events: [], totals: {} };
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return { events: [], totals: {} };
      const parsed = safeParse(raw);
      if (!parsed || typeof parsed !== 'object') return { events: [], totals: {} };
      const events = Array.isArray(parsed.events) ? parsed.events : [];
      const totals = parsed.totals && typeof parsed.totals === 'object' ? parsed.totals : {};
      return { events, totals };
    } catch (_) {
      return { events: [], totals: {} };
    }
  }

  function saveState(state) {
    if (typeof localStorage === 'undefined') return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
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
