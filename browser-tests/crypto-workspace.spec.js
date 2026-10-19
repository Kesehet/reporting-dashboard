const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const fakeStatus = {
  keyring: {
    current_id: 'synthetic-active-key-id',
    keys: [
      { id: 'synthetic-old-key-id', algorithm: 'AES_ECB_PKCS7', active: false },
      { id: 'synthetic-active-key-id', algorithm: 'AES_GCM', active: true },
    ],
  },
  job: { state: 'idle', processed: 0, updated: 0 },
};

async function mockBackend(page) {
  await page.route('**/api/crypto/**', async route => {
    const path = new URL(route.request().url()).pathname;
    const authed = route.request().headers()['x-crypto-admin-token'] === 'A'.repeat(36);
    if (!authed) {
      return route.fulfill({ status: 403, contentType: 'application/json',
        body: JSON.stringify({ error: 'Administrator authorization required' }) });
    }
    let payload;
    if (path.endsWith('/status')) payload = fakeStatus;
    else if (path.endsWith('/preflight')) {
      payload = { ready: true, scanned: 125, values_to_rotate: 160, failures: 0, examples: [] };
    } else if (path.endsWith('/decrypt')) payload = { plaintext: 'SYNTHETIC_SECRET_123' };
    else if (path.endsWith('/keys/rotate')) payload = { key_id: 'synthetic-next-key-id' };
    else if (path.endsWith('/start')) payload = { state: 'starting', run_id: 'a'.repeat(32) };
    else if (path.endsWith('/rollback')) payload = { state: 'starting', run_id: 'a'.repeat(32) };
    else payload = { error: 'Unknown mock request' };
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(payload) });
  });
}

async function openTab(page, width) {
  await page.setViewportSize({ width, height: 860 });
  await mockBackend(page);
  await page.goto('/');
  // Dashboard startup briefly switches the entire page to a loading state.
  // Wait for its existing 1-second initialization timers before selecting a tab.
  await page.waitForTimeout(1300);
  if (width < 800) await page.locator('.report-sidebar > button').first().click();
  await page.getByRole('button', { name: 'Crypto & Key Rotation', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Encryption & Key Rotation' })).toBeVisible();
}

for (const width of [375, 768, 1440]) {
  test('responsive crypto workspace at ' + width + 'px', async ({ page }) => {
    await openTab(page, width);
    const result = await page.evaluate(() => {
      const panels = [...document.querySelectorAll('.crypto-panel')];
      const viewport = document.documentElement.clientWidth;
      return {
        viewport,
        scroll: document.documentElement.scrollWidth,
        panels: panels.map(item => {
          const rect = item.getBoundingClientRect();
          return { left: rect.left, right: rect.right, width: rect.width };
        }),
      };
    });
    expect(result.panels.length).toBeGreaterThanOrEqual(3);
    expect(result.scroll).toBeLessThanOrEqual(width + 2);
    for (const rect of result.panels) {
      expect(rect.left).toBeGreaterThanOrEqual(0);
      expect(rect.right).toBeLessThanOrEqual(result.viewport + 2);
      expect(rect.width).toBeGreaterThan(170);
    }
    await page.getByLabel('Administrator token').fill('A'.repeat(36));
    await expect(page.getByText('Connected')).toBeVisible();
    await expect(page.getByText('synthetic-old-key-id')).toBeVisible();
    const location = path.join(__dirname, 'screenshots', 'crypto-' + width + '.png');
    fs.mkdirSync(path.dirname(location), { recursive: true });
    await page.screenshot({ path: location, fullPage: true });
  });
}

test('real browser: decrypt is masked; preflight must run before migrate', async ({ page }) => {
  await openTab(page, 1280);
  await expect(page.getByRole('button', { name: 'Start checked migration' })).toBeDisabled();
  const tokenInput = page.getByLabel('Administrator token');
  await tokenInput.fill('A'.repeat(36));
  await expect(page.getByText('Connected')).toBeVisible();
  await page.getByLabel('Encrypted value').fill('synthetic-ciphertext');
  await page.getByRole('button', { name: 'Decrypt value' }).click();
  await expect(page.getByLabel('Decryption result')).toHaveText('••••••••••••••••');
  await page.getByRole('button', { name: 'Reveal' }).click();
  await expect(page.getByLabel('Decryption result')).toHaveText('SYNTHETIC_SECRET_123');
  await page.getByLabel('Encrypted value').fill('new-value');
  await expect(page.getByLabel('Decryption result')).toHaveCount(0);
  await page.getByRole('button', { name: 'Run read-only preflight' }).click();
  await expect(page.getByText(/125 rows scanned/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Start checked migration' })).toBeDisabled();
  await page.getByLabel(/Type the exact confirmation required/).fill('MIGRATE_PII');
  await expect(page.getByRole('button', { name: 'Start checked migration' })).toBeEnabled();
  await page.getByRole('button', { name: 'Start checked migration' }).click();
  await expect(page.getByTestId('crypto-job-state')).toHaveText('starting');
  await page.getByRole('button', { name: 'Clear session' }).click();
  await expect(tokenInput).toHaveValue('');
});
