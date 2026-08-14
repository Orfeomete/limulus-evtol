#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARAR 45 — yan kaymayi en kucukleyen amac fonksiyonu.

Ön kayit `4-KARARLAR/45-yan-kayma-amac-fonksiyonu-on-kaydi.md`. Karar kurallari
sonuclar gorulmeden donduruldu, bu betik yalniz o kurallarin sordugu sayilari
uretir ve hicbir esik ya da yorum icermez.

Soru: yan kaymayi DOGRUDAN en kucukleyen bir amac fonksiyonu altinda, dort eksen
ile iki eksen arasindaki yan kayma farki kaliyor mu. Karar 21 uc kat fark bulmustu
(-5,63 dereceye karsi -18,60) fakat o olcum gucu en aza indiriyordu.

Izgara karar 43'un izgarasidir, 27 hiz x 4 pod = varyant basina 108 durum.
beta_hedef=None, yani yan kayma SERBEST — zorunlu sifirda soru anlamsiz.

Kosum
    cd 9-DIJITAL-IKIZ && python3 testler/olcum_yan_kayma_amaci.py
Cikti
    cikti_asimetrik/k45_yan_kayma_amaci.json
"""
import json
import math
import os
import sys
import time
from multiprocessing import Pool

_BURASI = os.path.dirname(os.path.abspath(__file__))
_KOK = os.path.dirname(_BURASI)
sys.path.insert(0, os.path.join(_KOK, "dinamik"))
CIKTI = os.path.join(_KOK, "cikti_asimetrik")

VARYANTLAR = ("limulus", "ikili", "senkron", "liftcruise")
HIZLAR = [5.0 + 2.5 * i for i in range(27)]
PODLAR = (0, 1, 2, 3)
KIPLER = ("guc", "yankayma")


def _kur(ad):
    """⚠️ B4 bayragi metrikler.py ile AYNI okunur (karar 22, 32)."""
    from arac import Limulus
    b = os.environ.get("LIMULUS_CRUISE_ITKI", "0") == "1"
    return Limulus(varyant_ad=ad, cruise_itki_etkin=b)


def _is(arg):
    ad, pod, V, kip = arg
    import trim
    ac = _kur(ad)
    r = trim.trim_yanal(ac, V, ariza=pod, beta_hedef=None, amac_kip=kip)
    tilt = [math.degrees(float(t)) for t in r.tilt] if r.tilt is not None else []
    return dict(varyant=ad, pod=pod, V=V, amac_kip=kip,
                basarili=bool(r.basarili), artik=float(r.artik),
                beta_derece=math.degrees(float(r.beta)),
                phi_derece=math.degrees(float(r.phi)),
                P_batarya_kW=float(r.P_batarya) / 1e3,
                tilt_yayilimi=float(max(tilt) - min(tilt)) if tilt else 0.0)


def ozet(kayitlar, kip):
    """Kural 3: karsilastirma yalniz IKISININ DE kapattigi noktalarda."""
    tab = {}
    for ad in VARYANTLAR:
        tab[ad] = {(k["pod"], k["V"]): k for k in kayitlar
                   if k["varyant"] == ad and k["amac_kip"] == kip
                   and k["basarili"]}
    print(f"\n  AMAC KIPI = {kip}")
    print(f"  {'varyant':<12}{'kapanan':>9}{'ort |beta|':>13}"
          f"{'azami |beta|':>14}{'ort guc kW':>13}")
    for ad in VARYANTLAR:
        d = tab[ad]
        if not d:
            print(f"  {ad:<12}{0:>5}/108{'—':>13}{'—':>14}{'—':>13}")
            continue
        b = [abs(k["beta_derece"]) for k in d.values()]
        p = [k["P_batarya_kW"] for k in d.values()]
        print(f"  {ad:<12}{len(d):>5}/108{sum(b)/len(b):>12.2f}°"
              f"{max(b):>13.2f}°{sum(p)/len(p):>13.1f}")
    return tab


def kesisim_karsilastirmasi(tab, a="limulus", b="ikili"):
    """Kural 2 ve 3: ortak noktalarda dort eksen ile iki eksen."""
    ortak = sorted(set(tab[a]) & set(tab[b]))
    if not ortak:
        print(f"  {a} ile {b} ortak kapanan nokta YOK")
        return None
    ba = [abs(tab[a][k]["beta_derece"]) for k in ortak]
    bb = [abs(tab[b][k]["beta_derece"]) for k in ortak]
    oa, ob = sum(ba) / len(ba), sum(bb) / len(bb)
    print(f"  ortak nokta {len(ortak)} · {a} ort |beta| {oa:.2f}° · "
          f"{b} ort |beta| {ob:.2f}° · oran {oa / ob if ob else float('nan'):.3f}")
    print(f"  kural 2 esigi: {a} <= 0,5 x {b} yani {oa:.2f} <= {0.5 * ob:.2f}  "
          f"{'SAGLANDI' if oa <= 0.5 * ob else 'SAGLANMADI'}")
    return dict(ortak_nokta=len(ortak), ort_a=oa, ort_b=ob,
                oran=oa / ob if ob else None,
                kural2=bool(oa <= 0.5 * ob))


def main():
    os.makedirs(CIKTI, exist_ok=True)
    isler = [(ad, pod, V, kip) for kip in KIPLER for ad in VARYANTLAR
             for pod in PODLAR for V in HIZLAR]
    print(f"KARAR 45 — yan kayma amac fonksiyonu, {len(isler)} cozum")
    t0 = time.time()
    with Pool(processes=max(1, (os.cpu_count() or 2))) as p:
        kayitlar = p.map(_is, isler, chunksize=4)
    print(f"  {len(kayitlar)} cozum, {time.time() - t0:.0f} s")

    sonuc = {}
    for kip in KIPLER:
        tab = ozet(kayitlar, kip)
        print(f"  --- kural 2 ve 3, {kip} ---")
        sonuc[kip] = kesisim_karsilastirmasi(tab)

    yol = os.path.join(CIKTI, "k45_yan_kayma_amaci.json")
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(dict(izgara=dict(hizlar=HIZLAR, podlar=list(PODLAR),
                                   kipler=list(KIPLER),
                                   beta_hedef=None),
                       ozet=sonuc, kayitlar=kayitlar), f,
                  indent=1, ensure_ascii=False)
    print(f"\n{os.path.relpath(yol, _KOK)} yazildi")


if __name__ == "__main__":
    main()
