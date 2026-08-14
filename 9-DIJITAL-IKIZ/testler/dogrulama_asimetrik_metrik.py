#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOGRULAMA — metrikler.py'nin besinci metrigi karar 43 olcumunu ureti yor mu

Karar 43'un olcumu `testler/olcum_asimetrik.py` betigiyle yapildi ve sonucu
`cikti_asimetrik/s1_pod_arizasi.json` dosyasina yazildi. Tezin Tablo 16.5'i,
`k3_asimetrik_ariza` figuru ve M1 Tablo 1'in besinci satiri o dosyadan geliyor.

09.08.2026'da ayni olcum `ogrenme/metrikler.py` icine besinci politikasiz
metrik olarak tasindi. Bu betik iki uygulamanin AYNI sayiyi urettigini
dogrular. Amac su, metrik katmani bagimsiz bir kod yolu oldugu icin sessizce
farkli bir sayi uretebilir ve tez ile metrik tablosu birbirinden kopabilir.

⚠️ Bu bir ic tutarlilik kontroludur, mutlak dogruluk kontrolu degil. Iki yol
ayni yanlisi yapiyorsa bu betik gecer. Yaptigi is, iki yolun ayrismasini
yakalamak.

Kosum
    cd 9-DIJITAL-IKIZ && python3 testler/dogrulama_asimetrik_metrik.py
Sure
    varyant basina ~1 dakika, dort varyant ~4 dakika
"""
import json
import os
import sys

_BURASI = os.path.dirname(os.path.abspath(__file__))
_KOK = os.path.dirname(_BURASI)
sys.path.insert(0, os.path.join(_KOK, "ogrenme"))

VARYANTLAR = ("limulus", "ikili", "senkron", "liftcruise")
OLCUM = os.path.join(_KOK, "cikti_asimetrik", "s1_pod_arizasi.json")


def karar43_ozeti():
    """Karar 43 olcum dosyasindan beta = 0 alt kumesinin ozeti."""
    with open(OLCUM, encoding="utf-8") as f:
        d = json.load(f)
    out = {}
    for ad in VARYANTLAR:
        alt = [k for k in d["kayitlar"]
               if k["varyant"] == ad and not k["beta_serbest"]]
        ok = [k for k in alt if k["basarili"]]
        out[ad] = dict(
            kapanan=len(ok), denenen=len(alt),
            ilk_kapanan_V=min((k["V"] for k in ok), default=None),
            azami_tilt_yayilimi=max((k["tilt_yayilimi"] for k in ok),
                                    default=0.0),
        )
    return out


def main():
    if not os.path.exists(OLCUM):
        raise SystemExit(f"olcum dosyasi yok: {OLCUM}\n"
                         "once testler/olcum_asimetrik.py kosulur")
    import metrikler as M

    bek = karar43_ozeti()
    print("KARAR 43 OLCUMU ile METRIK KATMANI KARSILASTIRMASI")
    print(f"olcum dosyasi  {os.path.relpath(OLCUM, _KOK)}")
    print(f"{'varyant':<13}{'karar 43':>14}{'metrikler.py':>16}"
          f"{'ilk V':>14}{'tilt yayilimi':>18}{'sonuc':>8}")
    print("-" * 83)

    hata = 0
    for ad in VARYANTLAR:
        r = M.metrik_asimetrik_trim(ad)
        b = bek[ad]
        ayni = (r["kapanan"] == b["kapanan"]
                and r["denenen"] == b["denenen"]
                and r["ilk_kapanan_V"] == b["ilk_kapanan_V"]
                and abs(r["azami_tilt_yayilimi_derece"]
                        - b["azami_tilt_yayilimi"]) < 0.05)
        if not ayni:
            hata += 1
        print(f"{ad:<13}{b['kapanan']:>7}/{b['denenen']:<6}"
              f"{r['kapanan']:>9}/{r['denenen']:<6}"
              f"{str(b['ilk_kapanan_V']):>14}"
              f"{b['azami_tilt_yayilimi']:>17.2f}°"
              f"{'OK' if ayni else 'FARK':>8}")
        if not ayni:
            print(f"    beklenen {b}")
            print(f"    olculen  kapanan={r['kapanan']}/{r['denenen']} "
                  f"ilk={r['ilk_kapanan_V']} "
                  f"yayilim={r['azami_tilt_yayilimi_derece']:.2f}")

    # Tez tablosunun kendisi de ayni dosyadan geliyor, oranlar da denetlenir.
    print("\nTEZ TABLOSU (tab:sonuc-asimetrik) ile karsilastirma")
    TEZ = {"limulus": 31, "ikili": 33, "senkron": 12, "liftcruise": 0}
    for ad, yuzde in TEZ.items():
        o = round(100 * bek[ad]["kapanan"] / max(bek[ad]["denenen"], 1))
        ok = o == yuzde
        if not ok:
            hata += 1
        print(f"  {ad:<13} tez %{yuzde:<4} olcum %{o:<4} "
              f"{'OK' if ok else 'FARK'}")

    print()
    if hata:
        raise SystemExit(f"{hata} FARK bulundu, metrik katmani ile karar 43 "
                         "olcumu ayrismis")
    print("Tum kontroller gecti. Metrik katmani karar 43 olcumunu birebir "
          "uretiyor.")


if __name__ == "__main__":
    main()
