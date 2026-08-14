#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TILT KANALSIZ LIMULUS — F2 ABLASYONUNUN TEMIZ KARSILIGI (karar 27)

F2'nin sinari: ablasyon SONRADAN yapilan bir mudahaledir. Politika tilt
kanali ACIKKEN egitildi, kanali kapatmak onu egitim dagiliminin disina
cikarir. Temiz olcum, kanali HIC gormeden sifirdan egitilmis politikadir.

BU BETIK UC POPULASYONU KARSILASTIRIR (ayni musfredat seviyesi 2,
deterministik, 5 bolum x 5 tohum):

  TAM      kosular_v2/limulus   tilt kanali ACIK egitildi, ACIK kosuldu
  ABLASYON kosular_v2/limulus   ACIK egitildi, tilt eylemi SIFIRLANDI (F2)
  KANALSIZ kosular_tk/limulus   tilt kanali OLMADAN egitildi (yeni)

SORU. F2'de "LIMULUS'ta ablasyon etkisi buyuk ama isareti tutarsiz"
cikmisti ve iki aciklama ayirt edilemiyordu:
  (a) kanal gercek katki veriyor, kapatinca bozuluyor
  (b) politika kanala bagimli ama katki uretmiyor, dagilim disi kaldi
KANALSIZ populasyon bu ikisini ayirir: kanalsiz egitim TAM'dan kotu
degilse kanalin katkisi YOK demektir (b), kotuyse katki VAR demektir (a).
"""
from __future__ import annotations

import json
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

SEVIYE = 2
BOLUM = 5


def yukle(dizin, tohum, kanal_kapali):
    # ortam kurulumundan ONCE bayragi ayarla ve modulu taze yukle
    os.environ["LIMULUS_TILT_KANALI"] = "0" if kanal_kapali else "1"
    import importlib
    import ortam as ortam_mod
    importlib.reload(ortam_mod)
    kok = os.path.join(_B, "..", "ogrenme", dizin, f"limulus_t{tohum}")
    if not os.path.exists(kok + ".pt"):
        return None
    j = json.load(open(kok + "_gunluk.json"))
    o = ortam_mod.LimulusOrtami(varyant="limulus", seviye=SEVIYE,
                                tohum=tohum, sensor=True)
    o.seviye = SEVIYE
    o.gorev = ortam_mod.MUFREDAT[SEVIYE]
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


def kos(pol, norm, o, tohum, tilt_sifirla=False):
    ham, _ = o.reset(seed=int(tohum))
    g = norm(ham) if norm else ham
    toplam = 0.0
    while True:
        e, _, _ = pol.eylem(g, ornekle=False)
        e = np.clip(e, -1.0, 1.0)
        if tilt_sifirla and o.n_eylem > 4:
            e = e.copy(); e[4:] = 0.0
        ham, r, bitti, kesildi, _ = o.step(e)
        g = norm(ham) if norm else ham
        toplam += r
        if bitti or kesildi:
            break
    return toplam


def populasyon(dizin, kanal_kapali, tilt_sifirla=False):
    oduller = []
    for t in range(5):
        y = yukle(dizin, t, kanal_kapali)
        if y is None:
            continue
        pol, norm, o = y
        bolumler = [kos(pol, norm, o, 100 + b, tilt_sifirla)
                    for b in range(BOLUM)]
        oduller.append(float(np.mean(bolumler)))
    return np.array(oduller)


def main():
    print("=" * 78)
    print("TILT KANALSIZ LIMULUS — uc populasyonun karsilastirilmasi")
    print(f"Mufredat seviyesi {SEVIYE}, {BOLUM} bolum, deterministik politika")
    print("=" * 78)

    tam = populasyon("kosular_v2", kanal_kapali=False)
    abl = populasyon("kosular_v2", kanal_kapali=False, tilt_sifirla=True)
    knl = populasyon("kosular_tk", kanal_kapali=True)

    print(f"\n{'populasyon':<34}{'ort odul':>10}{'std':>9}   tohumlar")
    print("-" * 78)
    for ad, d in (("TAM (acik egitim, acik kosum)", tam),
                  ("ABLASYON (acik egitim, tilt=0)", abl),
                  ("KANALSIZ (kanalsiz egitim)", knl)):
        print(f"{ad:<34}{d.mean():>10.1f}{d.std(ddof=1):>9.1f}   "
              + " ".join(f"{x:+7.1f}" for x in d))

    print()
    print("=" * 78)
    print("KARAR KURALI 2 — fark < 2 std ise 'fark yok'")
    print("=" * 78)
    for a_ad, a, b_ad, b in (("KANALSIZ", knl, "TAM", tam),
                             ("KANALSIZ", knl, "ABLASYON", abl)):
        f = a.mean() - b.mean()
        esik = 2 * max(a.std(ddof=1), b.std(ddof=1))
        print(f"  {a_ad:<9} vs {b_ad:<9} fark {f:>+8.1f}  esik {esik:>7.1f}  -> "
              f"{'FARK VAR' if abs(f) > esik else 'fark yok'}")

    print()
    print("YORUM")
    print("=" * 78)
    f = knl.mean() - tam.mean()
    esik = 2 * max(knl.std(ddof=1), tam.std(ddof=1))
    if f > esik:
        print("  KANALSIZ, TAM'dan IYI -> kanal ogrenmeyi ZORLASTIRIYOR,")
        print("  katki uretmiyor. Karar 26'daki yuksek varyansla tutarli.")
    elif f < -esik:
        print("  KANALSIZ, TAM'dan KOTU -> kanal gercek katki uretiyor,")
        print("  F2'nin (a) aciklamasi destekleniyor.")
    else:
        print("  Fark yok -> tilt kanali politikaya OLCULEBILIR katki")
        print("  vermiyor. F2'nin (b) aciklamasi destekleniyor: politika")
        print("  kanala bagimliydi ama kanal kazanc uretmiyordu.")


if __name__ == "__main__":
    main()
