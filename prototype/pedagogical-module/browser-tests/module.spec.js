const { test, expect } = require('@playwright/test');

const modulePath = '/self-attention.html';

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

  await page.locator('body').press('ArrowRight');
  await expect(phaseTitle).toHaveText('Arricchire ogni token con il contesto');

  await page.locator('#stepsNav button[data-step="3"]').click();
  await expect(phaseTitle).toHaveText('Passare ai calcoli interni');
  await expect(page.locator('#nextBtn')).toBeDisabled();

  await page.locator('#resetBtn').click();
  await expect(phaseTitle).toHaveText('Usare la figura come mappa');
});

test('persists Focus UI settings without stealing arrow keys from focused controls', async ({ page }) => {
  const phaseTitle = page.locator('#phaseTitle');
  const size = page.getByLabel('Testo');
  const density = page.getByLabel('Spaziatura');
  const width = page.getByLabel('Larghezza');
  const align = page.getByLabel('Allineamento');
  const motion = page.getByLabel('Animazioni');

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

  const stored = await page.evaluate(() => JSON.parse(localStorage.getItem('raiatea-reading-settings')));
  expect(stored).toEqual({
    theme: 'dark',
    size: '20',
    density: 'relaxed',
    width: '76',
    align: 'justify',
    motion: 'reduced'
  });

  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await expect(size).toHaveValue('20');
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

  await page.getByLabel('Animazioni').selectOption('reduced');
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
