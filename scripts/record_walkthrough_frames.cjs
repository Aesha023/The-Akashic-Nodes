const { chromium } = require('../frontend/node_modules/playwright');
const path = require('path');
const fs = require('fs');

async function recordWalkthroughFrames() {
  const framesDir = path.resolve(__dirname, '../artifacts/walkthrough_frames');
  if (!fs.existsSync(framesDir)) {
    fs.mkdirSync(framesDir, { recursive: true });
  }

  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });

  const page = await context.newPage();

  console.log('Frame 01: Sign-in');
  await page.goto('http://127.0.0.1:3000/#signin', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(framesDir, 'frame_01_00s_signin.png') });

  // Quick sign in as Analyst
  const analystBtn = page.getByRole('button', { name: 'Analyst', exact: true });
  if (await analystBtn.count() > 0 && await analystBtn.isVisible()) {
    await analystBtn.click();
    await page.waitForTimeout(400);
  }
  const submitBtn = page.locator('button[type="submit"]');
  if (await submitBtn.count() > 0 && await submitBtn.isVisible()) {
    await submitBtn.click();
    await page.waitForTimeout(1500);
  }

  console.log('Frame 02: Home Overview');
  await page.goto('http://127.0.0.1:3000/#home', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(framesDir, 'frame_02_05s_home.png') });

  console.log('Frame 03: Results Explorer Full Map');
  await page.goto('http://127.0.0.1:3000/#f05_results_explorer', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(framesDir, 'frame_03_10s_results_explorer.png') });

  console.log('Frame 04: Results Explorer Point Query');
  await page.mouse.click(750, 480);
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(framesDir, 'frame_04_15s_point_query.png') });

  console.log('Frame 05: Results Explorer Settlements Drawer');
  const settlementsBtn = page.locator('#toggle-settlements-drawer-btn');
  if (await settlementsBtn.count() > 0 && await settlementsBtn.isVisible()) {
    await settlementsBtn.click();
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(framesDir, 'frame_05_18s_settlements_drawer.png') });
    const closeBtn = page.locator('button[aria-label="Close drawer"]');
    if (await closeBtn.count() > 0 && await closeBtn.isVisible()) {
      await closeBtn.click();
      await page.waitForTimeout(600);
    }
  }

  console.log('Frame 06: Results Explorer Downloads Menu');
  const downloadBtn = page.locator('button:has-text("Download")');
  if (await downloadBtn.isVisible()) {
    await downloadBtn.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(framesDir, 'frame_06_22s_downloads_menu.png') });
    await page.mouse.click(400, 200);
    await page.waitForTimeout(600);
  }

  console.log('Frame 07: Impact Analysis');
  await page.goto('http://127.0.0.1:3000/#f09_impact', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(framesDir, 'frame_07_25s_impact_analysis.png') });

  console.log('Frame 08: Evacuation Router');
  await page.goto('http://127.0.0.1:3000/#f10_evacuation', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(framesDir, 'frame_08_30s_evacuation_routes.png') });

  await page.close();
  await context.close();
  await browser.close();
  console.log('All walkthrough frames captured successfully in artifacts/walkthrough_frames!');
}

recordWalkthroughFrames().catch(err => {
  console.error('Walkthrough frames capture error:', err);
  process.exit(1);
});
