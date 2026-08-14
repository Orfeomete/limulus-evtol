#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARAR 51 KURAL 5 — karar 45'in olcumu sicak baslangicla tekrar.

Ön kayit `4-KARARLAR/51-sicak-baslangic-on-kaydi.md`, kural 5. Karar 45'in
yan kayma karsilastirmasindaki 2,4 katlik aykirilik, karar 43'teki iki puanlik
eksiklikle AYNI cozucu kusurunun urunudur. Bu betik o olcumu sicak baslangicla
tekrarlar.

⚠️ KARAR 45 BETA SERBEST KOSULDU (`beta_hedef=None`), karar 43 ise beta = 0
zorluyordu. Bu yuzden bu betik ayri bir dosyadir ve kabul sinamasinin hedefi de
ayridir. Kural 1'in mantigi aynen gecerli, ek baslangic verilmeden karar 45'in
sayilari uretilmelidir.

Yardimci fonksiyonlar `olcum_sicak_baslangic.py`'den alinir, kopyalanmaz.

Kosum
    cd 9-DIJITAL-IKIZ && python3 testler/olcum_sicak_baslangic_k45.py
Cikti
    cikti_asimetrik/s1_sicak_baslangic_k45.json
"""
import json
import os
import sys
import time
from multiprocessing import Pool

_BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BURASI)
_KOK = os.path.dirname(_BURASI)
sys.path.insert(0, os.path.join(_KOK, "dinamik"))

from olcum_sicak_baslangic import (CIKTI, HIZLAR, PODLAR, _kayit, _kur,  # noqa
                                  _tavan, _x_vektoru)

ADLAR = ("limulus", "ikili", "senkron")
# Karar 45'in raporladigi degerler, (kapanan durum, kesisimde ort |beta|).
KARAR45 = {
    "guc": {"limulus": (34, 14.23), "ikili": (34, 17.45), "senkron": (11, 4.47)},
    "yankayma": {"limulus": (34, 1.56), "ikili": (34, 0.66),
                 "senkron": (6, 0.23)},
}


def _soguk(arg):
    ad, pod, V, kip = arg
    import trim
    ac = _kur(ad)
    r = trim.trim_yanal(ac, V, ariza=pod, beta_hedef=None, amac_kip=kip)
    return _kayit(r, _tavan(ac, V), varyant=ad, pod=pod, V=V, sicak=False)


def _sicak(arg):
    pod, V, kip = arg
    import trim
    ac2 = _kur("ikili")
    r2 = trim.trim_yanal(ac2, V, ariza=pod, beta_hedef=None, amac_kip=kip)
    ek = [_x_vektoru(r2, 4)] if r2.tilt is not None else []
    ac4 = _kur("limulus")
    r4 = trim.trim_yanal(ac4, V, ariza=pod, beta_hedef=None, amac_kip=kip,
                         ek_baslangic=ek or None)
    return (_kayit(r2, _tavan(ac2, V), varyant="ikili", pod=pod, V=V,
                   sicak=False),
            _kayit(r4, _tavan(ac4, V), varyant="limulus", pod=pod, V=V,
                   sicak=True))


def _kos(isler, fn, etiket):
    t0 = time.time()
    with Pool(processes=max(1, os.cpu_count() or 2)) as p:
        out = p.map(fn, isler)
    print(f"  {etiket}: {len(isler)} is, {time.time() - t0:.1f} s", flush=True)
    return out


def _anah(k):
    return (k["pod"], k["V"])


def _ort_kesisimde(a_kay, b_kay):
    """KESISIM uzerinde ortalama |beta|. Karar 45 Tablo 4'un tabani budur."""
    ka = {_anah(k) for k in a_kay if k["basarili"]}
    kb = {_anah(k) for k in b_kay if k["basarili"]}
    kes = ka & kb

    def o(ks):
        v = [abs(k["beta_derece"]) for k in ks
             if k["basarili"] and _anah(k) in kes]
        return sum(v) / max(1, len(v))
    return o(a_kay), o(b_kay), len(kes)


def main():
    os.makedirs(CIKTI, exist_ok=True)
    print("=" * 72)
    print("KARAR 51 KURAL 5 — karar 45 yeniden olcumu, BETA SERBEST")
    print("=" * 72)
    cikti = {}

    # --- kabul sinamasi, iki kipte de soguk ---
    soguk = {}
    for kip in ("guc", "yankayma"):
        isler = [(ad, p, V, kip) for ad in ADLAR for p in PODLAR for V in HIZLAR]
        kay = _kos(isler, _soguk, f"soguk {kip}")
        soguk[kip] = kay
        print(f"  KABUL SINAMASI, kip {kip}", flush=True)
        gecti = True
        ayrinti = {}
        # karar 45 ortalamalari LIMULUS ile IKILI kesisiminde alinmisti
        lim = [k for k in kay if k["varyant"] == "limulus"]
        iki = [k for k in kay if k["varyant"] == "ikili"]
        o4, o2, n_kes = _ort_kesisimde(lim, iki)
        for ad in ADLAR:
            ks = [k for k in kay if k["varyant"] == ad]
            n = sum(1 for k in ks if k["basarili"])
            if ad == "limulus":
                om = o4
            elif ad == "ikili":
                om = o2
            else:
                v = [abs(k["beta_derece"]) for k in ks if k["basarili"]]
                om = sum(v) / max(1, len(v))
            bn, bb = KARAR45[kip][ad]
            ok = (n == bn) and abs(om - bb) < 0.51
            gecti &= ok
            ayrinti[ad] = dict(kapanan=n, karar45_kapanan=bn,
                               ort_beta=om, karar45_ort_beta=bb, gecti=bool(ok))
            print(f"    {'✅' if ok else '⚠️'} {ad:<9} kapanan {n:>3} "
                  f"(karar 45 {bn:>3}) · kesisimde ort |beta| {om:6.2f} "
                  f"(karar 45 {bb:6.2f})", flush=True)
        print(f"    kesisim {n_kes} durum · kabul "
              f"{'GECTI' if gecti else 'GECMEDI, sapma raporlanir'}", flush=True)
        cikti[f"soguk_{kip}"] = dict(kabul=ayrinti, kabul_gecti=bool(gecti),
                                     kesisim=n_kes, kayitlar=kay)

    # --- sicak, yan kayma kipinde ---
    print("  SICAK BASLANGIC, kip yankayma", flush=True)
    ciftler = _kos([(p, V, "yankayma") for p in PODLAR for V in HIZLAR],
                   _sicak, "sicak yankayma")
    iki_s = [c[0] for c in ciftler]
    lim_s = [c[1] for c in ciftler]
    o4, o2, n_kes = _ort_kesisimde(lim_s, iki_s)
    n4 = sum(1 for k in lim_s if k["basarili"])
    n2 = sum(1 for k in iki_s if k["basarili"])
    oran = o4 / o2 if o2 > 0 else float("nan")
    print(f"    limulus {n4}/108 · ikili {n2}/108 · kesisim {n_kes}")
    print(f"    kesisimde ort |beta|  limulus {o4:.2f} · ikili {o2:.2f} · "
          f"oran {oran:.3f}")
    print(f"    karar 45 sogukta 1,56 / 0,66 = 2,364")
    # kural 2, matematiksel taban da yan kaymada gecerli
    kap_s = {_anah(k) for k in lim_s if k["basarili"]}
    kap_i = {_anah(k) for k in iki_s if k["basarili"]}
    kap_soguk_lim = {_anah(k) for k in soguk["yankayma"]
                     if k["varyant"] == "limulus" and k["basarili"]}
    eksik = sorted((kap_i | kap_soguk_lim) - kap_s)
    print(f"    KURAL 2 {'✅ GECTI' if not eksik else '❌ GECMEDI'}"
          + (f", kapanmayan {len(eksik)}: {eksik}" if eksik else ""))
    cikti["sicak_yankayma"] = dict(
        n_limulus=n4, n_ikili=n2, kesisim=n_kes,
        ort_beta_limulus=o4, ort_beta_ikili=o2, oran=oran,
        kural2_gecti=not eksik, kapanmayan=eksik,
        limulus_sicak=lim_s, ikili=iki_s)

    yol = os.path.join(CIKTI, "s1_sicak_baslangic_k45.json")
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(cikti, f)
    print(f"\nyazildi {yol}")


if __name__ == "__main__":
    main()
