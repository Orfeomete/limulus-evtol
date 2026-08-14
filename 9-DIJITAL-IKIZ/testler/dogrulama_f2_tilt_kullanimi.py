#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F2 — OGRENILMIS POLITIKA TILT KANALINI KULLANIYOR MU

NEDEN KRITIK. Karar 20 temel kontrolcuye tilt kanali eklemeyi denedi ve
basarisiz oldu. Karar 23, kapali cevrim senaryolarinin mimariler arasinda
fark uretemedigini gosterdi — cunku kontrolcu dort varyanta da birebir
ayni komutu veriyor. Karar 26'da ogrenme kosulari da anlamli fark
gostermedi.

Geriye tek soru kaliyor: politika, kontrolcunun kullanamadigi tilt
kanalini kullaniyor mu?

  Kullaniyorsa  → "fark yok" sonucu MIMARI hakkindadir, mimari
                  gercekten kazanim vermiyor demektir
  Kullanmiyorsa → "fark yok" sonucu POLITIKA hakkindadir, kanal
                  ogrenilmemis demektir ve mimari sinanmamis kalir

UC OLCUM, gucten zayifa.

  A  ABLASYON (en guclu). Politikayi kos, sonra tilt eylemlerini SIFIRA
     zorlayarak yeniden kos. Basarim dusmuyorsa kanal katki vermiyordur.
  B  DURUM BAGIMLILIGI. Tilt eylemi duruma gore degisiyor mu, yoksa
     sabit bir sapma mi. Sabitse kontrol degil, onyargidir.
  C  GENLIK. Tilt eylemi sifirdan ne kadar uzak. Itki kanaliyla
     karsilastirmali.

Eylem uzayi: e[0:4] itki, e[4:4+n_tilt] tilt. Sifir eylem trimi korur.
"""
from __future__ import annotations

import glob
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

KOSU_DIZIN = os.path.join(_B, "..", "ogrenme", "kosular_v2")
VARYANTLAR = ("limulus", "ikili", "senkron")            # liftcruise'da tilt yok
SEVIYE = 2                                              # gecis, hepsi ulasti
BOLUM = 5


def politika_yukle(varyant, tohum):
    kok = os.path.join(KOSU_DIZIN, f"{varyant}_t{tohum}")
    if not (os.path.exists(kok + ".pt") and os.path.exists(kok + "_gunluk.json")):
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
        norm.acik = False                # degerlendirmede dondurulur
    return pol, norm, o


def kos(pol, norm, o, tohum, tilt_sifirla=False):
    """Deterministik politika ile bir bolum. Eylem izini dondurur."""
    ham, _ = o.reset(seed=int(tohum))
    g = norm(ham) if norm else ham
    iz, toplam, adim = [], 0.0, 0
    while True:
        e, _, _ = pol.eylem(g, ornekle=False)          # ortalama eylem
        e = np.clip(e, -1.0, 1.0)
        iz.append(e.copy())
        if tilt_sifirla and o.n_tilt > 0:
            e = e.copy()
            e[4:4 + o.n_tilt] = 0.0                    # tilt kanali kapatildi
        ham, r, bitti, kesildi, _ = o.step(e)
        g = norm(ham) if norm else ham
        toplam += r
        adim += 1
        if bitti or kesildi:
            break
    return np.array(iz), toplam, adim


def main():
    print("=" * 80)
    print("F2 — POLITIKA TILT KANALINI KULLANIYOR MU")
    print(f"Mufredat seviyesi {SEVIYE} ({MUFREDAT[SEVIYE].ad}), "
          f"{BOLUM} bolum, deterministik politika")
    print("=" * 80)
    print(f"{'varyant':<10}{'tohum':>6}{'itki |e|':>10}{'tilt |e|':>10}"
          f"{'tilt std':>10}{'odul':>10}{'tilt=0 odul':>13}{'degisim':>10}")
    print("-" * 80)

    ozet = {}
    for v in VARYANTLAR:
        satirlar = []
        for t in range(5):
            y = politika_yukle(v, t)
            if y is None:
                continue
            pol, norm, o = y
            iz, od, _ = kos(pol, norm, o, t, tilt_sifirla=False)
            _, od0, _ = kos(pol, norm, o, t, tilt_sifirla=True)
            n = o.n_tilt
            itki = float(np.abs(iz[:, :4]).mean())
            tilt = float(np.abs(iz[:, 4:4 + n]).mean()) if n else 0.0
            tstd = float(iz[:, 4:4 + n].std()) if n else 0.0
            dg = od0 - od
            satirlar.append((itki, tilt, tstd, od, od0, dg))
            print(f"{v:<10}{t:>6}{itki:>10.3f}{tilt:>10.3f}{tstd:>10.3f}"
                  f"{od:>10.1f}{od0:>13.1f}{dg:>+10.1f}")
        if satirlar:
            a = np.array(satirlar)
            ozet[v] = a.mean(axis=0)
            print(f"{'  ORTALAMA':<16}{a[:,0].mean():>10.3f}{a[:,1].mean():>10.3f}"
                  f"{a[:,2].mean():>10.3f}{a[:,3].mean():>10.1f}"
                  f"{a[:,4].mean():>13.1f}{a[:,5].mean():>+10.1f}")
        print("-" * 80)

    print()
    print("YORUM")
    print("=" * 80)
    for v, m in ozet.items():
        itki, tilt, tstd, od, od0, dg = m
        oran = tilt / itki if itki > 1e-9 else 0.0
        # ablasyon etkisi, odulun kendi buyuklugune gore
        etki = abs(dg) / max(abs(od), 1e-6) * 100
        print(f"  {v:<10} tilt/itki genlik orani {oran:5.2f}   "
              f"tilt std {tstd:5.3f}   ablasyon etkisi %{etki:5.1f}")
    print()
    print("  Olcut. Ablasyon etkisi kucukse (%5'in altinda) politika tilt")
    print("  kanalini KULLANMIYOR demektir — kanali kapatmak basarimi")
    print("  degistirmiyorsa o kanal karar vermiyordur.")


if __name__ == "__main__":
    main()
