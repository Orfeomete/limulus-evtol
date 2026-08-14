#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IKILI TILTIN "SABIT SAPMA" DAVRANISI — karar 27'nin son acik maddesi

F2 sunu olcmustu: ikili tilt politikasinin tilt eylemi neredeyse sabit
(std/genlik = 0,20) ve bu sabiti KALDIRMAK bes tohumda da basarimi
ARTIRIYOR. Yani politika zararli bir sabit yaziyor.

SORULAR
  1  Sabitin fiziksel karsiligi ne?  e -> tilt = ankraj + 30 x e derece
  2  On ve arka kanallar AYNI yonde mi (ortak kip = program duzeltmesi)
     yoksa ZIT yonde mi (diferansiyel = yunuslama trimi)?
  3  Tohumlar arasinda isaret tutarli mi?
  4  LIMULUS'un dort kanali ayni soruya ne diyor?

Eylem uzayi: e[0:4] itki, e[4] on cift tilt, e[5] arka cift tilt
(ikili). LIMULUS'ta e[4:8] dort bagimsiz kanal (grup sirasi
tilt_gruplari'ndan gelir).
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

_B = os.path.dirname(os.path.abspath(__file__))
for _y in ("../dinamik", "../ogrenme"):
    _t = os.path.normpath(os.path.join(_B, _y))
    if _t not in sys.path:
        sys.path.insert(0, _t)

import torch                                            # noqa: E402
from egitim_v2 import KosanNorm, Politika2              # noqa: E402
from ortam import MUFREDAT, LimulusOrtami               # noqa: E402

KOSU = os.path.join(_B, "..", "ogrenme", "kosular_v2")
SEVIYE = 2
BOLUM = 5
YETKI = 30.0                       # derece, KTH_YETKI


def yukle(varyant, tohum):
    kok = os.path.join(KOSU, f"{varyant}_t{tohum}")
    if not os.path.exists(kok + ".pt"):
        return None
    j = json.load(open(kok + "_gunluk.json"))
    o = LimulusOrtami(varyant=varyant, seviye=SEVIYE, tohum=tohum, sensor=True)
    o.seviye = SEVIYE
    o.gorev = MUFREDAT[SEVIYE]
    pol = Politika2(o.observation_space.shape[0], o.n_eylem,
                    j["ayar"]["gizli"], j["ayar"]["log_std0"], None)
    pol.load_state_dict(torch.load(kok + ".pt", map_location="cpu"))
    pol.eval()
    norm = None
    if j.get("gozlem_norm"):
        norm = KosanNorm(o.observation_space.shape[0])
        norm.ort = np.array(j["gozlem_norm"]["ort"])
        norm.var = np.array(j["gozlem_norm"]["var"])
        norm.sayac = j["gozlem_norm"]["sayac"]
        norm.acik = False
    return pol, norm, o


def iz_topla(pol, norm, o, tohum):
    ham, _ = o.reset(seed=int(tohum))
    g = norm(ham) if norm else ham
    iz = []
    while True:
        e, _, _ = pol.eylem(g, ornekle=False)
        e = np.clip(e, -1.0, 1.0)
        iz.append(e.copy())
        ham, r, bitti, kesildi, _ = o.step(e)
        g = norm(ham) if norm else ham
        if bitti or kesildi:
            break
    return np.array(iz)


def main():
    print("=" * 84)
    print("IKILI TILT SABIT SAPMASI — fiziksel karsiligi ve yapisi")
    print(f"Seviye {SEVIYE} ({MUFREDAT[SEVIYE].ad}), {BOLUM} bolum, deterministik")
    print("=" * 84)

    for varyant, n_ch, adlar in (("ikili", 2, ("on cift", "arka cift")),
                                 ("limulus", 4, ("sol on", "sag on",
                                                 "sol arka", "sag arka"))):
        print(f"\n### {varyant.upper()}  (tilt sapmasi derece, ankraja gore)")
        print(f"{'tohum':>6}" + "".join(f"{a:>12}" for a in adlar)
              + f"{'ortak kip':>12}{'dif. kip':>10}")
        print("-" * 84)
        ortaklar, difler = [], []
        for t in range(5):
            y = yukle(varyant, t)
            if y is None:
                continue
            pol, norm, o = y
            izler = [iz_topla(pol, norm, o, 100 + b) for b in range(BOLUM)]
            iz = np.concatenate(izler, axis=0)
            tilt = iz[:, 4:4 + n_ch] * YETKI            # derece
            ort = tilt.mean(axis=0)
            ortak = float(ort.mean())
            if n_ch == 2:
                dif = float(ort[0] - ort[1]) / 2.0       # on - arka
            else:
                dif = float((ort[0] + ort[1]) / 2 - (ort[2] + ort[3]) / 2) / 2.0
            ortaklar.append(ortak); difler.append(dif)
            print(f"{t:>6}" + "".join(f"{x:>12.2f}" for x in ort)
                  + f"{ortak:>12.2f}{dif:>10.2f}")
        o_a, d_a = np.array(ortaklar), np.array(difler)
        print("-" * 84)
        print(f"{'ORT':>6}{'':>{12*n_ch}}{o_a.mean():>12.2f}{d_a.mean():>10.2f}")
        print(f"{'STD':>6}{'':>{12*n_ch}}{o_a.std(ddof=1):>12.2f}"
              f"{d_a.std(ddof=1):>10.2f}")
        ayni_isaret_o = np.all(o_a > 0) or np.all(o_a < 0)
        ayni_isaret_d = np.all(d_a > 0) or np.all(d_a < 0)
        print(f"       ortak kip isareti  {'TUTARLI' if ayni_isaret_o else 'tutarsiz'}"
              f"   ·   diferansiyel isareti  "
              f"{'TUTARLI' if ayni_isaret_d else 'tutarsiz'}")

    print()
    print("=" * 84)
    print("OKUMA REHBERI")
    print("=" * 84)
    print("  ortak kip  > 0  : politika tilt programini one (cruise yonune) itiyor")
    print("  ortak kip  < 0  : programi geri (hover yonune) cekiyor")
    print("  dif. kip   != 0 : on/arka ayrismasi, yani yunuslama trim duzeltmesi")
    print("  Tohumlar arasi TUTARLILIK, sapmaya sistematik bir neden isaret eder;")
    print("  tutarsizlik ogrenme gurultusu demektir.")


if __name__ == "__main__":
    main()
