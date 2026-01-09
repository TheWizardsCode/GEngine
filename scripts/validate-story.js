#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const fg = require('fast-glob');
const inkjs = require('inkjs/full');

const { Story, Compiler } = inkjs;

const DEFAULT_GLOB = 'web/stories/**/*.ink';
const DEFAULT_MAX_STEPS = 1000;

function parseArgs(argv) {
  const args = {
    story: DEFAULT_GLOB,
    seed: null,
    maxSteps: DEFAULT_MAX_STEPS,
    output: 'json',
    statePath: null,
    clearState: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    switch (arg) {
      case '--story':
        args.story = argv[++i];
        break;
      case '--seed':
        args.seed = parseInt(argv[++i], 10);
        if (Number.isNaN(args.seed)) args.seed = null;
        break;
      case '--max-steps':
        args.maxSteps = parseInt(argv[++i], 10) || DEFAULT_MAX_STEPS;
        break;
      case '--output':
        args.output = argv[++i] || 'json';
        break;
      case '--state':
        args.statePath = argv[++i];
        break;
      case '--clear-state':
        args.clearState = true;
        break;
      default:
        break;
    }
  }

  return args;
}

function resolveStories(pattern) {
  const resolvedPath = path.resolve(pattern);
  if (fs.existsSync(resolvedPath)) {
    const stats = fs.statSync(resolvedPath);
    if (stats.isFile()) return [resolvedPath];
    if (stats.isDirectory()) {
      return fg.sync(path.join(resolvedPath, '**/*.ink'), { absolute: true });
    }
  }
  return fg.sync(pattern, { absolute: true });
}

function mulberry32(seed) {
  return function rng() {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function chooseIndex(choices, rng) {
  if (!choices.length) return null;
  if (!rng) return 0;
  const idx = Math.floor(rng() * choices.length);
  return idx;
}

function loadState(story, statePath, clearState) {
  if (!statePath) return;
  if (clearState) return;
  if (!fs.existsSync(statePath)) return;
  const data = fs.readFileSync(statePath, 'utf8');
  try {
    story.state.LoadJson(data);
  } catch (err) {
    throw new Error(`Failed to load state from ${statePath}: ${err.message}`);
  }
}

function saveState(story, statePath) {
  if (!statePath) return;
  try {
    fs.writeFileSync(statePath, story.state.toJson(), 'utf8');
  } catch (err) {
    // ignore state save errors
  }
}

function runStory(filePath, opts) {
  let compiled;
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    if (!Compiler) throw new Error('InkJS Compiler missing');
    compiled = new Compiler(content).Compile();
  } catch (err) {
    return {
      story: filePath,
      pass: false,
      steps: 0,
      path: [],
      error: `Parse/compile error: ${err.message}`,
    };
  }

  const story = new Story(compiled.ToJson());
  const rng = opts.seed != null ? mulberry32(opts.seed) : null;
  loadState(story, opts.statePath, opts.clearState);

  const choicePath = [];
  let steps = 0;
  let error = null;

  try {
    while (story.canContinue && steps < opts.maxSteps) {
      story.Continue();
      steps += 1;
    }

    while (story.currentChoices.length && steps < opts.maxSteps) {
      const idx = chooseIndex(story.currentChoices, rng);
      if (idx == null) break;
      choicePath.push(idx);
      story.ChooseChoiceIndex(idx);
      steps += 1;
      while (story.canContinue && steps < opts.maxSteps) {
        story.Continue();
        steps += 1;
      }
    }
  } catch (err) {
    error = `Runtime error: ${err.message}`;
  }

  if (error) {
    return { story: filePath, pass: false, steps, path: choicePath, error };
  }

  const pass = !story.currentChoices.length && !story.canContinue && steps <= opts.maxSteps;
  saveState(story, opts.statePath);

  return { story: filePath, pass, steps, path: choicePath };
}

function outputResults(results, output) {
  const json = JSON.stringify(results, null, 2);
  if (output === 'stdout' || output === 'json' || !output) {
    console.log(json);
    return;
  }
  const outPath = path.resolve(output);
  fs.writeFileSync(outPath, json, 'utf8');
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const files = resolveStories(args.story);
  if (!files.length) {
    console.error(`No stories found for pattern: ${args.story}`);
    process.exitCode = 1;
    return;
  }

  const results = files.map((file) => runStory(file, {
    seed: args.seed,
    maxSteps: args.maxSteps,
    statePath: args.statePath,
    clearState: args.clearState,
  }));

  outputResults(results, args.output);

  const allPass = results.length > 0 && results.every((r) => r.pass);
  if (!allPass) {
    process.exitCode = 1;
  }
}

main();
