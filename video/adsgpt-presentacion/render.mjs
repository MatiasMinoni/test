// Renderiza index.html a MP4 cuadro por cuadro (Playwright + ffmpeg) y le agrega la música.
//
//   node render.mjs                         -> 16:9 y 9:16, 60 fps, desenfoque de movimiento, con audio
//   node render.mjs --format portrait       -> solo 9:16
//   node render.mjs --sub 1                 -> sin desenfoque de movimiento (más rápido)
//   node render.mjs --stills 1,4.5,9 --out /tmp/x   -> PNGs sueltos para revisar
//   node render.mjs --range 1.5,2.5 --out /tmp/x    -> solo ese tramo, sin audio (pruebas)
//
// Desenfoque de movimiento: cada cuadro final promedia `--sub` subcuadros repartidos en el
// obturador (`--shutter`, fracción del cuadro; 0.5 = 180°), como una cámara real.
import { chromium } from 'playwright';
import { spawn, spawnSync } from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const FORMATS = { landscape: [1920, 1080, '16x9'], portrait: [1080, 1920, '9x16'] };
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.woff2': 'font/woff2' };

const args = process.argv.slice(2);
const opt = (name, def) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : def;
};
const formats = opt('format', 'all') === 'all' ? Object.keys(FORMATS) : [opt('format')];
const fps = Number(opt('fps', 60));
const sub = Number(opt('sub', 4));
const shutter = Number(opt('shutter', 0.5));
const workers = Number(opt('workers', 4));
const outDir = path.resolve(opt('out', path.join(ROOT, 'out')));
const stills = opt('stills', null)?.split(',').map(Number);
const range = opt('range', null)?.split(',').map(Number);
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

const run = (cmd, argv) => {
  const r = spawnSync(cmd, argv, { stdio: 'inherit' });
  if (r.status !== 0) throw new Error(`${cmd} terminó con código ${r.status}`);
};

async function openPage(browser, format) {
  const [width, height] = FORMATS[format];
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => console.error('pageerror:', e.message));
  await page.goto(`${base}/index.html?format=${format}&render`);
  await page.waitForFunction(() => window.__ready === true);
  const cdp = await page.context().newCDPSession(page);
  const shot = async (t) => {
    await page.evaluate((x) => window.__seek(x), t);
    const { data } = await cdp.send('Page.captureScreenshot', { format: 'png' });
    return Buffer.from(data, 'base64');
  };
  return { page, shot, duration: await page.evaluate(() => window.__duration) };
}

// Un trabajador renderiza un tramo continuo de cuadros a su propio segmento de video.
async function renderSegment(format, first, last, file, progress) {
  const browser = await chromium.launch();
  const { shot } = await openPage(browser, format);
  const vf = sub > 1
    ? `tmix=frames=${sub},select='eq(mod(n\\,${sub})\\,${sub - 1})',setpts=N/(${fps}*TB)`
    : 'null';
  const ff = spawn('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(fps * sub), '-c:v', 'png', '-i', '-',
    '-vf', vf, '-r', String(fps),
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '12', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
    file,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', (c) => (c === 0 ? res() : rej(new Error(`ffmpeg ${c}`)))));
  for (let i = first; i < last; i++) {
    for (let k = 0; k < sub; k++) {
      const png = await shot((i + (k * shutter) / sub) / fps);
      if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
    }
    progress();
  }
  ff.stdin.end();
  await done;
  await browser.close();
}

if (stills) {
  const browser = await chromium.launch();
  for (const format of formats) {
    const { page, shot } = await openPage(browser, format);
    for (const t of stills) fs.writeFileSync(path.join(outDir, `${format}-${t.toFixed(2)}.png`), await shot(t));
    console.log(`${format}: ${stills.length} stills -> ${outDir}`);
    await page.close();
  }
  await browser.close();
  server.close();
  process.exit(0);
}

// Música y efectos (sincronizados con cues.js)
const wav = path.join(outDir, 'AdsGPT_musica_30s.wav');
if (!range) run('python3', [path.join(ROOT, 'audio', 'score.py'), wav]);

for (const format of formats) {
  const [, , tag] = FORMATS[format];
  const tmp = fs.mkdtempSync(path.join(outDir, `.tmp-${format}-`));
  const probe = await chromium.launch();
  const { duration } = await openPage(probe, format);
  await probe.close();
  const from = range ? Math.round(range[0] * fps) : 0;
  const frames = (range ? Math.round(range[1] * fps) : Math.round(duration * fps)) - from;
  const chunk = Math.ceil(frames / workers);
  let doneFrames = 0;
  const t0 = Date.now();
  const progress = () => {
    doneFrames++;
    if (doneFrames % 30 === 0 || doneFrames === frames) {
      const el = (Date.now() - t0) / 1000;
      process.stdout.write(`\r${format}: ${doneFrames}/${frames} cuadros · ${el.toFixed(0)} s · faltan ~${((el / doneFrames) * (frames - doneFrames)).toFixed(0)} s   `);
    }
  };
  const segs = [];
  const jobs = [];
  for (let w = 0; w < workers; w++) {
    const first = from + w * chunk;
    const last = Math.min(from + frames, first + chunk);
    if (first >= last) break;
    const file = path.join(tmp, `seg${w}.mp4`);
    segs.push(file);
    jobs.push(renderSegment(format, first, last, file, progress));
  }
  await Promise.all(jobs);
  process.stdout.write('\n');

  const list = path.join(tmp, 'list.txt');
  fs.writeFileSync(list, segs.map((s) => `file '${s}'`).join('\n'));
  const video = path.join(tmp, 'video.mp4');
  run('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', video]);
  const out = path.join(outDir, range ? `test_${tag}.mp4` : `AdsGPT_presentacion_30s_${tag}.mp4`);
  // Los tramos van casi sin pérdida; la compresión final deja el archivo liviano para compartir.
  const encode = ['-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-movflags', '+faststart'];
  if (range) run('ffmpeg', ['-y', '-loglevel', 'error', '-i', video, ...encode, out]);
  else run('ffmpeg', ['-y', '-loglevel', 'error', '-i', video, '-i', wav,
    '-map', '0:v', '-map', '1:a', ...encode, '-c:a', 'aac', '-b:a', '320k', '-shortest', out]);
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`${format}: ${frames} cuadros en ${((Date.now() - t0) / 1000).toFixed(0)} s -> ${out}`);
}

server.close();
