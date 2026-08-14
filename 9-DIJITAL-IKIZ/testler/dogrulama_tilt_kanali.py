#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 DOGRULAMA — tilt kanalinin kontrol otoritesine katkisi

Karar 14 su iddiayi kurdu.

    dM/dT     = +x cos(theta)       -> 90 derecede sifir
    dM/dtheta = -x T sin(theta)     -> 90 derecede azami

Temel kontrolcu ilk surumde yalniz itki sutununu kullaniyordu, yani
cruise'da otoritesizdi. F1 tilt'i kontrol girisi yapti.

Bu betik iki soruyu sayiyla yanitlar.

  1. Sinirli bir tilt sapmasiyla ne kadar yunuslama momenti uretilebilir,
     ve bu VARYANTA gore nasil degisir
  2. Kapali cevrimde cruise tutum sapmasi ne kadar azaliyor

Sutun normu KARSILASTIRMA OLCUTU DEGILDIR — serbestlik derecesi sayisi
degisince norm da degisir. Dogru olcut, sinirli sapma icin ulasilabilir
azami momenttir.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

_B = os.path.dirname(os.path.abspath(__file__))
for _y in ("../dinamik", "../ogrenme"):
    _t = os.path.normpath(os.path.join(_B, _y))
    if _t not in sys.path:
        sys.path.insert(0, _t)

from arac import Limulus                        # noqa: E402
from temel_kontrolcu import TemelKontrolcu, kos, hiz_programli_tilt  # noqa: E402

VARYANTLAR = ("limulus", "ikili", "senkron", "liftcruise")
SAPMA_TAVAN = math.radians(12.0)


# =====================================================================
def bolum_1_otorite():
    """Sinirli tilt sapmasiyla ulasilabilir azami yunuslama momenti."""
    print("=" * 74)
    print("1. ULASILABILIR YUNUSLAMA MOMENTI  (|d(theta)| <= 12 derece)")
    print("=" * 74)
    print(f"{'varyant':<12}{'tilt DOF':>9}{'itki kanali':>14}"
          f"{'tilt kanali':>14}{'oran':>10}")
    print("-" * 74)

    T_pod = 459.0          # N, cruise'da pod basina (karar 14'ten)
    dT = 200.0             # N, itki kanalinda makul sapma
    th = math.radians(85.0)

    sonuc = {}
    for v in VARYANTLAR:
        ac = Limulus(varyant_ad=v, sensor_etkin=False)
        kk = TemelKontrolcu(ac)
        J = kk._jakobiyen(np.full(4, th), np.full(4, T_pod))

        # itki kanali: on cift +dT, arka cift -dT (diferansiyel)
        u_T = np.array([dT, dT, -dT, -dT])
        M_itki = abs(float(J[3, :4] @ u_T))

        # tilt kanali: sinirli sapmayla azami moment
        # J sutunlari tilt_olcek ile carpili, sapma birimi olcekli
        n_th = J.shape[1] - 4
        if n_th > 0:
            j = J[3, 4:] / kk.tilt_olcek           # gercek birime don
            M_tilt = float(np.sum(np.abs(j)) * SAPMA_TAVAN)
        else:
            M_tilt = 0.0

        oran = M_tilt / M_itki if M_itki > 1e-9 else float("inf")
        sonuc[v] = (M_itki, M_tilt)
        print(f"{v:<12}{n_th:>9}{M_itki:>11.0f} Nm{M_tilt:>11.0f} Nm"
              f"{oran:>9.1f}x")

    print()
    print("  Yorum. Cruise'da itki kanali pratik olarak olu (cos 85 = 0,087).")
    print("  Tilt kanali bagimsiz ve ikili tiltte guclu, SENKRON tiltte yok —")
    print("  dort pod ayni acida oldugu icin diferansiyel moment uretilemiyor.")
    print("  Bu, mimarinin kendisinden gelen bir fark.")
    return sonuc


# =====================================================================
def bolum_2_kapali_cevrim():
    """Cruise'a gecis, tilt kanali acik ve kapali."""
    print()
    print("=" * 74)
    print("2. KAPALI CEVRIM — hover'dan cruise'a gecis, 60 s")
    print("=" * 74)
    print(f"{'varyant':<12}{'kanal':<8}{'|th| azami':>12}{'|th| son':>11}"
          f"{'irtifa hatasi':>15}{'V son':>9}")
    print("-" * 74)

    sonuc = {}
    for v in VARYANTLAR:
        for kanal in (False, True):
            ac = Limulus(varyant_ad=v, sensor_etkin=False)
            ac.sifirla(durum=np.array([0.] * 11 + [-300.0]),
                       tilt0=0.0, T0=ac.W / 4)
            V_hedef = 68.9
            k = kos(ac, 60.0, 300.0,
                    lambda t: V_hedef * min(max((t - 5.0) / 25.0, 0.0), 1.0),
                    lambda t: hiz_programli_tilt(ac.durum[0]),
                    tilt_kanali=kanal)
            iyi = [r for r in k if "hata" not in r]
            if not iyi:
                print(f"{v:<12}{'acik' if kanal else 'kapali':<8}"
                      f"{'ZARF DISI':>12}")
                continue
            # gecis sonrasi bant: t > 30 s
            gec = [r for r in iyi if r["t"] > 30.0] or iyi[-5:]
            th_max = max(abs(r["th"]) for r in gec)
            th_son = iyi[-1]["th"]
            dh = iyi[-1]["h"] - 300.0
            Vs = iyi[-1]["V"]
            sonuc[(v, kanal)] = (th_max, th_son, dh, Vs)
            print(f"{v:<12}{'acik' if kanal else 'kapali':<8}"
                  f"{th_max:>11.2f}d{th_son:>10.2f}d{dh:>14.1f} m{Vs:>8.1f}")
        print("-" * 74)
    return sonuc


# =====================================================================
def bolum_3_ozet(otorite, cevrim):
    print()
    print("=" * 74)
    print("3. F1'IN SONUCU")
    print("=" * 74)
    for v in VARYANTLAR:
        a = cevrim.get((v, False))
        b = cevrim.get((v, True))
        if not a or not b:
            continue
        kaz = a[0] - b[0]
        yuz = 100.0 * kaz / a[0] if a[0] > 1e-9 else 0.0
        print(f"  {v:<12} azami tutum sapmasi {a[0]:6.2f}d -> {b[0]:6.2f}d"
              f"   {'kazanim' if kaz > 0 else 'degisim'} {yuz:+6.1f}%")
    print()
    print("  Karsilastirmanin adilligi. Temel kontrolcu artik tilt kanalini")
    print("  kullaniyor. Ogrenilmis politika ile karsilastirma bundan sonra")
    print("  esit zeminde yapilir — onceki kurgu politikaya, taban")
    print("  kontrolcunun kullanmadigi bir kanali kullandigi icin haksiz")
    print("  avantaj veriyordu.")


# =====================================================================
def bolum_2b_cruise_bozucu():
    """Surekli cruise'da yunuslama bozucusu — kusurun asil gorundugu yer.

    Bolum 2'nin gecis senaryosu kusuru zorlamiyor, cunku orada tutum
    komutu zaten pid_gama'nin 12 derecelik limitinde doyuyor ve arac
    komutu takip edebiliyor. Itki kanalinin otoritesizligi ancak
    KAPATILAMAYAN bir moment varken ortaya cikar.

    Burada arac 85 derece tiltte cruise'da dengelenir, sonra sabit bir
    yunuslama bozucusu uygulanir. Itki kanalinin otoritesi cos(85)=0,087
    ile carpili oldugu icin bu momenti kapatmakta zorlanir. Tilt kanali
    varsa devralmali.
    """
    print()
    print("=" * 74)
    print("2b. SUREKLI CRUISE + YUNUSLAMA BOZUCUSU  (85 derece tilt, 40 s)")
    print("=" * 74)
    print(f"{'varyant':<12}{'kanal':<8}{'th kalici':>12}{'|th| azami':>12}"
          f"{'irtifa':>11}{'tilt sapma':>12}")
    print("-" * 74)

    M_BOZUCU = 1500.0        # Nm, sabit burun yukari — trim momenti mertebesi
    sonuc = {}
    for v in VARYANTLAR:
        for kanal in (False, True):
            ac = Limulus(varyant_ad=v, sensor_etkin=False)
            th_c = ac.k["THETA_CRUISE"] if v != "liftcruise" else 0.0
            d0 = np.zeros(12)
            d0[0] = 68.9
            d0[11] = -300.0
            ac.sifirla(durum=d0, tilt0=th_c, T0=500.0)
            kk = TemelKontrolcu(ac, tilt_kanali=kanal)
            kk.sifirla()
            th_izi, sapma_izi = [], []
            for i in range(int(40.0 / ac.dt)):
                T, tilt = kk(ac.durum, 300.0, 68.9, th_c)
                ac.adim(T, tilt, M_dis=np.array([0.0, M_BOZUCU, 0.0]))
                th_izi.append(math.degrees(ac.durum[7]))
                sapma_izi.append(math.degrees(abs(kk._son_trim)))
                if abs(ac.durum[7]) > math.radians(80) or -ac.durum[11] <= 0:
                    break
            kal = float(np.mean(th_izi[-int(5.0 / ac.dt):])) if th_izi else 0.0
            azm = max(abs(x) for x in th_izi) if th_izi else 0.0
            sonuc[(v, kanal)] = (kal, azm)
            print(f"{v:<12}{'acik' if kanal else 'kapali':<8}"
                  f"{kal:>11.2f}d{azm:>11.2f}d"
                  f"{-ac.durum[11]:>10.0f}m{max(sapma_izi or [0]):>11.2f}d")
        print("-" * 74)
    return sonuc


if __name__ == "__main__":
    o = bolum_1_otorite()
    c = bolum_2_kapali_cevrim()
    b = bolum_2b_cruise_bozucu()
    bolum_3_ozet(o, c)
    print()
    print("=" * 74)
    print("4. BOZUCU ALTINDA — F1'in asil olculdugu yer")
    print("=" * 74)
    for v in VARYANTLAR:
        a, y = b.get((v, False)), b.get((v, True))
        if not a or not y:
            continue
        d = abs(a[0]) - abs(y[0])
        yz = 100.0 * d / abs(a[0]) if abs(a[0]) > 1e-9 else 0.0
        print(f"  {v:<12} kalici tutum hatasi {a[0]:+7.2f}d -> {y[0]:+7.2f}d"
              f"   {yz:+6.1f}%")
