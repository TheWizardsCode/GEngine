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

async function loadDemo(page) {
  await useTestStory(page);
  await page.goto('/demo/');
  const story = page.locator('#story');
  await expect(story).toBeVisible();
  await expect(story).toContainText('Hello');
  const choices = page.locator('.choice-btn');
  await expect(choices.count()).resolves.toBeGreaterThan(0);
  return { story, choices };
}

// Click (baseline smoke)
test('demo loads and presents initial UI (click)', async ({ page }) => {
  const errors = await collectConsoleErrors(page);
  const { story, choices } = await loadDemo(page);
  const firstChoice = choices.first();
  const beforeText = await story.textContent();
  await firstChoice.click();
  await expect(story).not.toHaveText(beforeText || '');
  expect(errors, 'Console errors should be empty').toEqual([]);
});

// Keyboard advance
test('choice can be selected via keyboard', async ({ page }) => {
  const errors = await collectConsoleErrors(page);
  const { story, choices } = await loadDemo(page);
  const firstChoice = choices.first();
  await firstChoice.focus();
  const beforeText = await story.textContent();
  await page.keyboard.press('Enter');
  await expect(story).not.toHaveText(beforeText || '');
  expect(errors, 'Console errors should be empty').toEqual([]);
});

// Touch/tap advance (touch project only)
test('choice can be selected via tap (touch)', async ({ page, browserName }) => {
  test.skip(!!page.context()._options?.hasTouch === false, 'Tap only for touch-enabled context');
  const errors = await collectConsoleErrors(page);
  const { story, choices } = await loadDemo(page);
  const firstChoice = choices.first();
  const beforeText = await story.textContent();
  await firstChoice.tap();
  await expect(story).not.toHaveText(beforeText || '');
  expect(errors, 'Console errors should be empty').toEqual([]);
});

// Controller/gamepad surrogate via Space key
test('choice can be selected via controller (Space key surrogate)', async ({ page }) => {
  const errors = await collectConsoleErrors(page);
  const { story, choices } = await loadDemo(page);
  const firstChoice = choices.first();
  await firstChoice.focus();
  const beforeText = await story.textContent();
  await page.keyboard.press('Space');
  await expect(story).not.toHaveText(beforeText || '');
  expect(errors, 'Console errors should be empty').toEqual([]);
});
