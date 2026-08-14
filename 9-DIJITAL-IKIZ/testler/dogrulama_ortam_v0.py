#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KARAR 52 B0 — LIMULUS_ORTAM_V0 bayraginin birim dogrulamasi.

Uc denetim: T1 mutlak esleme, T2 esiksiz stall cezasi, T3 cezasiz tutum
sonlanmasi. Ayrica bayrak KAPALI regresyon ayri koşuldu (taban iz sha).
"""
import os, sys, math
os.environ["LIMULUS_ORTAM_V0"] = "1"
os.environ["LIMULUS_CRUISE_ITKI"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ogrenme"))
import numpy as np
from ortam import ortam_yap

# --- T1: sifir eylem artik trimi KORUMAZ, mutlak eslemede dusme beklenir
o = ortam_yap("limulus", seviye=0, tohum=2)
o.reset(seed=2)
e0 = np.zeros(o.n_eylem)
n = 0
for i in range(1000):
    g, r, bitti, kesildi, bilgi = o.step(e0)
    n += 1
    if bitti or kesildi:
        break
print(f"T1  sifir eylem: {n} adim, {'COKTU' if bitti else 'sure doldu'}")
assert bitti and n < 1000, "T1 dogrulanamadi, sifir eylem hala trimi koruyor"

# --- T2: hover'da (V < 25) stall cezasi atesleniyor mu
o = ortam_yap("limulus", seviye=0, tohum=3)
o.reset(seed=3)
t2_bulundu = False
for i in range(1000):
    g, r, bitti, kesildi, bilgi = o.step(np.zeros(o.n_eylem))
    if bilgi["V"] < 25.0 and bilgi["zarf"] <= -5.0 and abs(bilgi["alfa"]) > o.ac.kanat.alfa_stall:
        t2_bulundu = True
        print(f"T2  adim {i}: V={bilgi['V']:.1f} m/s, alfa buyuk, zarf={bilgi['zarf']:.1f}")
        break
    if bitti or kesildi:
        o.reset(seed=100+i)
assert t2_bulundu, "T2 dogrulanamadi, dusuk hizda stall cezasi gorulmedi"

# --- T3a: tutum asimiyla biten bolumde cokme cezasi SIFIR
tutum_cezasiz = None
o = ortam_yap("limulus", seviye=0, tohum=5)
rng = np.random.default_rng(42)
deneme = 0
while tutum_cezasiz is None and deneme < 400:
    o.reset(seed=1000+deneme)
    deneme += 1
    for i in range(1500):
        g, r, bitti, kesildi, bilgi = o.step(rng.uniform(-1, 1, o.n_eylem))
        if bitti:
            d = o.ac.durum
            h = -d[11]
            tutum = abs(d[6]) > math.radians(85) or abs(d[7]) > math.radians(85)
            if h > 0.0 and tutum and bilgi["enerji_orani"] <= 1.0:
                tutum_cezasiz = bilgi["cokme"]
                print(f"T3a tutum asimi sonlanmasi: cokme parcasi = {bilgi['cokme']:.1f} (beklenen 0)")
            break
        if kesildi:
            break
assert tutum_cezasiz == 0.0, f"T3a dogrulanamadi: {tutum_cezasiz}"

# --- T3b: yere carpmayla biten bolum cezali. Rastgele politika V0'da hep
# takla attigi icin carpma sifir eylemle uretilir (yavas one dusme).
o = ortam_yap("limulus", seviye=0, tohum=2)
o.reset(seed=2)
carpma_cezali = None
for i in range(1000):
    g, r, bitti, kesildi, bilgi = o.step(np.zeros(o.n_eylem))
    if bitti:
        h = -o.ac.durum[11]
        assert h <= 0.0, "beklenen carpma, baska sonlanma geldi"
        carpma_cezali = bilgi["cokme"]
        print(f"T3b yere carpma sonlanmasi: cokme parcasi = {bilgi['cokme']:.1f} (beklenen -100)")
        break
assert carpma_cezali == -100.0, f"T3b dogrulanamadi: {carpma_cezali}"

print("\nB0 DOGRULAMASI GECTI — uc kusur da bayrak arkasinda geri geldi")
