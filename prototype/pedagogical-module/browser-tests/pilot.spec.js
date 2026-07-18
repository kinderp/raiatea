const { test, expect } = require('@playwright/test');

test.describe('Raiatea pilot launcher', () => {
  test('opens the two-module journey and follows route navigation', async ({ page }) => {
    const consoleErrors = [];
    page.on('console', message => {
      if (message.type() === 'error') consoleErrors.push(message.text());
    });

    await page.goto('/index.html');
    await expect(page.getByRole('heading', { name: 'Raiatea: primo percorso pilot' })).toBeVisible();
    await expect(page.getByRole('link', { name: /1\. Query, key e value/ })).toHaveAttribute('href', 'query-key-value.html');
    await expect(page.getByRole('link', { name: /2\. Self-attention/ })).toHaveAttribute('href', 'self-attention.html');

    await page.getByRole('link', { name: 'Inizia il percorso' }).click();
    await expect(page).toHaveURL(/query-key-value\.html$/);
    await expect(page.getByRole('navigation', { name: 'Percorso pilot' })).toBeVisible();
    await page.getByRole('link', { name: /Self-attention/ }).click();
    await expect(page).toHaveURL(/self-attention\.html$/);
    await expect(page.getByRole('link', { name: /Query, key e value/ })).toBeVisible();
    await page.getByRole('link', { name: 'Indice del pilot' }).click();
    await expect(page).toHaveURL(/index\.html$/);

    expect(consoleErrors).toEqual([]);
  });
});
