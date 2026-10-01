/* AdsGPT · video presentación 15 s
 * Toda la animación vive en una única timeline de GSAP en pausa, sincronizada con la música
 * a través de cues.js (128 BPM, un compás por escena).
 * - Vista previa: servir la carpeta y abrir index.html (se reproduce en loop).
 * - Render: render.mjs llama a window.__seek(t) por cada subcuadro.
 * Nada usa transiciones/animaciones CSS, así cada cuadro es determinístico.
 */
(() => {
  const C = window.CUES;
  const params = new URLSearchParams(location.search);
  const FORMAT = params.get('format') === 'portrait' ? 'portrait' : 'landscape';
  const PORTRAIT = FORMAT === 'portrait';
  const RENDER = params.has('render');
  const DUR = C.end;
  const BEAT = 60 / C.bpm;
  const [, B1, B2, B3, B4, B5, B6, B7] = C.bars;

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const stage = $('#stage');
  stage.className = FORMAT;
  const W = stage.offsetWidth;
  const H = stage.offsetHeight;

  // PRNG con semilla: partículas, grano, chispas y "personas" del radar siempre iguales.
  const mulberry = (a) => () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const rand = mulberry(7);

  /* ---------- Texto partido en palabras con máscara ---------- */
  const split = (el) => {
    const frag = document.createDocumentFragment();
    const walk = (node, hl) => {
      for (const n of Array.from(node.childNodes)) {
        if (n.nodeType === 3) {
          for (const part of n.textContent.split(/([ \n\t]+)/)) {
            if (!part) continue;
            if (/^[ \n\t]+$/.test(part)) { frag.appendChild(document.createTextNode(' ')); continue; }
            const m = document.createElement('span');
            m.className = 'm';
            const mi = document.createElement('span');
            mi.className = hl ? 'mi hl' : 'mi';
            mi.textContent = part;
            m.appendChild(mi);
            frag.appendChild(m);
          }
        } else if (n.nodeName === 'BR') {
          frag.appendChild(n.cloneNode());
        } else {
          walk(n, hl || n.classList.contains('hl'));
        }
      }
    };
    walk(el, false);
    el.textContent = '';
    el.appendChild(frag);
  };
  $$('.split').forEach(split);

  /* ---------- Capas procedurales ---------- */
  // Grano de película
  const grainCanvas = document.createElement('canvas');
  grainCanvas.width = grainCanvas.height = 256;
  const gctx = grainCanvas.getContext('2d');
  const img = gctx.createImageData(256, 256);
  const grng = mulberry(99);
  for (let i = 0; i < img.data.length; i += 4) {
    const v = grng() < .5 ? 0 : 255;
    img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
    img.data[i + 3] = Math.floor(grng() * 70);
  }
  gctx.putImageData(img, 0, 0);
  const grain = $('#grain');
  grain.style.backgroundImage = `url(${grainCanvas.toDataURL()})`;

  // Partículas con profundidad
  const particles = [];
  const pWrap = $('#particles');
  for (let i = 0; i < 46; i++) {
    const z = .25 + rand() * .75;
    const el = document.createElement('i');
    const size = (3 + rand() * 7) * z;
    el.style.width = el.style.height = `${size * 3}px`;
    pWrap.appendChild(el);
    particles.push({ el, z, x0: rand() * W, y0: rand() * H, vx: (rand() - .5) * 14 * z, vy: -(10 + rand() * 26) * z, ph: rand() * 6.28, half: size * 1.5 });
  }

  // Personas en el radar
  const people = $('#people');
  for (let i = 0; i < 16; i++) {
    const a = rand() * Math.PI * 2;
    const r = 10 + rand() * 30;
    const el = document.createElement('i');
    el.style.left = `${50 + Math.cos(a) * r}%`;
    el.style.top = `${50 + Math.sin(a) * r}%`;
    people.appendChild(el);
  }

  // Chispas del lanzamiento
  const sparks = $('#sparks');
  const sparkData = [];
  for (let i = 0; i < 30; i++) {
    const el = document.createElement('i');
    sparks.appendChild(el);
    const a = (i / 30) * Math.PI * 2 + rand() * .2;
    sparkData.push({ el, a, r: 240 + rand() * 260 });
  }

  /* ---------- Estados iniciales y medidas (antes de crear tweens) ---------- */
  gsap.set(['#pubBtn', '#pubDone'], { xPercent: -50, yPercent: -50 });
  gsap.set('#streak', { scaleX: 0 });
  gsap.set('#trail', { scaleY: 0 });
  gsap.set('.step .dot i', { scale: 0 });
  gsap.set('#s4 .sheen', { xPercent: -160, skewX: -18 });
  gsap.set('.beam', { '--a': '0deg' });

  const centerOf = (sel) => {
    const r = $(sel).getBoundingClientRect();
    const s = stage.getBoundingClientRect();
    return { x: r.left - s.left + r.width / 2, y: r.top - s.top + r.height / 2 };
  };
  const btnLink = centerOf('#urlBtn');
  const btnPublish = centerOf('#pubBtn');
  const iconC = centerOf('#appicon');
  const iconStart = { x: W / 2 - iconC.x, y: H / 2 - iconC.y };

  /* ---------- Estado numérico que sync() vuelca al DOM ---------- */
  const st = { typed: 0, ageMin: 18, ageMax: 65, reach: 0, imp: 0, clk: 0, pAlpha: .55 };

  const tl = gsap.timeline({ paused: true, defaults: { ease: 'power3.out' } });
  const BLUR0 = 'blur(0px)';

  /* ---------- Helpers ---------- */
  const pop = (targets, t, extra = {}) => tl.fromTo(targets,
    { scale: 0, autoAlpha: 0 },
    { scale: 1, autoAlpha: 1, duration: .45, ease: 'back.out(2.6)', ...extra }, t);
  const rise = (targets, t, extra = {}) => tl.fromTo(targets,
    { y: 34, autoAlpha: 0, filter: 'blur(8px)' },
    { y: 0, autoAlpha: 1, filter: BLUR0, duration: .55, ease: 'expo.out', ...extra }, t);

  const words = (targets, t, stagger = .045) => {
    tl.fromTo(targets,
      { yPercent: 118, rotation: 6, transformOrigin: '0% 100%' },
      { yPercent: 0, rotation: 0, duration: .65, ease: 'expo.out', stagger }, t);
  };
  const shine = (targets, t) => {
    if ($$(targets).length) tl.to(targets, { backgroundPosition: '0% 0', duration: .9, ease: 'power2.inOut', stagger: .05 }, t);
  };
  const captionIn = (sel, t) => {
    const eb = $(`${sel} .eyebrow`);
    if (eb) tl.fromTo(eb, { y: 18, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: .5, ease: 'expo.out' }, t);
    words($$(`${sel} .caption .mi`), t + .05);
    shine(`${sel} .caption .mi.hl`, t + .5);
  };

  // Entrada: la escena llega desde lejos y la cámara sigue empujando despacio.
  const sceneIn = (sel, t, driftEnd) => {
    const cam = $(`${sel} .cam`);
    tl.set(sel, { autoAlpha: 1 }, t - .002);
    tl.fromTo(cam, { scale: .8, autoAlpha: 0, filter: 'blur(16px)' },
      { scale: 1, autoAlpha: 1, filter: BLUR0, duration: .6, ease: 'expo.out' }, t);
    tl.to(cam, { scale: 1.035, duration: (driftEnd ?? t + 1.875) - t - .6, ease: 'none' }, t + .6);
  };
  // Salida: atravesamos la escena (zoom hacia cámara + desenfoque).
  const sceneOut = (sel, t, dur = .3) => {
    tl.to(sel, { scale: 1.3, autoAlpha: 0, filter: 'blur(22px)', duration: dur, ease: 'power3.in' }, t - dur);
  };
  // Golpe de luz en cada corte (coincide con el impacto de la música).
  const cutFX = (t, k = 1) => {
    tl.fromTo('#streak', { scaleX: 0, scaleY: 1, autoAlpha: 1 },
      { scaleX: 1, duration: .14, ease: 'power2.out', immediateRender: false }, t - .07);
    tl.to('#streak', { autoAlpha: 0, scaleY: 4, duration: .35, ease: 'power2.out' }, t + .07);
    tl.fromTo('#flash', { autoAlpha: 0 }, { autoAlpha: .5 * k, duration: .05, ease: 'none', immediateRender: false }, t - .02);
    tl.to('#flash', { autoAlpha: 0, duration: .45, ease: 'power2.out' }, t + .03);
  };
  const beam = (sel, t0, t1, turns = 1.5) => {
    tl.fromTo(sel, { '--a': '0deg' }, { '--a': `${360 * turns}deg`, duration: t1 - t0, ease: 'none', immediateRender: false }, t0);
  };
  // Cursor que viaja a un botón y hace clic
  const click = (pt, tIn, tPress, tOut) => {
    const x = pt.x + 6, y = pt.y + 8;
    tl.fromTo('#cursor', { x: x + 260, y: y + 230, autoAlpha: 0, scale: 1 },
      { x, y, autoAlpha: 1, duration: tPress - tIn - .03, ease: 'power3.inOut', immediateRender: false }, tIn);
    tl.to('#cursor', { scale: .8, duration: .07, ease: 'power2.in', transformOrigin: '15% 8%' }, tPress - .02);
    tl.to('#cursor', { scale: 1, duration: .16, ease: 'back.out(3)' }, tPress + .05);
    tl.to('#cursor', { autoAlpha: 0, duration: .2 }, tOut);
  };

  /* ---------- Fondo vivo ---------- */
  tl.to('.g1', { x: 300, y: 200, duration: DUR, ease: 'sine.inOut' }, 0);
  tl.to('.g2', { x: -260, y: -160, duration: DUR, ease: 'sine.inOut' }, 0);
  tl.fromTo('#glowCenter', { scale: .6, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: 1.2, ease: 'power2.out' }, 0);
  tl.to('#glowCenter', { scale: 1.45, duration: .9, ease: 'power2.out' }, B7);
  tl.to(st, { pAlpha: 1, duration: .8 }, B7);

  /* ---------- S1 · Hook (compás 1) ---------- */
  tl.set('#s1', { autoAlpha: 1 }, 0);
  tl.fromTo('#flare', { scaleX: 0, autoAlpha: 0 }, { scaleX: 1, autoAlpha: 1, duration: .55, ease: 'expo.out' }, 0);
  tl.to('#flare', { autoAlpha: 0, scaleY: .2, duration: .7, ease: 'power2.out' }, .4);
  words($$('#s1 .l1 .mi'), C.hook[0], .07);
  words($$('#s1 .l2 .mi'), C.hook[1], .055);
  tl.fromTo('#s1 .hook',
    { textShadow: '-10px 0 rgba(255,40,110,.75), 10px 0 rgba(40,170,255,.75)' },
    { textShadow: '0px 0 rgba(255,40,110,0), 0px 0 rgba(40,170,255,0)', duration: .5, ease: 'power2.out' }, C.hook[0]);
  shine('#s1 .mi.hl', C.hook[1] + .35);
  tl.fromTo('#s1 .cam', { scale: 1 }, { scale: 1.08, duration: B1, ease: 'none' }, 0);
  sceneOut('#s1', B1);
  cutFX(B1, 1.2);

  /* ---------- Marca y guía de pasos ---------- */
  tl.fromTo('#cornerLogo', { y: -16, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: .5, ease: 'expo.out' }, B1 + .1);
  tl.to('#cornerLogo', { autoAlpha: 0, duration: .25, ease: 'power2.in' }, B7 - .3);
  tl.fromTo('#stepper', { y: 30, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: .5, ease: 'expo.out' }, B1 + .15);
  tl.to('#stepper', { y: 30, autoAlpha: 0, duration: .3, ease: 'power2.in' }, B6 - .3);
  const dots = $$('.step .dot i');
  const labels = $$('.step label');
  [B1, B2, B3, B4, B5].forEach((t, i) => {
    tl.to('#stepFill', { width: `${i * 25}%`, duration: .5, ease: 'power3.inOut' }, t - .12);
    tl.to(dots[i], { scale: 1, duration: .45, ease: 'back.out(3)' }, t + .2);
    tl.to(labels[i], { color: '#FFFFFF', duration: .3 }, t + .2);
    if (i > 0) tl.to(labels[i - 1], { color: '#A1A1AA', duration: .3 }, t + .2);
  });

  /* ---------- S2 · Link (compás 2) ---------- */
  sceneIn('#s2', B1);
  captionIn('#s2', B1 + .04);
  tl.fromTo('#s2 .urlbar',
    { rotationX: 40, y: 90, z: -260, autoAlpha: 0 },
    { rotationX: 0, y: 0, z: 0, autoAlpha: 1, duration: .85, ease: 'expo.out' }, B1 + .1);
  beam('#s2 .beam', B1, B2, 1.6);
  tl.to(st, { typed: C.url.length, duration: C.type[1] - C.type[0], ease: 'none' }, C.type[0]);
  rise('#s2 .chip', B1 + .35, { stagger: .08 });
  click(btnLink, C.clickLink - .45, C.clickLink, B2 - .22);
  tl.to('#urlBtn', { scale: .86, duration: .07, ease: 'power2.in' }, C.clickLink - .02);
  tl.to('#urlBtn', { scale: 1, duration: .4, ease: 'back.out(3)' }, C.clickLink + .05);
  tl.fromTo('#urlRipple', { scale: .4, autoAlpha: 1 }, { scale: 2.4, autoAlpha: 0, duration: .6, ease: 'power2.out' }, C.clickLink);
  tl.to('#s2 .chip:nth-child(2)', {
    borderColor: '#1A7BFF', backgroundColor: 'rgba(26,123,255,.2)', color: '#FFFFFF',
    boxShadow: '0 0 40px rgba(26,123,255,.55)', scale: 1.1, duration: .3, ease: 'back.out(3)',
  }, C.chipDetect);
  tl.to('#s2 .urlbar', { scale: 1.06, duration: .4, ease: 'power2.in' }, B2 - .4);
  sceneOut('#s2', B2);
  cutFX(B2);

  /* ---------- S3 · Análisis (compás 3) ---------- */
  sceneIn('#s3', B2);
  captionIn('#s3', B2 + .04);
  const pose = PORTRAIT ? { rotationY: 0, rotationX: 10 } : { rotationY: 18, rotationX: 4 };
  tl.fromTo('#s3 .site',
    { rotationY: PORTRAIT ? 0 : 55, rotationX: PORTRAIT ? 45 : 10, z: -600, autoAlpha: 0 },
    { ...pose, z: 0, autoAlpha: 1, duration: .9, ease: 'expo.out' }, B2 + .06);
  tl.to('#s3 .site', { rotationY: PORTRAIT ? 0 : 11, rotationX: PORTRAIT ? 4 : 2, duration: 1, ease: 'sine.inOut' }, B2 + .96);
  tl.set('#scan', { autoAlpha: 1, yPercent: -100 }, C.scan[0]);
  tl.to('#scan', { yPercent: 450, duration: C.scan[1] - C.scan[0], ease: 'power1.inOut' }, C.scan[0]);
  tl.to('#scan', { autoAlpha: 0, duration: .15 }, C.scan[1] - .1);
  ['.d1', '.d2'].forEach((d, i) => {
    tl.fromTo(`#s3 ${d}`, { scale: 1.3, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: .35, ease: 'back.out(2)' }, C.detect[i]);
  });
  const res = $$('#s3 .res');
  C.results.forEach((t, i) => {
    tl.fromTo(res[i],
      { x: 90, rotationY: -30, transformPerspective: 1200, autoAlpha: 0 },
      { x: 0, rotationY: 0, autoAlpha: 1, duration: .55, ease: 'expo.out' }, t - .06);
    pop($('.ok', res[i]), t);
  });
  pop('#s3 .swatches i', C.swatches, { stagger: .05, ease: 'back.out(3)' });
  sceneOut('#s3', B3);
  cutFX(B3);

  /* ---------- S4 · Creatividades (compás 4) ---------- */
  sceneIn('#s4', B3);
  captionIn('#s4', B3 + .04);
  const wraps = $$('#s4 .ad-wrap');
  const restY = PORTRAIT ? [0, 0, 0] : [14, 0, -14];
  C.skeleton.forEach((t, i) => {
    tl.fromTo(wraps[i],
      { z: -900, y: 140, rotationY: PORTRAIT ? 0 : [-40, 0, 40][i], autoAlpha: 0 },
      { z: 0, y: 0, rotationY: restY[i], autoAlpha: 1, duration: .8, ease: 'expo.out' }, t);
  });
  tl.fromTo('#s4 .skel', { '--shx': '100%' }, { '--shx': '-60%', duration: .55, ease: 'none', repeat: 1 }, C.skeleton[0]);
  $$('#s4 .ad').forEach((ad, i) => {
    const t = C.generate[i];
    const dur = .42;
    tl.set($('.gen-line', ad), { autoAlpha: 1, top: '0%' }, t);
    tl.to($('.gen-line', ad), { top: '100%', duration: dur, ease: 'power1.inOut' }, t);
    tl.to($('.gen-line', ad), { autoAlpha: 0, duration: .12 }, t + dur - .04);
    tl.to($('.ad-c', ad), { clipPath: 'inset(0% 0% 0% 0%)', duration: dur, ease: 'power1.inOut' }, t);
    tl.fromTo($('.skel', ad), { clipPath: 'inset(0% 0% 0% 0%)' }, { clipPath: 'inset(100% 0% 0% 0%)', duration: dur, ease: 'power1.inOut' }, t);
    tl.to($('.sheen', ad), { xPercent: 380, duration: .75, ease: 'power2.inOut' }, C.sheen + i * .09);
  });
  pop('#s4 .ai-badge', C.aiBadge);
  wraps.forEach((w, i) => tl.to(w, { y: i === 1 ? -16 : -8, duration: 1, ease: 'sine.inOut' }, C.generate[2] + .3));
  if (!PORTRAIT) {
    tl.to(wraps[0], { x: -260, rotationY: 35, duration: .3, ease: 'power3.in' }, B4 - .3);
    tl.to(wraps[2], { x: 260, rotationY: -35, duration: .3, ease: 'power3.in' }, B4 - .3);
  }
  sceneOut('#s4', B4);
  cutFX(B4);

  /* ---------- S5 · Audiencia (compás 5) ---------- */
  sceneIn('#s5', B4);
  captionIn('#s5', B4 + .04);
  tl.fromTo('#s5 .radar', { scale: .4, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: .8, ease: 'expo.out' }, B4 + .08);
  tl.fromTo('#sweep', { '--sw': '0deg' }, { '--sw': '540deg', duration: B5 - B4, ease: 'none' }, B4);
  tl.fromTo('#s5 .pin', { y: -140, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: .6, ease: 'bounce.out' }, B4 + .2);
  tl.fromTo('#s5 .pin-beam', { scaleY: 0, autoAlpha: 0 }, { scaleY: 1, autoAlpha: 1, duration: .5, ease: 'expo.out' }, B4 + .38);
  $$('#s5 .ring').forEach((r, i) => {
    tl.fromTo(r, { scale: .1, autoAlpha: 1 }, { scale: 1.2, autoAlpha: 0, duration: 1, ease: 'power2.out' }, C.pings[i]);
  });
  pop('#people i', B4 + .42, { stagger: .04, duration: .35 });
  tl.fromTo('#s5 .aud-panel',
    { x: PORTRAIT ? 0 : 100, y: PORTRAIT ? 80 : 0, rotationY: PORTRAIT ? 0 : -25, transformPerspective: 1400, autoAlpha: 0 },
    { x: 0, y: 0, rotationY: 0, autoAlpha: 1, duration: .7, ease: 'expo.out' }, B4 + .12);
  const rows = $$('#s5 .aud-row, #s5 .reach');
  C.audRows.forEach((t, i) => tl.fromTo(rows[i], { x: 40, autoAlpha: 0 }, { x: 0, autoAlpha: 1, duration: .5, ease: 'expo.out' }, t - .05));
  tl.to(st, { ageMin: 25, ageMax: 44, duration: C.age[1] - C.age[0], ease: 'power2.inOut' }, C.age[0]);
  $$('#s5 .tags span').forEach((s, i) => pop(s, C.tags[i]));
  tl.to(st, { reach: 1.2, duration: C.reach[1] - C.reach[0], ease: 'power2.out' }, C.reach[0]);
  sceneOut('#s5', B5);
  cutFX(B5);

  /* ---------- S6 · Publicación (compás 6) ---------- */
  sceneIn('#s6', B5);
  captionIn('#s6', B5 + .04);
  tl.fromTo('#pubBtn', { scale: .55, autoAlpha: 0, filter: 'blur(10px)' },
    { scale: 1, autoAlpha: 1, filter: BLUR0, duration: .6, ease: 'back.out(1.6)' }, B5 + .1);
  beam('#pubBtn .beam', B5, C.clickPublish + .2, 1.2);
  click(btnPublish, C.clickPublish - .42, C.clickPublish, C.clickPublish + .1);
  const L = C.clickPublish;
  tl.to('#pubBtn', { scale: .9, duration: .07, ease: 'power2.in' }, L - .02);
  tl.fromTo('#pubRipple', { scale: .4, autoAlpha: 1 }, { scale: 2.4, autoAlpha: 0, duration: .55, ease: 'power2.out' }, L);
  tl.to('#pubBtn', { scale: .15, autoAlpha: 0, filter: 'blur(14px)', duration: .17, ease: 'power3.in' }, L + .06);
  tl.fromTo('#orb', { scale: .3, y: 0, autoAlpha: 0 }, { scale: 1.1, autoAlpha: 1, duration: .1, immediateRender: false }, L + .12);
  tl.to('#orb', { y: -640, scale: .55, duration: .3, ease: 'power3.in' }, L + .2);
  tl.to('#orb', { autoAlpha: 0, duration: .06 }, L + .48);
  tl.set('#trail', { autoAlpha: 1 }, L + .2);
  tl.to('#trail', { scaleY: 1, duration: .3, ease: 'power3.in' }, L + .2);
  tl.to('#trail', { autoAlpha: 0, duration: .4, ease: 'power2.out' }, L + .46);
  tl.fromTo('#shock', { scale: .2, autoAlpha: 1 }, { scale: 2.8, autoAlpha: 0, duration: .75, ease: 'power2.out', immediateRender: false }, C.success - .02);
  sparkData.forEach(({ el, a, r }) => {
    tl.fromTo(el,
      { x: 0, y: 0, rotation: (a * 180) / Math.PI + 90, autoAlpha: 1, scaleY: 1.4 },
      { x: Math.cos(a) * r, y: Math.sin(a) * r, autoAlpha: 0, scaleY: .4, duration: .7, ease: 'power3.out', immediateRender: false }, C.success);
  });
  tl.fromTo('#flash', { autoAlpha: 0 }, { autoAlpha: .4, duration: .05, ease: 'none', immediateRender: false }, C.success - .02);
  tl.to('#flash', { autoAlpha: 0, duration: .5, ease: 'power2.out' }, C.success + .03);
  tl.set('#pubDone', { autoAlpha: 1 }, C.success);
  pop('#pubDone .pub-check', C.success, { ease: 'back.out(2.2)', duration: .55 });
  rise(['#pubDone b', '#pubDone .live'], C.success + .1, { stagger: .08 });
  [['.st-a', -70], ['.st-b', 70]].forEach(([s, dx], i) => {
    tl.fromTo(`#s6 ${s}`, { x: PORTRAIT ? 0 : dx, y: 40, autoAlpha: 0, filter: 'blur(8px)' },
      { x: 0, y: 0, autoAlpha: 1, filter: BLUR0, duration: .55, ease: 'expo.out' }, C.stats[i]);
    tl.to(`#s6 ${s} path`, { strokeDashoffset: 0, duration: .9, ease: 'power2.out' }, C.stats[i] + .1);
  });
  tl.to(st, { imp: 12480, duration: B6 - C.stats[0] - .1, ease: 'power2.out' }, C.stats[0]);
  tl.to(st, { clk: 486, duration: B6 - C.stats[1] - .1, ease: 'power2.out' }, C.stats[1]);
  sceneOut('#s6', B6);
  cutFX(B6);

  /* ---------- S7 · Comparación (compás 7) ---------- */
  const pushAt = C.build[1] - .58;
  sceneIn('#s7', B6, pushAt);
  captionIn('#s7', B6 + .03);
  tl.fromTo('#s7 .cmp', { rotationX: 28, y: 70, transformPerspective: 1800 }, { rotationX: 0, y: 0, duration: .85, ease: 'expo.out' }, B6 + .08);
  tl.fromTo('#s7 .cmp-hl', { scaleY: .4, autoAlpha: 0 }, { scaleY: 1, autoAlpha: 1, duration: .6, ease: 'expo.out' }, B6 + .14);
  beam('#s7 .cmp-hl .beam', B6, B7, 1.5);
  const crow = $$('#s7 .cmp-row');
  C.cmpRows.forEach((t, i) => {
    tl.fromTo(crow[i], { y: 30, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: .45, ease: 'expo.out' }, t - .06);
  });
  $$('#s7 .yes svg').forEach((s, i) => pop(s, C.cmpRows[i + 1], { ease: 'back.out(3)' }));
  tl.to('#s7 .cam', { scale: 1.16, x: PORTRAIT ? -150 : -330, duration: B7 - pushAt, ease: 'power2.in' }, pushAt);
  sceneOut('#s7', B7, .22);
  cutFX(B7, 1.6);

  /* ---------- S8 · Cierre (compás 8) ---------- */
  tl.set('#s8', { autoAlpha: 1 }, B7 - .002);
  tl.fromTo('#rays', { autoAlpha: 0, scale: .7, rotation: 0 }, { autoAlpha: 1, scale: 1, duration: .9, ease: 'power2.out' }, B7);
  tl.to('#rays', { rotation: 24, duration: DUR - B7, ease: 'none' }, B7);
  tl.fromTo('#s8 .cam', { scale: .97 }, { scale: 1.02, duration: DUR - B7, ease: 'sine.out' }, B7);
  tl.set('#appicon', { x: iconStart.x, y: iconStart.y, scale: 1.4 }, B7 - .002);
  $$('#s8 .blk').forEach((b, i) => {
    const t = C.logoBlocks[i];
    tl.fromTo(b, { scale: 2.4, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: .3, ease: 'expo.out' }, t);
    tl.fromTo(b, { filter: 'drop-shadow(0 0 6px rgba(190,220,255,1))' },
      { filter: 'drop-shadow(0 0 0px rgba(190,220,255,0))', duration: .55, ease: 'power2.out' }, t);
  });
  tl.fromTo('#iconFrame', { scale: 1.3, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: .5, ease: 'expo.out' }, C.logoIcon);
  tl.to('#appicon', { x: 0, y: 0, scale: 1, duration: .7, ease: 'expo.inOut' }, C.wordmark - .12);
  tl.fromTo('#endWord',
    { clipPath: 'inset(-20% 100% -20% 0%)', x: PORTRAIT ? 0 : -60, y: PORTRAIT ? -40 : 0 },
    { clipPath: 'inset(-20% 0% -20% 0%)', x: 0, y: 0, duration: .75, ease: 'expo.out' }, C.wordmark + .12);
  words($$('#s8 .end-tag .mi'), C.tagline, .05);
  shine('#s8 .end-tag .mi.hl', C.tagline + .4);
  rise('#s8 .end-foot', C.footer);
  rise('#s8 .end-by', C.footer + .12);
  tl.fromTo('#iconSheen', { autoAlpha: 1, '--ish': '150%' }, { '--ish': '-60%', duration: .9, ease: 'power2.inOut' }, 14.2);

  // Ancla la duración exacta
  tl.set({}, {}, DUR);

  /* ---------- Valores y capas procedurales → DOM ---------- */
  const urlTyped = $('#urlTyped');
  const caret = $('#caret');
  const hMin = $('#hMin');
  const hMax = $('#hMax');
  const ageRange = $('#ageRange');
  const ageLabel = $('#ageLabel');
  const reachNum = $('#reachNum');
  const statImp = $('#statImp');
  const statClk = $('#statClk');
  const floorGrid = $('#floorGrid');
  const pct = (v) => ((v - 18) / (65 - 18)) * 100;
  const fmt = new Intl.NumberFormat('es-AR');
  // Golpes de bombo (igual que en la música) para que la luz respire con el ritmo
  const kicks = [];
  for (let t = B1; t < B6 + 2 * BEAT - 1e-6; t += BEAT) kicks.push(t);
  const hits = [0, B1, B7, ...C.logoBlocks];

  function sync() {
    const t = tl.time();
    // Texto tipeado
    urlTyped.textContent = C.url.slice(0, Math.round(st.typed));
    const typing = t > C.type[0] - .05 && t < C.type[1] + .05;
    caret.style.opacity = t > C.clickLink ? 0 : (typing || Math.floor(t * 2.6) % 2 === 0 ? 1 : 0);
    // Audiencia y métricas
    hMin.style.left = `${pct(st.ageMin)}%`;
    hMax.style.left = `${pct(st.ageMax)}%`;
    ageRange.style.left = `${pct(st.ageMin)}%`;
    ageRange.style.width = `${pct(st.ageMax) - pct(st.ageMin)}%`;
    ageLabel.textContent = `${Math.round(st.ageMin)} – ${Math.round(st.ageMax)}`;
    reachNum.textContent = `${st.reach.toFixed(1).replace('.', ',')} M`;
    statImp.textContent = fmt.format(Math.round(st.imp));
    statClk.textContent = fmt.format(Math.round(st.clk));
    // Pulso de luz con el bombo
    let env = 0;
    for (const k of kicks) if (k <= t) env = Math.max(env, .7 * Math.exp(-(t - k) / .16));
    for (const h of hits) if (h <= t) env = Math.max(env, Math.exp(-(t - h) / .35));
    stage.style.setProperty('--pulse', env.toFixed(3));
    // Piso en perspectiva avanzando hacia cámara
    floorGrid.style.backgroundPosition = `50% ${(t * 90) % 110}px`;
    // Partículas
    for (const p of particles) {
      const x = ((p.x0 + p.vx * t) % W + W) % W;
      const y = ((p.y0 + p.vy * t) % (H + 40) + H + 40) % (H + 40) - 20;
      const a = st.pAlpha * (.3 + .7 * p.z) * (.55 + .45 * Math.sin(t * 2.2 + p.ph)) * (1 + env * .6);
      p.el.style.transform = `translate3d(${(x - p.half).toFixed(1)}px, ${(y - p.half).toFixed(1)}px, 0)`;
      p.el.style.opacity = Math.min(1, a).toFixed(3);
    }
    // Grano a 24 fps
    const g = Math.floor(t * 24);
    grain.style.backgroundPosition = `${(g * 73) % 256}px ${(g * 151) % 256}px`;
  }

  window.__duration = DUR;
  window.__seek = (t) => { tl.seek(t, false); sync(); };

  // Las fuentes se cargan recién cuando se usan: se fuerzan todas antes de empezar.
  const fontsLoaded = Promise.all(Array.from(document.fonts).map((f) => f.load())).then(() => document.fonts.ready);

  if (RENDER) {
    window.__seek(0);
    fontsLoaded.then(() => { window.__ready = true; });
  } else {
    // Vista previa en el navegador: escala al viewport y loop.
    const fit = () => {
      const s = Math.min(innerWidth / W, innerHeight / H);
      stage.style.transform = `translate(${(innerWidth - W * s) / 2}px, ${(innerHeight - H * s) / 2}px) scale(${s})`;
    };
    addEventListener('resize', fit);
    fit();
    tl.eventCallback('onUpdate', sync);
    tl.repeat(-1).repeatDelay(.6);
    fontsLoaded.then(() => tl.play(0));
  }
})();
