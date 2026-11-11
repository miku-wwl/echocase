import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  reporter: [
    ["list"],
    [
      "json",
      {
        outputFile: `${process.env.ECHOCASE_BROWSER_EVIDENCE ?? "../evidence/browser"}/results.json`,
      },
    ],
    ["html", { open: "never" }],
  ],
  use: {
    baseURL: process.env.ECHOCASE_BASE_URL ?? "http://127.0.0.1:5173",
    channel: process.env.CI ? "chromium" : "msedge",
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "edge",
      use: {
        ...devices["Desktop Edge"],
        viewport: { width: 1440, height: 1000 },
      },
    },
  ],
});
