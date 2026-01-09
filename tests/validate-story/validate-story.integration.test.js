const cp = require('child_process')
const path = require('path')
const fs = require('fs')
const os = require('os')

const CLI = path.resolve(__dirname, '../../scripts/validate-story.js')

function runCLI(args, env = {}){
  const res = cp.spawnSync(process.execPath, [CLI, ...args], { encoding: 'utf8', env: { ...process.env, ...env } })
  return res
}

describe('validate-story CLI integration', () => {
  const fixturesDir = path.resolve(__dirname, '../fixtures')
  const valid = path.join(fixturesDir, 'valid.ink')
  const invalid = path.join(fixturesDir, 'invalid.ink')
  const runtimeErr = path.join(fixturesDir, 'runtime_err.ink')

  test('parse failure returns non-zero and error field', () => {
    const r = runCLI(['--story', invalid, '--output', 'stdout'])
    expect(r.status).not.toBe(0)
    const out = r.stdout.trim()
    const parsed = JSON.parse(out)
    expect(parsed.error).toBeDefined()
    expect(parsed.pass).toBe(false)
  })

  test('successful run outputs pass true and steps > 0', () => {
    const r = runCLI(['--story', valid, '--seed', '42', '--output', 'stdout'])
    expect(r.status).toBe(0)
    const parsed = JSON.parse(r.stdout.trim())
    expect(parsed.pass).toBe(true)
    expect(parsed.steps).toBeGreaterThan(0)
  })

  test('deterministic seeded runs produce same path', () => {
    const r1 = runCLI(['--story', valid, '--seed', '123', '--output', 'stdout'])
    const r2 = runCLI(['--story', valid, '--seed', '123', '--output', 'stdout'])
    const p1 = JSON.parse(r1.stdout.trim())
    const p2 = JSON.parse(r2.stdout.trim())
    expect(p1.path).toEqual(p2.path)
  })

  test('state rotation avoids previous choice when alternatives exist', () => {
    const tmpState = path.join(os.tmpdir(), `validate-state-${Date.now()}.json`)
    // first run
    const r1 = runCLI(['--story', valid, '--seed', '7', '--state', tmpState, '--output', 'stdout'])
    expect(r1.status).toBe(0)
    const p1 = JSON.parse(r1.stdout.trim())
    // second run should avoid previous choice when alternative exists
    const r2 = runCLI(['--story', valid, '--seed', '7', '--state', tmpState, '--output', 'stdout'])
    const p2 = JSON.parse(r2.stdout.trim())
    // If the story has branching, the path arrays should not be identical
    // (test fixture should include a branching decision)
    expect(p1.path).not.toEqual(p2.path)
    fs.unlinkSync(tmpState)
  })

  test('multi-story glob runs produce aggregated output', () => {
    const r = runCLI(['--story', fixturesDir + '/*.ink', '--output', 'stdout'])
    expect(r.status).toBe(0)
    const parsed = JSON.parse(r.stdout.trim())
    // Expect an array of results
    expect(Array.isArray(parsed)).toBe(true)
    expect(parsed.length).toBeGreaterThanOrEqual(2)
  })
})
