import { expect, test } from "@playwright/test";
import { deflateSync } from "node:zlib";

const API = "http://localhost:8000/api/v1";

function crc32(data: Buffer): number {
  let crc = 0xffffffff;
  for (const byte of data) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function pngChunk(type: string, data: Buffer): Buffer {
  const name = Buffer.from(type, "ascii");
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length);
  const checksum = Buffer.alloc(4);
  checksum.writeUInt32BE(crc32(Buffer.concat([name, data])));
  return Buffer.concat([length, name, data, checksum]);
}

function phaseOneFixturePng(): Buffer {
  const width = 800;
  const height = 600;
  const pixels = Buffer.alloc((width * 3 + 1) * height);
  const color = (x: number, y: number, rgb: [number, number, number]) => {
    const offset = y * (width * 3 + 1) + 1 + x * 3;
    pixels[offset] = rgb[0]; pixels[offset + 1] = rgb[1]; pixels[offset + 2] = rgb[2];
  };
  for (let y = 0; y < height; y += 1) {
    pixels[y * (width * 3 + 1)] = 0;
    for (let x = 0; x < width; x += 1) color(x, y, [224, 232, 238]);
  }
  for (let y = 100; y < 300; y += 1) for (let x = 190; x < 610; x += 1) color(x, y, [20, 155, 105]);
  for (let y = 300; y < 520; y += 1) for (let x = 80; x < 720; x += 1) color(x, y, [25, 95, 210]);
  for (let y = 370; y < 455; y += 1) for (let x = 210; x < 335; x += 1) color(x, y, [220, 35, 55]);
  for (let step = 0; step < 170; step += 1) {
    const x = 430 + step;
    const centerY = 350 + Math.floor(step * 0.45);
    for (let offset = -7; offset <= 7; offset += 1) color(x, centerY + offset, [245, 125, 25]);
  }
  for (let step = 0; step < 115; step += 1) {
    const x = 345 + step;
    const centerY = 155 + step;
    for (let offset = -5; offset <= 5; offset += 1) color(x + offset, centerY, [125, 45, 185]);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0); ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 2;
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    pngChunk("IHDR", ihdr),
    pngChunk("IDAT", deflateSync(pixels)),
    pngChunk("IEND", Buffer.alloc(0)),
  ]);
}

test("reviewer runs Phase 1 analysis and preserves a correction", async ({ page, request }) => {
  const login = await request.post(`${API}/auth/login`, { data: { email: "admin@claimshield.local", password: "ClaimShield123!" } });
  expect(login.ok()).toBeTruthy();
  const token = (await login.json()).access_token as string;
  const headers = { Authorization: `Bearer ${token}` };
  const unique = Date.now().toString();
  const vehicle = await request.post(`${API}/vehicles`, { headers, data: { registration_number: `P1-${unique}`, vin: null, make: "Fixture", model: "Evaluation", year: 2026, color: "Blue" } });
  expect(vehicle.ok()).toBeTruthy();
  const vehicleId = (await vehicle.json()).id as string;
  const policy = await request.post(`${API}/policies`, { headers, data: { vehicle_id: vehicleId, policy_number: `P1-POL-${unique}`, start_date: "2026-01-01", end_date: "2026-12-31", status: "ACTIVE" } });
  expect(policy.ok()).toBeTruthy();
  const policyId = (await policy.json()).id as string;
  const claim = await request.post(`${API}/claims`, { headers, data: { policy_id: policyId, claim_number: `P1-CLM-${unique}`, incident_date: "2026-09-01T12:00:00Z", incident_location: "Synthetic evaluation", description: "Synthetic fixture used to verify the Phase 1 review workflow.", status: "EVIDENCE_PENDING" } });
  expect(claim.ok()).toBeTruthy();
  const claimId = (await claim.json()).id as string;
  const inspection = await request.post(`${API}/inspections`, { headers, data: { vehicle_id: vehicleId, policy_id: policyId, claim_id: claimId, type: "CLAIM" } });
  expect(inspection.ok()).toBeTruthy();
  const inspectionId = (await inspection.json()).id as string;
  const upload = await request.post(`${API}/inspections/${inspectionId}/media`, { headers, multipart: { viewpoint: "FRONT", file: { name: "phase-one-e2e.png", mimeType: "image/png", buffer: phaseOneFixturePng() } } });
  expect(upload.ok()).toBeTruthy();
  const submit = await request.post(`${API}/inspections/${inspectionId}/submit`, { headers: { ...headers, "Idempotency-Key": `e2e-foundation-${unique}` } });
  expect(submit.ok()).toBeTruthy();

  await page.goto("/login");
  await page.getByLabel("Email address").fill("admin@claimshield.local");
  await page.getByLabel("Password").fill("ClaimShield123!");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/dashboard/);
  await page.goto(`/inspections/${inspectionId}?claim=${claimId}`);
  const start = page.getByRole("button", { name: "Start analysis" });
  await expect(start).toBeEnabled({ timeout: 20_000 });
  await start.click();
  await expect(page.getByRole("cell", { name: "DENT", exact: true })).toBeVisible({ timeout: 30_000 });
  const dentRow = page.getByRole("row").filter({ hasText: "DENT" });
  await dentRow.getByRole("button", { name: "Review" }).click();
  await page.getByLabel("Review action").selectOption("CORRECT");
  await page.getByLabel("Corrected class").selectOption("SCRATCH");
  await page.getByLabel("Reviewer notes").fill("Verified correction in the browser workflow.");
  await page.getByRole("button", { name: "Save review version" }).click();
  await expect(dentRow.getByText("CORRECT v1")).toBeVisible();
});
