#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DENEY SURUCUSU — dort konfigurasyon x N tohum

Karsilastirmanin tek degiskeni kontrol mimarisidir. Bu dosya, her
varyanti AYNI tohum setiyle, AYNI hiperparametrelerle ve AYNI
mufredatla egiterek bunu yapisal olarak garanti eder.

Kosular BAGIMSIZDIR ve her biri bittiginde sonucu diske yazilir.
Boylece kosu yarida kesilse bile o ana kadarki veri kullanilabilir
kalir. Kismi sonuc, hicbir sonuctan iyidir — ama kismi oldugu
raporda ACIKCA yazilir.

Kullanim
    python3 deney.py --adim 400000 --tohum-sayisi 5 --isci 2
    python3 deney.py --ozet          # yalniz mevcut sonuclari topla
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

_TUM = ("limulus", "ikili", "senkron", "liftcruise")
# Tek varyanti yeniden kosmak icin (ornegin B4 sonrasi lift+cruise).
VARYANTLAR = tuple(os.environ.get("LIMULUS_VARYANTLAR", "").split(",")) \
    if os.environ.get("LIMULUS_VARYANTLAR") else _TUM
CIKTI = os.environ.get("LIMULUS_KOSU_DIZINI", "kosular")


def kosu_yolu(varyant: str, tohum: int) -> str:
    return os.path.join(CIKTI, f"{varyant}_t{tohum}_gunluk.json")


def tek_kosu(varyant: str, tohum: int, adim: int) -> dict:
    """Ayri bir surecte tek egitim kosusu. Cikti dosyasi zaten varsa atlar."""
    yol = kosu_yolu(varyant, tohum)
    if os.path.exists(yol):
        return dict(varyant=varyant, tohum=tohum, durum="zaten var")
    ortam_env = dict(os.environ)
    ortam_env["OMP_NUM_THREADS"] = "1"
    ortam_env["MKL_NUM_THREADS"] = "1"
    t0 = time.time()
    r = subprocess.run(
        [sys.executable, os.environ.get("LIMULUS_EGITIM", "egitim.py"), "--varyant", varyant,
         "--tohum", str(tohum), "--adim", str(adim)],
        capture_output=True, text=True, env=ortam_env,
        cwd=os.path.dirname(os.path.abspath(__file__)))
    return dict(varyant=varyant, tohum=tohum,
                durum="tamam" if r.returncode == 0 else "hata",
                sure=time.time() - t0,
                hata=r.stderr[-500:] if r.returncode != 0 else "")


def ozet() -> dict:
    """Diskteki gunlukleri topla. Eksik kosular acikca isaretlenir."""
    out = {}
    for v in VARYANTLAR:
        kayitlar = []
        for t in range(20):
            y = kosu_yolu(v, t)
            if not os.path.exists(y):
                continue
            with open(y) as f:
                d = json.load(f)
            g = d["gunluk"]
            if not g:
                continue
            kayitlar.append(dict(
                tohum=t,
                son_odul=g[-1]["odul"],
                en_yuksek_seviye=max(x["seviye"] for x in g),
                toplam_adim=g[-1]["adim"],
                sure=g[-1]["sure"],
                gunluk=g))
        out[v] = kayitlar
    return out


def esige_ulasma(gunluk, esik: float) -> float | None:
    """Odul esigi ilk kez asildiginda harcanan cevre adimi."""
    for k in gunluk:
        if k["odul"] >= esik:
            return float(k["adim"])
    return None


def rapor(o: dict, esik: float = 0.5) -> str:
    s = []
    s.append("DENEY OZETI")
    s.append("=" * 78)
    beklenen = max((len(k) for k in o.values()), default=0)
    s.append(f"{'varyant':<14}{'kosu':>6}{'son odul':>12}{'std':>9}"
             f"{'en yuksek sev.':>16}{'ogrenme verimi':>17}")
    s.append("-" * 78)
    for v, kayitlar in o.items():
        if not kayitlar:
            s.append(f"{v:<14}{'0':>6}   kosu yok")
            continue
        oduller = [k["son_odul"] for k in kayitlar]
        ort = sum(oduller) / len(oduller)
        std = (sum((x - ort) ** 2 for x in oduller) / max(len(oduller) - 1, 1)) ** 0.5
        sev = max(k["en_yuksek_seviye"] for k in kayitlar)
        ver = [esige_ulasma(k["gunluk"], esik) for k in kayitlar]
        ver = [x for x in ver if x is not None]
        vs = f"{sum(ver)/len(ver):,.0f} adim" if ver else "ulasilmadi"
        s.append(f"{v:<14}{len(kayitlar):>6}{ort:>12.3f}{std:>9.3f}"
                 f"{sev:>16}{vs:>17}")
    s.append("")
    eksik = [f"{v} ({beklenen - len(k)})" for v, k in o.items()
             if len(k) < beklenen]
    if eksik:
        s.append("⚠️ EKSIK KOSU VAR — sonuc kismidir: " + ", ".join(eksik))
    else:
        s.append("Tum kosular tamamlandi.")
    s.append(f"Ogrenme verimi esigi {esik}")
    return "\n".join(s)


def main():
    p = argparse.ArgumentParser(description="LIMULUS deney surucusu")
    p.add_argument("--adim", type=int, default=1_000_000)
    p.add_argument("--tohum-sayisi", type=int, default=5)
    p.add_argument("--isci", type=int, default=2)
    p.add_argument("--ozet", action="store_true")
    ar = p.parse_args()

    os.makedirs(CIKTI, exist_ok=True)
    if ar.ozet:
        print(rapor(ozet()))
        return

    isler = [(v, t) for t in range(ar.tohum_sayisi) for v in VARYANTLAR]
    print(f"{len(isler)} kosu · {ar.adim:,} adim · {ar.isci} isci")
    print("Sira tohum-oncelikli: her tohum icin dort varyant birlikte biter,")
    print("boylece kosu yarida kesilse de karsilastirilabilir bir set kalir.\n")

    from concurrent.futures import ThreadPoolExecutor
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=ar.isci) as ex:
        for i, r in enumerate(ex.map(lambda a: tek_kosu(*a, ar.adim), isler), 1):
            print(f"[{i:>2}/{len(isler)}] {r['varyant']:<11} tohum {r['tohum']} "
                  f"{r['durum']:<10} {r.get('sure', 0)/60:5.1f} dk "
                  f"(toplam {(time.time()-t0)/60:.0f} dk)", flush=True)
            if r["durum"] == "hata":
                print("   " + r["hata"].replace("\n", "\n   "), flush=True)

    print("\n" + rapor(ozet()))
    with open("deney_ozeti.json", "w") as f:
        json.dump(ozet(), f, indent=1)


if __name__ == "__main__":
    main()
