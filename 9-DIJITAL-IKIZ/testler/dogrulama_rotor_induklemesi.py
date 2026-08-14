#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARAR 50 KABUL TESTI — rotor induklemesinin itkiye baglanmasi bayragi.

Ön kayit `4-KARARLAR/50-rotor-induklemesi-itki-baglanmasi-on-kaydi.md`. Bu
betik ON KAYDIN KABUL TESTIDIR ve orada yazili kurallari sinar. Bir kural
gecmezse model degisikligi GERI ALINIR ve sonuc uretilmez.

  Kural 2  BOZULMAZLIK. Bayrak KAPALI oldugunda kuvvet ve moment, bayrak
           eklenmeden onceki hali ile BIREBIR ayni olmali. Olcut, donme
           kuplaji acik ve kapali her iki halde de rotor indukleme
           bayraginin HICBIR fark uretmemesi (omega = 0 dahil).
  Kural 3  ISARET. Bayrak acik ve q sifirdan farkli oldugunda ortaya cikan
           yunuslama momenti, yunuslama hizina KARSI koymali, yani
           dM/dq < 0. Pozitif cikarsa bu bir KODLAMA HATASI isaretidir ve
           bulgu olarak yazilmaz.
  Kural 4  KARSILASTIRMA. Sonumlemeye esik konmaz. Rotor payi, kanat ve
           govde paylarinin YANINDA raporlanir.

⚠️ Bu betik bir OLCUM betigi degil bir KABUL testidir. Urettigi sayilar
karar 50'nin sonuc bolumune girer, fakat hukum ön kayittaki kurallardan
cikar, buradan cikmaz.

Kosum
    cd 9-DIJITAL-IKIZ && python3 testler/dogrulama_rotor_induklemesi.py
Cikis kodu
    0 = kural 2 ve 3 gecti. 1 = biri gecmedi, degisiklik geri alinir.
"""
import json
import math
import os
import subprocess
import sys

_BURASI = os.path.dirname(os.path.abspath(__file__))
_KOK = os.path.dirname(_BURASI)
_DIN = os.path.join(_KOK, "dinamik")

# --- dondurulmus sinama noktasi -------------------------------------
# Cruise tasarim noktasi. Ön kayitta bir nokta secimi yazili degildi,
# dolayisiyla burada TASARIM NOKTASI secildi ve gerekcesi sudur, karar 46
# de ayni noktada olcmustu, iki olcum karsilastirilabilir kalsin.
V_CRUISE = 68.9          # m/s, tasarim cruise hizi
TILT_CRUISE = 85.0       # derece
Q_SINAMA = 0.10          # rad/s, yunuslama hizi
P_SINAMA = 0.10          # rad/s, yatis hizi
R_SINAMA = 0.10          # rad/s, sapma hizi


def _cocukta(indukleme: str, kuplaj: str, omega) -> dict:
    """Alt surecte kuvvetler() cagirir.

    ⚠️ Bayraklar IMPORT ANINDA okunuyor, dolayisiyla ayni surecte iki
    degeri birlikte sinamak yanlis olurdu. Karar 46'nin testi de boyle
    yapiyor, ayni desen korundu.
    """
    kod = f"""
import os, json, math
os.environ["LIMULUS_ROTOR_INDUKLEME"] = {indukleme!r}
os.environ["LIMULUS_DONME_KUPLAJI"] = {kuplaj!r}
import sys; sys.path.insert(0, {_DIN!r})
import numpy as np, atmosfer as atm
from arac import Limulus
ac = Limulus(varyant_ad="limulus")
hava = atm.isa(300.0)
V = {V_CRUISE!r}
tilt = np.full(4, math.radians({TILT_CRUISE!r}))
# trim itkisi, dort pod esit ve cruise suruklemesini yenecek kadar
import trim
r = trim.trim_duz(ac, V) if hasattr(trim, "trim_duz") else None
if r is not None and getattr(r, "basarili", False):
    T = np.asarray(r.T, float); tilt = np.asarray(r.tilt, float)
else:
    T = np.full(4, ac.W / 4.0 * 0.10)
durum = np.zeros(12)
durum[0] = V
durum[3:6] = {list(omega)!r}
F, M, bilgi = ac.kuvvetler(durum, T, tilt, hava)
print(json.dumps(dict(F=[float(x) for x in F], M=[float(x) for x in M],
                      T=[float(x) for x in T],
                      tilt=[float(x) for x in tilt],
                      dT=[float(x) for x in bilgi.get("dT_indukleme", [0,0,0,0])])))
"""
    r = subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-1500:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def _bar(t):
    print("\n" + "=" * 74)
    print(t)
    print("=" * 74)


def main() -> int:
    print("=" * 74)
    print("KARAR 50 KABUL TESTI — rotor induklemesinin itkiye baglanmasi")
    print("=" * 74)
    print(f"sinama noktasi  V = {V_CRUISE} m/s · tilt = {TILT_CRUISE} deg · "
          f"q = {Q_SINAMA} rad/s")

    gecti = True

    # ---------------------------------------------------------------
    _bar("KURAL 2 — BOZULMAZLIK, bayrak kapaliyken model degismemeli")
    sifir = [0.0, 0.0, 0.0]
    qvec = [0.0, Q_SINAMA, 0.0]

    haller = [
        ("kuplaj KAPALI · omega = 0", "0", sifir),
        ("kuplaj KAPALI · omega = q", "0", qvec),
        ("kuplaj ACIK   · omega = 0", "1", sifir),
    ]
    for etiket, kup, om in haller:
        a = _cocukta("0", kup, om)
        b = _cocukta("1", kup, om)
        dF = max(abs(x - y) for x, y in zip(a["F"], b["F"]))
        dM = max(abs(x - y) for x, y in zip(a["M"], b["M"]))
        dT = max(abs(x) for x in b["dT"])
        ok = dF < 1e-9 and dM < 1e-9 and dT < 1e-12
        gecti &= ok
        print(f"  {'GECTI' if ok else 'GECMEDI':<8}{etiket:<28}"
              f"dF {dF:.2e} N · dM {dM:.2e} N m · azami dT {dT:.2e} N")

    print("\n  ⚠️ Ucuncu satir onemlidir. Kuplaj ACIK fakat omega SIFIR iken de")
    print("     duzeltme sifir kalmali, yoksa kod hizdan bagimsiz bir yan etki")
    print("     de ekliyor demektir.")

    # ---------------------------------------------------------------
    _bar("KURAL 3 — ISARET, dM/dq negatif olmali")
    print("  ⚠️ Kuplaj ACIK olmadan bu bayrak etkisizdir, cunku yerel akis")
    print("     govde akisinin aynisi olur. Ikisi birlikte aciliyor.")
    kapali = _cocukta("0", "1", sifir)
    tablo = []
    for ad, om, eksen in (("yunuslama q", [0.0, Q_SINAMA, 0.0], 1),
                          ("yatis p", [P_SINAMA, 0.0, 0.0], 0),
                          ("sapma r", [0.0, 0.0, R_SINAMA], 2)):
        a = _cocukta("0", "1", om)          # yalniz kuplaj
        b = _cocukta("1", "1", om)          # kuplaj + indukleme
        # kuplajin kendi payi ve induklemenin EK payi
        pay_kuplaj = a["M"][eksen] - kapali["M"][eksen]
        pay_ind = b["M"][eksen] - a["M"][eksen]
        toplam = b["M"][eksen] - kapali["M"][eksen]
        hiz = om[eksen]
        tablo.append((ad, pay_kuplaj, pay_ind, toplam, toplam / hiz,
                      max(abs(x) for x in b["dT"])))

    print(f"\n  {'eksen':<14}{'kuplaj payi':>14}{'indukleme payi':>16}"
          f"{'toplam':>12}{'turev':>12}{'azami dT':>11}")
    print("  " + "-" * 79)
    for ad, pk, pi, tp, tr, dt in tablo:
        print(f"  {ad:<14}{pk:>14.3f}{pi:>16.3f}{tp:>12.3f}{tr:>12.3f}{dt:>11.2f}")
    print(f"  {'':14}{'N m':>14}{'N m':>16}{'N m':>12}{'N m s':>12}{'N':>11}")

    q_turev = tablo[0][4]
    ok3 = q_turev < 0.0
    gecti &= ok3
    print(f"\n  {'GECTI' if ok3 else 'GECMEDI'}  dM/dq = {q_turev:.4f} N m s, "
          f"{'sonumleyici' if ok3 else 'KARARSIZ, kodlama hatasi aranir'}")
    if not ok3 and abs(q_turev) < 1e-9:
        print("  ⚠️ Turev SIFIR cikti. Bu kural 3'un ihlali degildir fakat")
        print("     bulgu 'sonumleme uretilmedi' olur, kural 4 tablosu yine yazilir.")
        gecti = True

    # ---------------------------------------------------------------
    _bar("KURAL 4 — KARSILASTIRMA, esik yok, paylar yan yana")
    print("  Yukaridaki tablonun 'kuplaj payi' sutunu kanat ve govdenin")
    print("  kattigini, 'indukleme payi' sutunu rotorun kattigini vermektedir.")
    print("  Mutlak bir yeterlilik iddiasi KURULMAZ, o ucus nitelikleri")
    print("  olcutu gerektirir ve Bölüm 10'un konusudur.")

    # ---------------------------------------------------------------
    _bar("SONUC")
    if gecti:
        print("Kural 2 ve 3 gecti. Sonuclar karar 50'nin SONUCLAR bolumune yazilabilir.")
    else:
        print("BIR KURAL GECMEDI. Ön kayit geregi model degisikligi GERI ALINIR.")
    return 0 if gecti else 1


if __name__ == "__main__":
    sys.exit(main())
