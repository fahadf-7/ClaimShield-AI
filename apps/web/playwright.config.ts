import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000/login",
    reuseExistingServer: true,
  },
  projects: [
    { name: "desktop-edge", use: { ...devices["Desktop Chrome"], channel: "msedge" } },
    { name: "mobile-edge", use: { ...devices["Pixel 7"], channel: "msedge" } },
    {
      name: "mobile-edge-landscape",
      use: {
        ...devices["Pixel 7"],
        channel: "msedge",
        viewport: { width: 844, height: 390 },
      },
    },
  ],
});
