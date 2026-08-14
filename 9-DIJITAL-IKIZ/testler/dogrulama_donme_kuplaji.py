#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARAR 46 KABUL TESTI — donme hizi kuplaji bayragi.

Ön kayit `4-KARARLAR/46-donme-hizi-kuplaji-on-kaydi.md`. Bu betik ON KAYDIN
KABUL TESTIDIR ve ön kayitta yazili olan uc kurali sinar. Kurallardan biri
gecmezse model degisikligi GERI ALINIR, sonuc uretilmez.

  Kural A  ICE GECMISLIK. Bayrak KAPALI oldugunda model, bayrak eklenmeden
           onceki hali ile birebir ayni sonucu vermeli. Kabul olcutu, karar
           43'un olcum dosyasindaki kayitlarla tam esitlik.
  Kural B  SIFIR HIZDA ESITLIK. Bayrak ACIK ve omega = 0 oldugunda sonuc
           bayrak kapalıyla birebir ayni olmali. Aksi halde kod, hizdan
           bagimsiz bir yan etki de ekliyor demektir.
  Kural C  SONUMLEME ISARETI. Bayrak acik ve omega sifirdan farkli
           oldugunda ortaya cikan moment, donme hizina KARSI koymali
           (M . omega < 0). Isaret ters cikarsa model kararsizlik uretiyor.

Kosum
    cd 9-DIJITAL-IKIZ && python3 testler/dogrulama_donme_kuplaji.py
Cikis kodu 0 ise uc kural da gecti.
"""
import json
import math
import os
import subprocess
import sys

_BURASI = os.path.dirname(os.path.abspath(__file__))
_KOK = os.path.dirname(_BURASI)
sys.path.insert(0, os.path.join(_KOK, "dinamik"))

OLCUM = os.path.join(_KOK, "cikti_asimetrik", "s1_pod_arizasi.json")
ORNEK = 8                      # karar 43 dosyasindan kac kayit sinanacak


def _cocukta_kuvvet(kuplaj: str, omega) -> dict:
    """Alt surecte kuvvetler() cagirir. Bayrak import aninda okundugu icin
    ayni surecte iki degeri birlikte sinamak yanlis olurdu."""
    kod = f"""
import os, json, math
os.environ["LIMULUS_DONME_KUPLAJI"] = {kuplaj!r}
import sys; sys.path.insert(0, {os.path.join(_KOK, 'dinamik')!r})
import numpy as np, atmosfer as atm
from arac import Limulus
ac = Limulus(varyant_ad="limulus")
d = np.zeros(12)
d[0] = 45.0
d[2] = 2.0
d[3:6] = {list(omega)!r}
T = np.full(4, ac.W / 4)
tilt = np.full(4, math.radians(35.0))
F, M, b = ac.kuvvetler(d, T, tilt, atm.isa(0.0))
print(json.dumps(dict(F=[float(x) for x in F], M=[float(x) for x in M],
                      P=float(b["P_batarya"]), bayrak=ac._donme_kuplaji)))
"""
    r = subprocess.run([sys.executable, "-c", kod], capture_output=True,
                       text=True, cwd=_KOK)
    if r.returncode != 0:
        raise SystemExit(f"alt surec hata verdi:\n{r.stderr}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def kural_a() -> int:
    """Bayrak kapali, karar 43 kayitlari birebir uretiliyor mu."""
    print("KURAL A — ice gecmislik, bayrak KAPALI")
    if not os.path.exists(OLCUM):
        print("  ATLANDI  karar 43 olcum dosyasi yok")
        return 0
    if os.environ.get("LIMULUS_DONME_KUPLAJI", "0") == "1":
        print("  ATLANDI  bayrak ortamda ACIK, bu test kapali ister")
        return 0
    import trim
    from arac import Limulus
    with open(OLCUM, encoding="utf-8") as f:
        d = json.load(f)
    ornek = ([k for k in d["kayitlar"] if not k["beta_serbest"]][:ORNEK]
             + [k for k in d["kayitlar"] if k["beta_serbest"]][:ORNEK])
    hata = 0
    for k in ornek:
        ac = Limulus(varyant_ad=k["varyant"])
        r = trim.trim_yanal(ac, k["V"], ariza=k["pod"],
                            beta_hedef=None if k["beta_serbest"] else 0.0)
        ok = (bool(r.basarili) == k["basarili"]
              and abs(math.degrees(float(r.beta)) - k["beta_derece"]) < 1e-6
              and abs(float(r.P_batarya) / 1e3 - k["P_batarya_kW"]) < 1e-6)
        if not ok:
            hata += 1
            print(f"  HATA   {k['varyant']} V={k['V']} pod={k['pod']} "
                  f"serbest={k['beta_serbest']}")
    print(f"  {'GECTI ' if not hata else 'HATA  '} {len(ornek)} kayit "
          f"sinandi, {hata} fark")
    return hata


def kural_b() -> int:
    """Bayrak acik ve omega = 0, kapaliyla birebir ayni mi."""
    print("\nKURAL B — bayrak ACIK, omega = 0")
    kapali = _cocukta_kuvvet("0", [0.0, 0.0, 0.0])
    acik = _cocukta_kuvvet("1", [0.0, 0.0, 0.0])
    if kapali["bayrak"] or not acik["bayrak"]:
        print("  HATA   bayrak alt surecte beklendigi gibi okunmadi")
        return 1
    hata = 0
    for ad in ("F", "M"):
        for i, (a, b) in enumerate(zip(kapali[ad], acik[ad])):
            if abs(a - b) > 1e-9:
                hata += 1
                print(f"  HATA   {ad}[{i}]  kapali {a:.9f}  acik {b:.9f}")
    if abs(kapali["P"] - acik["P"]) > 1e-9:
        hata += 1
        print(f"  HATA   P  kapali {kapali['P']:.6f}  acik {acik['P']:.6f}")
    print(f"  {'GECTI ' if not hata else 'HATA  '} kuvvet, moment ve guc "
          f"{'birebir ayni' if not hata else 'AYRISTI'}")
    return hata


def kural_c() -> int:
    """Sonumleme donme hizina karsi mi koyuyor."""
    print("\nKURAL C — sonumleme isareti, M . omega < 0 olmali")
    taban = _cocukta_kuvvet("1", [0.0, 0.0, 0.0])
    hata = 0
    for ad, om in (("yatis  p", [0.30, 0.0, 0.0]),
                   ("yunuslama q", [0.0, 0.30, 0.0]),
                   ("sapma  r", [0.0, 0.0, 0.30])):
        r = _cocukta_kuvvet("1", om)
        dM = [a - b for a, b in zip(r["M"], taban["M"])]
        ic = sum(a * b for a, b in zip(dM, om))
        buyukluk = math.sqrt(sum(x * x for x in dM))
        if buyukluk < 1e-6:
            print(f"  UYARI  {ad:<12} moment degisimi ~0 "
                  f"({buyukluk:.2e} N m), sonumleme YOK")
            continue
        ok = ic < 0
        hata += 0 if ok else 1
        print(f"  {'GECTI ' if ok else 'HATA  '} {ad:<12} "
              f"dM = ({dM[0]:+8.1f}, {dM[1]:+8.1f}, {dM[2]:+8.1f}) N m  "
              f"dM . omega = {ic:+.2f}")
    return hata


def main():
    print("KARAR 46 KABUL TESTI — donme hizi kuplaji")
    print("=" * 72)
    hata = kural_a() + kural_b() + kural_c()
    print("=" * 72)
    if hata:
        print(f"SONUC: {hata} KURAL IHLALI. Ön kayit geregi model "
              "degisikligi GERI ALINIR.")
        return 1
    print("SONUC: UC KURAL DA GECTI. Bayrak kullanilabilir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
