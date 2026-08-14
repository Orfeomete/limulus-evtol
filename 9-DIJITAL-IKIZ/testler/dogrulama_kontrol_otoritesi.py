# -*- coding: utf-8 -*-
"""TAM MODEL kontrol otoritesi kontrolu (cebir degil, simulatorun kendisi)."""
import sys, math
import numpy as np
sys.path.insert(0, '/home/claude/limulus/9-DIJITAL-IKIZ/dinamik')
from konfigurasyon import KONF as K
from arac import Limulus
from trim import trim
import atmosfer as atm

ac = Limulus()
hava = atm.isa(0.0)

def M_y(V, alfa, T, tilt):
    d = np.zeros(12)
    d[0] = V*math.cos(alfa); d[2] = V*math.sin(alfa); d[7] = alfa
    F, M, _ = ac.kuvvetler(d, np.asarray(T, float), np.asarray(tilt, float), hava)
    return M[1]

print("=" * 74)
print("TAM MODELDE KONTROL OTORITESI — iki kanal ayri ayri bozuluyor")
print("=" * 74)
for V, ad in ((K["V_CRUISE"], "cruise"), (0.0, "hover")):
    r = trim(ac, V=V, gama=0.0)
    if not r.basarili:
        print(f"{ad}: trim yok"); continue
    T0, th0, al0 = r.T.copy(), r.tilt.copy(), r.alfa
    M0 = M_y(V, al0, T0, th0)
    print(f"\n--- {ad}: V={V:.1f} m/s  alfa={math.degrees(al0):+.2f}  "
          f"tilt={np.degrees(th0).round(1)}  T={T0.round(0)} N")
    print(f"    trim momenti M0 = {M0:+.1f} N m  (sifira yakin olmali)")

    # kanal 1: diferansiyel itki, on cift +dT, arka cift -dT
    dT = 200.0
    Ta = T0 + np.array([+dT, +dT, -dT, -dT])
    M1 = M_y(V, al0, Ta, th0) - M0

    # kanal 2: diferansiyel tilt, on cift +dth, arka cift -dth
    dth = math.radians(10.0)
    tha = np.clip(th0 + np.array([+dth, +dth, -dth, -dth]), 0.0, math.pi/2)
    M2 = M_y(V, al0, T0, tha) - M0
    # kirpma olduysa bildir
    kirp = np.any(np.abs((th0 + np.array([+dth,+dth,-dth,-dth])) - tha) > 1e-9)

    print(f"    diferansiyel itki  +-{dT:.0f} N   ->  dM_y = {M1:+9.1f} N m")
    print(f"    diferansiyel tilt  +-{math.degrees(dth):.0f} derece ->  "
          f"dM_y = {M2:+9.1f} N m" + ("   [KIRPILDI, 90 sinirinda]" if kirp else ""))

print("\n" + "=" * 74)
print("TILT TARAMASI — sabit itkide iki sutun (kirpma olmasin diye 80 derecede durur)")
print("=" * 74)
r = trim(ac, V=K["V_CRUISE"], gama=0.0)
T_cr, al = r.T.copy(), r.alfa
r0 = trim(ac, V=0.0, gama=0.0)
T_hv = r0.T.copy()
print(f"{'tilt':>6}{'HOVER itki':>13}{'HOVER tilt':>13}"
      f"{'CRUISE itki':>14}{'CRUISE tilt':>14}")
for d in (0, 20, 40, 60, 80):
    th = np.full(4, math.radians(d))
    out = [d]
    for V, al_, T_ in ((0.0, 0.0, T_hv), (K["V_CRUISE"], al, T_cr)):
        b = M_y(V, al_, T_, th)
        a1 = M_y(V, al_, T_ + np.array([200.,200.,-200.,-200.]), th) - b
        a2 = M_y(V, al_, T_, th + np.array([1.,1.,-1.,-1.])*math.radians(10)) - b
        out += [a1, a2]
    print(f"{out[0]:>6}{out[1]:>13.0f}{out[2]:>13.0f}{out[3]:>14.0f}{out[4]:>14.0f}")
