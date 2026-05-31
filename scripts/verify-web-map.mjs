import { createRequire } from "node:module";
import { mkdir } from "node:fs/promises";

const require = createRequire(import.meta.url);
const playwrightPackage = process.env.PLAYWRIGHT_PACKAGE || "playwright";
const { chromium } = require(playwrightPackage);

const url = process.env.URL || "http://127.0.0.1:9000/";
const outDir = process.env.OUT_DIR || "/tmp/cable-world-web-map";

async function waitForGodot(page) {
  await page.goto(url, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("canvas", { timeout: 60000 });
  await page.waitForTimeout(8000);
}

async function screenshot(page, name) {
  const path = `${outDir}/${name}.png`;
  await page.screenshot({ path, fullPage: false });
  console.log(path);
}

async function zoomAndScreenshot(page, name, zoomName, wheelDelta) {
  await page.mouse.wheel(0, wheelDelta);
  await page.waitForTimeout(700);
  await screenshot(page, `${name}-${zoomName}`);
}

async function runViewport(browser, name, viewport, markerPoint) {
  const page = await browser.newPage({ viewport, deviceScaleFactor: 1 });
  await waitForGodot(page);
  await screenshot(page, `${name}-initial`);

  if (name.startsWith("mobile-")) {
    await zoomAndScreenshot(page, name, "zoom-150", -420);
    await zoomAndScreenshot(page, name, "zoom-200", -420);
  }

  if (markerPoint) {
    await page.mouse.click(markerPoint.x, markerPoint.y);
    await page.waitForTimeout(700);
    await screenshot(page, `${name}-after-marker-click`);
  }

  const cx = Math.round(viewport.width * 0.5);
  const cy = Math.round(viewport.height * 0.5);
  await page.mouse.move(cx, cy);
  await page.mouse.down();
  await page.mouse.move(cx + Math.round(viewport.width * 0.26), cy - Math.round(viewport.height * 0.08), { steps: 12 });
  await page.mouse.up();
  await page.waitForTimeout(700);
  await screenshot(page, `${name}-after-drag`);
  await page.close();
}

await mkdir(outDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
try {
  await runViewport(browser, "mobile-390x844", { width: 390, height: 844 }, { x: 202, y: 382 });
  await runViewport(browser, "desktop-1280x800", { width: 1280, height: 800 }, { x: 340, y: 140 });
} finally {
  await browser.close();
}
