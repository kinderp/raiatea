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
      'python build/build_module.py examples/self-attention.json',
      '--output .browser-artifacts/self-attention.html',
      `&& python -m http.server ${port} --bind ${host} --directory .browser-artifacts`
    ].join(' '),
    url: `${baseURL}/self-attention.html`,
    reuseExistingServer: !process.env.CI,
    timeout: 120000
  }
});
