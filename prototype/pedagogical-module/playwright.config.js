const { defineConfig } = require('@playwright/test');

const host = '127.0.0.1';
const port = 4173;
const baseURL = `http://${host}:${port}`;

module.exports = defineConfig({
  testDir: './browser-tests',
  fullyParallel: false,
  workers: 1,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL,
    browserName: 'chromium',
    trace: 'retain-on-failure'
  },
  webServer: {
    command: [
      'rm -rf .browser-artifacts',
      '&& python build/build_pilot.py --output .browser-artifacts',
      `&& python -m http.server ${port} --bind ${host} --directory .browser-artifacts`
    ].join(' '),
    url: `${baseURL}/index.html`,
    reuseExistingServer: !process.env.CI,
    timeout: 120000
  }
});
