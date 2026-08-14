#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MUFREDAT ESIGI TESHISI — karar 39 on kaydinin Asama 0 ve Asama 1'i.
# Fizik kosular_uzun ile ayni tutulur, cunku olculen politikalar oradan gelir.
import os as _os
_os.environ["LIMULUS_CRUISE_ITKI"] = "1"
"""
MUFREDAT KAPISI NEDEN GECILEMIYOR

Karar 38: 19/20 kosu mufredat seviye 2'de (gecis) platoya oturuyor ve
seviye 3'e gecemiyor. Reçete olarak "gevsetilmis esik" onerildi. Bu betik
o receteyi YAZMADAN ONCE kapinin kendisini olcer.

Uc soru, ucu de politikadan bagimsiz.

  A0  ARITMETIK. Esik 0,65 nedir? Bolum odulu, bolumun AZAMI uzunluguna
      bolunerek normalize ediliyor. Yani kapi ayni zamanda bir HAYATTA
      KALMA kapisidir. Adim basi odul ustsiniri ve cokme cezasi biliniyor,
      dolayisiyla "mukemmel izlemeyle bile en az kac adim yasamak gerekir"
      sorusu KAPALI FORMDA cevaplanir.

  A1  EYLEM UZAYININ ERISIMI. Eylemler trim ankrajina gore artimsaldir ve
      ankraj bolumun BASLANGIC kosulunda bir kez hesaplanir. Gecis
      gorevinde baslangic hover oldugu icin ankraj hover trimidir. Tilt
      komutu ankraj +- KTH_YETKI ile sinirli. Cruise 85 derece istiyor.
      Erisilebilir azami tilt hesaplanir.

  A2  TABAN KONTROLCUNUN TAVANI. Kaskad PID kontrolcu, ogrenmeden bagimsiz
      bir yetkinlik referansidir. Ayni ortamda, ayni eylem uzayindan
      surulur ve her seviyede normalize odulu olculur. Kapi taban
      kontrolcu icin de asilamiyorsa, kapi bir yetkinlik olcusu degildir.

  A3  EGITILMIS POLITIKALARIN SONLANMA NEDENI. Bolumler neden bitiyor.
      Yere carpma, tutum sinir, enerji tukenmesi ya da sure dolmasi.

Cikti bir teshis tablosudur, karar kurali icermez. Karar kurallari
4-KARARLAR/39-mufredat-esigi-on-kaydi.md icindedir.
"""

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
from arac import Limulus                                # noqa: E402
from egitim_v2 import KosanNorm, Politika2              # noqa: E402
from ortam import (KT_YETKI, KTH_YETKI, MUFREDAT, ODUL_AGIRLIK,  # noqa: E402
                   LimulusOrtami, trim_ankraji)
from temel_kontrolcu import TemelKontrolcu              # noqa: E402

# Politika dizini cevre degiskeniyle degistirilebilir. Varsayilan
# kosular_uzun, yani dondurulmus kampanya. Karar 39 Asama 2a
# degerlendirmesi LIMULUS_OLCUM_DIZINI=kosular_esik_sonda ile kosar.
KOSU_DIZIN = os.path.join(_B, "..", "ogrenme",
                          os.environ.get("LIMULUS_OLCUM_DIZINI",
                                         "kosular_uzun"))
ESIK = 0.65                        # DONMUS, karar 12 §4
DT = 0.02
VARYANTLAR = ("limulus", "ikili", "senkron", "liftcruise")


# =====================================================================
# A0 — kapinin aritmetigi
# =====================================================================
def a0_aritmetik():
    r_max = (ODUL_AGIRLIK["hiz"] + ODUL_AGIRLIK["irtifa"]
             + ODUL_AGIRLIK["tutum"])
    cokme = ODUL_AGIRLIK["cokme"]
    print("=" * 78)
    print("A0 — MUFREDAT KAPISININ ARITMETIGI")
    print("=" * 78)
    print(f"Adim basi odul ustsiniri {r_max:.2f} (ceza yok kabulu) · "
          f"cokme cezasi {cokme:.0f} · esik {ESIK:.2f}")
    print(f"\n{'sev':>3} {'gorev':<12}{'sure':>6}{'n_azami':>9}"
          f"{'gereken adim':>14}{'hayatta kalma payi':>21}")
    print("-" * 78)
    sonuc = {}
    for i, g in enumerate(MUFREDAT):
        n_az = int(g.sure / DT)
        n_min = (ESIK * n_az + cokme) / r_max
        sonuc[i] = (n_az, n_min, n_min / n_az)
        print(f"{i:>3} {g.ad:<12}{g.sure:>6.0f}{n_az:>9}{n_min:>14.0f}"
              f"{n_min / n_az * 100:>20.1f}%")
    print("\nOkuma. Cokmeyle biten bolumde toplam odul en cok r_max*n - cokme")
    print("olabilir. Kapi bu yuzden ayni zamanda bir hayatta kalma kapisidir")
    print("ve tablodaki pay, izleme MUKEMMEL olsa bile gereken alt siniridir.")
    return sonuc


# =====================================================================
# A1 — eylem uzayinin tilt erisimi
# =====================================================================
def a1_erisim():
    print("\n" + "=" * 78)
    print("A1 — EYLEM UZAYININ TILT ERISIMI (ankraj baslangic kosulunda)")
    print("=" * 78)
    ac = Limulus(dt=DT, varyant_ad="limulus", sensor_etkin=False)
    print(f"KT_YETKI {KT_YETKI:.2f} (itki, trim etrafinda) · "
          f"KTH_YETKI {math.degrees(KTH_YETKI):.0f} derece (tilt)")
    print(f"\n{'sev':>3} {'gorev':<12}{'baslangic V':>12}{'ankraj tilt':>13}"
          f"{'erisilebilir tilt':>19}{'cruise 85 der.':>16}")
    print("-" * 78)
    sonuc = {}
    for i, g in enumerate(MUFREDAT):
        _, tilt_ank = trim_ankraji(ac, g.baslangic_V, g.baslangic_h)
        th0 = float(np.mean(tilt_ank))
        alt = max(0.0, th0 - KTH_YETKI)
        ust = min(ac.k["THETA_MAX"], th0 + KTH_YETKI)
        yeter = "evet" if ust >= math.radians(85.0) else "HAYIR"
        sonuc[i] = (th0, alt, ust)
        print(f"{i:>3} {g.ad:<12}{g.baslangic_V:>10.0f} m/s"
              f"{math.degrees(th0):>11.1f} d"
              f"{math.degrees(alt):>9.1f} - {math.degrees(ust):<7.1f} d"
              f"{yeter:>14}")
    print("\nOkuma. Ankraj bolum basinda bir kez hesaplanir ve bolum boyunca")
    print("sabit kalir. Gecis gorevi hover'da basladigi icin ankraj hover")
    print("trimidir, dolayisiyla erisilebilir tilt bandi da hover cevresidir.")
    return sonuc


# =====================================================================
# ortak — ortam kurulumu ve sonlanma nedeni
# =====================================================================
def ortam_kur(varyant, seviye, tohum):
    o = LimulusOrtami(varyant=varyant, seviye=seviye, tohum=tohum,
                      sensor=True)
    o.seviye = seviye
    o.gorev = MUFREDAT[seviye]
    return o


def sonlanma_nedeni(o, bilgi):
    d = o.ac.durum
    if -d[11] <= 0.0:
        return "yere carpma"
    if abs(d[6]) > math.radians(85) or abs(d[7]) > math.radians(85):
        return "tutum > 85 der."
    if bilgi.get("enerji_orani", 0.0) > 1.0:
        return "enerji tukendi"
    return "sure doldu"


# =====================================================================
# A2 — taban kontrolcunun tavani
# =====================================================================
def taban_bolum(varyant, seviye, tohum):
    """Kaskad PID kontrolcu, ortamin ARTIMSAL eylem uzayindan surulur.

    Kontrolcunun istedigi komut, ortamin eslemesi ters cevrilerek
    normalize eyleme donusturulur. Kirpma orani ayrica sayilir, cunku
    eylem uzayinin kontrolcuyu ne kadar kistigi olcumun parcasidir.
    """
    o = ortam_kur(varyant, seviye, tohum)
    ham, _ = o.reset(seed=int(tohum))
    kk = TemelKontrolcu(o.ac, tilt_kanali=True)
    kk.sifirla()
    g = o.gorev
    n_az = int(g.sure / DT)
    toplam, adim, kirpma = 0.0, 0, 0
    bilgi = {}
    while True:
        t = o.ac.t
        # Ucus programi gorevin KENDI baslangic kosulundan hedefe rampalanir.
        # ⚠️ Ilk surumde rampa her seviyede sifirdan basliyordu ve cruise
        # gorevinde (baslangic 60 m/s) kontrolcuye once yavaslama emri
        # veriyordu. Bu betigin kusuruydu, ortamin degil.
        pay = min(max((t - 3.0) / max(g.sure * 0.5, 1.0), 0.0), 1.0)
        V_hedef = g.baslangic_V + (g.V_hedef - g.baslangic_V) * pay
        th0 = float(np.mean(o.tilt_ank))
        th_son = math.radians(85.0) if g.V_hedef > 25.0 else th0
        tilt_hedef = th0 + (th_son - th0) * pay
        T_ist, tilt_ist = kk(o.ac.durum, g.h_hedef, V_hedef, tilt_hedef)
        e = np.zeros(o.n_eylem)
        e[:4] = (T_ist / np.maximum(o.T_ank, 1e-6) - 1.0) / KT_YETKI
        if o.n_tilt > 0:
            th_ank = np.array([o.tilt_ank[grp[0]]
                               for grp in o.ac.var.tilt_gruplari])
            e[4:4 + o.n_tilt] = (tilt_ist[:o.n_tilt] - th_ank) / KTH_YETKI
        if np.any(np.abs(e) > 1.0):
            kirpma += 1
        ham, r, bitti, kesildi, bilgi = o.step(np.clip(e, -1.0, 1.0))
        toplam += r
        adim += 1
        if bitti or kesildi:
            break
    return dict(odul=toplam / n_az, adim=adim, pay=adim / n_az,
                kirpma=kirpma / max(adim, 1),
                neden=sonlanma_nedeni(o, bilgi))


def a2_taban(bolum=3):
    print("\n" + "=" * 78)
    print("A2 — TABAN KONTROLCUNUN NORMALIZE ODULU (ogrenmeden bagimsiz)")
    print("=" * 78)
    print(f"{'sev':>3} {'gorev':<12}{'varyant':<12}{'odul':>8}{'kapi':>7}"
          f"{'adim':>7}{'pay':>7}{'kirpma':>8}  sonlanma")
    print("-" * 78)
    sonuc = {}
    for sev in range(len(MUFREDAT)):
        for v in VARYANTLAR:
            satir = [taban_bolum(v, sev, t) for t in range(bolum)]
            od = float(np.mean([s["odul"] for s in satir]))
            ad = float(np.mean([s["adim"] for s in satir]))
            pay = float(np.mean([s["pay"] for s in satir]))
            kir = float(np.mean([s["kirpma"] for s in satir]))
            ned = max(set(s["neden"] for s in satir),
                      key=lambda x: sum(1 for s in satir if s["neden"] == x))
            sonuc[(sev, v)] = od
            gecti = "GECER" if od >= ESIK else "gecmez"
            print(f"{sev:>3} {MUFREDAT[sev].ad:<12}{v:<12}{od:>8.3f}"
                  f"{gecti:>7}{ad:>7.0f}{pay * 100:>6.0f}%{kir * 100:>7.0f}%"
                  f"  {ned}")
        print("-" * 78)
    return sonuc


# =====================================================================
# A3 — egitilmis politikalarin sonlanma nedeni
# =====================================================================
def politika_yukle(varyant, tohum, seviye):
    kok = os.path.join(KOSU_DIZIN, f"{varyant}_t{tohum}")
    if not (os.path.exists(kok + ".pt")
            and os.path.exists(kok + "_gunluk.json")):
        return None
    j = json.load(open(kok + "_gunluk.json"))
    o = ortam_kur(varyant, seviye, tohum)
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


def a3_politika(seviye=2, bolum=3):
    print("\n" + "=" * 78)
    print(f"A3 — EGITILMIS POLITIKALAR, SEVIYE {seviye} "
          f"({MUFREDAT[seviye].ad}), deterministik")
    print("=" * 78)
    n_az = int(MUFREDAT[seviye].sure / DT)
    print(f"{'varyant':<12}{'tohum':>6}{'odul':>8}{'kapi':>7}{'adim':>7}"
          f"{'pay':>7}  sonlanma")
    print("-" * 78)
    sonuc, nedenler = {}, {}
    for v in VARYANTLAR:
        satir = []
        for t in range(5):
            y = politika_yukle(v, t, seviye)
            if y is None:
                continue
            pol, norm, o = y
            for b in range(bolum):
                ham, _ = o.reset(seed=int(1000 * t + b))
                gz = norm(ham) if norm else ham
                toplam, adim, bilgi = 0.0, 0, {}
                while True:
                    e, _, _ = pol.eylem(gz, ornekle=False)
                    ham, r, bitti, kesildi, bilgi = o.step(
                        np.clip(e, -1.0, 1.0))
                    gz = norm(ham) if norm else ham
                    toplam += r
                    adim += 1
                    if bitti or kesildi:
                        break
                ned = sonlanma_nedeni(o, bilgi)
                nedenler[ned] = nedenler.get(ned, 0) + 1
                satir.append((toplam / n_az, adim, ned))
            od = float(np.mean([s[0] for s in satir[-bolum:]]))
            ad = float(np.mean([s[1] for s in satir[-bolum:]]))
            ned = satir[-1][2]
            print(f"{v:<12}{t:>6}{od:>8.3f}"
                  f"{'GECER' if od >= ESIK else 'gecmez':>7}{ad:>7.0f}"
                  f"{ad / n_az * 100:>6.0f}%  {ned}")
        if satir:
            sonuc[v] = float(np.mean([s[0] for s in satir]))
        print("-" * 78)
    print("Sonlanma nedeni dagilimi:", nedenler)
    return sonuc, nedenler


# =====================================================================
if __name__ == "__main__":
    a0 = a0_aritmetik()
    a1 = a1_erisim()
    a2 = a2_taban(bolum=int(os.environ.get("LIMULUS_TABAN_BOLUM", 3)))
    a3, ned = a3_politika(seviye=2, bolum=2)

    print("\n" + "=" * 78)
    print("TESHIS OZETI")
    print("=" * 78)
    n_az2, n_min2, pay2 = a0[2]
    print(f"Seviye 2 kapisi, mukemmel izlemeyle bile bolumun "
          f"%{pay2 * 100:.0f}'ini yasamayi gerektiriyor "
          f"({n_min2:.0f} / {n_az2} adim).")
    tb = [a2[(2, v)] for v in VARYANTLAR]
    print(f"Taban kontrolcunun seviye 2 normalize odulu "
          f"{min(tb):.3f} - {max(tb):.3f}, kapi {ESIK:.2f}.")
    if a3:
        print(f"Egitilmis politikalarin seviye 2 odulu "
              f"{min(a3.values()):.3f} - {max(a3.values()):.3f}.")
    print("\nBu betik karar kurali icermez. Kurallar "
          "4-KARARLAR/39-mufredat-esigi-on-kaydi.md icindedir.")
