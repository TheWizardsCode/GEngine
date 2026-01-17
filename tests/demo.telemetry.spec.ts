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

async function openSettings(page) {
  const settingsBtn = page.locator('#ai-settings-btn');
  await expect(settingsBtn).toBeVisible();
  await settingsBtn.click();
  const panel = page.locator('#ai-settings-panel');
  await expect(panel).toBeVisible();
  return panel;
}

async function setSliderValue(page, selector, value) {
  const slider = page.locator(selector);
  await expect(slider).toBeVisible();
  const target = Number(value);
  await slider.evaluate((el, val) => {
    (el as HTMLInputElement).value = String(val);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }, target);
}

async function waitForAIChoice(page, timeout = 15_000) {
  const aiChoice = page.locator('.choice-btn.ai-choice, .choice-btn.ai-choice-normal');
  await expect.poll(async () => aiChoice.count(), { timeout, interval: 500 }).toBeGreaterThan(0);
  return aiChoice;
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

test('Director threshold slider updates stored settings', async ({ page }) => {
  await loadDemo(page);
  await openSettings(page);

  await expect(page.locator('.ai-config-section')).toBeVisible();

  const slider = page.locator('#director-risk-threshold');
  await expect(slider).toHaveValue('0.4');

  await slider.evaluate((el) => {
    (el as HTMLInputElement).value = '0.65';
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  });

  await expect(page.locator('#director-threshold-value')).toHaveText('0.65');

  const saved = await page.evaluate(() => window.ApiKeyManager.getSettings().directorRiskThreshold);
  expect(saved).toBeCloseTo(0.65, 2);
});

test('invalid threshold input clamps to range', async ({ page }) => {
  await loadDemo(page);
  await openSettings(page);

  const slider = page.locator('#director-risk-threshold');
  await slider.evaluate((el) => {
    (el as HTMLInputElement).value = '2.0';
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  });

  await expect(slider).toHaveValue('0.8');
  const saved = await page.evaluate(() => window.ApiKeyManager.getSettings().directorRiskThreshold);
  expect(saved).toBeCloseTo(0.8, 2);
});

test('Director high threshold approves more proposals than low threshold', async ({ page }) => {
  await loadDemo(page);
  await openSettings(page);

  await page.locator('#director-enabled').check();
  await setSliderValue(page, '#director-risk-threshold', 0.8);
  await page.locator('#ai-settings-close').click();

  await expect(page.locator('.ai-config-section')).toBeHidden({ timeout: 1 });

  const highApprovals = await page.evaluate(async () => {
    const inkrunner = (window as any).__inkrunner;
    const story = inkrunner.__getStory?.() ?? inkrunner.__getStory?.();
    let approvals = 0;
    for (let i = 0; i < 3; i++) {
      const result = await inkrunner.addAIChoice({
        forceDirectorEnabled: true,
        forceRiskThreshold: 0.8,
        mockProposalOverride: {
          choice_text: `AI suggestion ${i}`,
          content: { text: 'Mock AI content for testing', return_path: 'pines' },
          metadata: { confidence_score: 0.5 }
        }
      });
      if (result === 'approved') approvals++;
    }
    return approvals;
  });

  await openSettings(page);
  await setSliderValue(page, '#director-risk-threshold', 0.2);
  await page.locator('#ai-settings-close').click();

  const lowApprovals = await page.evaluate(async () => {
    const inkrunner = (window as any).__inkrunner;
    let approvals = 0;
    for (let i = 0; i < 3; i++) {
      const result = await inkrunner.addAIChoice({
        forceDirectorEnabled: true,
        forceRiskThreshold: 0.2,
        mockProposalOverride: {
          choice_text: `AI suggestion low ${i}`,
          content: { text: 'Mock AI content for low threshold', return_path: 'pines' },
          metadata: { confidence_score: 0.1 }
        }
      });
      if (result === 'approved') approvals++;
    }
    return approvals;
  });

  expect(highApprovals).toBeGreaterThan(lowApprovals);
});

test('Director off restores naive injection', async ({ page }) => {
  await loadDemo(page);
  await openSettings(page);

  const directorToggle = page.locator('#director-enabled');
  await expect(directorToggle).toBeChecked();
  await directorToggle.uncheck();

  await expect(page.locator('.ai-director-controls')).toHaveCSS('display', 'none');

  const aiChoice = await waitForAIChoice(page);
  await expect(aiChoice.first()).toBeVisible();
});
