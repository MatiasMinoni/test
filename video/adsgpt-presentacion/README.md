# AdsGPT · Video presentación (30 s)

Motion graphics de 30 segundos con música propia que explica qué hace AdsGPT y en qué se diferencia de un chat de IA convencional.

Usa la identidad de [adsgpt.dev](https://adsgpt.dev): fondo negro, blanco y azul de acento, el isotipo de 4 bloques (celdas 11, 7, 3 y 9 de una grilla de 5×3), la caja de prompt con texto monoespaciado y el claim "Tu agente de IA para el crecimiento".

| Archivo | Formato | Uso sugerido |
|---|---|---|
| `out/AdsGPT_presentacion_30s_16x9.mp4` | 1920×1080 · 60 fps · con audio | LinkedIn, YouTube, web, presentaciones |
| `out/AdsGPT_presentacion_30s_9x16.mp4` | 1080×1920 · 60 fps · con audio | Reels, Stories, TikTok, Shorts |
| `out/AdsGPT_musica_30s.wav` | 48 kHz estéreo | La banda sonora sola, por si se quiere remezclar o reemplazar |

## La marca de ejemplo: cítrica

Para que la demo no se vea genérica, el recorrido usa una marca de skincare con vitamina C con todo lo que tendría una real: Instagram `@citrica.skin`, web `citricaskin.com.ar`, etiquetas, paleta, tipografía y fotos de producto. **Es una marca inventada.** No se usó ninguna marca de terceros porque mostrarla en un aviso de AdsGPT daría a entender que es cliente. Para cambiarla por un cliente real que lo autorice, alcanza con reemplazar las fotos de `assets/products/` y los textos de `index.html`.

Las fotos de producto son renders 3D fotorrealistas hechos con Blender (Cycles), no dibujos:

| Foto | Dónde aparece |
|---|---|
| `hero_orange.jpg` · sérum en podio sobre fondo naranja, con media naranja y luz de persiana | Gancho, grilla de Instagram, anuncio feed, resumen y tablero |
| `hero_cream.jpg` · sérum en podios crema | Grilla de Instagram, anuncio historia |
| `family.jpg` · gel limpiador, sérum y crema | Gancho (web), grilla de Instagram, anuncio post |
| `flatlay.jpg` · vista cenital sobre terrazo | Gancho (Instagram), grilla de Instagram |

## Guion (128 BPM: dos compases por escena, cada corte cae en el tiempo fuerte)

| Tiempo | Escena | Qué pasa |
|---|---|---|
| 0.00 – 3.75 s | Gancho | "¿Tenés un producto, una web o un Instagram?", con tres tarjetas reales (producto, web y post). Después: "Pegá el link. AdsGPT hace todo el resto." |
| 3.75 – 7.50 s | 01 · Tu link | Se tipea `instagram.com/citrica.skin` en la caja de prompt, con ejemplos de web, producto e Instagram. Clic, se detecta Instagram y aparece "Analizando @citrica.skin". |
| 7.50 – 11.25 s | 02 · Análisis | Se abre el perfil de Instagram (bio, seguidores, grilla de 6 posts). Un escáner lo recorre, detecta producto y paleta, y aparecen: perfil de Instagram · skincare, producto estrella, anuncio ideal e identidad de marca. |
| 11.25 – 15.00 s | 03 · Creatividades | Tres anuncios se generan con las fotos de la marca: feed 4:5, historia 9:16 con −20% y post 1:1 con envío gratis. |
| 15.00 – 18.75 s | 04 · Audiencia | Radar 3D sobre Buenos Aires, 25 a 44 años, intereses (skincare, cosmética natural, bienestar, belleza) y 1,8 M de alcance. |
| 18.75 – 22.50 s | 05 · Publicación | Resumen de la campaña, clic en *Publicar campaña*, despegue, "¡Campaña publicada!" y tablero en vivo con impresiones, clics, CTR, ventas e inversión. |
| 22.50 – 26.25 s | Comparación | "No es un chat. Es tu agente de anuncios." La música baja y vuelve a subir hacia el cierre. |
| 26.25 – 30.00 s | Cierre | Los 4 bloques del isotipo entran con la música, ícono, "AdsGPT", "Tu agente de IA para el crecimiento.", botón "Descargala gratis", tiendas, web y Powered by Wortise. |

Las métricas (seguidores, alcance, impresiones, clics, ventas, inversión) son valores de ejemplo para la demo.

## Cómo está hecho

- **Animación:** HTML/CSS + [GSAP](https://gsap.com), en una sola línea de tiempo (`timeline.js`).
- **Sincronía:** `cues.js` guarda todos los tiempos. Lo leen la animación y la música, así los golpes visuales y sonoros coinciden al cuadro.
- **Música y efectos:** `audio/score.py` los sintetiza desde cero con numpy/scipy, sin samples ni licencias de terceros. La mezcla queda en −14 LUFS, el estándar de redes.
- **Fotos de producto:** `products/make_labels.mjs` exporta las etiquetas y las piezas gráficas desde `products/labels.html`. Después `products/render_products.py` modela los envases, las naranjas, los podios y la luz en Blender y renderiza las 4 fotos.
- **Render del video:** `render.mjs` abre 4 Chromium en paralelo y captura cada cuadro. Para el desenfoque de movimiento, cada cuadro final promedia varios subcuadros dentro de un obturador de 180°. Después une los tramos, comprime y agrega el audio.

## Editar y volver a renderizar

- **Textos:** `index.html`
- **Tiempos:** `cues.js` (la música se ajusta sola al volver a renderizar)
- **Colores de AdsGPT:** variables `--blue`, `--blue-2`, `--blue-3` y `--blue-soft` en `styles.css`
- **Marca de ejemplo:** variables `--c-*` en `styles.css`, etiquetas en `products/labels.html` y fotos en `assets/products/`

```bash
npm install
pip install numpy scipy
npx serve .                                   # vista previa en loop (agregar ?format=portrait para 9:16)
node render.mjs                               # 16:9 y 9:16 con desenfoque de movimiento y audio
node render.mjs --format portrait --sub 1     # solo 9:16, sin desenfoque (más rápido)
node render.mjs --stills 2.9,6.9 --out /tmp/frames   # PNG sueltos para revisar
python3 audio/score.py out/AdsGPT_musica_30s.wav     # solo la música

# Fotos de producto (Blender 4.2 como módulo de Python 3.11)
pip install bpy==4.2.0
node products/make_labels.mjs
python products/render_products.py              # o una sola toma: hero_orange, hero_cream, family, flatlay
python products/render_products.py --preview    # versión rápida en baja resolución
```

Requisitos: Node 18+, Python 3 con numpy y scipy, ffmpeg y Chromium para Playwright (`npx playwright install chromium`). Para las fotos, además, Python 3.11 con `bpy==4.2.0`.
