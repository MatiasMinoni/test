#!/usr/bin/env python3
"""Música y efectos del video AdsGPT, sintetizados desde cero y sincronizados con cues.js.

    python3 audio/score.py out/AdsGPT_musica_30s.wav

Tema en La menor a 128 BPM (16 compases = 30 s, dos por escena):
  compases 1-2    intro: golpe grave, pads, pulsos y subida hacia el drop
  compases 3-12   groove: bombo en negras, bajo con sidechain y pads; desde el 5 suman palmas, hats y arpegio
  compás 13       quiebre: sin batería, pad abierto (comparación)
  compás 14       build: redoble y riser hacia el cierre
  compases 15-16  golpe final, 4 notas para los bloques del logo y acorde que queda sonando
Encima van los efectos de interfaz (tipeo, clics, checks, escaneo, lanzamiento, etc.).
"""
import json
import os
import sys

import numpy as np
from scipy import signal

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, 'cues.js'), encoding='utf-8').read()
C = json.loads(src[src.index('{'):src.rindex('}') + 1])
BEAT = 60 / C['bpm']
BAR = 4 * BEAT
END = C['end']
N = int((END + 4) * SR)  # margen para colas; se recorta al final
rng = np.random.default_rng(11)

music = np.zeros((2, N))   # bus con sidechain
drums = np.zeros((2, N))
sfx = np.zeros((2, N))
verb = np.zeros((2, N))    # envío a reverb


def note(name):
    names = {'C': -9, 'C#': -8, 'D': -7, 'D#': -6, 'E': -5, 'F': -4, 'F#': -3, 'G': -2, 'G#': -1, 'A': 0, 'A#': 1, 'B': 2}
    n, octv = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[n] + 12 * (octv - 4)) / 12)


def tt(d):
    return np.arange(int(d * SR)) / SR


def fade(x, a=.003, r=.006):
    n = x.shape[-1]
    ia, ir = min(n, int(a * SR)), min(n, int(r * SR))
    env = np.ones(n)
    if ia:
        env[:ia] = np.linspace(0, 1, ia)
    if ir:
        env[n - ir:] *= np.linspace(1, 0, ir)
    return x * env


def noise(d):
    return rng.standard_normal(int(d * SR))


def sos(kind, f, order=2):
    return signal.butter(order, f, kind, fs=SR, output='sos')


def lp(x, f, order=2):
    return signal.sosfilt(sos('low', f, order), x)


def hp(x, f, order=2):
    return signal.sosfilt(sos('high', f, order), x)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(sos('band', [lo, hi], order), x)


def place(bus, sig, t0, gain=1.0, pan=0.0, send=0.0):
    """Suma una señal mono o estéreo en el bus, con paneo de potencia constante y envío a reverb."""
    sig = np.asarray(sig, dtype=float) * gain
    if sig.ndim == 1:
        a = (pan + 1) * np.pi / 4
        sig = np.vstack([sig * np.cos(a), sig * np.sin(a)]) * np.sqrt(2)
    i0 = int(round(t0 * SR))
    if i0 < 0:
        sig, i0 = sig[:, -i0:], 0
    n = min(sig.shape[1], N - i0)
    bus[:, i0:i0 + n] += sig[:, :n]
    if send:
        verb[:, i0:i0 + n] += sig[:, :n] * send


def saw(f, t, fmax=7000, decay=None):
    """Diente de sierra limitado en banda (aditivo). decay: amortiguación extra por armónico (pluck)."""
    out = np.zeros_like(t)
    k = max(1, int(fmax // f))
    ph = rng.uniform(0, 2 * np.pi)
    for n in range(1, k + 1):
        a = 1 / n
        if decay is not None:
            a = a * np.exp(-t * decay * n)
        out += a * np.sin(2 * np.pi * f * n * t + ph * n)
    return out * .6


def swept_noise(d, f_start, f_end, q=.35, shape=None):
    """Ruido con un filtro pasabanda que se mueve en el tiempo (vía STFT)."""
    x = noise(d)
    nper = 1024
    f, frames, Z = signal.stft(x, SR, nperseg=nper)
    pos = frames / max(d, 1e-6)
    if shape is None:
        fc = f_start * (f_end / f_start) ** np.clip(pos, 0, 1)
    else:
        fc = shape(np.clip(pos, 0, 1))
    lf = np.log2(np.maximum(f, 20))[:, None]
    mask = np.exp(-((lf - np.log2(fc)[None, :]) ** 2) / (2 * (q * 2) ** 2))
    _, y = signal.istft(Z * mask, SR, nperseg=nper)
    y = y[:len(x)]
    return y / (np.max(np.abs(y)) + 1e-9)


# ---------------------------------------------------------------- instrumentos
def kick():
    t = tt(.5)
    f = 46 + 125 * np.exp(-t / .028)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .2)
    click = hp(noise(.5), 3000) * np.exp(-t / .003) * .35
    return fade(np.tanh(1.8 * (body + click)) * .9)


def clap():
    t = tt(.4)
    x = np.zeros_like(t)
    for off in (0, .011, .023):
        i = int(off * SR)
        x[i:] += bp(noise(.4), 1000, 4200)[:len(t) - i] * np.exp(-t[:len(t) - i] / .007)
    x += bp(noise(.4), 900, 3800) * np.exp(-t / .13) * .55
    return fade(x * .5)


def hat(open_=False):
    d = .25 if open_ else .08
    t = tt(d)
    x = lp(hp(noise(d), 7200), 13000) * np.exp(-t / (.085 if open_ else .022))
    return fade(x * .4)


def bass(f, d=.2):
    t = tt(d)
    body = saw(f, t, fmax=1400)
    x = lp(body, 420) + lp(body, 1600) * np.exp(-t / .04) * .5 + np.sin(2 * np.pi * f * t) * .55
    return fade(x * np.exp(-t / .16), .002, .02)


def pad(freqs, d, att=.35, rel=.5, cutoff=1700):
    t = tt(d + rel)
    st = np.zeros((2, len(t)))
    for f in freqs:
        for det, pan in ((-.09, -.7), (0, 0), (.09, .7)):
            v = saw(f * 2 ** (det / 12), t, fmax=5000)
            a = (pan + 1) * np.pi / 4
            st[0] += v * np.cos(a)
            st[1] += v * np.sin(a)
    st = np.vstack([lp(st[0], cutoff), lp(st[1], cutoff)])
    env = np.minimum(1, t / att) * np.where(t > d, np.exp(-(t - d) / (rel / 3)), 1)
    return fade(st * env / (len(freqs) * 2.2))


def pluck(f, d=.32):
    t = tt(d)
    x = saw(f, t, fmax=6000, decay=4.0) * np.exp(-t / .11)
    return fade(lp(x, 5000))


def bell(f, d=1.6, index=2.2, ratio=3.5):
    t = tt(d)
    mod = np.sin(2 * np.pi * f * ratio * t) * index * np.exp(-t / .25)
    x = np.sin(2 * np.pi * f * t + mod) * np.exp(-t / .55)
    return fade(x * .5)


def boom(d=2.6, f0=70, f1=30, tau=1.0):
    t = tt(d)
    f = f1 + (f0 - f1) * np.exp(-t / .3)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau)
    x += lp(noise(d), 260) * np.exp(-t / .35) * .35
    return fade(np.tanh(1.5 * x) * .9, .001, .3)


def impact(size=1.0):
    d = 3.2
    t = tt(d)
    x = boom(d, 75, 28, .9 * size)
    x += lp(noise(d), 5000) * np.exp(-t / .16) * .45
    metal = np.zeros_like(t)
    for f in (173, 287, 431, 577, 911, 1307):
        metal += np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * np.exp(-t / (1.2 * size))
    x += metal * .025 * size
    return fade(x)


def crash():
    d = 2.5
    t = tt(d)
    x = hp(noise(d), 4000) * np.exp(-t / .55) + bp(noise(d), 2500, 9000) * np.exp(-t / .2) * .6
    return fade(lp(x, 14000) * .3)


def reverse_swell(d=.7):
    t = tt(d)
    x = hp(noise(d), 2500) * (t / d) ** 3
    return fade(x * .35, .01, .004)


def riser(d):
    t = tt(d)
    x = swept_noise(d, 250, 9000, q=.45) * (t / d) ** 2.2 * .55
    f = 180 + 1300 * (t / d) ** 2
    trem = .6 + .4 * np.sin(2 * np.pi * np.cumsum(4 + 22 * (t / d) ** 2) / SR)
    x += np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 2.5 * trem * .16
    return fade(x, .02, .004)


def whoosh(d=.55, lo=350, hi=4200):
    t = tt(d)
    bell_ = np.sin(np.pi * t / d) ** 1.6
    shape = lambda p: lo * (hi / lo) ** np.sin(np.pi * p) ** 1.3
    x = swept_noise(d, lo, hi, q=.5, shape=shape) * bell_
    return fade(x * .55)


def tick():
    t = tt(.03)
    x = hp(noise(.03), 2600) * np.exp(-t / .0035) + np.sin(2 * np.pi * rng.uniform(3000, 3800) * t) * np.exp(-t / .008) * .25
    return fade(x * .35, .0005, .005)


def ui_click():
    t = tt(.12)
    f = 1100 + 900 * np.exp(-t / .01)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .025) * .5
    x += np.sin(2 * np.pi * 140 * t) * np.exp(-t / .03) * .6
    x += hp(noise(.12), 2000) * np.exp(-t / .003) * .4
    return fade(x * .7, .0005)


def blip(f, d=.18):
    t = tt(d)
    fr = f * (.72 + .28 * (1 - np.exp(-t / .012)))
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR) + .25 * np.sin(4 * np.pi * np.cumsum(fr) / SR)
    return fade(x * np.exp(-t / .06) * .45, .001)


def thump(f=60, d=.35):
    t = tt(d)
    fr = f + 60 * np.exp(-t / .02)
    return fade(np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / .1) * .8)


def ping(f=1318.5, d=.9):
    t = tt(d)
    x = np.sin(2 * np.pi * f * (1 - .01 * t) * t) * np.exp(-t / .22)
    return fade(x * .35)


# ---------------------------------------------------------------- arreglo
S = C['scenes']
MU = C['music']
bar_t = lambda b: b * BAR
A, Fm, Cm, G = 'A', 'F', 'C', 'G'
chords = {  # (raíz del bajo, notas del pad, notas del arpegio)
    A: ('A1', ['A3', 'C4', 'E4'], ['A4', 'C5', 'E5', 'A5']),
    Fm: ('F1', ['F3', 'A3', 'C4'], ['F4', 'A4', 'C5', 'F5']),
    Cm: ('C2', ['G3', 'C4', 'E4'], ['C5', 'E5', 'G5', 'C6']),
    G: ('G1', ['G3', 'B3', 'D4'], ['G4', 'B4', 'D5', 'G5']),
}
cycle = [A, Fm, Cm, G]
prog = {b: cycle[(b - MU['dropBar']) % 4] for b in range(MU['dropBar'], MU['endBar'])}

# Intro (compases 1-2): drone, pulsos y subida hacia el drop
place(drums, impact(.7), 0.0, .5, send=.35)
place(music, pad([note(n) for n in ('A2', 'E3', 'A3')], BAR - .1, att=1.0, rel=.6, cutoff=900), 0.0, .5, send=.4)
place(music, pad([note(n) for n in ('F2', 'C3', 'F3', 'A3')], BAR - .1, att=.6, rel=.4, cutoff=1300), BAR, .5, send=.4)
for k in (1, 2, 3):
    place(drums, thump(52, .4), k * BEAT, .3 + .08 * k)
for k in range(8):
    place(drums, thump(50, .25), BAR + k * BEAT / 2, .18 + .05 * k)
for t in C['question']:
    place(sfx, whoosh(.45, 400, 3200), t - .1, .22, pan=rng.uniform(-.5, .5), send=.2)
place(drums, boom(1.4, 85, 40, .45), C['answer'][0], .55, send=.3)
place(sfx, crash(), C['answer'][0], .25, send=.3)
place(sfx, whoosh(.5, 300, 2500), C['answer'][1] - .12, .25, pan=.3, send=.2)
place(sfx, riser(S[1] - C['answer'][0] - .2), C['answer'][0] + .2, .55)
place(sfx, reverse_swell(.8), S[1] - .8, .6)

# Drop (compás 3)
place(drums, impact(.9), S[1], .7, send=.4)
place(sfx, crash(), S[1], .45, send=.3)

# Groove (compases 3-12)
kicks = []
for b in range(MU['dropBar'], MU['grooveEndBar']):
    t0 = bar_t(b)
    for k in range(4):
        kicks.append(t0 + k * BEAT)
    if b >= MU['clapsBar']:
        for beat in (1, 3):
            place(drums, clap(), t0 + beat * BEAT, .55, send=.18)
    for s16 in range(16):
        tt16 = t0 + s16 * BEAT / 4
        if s16 % 4 == 2:
            place(drums, hat(True), tt16, .3, pan=.25)
        elif s16 % 4 != 0 and b >= MU['clapsBar']:
            place(drums, hat(), tt16, .2 + .07 * (s16 % 2), pan=-.2)
    root, padn, _ = chords[prog[b]]
    for b8 in range(1, 8, 2):  # bajo en los contratiempos de corchea
        place(music, bass(note(root), .22), t0 + b8 * BEAT / 2, .62)
    place(music, pad([note(n) for n in padn], BAR - .05, att=.25, rel=.35), t0, .5, send=.3)
# Bombos del build (dos primeros tiempos)
kicks += [bar_t(MU['buildBar']), bar_t(MU['buildBar']) + BEAT]
for k in kicks:
    place(drums, kick(), k, .95)

# Arpegio
for b in range(MU['arp'][0], MU['arp'][1]):
    t0 = bar_t(b)
    _, _, arp = chords[prog[b]]
    soft = b >= MU['breakdownBar']
    for s16 in range(16):
        f = note(arp[[0, 1, 2, 3, 2, 1, 2, 3][s16 % 8]])
        p = pluck(f) if not soft else lp(pluck(f), 1800)
        tt16 = t0 + s16 * BEAT / 4
        place(music, p, tt16, .2 if not soft else .16, pan=-.35 if s16 % 2 else .35, send=.2 if soft else .15)
        place(music, p, tt16 + 3 * BEAT / 4, .07, pan=.7 if s16 % 2 else -.7)  # eco ping-pong

# Quiebre (compás 13) y build (compás 14)
bd = bar_t(MU['breakdownBar'])
place(music, pad([note(n) for n in chords[Cm][1]], BAR, att=.6, rel=.3, cutoff=1100), bd, .55, send=.45)
place(music, np.sin(2 * np.pi * note('C2') * tt(BAR)) * np.exp(-tt(BAR) / 1.5) * .4, bd, .5)
bl = bar_t(MU['buildBar'])
place(music, pad([note(n) for n in chords[G][1]], BAR, att=.9, rel=.1, cutoff=2600), bl, .6, send=.35)
roll = []
t = bl + 2 * BEAT
while t < S[7] - 1e-6:
    roll.append(t)
    t += BEAT / 4 if t < bl + 3 * BEAT - 1e-6 else BEAT / 8
for i, t in enumerate(roll):
    place(drums, clap(), t, .18 + .5 * (i / len(roll)) ** 1.5, send=.15)
place(sfx, riser(S[7] - C['build'][0]), C['build'][0], .8)
place(sfx, reverse_swell(1.0), S[7] - 1.0, .7)

# Cortes entre escenas: whoosh que culmina en el tiempo fuerte
for i, b in enumerate(S[2:7]):
    place(sfx, whoosh(.5), b - .38, .5, pan=-.4 if i % 2 else .4, send=.2)

# Cierre (compases 15-16)
END_T = S[7]
place(drums, impact(1.4), END_T, 1.0, send=.55)
place(drums, kick(), END_T, 1.0)
place(sfx, crash(), END_T, .7, send=.4)
for t, n in zip(C['logoBlocks'], ('A4', 'C5', 'E5', 'A5')):
    place(sfx, bell(note(n), 1.8, index=1.6, ratio=2.0), t, .32, send=.45)
    place(sfx, pluck(note(n), .5), t, .3, send=.3)
    place(drums, thump(58, .3), t, .5)
final = [note(n) for n in ('A2', 'E3', 'A3', 'C4', 'E4', 'B4')]
place(music, pad(final, END - END_T + .2, att=.5, rel=1.2, cutoff=2400), END_T, .62, send=.5)
place(music, np.sin(2 * np.pi * note('A1') * tt(END - END_T + 1)) * np.exp(-tt(END - END_T + 1) / 2.6) * .5, END_T, .45)
place(sfx, whoosh(.6, 300, 3000), C['wordmark'] - .2, .3, pan=.2, send=.25)
place(sfx, bell(note('E6'), 1.5, index=.8), C['tagline'] + .35, .07, pan=.3, send=.5)
place(sfx, blip(note('A5')), C['cta'], .35, send=.35)

# ---------------------------------------------------------------- efectos de interfaz
n = len(C['url'])
t0, t1 = C['type']
for k in range(1, n + 1):
    place(sfx, tick(), t0 + (k - .5) / n * (t1 - t0), rng.uniform(.5, .85), pan=rng.uniform(-.25, .25))
for t in (C['clickLink'], C['clickPublish']):
    place(sfx, ui_click(), t - .015, .8)
place(sfx, blip(note('E5')), C['chipDetect'], .5, send=.2)
for i in range(6):
    place(sfx, blip(rng.uniform(1800, 2600), .05), C['status'] + .1 + i * BEAT / 2, .08, pan=rng.uniform(-.4, .4))
for i, t in enumerate(C['grid']):
    place(sfx, tick(), t, .5, pan=-.4 + .16 * i)
place(sfx, swept_noise(C['scan'][1] - C['scan'][0], 500, 6000, q=.3) * .2, C['scan'][0], .6, pan=-.2, send=.1)
for i in range(16):
    place(sfx, blip(rng.uniform(2200, 3600), .05), C['scan'][0] + .05 + i * BEAT / 4 * .9, .1, pan=rng.uniform(-.5, .5))
for t in C['detect']:
    place(sfx, blip(note('A5'), .12), t, .32, pan=-.3)
for t, nn in zip(C['results'], ('A4', 'C5', 'E5', 'A5')):
    place(sfx, blip(note(nn)), t, .5, send=.25)
for i in range(4):
    place(sfx, tick(), C['swatches'] + i * .05, .6, pan=.4)
for i, t in enumerate(C['skeleton']):
    place(sfx, whoosh(.35, 500, 3000), t - .05, .22, pan=(-.6, 0, .6)[i])
for i, t in enumerate(C['generate']):
    place(sfx, swept_noise(.5, 900, 7000, q=.25) * np.hanning(int(.5 * SR)) ** .5 * .35, t, .45, pan=(-.5, 0, .5)[i], send=.2)
    place(sfx, bell(note(('E6', 'A6', 'C7')[i]), .6, index=.6), t + .46, .06, pan=(-.5, 0, .5)[i], send=.3)
place(sfx, blip(note('A5')), C['aiBadge'], .45, send=.3)
for t in C['pings']:
    place(sfx, ping(), t, .5, send=.6)
place(sfx, thump(90, .25), S[4] + .3, .4)
for t, nn in zip(C['tags'], ('C5', 'E5', 'G5', 'A5')):
    place(sfx, blip(note(nn), .12), t, .28, pan=.3)
r0, r1 = C['reach']
tc = r0
while tc < r1:
    place(sfx, tick(), tc, .3, pan=.35)
    tc += .035 + .14 * ((tc - r0) / (r1 - r0)) ** 2
place(sfx, blip(note('E5'), .14), C['summary'], .35)
L = C['clickPublish']
place(sfx, swept_noise(.4, 300, 7000, q=.45) * np.linspace(.2, 1, int(.4 * SR)) ** 2, L + .08, .55, send=.3)
place(drums, boom(1.6, 90, 40, .5), C['success'], .7, send=.3)
for i, nn in enumerate(('C5', 'E5', 'G5', 'C6')):
    place(sfx, bell(note(nn), 1.4, index=1.2), C['success'] + i * .045, .2, pan=(-.3, -.1, .1, .3)[i], send=.5)
place(sfx, whoosh(.45, 400, 3000), C['dashboard'] - .2, .3, pan=.4, send=.2)
m0, m1 = C['metrics']
tc = m0
while tc < m1:
    place(sfx, tick(), tc, .22, pan=.4)
    tc += .04 + .16 * ((tc - m0) / (m1 - m0)) ** 2
for i, t in enumerate(C['cmpRows'][1:]):
    place(sfx, blip(note(('A4', 'C5', 'E5', 'A5')[i])), t, .5, send=.25)

# ---------------------------------------------------------------- mezcla
# Sidechain del bombo sobre la música
sc = np.ones(N)
tsamp = np.arange(N) / SR
for k in kicks + [S[7]]:
    i0 = int(k * SR)
    i1 = min(N, i0 + int(.45 * SR))
    seg = 1 - .65 * np.exp(-(tsamp[i0:i1] - k) / .11)
    sc[i0:i1] = np.minimum(sc[i0:i1], seg)
music *= sc

# Reverb por convolución (respuesta al impulso sintética, estéreo)
ir_t = tt(2.6)
ir = np.vstack([lp(noise(2.6), 6500) * np.exp(-ir_t / .42), lp(noise(2.6), 6500) * np.exp(-ir_t / .42)])
ir[:, :int(.02 * SR)] = 0
ir /= np.sqrt(np.sum(ir ** 2, axis=1, keepdims=True))
wet = np.vstack([signal.fftconvolve(verb[0], ir[0])[:N], signal.fftconvolve(verb[1], ir[1])[:N]])
wet = hp(wet, 180)

mixdown = music * .9 + drums * .95 + sfx * .9 + wet * .55
mixdown = np.vstack([hp(mixdown[0], 25), hp(mixdown[1], 25)])

# Recorte a 15 s con fundido final
mixdown = mixdown[:, :int(END * SR)]
fo = int(.35 * SR)
mixdown[:, -fo:] *= np.linspace(1, 0, fo) ** 1.5

# Nivel: normaliza por RMS y limita suave
rms = np.sqrt(np.mean(mixdown ** 2))
mixdown *= 0.16 / rms
mixdown = np.tanh(mixdown * 1.1) / np.tanh(1.1)
mixdown *= .93 / np.max(np.abs(mixdown))

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'out', 'AdsGPT_musica_30s.wav')
os.makedirs(os.path.dirname(out), exist_ok=True)
pcm = (mixdown.T * 32767).astype('<i2')
import wave
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f'audio -> {out} (pico {20 * np.log10(np.max(np.abs(mixdown))):.1f} dBFS, RMS {20 * np.log10(np.sqrt(np.mean(mixdown ** 2))):.1f} dBFS)')
