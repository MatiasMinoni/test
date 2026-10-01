// Hoja de tiempos compartida por la animación (timeline.js) y la música (audio/score.py).
// 128 BPM: 1 tiempo = 0,46875 s · 1 compás = 1,875 s · 16 compases = 30 s exactos.
// Cada escena dura dos compases y todos los cortes caen en el tiempo fuerte.
window.CUES = {
  "bpm": 128,
  "end": 30,
  "scenes": [0, 3.75, 7.5, 11.25, 15, 18.75, 22.5, 26.25],
  "music": { "dropBar": 2, "clapsBar": 4, "arp": [4, 13], "grooveEndBar": 12, "breakdownBar": 12, "buildBar": 13, "endBar": 14 },

  "question": [0.1, 0.62, 1.1],
  "answer": [1.875, 2.58],

  "type": [4.35, 5.45],
  "url": "instagram.com/citrica.skin",
  "clickLink": 6.094,
  "chipDetect": 6.2,
  "status": 6.4,

  "grid": [7.97, 8.06, 8.15, 8.24, 8.33, 8.42],
  "scan": [8.44, 9.7],
  "detect": [8.906, 9.375],
  "results": [8.672, 9.141, 9.609, 10.078],
  "swatches": 10.2,

  "skeleton": [11.48, 11.6, 11.72],
  "generate": [12.188, 12.422, 12.656],
  "aiBadge": 13.125,
  "sheen": 13.45,

  "audRows": [15.469, 15.938, 16.406, 16.875],
  "pings": [15.234, 16.172, 17.109],
  "age": [15.95, 16.65],
  "tags": [16.406, 16.523, 16.641, 16.758],
  "reach": [16.9, 18.2],

  "summary": 19.0,
  "clickPublish": 19.922,
  "success": 20.156,
  "dashboard": 20.625,
  "metrics": [20.9, 22.35],

  "cmpRows": [22.734, 23.203, 23.672, 24.141, 24.609],
  "build": [24.375, 26.25],

  "logoBlocks": [26.25, 26.367, 26.484, 26.602],
  "logoIcon": 26.72,
  "wordmark": 26.85,
  "tagline": 27.19,
  "cta": 27.66,
  "footer": 27.9
};
