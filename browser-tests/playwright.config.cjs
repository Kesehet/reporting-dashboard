const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: __dirname,
  testMatch: ['*.spec.js'],
  timeout: 30000,
  expect: { timeout: 10000 },
  workers: 1,
  retries: 1,
  use: {
    baseURL: 'http://127.0.0.1:4173/',
    browserName: 'chromium',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npx serve -s build -l 4173',
    url: 'http://127.0.0.1:4173/',
    reuseExistingServer: false,
    timeout: 120000,
  },
});
