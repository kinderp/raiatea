const { test, expect } = require('@playwright/test');

function progress(stepCount, mutate = () => {}) {
  const value = {
    currentStep: 0,
    steps: Array.from({ length: stepCount }, () => ({
      attempts: 0,
      correct: false,
      usedRemediation: false,
      activityCompleted: false
    }))
  };
  mutate(value);
  return value;
}

test('launcher opens the canonical two-module route with working relative navigation', async ({ page }) => {
  const requests = [];
  page.on('request', request => requests.push(request.url()));
  await page.goto('/index.html');
  await expect(page.getByRole('heading', { name: 'Raiatea: primo percorso pilot' })).toBeVisible();
  await expect(page.getByRole('link', { name: /^1\. Il ruolo della self-attention/ })).toHaveAttribute('href', 'self-attention.html');
  await expect(page.getByRole('link', { name: /^2\. Query, Key e Value/ })).toHaveAttribute('href', 'query-key-value.html');
  await page.getByRole('link', { name: 'Inizia il percorso' }).click();
  await expect(page).toHaveURL(/\/self-attention\.html$/);
  const firstRoute = page.getByRole('navigation', { name: 'Percorso pilot' });
  await firstRoute.getByRole('link', { name: /Query, Key e Value nella self-attention/ }).click();
  await expect(page).toHaveURL(/\/query-key-value\.html$/);
  await page.getByRole('navigation', { name: 'Percorso pilot' })
    .getByRole('link', { name: 'Indice del pilot' }).click();
  await expect(page).toHaveURL(/\/index\.html$/);
  expect(requests.every(url => url.startsWith('http://127.0.0.1:4173/'))).toBe(true);
});

test('dashboard derives empty partial and completed states without gating links', async ({ page }) => {
  await page.goto('/index.html');
  const manifest = await page.evaluate(() => window.RAIATEA_PILOT);
  const [first, second] = manifest.modules;

  await expect(page.locator(`[data-pilot-module="${first.id}"] [data-pilot-status]`)).toHaveText('Non iniziato');
  await expect(page.locator(`[data-pilot-module="${second.id}"] [data-pilot-status]`)).toHaveText('Non iniziato');
  await expect(page.locator('[data-pilot-recommendation]')).toContainText(first.title);

  await page.evaluate(({ first }) => {
    localStorage.setItem(`raiatea-progress:${first.id}`, JSON.stringify({
      currentStep: 0,
      steps: Array.from({ length: first.stepCount }, (_, index) => ({
        attempts: index === 0 ? 1 : 0,
        correct: false,
        usedRemediation: index === 0,
        activityCompleted: false
      }))
    }));
  }, { first });
  await page.reload();
  await expect(page.locator(`[data-pilot-module="${first.id}"] [data-pilot-status]`)).toHaveText('In corso');
  await expect(page.getByRole('link', { name: new RegExp(first.title) })).toBeEnabled();
  await expect(page.getByRole('link', { name: new RegExp(second.title) })).toBeEnabled();

  await page.evaluate(({ first }) => {
    localStorage.setItem(`raiatea-progress:${first.id}`, JSON.stringify({
      currentStep: first.stepCount - 1,
      steps: Array.from({ length: first.stepCount }, () => ({
        attempts: 1,
        correct: true,
        usedRemediation: true,
        activityCompleted: false
      }))
    }));
  }, { first });
  await page.reload();
  await expect(page.locator(`[data-pilot-module="${first.id}"] [data-pilot-status]`)).toHaveText('Completato localmente');
  await expect(page.locator('[data-pilot-recommendation]')).toContainText(second.title);
});

test('dashboard fails closed for malformed and unrelated storage without writing', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('unrelated-secret', 'do-not-read-or-change');
    localStorage.setItem('raiatea-progress:self-attention-orientation', '{broken');
  });
  await page.goto('/index.html');
  await expect(page.locator('[data-pilot-module="self-attention-orientation"] [data-pilot-status]')).toHaveText('Non iniziato');
  const snapshot = await page.evaluate(() => ({
    unrelated: localStorage.getItem('unrelated-secret'),
    malformed: localStorage.getItem('raiatea-progress:self-attention-orientation'),
    keys: Object.keys(localStorage).sort()
  }));
  expect(snapshot.unrelated).toBe('do-not-read-or-change');
  expect(snapshot.malformed).toBe('{broken');
  expect(snapshot.keys).toEqual(['raiatea-progress:self-attention-orientation', 'unrelated-secret']);
});

test('dashboard refreshes on pageshow and relevant storage events', async ({ page }) => {
  await page.goto('/index.html');
  const first = await page.evaluate(() => window.RAIATEA_PILOT.modules[0]);
  await page.evaluate(({ first }) => {
    localStorage.setItem(`raiatea-progress:${first.id}`, JSON.stringify({
      currentStep: 0,
      steps: Array.from({ length: first.stepCount }, () => ({
        attempts: 0,
        correct: false,
        usedRemediation: false,
        activityCompleted: false
      }))
    }));
    window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
  }, { first });
  await expect(page.locator(`[data-pilot-module="${first.id}"] [data-pilot-status]`)).toHaveText('Non iniziato');

  await page.evaluate(({ first }) => {
    const value = {
      currentStep: 0,
      steps: Array.from({ length: first.stepCount }, (_, index) => ({
        attempts: index === 0 ? 1 : 0,
        correct: false,
        usedRemediation: false,
        activityCompleted: false
      }))
    };
    const key = `raiatea-progress:${first.id}`;
    localStorage.setItem(key, JSON.stringify(value));
    window.dispatchEvent(new StorageEvent('storage', {
      key,
      newValue: JSON.stringify(value),
      storageArea: localStorage
    }));
  }, { first });
  await expect(page.locator(`[data-pilot-module="${first.id}"] [data-pilot-status]`)).toHaveText('In corso');
});
