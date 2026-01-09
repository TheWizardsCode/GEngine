const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');

const CLI_PATH = path.join(__dirname, '../../scripts/validate-story.js');

const fixturesDir = path.join(__dirname, '../fixtures');
const validInk = `Hello world\n* [Choice A]\n  Hello again\n`; // simple story
const invalidInk = `=== bad`; // invalid ink

const fixturePaths = {
  valid: path.join(fixturesDir, 'valid.ink'),
  invalid: path.join(fixturesDir, 'invalid.ink'),
};

function runCli(args = []) {
  return execFileSync('node', [CLI_PATH, ...args], {
    encoding: 'utf8',
    env: { ...process.env, NODE_OPTIONS: '--no-warnings' },
  });
}

describe('validate-story CLI', () => {
  beforeAll(() => {
    if (!fs.existsSync(fixturesDir)) fs.mkdirSync(fixturesDir);
    fs.writeFileSync(fixturePaths.valid, validInk, 'utf8');
    fs.writeFileSync(fixturePaths.invalid, invalidInk, 'utf8');
  });

  afterAll(() => {
    Object.values(fixturePaths).forEach((p) => {
      if (fs.existsSync(p)) fs.unlinkSync(p);
    });
    // keep fixturesDir for smoke usage outside tests
  });

  it('fails on parse error', () => {
    let error = null;
    try {
      runCli(['--story', fixturePaths.invalid]);
    } catch (err) {
      error = err;
    }
    expect(error).toBeTruthy();
    expect(error.status).toBe(1);
    expect(error.stdout).toContain('"pass": false');
    expect(error.stdout).toContain('Parse/compile error');
  });

  it('runs a simple story successfully', () => {
    const output = runCli(['--story', fixturePaths.valid]);
    const parsed = JSON.parse(output);
    expect(parsed).toHaveLength(1);
    const result = parsed[0];
    expect(result.pass).toBe(true);
    expect(result.steps).toBeGreaterThan(0);
  });

  it('produces deterministic paths with seed', () => {
    const first = JSON.parse(runCli(['--story', fixturePaths.valid, '--seed', '42']));
    const second = JSON.parse(runCli(['--story', fixturePaths.valid, '--seed', '42']));

    expect(first[0].path).toEqual(second[0].path);
  });
});
