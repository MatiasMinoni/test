# AdsGPT · Video presentación (15 s)

Motion graphics de 15 segundos con música propia que explica qué hace AdsGPT y en qué se diferencia de un chat de IA convencional.

Usa la identidad de [adsgpt.dev](https://adsgpt.dev): fondo negro, blanco y azul de acento, el isotipo de 4 bloques (celdas 11, 7, 3 y 9 de una grilla de 5×3), la caja de prompt con texto monoespaciado y el claim "Tu agente de IA para el crecimiento".

| Archivo | Formato | Uso sugerido |
|---|---|---|
| `out/AdsGPT_presentacion_15s_16x9.mp4` | 1920×1080 · 60 fps · con audio | LinkedIn, YouTube, web, presentaciones |
| `out/AdsGPT_presentacion_15s_9x16.mp4` | 1080×1920 · 60 fps · con audio | Reels, Stories, TikTok, Shorts |
| `out/AdsGPT_musica_15s.wav` | 48 kHz estéreo | La banda sonora sola, por si se quiere remezclar o reemplazar |

## Guion (128 BPM: un compás por escena, cada corte cae en el tiempo fuerte)

| Tiempo | Escena | Qué pasa |
|---|---|---|
| 0.00 – 1.88 s | Gancho | Destello de luz, "Pegá un link. AdsGPT hace todo el resto." |
| 1.88 – 3.75 s | 01 · Tu link | "Web, producto o Instagram." Se tipea la URL en la caja de prompt y el cursor hace clic en la flecha. |
| 3.75 – 5.63 s | 02 · Análisis | "Entiende qué vendés." El sitio gira en 3D, un escáner lo recorre, se detectan producto y precio, y aparecen tipo, categoría, anuncio ideal y paleta de la marca. |
| 5.63 – 7.50 s | 03 · Creatividades | "Anuncios a medida, fieles a tu marca." Tres anuncios llegan como esqueletos y se "generan" con una línea de luz (feed, historia y post). |
| 7.50 – 9.38 s | 04 · Audiencia | "Segmenta a tu cliente ideal." Radar 3D sobre Buenos Aires, edad, intereses y alcance estimado. |
| 9.38 – 11.25 s | 05 · Publicación | "Y la publica por vos." Clic en *Publicar campaña*, la campaña despega, "¡Campaña publicada!" y métricas en vivo. |
| 11.25 – 13.13 s | Comparación | "No es un chat. Es tu agente de anuncios." Tabla contra un chat de IA convencional, con un redoble que sube. |
| 13.13 – 15.00 s | Cierre | Golpe final: los 4 bloques del isotipo entran uno por uno con la música, ícono de la app, "AdsGPT", "Tu agente de IA para el crecimiento.", tiendas, web y Powered by Wortise. |

## Cómo está hecho

- **Animación:** HTML/CSS + [GSAP](https://gsap.com), en una sola línea de tiempo (`timeline.js`).
- **Sincronía:** `cues.js` guarda todos los tiempos. Lo leen la animación y la música, así los golpes visuales y sonoros coinciden al cuadro.
- **Música y efectos:** `audio/score.py` los sintetiza desde cero con numpy/scipy, sin samples ni licencias de terceros. Incluye bombo, palmas, bajo con sidechain, pads, arpegio, risers, impactos, whooshes y sonidos de interfaz (tipeo, clics, checks, escaneo, lanzamiento). La mezcla queda en −14 LUFS, el estándar de redes.
- **Render:** `render.mjs` abre 4 Chromium en paralelo y captura cada cuadro. Para el desenfoque de movimiento, cada cuadro final promedia 4 subcuadros dentro de un obturador de 180°. Después une los tramos con ffmpeg y agrega el audio.

## Editar y volver a renderizar

- **Textos:** `index.html`
- **Tiempos:** `cues.js` (la música se ajusta sola al volver a renderizar)
- **Colores de AdsGPT:** variables `--blue`, `--blue-2`, `--blue-3` y `--blue-soft` en `styles.css`
- **Isotipo:** símbolo `#mark` y los 4 `.blk` del cierre en `index.html`
- **Marca de ejemplo (NOVA Running):** variables `--n-*` en `styles.css`

```bash
npm install
pip install numpy scipy
npx serve .                                   # vista previa en loop (agregar ?format=portrait para 9:16)
node render.mjs                               # 16:9 y 9:16 con desenfoque de movimiento y audio (~20 min por formato)
node render.mjs --format portrait --sub 1     # solo 9:16, sin desenfoque (más rápido)
node render.mjs --stills 2.9,6.9 --out /tmp/frames   # PNG sueltos para revisar
node render.mjs --range 1.5,2.5 --out /tmp/test      # un tramo, sin audio
python3 audio/score.py out/AdsGPT_musica_15s.wav     # solo la música
```

Requisitos: Node 18+, Python 3 con numpy y scipy, ffmpeg y Chromium para Playwright (`npx playwright install chromium`).
