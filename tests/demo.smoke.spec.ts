import { test, expect } from '@playwright/test';

// Smoke: load demo, ensure no console errors, story renders, choices exist, and clicking advances.
test('demo loads and presents initial UI', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  await page.goto('/demo/');

  // Story container appears
  const story = page.locator('#story');
  await expect(story).toBeVisible();

  // Wait for initial text to render
  await expect(story).toContainText('Hello');

  // Choices render
  const choices = page.locator('.choice-btn');
  await expect(choices.count()).resolves.toBeGreaterThan(0);

  // Click the first choice and expect story to advance
  const firstChoice = choices.first();
  const beforeText = await story.textContent();
  await firstChoice.click();
  await expect(story).not.toHaveText(beforeText || '');

  // Should be no console errors
  expect(errors, 'Console errors should be empty').toEqual([]);
});
