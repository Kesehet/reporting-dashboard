const { defineConfig } = require('@playwright/test');
const path = require('path');
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
    command: 'python3 -m http.server 4173 --bind 127.0.0.1 --directory ' + JSON.stringify(path.resolve(__dirname, '../build')),
    url: 'http://127.0.0.1:4173/',
    reuseExistingServer: false,
    cwd: path.resolve(__dirname, '..'),
    timeout: 120000,
  },
});
