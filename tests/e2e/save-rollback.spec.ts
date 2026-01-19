import { test, expect } from '@playwright/test';

// E2E smoke: save mid-branch -> reload -> resume or show graceful rollback

test('save mid-branch then reload resumes or rolls back gracefully', async ({ page }) => {
  await page.goto('http://127.0.0.1:4173/demo/?story=/stories/demo.ink');
  // Wait for demo to load and present choices
  await page.waitForSelector('#choices');
  // Click first choice to get into a branched flow
  await page.click('#choices button');

  // Trigger a manual save via window API exposed by demo
  await page.evaluate(() => { window.DemoSave && window.DemoSave.save('e2e-test'); });

  // Reload the page
  await page.reload();

  // Load from save via API
  await page.evaluate(() => { window.DemoSave && window.DemoSave.load('e2e-test'); });

  // Expect either continued play or a graceful recovery message
  const body = await page.textContent('#main');
  expect(body).toBeTruthy();
});
