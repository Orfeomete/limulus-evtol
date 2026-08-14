#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARAR 51 — dort eksenli problemde SICAK BASLANGIC.

Ön kayit `4-KARARLAR/51-sicak-baslangic-on-kaydi.md`. Kurallar olcumden once
donduruldu, bu betik yalniz o kurallarin sordugu sayilari uretir.

SORUN. Karar 43'te dort eksenli varyant 108 durumun 34'unu, iki eksenli varyant
36'sini kapatmisti. Iki eksenin olurlu kumesi dort eksenin ALT KUMESI oldugundan
bu fizik olamaz, cozucu hakkinda bir ifadedir.

YAPILAN. `ikili` cozumleri `limulus` icin EK BASLANGIC olarak verilir.
`tilt_esle` iki serbestligi dort poda yaydigindan, `ikili` cozumunun tilt
vektoru `limulus` uzayinda dogrudan gecerli bir noktadir ve orada artik BIREBIR
AYNIDIR. Dolayisiyla yakinsama olcutu baslangicin kendisinde saglanmistir.

⚠️ COZUCU AYARLARI DONDURULMUS. maxiter, ftol, olcek ve 0,05 esigi karar 43'un
degerleridir. Sicak baslangic disinda hicbir sey degismez.

Kosum
    cd 9-DIJITAL-IKIZ && python3 testler/olcum_sicak_baslangic.py
    cd 9-DIJITAL-IKIZ && python3 testler/olcum_sicak_baslangic.py --kabul
Cikti
    cikti_asimetrik/s1_sicak_baslangic.json
    cikti_asimetrik/s1_kabul_sinamasi.json      (--kabul ile)
"""
import argparse
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

# ⚠️ Izgara karar 43 ile BIREBIR AYNI.
HIZLAR = [5.0 + 2.5 * i for i in range(27)]
PODLAR = (0, 1, 2, 3)
KADEME = "surekli"
# Karar 43'un raporladigi sayilar, kabul sinamasinin hedefi.
KARAR43 = {"limulus": 34, "ikili": 36, "senkron": 13, "liftcruise": 0}


def _kur(ad):
    from arac import Limulus
    b = os.environ.get("LIMULUS_CRUISE_ITKI", "0") == "1"
    return Limulus(varyant_ad=ad, cruise_itki_etkin=b)


def _tavan(ac, V):
    import atmosfer as atm
    hava = atm.isa(0.0)
    return ac.rotor.itki_limiti(ac.itki[0].guc_tavani(KADEME),
                                hava.rho, V, math.pi / 2)


def _kayit(r, tav, **ek):
    T = [float(t) for t in r.T]
    tilt = [math.degrees(float(t)) for t in r.tilt] if r.tilt is not None else []
    k = dict(basarili=bool(r.basarili), artik=float(r.artik),
             beta_derece=math.degrees(float(r.beta)),
             phi_derece=math.degrees(float(r.phi)),
             alfa_derece=math.degrees(float(r.alfa)),
             T=T, T_tavan=float(tav),
             kontrol_payi=float(1.0 - max(T) / tav) if tav > 0 else float("nan"),
             tilt_derece=tilt,
             tilt_yayilimi=float(max(tilt) - min(tilt)) if tilt else 0.0,
             P_batarya_kW=float(r.P_batarya) / 1e3)
    k.update(ek)
    return k


def _x_vektoru(r, n_tilt):
    """Cozumu `limulus` uzayinda bir baslangic vektorune cevirir.

    ⚠️ n_tilt = 4 icin tilt vektoru DOGRUDAN dort podun acisidir, cunku
    `limulus`ta `tilt_esle` birim eslemedir. Iki eksenli cozumun dort pod
    acisi bu uzayda gecerli bir noktadir, ON KAYITTAKI dayanak budur.
    """
    import numpy as np
    return np.concatenate([[float(r.alfa), float(r.beta), float(r.phi)],
                           np.asarray(r.T, float),
                           np.asarray(r.tilt, float)[:n_tilt]])


def _is_soguk(arg):
    """Ek baslangic VERILMEDEN, yani karar 43'un yolu."""
    ad, pod, V, kip = arg
    import trim
    ac = _kur(ad)
    r = trim.trim_yanal(ac, V, ariza=pod, beta_hedef=0.0, amac_kip=kip)
    return _kayit(r, _tavan(ac, V), varyant=ad, pod=pod, V=V, sicak=False)


def _is_sicak(arg):
    """`ikili` cozulur, sonra `limulus` o cozumle SICAK baslatilir."""
    pod, V, kip = arg
    import trim
    ac2 = _kur("ikili")
    r2 = trim.trim_yanal(ac2, V, ariza=pod, beta_hedef=0.0, amac_kip=kip)
    ek = []
    if r2.tilt is not None:
        ek.append(_x_vektoru(r2, 4))
    ac4 = _kur("limulus")
    r4 = trim.trim_yanal(ac4, V, ariza=pod, beta_hedef=0.0, amac_kip=kip,
                         ek_baslangic=ek or None)
    return (_kayit(r2, _tavan(ac2, V), varyant="ikili", pod=pod, V=V,
                   sicak=False),
            _kayit(r4, _tavan(ac4, V), varyant="limulus", pod=pod, V=V,
                   sicak=True, ek_baslangic_verildi=bool(ek)))


def _kos(isler, fn, etiket):
    t0 = time.time()
    with Pool(processes=max(1, os.cpu_count() or 2)) as p:
        out = p.map(fn, isler)
    print(f"  {etiket}: {len(isler)} is, {time.time() - t0:.1f} s")
    return out


def _say(kayitlar, ad):
    return sum(1 for k in kayitlar if k["varyant"] == ad and k["basarili"])


def kabul_sinamasi(kip="guc"):
    """KURAL 1. Ek baslangic verilmeden karar 43'un sayilari uretilmeli."""
    print("KURAL 1 — KABUL SINAMASI (ek_baslangic verilmiyor)")
    isler = [(ad, p, V, kip) for ad in KARAR43 for p in PODLAR for V in HIZLAR]
    kay = _kos(isler, _is_soguk, "soguk koşum")
    tamam, sonuc = True, {}
    for ad, bek in KARAR43.items():
        g = _say(kay, ad)
        sonuc[ad] = dict(beklenen=bek, olculen=g, gecti=bool(g == bek))
        isaret = "✅" if g == bek else "❌"
        print(f"    {isaret} {ad:<11} beklenen {bek:>3}  olculen {g:>3}")
        tamam &= (g == bek)
    with open(os.path.join(CIKTI, "s1_kabul_sinamasi.json"), "w",
              encoding="utf-8") as f:
        json.dump(dict(kip=kip, sonuc=sonuc, tamam=tamam, kayitlar=kay), f)
    return tamam, kay


def sicak_kosum(kip, soguk_kay=None):
    print(f"SICAK BASLANGIC KOSUMU — amac_kip = {kip}")
    isler = [(p, V, kip) for p in PODLAR for V in HIZLAR]
    ciftler = _kos(isler, _is_sicak, "sicak koşum")
    ikili = [c[0] for c in ciftler]
    limulus = [c[1] for c in ciftler]
    n_ikili, n_limulus = _say(ikili, "ikili"), _say(limulus, "limulus")

    # KURAL 2 — matematiksel taban, iki kumenin BIRLESIMI
    anahtar = lambda k: (k["pod"], k["V"])
    kap_ikili = {anahtar(k) for k in ikili if k["basarili"]}
    kap_sicak = {anahtar(k) for k in limulus if k["basarili"]}
    kap_soguk = set()
    if soguk_kay:
        kap_soguk = {anahtar(k) for k in soguk_kay
                     if k["varyant"] == "limulus" and k["basarili"]}
    taban = kap_ikili | kap_soguk
    eksik = sorted(taban - kap_sicak)
    print(f"    ikili {n_ikili}/108 · limulus SICAK {n_limulus}/108 · "
          f"taban (birlesim) {len(taban)}")
    print(f"    KURAL 2 {'✅ GECTI' if not eksik else '❌ GECMEDI'}"
          + (f", kapanmayan {len(eksik)} durum {eksik}" if eksik else ""))
    # KURAL 3 — on kayitli on puan esigi
    fark = (n_limulus - n_ikili) / 108.0 * 100.0
    print(f"    KURAL 3 fark {fark:+.1f} yuzde puan, esik +10,0 -> "
          f"{'ustunluk YAZILIR' if fark >= 10.0 else 'ustunluk yazilmaz'}")
    ort = lambda ks, alan: (sum(k[alan] for k in ks if k["basarili"])
                            / max(1, sum(1 for k in ks if k["basarili"])))
    yay = [k["tilt_yayilimi"] for k in limulus if k["basarili"]]
    print(f"    limulus sicak: ort |beta| "
          f"{ort(limulus, 'beta_derece'):+.2f} derece · ort guc "
          f"{ort(limulus, 'P_batarya_kW'):.1f} kW · azami tilt yayilimi "
          f"{max(yay) if yay else 0.0:.1f} derece")
    print(f"    ikili        : ort |beta| "
          f"{ort(ikili, 'beta_derece'):+.2f} derece · ort guc "
          f"{ort(ikili, 'P_batarya_kW'):.1f} kW")
    return dict(kip=kip, n_ikili=n_ikili, n_limulus_sicak=n_limulus,
                taban=len(taban), kural2_gecti=not eksik,
                kapanmayan=eksik, fark_yuzde_puan=fark,
                ikili=ikili, limulus_sicak=limulus)


def main():
    os.makedirs(CIKTI, exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--kabul", action="store_true",
                    help="yalniz kural 1 kabul sinamasini kos")
    ap.add_argument("--kip", default="guc", choices=("guc", "yankayma"))
    ap.add_argument("--kabulu-atla", action="store_true",
                    help="kural 1 sonucunu diskteki kayittan OKU, yeniden "
                         "kosma. Kayit yoksa hata verir, sessizce atlamaz")
    a = ap.parse_args()
    print("=" * 72)
    print("KARAR 51 — SICAK BASLANGIC")
    print(f"Izgara {len(HIZLAR)} hiz ({HIZLAR[0]:.1f}-{HIZLAR[-1]:.1f} m/s) x "
          f"{len(PODLAR)} pod = {len(HIZLAR) * len(PODLAR)} durum")
    print("=" * 72)
    if a.kabulu_atla:
        yol_k = os.path.join(CIKTI, "s1_kabul_sinamasi.json")
        if not os.path.exists(yol_k):
            sys.exit(f"❌ kabul sinamasi kaydi yok: {yol_k}")
        with open(yol_k, encoding="utf-8") as f:
            _k = json.load(f)
        tamam, soguk = bool(_k["tamam"]), _k["kayitlar"]
        print("KURAL 1 — kabul sinamasi diskteki kayittan okundu, "
              f"tamam={tamam}")
        for ad, d in _k["sonuc"].items():
            print(f"    {'✅' if d['gecti'] else '❌'} {ad:<11} "
                  f"beklenen {d['beklenen']:>3}  olculen {d['olculen']:>3}")
    else:
        tamam, soguk = (kabul_sinamasi(a.kip) if a.kip == "guc"
                        else (True, None))
    if a.kabul:
        return
    if a.kip == "guc" and not tamam:
        sys.exit("❌ KURAL 1 GECMEDI, kosum gecersiz, hicbir sayi raporlanmaz")
    print()
    s = sicak_kosum(a.kip, soguk)
    yol = os.path.join(CIKTI, f"s1_sicak_baslangic_{a.kip}.json")
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(s, f)
    print(f"\nyazildi {yol}")


if __name__ == "__main__":
    main()
