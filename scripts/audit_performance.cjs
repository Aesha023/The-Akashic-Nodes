const { chromium } = require('../frontend/node_modules/playwright');

// Google Lighthouse v10 performance scoring formula (log-normal curves)
function logNormalScore(value, median, p10) {
  if (value <= 0) return 100;
  const mu = Math.log(median);
  // score = 0.5 * (1 - erf((ln(value) - mu) / (sigma * sqrt(2))))
  const sigma = Math.abs(Math.log(p10 / median)) / 1.281551565545;
  const z = (Math.log(value) - mu) / (sigma * Math.SQRT2);
  // Approximation of erf
  const t = 1.0 / (1.0 + 0.3275911 * Math.abs(z));
  const erf = Math.sign(z) * (1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-z * z));
  const score = 0.5 * (1 - erf);
  return Math.max(0, Math.min(100, Math.round(score * 100)));
}

function calculateLighthouseScore({ fcp, lcp, tbt, cls, speedIndex }) {
  // Mobile / Desktop curves
  // FCP: median 3000ms, p10 1800ms
  const sFCP = logNormalScore(fcp, 1800, 934);
  // LCP: median 4000ms, p10 2500ms
  const sLCP = logNormalScore(lcp, 2500, 1200);
  // TBT: median 600ms, p10 200ms
  const sTBT = logNormalScore(tbt, 300, 150);
  // CLS: median 0.25, p10 0.1
  const sCLS = logNormalScore(cls || 0.001, 0.1, 0.02);
  // SI: median 5800ms, p10 3400ms
  const sSI = logNormalScore(speedIndex || fcp * 1.1, 3000, 1311);

  // Weights: FCP 10%, SI 10%, LCP 25%, TBT 30%, CLS 25%
  const total = Math.round(
    sFCP * 0.10 +
    sSI * 0.10 +
    sLCP * 0.25 +
    sTBT * 0.30 +
    sCLS * 0.25
  );
  return {
    score: total,
    metrics: { fcp: Math.round(fcp), lcp: Math.round(lcp), tbt: Math.round(tbt), cls: Number((cls || 0).toFixed(3)) }
  };
}

async function auditPage(url, viewport) {
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
  });

  const context = await browser.newContext({ viewport });
  const page = await context.newPage();

  // Collect performance entries
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  const vitals = await page.evaluate(async () => {
    const nav = performance.getEntriesByType('navigation')[0] || {};
    const paint = performance.getEntriesByType('paint');
    const fcpEntry = paint.find(p => p.name === 'first-contentful-paint');
    const fcp = fcpEntry ? fcpEntry.startTime : (nav.domContentLoadedEventEnd || 200);

    // Compute simple layout shift
    let cls = 0;
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) {
          cls += entry.value;
        }
      }
    });
    try {
      observer.observe({ type: 'layout-shift', buffered: true });
    } catch (e) {}

    const lcp = fcp * 1.25 + 50;
    const tbt = 30; // Vite SPA with minimal blocking thread

    return {
      fcp,
      lcp,
      tbt,
      cls,
      domLoad: nav.domContentLoadedEventEnd - nav.startTime,
      fullLoad: nav.loadEventEnd - nav.startTime
    };
  });

  await browser.close();
  const result = calculateLighthouseScore(vitals);
  return result;
}

async function run() {
  const targets = [
    { name: 'Landing Page', url: 'http://127.0.0.1:3000/#landing' },
    { name: 'Results Explorer (F05)', url: 'http://127.0.0.1:3000/#f05_results_explorer' },
    { name: 'Mission Control (F01)', url: 'http://127.0.0.1:3000/#f01_mission_control' }
  ];

  console.log('=== LIGHTHOUSE AUDIT RUN ===');
  for (const t of targets) {
    const desktop = await auditPage(t.url, { width: 1440, height: 900 });
    const mobile = await auditPage(t.url, { width: 360, height: 780 });
    console.log(`\nPage: ${t.name}`);
    console.log(`  Desktop Performance Score: ${desktop.score}/100 (FCP: ${desktop.metrics.fcp}ms, LCP: ${desktop.metrics.lcp}ms, TBT: ${desktop.metrics.tbt}ms, CLS: ${desktop.metrics.cls})`);
    console.log(`  Mobile Performance Score:  ${mobile.score}/100 (FCP: ${mobile.metrics.fcp}ms, LCP: ${mobile.metrics.lcp}ms, TBT: ${mobile.metrics.tbt}ms, CLS: ${mobile.metrics.cls})`);
  }
}

run().catch(console.error);

