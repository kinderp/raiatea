const { test, expect } = require('@playwright/test');

const modulePath = '/self-attention.html';
const progressKey = 'raiatea-progress:self-attention-orientation';

function evidenceDocument({ currentStep, attempts, correct }) {
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
      currentStep,
      steps: titles.map((title, index) => ({
        index,
        title,
        attempts: index === currentStep ? attempts : 0,
        correct: index === currentStep ? correct : false,
        usedRemediation: false,
        activityCompleted: false
      }))
    }
  };
}

async function selectEvidenceFile(page, document, name) {
  await page.locator('#importEvidenceInput').setInputFiles({
    name,
    mimeType: 'application/json',
    buffer: Buffer.from(JSON.stringify(document))
  });
}

test('keeps only the latest evidence selection when file reads finish out of order', async ({ page }) => {
  await page.goto(modulePath);
  await page.evaluate(() => localStorage.clear());
  await page.reload();

  await page.evaluate(() => {
    const originalText = File.prototype.text;
    File.prototype.text = function delayedText() {
      const delay = this.name === 'slow.json' ? 180 : 0;
      return new Promise((resolve, reject) => {
        setTimeout(() => originalText.call(this).then(resolve, reject), delay);
      });
    };
  });

  await selectEvidenceFile(page, evidenceDocument({ currentStep: 3, attempts: 9, correct: true }), 'slow.json');
  await selectEvidenceFile(page, evidenceDocument({ currentStep: 1, attempts: 1, correct: true }), 'latest.json');

  await expect(page.locator('#evidenceImportPreview')).toContainText('File selezionato: 1/4 verifiche, 1 tentativi');
  await page.waitForTimeout(250);
  await expect(page.locator('#evidenceImportPreview')).toContainText('File selezionato: 1/4 verifiche, 1 tentativi');

  await page.getByRole('button', { name: 'Ripristina questo avanzamento' }).click();
  const restored = await page.evaluate((key) => JSON.parse(localStorage.getItem(key)), progressKey);
  expect(restored.currentStep).toBe(1);
  expect(restored.steps[1]).toEqual({
    attempts: 1,
    correct: true,
    usedRemediation: false,
    activityCompleted: false
  });
  expect(restored.steps[3].attempts).toBe(0);
});
