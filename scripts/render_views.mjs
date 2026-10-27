// Crop world-coordinate windows out of the full-drawing SVG and save PNGs (dark ink on white).
// usage: node scripts/render_views.mjs full.svg views.json outdir
//   views.json: [{"name": "plan_4F", "bbox": [x0, y0, x1, y1], "px": 2600, "sw": 3}]  (world units = cm)
import fs from 'fs';
import { createRequire } from 'module'; const require = createRequire(import.meta.url); const { chromium } = require('playwright');
const [,, svgPath, viewsPath, outDir] = process.argv;
let svg = fs.readFileSync(svgPath, 'utf8');
const views = JSON.parse(fs.readFileSync(viewsPath, 'utf8'));
const style = `<style>
 g, path, line, circle, ellipse, polyline, polygon { stroke: #2b2b2b !important; }
 text { fill: #1a1a1a !important; stroke: none !important; font-family: 'Noto Sans CJK TC','Noto Sans CJK JP',sans-serif; }
 path[fill]:not([fill="none"]) { fill-opacity: 0.08 !important; }
</style>`;
svg = svg.replace('<defs>', style + '<defs>');
svg = svg.replace(/viewBox="[^"]*"/, 'viewBox="0 0 10 10"').replace('width="100%" height="100%"', 'width="2000" height="1400"');
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 2000, height: 1400 } });
await page.setContent(`<html><body style="margin:0;background:#fff">${svg}</body></html>`, { timeout: 600000 });
for (const v of views) {
  const [x0, y0, x1, y1] = v.bbox; const w = x1 - x0, h = y1 - y0;
  const W = v.px || 2000, H = Math.round(W * h / w);
  await page.setViewportSize({ width: W, height: H });
  await page.evaluate(([vb, W, H, sw]) => { const s = document.querySelector('svg'); s.setAttribute('viewBox', vb); s.setAttribute('width', W); s.setAttribute('height', H);
     const g = s.querySelector('svg > g[stroke]'); if (g) g.setAttribute('stroke-width', sw); },
     [`${x0} ${-y1} ${w} ${h}`, W, H, String(v.sw || w / 1500)]);
  await page.screenshot({ path: `${outDir}/${v.name}.png`, clip: { x: 0, y: 0, width: W, height: H }, timeout: 600000 });
  console.log('ok', v.name, W, H);
}
await browser.close();
