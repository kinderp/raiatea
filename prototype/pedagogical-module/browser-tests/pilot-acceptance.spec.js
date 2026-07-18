const { test, expect } = require('@playwright/test');
const fs = require('node:fs/promises');

test('complete generated pilot journey works end to end without external services', async ({ page }) => {
  const externalRequests = [];
  const downloads = [];
  page.on('request', request => {
    if (!request.url().startsWith('http://127.0.0.1:4173/')) externalRequests.push(request.url());
  });
  page.on('download', download => downloads.push(download));

  await page.goto('/index.html');
  await expect(page.getByRole('heading', { name: 'Raiatea: primo percorso pilot' })).toBeVisible();
  await expect(page.locator('[data-pilot-module="self-attention-orientation"] [data-pilot-status]')).toHaveText('Non iniziato');
  await expect(page.locator('[data-pilot-module="query-key-value"] [data-pilot-status]')).toHaveText('Non iniziato');
  await expect(page.locator('[data-pilot-recommendation]')).toContainText('Il ruolo della self-attention nel modello GPT');
  await expect(page.getByRole('heading', { name: 'Come leggere il riepilogo ed esportare le evidenze' })).toBeVisible();

  await page.getByRole('link', { name: 'Inizia il percorso' }).click();
  await expect(page).toHaveURL(/\/self-attention\.html$/);
  await expect(page.getByRole('heading', { name: 'Il ruolo della self-attention nel modello GPT' })).toBeVisible();

  await page.getByRole('button', { name: 'Sì', exact: true }).click();
  const remediation = page.getByRole('region', { name: 'Recupero mirato' });
  await expect(remediation).toBeVisible();
  await remediation.getByRole('button', { name: 'Si calcolano score, pesi e una somma pesata' }).click();
  await expect(remediation).toContainText('Corretto: questa descrizione elenca operazioni interne.');
  await remediation.getByRole('button', { name: 'Torna alla domanda originale' }).click();
  await page.getByRole('button', { name: 'No', exact: true }).click();
  await expect(page.locator('#quizFeedback')).toContainText('Esatto: è una mappa di orientamento.');
  await expect(page.locator('#evidenceSummary')).toContainText('1/4 verifiche completate');
  await expect(page.locator('#evidenceSummary')).toContainText('risposte corrette dopo recupero');

  await page.getByRole('navigation', { name: 'Percorso pilot' })
    .getByRole('link', { name: /Query, Key e Value nella self-attention/ }).click();
  await expect(page).toHaveURL(/\/query-key-value\.html$/);
  await expect(page.getByRole('heading', { name: 'Query, Key e Value nella self-attention' })).toBeVisible();
  await page.getByRole('button', { name: 'Dallo stesso embedding con matrici diverse' }).click();
  await expect(page.locator('#quizFeedback')).toContainText('Corretto.');
  await expect(page.locator('#evidenceSummary')).toContainText('1/3 verifiche completate');
  expect(downloads).toHaveLength(0);

  const before = await page.evaluate(() => ({
    first: localStorage.getItem('raiatea-progress:self-attention-orientation'),
    second: localStorage.getItem('raiatea-progress:query-key-value'),
    keys: Object.keys(localStorage).sort()
  }));

  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Esporta evidenze JSON' }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('query-key-value-evidence-v1.json');
  const path = await download.path();
  expect(path).not.toBeNull();
  const evidence = JSON.parse(await fs.readFile(path, 'utf8'));
  expect(evidence.format).toBe('raiatea-learner-evidence');
  expect(evidence.version).toBe(1);
  expect(evidence.module.id).toBe('query-key-value');
  expect(evidence.progress.steps[0].correct).toBe(true);
  expect(evidence.progress.steps[0].attempts).toBe(1);
  expect(JSON.stringify(evidence)).not.toContain('self-attention-orientation');

  const after = await page.evaluate(() => ({
    first: localStorage.getItem('raiatea-progress:self-attention-orientation'),
    second: localStorage.getItem('raiatea-progress:query-key-value'),
    keys: Object.keys(localStorage).sort()
  }));
  expect(after).toEqual(before);
  expect(downloads).toHaveLength(1);

  await page.getByRole('navigation', { name: 'Percorso pilot' })
    .getByRole('link', { name: 'Indice del pilot' }).click();
  await expect(page).toHaveURL(/\/index\.html$/);
  await expect(page.locator('[data-pilot-module="self-attention-orientation"] [data-pilot-status]')).toHaveText('In corso');
  await expect(page.locator('[data-pilot-module="query-key-value"] [data-pilot-status]')).toHaveText('In corso');
  await expect(page.locator('[data-pilot-recommendation]')).toContainText('Il ruolo della self-attention nel modello GPT');
  await expect(page.getByRole('link', { name: /^1\. Il ruolo della self-attention/ })).toBeEnabled();
  await expect(page.getByRole('link', { name: /^2\. Query, Key e Value/ })).toBeEnabled();
  expect(externalRequests).toEqual([]);
});
