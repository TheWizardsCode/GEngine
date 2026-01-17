const path = require('path');

describe('Director core', () => {
  let Director;

  beforeEach(() => {
    jest.resetModules();

    // Provide minimal browser/globals the module expects when running in Node
    global.window = global.window || {};
    global.window.Telemetry = { emit: jest.fn() };

    // Default ProposalValidator that approves
    global.window.ProposalValidator = {
      quickValidate: jest.fn(() => ({ valid: true }))
    };

    jest.isolateModules(() => {
      Director = require(path.join(process.cwd(), 'web/demo/js/director.js'));
    });
  });

  afterEach(() => {
    // clean up any globals we set
    delete global.window.__proposalValidReturnPaths;
  });

  it('approves a low-risk proposal and returns latencyMs', async () => {
    const story = {
      mainContentContainer: { _namedContent: { campfire: {} } }
    };

    const proposal = {
      content: { text: 'Short content', return_path: 'campfire' },
      metadata: { confidence_score: 0.9 }
    };

    const res = await Director.evaluate(proposal, { story }, { riskThreshold: 0.5 });

    expect(res).toHaveProperty('decision', 'approve');
    expect(typeof res.riskScore).toBe('number');
    expect(res.riskScore).toBeLessThanOrEqual(0.5);
    expect(typeof res.latencyMs).toBe('number');
    expect(res.latencyMs).toBeGreaterThanOrEqual(0);
  });

  it('rejects when ProposalValidator fails', async () => {
    // make the validator fail
    global.window.ProposalValidator.quickValidate.mockReturnValueOnce({ valid: false, reason: 'Blocked by policy' });

    const proposal = { content: { text: 'x' }, metadata: { confidence_score: 0.5 } };

    const res = await Director.evaluate(proposal, {}, { riskThreshold: 0.5 });

    expect(res).toHaveProperty('decision', 'reject');
    expect(res).toHaveProperty('reason');
    expect(res.reason).toMatch(/Blocked|policy|Failed/i);
    expect(res.riskScore).toBe(1.0);
  });

  it('throws on malformed proposal (non-object)', async () => {
    await expect(Director.evaluate(null)).rejects.toThrow('Malformed proposal');
  });

  it('checkReturnPath recognizes named knots on story', () => {
    const story = { mainContentContainer: { _namedContent: { campfire: {}, elsewhere: {} } } };

    const ok = Director.checkReturnPath('campfire', story);
    expect(ok.feasible).toBe(true);
    expect(ok.confidence).toBeGreaterThan(0);

    const bad = Director.checkReturnPath('missing_knot', story);
    expect(bad.feasible).toBe(false);
  });

  it('checkReturnPath falls back to __proposalValidReturnPaths', () => {
    // no story shape
    global.window.__proposalValidReturnPaths = ['alpha', 'beta'];

    const ok = Director.checkReturnPath('alpha', null);
    expect(ok.feasible).toBe(true);

    const bad = Director.checkReturnPath('gamma', null);
    expect(bad.feasible).toBe(false);
  });

  it('computeRiskScore is deterministic and sensitive to confidence', () => {
    const pHigh = { metadata: { confidence_score: 0.95 }, content: { text: 'short' } };
    const pLow = { metadata: { confidence_score: 0.2 }, content: { text: 'short' } };

    const s1 = Director.computeRiskScore(pHigh, { returnPathCheck: { confidence: 0.9 } }, {});
    const s2 = Director.computeRiskScore(pHigh, { returnPathCheck: { confidence: 0.9 } }, {});
    const sLow = Director.computeRiskScore(pLow, { returnPathCheck: { confidence: 0.9 } }, {});

    expect(s1).toBeCloseTo(s2);
    expect(sLow).toBeGreaterThanOrEqual(s1);
  });

  it('evaluate respects a very low threshold and rejects accordingly', async () => {
    const story = { mainContentContainer: { _namedContent: { campfire: {} } } };
    const proposal = { content: { text: 'This is somewhat long content '.repeat(40), return_path: 'campfire' }, metadata: { confidence_score: 0.5 } };

    // Set threshold extremely low so even modest risk should reject
    const res = await Director.evaluate(proposal, { story }, { riskThreshold: 0.01 });
    expect(res.decision).toBe('reject');
    expect(res.riskScore).toBeGreaterThan(0.01);
  });
});
