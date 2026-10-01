// Renderiza index.html a MP4 cuadro por cuadro (Playwright + ffmpeg).
//
//   node render.mjs                       -> 16:9 y 9:16 a 60 fps
//   node render.mjs --format portrait     -> solo 9:16
//   node render.mjs --stills 1,4.5,9 --out /tmp/x   -> PNGs sueltos para revisar
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const FORMATS = { landscape: [1920, 1080], portrait: [1080, 1920] };
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.woff2': 'font/woff2' };

const args = process.argv.slice(2);
const opt = (name, def) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : def;
};
const formats = opt('format', 'all') === 'all' ? Object.keys(FORMATS) : [opt('format')];
const fps = Number(opt('fps', 60));
const outDir = path.resolve(opt('out', path.join(ROOT, 'out')));
const stills = opt('stills', null)?.split(',').map(Number);
fs.mkdirSync(outDir, { recursive: true });

const server = http.createServer((req, res) => {
  const file = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404).end();
    return;
  }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] ?? 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch();

for (const format of formats) {
  const [width, height] = FORMATS[format];
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => console.error('pageerror:', e.message));
  await page.goto(`${base}/index.html?format=${format}&render`);
  await page.waitForFunction(() => window.__ready === true);
  const duration = await page.evaluate(() => window.__duration);

  if (stills) {
    for (const t of stills) {
      await page.evaluate((x) => window.__seek(x), t);
      await page.screenshot({ path: path.join(outDir, `${format}-${t.toFixed(2)}.png`) });
    }
    console.log(`${format}: ${stills.length} stills -> ${outDir}`);
    await page.close();
    continue;
  }

  const file = path.join(outDir, `AdsGPT_presentacion_15s_${format === 'landscape' ? '16x9' : '9x16'}.mp4`);
  const ff = spawn('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p',
    '-profile:v', 'high', '-movflags', '+faststart', file,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', (c) => (c === 0 ? res() : rej(new Error(`ffmpeg ${c}`)))));

  const frames = Math.round(duration * fps);
  const t0 = Date.now();
  for (let i = 0; i < frames; i++) {
    await page.evaluate((x) => window.__seek(x), i / fps);
    const png = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
    if (i % 60 === 0) process.stdout.write(`\r${format}: ${i}/${frames}`);
  }
  ff.stdin.end();
  await done;
  console.log(`\r${format}: ${frames} frames en ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${file}`);
  await page.close();
}

await browser.close();
server.close();
