const { test, expect } = require('@playwright/test');

// No backend is used here; inject synthetic browser-only identity for layout tests.
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'synthetic-browser-session');
    localStorage.setItem('tokenExpiration', String(Date.now() + 3600000));
    localStorage.setItem('display_name', 'Test User');
  });
});
const fs = require('fs');
const path = require('path');
// Real chart HTTP responses with deferred cells resolved against synthetic SQL data.
const fixture = require('./fixtures/business-summary.json');

test('business summary shows whole application counts and unique product codes', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.route('**/api/**', route => {
    const pathname = decodeURIComponent(new URL(route.request().url()).pathname);
    let payload = [];
    if (pathname.endsWith('/Business Account Summary Number Of Apps Table')) payload = fixture.apps;
    else if (pathname.endsWith('/Business Account Summary Top 10 Products Table')) payload = fixture.products;
    else if (pathname.includes('/charts/')) payload = { headers: ['-', 'Total'], rows: [['No data', 0]] };
    else if (pathname.endsWith('/metrics')) payload = {};
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify(payload) });
  });
  await page.goto('/');
  await page.waitForTimeout(1300);
  await page.getByRole('button', { name: 'Business Accounts Summary', exact: true }).click();
  const apps = page.locator('.p-card').filter({ has: page.locator('.p-card-title', { hasText: 'Number Of Applications by Product Type' }) }).first();
  const products = page.locator('.p-card').filter({ has: page.locator('.p-card-title', { hasText: 'Top 10 Products' }) }).first();
  await expect(apps.locator('tbody tr')).toHaveCount(27);
  await expect(apps.locator('tbody tr').last()).toContainText('54');
  const values = await apps.locator('tbody td:not(:first-child)').allTextContents();
  expect(values).toHaveLength(81);
  for (const value of values) expect(value.trim()).toBe('54');
  await expect(products.locator('tbody tr')).toHaveCount(3);
  const codes = await products.locator('tbody tr td:nth-child(2)').allTextContents();
  expect(codes).toEqual(['20903', '20601', '101']);
  expect(new Set(codes).size).toBe(codes.length);
  expect(await products.locator('tbody tr td:nth-child(3)').allTextContents()).toEqual(['91', '31', '8']);
  const directory = path.join(__dirname, 'screenshots');
  fs.mkdirSync(directory, { recursive: true });
  await apps.screenshot({ path: path.join(directory, 'business-summary-whole-counts.png') });
  await products.screenshot({ path: path.join(directory, 'business-summary-unique-products.png') });
});
