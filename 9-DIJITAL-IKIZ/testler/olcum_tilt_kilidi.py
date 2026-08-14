#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARAR 48 — tilt aktuatoru yedekliligi ve tork bedeli.

Ön kayit `4-KARARLAR/48-tilt-aktuatoru-yedeklilik-on-kaydi.md`. Karar kurallari
sonuclar gorulmeden donduruldu, bu betik yalniz o kurallarin sordugu sayilari
uretir ve hicbir esik ya da yorum icermez.

Iki sey olculur.
  1. YEDEKLILIK. Karar 43'un supurmesi bir tilt aktuatoru KILITLI halde
     tekrarlanir, kapanma oraninin dususu olculur.
  2. TORK. Her kapanan cozumde her podun tilt eksenine gore momenti, yani bir
     aktuatorun tutmasi gereken tork hesaplanir.

⚠️ AKTUATOR SIKISMASI GRUP BAZINDADIR. Iki eksenli kurguda tek aktuator bir
cifti surdugu icin bir sikisma IKI podu birlikte etkiler. Genisletme burada
yapilir, `trim_yanal` icinde degil, cunku varyant gruplamasi tek yerde
(`arac.tilt_esle`) tutulur.

⚠️ KILIT ACISI 85 DERECE ve tek bir aci deneniyor. Ön kayit bunu bir varsayim
olarak beyan etti, duyarlilik OLCULMEYECEK diye yazdi.

Kosum
    cd 9-DIJITAL-IKIZ && python3 testler/olcum_tilt_kilidi.py
Cikti
    cikti_asimetrik/k48_tilt_kilidi.json
"""
import json
import math
import os
import sys
import time

_BURASI = os.path.dirname(os.path.abspath(__file__))
_KOK = os.path.dirname(_BURASI)
sys.path.insert(0, os.path.join(_KOK, "dinamik"))
CIKTI = os.path.join(_KOK, "cikti_asimetrik")

VARYANTLAR = ("limulus", "ikili", "senkron")   # sifir eksende tilt yok
HIZLAR = [5.0 + 2.5 * i for i in range(27)]
PODLAR = (0, 1, 2, 3)
KILIT_ACI = math.radians(85.0)                 # ön kayitta dondurulmus


def _kur(ad):
    """⚠️ B4 bayragi metrikler.py ile AYNI okunur (karar 22, 32)."""
    from arac import Limulus
    b = os.environ.get("LIMULUS_CRUISE_ITKI", "0") == "1"
    return Limulus(varyant_ad=ad, cruise_itki_etkin=b)


def aktuator_gruplari(ac):
    """Bir aktuatorun surdugu pod kumeleri. Varyanttan okunur, elle yazilmaz."""
    v = ac.var
    if v.sabit_tilt is not None:
        return []
    return [tuple(g) for g in v.tilt_gruplari]


def tilt_torku(ac, T, tilt, hava, V):
    """Her podun tilt eksenine gore momenti, N m.

    Tilt ekseni govde y eksenine paralel kabul edilir, yani pod kendi
    enine ekseni etrafinda dondurulur. Itki vektoru disk normaline dik
    olmadigindan, itkinin tilt eksenine gore kolu rotorun kendi
    merkezinden gecer ve o kol SIFIRDIR. Dolayisiyla torku ureten sey
    itkinin kendisi degil, aerodinamik yuk ve download bilesenidir.

    ⚠️ Bu model tilt aktuatoru torkunu ALT SINIR olarak verir. Rotorun
    kendi moment katkilari (H kuvveti, disk momenti) modelde tanimli
    degil, bu yuzden gercek tork daha buyuktur. Ön kayit torku bir
    KARSILASTIRMA degil BEDEL KAYDI olarak istedi, alt sinir bu amac
    icin yeterlidir ve sinir oldugu yazilir.
    """
    q = hava.q(V)
    out = []
    for i in range(4):
        # download bileseni pod merkezinde asagi etkir, tilt eksenine gore
        # kolu rotor yarıcapinin efektif merkezidir
        f_dl = (ac.k["DOWNLOAD"] - 1.0) * math.cos(tilt[i]) * float(T[i])
        kol = ac.rotor.D / 4.0          # disk alaninin merkez yariçapi
        out.append(abs(f_dl * kol))
    return out


def _is(arg):
    ad, pod, V, kilit_grup = arg
    import atmosfer as atm
    import trim
    ac = _kur(ad)
    kilit = ({p: KILIT_ACI for p in kilit_grup} if kilit_grup else None)
    r = trim.trim_yanal(ac, V, ariza=pod, beta_hedef=0.0, tilt_kilit=kilit)
    tork = (tilt_torku(ac, r.T, r.tilt, atm.isa(0.0), V)
            if r.basarili and r.tilt is not None else None)
    return dict(varyant=ad, pod=pod, V=V,
                kilit_grup=list(kilit_grup) if kilit_grup else None,
                kilit_pod_sayisi=len(kilit_grup) if kilit_grup else 0,
                arizali_pod_kilitli=bool(kilit_grup and pod in kilit_grup),
                basarili=bool(r.basarili), artik=float(r.artik),
                tork_N_m=tork,
                azami_tork_N_m=(max(tork) if tork else None))


def main():
    os.makedirs(CIKTI, exist_ok=True)
    isler = []
    for ad in VARYANTLAR:
        ac = _kur(ad)
        gruplar = aktuator_gruplari(ac)
        for pod in PODLAR:
            for V in HIZLAR:
                isler.append((ad, pod, V, None))          # kilitsiz taban
                for g in gruplar:
                    isler.append((ad, pod, V, g))         # her aktuator ayri

    print(f"KARAR 48 — tilt kilidi ve tork, {len(isler)} cozum")
    for ad in VARYANTLAR:
        print(f"  {ad}: aktuator gruplari {aktuator_gruplari(_kur(ad))}")
    t0 = time.time()
    # ⚠️ SIRALI, paralel DEGIL. Karar 47'de olculdu, iki surec toplam verimi
    # dusuruyor cunku torch zaten iki cekirdegi kullaniyor.
    kayitlar = [_is(x) for x in isler]
    print(f"  {len(kayitlar)} cozum, {time.time() - t0:.0f} s")

    yol = os.path.join(CIKTI, "k48_tilt_kilidi.json")
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(dict(izgara=dict(hizlar=HIZLAR, podlar=list(PODLAR),
                                   kilit_aci_derece=85.0,
                                   beta_hedef=0.0),
                       kayitlar=kayitlar), f, indent=1, ensure_ascii=False)
    print(f"\n{os.path.relpath(yol, _KOK)} yazildi")
    ozet(kayitlar)


def ozet(K):
    print(f"\n{'varyant':<11}{'durum':<22}{'kapanan':>9}{'oran':>7}"
          f"{'azami tork N m':>16}")
    print("-" * 66)
    for ad in VARYANTLAR:
        taban = [k for k in K if k["varyant"] == ad and not k["kilit_grup"]]
        kilit = [k for k in K if k["varyant"] == ad and k["kilit_grup"]]
        for etiket, alt in (("kilitsiz taban", taban),
                            ("kilitli, hepsi", kilit),
                            ("kilitli, arizali pod haric",
                             [k for k in kilit
                              if not k["arizali_pod_kilitli"]]),
                            ("kilitli, arizali pod dahil",
                             [k for k in kilit if k["arizali_pod_kilitli"]])):
            if not alt:
                continue
            ok = [k for k in alt if k["basarili"]]
            tork = [k["azami_tork_N_m"] for k in ok
                    if k["azami_tork_N_m"] is not None]
            print(f"{ad:<11}{etiket:<22}{len(ok):>4}/{len(alt):<4}"
                  f"%{100 * len(ok) / len(alt):>5.0f}"
                  f"{(max(tork) if tork else float('nan')):>16.1f}")


if __name__ == "__main__":
    main()
