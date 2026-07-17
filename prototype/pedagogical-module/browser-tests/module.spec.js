const { test, expect } = require('@playwright/test');
const fs = require('fs/promises');

const modulePath = '/self-attention.html';
const progressKey = 'raiatea-progress:self-attention-orientation';

function evidenceDocument(overrides = {}) {
  const document = {
    format: 'raiatea-learner-evidence',
    version: 1,
    module: {
      id: 'self-attention-orientation',
      title: 'Il ruolo della self-attention nel modello GPT',
      language: 'it',
      stepCount: 4,
      source: {
        title: 'Build a Large Language Model (From Scratch)',
        chapter: '3',
        section: '3.3',
        figure: '3.6',
        pages: [55]
      }
    },
    progress: {
      currentStep: 2,
      steps: [
        { index: 0, title: 'Usare la figura come mappa', attempts: 2, correct: true, usedRemediation: true, activityCompleted: true },
        { index: 1, title: 'Dal testo agli embedding', attempts: 1, correct: true, usedRemediation: false, activityCompleted: false },
        { index: 2, title: 'Arricchire ogni token con il contesto', attempts: 1, correct: false, usedRemediation: false, activityCompleted: false },
        { index: 3, title: 'Passare ai calcoli interni', attempts: 0, correct: false, usedRemediation: false, activityCompleted: false }
      ]
    }
  };
  return {
    ...document,
    ...overrides,
    module: { ...document.module, ...(overrides.module || {}) },
    progress: { ...document.progress, ...(overrides.progress || {}) }
  };
}

async function selectEvidenceFile(page, content, name = 'learner-evidence.json') {
  const fileChooserPromise = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Importa evidenze JSON' }).click();
  const fileChooser = await fileChooserPromise;
  await fileChooser.setFiles({
    name,
    mimeType: 'application/json',
    buffer: Buffer.from(typeof content === 'string' ? content : JSON.stringify(content))
  });
}

async function resetBrowserState(page) {
  await page.goto(modulePath);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
}

test.beforeEach(async ({ page }) => {
  await resetBrowserState(page);
});

test('navigates steps through controls, direct selection, and keyboard shortcuts', async ({ page }) => {
  const phaseTitle = page.locator('#phaseTitle');

  await expect(phaseTitle).toHaveText('Usare la figura come mappa');
  await expect(page.locator('#stepLabel')).toContainText('Passo 1 di 4');
  await expect(page.locator('#prevBtn')).toBeDisabled();

  await page.locator('#nextBtn').click();
  await expect(phaseTitle).toHaveText('Dal testo agli embedding');
  await expect(page.locator('#input')).not.toHaveClass(/dim/);
  await expect(page.locator('#embedding')).not.toHaveClass(/dim/);
  await expect(page.locator('#attention')).toHaveClass(/dim/);

  await page.evaluate(() => document.activeElement?.blur());
  await page.keyboard.press('ArrowRight');
  await expect(phaseTitle).toHaveText('Arricchire ogni token con il contesto');

  await page.locator('#stepsNav button[data-step="3"]').click();
  await expect(phaseTitle).toHaveText('Passare ai calcoli interni');
  await expect(page.locator('#nextBtn')).toBeDisabled();

  await page.locator('#resetBtn').click();
  await expect(phaseTitle).toHaveText('Usare la figura come mappa');
});

test('persists Focus UI settings without stealing arrow keys from focused controls', async ({ page }) => {
  const phaseTitle = page.locator('#phaseTitle');
  const size = page.locator('#fontSizeSelect');
  const density = page.locator('#densitySelect');
  const width = page.locator('#widthSelect');
  const align = page.locator('#alignSelect');
  const motion = page.locator('#motionSelect');

  await page.locator('#themeBtn').click();
  await size.selectOption('20');
  await density.selectOption('relaxed');
  await width.selectOption('76');
  await align.selectOption('justify');
  await motion.selectOption('reduced');

  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await expect(page.locator('html')).toHaveAttribute('data-density', 'relaxed');
  await expect(page.locator('html')).toHaveAttribute('data-align', 'justify');
  await expect(page.locator('html')).toHaveAttribute('data-motion', 'reduced');
  await expect(page.locator('html')).toHaveCSS('--reading-size', '20px');

  await size.focus();
  await size.press('ArrowRight');
  await expect(phaseTitle).toHaveText('Usare la figura come mappa');
  const selectedSize = await size.inputValue();

  const stored = await page.evaluate(() => JSON.parse(localStorage.getItem('raiatea-reading-settings')));
  expect(stored).toEqual({
    theme: 'dark',
    size: selectedSize,
    density: 'relaxed',
    width: '76',
    align: 'justify',
    motion: 'reduced'
  });

  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await expect(size).toHaveValue(selectedSize);
  await expect(density).toHaveValue('relaxed');
  await expect(width).toHaveValue('76');
  await expect(align).toHaveValue('justify');
  await expect(motion).toHaveValue('reduced');
});

test('supports targeted remediation, concept focus, retry, and persisted evidence', async ({ page }) => {
  await expect(page.locator('html')).toHaveAttribute('lang', 'it');
  await expect(page.locator('aside.panel')).toHaveAttribute('aria-live', 'polite');
  await expect(page.locator('.visual svg')).toHaveAttribute('role', 'img');

  await page.locator('#quizAnswers button').filter({ hasText: /^Sì$/ }).click();
  const remediation = page.getByRole('region', { name: 'Recupero mirato' });
  await expect(remediation).toBeVisible();

  await page.locator('#motionSelect').selectOption('reduced');
  await page.getByRole('link', { name: 'Ripassa self-attention' }).click();
  const concept = page.locator('#concept-self-attention');
  await expect(concept).toBeFocused();
  await expect(concept).toHaveClass(/target-flash/);

  await page.getByRole('button', { name: 'Si calcolano score, pesi e una somma pesata' }).click();
  await expect(page.locator('.remediation-activity-feedback')).toHaveText('Corretto: questa descrizione elenca operazioni interne.');
  const retry = page.getByRole('button', { name: 'Torna alla domanda originale' });
  await expect(retry).toBeEnabled();
  await retry.click();
  await expect(page.locator('#quizAnswers button').first()).toBeFocused();

  await page.locator('#quizAnswers button').filter({ hasText: /^No$/ }).click();
  await expect(page.locator('#evidenceSummary')).toContainText('1/4 verifiche completate');
  await expect(page.locator('#evidenceSummary')).toContainText('2 tentativi');
  await expect(page.locator('#evidenceSummary')).toContainText('1 risposte corrette dopo recupero');

  const progress = await page.evaluate(() => JSON.parse(localStorage.getItem('raiatea-progress:self-attention-orientation')));
  expect(progress.steps[0]).toEqual({
    attempts: 2,
    correct: true,
    usedRemediation: true,
    activityCompleted: true
  });

  await page.reload();
  await expect(page.locator('#evidenceSummary')).toContainText('1/4 verifiche completate');
  await expect(page.locator('#phaseTitle')).toHaveText('Usare la figura come mappa');
});

test('exports only versioned observable learner evidence', async ({ page }) => {
  const progress = {
    currentStep: 1,
    steps: [
      { attempts: 2, correct: true, usedRemediation: true, activityCompleted: true },
      { attempts: 1, correct: false, usedRemediation: false, activityCompleted: false },
      { attempts: 0, correct: false, usedRemediation: false, activityCompleted: false },
      { attempts: 0, correct: false, usedRemediation: false, activityCompleted: false }
    ]
  };
  await page.evaluate((storedProgress) => {
    localStorage.setItem('raiatea-progress:self-attention-orientation', JSON.stringify(storedProgress));
    localStorage.setItem('raiatea-reading-settings', JSON.stringify({ theme: 'dark', size: '22' }));
    localStorage.setItem('unrelated-secret', 'do-not-export');
  }, progress);
  await page.reload();

  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Esporta evidenze JSON' }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('self-attention-orientation-evidence-v1.json');

  const downloadedPath = await download.path();
  const exported = JSON.parse(await fs.readFile(downloadedPath, 'utf8'));
  expect(exported.format).toBe('raiatea-learner-evidence');
  expect(exported.version).toBe(1);
  expect(exported.module).toEqual({
    id: 'self-attention-orientation',
    title: 'Il ruolo della self-attention nel modello GPT',
    language: 'it',
    stepCount: 4,
    source: {
      title: 'Build a Large Language Model (From Scratch)',
      chapter: '3',
      section: '3.3',
      figure: '3.6',
      pages: [55]
    }
  });
  expect(exported.progress.currentStep).toBe(1);
  expect(exported.progress.steps[0]).toEqual({
    index: 0,
    title: 'Usare la figura come mappa',
    attempts: 2,
    correct: true,
    usedRemediation: true,
    activityCompleted: true
  });
  expect(exported.progress.steps[1].attempts).toBe(1);
  expect(exported.progress.steps).toHaveLength(4);

  const serialized = JSON.stringify(exported);
  expect(serialized).not.toContain('raiatea-reading-settings');
  expect(serialized).not.toContain('dark');
  expect(serialized).not.toContain('unrelated-secret');
  expect(serialized).not.toContain('do-not-export');
  expect(serialized).not.toContain('mastery');
  expect(serialized).not.toContain('email');
  await expect(page.locator('#evidenceExportStatus')).toHaveText('Evidenze esportate in un file JSON locale.');
});

test('previews compatible evidence before explicit restore and preserves unrelated storage', async ({ page }) => {
  const currentProgress = {
    currentStep: 0,
    steps: [
      { attempts: 1, correct: false, usedRemediation: false, activityCompleted: false },
      { attempts: 0, correct: false, usedRemediation: false, activityCompleted: false },
      { attempts: 0, correct: false, usedRemediation: false, activityCompleted: false },
      { attempts: 0, correct: false, usedRemediation: false, activityCompleted: false }
    ]
  };
  await page.evaluate(({ key, progress }) => {
    localStorage.setItem(key, JSON.stringify(progress));
    localStorage.setItem('raiatea-reading-settings', JSON.stringify({ theme: 'dark', size: '22' }));
    localStorage.setItem('unrelated-secret', 'keep-me');
  }, { key: progressKey, progress: currentProgress });
  await page.reload();

  await page.locator('#playBtn').click();
  await expect(page.locator('#playBtn')).toHaveText('⏸ Pausa');
  await selectEvidenceFile(page, evidenceDocument());
  await expect(page.locator('#playBtn')).toHaveText('▶ Riproduci');
  await expect(page.locator('#evidenceImportPanel')).toBeVisible();
  await expect(page.locator('#evidenceImportStatus')).toContainText('File compatibile');
  await expect(page.locator('#evidenceImportPreview')).toContainText('Avanzamento attuale: 0/4 verifiche, 1 tentativi');
  await expect(page.locator('#evidenceImportPreview')).toContainText('File selezionato: 2/4 verifiche, 4 tentativi');

  const beforeConfirm = await page.evaluate((key) => JSON.parse(localStorage.getItem(key)), progressKey);
  expect(beforeConfirm).toEqual(currentProgress);

  await page.getByRole('button', { name: 'Ripristina questo avanzamento' }).click();
  const restored = await page.evaluate((key) => JSON.parse(localStorage.getItem(key)), progressKey);
  expect(restored).toEqual({
    currentStep: 2,
    steps: [
      { attempts: 2, correct: true, usedRemediation: true, activityCompleted: true },
      { attempts: 1, correct: true, usedRemediation: false, activityCompleted: false },
      { attempts: 1, correct: false, usedRemediation: false, activityCompleted: false },
      { attempts: 0, correct: false, usedRemediation: false, activityCompleted: false }
    ]
  });
  expect(await page.evaluate(() => localStorage.getItem('unrelated-secret'))).toBe('keep-me');
  expect(await page.evaluate(() => JSON.parse(localStorage.getItem('raiatea-reading-settings')))).toEqual({ theme: 'dark', size: '22' });
  await expect(page.locator('#phaseTitle')).toHaveText('Arricchire ogni token con il contesto');
  await expect(page.locator('#evidenceSummary')).toContainText('2/4 verifiche completate');
  await expect(page.locator('#evidenceImportStatus')).toHaveText('Avanzamento ripristinato dal file JSON locale.');

  await page.reload();
  await expect(page.locator('#phaseTitle')).toHaveText('Arricchire ogni token con il contesto');
  await expect(page.locator('#evidenceSummary')).toContainText('2/4 verifiche completate');
});

test('cancels a compatible evidence import without changing progress', async ({ page }) => {
  const current = await page.evaluate((key) => JSON.parse(localStorage.getItem(key)), progressKey);
  await selectEvidenceFile(page, evidenceDocument());
  await expect(page.locator('#evidenceImportPanel')).toBeVisible();
  await page.getByRole('button', { name: 'Annulla importazione' }).click();
  await expect(page.locator('#evidenceImportPanel')).toBeHidden();
  await expect(page.locator('#evidenceImportStatus')).toHaveText('Importazione annullata. Nessuna modifica applicata.');
  expect(await page.evaluate((key) => JSON.parse(localStorage.getItem(key)), progressKey)).toEqual(current);
});

test('rejects malformed evidence without changing progress', async ({ page }) => {
  const current = await page.evaluate((key) => JSON.parse(localStorage.getItem(key)), progressKey);
  await selectEvidenceFile(page, '{not valid json');
  await expect(page.locator('#evidenceImportPanel')).toBeHidden();
  await expect(page.locator('#confirmEvidenceImportBtn')).toBeDisabled();
  await expect(page.locator('#evidenceImportStatus')).toContainText('JSON non valido');
  await expect(page.locator('#evidenceImportStatus')).toContainText('Nessuna modifica applicata');
  expect(await page.evaluate((key) => JSON.parse(localStorage.getItem(key)), progressKey)).toEqual(current);
});

test('rejects evidence for another module without changing progress', async ({ page }) => {
  const current = await page.evaluate((key) => JSON.parse(localStorage.getItem(key)), progressKey);
  await selectEvidenceFile(page, evidenceDocument({ module: { id: 'another-module' } }));
  await expect(page.locator('#evidenceImportPanel')).toBeHidden();
  await expect(page.locator('#confirmEvidenceImportBtn')).toBeDisabled();
  await expect(page.locator('#evidenceImportStatus')).toContainText('another-module');
  await expect(page.locator('#evidenceImportStatus')).toContainText('self-attention-orientation');
  await expect(page.locator('#evidenceImportStatus')).toContainText('Nessuna modifica applicata');
  expect(await page.evaluate((key) => JSON.parse(localStorage.getItem(key)), progressKey)).toEqual(current);
});
