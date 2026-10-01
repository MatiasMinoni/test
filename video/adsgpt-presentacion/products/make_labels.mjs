// Exporta las etiquetas y piezas gráficas de la marca de ejemplo (cítrica) a PNG.
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MIME = { '.html': 'text/html', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  const file = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) { res.writeHead(404).end(); return; }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] ?? 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));

const outTex = path.join(ROOT, 'products', 'tex');
const outAssets = path.join(ROOT, 'assets', 'products');
fs.mkdirSync(outTex, { recursive: true });
fs.mkdirSync(outAssets, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 3000, height: 1200 } });
await page.goto(`http://127.0.0.1:${server.address().port}/products/labels.html`);
await page.evaluate(() => Promise.all(Array.from(document.fonts).map((f) => f.load())));
const shots = { serum: outTex, jar: outTex, pump: outTex, avatar: outAssets, 'post-new': outAssets, 'post-routine': outAssets };
for (const [id, dir] of Object.entries(shots)) {
  await page.locator(`#${id}`).screenshot({ path: path.join(dir, `${id}.png`), omitBackground: id === 'avatar' });
  console.log(`${id}.png`);
}
await browser.close();
server.close();
