const { test, expect } = require('@playwright/test');
const fs = require('fs/promises');

const modulePath = '/self-attention.html';

test('keeps canonical revision and step IDs out of learner-evidence v1', async ({ page }) => {
  await page.goto(modulePath);
  await page.evaluate(() => localStorage.clear());
  await page.reload();

  const canonicalIdentity = await page.evaluate(() => ({
    revision: window.RAIATEA_MODULE.revision,
    stepIds: window.RAIATEA_MODULE.steps.map((step) => step.id)
  }));
  expect(canonicalIdentity.revision).toBe(1);
  expect(canonicalIdentity.stepIds).toEqual([
    'orient-with-system-map',
    'convert-tokens-to-embeddings',
    'contextualize-token-representations',
    'transition-to-internal-calculations'
  ]);

  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Esporta evidenze JSON' }).click();
  const download = await downloadPromise;
  const exported = JSON.parse(await fs.readFile(await download.path(), 'utf8'));

  expect(exported.format).toBe('raiatea-learner-evidence');
  expect(exported.version).toBe(1);
  expect(Object.keys(exported.module).sort()).toEqual([
    'id',
    'language',
    'source',
    'stepCount',
    'title'
  ]);
  expect(exported.module).not.toHaveProperty('revision');
  expect(exported.module).not.toHaveProperty('stepId');

  for (const step of exported.progress.steps) {
    expect(Object.keys(step).sort()).toEqual([
      'activityCompleted',
      'attempts',
      'correct',
      'index',
      'title',
      'usedRemediation'
    ]);
    expect(step).not.toHaveProperty('id');
    expect(step).not.toHaveProperty('stepId');
  }
});
