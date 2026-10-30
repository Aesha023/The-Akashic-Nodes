const { chromium } = require('../frontend/node_modules/playwright');
const path = require('path');
const fs = require('fs');

async function recordWalkthrough() {
  const videoDir = path.resolve(__dirname, '../artifacts/videos');
  if (!fs.existsSync(videoDir)) {
    fs.mkdirSync(videoDir, { recursive: true });
  }

  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: {
      dir: videoDir,
      size: { width: 1440, height: 900 }
    }
  });

  const page = await context.newPage();

  console.log('1. Navigating to Sign-in...');
  await page.goto('http://127.0.0.1:3000/#signin', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  // Click Analyst quick-login pill
  const analystBtn = page.locator('button:has-text("Analyst")');
  if (await analystBtn.isVisible()) {
    await analystBtn.click();
    await page.waitForTimeout(800);
  }
  const submitBtn = page.locator('button[type="submit"]');
  if (await submitBtn.isVisible()) {
    await submitBtn.click();
    await page.waitForTimeout(2000);
  }

  console.log('2. Viewing Home Overview...');
  await page.goto('http://127.0.0.1:3000/#home', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);

  console.log('3. Navigating to Results Explorer (F05)...');
  await page.goto('http://127.0.0.1:3000/#f05_results_explorer', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  // Toggle a layer checkbox
  const roadsToggle = page.locator('text=Flooded Roads');
  if (await roadsToggle.isVisible()) {
    await roadsToggle.click();
    await page.waitForTimeout(1000);
    await roadsToggle.click();
    await page.waitForTimeout(1000);
  }

  // Click on the map to trigger point query popover
  console.log('Clicking map for depth point query...');
  await page.mouse.click(750, 480);
  await page.waitForTimeout(2500);

  // Open Settlements Drawer
  console.log('Opening Settlements Drawer...');
  const settlementsBtn = page.locator('button:has-text("Settlements")');
  if (await settlementsBtn.isVisible()) {
    await settlementsBtn.click();
    await page.waitForTimeout(2500);
    // Click close or minimize
    const closeBtn = page.locator('button[aria-label="Close drawer"]');
    if (await closeBtn.isVisible()) {
      await closeBtn.click();
      await page.waitForTimeout(800);
    }
  }

  // Open Downloads Menu
  console.log('Opening Downloads Menu...');
  const downloadBtn = page.locator('button:has-text("Download")');
  if (await downloadBtn.isVisible()) {
    await downloadBtn.click();
    await page.waitForTimeout(2500);
    // Click outside to dismiss
    await page.mouse.click(400, 200);
    await page.waitForTimeout(1000);
  }

  console.log('4. Navigating to Impact Analysis (F09)...');
  await page.goto('http://127.0.0.1:3000/#f09_impact', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3500);

  // Scroll down to view tables and economic loss honest card
  await page.evaluate(() => window.scrollBy({ top: 400, behavior: 'smooth' }));
  await page.waitForTimeout(2500);

  console.log('5. Navigating to Evacuation Router (F10)...');
  await page.goto('http://127.0.0.1:3000/#f10_evacuation', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3500);

  // Click route item
  const routeItem = page.locator('div:has-text("Route EV-01")').first();
  if (await routeItem.isVisible()) {
    await routeItem.click();
    await page.waitForTimeout(2000);
  }

  console.log('6. Concluding walkthrough...');
  await page.waitForTimeout(2000);

  await page.close();
  await context.close();
  await browser.close();

  // Find the generated video file and copy to artifacts/recording_walkthrough.webm
  const files = fs.readdirSync(videoDir).filter(f => f.endsWith('.webm'));
  if (files.length > 0) {
    const latestFile = path.join(videoDir, files[files.length - 1]);
    const targetFile = path.resolve(__dirname, '../artifacts/recording_walkthrough.webm');
    fs.copyFileSync(latestFile, targetFile);
    console.log(`Video recorded successfully and saved to ${targetFile}`);
  }
}

recordWalkthrough().catch(err => {
  console.error('Walkthrough recording error:', err);
  process.exit(1);
});
