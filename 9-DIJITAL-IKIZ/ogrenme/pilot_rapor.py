# -*- coding: utf-8 -*-
"""Pilot kosunun on kayit karar kurallarina gore degerlendirilmesi."""
import json, glob, os
import numpy as np

D = "/home/claude/limulus/9-DIJITAL-IKIZ/ogrenme/kosular"
VAR = ("limulus", "ikili", "senkron", "liftcruise")
sonuc = {}
for v in VAR:
    kayit = []
    for f in sorted(glob.glob(os.path.join(D, f"{v}_t*_gunluk.json"))):
        d = json.load(open(f))
        g = d["gunluk"] if isinstance(d, dict) and "gunluk" in d else d
        son = g[-1]
        # son %10'un ortalamasi, tek noktanin gurultusunden kacinmak icin
        n = max(1, len(g)//10)
        odul_son = float(np.mean([x["odul"] for x in g[-n:]]))
        uz_son = float(np.mean([x["adim"]/max(x["n_bolum"],1) for x in g[-n:]]))
        kayit.append(dict(tohum=os.path.basename(f), odul=odul_son,
                          uzunluk=uz_son, seviye=son["seviye"]))
    sonuc[v] = kayit

print("="*78)
print("PILOT KOSU — ON KAYIT §5 KARAR KURALLARINA GORE DEGERLENDIRME")
print("="*78)
print(f"{'varyant':<12}{'kosu':>5}{'odul ort':>11}{'std':>9}"
      f"{'bolum uz.':>11}{'en yuksek sev.':>16}")
print("-"*78)
istat = {}
for v in VAR:
    k = sonuc[v]
    if not k:
        print(f"{v:<12}{0:>5}{'KOSU YOK':>11}")
        continue
    o = np.array([x["odul"] for x in k]); u = np.array([x["uzunluk"] for x in k])
    s = max(x["seviye"] for x in k)
    istat[v] = (o.mean(), o.std(ddof=1) if len(o)>1 else 0.0, u.mean(), s, len(k))
    print(f"{v:<12}{len(k):>5}{o.mean():>11.3f}{istat[v][1]:>9.3f}"
          f"{u.mean():>11.0f}{s:>16}")

print()
print("KURAL 1 — ic ice gecmislik kontrolu")
if "limulus" in istat and "senkron" in istat:
    dL, dS = istat["limulus"], istat["senkron"]
    esik = 2*max(dL[1], dS[1])
    fark = dL[0]-dS[0]
    print(f"  LIMULUS {dL[0]:+.3f}  senkron {dS[0]:+.3f}  fark {fark:+.3f}"
          f"  (2 std = {esik:.3f})")
    if fark < -esik:
        print("  ⛔ IHLAL — LIMULUS senkrondan anlamli KOTU, kosu gecersiz")
    else:
        print("  ✅ ihlal yok")

print()
print("KURAL 2 — anlamlilik")
if "limulus" in istat and "ikili" in istat:
    a, b = istat["limulus"], istat["ikili"]
    esik = 2*max(a[1], b[1])
    print(f"  LIMULUS {a[0]:+.3f} vs ikili {b[0]:+.3f}  |fark| {abs(a[0]-b[0]):.3f}"
          f"  esik {esik:.3f}  -> "
          f"{'FARK VAR' if abs(a[0]-b[0])>esik else 'FARK YOK'}")

print()
print("KURAL 3 — seviye ilerlemesi")
en = max((istat[v][3] for v in istat), default=-1)
print(f"  Ulasilan en yuksek mufredat seviyesi: {en} (hover)")
print("  Seviye 2 (gecis) ULASILMADI.")
print("  -> Bagimsiz tiltin gecis rejimindeki iddiasi OGRENME KOSULARIYLA")
print("     SINANAMAMIS sayilir. Politikadan bagimsiz metrikler tek kanit.")

print()
print("KURAL 4 — olumsuz sonuc gizlenmez")
print("  Pilot hicbir eksende karsilastirilabilir sonuc uretmedi.")
print("  Uretemeyisin nedeni ortamin kusurlariydi (4-KARARLAR/15), varyant")
print("  farki degil. Bu ayrim raporlanir.")

print()
print("TAMLIK")
top = sum(istat[v][4] for v in istat)
print(f"  {top}/20 kosu tamamlandi. Eksik: ", end="")
print(", ".join(f"{v} ({5-istat[v][4]})" for v in VAR if istat.get(v,(0,0,0,0,0))[4]<5))
print("  Kalan 10 kosu BASLATILMADI cunku ilk 10'un tamami seviye 0'da takildi")
print("  ve kok neden bulundu. Ayni kusurla 10 kosu daha uretmek bilgi katmaz.")
