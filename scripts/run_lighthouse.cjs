/**
 * Lighthouse CLI execution runner for PravahX production preview.
 * Runs Lighthouse 13.6.0 on landing, results explorer, and mission control (desktop + mobile).
 */

const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
process.env.CHROME_PATH = CHROME_PATH;

const OUT_DIR = path.resolve(__dirname, '..', 'artifacts', 'lighthouse');
if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

const LH_CLI = path.resolve(__dirname, '..', 'frontend', 'node_modules', 'lighthouse', 'cli', 'index.js');

const TARGETS = [
  { name: 'landing', url: 'http://127.0.0.1:4173/#landing' },
  { name: 'results', url: 'http://127.0.0.1:4173/#f05_results_explorer' },
  { name: 'mission_control', url: 'http://127.0.0.1:4173/#f01_mission_control' },
];

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const frontendDir = path.resolve(__dirname, '..', 'frontend');

async function waitForServer(url, timeoutMs = 15000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url);
      if (res.ok) return true;
    } catch (e) {}
    await sleep(500);
  }
  throw new Error(`Timeout waiting for server at ${url}`);
}

async function main() {
  console.log(`[INFO] Starting production preview server on port 4173 from ${frontendDir}...`);
  const previewProcess = spawn('npx.cmd', ['vite', 'preview', '--host', '127.0.0.1', '--port', '4173', '--strictPort'], {
    cwd: frontendDir,
    stdio: 'ignore',
    shell: true,
  });

  await waitForServer('http://127.0.0.1:4173/');
  console.log('[INFO] Production preview server is UP and responding.');

  const results = {};

  for (const target of TARGETS) {
    for (const preset of ['desktop', 'mobile']) {
      const runKey = `${target.name}_${preset}`;
      const outBase = path.join(OUT_DIR, runKey);
      console.log(`\n[LIGHTHOUSE] Running ${runKey} -> ${target.url}`);

      const args = [
        LH_CLI,
        target.url,
        `--output=json,html`,
        `--output-path=${outBase}`,
        `--chrome-flags="--headless --no-sandbox --disable-gpu --disable-dev-shm-usage"`,
        `--quiet`,
      ];

      if (preset === 'desktop') {
        args.push(`--preset=desktop`);
      } else {
        args.push(`--form-factor=mobile`);
      }

      const cmd = `node ${args.join(' ')}`;
      try {
        execSync(cmd, {
          env: { ...process.env, CHROME_PATH },
          stdio: 'inherit',
          timeout: 90000,
        });

        const jsonFile = `${outBase}.report.json`;
        if (fs.existsSync(jsonFile)) {
          const report = JSON.parse(fs.readFileSync(jsonFile, 'utf8'));
          results[runKey] = {
            performance: Math.round((report.categories.performance?.score || 0) * 100),
            accessibility: Math.round((report.categories.accessibility?.score || 0) * 100),
            bestPractices: Math.round((report.categories['best-practices']?.score || 0) * 100),
            seo: Math.round((report.categories.seo?.score || 0) * 100),
          };
          console.log(`[PASS] ${runKey} Scores:`, results[runKey]);
        }
      } catch (err) {
        console.error(`[FAIL] ${runKey} failed:`, err.message);
      }
    }
  }

  // Kill preview process
  try {
    process.kill(previewProcess.pid);
  } catch (e) {}

  console.log('\n========================================');
  console.log('LIGHTHOUSE AUDIT FINAL RESULTS');
  console.log('========================================');
  console.log(JSON.stringify(results, null, 2));

  fs.writeFileSync(path.join(OUT_DIR, 'summary.json'), JSON.stringify(results, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
