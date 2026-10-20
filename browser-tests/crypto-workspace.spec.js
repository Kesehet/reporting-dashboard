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

async function mockBackend(page, job = fakeStatus.job) {
  await page.route('**/api/crypto/**', async route => {
    const path = new URL(route.request().url()).pathname;
    let payload;
    if (path.endsWith('/status')) payload = { ...fakeStatus, job };
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

async function openTab(page, width, job) {
  await page.setViewportSize({ width, height: 860 });
  page.on('request', request => { if (request.url().includes('/crypto/')) console.log('CRYPTO_REQUEST', request.method(), request.url()); });
  page.on('console', message => { if (message.type() === 'error') console.log('PAGE_ERROR', message.text()); });
  page.on('pageerror', error => console.log('PAGE_EXCEPTION', error.message));
  await mockBackend(page, job);
  await page.goto('/');
  // Dashboard startup briefly switches the entire page to a loading state.
  // Wait for its existing 1-second initialization timers before selecting a tab.
  await page.waitForTimeout(1300);
  if (width < 800) await page.locator('.report-sidebar > button').first().click();
  await page.getByRole('button', { name: 'Key Rotation', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Key Rotation', level: 1 })).toBeVisible();
  console.log('CRYPTO_PAGE_URL', page.url());
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
    expect(result.panels.length).toBeGreaterThanOrEqual(2);
    expect(result.scroll).toBeLessThanOrEqual(width + 2);
    for (const rect of result.panels) {
      expect(rect.left).toBeGreaterThanOrEqual(0);
      expect(rect.right).toBeLessThanOrEqual(result.viewport + 2);
      expect(rect.width).toBeGreaterThan(170);
    }
    await expect(page.getByText('synthetic-old-key-id')).toBeVisible();
    await expect(page.getByLabel('Administrator token')).toHaveCount(0);
    await expect(page.getByText('synthetic-old-key-id')).toBeVisible();
    const location = path.join(__dirname, 'screenshots', 'crypto-' + width + '.png');
    fs.mkdirSync(path.dirname(location), { recursive: true });
    await page.screenshot({ path: location, fullPage: true });
  });
}

test('real browser: two-button rotation starts without technical confirmation fields', async ({ page }) => {
  await openTab(page, 1280);
  await expect(page.getByRole('button', { name: 'Rotate', exact: true })).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Restore', exact: true })).toBeDisabled();
  await expect(page.getByLabel('Administrator token')).toHaveCount(0);
  await expect(page.getByLabel('Confirmation')).toHaveCount(0);
  await expect(page.getByLabel('Encrypted value')).toHaveCount(0);
  await expect(page.locator('[aria-label="Key rotation controls"] button')).toHaveCount(2);
  const call = page.waitForRequest(req => req.url().endsWith('/crypto/rotate') && req.method() === 'POST');
  await page.getByRole('button', { name: 'Rotate', exact: true }).click();
  await call;
  await expect(page.getByTestId('crypto-job-state')).toHaveText('starting');
  await expect(page.getByRole('button', { name: 'Rotate', exact: true })).toBeDisabled();
});

test('real browser: restore uses the last successful recovery snapshot', async ({ page }) => {
  await openTab(page, 1280, {
    state: 'completed', run_id: 'a'.repeat(32), processed: 125, updated: 100,
    preflight: { scanned: 125, values_to_rotate: 160, failures: 0 },
  });
  await expect(page.getByRole('button', { name: 'Restore', exact: true })).toBeEnabled();
  const call = page.waitForRequest(req => req.url().endsWith('/crypto/rollback') && req.method() === 'POST');
  await page.getByRole('button', { name: 'Restore', exact: true }).click();
  const request = await call;
  expect(JSON.parse(request.postData()).run_id).toBe('a'.repeat(32));
  await expect(page.getByTestId('crypto-job-state')).toHaveText('restoring');
});
