const path = require('path')
const cp = require('child_process')

const CLI = path.resolve(__dirname, '../../scripts/validate-story.js')
const demoStory = path.resolve(__dirname, '../../web/stories/demo.ink')

function runCLI(args){
  return cp.spawnSync(process.execPath, [CLI, ...args], { encoding: 'utf8' })
}

describe('validate-story demo story', () => {
  test('demo story passes validation', () => {
    const result = runCLI(['--story', demoStory, '--output', 'stdout'])
    expect(result.status).toBe(0)
    let parsed = JSON.parse(result.stdout.trim())
    if (Array.isArray(parsed) && parsed.length === 1) parsed = parsed[0]
    expect(parsed.pass).toBe(true)
    expect(parsed.steps).toBeGreaterThan(0)
  })
})
