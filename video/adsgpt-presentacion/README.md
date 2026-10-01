# AdsGPT · Video presentación (15 s)

Motion graphics de 15 segundos que explica qué hace AdsGPT y en qué se diferencia de un chat de IA convencional.

Usa la identidad de [adsgpt.dev](https://adsgpt.dev): fondo negro, blanco y azul de acento, el isotipo de bloques, la caja de prompt con texto monoespaciado y el claim "Tu agente de IA para el crecimiento".

| Archivo | Formato | Uso sugerido |
|---|---|---|
| `out/AdsGPT_presentacion_15s_16x9.mp4` | 1920×1080 · 60 fps | LinkedIn, YouTube, web, presentaciones |
| `out/AdsGPT_presentacion_15s_9x16.mp4` | 1080×1920 · 60 fps | Reels, Stories, TikTok, Shorts |

Los videos no tienen audio: se puede sumar música o locución en cualquier editor (o directamente en la red social).

## Guion

| Tiempo | Escena | Texto en pantalla |
|---|---|---|
| 0.0 – 1.6 s | Hook | "Pegá un link. AdsGPT hace todo el resto." |
| 1.6 – 3.5 s | 01 · Tu link | "Web, producto o Instagram." Se escribe la URL en la caja de prompt de AdsGPT y se hace clic en la flecha. |
| 3.5 – 5.5 s | 02 · Análisis | "Entiende qué vendés." Escaneo del sitio: tipo de producto, categoría, anuncio ideal y paleta de marca. |
| 5.5 – 7.5 s | 03 · Creatividades | "Anuncios a medida, fieles a tu marca." Feed 4:5, Historia 9:16 y Post 1:1 con los colores detectados. |
| 7.5 – 9.5 s | 04 · Audiencia | "Segmenta a tu cliente ideal." Ubicación, edad, intereses y alcance estimado. |
| 9.5 – 10.9 s | 05 · Publicación | "Y la publica por vos." Clic en *Publicar campaña*, después "¡Campaña publicada!". |
| 10.9 – 13.0 s | Comparación | "No es un chat. Es tu agente de anuncios." Tabla: chat de IA convencional vs AdsGPT. |
| 13.0 – 15.0 s | Cierre | Ícono de la app + "AdsGPT", "Tu agente de IA para el crecimiento.", "Del link a la campaña publicada, todo automático.", tiendas y web, adsgpt.dev, Powered by Wortise. |

Debajo de las escenas 01 a 05 aparece una guía de pasos (Link, Análisis, Creatividades, Audiencia, Publicación) que muestra que el agente acompaña desde el link hasta la publicación.

## Editar y volver a renderizar

Todo es HTML/CSS + GSAP, así que los textos y colores se editan sin programas de video:

- **Textos:** `index.html`
- **Colores de AdsGPT:** variables `--blue`, `--blue-2` y `--blue-soft` en `styles.css`
- **Isotipo:** símbolo `#mark` en `index.html` (SVG redibujado a partir del ícono de la app; si tienen el SVG oficial, se reemplaza ahí)
- **Tipografías:** Geist y Geist Mono para AdsGPT; Sora solo para la marca de ejemplo
- **Marca de ejemplo (NOVA Running):** variables `--n-*` en `styles.css`
- **Tiempos:** `timeline.js` (cada escena está comentada con su rango en segundos)

```bash
npm install
npx serve .                           # vista previa en loop: abrir la URL que muestra (agregar ?format=portrait para 9:16)
node render.mjs                       # renderiza 16:9 y 9:16 en out/
node render.mjs --format portrait     # solo 9:16
node render.mjs --stills 2.9,6.9 --out /tmp/frames   # PNG sueltos para revisar
```

Requisitos: Node 18+, ffmpeg y Chromium para Playwright (`npx playwright install chromium`).
