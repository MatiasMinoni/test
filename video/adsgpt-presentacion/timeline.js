/* AdsGPT · video presentación 15s
 * Toda la animación vive en una única timeline de GSAP en pausa.
 * - Vista previa: abrir index.html (se reproduce en loop).
 * - Render: render.mjs llama a window.__seek(t) cuadro por cuadro.
 * Nada usa transiciones/animaciones CSS, así cada cuadro es determinístico.
 */
(() => {
  const params = new URLSearchParams(location.search);
  const FORMAT = params.get('format') === 'portrait' ? 'portrait' : 'landscape';
  const RENDER = params.has('render');
  const DURATION = 15;
  const URL_TEXT = 'https://tumarca.com/nova-run';

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const stage = $('#stage');
  stage.className = FORMAT;

  // PRNG con semilla: confeti y "personas" del mapa siempre en el mismo lugar.
  let seed = 7;
  const rand = () => {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };

  // Elementos generados
  const people = $('#people');
  for (let i = 0; i < 18; i++) {
    const a = rand() * Math.PI * 2;
    const r = 9 + rand() * 30;
    const el = document.createElement('i');
    el.style.left = `${50 + Math.cos(a) * r}%`;
    el.style.top = `${50 + Math.sin(a) * r}%`;
    people.appendChild(el);
  }
  const confetti = $('#confetti');
  const confColors = ['#1A7BFF', '#4B9BFF', '#FFFFFF', '#22C55E', '#FF5A36', '#FFC93C', '#A9CEFF'];
  for (let i = 0; i < 40; i++) {
    const el = document.createElement('i');
    el.style.background = confColors[i % confColors.length];
    if (i % 3 === 0) { el.style.width = '16px'; el.style.height = '16px'; el.style.borderRadius = '50%'; }
    confetti.appendChild(el);
  }

  // Centro de un elemento en coordenadas del stage (se mide antes de animar nada)
  const centerOf = (sel) => {
    const r = $(sel).getBoundingClientRect();
    const s = stage.getBoundingClientRect();
    return { x: r.left - s.left + r.width / 2, y: r.top - s.top + r.height / 2 };
  };
  const btnCreate = centerOf('#urlBtn');
  const btnPublish = centerOf('#pubBtn');

  // Estado numérico que se vuelca al DOM en sync()
  const st = { typed: 0, ageMin: 18, ageMax: 65, reach: 0 };

  const tl = gsap.timeline({ paused: true, defaults: { ease: 'power3.out' } });
  const BLUR0 = 'blur(0px)';

  const enter = (sel, t) => {
    const scene = $(sel);
    tl.set(scene, { autoAlpha: 1, filter: BLUR0 }, t);
    const cap = $('.caption', scene);
    if (cap) {
      tl.fromTo(cap.children,
        { y: 40, autoAlpha: 0, filter: 'blur(10px)' },
        { y: 0, autoAlpha: 1, filter: BLUR0, duration: .55, stagger: .08 }, t);
    }
  };
  const exit = (sel, t, dur = .3) => {
    tl.to(sel, { autoAlpha: 0, x: -90, scale: .985, filter: 'blur(14px)', duration: dur, ease: 'power2.in' }, t);
  };
  const pop = (targets, t, extra = {}) => tl.fromTo(targets,
    { scale: 0, autoAlpha: 0 },
    { scale: 1, autoAlpha: 1, duration: .45, ease: 'back.out(2.6)', ...extra }, t);
  const rise = (targets, t, extra = {}) => tl.fromTo(targets,
    { y: 40, autoAlpha: 0, filter: 'blur(8px)' },
    { y: 0, autoAlpha: 1, filter: BLUR0, duration: .55, ...extra }, t);

  /* ---------- Fondo vivo (toda la pieza) ---------- */
  tl.to('.b1', { x: 260, y: 160, duration: DURATION, ease: 'sine.inOut' }, 0);
  tl.to('.b2', { x: -220, y: -140, duration: DURATION, ease: 'sine.inOut' }, 0);
  tl.to('.b3', { scale: 1.35, duration: DURATION / 2, ease: 'sine.inOut', yoyo: true, repeat: 1 }, 0);
  tl.to('.grid', { y: 80, duration: DURATION, ease: 'none' }, 0);

  /* ---------- S1 · Hook (0 – 1.6) ---------- */
  tl.set('#s1', { autoAlpha: 1, filter: BLUR0 }, 0);
  tl.fromTo('#s1 .l1 .w',
    { yPercent: 70, autoAlpha: 0, filter: 'blur(14px)' },
    { yPercent: 0, autoAlpha: 1, filter: BLUR0, duration: .6, stagger: .08 }, .06);
  tl.fromTo('#s1 .l2 .w',
    { yPercent: 70, autoAlpha: 0, filter: 'blur(14px)' },
    { yPercent: 0, autoAlpha: 1, filter: BLUR0, duration: .6, stagger: .05 }, .36);
  tl.fromTo('#s1 .l2 .hl', { scale: .7 }, { scale: 1, duration: .7, ease: 'back.out(2.2)', transformOrigin: '50% 70%' }, .36);
  tl.to('#s1 .hook', { scale: .9, y: -50, autoAlpha: 0, filter: 'blur(16px)', duration: .3, ease: 'power2.in' }, 1.38);

  /* ---------- Marca y guía de pasos ---------- */
  tl.fromTo('#cornerLogo', { y: -16, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: .5 }, 1.7);
  tl.to('#cornerLogo', { autoAlpha: 0, duration: .3, ease: 'power2.in' }, 12.7);

  tl.fromTo('#stepper', { y: 30, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: .5 }, 1.75);
  const stepT = [1.85, 3.55, 5.55, 7.55, 9.55];
  const dots = $$('.step .dot i');
  const labels = $$('.step label');
  stepT.forEach((t, i) => {
    tl.to('#stepFill', { width: `${i * 25}%`, duration: .55, ease: 'power2.inOut' }, t - .15);
    tl.to(dots[i], { scale: 1, duration: .45, ease: 'back.out(3)' }, t + .2);
    tl.to(labels[i], { color: '#FFFFFF', duration: .3 }, t + .2);
    if (i > 0) tl.to(labels[i - 1], { color: '#A1A1AA', duration: .3 }, t + .2);
  });
  tl.to('#stepper', { y: 30, autoAlpha: 0, duration: .3, ease: 'power2.in' }, 10.62);

  /* ---------- S2 · Link (1.6 – 3.5) ---------- */
  enter('#s2', 1.55);
  tl.fromTo('#s2 .urlbar',
    { y: 50, scale: .9, autoAlpha: 0, filter: 'blur(10px)' },
    { y: 0, scale: 1, autoAlpha: 1, filter: BLUR0, duration: .6, ease: 'expo.out' }, 1.68);
  tl.to(st, { typed: URL_TEXT.length, duration: .9, ease: 'none' }, 1.92);
  rise('#s2 .chip', 2.0, { stagger: .08 });
  tl.to('#urlBtn', { scale: .9, duration: .1, ease: 'power2.in' }, 2.92);
  tl.to('#urlBtn', { scale: 1, duration: .3, ease: 'back.out(3)' }, 3.02);
  tl.fromTo('#urlRipple', { scale: .4, autoAlpha: 1 }, { scale: 1.9, autoAlpha: 0, duration: .55, ease: 'power2.out' }, 2.98);
  tl.to('#s2 .chip:nth-child(2)', {
    borderColor: '#1A7BFF', backgroundColor: 'rgba(26,123,255,.16)', color: '#FFFFFF',
    scale: 1.08, duration: .25, ease: 'back.out(3)',
  }, 3.05);
  exit('#s2', 3.22);

  // Cursor que hace clic en un botón
  const click = (pt, tIn, tPress, tOut) => {
    const x = pt.x + 14 - 9, y = pt.y + 10 - 4; // punta del puntero sobre el botón
    tl.fromTo('#cursor', { x: x + 240, y: y + 220, autoAlpha: 0, scale: 1 },
      { x, y, autoAlpha: 1, duration: tPress - tIn - .04, ease: 'power2.inOut', immediateRender: false }, tIn);
    tl.to('#cursor', { scale: .82, duration: .08, ease: 'power2.in', transformOrigin: '15% 8%' }, tPress);
    tl.to('#cursor', { scale: 1, duration: .16, ease: 'back.out(3)' }, tPress + .08);
    tl.to('#cursor', { autoAlpha: 0, duration: .2 }, tOut);
  };
  click(btnCreate, 2.5, 2.9, 3.18);

  /* ---------- S3 · Análisis (3.5 – 5.5) ---------- */
  enter('#s3', 3.45);
  tl.fromTo('#s3 .site',
    { y: 60, scale: .92, autoAlpha: 0, filter: 'blur(10px)' },
    { y: 0, scale: 1, autoAlpha: 1, filter: BLUR0, duration: .6, ease: 'expo.out' }, 3.52);
  tl.set('#scan', { autoAlpha: 1, yPercent: -100 }, 3.7);
  tl.to('#scan', { yPercent: 489, duration: .95, ease: 'power1.inOut' }, 3.7);
  tl.to('#scan', { autoAlpha: 0, duration: .15 }, 4.55);
  tl.fromTo('#s3 .d1', { scale: 1.12, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: .35, ease: 'back.out(2)' }, 4.0);
  tl.fromTo('#s3 .d2', { scale: 1.12, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: .35, ease: 'back.out(2)' }, 4.25);
  tl.fromTo('#s3 .res',
    { x: 50, autoAlpha: 0, filter: 'blur(8px)' },
    { x: 0, autoAlpha: 1, filter: BLUR0, duration: .5, stagger: .18 }, 3.85);
  pop('#s3 .res .ok', 4.0, { stagger: .18 });
  pop('#s3 .swatches i', 4.62, { stagger: .06, ease: 'back.out(3)' });
  exit('#s3', 5.22);

  /* ---------- S4 · Creatividades (5.5 – 7.5) ---------- */
  enter('#s4', 5.45);
  tl.fromTo('#s4 .ad-wrap',
    { y: 110, rotationY: -28, transformPerspective: 1400, autoAlpha: 0, filter: 'blur(10px)' },
    { y: 0, rotationY: 0, autoAlpha: 1, filter: BLUR0, duration: .75, ease: 'expo.out', stagger: .12 }, 5.55);
  tl.fromTo('#s4 .shoe', { x: -70, autoAlpha: 0 }, { x: 0, autoAlpha: 1, duration: .6, stagger: .12 }, 5.78);
  tl.fromTo(['#s4 .ad-img strong', '#s4 .story strong', '#s4 .post strong'],
    { y: 24, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: .45, stagger: .12 }, 5.88);
  pop('#s4 .ai-badge', 6.3);
  tl.to('#s4 .ad-wrap:nth-child(2)', { y: -14, duration: .8, ease: 'sine.inOut' }, 6.45);
  exit('#s4', 7.22);

  /* ---------- S5 · Audiencia (7.5 – 9.5) ---------- */
  enter('#s5', 7.45);
  tl.fromTo('#s5 .aud',
    { y: 60, scale: .94, autoAlpha: 0, filter: 'blur(10px)' },
    { y: 0, scale: 1, autoAlpha: 1, filter: BLUR0, duration: .6, ease: 'expo.out' }, 7.52);
  tl.fromTo('#s5 .pin', { y: -70, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: .55, ease: 'bounce.out' }, 7.7);
  $$('#s5 .ring').forEach((r, i) => {
    tl.fromTo(r, { scale: .15, autoAlpha: .95 }, { scale: 1.2, autoAlpha: 0, duration: 1.15, ease: 'power1.out', repeat: 1 }, 7.75 + i * .38);
  });
  pop('#people i', 7.95, { stagger: .045, duration: .35 });
  tl.fromTo('#s5 .aud-row, #s5 .reach',
    { x: 40, autoAlpha: 0 }, { x: 0, autoAlpha: 1, duration: .5, stagger: .12 }, 7.66);
  tl.to(st, { ageMin: 25, ageMax: 44, duration: .65, ease: 'power2.inOut' }, 8.05);
  pop('#s5 .tags span', 8.25, { stagger: .08 });
  tl.to(st, { reach: 1.2, duration: .8, ease: 'power2.out' }, 8.45);
  exit('#s5', 9.22);

  /* ---------- S6 · Publicación (9.5 – 10.9) ---------- */
  enter('#s6', 9.45);
  tl.fromTo('#pubBtn', { scale: .7, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: .45, ease: 'back.out(1.8)' }, 9.55);
  click(btnPublish, 9.62, 9.9, 10.14);
  tl.to('#pubBtn', { scale: .92, duration: .1, ease: 'power2.in' }, 9.92);
  tl.to('#pubBtn', { scale: 1.08, autoAlpha: 0, filter: 'blur(8px)', duration: .2, ease: 'power2.in' }, 10.04);
  tl.fromTo('#pubRipple', { scale: .5, autoAlpha: 1 }, { scale: 2.4, autoAlpha: 0, duration: .6, ease: 'power2.out' }, 9.98);
  tl.set('#pubDone', { autoAlpha: 1 }, 10.06);
  pop('#pubDone .pub-check', 10.06, { ease: 'back.out(2.2)', duration: .5 });
  rise(['#pubDone b', '#pubDone .live'], 10.16, { stagger: .08, duration: .45 });
  $$('#confetti i').forEach((el) => {
    const a = rand() * Math.PI * 2;
    const r = 200 + rand() * 300;
    const dx = Math.cos(a) * r;
    const dy = Math.sin(a) * r * .62;
    tl.fromTo(el,
      { x: 0, y: 0, rotation: 0, scale: .3, autoAlpha: 1 },
      { x: dx, y: dy, rotation: (rand() - .5) * 720, scale: 1, duration: .8, ease: 'power3.out', immediateRender: false }, 10.08);
    tl.to(el, { y: dy + 70, autoAlpha: 0, duration: .35, ease: 'power1.in' }, 10.6 + rand() * .15);
  });
  exit('#s6', 10.62);

  /* ---------- S7 · Comparación (10.9 – 13.0) ---------- */
  enter('#s7', 10.85);
  tl.fromTo('#s7 .cmp-hl', { scaleY: .6, autoAlpha: 0 }, { scaleY: 1, autoAlpha: 1, duration: .55, ease: 'expo.out' }, 11.0);
  tl.fromTo('#s7 .cmp-row', { y: 26, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: .45, stagger: .1 }, 10.98);
  pop('#s7 .yes svg', 11.32, { stagger: .14, ease: 'back.out(3)' });
  exit('#s7', 12.72);

  /* ---------- S8 · Cierre (13.0 – 15.0) ---------- */
  tl.set('#s8', { autoAlpha: 1, filter: BLUR0 }, 12.98);
  tl.fromTo('#flash', { autoAlpha: 0 }, { autoAlpha: 1, duration: .15, ease: 'power1.out' }, 12.98);
  tl.to('#flash', { autoAlpha: 0, duration: .7, ease: 'power2.out' }, 13.13);
  tl.fromTo('#s8 .appicon',
    { scale: .5, autoAlpha: 0, filter: 'blur(12px)' },
    { scale: 1, autoAlpha: 1, filter: BLUR0, duration: .6, ease: 'back.out(1.6)' }, 13.0);
  // El isotipo se "construye" bloque a bloque, como un gráfico que crece
  tl.fromTo('#s8 .appicon .mark',
    { clipPath: 'inset(0% 100% 0% 0%)' },
    { clipPath: 'inset(0% 0% 0% 0%)', duration: .48, ease: 'steps(4)' }, 13.12);
  tl.fromTo('#s8 .end-logo .wordmark',
    { x: FORMAT === 'portrait' ? 0 : -40, y: FORMAT === 'portrait' ? 30 : 0, autoAlpha: 0, filter: 'blur(12px)' },
    { x: 0, y: 0, autoAlpha: 1, filter: BLUR0, duration: .6 }, 13.18);
  rise('#s8 .end-tag', 13.42);
  rise('#s8 .end-sub', 13.6);
  rise(['#s8 .end-foot', '#s8 .end-by'], 13.78, { stagger: .1 });
  tl.fromTo('#s8 .end', { scale: .97 }, { scale: 1.02, duration: 2, ease: 'sine.out' }, 13.0);
  tl.to('.b3', { opacity: .2, duration: 1, ease: 'sine.inOut' }, 13.0);

  // Ancla la duración exacta
  tl.set({}, {}, DURATION);

  /* ---------- Valores numéricos → DOM ---------- */
  const urlTyped = $('#urlTyped');
  const caret = $('#caret');
  const hMin = $('#hMin');
  const hMax = $('#hMax');
  const ageRange = $('#ageRange');
  const ageLabel = $('#ageLabel');
  const reachNum = $('#reachNum');
  const pct = (v) => ((v - 18) / (65 - 18)) * 100;

  function sync() {
    const t = tl.time();
    urlTyped.textContent = URL_TEXT.slice(0, Math.round(st.typed));
    const typing = t > 1.9 && t < 2.9;
    caret.style.opacity = t > 2.95 ? 0 : (typing || Math.floor(t * 2.6) % 2 === 0 ? 1 : 0);
    hMin.style.left = `${pct(st.ageMin)}%`;
    hMax.style.left = `${pct(st.ageMax)}%`;
    ageRange.style.left = `${pct(st.ageMin)}%`;
    ageRange.style.width = `${pct(st.ageMax) - pct(st.ageMin)}%`;
    ageLabel.textContent = `${Math.round(st.ageMin)} – ${Math.round(st.ageMax)}`;
    reachNum.textContent = `${st.reach.toFixed(1).replace('.', ',')} M`;
  }

  window.__duration = DURATION;
  window.__seek = (t) => { tl.seek(t, false); sync(); };

  if (RENDER) {
    window.__seek(0);
    document.fonts.ready.then(() => { window.__ready = true; });
  } else {
    // Vista previa en el navegador: escala al viewport y loop.
    const fit = () => {
      const s = Math.min(innerWidth / stage.offsetWidth, innerHeight / stage.offsetHeight);
      stage.style.transform = `translate(${(innerWidth - stage.offsetWidth * s) / 2}px, ${(innerHeight - stage.offsetHeight * s) / 2}px) scale(${s})`;
    };
    addEventListener('resize', fit);
    fit();
    tl.eventCallback('onUpdate', sync);
    tl.repeat(-1).repeatDelay(.6);
    document.fonts.ready.then(() => tl.play(0));
  }
})();
