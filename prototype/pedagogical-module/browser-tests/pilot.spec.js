const { test, expect } = require('@playwright/test');

test('launcher opens the canonical two-module route with working relative navigation', async ({ page }) => {
  const requests = [];
  page.on('request', request => requests.push(request.url()));

  await page.goto('/index.html');
  await expect(page.getByRole('heading', { name: 'Raiatea: primo percorso pilot' })).toBeVisible();
  await expect(page.getByRole('link', { name: /^1\. Il ruolo della self-attention/ })).toHaveAttribute('href', 'self-attention.html');
  await expect(page.getByRole('link', { name: /^2\. Query, Key e Value/ })).toHaveAttribute('href', 'query-key-value.html');

  await page.getByRole('link', { name: 'Inizia il percorso' }).click();
  await expect(page).toHaveURL(/\/self-attention\.html$/);
  await expect(page.locator('h1').first()).toContainText('Il ruolo della self-attention nel modello GPT');

  const firstRoute = page.getByRole('navigation', { name: 'Percorso pilot' });
  await expect(firstRoute.getByRole('link', { name: 'Indice del pilot' })).toHaveAttribute('href', 'index.html');
  await firstRoute.getByRole('link', { name: /Query, Key e Value nella self-attention/ }).click();

  await expect(page).toHaveURL(/\/query-key-value\.html$/);
  await expect(page.locator('h1').first()).toContainText('Query, Key e Value nella self-attention');
  const secondRoute = page.getByRole('navigation', { name: 'Percorso pilot' });
  await expect(secondRoute.getByRole('link', { name: /Il ruolo della self-attention nel modello GPT/ })).toHaveAttribute('href', 'self-attention.html');
  await secondRoute.getByRole('link', { name: 'Indice del pilot' }).click();
  await expect(page).toHaveURL(/\/index\.html$/);

  expect(requests.every(url => url.startsWith('http://127.0.0.1:4173/'))).toBe(true);
});
