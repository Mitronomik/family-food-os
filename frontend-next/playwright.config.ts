import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  forbidOnly: Boolean(process.env.CI),
  reporter: [
    ["list"],
    ["html", { open: "never" }],
    ["junit", { outputFile: "test-results/junit.xml" }],
  ],
  use: {
    baseURL: "http://127.0.0.1:3100",
    browserName: "chromium",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: [
    { command: "npm run start", url: "http://127.0.0.1:3100", reuseExistingServer: false },
    {
      command: "python3 frontend-next/e2e/serve_synthetic_backend.py",
      cwd: "..",
      url: "http://127.0.0.1:8000/health",
      env: { AI_ENABLED: "false", PYTHONPATH: "backend:." },
      reuseExistingServer: false,
      gracefulShutdown: { signal: "SIGTERM", timeout: 5000 },
    },
  ],
});
