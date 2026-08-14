#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A4 — ASIMETRIK DINAMIK SENARYOLAR

B1 statik trimde su cevabi verdi: tilt kabiliyeti pod arizasini yan
kaymasiz kapatabiliyor (%67), senkron ve lift+cruise kapatamiyor (%0).
Fakat DORT eksen ile IKI eksen ayni cikti.

Bu betik soruyu dinamik senaryolara tasiyor. Statik trim bir denge
noktasinin VARLIGINI sorar, dinamik senaryo o noktaya ULASILABILIRLIGINI
ve gecis surecini sorar. Dort eksenin gerekcesi buradaysa burada
gorunmelidir.

Uc senaryo, ucu de kapali cevrim, temel kontrolcu ile.

  S1  Cruise'da ani pod arizasi     — toparlanma, azami sapma, kalici hata
  S2  Yanal gust (Dryden benzeri)   — yatis ve sapma sapmasi
  S3  Gecis sirasinda pod arizasi   — en zor durum, iki gecici ust uste

Politikadan bagimsizdir, egitim gerektirmez.
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

from arac import Limulus                                     # noqa: E402
from temel_kontrolcu import TemelKontrolcu, hiz_programli_tilt  # noqa: E402

VARYANTLAR = ("limulus", "ikili", "senkron", "liftcruise")


def _kos(v, sure, kur, bozucu=None, ariza_t=None, ariza_pod=0):
    """Kapali cevrim kosu. kur(ac) baslangic durumunu kurar."""
    ac = Limulus(varyant_ad=v, sensor_etkin=False)
    th_c, V_h, h_h = kur(ac)
    kk = TemelKontrolcu(ac)
    kk.sifirla()
    olcum = dict(phi=[], theta=[], psi=[], h=[], V=[], dusdu=False)
    n = int(sure / ac.dt)
    for i in range(n):
        t = ac.t
        T, tilt = kk(ac.durum, h_h, V_h(t) if callable(V_h) else V_h,
                     th_c(t) if callable(th_c) else th_c)
        if ariza_t is not None and t >= ariza_t:
            T = np.array(T, float)
            T[ariza_pod] = 0.0
        M = bozucu(t) if bozucu else None
        ac.adim(T, tilt, M_dis=M)
        d = ac.durum
        olcum["phi"].append(math.degrees(d[6]))
        olcum["theta"].append(math.degrees(d[7]))
        olcum["psi"].append(math.degrees(d[8]))
        olcum["h"].append(-d[11])
        olcum["V"].append(float(np.linalg.norm(d[0:3])))
        if -d[11] <= 0.0 or abs(d[7]) > math.radians(80) \
                or abs(d[6]) > math.radians(80):
            olcum["dusdu"] = True
            break
    return ac, olcum


def _ozet(o, t_ariza_orani=0.5):
    """Ariza sonrasi bandin ozeti."""
    n = len(o["phi"])
    if n == 0:
        return dict(phi=999, psi=999, dh=999, dusdu=True)
    k = int(n * t_ariza_orani)
    son = slice(max(k, n - int(n * 0.25)), n)
    return dict(
        phi=max(abs(x) for x in o["phi"][k:]) if k < n else 0.0,
        psi=max(abs(x) for x in o["psi"][k:]) if k < n else 0.0,
        dh=o["h"][-1] - o["h"][0],
        dusdu=o["dusdu"])


# =====================================================================
def s1_cruise_ariza():
    print("=" * 78)
    print("S1 — CRUISE'DA ANI POD ARIZASI  (t=5 s, pod 0, 25 s izleme)")
    print("=" * 78)
    print(f"{'varyant':<12}{'dustu':>8}{'|phi| azami':>13}{'|psi| azami':>13}"
          f"{'irtifa degisimi':>17}")
    print("-" * 78)
    r = {}
    for v in VARYANTLAR:
        def kur(ac, v=v):
            th = ac.k["THETA_CRUISE"] if v != "liftcruise" else 0.0
            d = np.zeros(12); d[0] = 68.9; d[11] = -300.0
            ac.sifirla(durum=d, tilt0=th, T0=500.0)
            return th, 68.9, 300.0
        _, o = _kos(v, 25.0, kur, ariza_t=5.0)
        s = _ozet(o, 0.2)
        r[v] = s
        print(f"{v:<12}{'EVET' if s['dusdu'] else 'hayir':>8}"
              f"{s['phi']:>12.2f}d{s['psi']:>12.2f}d{s['dh']:>16.1f}m")
    return r


def s2_yanal_gust():
    print()
    print("=" * 78)
    print("S2 — YANAL GUST  (t=5 s'de 3000 Nm sapma bozucusu, 3 s sureli)")
    print("=" * 78)
    print(f"{'varyant':<12}{'dustu':>8}{'|phi| azami':>13}{'|psi| azami':>13}"
          f"{'irtifa degisimi':>17}")
    print("-" * 78)

    def gust(t):
        return np.array([0.0, 0.0, 3000.0]) if 5.0 <= t < 8.0 else None

    r = {}
    for v in VARYANTLAR:
        def kur(ac, v=v):
            th = ac.k["THETA_CRUISE"] if v != "liftcruise" else 0.0
            d = np.zeros(12); d[0] = 68.9; d[11] = -300.0
            ac.sifirla(durum=d, tilt0=th, T0=500.0)
            return th, 68.9, 300.0
        _, o = _kos(v, 25.0, kur, bozucu=gust)
        s = _ozet(o, 0.2)
        r[v] = s
        print(f"{v:<12}{'EVET' if s['dusdu'] else 'hayir':>8}"
              f"{s['phi']:>12.2f}d{s['psi']:>12.2f}d{s['dh']:>16.1f}m")
    return r


def s3_gecis_ariza():
    print()
    print("=" * 78)
    print("S3 — GECIS SIRASINDA POD ARIZASI  (t=15 s, en zor durum)")
    print("=" * 78)
    print(f"{'varyant':<12}{'dustu':>8}{'|phi| azami':>13}{'|psi| azami':>13}"
          f"{'irtifa degisimi':>17}")
    print("-" * 78)
    r = {}
    for v in VARYANTLAR:
        acs = {}

        def kur(ac, v=v, acs=acs):
            acs["ac"] = ac
            d = np.zeros(12); d[11] = -300.0
            ac.sifirla(durum=d, tilt0=0.0, T0=ac.W / 4)
            th = (lambda t: hiz_programli_tilt(acs["ac"].durum[0])) \
                if v != "liftcruise" else 0.0
            return th, (lambda t: 68.9 * min(max((t - 5.0) / 25.0, 0.0), 1.0)), \
                300.0
        _, o = _kos(v, 40.0, kur, ariza_t=15.0)
        s = _ozet(o, 0.35)
        r[v] = s
        print(f"{v:<12}{'EVET' if s['dusdu'] else 'hayir':>8}"
              f"{s['phi']:>12.2f}d{s['psi']:>12.2f}d{s['dh']:>16.1f}m")
    return r


if __name__ == "__main__":
    a = s1_cruise_ariza()
    b = s2_yanal_gust()
    c = s3_gecis_ariza()
    print()
    print("=" * 78)
    print("DORT EKSEN ILE IKI EKSEN ARASINDA FARK VAR MI")
    print("=" * 78)
    for ad, r in (("S1 cruise ariza", a), ("S2 yanal gust", b),
                  ("S3 gecis ariza", c)):
        l, i = r.get("limulus"), r.get("ikili")
        if not l or not i:
            continue
        fark = (abs(l["phi"] - i["phi"]) + abs(l["psi"] - i["psi"])
                + abs(l["dh"] - i["dh"]))
        print(f"  {ad:<18} limulus phi {l['phi']:6.2f} psi {l['psi']:6.2f}"
              f"   ikili phi {i['phi']:6.2f} psi {i['psi']:6.2f}"
              f"   {'FARK VAR' if fark > 0.5 else 'fark yok'}")
