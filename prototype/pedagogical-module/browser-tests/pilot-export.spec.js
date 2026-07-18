const { test, expect } = require('@playwright/test');
const fs = require('node:fs/promises');

function completedProgress(stepCount) {
  return {
    currentStep: stepCount - 1,
    steps: Array.from({ length: stepCount }, (_, index) => ({
      attempts: index + 1,
      correct: true,
      usedRemediation: index === 0,
      activityCompleted: index === 0
    }))
  };
}

test('pilot guidance is static and distinguishes dashboard summary and module export', async ({ page }) => {
  await page.goto('/index.html');
  const guide = page.getByRole('region', { name: 'Come leggere il riepilogo ed esportare le evidenze' });
  await expect(guide).toBeVisible();
  await expect(guide).toContainText('stato della dashboard');
  await expect(guide).toContainText('Riepilogo del percorso');
  await expect(guide).toContainText('Esporta evidenze JSON');
  await expect(guide).toContainText('solo modulo aperto');
  await expect(guide).toContainText('non sono un voto o un mastery score');
  await expect(page.getByRole('link', { name: /^1\. Il ruolo della self-attention/ })).toBeEnabled();
  await expect(page.getByRole('link', { name: /^2\. Query, Key e Value/ })).toBeEnabled();
});

test('explicit export downloads the existing module-scoped v1 document without mutations', async ({ page }) => {
  const externalRequests = [];
  const downloads = [];
  page.on('request', request => {
    if (!request.url().startsWith('http://127.0.0.1:4173/')) externalRequests.push(request.url());
  });
  page.on('download', download => downloads.push(download));

  await page.goto('/self-attention.html');
  const moduleData = await page.evaluate(() => ({
    id: window.RAIATEA_MODULE.id,
    title: window.RAIATEA_MODULE.title,
    language: window.RAIATEA_MODULE.language,
    stepCount: window.RAIATEA_MODULE.steps.length
  }));
  const progress = completedProgress(moduleData.stepCount);
  const progressKey = `raiatea-progress:${moduleData.id}`;

  await page.evaluate(({ progressKey, progress }) => {
    localStorage.setItem(progressKey, JSON.stringify(progress));
    localStorage.setItem('raiatea-reading-settings:test', 'preserve-me');
    localStorage.setItem('unrelated-secret', 'do-not-touch');
  }, { progressKey, progress });
  await page.reload();

  const before = await page.evaluate(({ progressKey }) => ({
    progress: localStorage.getItem(progressKey),
    reading: localStorage.getItem('raiatea-reading-settings:test'),
    unrelated: localStorage.getItem('unrelated-secret'),
    keys: Object.keys(localStorage).sort()
  }), { progressKey });
  expect(downloads).toHaveLength(0);

  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Esporta evidenze JSON' }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe(`${moduleData.id}-evidence-v1.json`);

  const downloadPath = await download.path();
  expect(downloadPath).not.toBeNull();
  const exported = JSON.parse(await fs.readFile(downloadPath, 'utf8'));
  expect(Object.keys(exported).sort()).toEqual(['format', 'module', 'progress', 'version']);
  expect(exported.format).toBe('raiatea-learner-evidence');
  expect(exported.version).toBe(1);
  expect(exported.module.id).toBe(moduleData.id);
  expect(exported.module.title).toBe(moduleData.title);
  expect(exported.module.language).toBe(moduleData.language);
  expect(exported.module.stepCount).toBe(moduleData.stepCount);
  expect(exported.progress.currentStep).toBe(progress.currentStep);
  expect(exported.progress.steps).toHaveLength(moduleData.stepCount);
  expect(exported.progress.steps[0].attempts).toBe(1);
  expect(exported.progress.steps[0].correct).toBe(true);
  expect(exported.progress.steps[0].usedRemediation).toBe(true);
  expect(exported.progress.steps[0].activityCompleted).toBe(true);

  const serialized = JSON.stringify(exported);
  for (const forbidden of [
    'unrelated-secret',
    'do-not-touch',
    'raiatea-reading-settings:test',
    'preserve-me',
    'timestamp',
    'analytics',
    'telemetry',
    'email'
  ]) expect(serialized).not.toContain(forbidden);

  const after = await page.evaluate(({ progressKey }) => ({
    progress: localStorage.getItem(progressKey),
    reading: localStorage.getItem('raiatea-reading-settings:test'),
    unrelated: localStorage.getItem('unrelated-secret'),
    keys: Object.keys(localStorage).sort()
  }), { progressKey });
  expect(after).toEqual(before);
  expect(downloads).toHaveLength(1);
  expect(externalRequests).toEqual([]);

  await page.goto('/index.html');
  await expect(page.locator(`[data-pilot-module="${moduleData.id}"] [data-pilot-status]`))
    .toHaveText('Completato localmente');
  await expect(page.locator('[data-pilot-recommendation]'))
    .toContainText('Query, Key e Value nella self-attention');
});
