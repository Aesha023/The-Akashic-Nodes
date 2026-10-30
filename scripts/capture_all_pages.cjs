const { chromium } = require('../frontend/node_modules/playwright');
const path = require('path');
const fs = require('fs');

const PAGES = [
  { id: 'landing', name: 'landing' },
  { id: 'home', name: 'home' },
  { id: 'signin', name: 'signin' },
  { id: 'f01_mission_control', name: 'f01_mission_control' },
  { id: 'f02_new_scenario', name: 'f02_new_scenario' },
  { id: 'f04_run_monitor', name: 'f04_run_monitor' },
  { id: 'f05_results_explorer', name: 'f05_results_explorer' },
  { id: 'f06_engine_comparison', name: 'f06_engine_comparison' },
  { id: 'f07_satellite_validation', name: 'f07_satellite_validation' },
  { id: 'f08_live_flood', name: 'f08_live_flood' },
  { id: 'f09_impact', name: 'f09_impact' },
  { id: 'f10_evacuation', name: 'f10_evacuation' },
  { id: 'f11_cascade', name: 'f11_cascade' },
  { id: 'f14_library', name: 'f14_library' },
  { id: 'f15_batch', name: 'f15_batch' },
  { id: 'f16_lake_watch', name: 'f16_lake_watch' },
  { id: 'f17_alerts', name: 'f17_alerts' },
  { id: 'f18_catalogue', name: 'f18_catalogue' },
  { id: 'f19_benchmarks', name: 'f19_benchmarks' },
  { id: 'f20_health', name: 'f20_health' },
  { id: 'f21_audit', name: 'f21_audit' },
  { id: 'f22_admin', name: 'f22_admin' },
  { id: 'f12_exports', name: 'f12_exports' },
];

const OUT_DIR = path.resolve(__dirname, '../artifacts/screenshots');
if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

(async () => {
  const browser = await chromium.launch({
    channel: 'chrome',
    headless: true,
  });

  console.log(`Starting full-suite screenshot capture across ${PAGES.length} pages...`);

  // 1. Capture Desktop (Presentation mode)
  console.log('Capturing Desktop Presentation Mode...');
  const ctxPres = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  // Set demo mode in localStorage
  await ctxPres.addInitScript(() => {
    localStorage.setItem('pravahx_demo_mode', 'true');
  });
  const pagePres = await ctxPres.newPage();

  for (const p of PAGES) {
    const url = `http://127.0.0.1:3000/#${p.id}`;
    try {
      await pagePres.goto(url, { waitUntil: 'domcontentloaded' });
      await pagePres.waitForTimeout(1000);
      const outPath = path.join(OUT_DIR, `desktop_pres_${p.name}.png`);
      await pagePres.screenshot({ path: outPath, fullPage: false });
      console.log(`Captured: desktop_pres_${p.name}.png`);
    } catch (err) {
      console.error(`Error on ${p.name}:`, err.message);
    }
  }
  await ctxPres.close();

  // 2. Capture Desktop (Operational mode)
  console.log('Capturing Desktop Operational Mode...');
  const ctxOp = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctxOp.addInitScript(() => {
    localStorage.setItem('pravahx_demo_mode', 'false');
  });
  const pageOp = await ctxOp.newPage();

  for (const p of PAGES) {
    const url = `http://127.0.0.1:3000/#${p.id}`;
    try {
      await pageOp.goto(url, { waitUntil: 'domcontentloaded' });
      await pageOp.waitForTimeout(1000);
      const outPath = path.join(OUT_DIR, `desktop_op_${p.name}.png`);
      await pageOp.screenshot({ path: outPath, fullPage: false });
      console.log(`Captured: desktop_op_${p.name}.png`);
    } catch (err) {
      console.error(`Error on ${p.name}:`, err.message);
    }
  }
  await ctxOp.close();

  // 3. Capture Mobile 360px Viewport (Presentation mode)
  console.log('Capturing Mobile 360px Viewport...');
  const ctxMob = await browser.newContext({ viewport: { width: 360, height: 740 } });
  await ctxMob.addInitScript(() => {
    localStorage.setItem('pravahx_demo_mode', 'true');
  });
  const pageMob = await ctxMob.newPage();

  for (const p of PAGES) {
    const url = `http://127.0.0.1:3000/#${p.id}`;
    try {
      await pageMob.goto(url, { waitUntil: 'domcontentloaded' });
      await pageMob.waitForTimeout(1000);
      const outPath = path.join(OUT_DIR, `mobile_360px_${p.name}.png`);
      await pageMob.screenshot({ path: outPath, fullPage: false });
      console.log(`Captured: mobile_360px_${p.name}.png`);
    } catch (err) {
      console.error(`Error on ${p.name}:`, err.message);
    }
  }
  await ctxMob.close();

  await browser.close();
  console.log('All screenshots captured successfully!');
})();

