const PlayerPreference = require('../../web/demo/js/player-preference');

function clearStorage() {
  if (typeof localStorage !== 'undefined') {
    localStorage.clear();
  }
}

describe('PlayerPreference', () => {
  beforeEach(() => {
    clearStorage();
  });

  test('cold start returns default 0.5', () => {
    expect(PlayerPreference.getPreference('combat')).toBe(0.5);
  });

  test('records outcomes and updates preference', () => {
    const p1 = PlayerPreference.recordOutcome('lore', true);
    const p2 = PlayerPreference.recordOutcome('lore', false);
    expect(p1).toBeCloseTo(1.0);
    expect(p2).toBeCloseTo(0.5);
    expect(PlayerPreference.getPreference('lore')).toBeCloseTo(0.5);
  });

  test('persists across calls via localStorage', () => {
    PlayerPreference.recordOutcome('puzzle', true);
    // Re-require to simulate reload
    jest.resetModules();
    const Reloaded = require('../../web/demo/js/player-preference');
    expect(Reloaded.getPreference('puzzle')).toBeCloseTo(1.0);
  });

  test('clamps to 0-1 and handles bad inputs', () => {
    expect(PlayerPreference.getPreference('')).toBe(0.5);
    expect(PlayerPreference.recordOutcome('', true)).toBe(0.5);
    // Corrupt storage
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('ge-hch.ai-preferences', '{ not valid json');
    }
    expect(PlayerPreference.getPreference('combat')).toBe(0.5);
  });
});
