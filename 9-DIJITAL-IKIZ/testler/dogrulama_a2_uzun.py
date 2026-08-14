#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# A2-UZUN — dogrulama_a2_bozucu_reddi.py'nin uzun butceli kampanya surumu.
# Karar 38 bekleyen kalem: senkron t2 (seviye 4) dahil 3M politikalarinin gust olcumu.
# Iki fark: KOSU=kosular_uzun, LIMULUS_CRUISE_ITKI=1 (egitim fizigiyle ayni).
# Metodoloji birebir: duzeltilmis metrik (yalniz tam bolumler + hayatta kalma ayri), 8 bozucu tohumu.
import os as _os
_os.environ["LIMULUS_CRUISE_ITKI"] = "1"
"""
A2 — BOZUCU REDDI METRIGI

Gust altinda yorunge sapmasinin RMS'i. Kucuk iyi.

⚠️ IKI GOREVDE OLCULUYOR, GEREKCESI ONCEDEN YAZILDI.

`metrikler.metrik_bozucu_reddi` gorevi CRUISE olarak tanimliyor
(baslangic 68,9 m/s, 300 m). Fakat karar 26'da olculdu ki yirmi
politikanin tamami mufredatin SEVIYE 2'sinde (gecis) kaldi, cruise
seviyesini (3) hicbiri gormedi.

Cruise'da olcmek, politikalari hic egitilmedikleri rejimde sinamak
olur ve olculen sey bozucu reddi degil "gormedigi rejimde hayatta
kalabiliyor mu" olurdu.

Bu yuzden IKISI DE kosuluyor.

  GECIS + gust   politikanin OGRENDIGI rejim, bozucu eklenmis
  CRUISE + gust  metrigin ozgun tanimi, dagitim disi

Ikisi de raporlanir. Sonuc gorulmeden once hangisinin birincil
olacagina karar verildi: **GECIS**, cunku dagitim ici olan odur.

⚠️ METRIK KUSURU — ILK KOSUDA YAKALANDI VE DUZELTILDI.
Ham RMS, ERKEN OLMEYI ODULLENDIRIYOR. Bolum kisa biterse sapma
birikmeye vakit bulamiyor ve RMS kucuk cikiyor. Ilk kosuda limulus
cruise'da 153 adimda olup RMS 11,5 aldi, ikili 955 adim hayatta kalip
123,4 aldi — yani duseni "daha iyi" gosteriyordu.

Duzeltme: RMS yalnizca TAM SUREYI TAMAMLAYAN bolumler uzerinden
hesaplanir, hayatta kalma orani AYRI raporlanir. Hayatta kalamayan bir
konfigurasyonun dusuk RMS'i bir basari degildir.
"""

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
from ortam import Gorev, LimulusOrtami                  # noqa: E402

KOSU = os.path.join(_B, "..", "ogrenme", "kosular_uzun")
VARYANTLAR = ("limulus", "ikili", "senkron", "liftcruise")
N_BOZUCU_TOHUM = 8

GOREVLER = {
    "gecis": Gorev("gust_gecis", 30.0, 60.0, 300.0, gust="orta",
                   baslangic_V=0.0, baslangic_h=150.0),
    "cruise": Gorev("gust_cruise", 30.0, 68.9, 300.0, gust="orta",
                    baslangic_V=68.9, baslangic_h=300.0),
}


def yukle(varyant, tohum, gorev):
    kok = os.path.join(KOSU, f"{varyant}_t{tohum}")
    if not os.path.exists(kok + ".pt"):
        return None
    j = json.load(open(kok + "_gunluk.json"))
    o = LimulusOrtami(varyant=varyant, seviye=2, tohum=tohum, sensor=True)
    o._gorev_zorla = gorev      # ⚠️ o.gorev atamasi reset()te ezilir
    o.gorev = gorev
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


def sapma_rms(pol, norm, o, tohum):
    ham, _ = o.reset(seed=int(tohum))
    g = norm(ham) if norm else ham
    h_h, V_h, n = [], [], 0
    while True:
        e, _, _ = pol.eylem(g, ornekle=False)
        ham, r, bitti, kesildi, bi = o.step(np.clip(e, -1.0, 1.0))
        g = norm(ham) if norm else ham
        h_h.append(bi.get("irtifa_hatasi", 0.0))
        V_h.append(bi.get("hiz_hatasi", 0.0))
        n += 1
        if bitti or kesildi:
            break
    if not h_h:
        return None, 0, False
    tam = n >= int(o.gorev.sure / o.ac.dt) * 0.95
    return math.sqrt(np.mean(np.square(h_h)) + np.mean(np.square(V_h))), n, tam


def main():
    print("=" * 84)
    print("A2 — BOZUCU REDDI  (orta siddet gust, 30 s, deterministik politika)")
    print("=" * 84)
    sonuc = {}
    for gad, gorev in GOREVLER.items():
        print()
        print(f"### GOREV: {gad}"
              + ("   (dagitim ICI — politikalar bu seviyede egitildi)"
                 if gad == "gecis" else
                 "   ⚠️ dagitim DISI — hicbir politika bu seviyeyi gormedi"))
        print("-" * 84)
        print(f"{'varyant':<12}{'n politika':>11}{'RMS (tam)':>12}{'std':>10}"
              f"{'hayatta':>10}{'ort adim':>10}{'tam/toplam':>13}")
        print("-" * 84)
        for v in VARYANTLAR:
            r, uz, tam_r, n_tam = [], [], [], 0
            for t in range(5):
                y = yukle(v, t, gorev)
                if y is None:
                    continue
                pol, norm, o = y
                for bt in range(N_BOZUCU_TOHUM):
                    s, n, tam = sapma_rms(pol, norm, o, 1000 + bt)
                    if s is not None:
                        r.append(s); uz.append(n)
                        if tam:
                            tam_r.append(s); n_tam += 1
            if r:
                hk = 100.0 * n_tam / len(r)
                if tam_r:
                    a = np.array(tam_r)
                    sonuc[(gad, v)] = (a.mean(), a.std(ddof=1) if len(a) > 1
                                       else 0.0, hk, n_tam, len(r))
                    print(f"{v:<12}{len(r)//N_BOZUCU_TOHUM:>11}"
                          f"{a.mean():>12.2f}{(a.std(ddof=1) if len(a)>1 else 0):>10.2f}"
                          f"{hk:>9.0f}%{np.mean(uz):>10.0f}{n_tam:>8}/{len(r):<4}")
                else:
                    print(f"{v:<12}{len(r)//N_BOZUCU_TOHUM:>11}"
                          f"{'—':>12}{'—':>10}{hk:>9.0f}%{np.mean(uz):>10.0f}"
                          f"{0:>8}/{len(r):<4}   HICBIRI TAMAMLAYAMADI")
            else:
                print(f"{v:<12}{'politika yok':>11}")

    print()
    print("=" * 84)
    print("KARAR KURALI 2 — fark < 2 std ise 'fark yok'")
    print("=" * 84)
    for gad in GOREVLER:
        print(f"\n  [{gad}]")
        vs = [v for v in VARYANTLAR if (gad, v) in sonuc]
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                a, b = sonuc[(gad, vs[i])], sonuc[(gad, vs[j])]
                f = a[0] - b[0]; e = 2 * max(a[1], b[1])
                print(f"    {vs[i]:<11} vs {vs[j]:<11} fark {f:>+9.2f}  "
                      f"esik {e:>8.2f}  → "
                      f"{'FARK VAR' if abs(f) > e else 'fark yok'}")


if __name__ == "__main__":
    main()
