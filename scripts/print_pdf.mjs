// Print build/report.html to an A4 PDF with Chromium.
// usage: node scripts/print_pdf.mjs [out.pdf]
import path from 'path';
import { fileURLToPath, pathToFileURL } from 'url';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = process.argv[2] || path.join(root, 'reports', 'Shuangfu768_Building_Analysis_Proposal_v1.0.pdf');
const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(pathToFileURL(path.join(root, 'build', 'report.html')).href, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.pdf({ path: out, format: 'A4', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 }, preferCSSPageSize: true });
await browser.close();
console.log('wrote', out);
