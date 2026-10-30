const { chromium } = require('../frontend/node_modules/playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({
    channel: 'chrome',
    headless: true,
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  console.log('Navigating to Results Explorer...');
  await page.goto('http://localhost:3000/#f05_results_explorer', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  // 1. Open Settlements Drawer
  console.log('Opening Settlements Drawer...');
  const drawerBtn = await page.waitForSelector('#toggle-settlements-drawer-btn');
  await drawerBtn.click();
  await page.waitForTimeout(1000);

  // Capture screenshot with settlements drawer open
  const drawerScreenshotPath = path.resolve(__dirname, '../artifacts/screenshot_settlements_drawer.png');
  await page.screenshot({ path: drawerScreenshotPath });
  console.log(`Saved settlements drawer screenshot to ${drawerScreenshotPath}`);

  // 2. Click on map to trigger point-query popover
  console.log('Clicking map to inspect point...');
  await page.mouse.click(650, 420);
  await page.waitForTimeout(1500);

  const popoverScreenshotPath = path.resolve(__dirname, '../artifacts/screenshot_point_query.png');
  await page.screenshot({ path: popoverScreenshotPath });
  console.log(`Saved point query screenshot to ${popoverScreenshotPath}`);

  // 3. Test layer toggle
  console.log('Testing layer toggle...');
  const depthCheckbox = await page.$('input[type="checkbox"]');
  if (depthCheckbox) {
    await depthCheckbox.click();
    await page.waitForTimeout(500);
    await depthCheckbox.click();
  }

  // 4. Test Downloads Dropdown
  console.log('Testing Downloads Dropdown...');
  const dlBtn = await page.waitForSelector('#downloads-menu-btn');
  await dlBtn.click();
  await page.waitForTimeout(1000);

  const downloadsScreenshotPath = path.resolve(__dirname, '../artifacts/screenshot_downloads_menu.png');
  await page.screenshot({ path: downloadsScreenshotPath });
  console.log(`Saved downloads menu screenshot to ${downloadsScreenshotPath}`);

  // 5. Test Mobile view (360px viewport)
  console.log('Testing Mobile 360px view...');
  await page.setViewportSize({ width: 360, height: 740 });
  await page.waitForTimeout(1000);

  const mobileScreenshotPath = path.resolve(__dirname, '../artifacts/screenshot_results_mobile_360px.png');
  await page.screenshot({ path: mobileScreenshotPath });
  console.log(`Saved mobile 360px screenshot to ${mobileScreenshotPath}`);

  await browser.close();
  console.log('All tests and screenshots complete!');
})();
