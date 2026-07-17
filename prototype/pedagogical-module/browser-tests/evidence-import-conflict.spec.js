const { test, expect } = require('@playwright/test');

const modulePath = '/self-attention.html';
const progressKey = 'raiatea-progress:self-attention-orientation';

function compatibleEvidence() {
  const titles = [
    'Usare la figura come mappa',
    'Dal testo agli embedding',
    'Arricchire ogni token con il contesto',
    'Passare ai calcoli interni'
  ];
  return {
    format: 'raiatea-learner-evidence',
    version: 1,
    module: {
      id: 'self-attention-orientation',
      title: 'Il ruolo della self-attention nel modello GPT',
      language: 'it',
      stepCount: titles.length
    },
    progress: {
      currentStep: 2,
      steps: titles.map((title, index) => ({
        index,
        title,
        attempts: index === 0 ? 2 : 0,
        correct: index === 0,
        usedRemediation: false,
        activityCompleted: false
      }))
    }
  };
}

async function selectThroughVisibleControl(page, document) {
  const chooserPromise = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Importa evidenze JSON' }).click();
  const chooser = await chooserPromise;
  await chooser.setFiles({
    name: 'compatible-evidence.json',
    mimeType: 'application/json',
    buffer: Buffer.from(JSON.stringify(document))
  });
}

test('invalidates a pending restore preview when local progress changes', async ({ page }) => {
  await page.goto(modulePath);
  await page.evaluate(() => localStorage.clear());
  await page.reload();

  await selectThroughVisibleControl(page, compatibleEvidence());
  await expect(page.locator('#evidenceImportPanel')).toBeVisible();
  await expect(page.locator('#confirmEvidenceImportBtn')).toBeEnabled();

  await page.locator('#nextBtn').click();

  await expect(page.locator('#evidenceImportPanel')).toBeHidden();
  await expect(page.locator('#confirmEvidenceImportBtn')).toBeDisabled();
  await expect(page.locator('#evidenceImportStatus')).toContainText('Avanzamento locale cambiato');
  await expect(page.locator('#evidenceImportStatus')).toContainText('seleziona di nuovo il file');

  const progress = await page.evaluate((key) => JSON.parse(localStorage.getItem(key)), progressKey);
  expect(progress.currentStep).toBe(1);
  expect(progress.steps.every((item) => item.attempts === 0 && item.correct === false)).toBe(true);
});
