const path = require('path');
const { runReplay } = require('../../scripts/replay');

describe('replay harness', () => {
  const storyPath = path.join(__dirname, '..', '..', 'web', 'stories', 'demo.ink');
  const scriptPath = path.join(__dirname, '..', '..', 'web', 'stories', 'golden.demo.json');

  test('runs demo.ink to completion using golden path', () => {
    const result = runReplay({ storyPath, scriptPath, maxSteps: 2000 });
    expect(result.pass).toBe(true);
    expect(result.error).toBeUndefined();
    expect(Array.isArray(result.path)).toBe(true);
    expect(result.path.length).toBeGreaterThan(0);
  });
});
