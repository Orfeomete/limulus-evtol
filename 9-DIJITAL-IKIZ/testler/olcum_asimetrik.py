#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARAR 43 — asimetrik senaryolarin olcumu.

Ön kayit `4-KARARLAR/43-asimetrik-senaryolar-on-kaydi.md`. Karar kurallari
sonuclar gorulmeden donduruldu, bu betik yalniz o kurallarin sordugu sayilari
uretir ve hicbir esik ya da yorum icermez.

Senaryolar
    S1  gecişte tek pod arizasi        birincil, on kayitli
    S2  yanal gust, kalici esdeger     kesifsel, vekil olcum
    S3  koordineli donus               ayri betik, model degisikligi gerektiriyor

Yontem karar 21'in yontemidir, tek fark izgaranin incelmesi. Karar 21 uc hiz ve
iki pod denemisti (6 durum), burada yirmi yedi hiz ve dort pod var (108 durum),
boylece karar 21'in acik biraktigi uc soru da yanitlanir.
    1. 45 m/s'de trim bulunamamasi fiziksel sinir mi cozucu sorunu mu
    2. Sag taraf podlari (1 ve 3) simetri geregi ayni cikiyor mu
    3. Serbest yan kaymanin kazanci nerede

Kosum
    cd 9-DIJITAL-IKIZ && python3 testler/olcum_asimetrik.py
Cikti
    cikti_asimetrik/s1_pod_arizasi.json
    cikti_asimetrik/s2_yanal_gust.json
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
HIZLAR = [5.0 + 2.5 * i for i in range(27)]          # 5 ... 70 m/s
PODLAR = (0, 1, 2, 3)
GUSTLAR = (5.0, 10.0, 15.0)                          # m/s yanal
KADEME = "surekli"


def _kur(ad):
    """⚠️ B4 bayragi metrikler.py ile AYNI okunur (karar 22, 32)."""
    from arac import Limulus
    b = os.environ.get("LIMULUS_CRUISE_ITKI", "0") == "1"
    return Limulus(varyant_ad=ad, cruise_itki_etkin=b)


def _tavan(ac, V):
    """Rotorun o hizdaki itki tavani. Kontrol payi buna gore olculur."""
    import atmosfer as atm
    hava = atm.isa(0.0)
    return ac.rotor.itki_limiti(ac.itki[0].guc_tavani(KADEME),
                                hava.rho, V, math.pi / 2)


def _cozum_kaydi(r, tav):
    """Ön kayitta sayilan dort buyukluk, artı artik ve tilt yayilimi."""
    T = [float(t) for t in r.T]
    pay = 1.0 - max(T) / tav if tav > 0 else float("nan")
    tilt = [math.degrees(float(t)) for t in r.tilt] if r.tilt is not None else []
    return dict(basarili=bool(r.basarili), artik=float(r.artik),
                beta_derece=math.degrees(float(r.beta)),
                phi_derece=math.degrees(float(r.phi)),
                T=T, T_tavan=float(tav), kontrol_payi=float(pay),
                tilt_derece=tilt,
                tilt_yayilimi=float(max(tilt) - min(tilt)) if tilt else 0.0,
                P_batarya_kW=float(r.P_batarya) / 1e3)


def _s1_is(arg):
    ad, pod, V, beta_serbest = arg
    import trim
    ac = _kur(ad)
    r = trim.trim_yanal(ac, V, ariza=pod,
                        beta_hedef=None if beta_serbest else 0.0)
    k = _cozum_kaydi(r, _tavan(ac, V))
    k.update(varyant=ad, pod=pod, V=V, beta_serbest=beta_serbest)
    return k


def _s2_is(arg):
    ad, v_gust, V = arg
    import trim
    ac = _kur(ad)
    beta = math.atan2(v_gust, V)                     # kalici esdeger yan kayma
    r = trim.trim_yanal(ac, V, beta_hedef=beta)
    k = _cozum_kaydi(r, _tavan(ac, V))
    k.update(varyant=ad, v_gust=v_gust, V=V, beta_hedef_derece=math.degrees(beta))
    return k


def kosu(ad, isler, fn):
    t0 = time.time()
    with Pool(processes=max(1, (os.cpu_count() or 2))) as p:
        sonuc = p.map(fn, isler, chunksize=4)
    print(f"  {ad}: {len(sonuc)} cozum, {time.time() - t0:.0f} s")
    return sonuc


def ozet_s1(kayitlar, beta_serbest):
    print(f"\n  {'varyant':<12}{'kapanan':>9}{'oran':>8}"
          f"{'ilk kapanan V':>15}{'ort kontrol payi':>18}{'azami tilt yayilimi':>21}")
    for ad in VARYANTLAR:
        alt = [k for k in kayitlar
               if k["varyant"] == ad and k["beta_serbest"] == beta_serbest]
        ok = [k for k in alt if k["basarili"]]
        ilk = min((k["V"] for k in ok), default=None)
        pay = (sum(k["kontrol_payi"] for k in ok) / len(ok)) if ok else float("nan")
        yay = max((k["tilt_yayilimi"] for k in ok), default=0.0)
        print(f"  {ad:<12}{len(ok):>4}/{len(alt):<4}{100*len(ok)/max(len(alt),1):>7.0f}%"
              f"{(f'{ilk:.1f}' if ilk else '—'):>15}"
              f"{(f'{100*pay:.1f}%' if ok else '—'):>18}"
              f"{yay:>20.2f}°")


def main():
    os.makedirs(CIKTI, exist_ok=True)
    print("KARAR 43 — asimetrik senaryolar olcumu")
    print("=" * 78)
    print(f"Izgara {len(HIZLAR)} hiz ({HIZLAR[0]:.1f}-{HIZLAR[-1]:.1f} m/s, "
          f"2,5 m/s adim) · {len(VARYANTLAR)} varyant")

    # --- S1, once yan kaymasiz (birincil), sonra serbest (ikincil) ---
    isler = [(ad, p, V, False) for ad in VARYANTLAR for p in PODLAR for V in HIZLAR]
    isler += [(ad, p, V, True) for ad in VARYANTLAR for p in PODLAR for V in HIZLAR]
    s1 = kosu("S1 pod arizasi", isler, _s1_is)
    print("\nS1 — YAN KAYMASIZ (birincil, karar 21 ile karsilastirilabilir)")
    ozet_s1(s1, False)
    print("\nS1 — SERBEST YAN KAYMA (ikincil, daha musamahakar)")
    ozet_s1(s1, True)
    with open(os.path.join(CIKTI, "s1_pod_arizasi.json"), "w") as f:
        json.dump(dict(izgara=dict(hizlar=HIZLAR, podlar=list(PODLAR),
                                   varyantlar=list(VARYANTLAR)),
                       kayitlar=s1), f, ensure_ascii=False, indent=1)

    # --- S2, yanal gust ---
    isler2 = [(ad, g, V) for ad in VARYANTLAR for g in GUSTLAR for V in HIZLAR]
    s2 = kosu("S2 yanal gust", isler2, _s2_is)
    print("\nS2 — YANAL GUST (kesifsel, kalici esdeger yan kayma)")
    print(f"  {'varyant':<12}" + "".join(f"{f'{g:.0f} m/s':>12}" for g in GUSTLAR))
    for ad in VARYANTLAR:
        hucre = []
        for g in GUSTLAR:
            alt = [k for k in s2 if k["varyant"] == ad and k["v_gust"] == g]
            ok = sum(1 for k in alt if k["basarili"])
            hucre.append(f"{ok}/{len(alt)}")
        print(f"  {ad:<12}" + "".join(f"{h:>12}" for h in hucre))
    with open(os.path.join(CIKTI, "s2_yanal_gust.json"), "w") as f:
        json.dump(dict(izgara=dict(hizlar=HIZLAR, gustlar=list(GUSTLAR),
                                   varyantlar=list(VARYANTLAR)),
                       kayitlar=s2), f, ensure_ascii=False, indent=1)

    print("\n" + "=" * 78)
    print("Ham veri cikti_asimetrik/ altinda. Karar kurallari ON KAYITTA, "
          "bu betik esik uygulamaz.")


if __name__ == "__main__":
    main()
