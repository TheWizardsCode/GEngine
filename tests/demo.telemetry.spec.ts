import { test, expect } from '@playwright/test';
async function collectConsoleErrors(page) {
  const errors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  return errors;
}

async function captureSmokeState(page) {
  await page.exposeBinding('__getSmokeState', () => {
    const state = (window as any).Smoke?.getState?.();
    return state || null;
  });
  await page.exposeBinding('__smokeEvents', () => {
    const events = (window as any).__smokeEvents || [];
    return [...events];
  });
  await page.addInitScript(() => {
    // @ts-ignore
    window.__smokeEvents = [];
    // @ts-ignore
    window.addEventListener('smoke_state', (e) => {
      // @ts-ignore
      window.__smokeEvents.push(e.detail);
    });
  });
}

async function setupTelemetryCapture(page) {
  await page.addInitScript(() => {
    // @ts-ignore
    window.__telemetryEvents = [];
    const _log = console.log.bind(console);
    console.log = (...args) => {
      try {
        // @ts-ignore
        window.__telemetryEvents.push(args);
      } catch (e) {
        // ignore capture errors
      }
      _log(...args);
    };
  });
}

async function loadDemo(page) {
  await setupTelemetryCapture(page);
  await captureSmokeState(page);
  await page.goto('/demo/');
  const story = page.locator('#story');
  await expect(story).toBeVisible();
  await page.waitForFunction(() => {
    const el = document.querySelector('#story');
    return !!el && el.textContent && el.textContent.trim().length > 0;
  }, undefined, { timeout: 5_000 });
  const choices = page.locator('.choice-btn');
  await expect.poll(async () => choices.count(), { timeout: 5_000 }).toBeGreaterThan(0);
  await page.waitForFunction(() => {
    const smoke = (window as any).Smoke?.getState?.();
    return smoke && typeof smoke.running === 'boolean';
  }, undefined, { timeout: 5_000 });
  return { story, choices };
}

async function waitForTelemetry(page, event: string, timeout = 10_000) {
  await expect.poll(async () => {
    return page.evaluate(name => {
      const evts = (window as any).__telemetryEvents;
      if (!Array.isArray(evts)) return null;
      return evts.some((args: any) => {
        if (!Array.isArray(args)) return false;
        return args.some((val) => typeof val === 'string' && val.includes(name));
      });
    }, event);
  }, { timeout, interval: 250 }).toBeTruthy();
}

// Telemetry and smoke assertions
test('emits telemetry events and triggers smoke', async ({ page }) => {
  const errors = await collectConsoleErrors(page);
  const { choices } = await loadDemo(page);

  await waitForTelemetry(page, 'story_start');

  await waitForTelemetry(page, 'smoke_triggered');

  while (await choices.count() > 0) {
    await choices.first().click();
    await waitForTelemetry(page, 'choice_selected');
    await page.waitForTimeout(50);
  }

  await waitForTelemetry(page, 'story_complete');

  const smokeStates: Array<Record<string, any> | null> = [];

  await expect.poll(async () => {
    const state = await page.evaluate(() => {
      const s = (window as any).Smoke?.getState?.();
      return s ? { ...s } : null;
    });
    smokeStates.push(state);
    const events = await page.evaluate(() => (window as any).__smokeEvents || []);
    const stateOk = !!(state && (state.running || state.remainingMs > 0 || state.durationMs > 0));
    const eventsOk = Array.isArray(events) && events.length > 0;
    return stateOk || eventsOk;
  }, { timeout: 10_000, intervals: [200, 400, 800, 1600, 2000] }).toBeTruthy();

  const smokeEvents = await page.evaluate(() => (window as any).__smokeEvents || []);

  if (errors.length || smokeStates.every(s => !s || (!s.running && !(s.remainingMs > 0) && !(s?.durationMs > 0)))) {
    console.warn('Smoke state samples:', JSON.stringify(smokeStates));
    console.warn('Smoke events:', JSON.stringify(smokeEvents));
  }

  expect(errors, 'Console errors should be empty').toEqual([]);
});
