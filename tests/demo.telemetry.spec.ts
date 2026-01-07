import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const TEST_STORY_PATH = path.join(__dirname, '..', 'web', 'stories', 'test.ink');
const TEST_STORY_SOURCE = fs.readFileSync(TEST_STORY_PATH, 'utf8');

async function useTestStory(page) {
  await page.route('**/stories/demo.ink', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'text/plain; charset=utf-8',
      body: TEST_STORY_SOURCE,
    });
  });
}

async function collectConsoleErrors(page) {
  const errors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  return errors;
}

async function setupTelemetryCapture(page) {
  await page.addInitScript(() => {
    // @ts-ignore
    window.__telemetryEvents = [];
    const _log = console.log.bind(console);
    console.log = (...args) => {
      try {
        // @ts-ignore
        window.__telemetryEvents.push(args.join(' '));
      } catch (e) {
        // ignore capture errors
      }
      _log(...args);
    };
  });
}

async function loadDemo(page) {
  await useTestStory(page);
  await setupTelemetryCapture(page);
  await page.goto('/demo/');
  const story = page.locator('#story');
  await expect(story).toBeVisible();
  const choices = page.locator('.choice-btn');
  await expect(choices.count()).resolves.toBeGreaterThan(0);
  return { story, choices };
}

async function waitForTelemetry(page, event: string, timeout = 5_000) {
  await page.waitForFunction(
    name => Array.isArray((window as any).__telemetryEvents) && (window as any).__telemetryEvents.includes(name),
    event,
    { timeout },
  );
}

// Telemetry and smoke assertions
test('emits telemetry events and triggers smoke', async ({ page }) => {
  const errors = await collectConsoleErrors(page);
  const { choices } = await loadDemo(page);

  await waitForTelemetry(page, 'story_start');

  await waitForTelemetry(page, 'smoke_triggered');

  const firstChoice = choices.first();
  await firstChoice.click();
  await waitForTelemetry(page, 'choice_selected');

  await waitForTelemetry(page, 'story_complete');

  await expect.poll(async () => {
    return page.evaluate(() => {
      return !!(window as any).Smoke?.getState?.().running;
    });
  }, { timeout: 5_000 }).toBeTruthy();

  expect(errors, 'Console errors should be empty').toEqual([]);
});
