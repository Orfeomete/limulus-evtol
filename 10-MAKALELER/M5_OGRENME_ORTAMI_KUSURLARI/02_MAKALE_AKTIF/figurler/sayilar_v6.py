#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M5 v6 SAYI TURETICI — makalede gecen her yeni sayiyi kosu ciktilarindan uretir.

Kaynaklar
    9-DIJITAL-IKIZ/ogrenme/k52_degerlendirme.json   (karar 52 Bolum A, 40 kosu)
    9-DIJITAL-IKIZ/ogrenme/kosular_t3_v0/*.json     (karar 52 Bolum B, 2 kosu)

⚠️ Bu betik SAYI URETMEZ, olcum ciktilarindan OKUR. v5'te Sekil 3'un girdileri
`fig3_veri.json` icine ELLE yaziliyordu, cunku degerlendirme cagrisinin cikti
dosyasi saklanmamisti. Karar 52 kampanyasinda cikti dosyasi saklandigi icin
v6'da o dosya bu betik tarafindan URETILIR ve elle yazilan tek sutun klasik
kontrolcu sutunu olarak kalir (o olcumun cikti dosyasi hala yoktur).

Kosum
    python3 sayilar_v6.py            # ozet yazar
    python3 sayilar_v6.py --fig3     # ayrica fig3_veri.json'u gunceller
"""
import argparse
import json
import os
import statistics as st

_B = os.path.dirname(os.path.abspath(__file__))
_KOK = os.path.abspath(os.path.join(_B, "..", "..", "..", ".."))
KOSU = os.path.join(_KOK, "9-DIJITAL-IKIZ", "ogrenme")

VARYANT = ("limulus", "ikili", "senkron", "liftcruise")
SONDA = {"kosular_esik_sonda600_s5": "A1 (F1, gamma 0,99)",
         "kosular_esik_gamma999_s5": "A2 (F1+F2, gamma 0,999)"}


def _yukle():
    with open(os.path.join(KOSU, "k52_degerlendirme.json"), encoding="utf-8") as f:
        return json.load(f)


def bolum_a(D):
    """Bolum A ozeti. Dagilim disi kosular karar 52 kural 3 geregi bant
    hesabindan cikarilir, mekanizma sayimlarina (irtifa, sonlanma) girer."""
    ozet = {}
    for dizin, ad in SONDA.items():
        s = {"ad": ad, "varyant": {}, "neden": {}, "h_azami": [], "tilt": [],
             "kapi_gecen": [], "disi": []}
        icdeki_pay, icdeki_odul = [], []
        for v in VARYANT:
            ks = D[dizin][v]
            ic = [k for k in ks if not k["dagilim_disi"]]
            pay = [k["pay"] * 100 for k in ic]
            odul = [k["odul"] for k in ic]
            s["varyant"][v] = dict(
                n=len(ic), n_toplam=len(ks),
                pay_ort=st.mean(pay), pay_sap=st.stdev(pay) if len(pay) > 1 else 0.0,
                pay_alt=min(pay), pay_ust=max(pay),
                odul_ort=st.mean(odul), odul_sap=st.stdev(odul) if len(odul) > 1 else 0.0)
            icdeki_pay += pay
            icdeki_odul += odul
            s["disi"] += [f"{v} t{k['tohum']}({k['sev2_egitim']})"
                          for k in ks if k["dagilim_disi"]]
            for k in ks:
                s["h_azami"].append(k["h_azami"])
                s["tilt"].append((v, k["tohum"], k["tilt_der"]))
                for n in k["nedenler"]:
                    s["neden"][n] = s["neden"].get(n, 0) + 1
                if k["odul"] >= 0.65:
                    s["kapi_gecen"].append((v, k["tohum"], k["odul"], k["pay"],
                                            k["h_azami"], k["tilt_der"]))
        s["pay_alt"], s["pay_ust"] = min(icdeki_pay), max(icdeki_pay)
        s["odul_alt"], s["odul_ust"] = min(icdeki_odul), max(icdeki_odul)
        s["n_ic"] = len(icdeki_pay)
        s["bolum_ic"] = len(icdeki_pay) * 3
        s["bolum_toplam"] = sum(len(D[dizin][v]) for v in VARYANT) * 3
        ozet[dizin] = s
    return ozet


def kural2(A):
    """Anlamlilik kurali. Fark, iki varyanttan buyuk olanin tohumlar arasi
    standart sapmasinin iki katindan kucukse FARK YOK (karar 12 ve 39 kural 4)."""
    import itertools
    cikti = {}
    for dizin, s in A.items():
        ciftler = []
        for a, b in itertools.combinations(VARYANT, 2):
            xa, xb = s["varyant"][a], s["varyant"][b]
            fark = abs(xa["pay_ort"] - xb["pay_ort"])
            esik = 2 * max(xa["pay_sap"], xb["pay_sap"])
            ciftler.append((a, b, fark, esik, fark < esik))
        cikti[dizin] = ciftler
    return cikti


def bolum_b():
    """T3 kusurlu ortaminin iz imzasi, iki kosunun kendi gunluklerinden."""
    cikti = {}
    for t in (0, 1):
        yol = os.path.join(KOSU, "kosular_t3_v0", f"limulus_t{t}_gunluk.json")
        g = json.load(open(yol, encoding="utf-8"))["gunluk"]
        o = [r["odul"] for r in g]
        u = [r["ort_bolum_uzunlugu"] for r in g]
        mo, mu = st.mean(o), st.mean(u)
        pay = sum((a - mo) * (b - mu) for a, b in zip(o, u))
        bol = (sum((a - mo) ** 2 for a in o) ** 0.5) * (sum((b - mu) ** 2 for b in u) ** 0.5)
        cikti[t] = dict(n=len(g), adim=g[-1]["adim"],
                        odul_ilk=o[0], odul_son=o[-1],
                        uzunluk_ilk=u[0], uzunluk_son=u[-1], r=pay / bol)
    return cikti


def fig3_guncelle(A):
    """fig3_veri.json'un iki PPO sonda sutununu bes tohumlu olcume cevirir."""
    yol = os.path.join(_B, "fig3_veri.json")
    V = json.load(open(yol, encoding="utf-8"))
    esle = {"irtifa": "kosular_esik_sonda600_s5", "ikisi": "kosular_esik_gamma999_s5"}
    for s in V["sutunlar"]:
        d = esle.get(s["anahtar"])
        if not d:
            continue
        a = A[d]
        s["kaynak"] = (f"9-DIJITAL-IKIZ/ogrenme/k52_degerlendirme.json, "
                       f"dizin {d}, karar 52 Bolum A")
        s["politika_sayisi"] = 20
        s["tohum_basina_varyant"] = 5
        s["bolum_politika_basina"] = 3
        s["bolum_toplam"] = a["bolum_toplam"]
        s["bolum_dagilim_ici"] = a["bolum_ic"]
        s["politika_dagilim_ici"] = a["n_ic"]
        # ⚠️ Sutun bandi DORT VARYANT ORTALAMASININ bandidir, donmus kampanya
        # sutunuyla ayni buyuklugu anmak icin. Tohumlar arasi yayilim ayri
        # alanda tasinir ve makalede Tablo 3'e girer, sutun etiketine girmez.
        ort = [a["varyant"][v]["pay_ort"] for v in VARYANT]
        s["hayatta_kalma_alt"] = round(min(ort), 1)
        s["hayatta_kalma_ust"] = round(max(ort), 1)
        s["tohum_yayilimi_alt"] = round(a["pay_alt"], 1)
        s["tohum_yayilimi_ust"] = round(a["pay_ust"], 1)
        s["azami_irtifa_alt"] = round(min(a["h_azami"]), 1)
        s["azami_irtifa_ust"] = round(max(a["h_azami"]), 1)
        s["yere_carpma"] = f"{a['neden'].get('yere carpma', 0)}/{a['bolum_toplam']}"
        s.pop("bolum_uzunlugu_alt", None)
        s.pop("bolum_uzunlugu_ust", None)
    V["_kural_G"] = (
        "v6'da iki PPO sonda sutunu ELLE YAZILMIS tek tohumlu degerlerden "
        "OLCULMUS bes tohumlu degerlere gecti, kaynak karar 52 Bolum A ve "
        "uretici sayilar_v6.py. Tek tohumlu onceki degerler (%30,1-55,3 ve "
        "%38,8-67,1) karar 52 kural 2 geregi kayitta kalir ve bu dosyada "
        "_v5_tek_tohum alaninda saklanir, hicbir sutunla karistirilmaz. "
        "Klasik kontrolcu sutunu elle yazili kalir, o olcumun cikti dosyasi yoktur.")
    V["_v5_tek_tohum"] = {
        "irtifa": {"bolum_toplam": 12, "hayatta_kalma_alt": 30.1, "hayatta_kalma_ust": 55.3},
        "ikisi": {"bolum_toplam": 12, "hayatta_kalma_alt": 38.8, "hayatta_kalma_ust": 67.1}}
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(V, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"  fig3_veri.json guncellendi: {yol}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fig3", action="store_true")
    a = ap.parse_args()
    D = _yukle()
    A = bolum_a(D)

    print("=== BOLUM A, bes tohumlu tekrar (karar 52) ===")
    h_hepsi, bolum_hepsi, ic_hepsi = [], 0, 0
    for d, s in A.items():
        print(f"\n{s['ad']}   dizin {d}")
        print(f"  degerlendirilen politika 20, dagilim ici {s['n_ic']}"
              f"  (disi: {', '.join(s['disi']) or 'yok'})")
        print(f"  bolum {s['bolum_toplam']} (dagilim ici {s['bolum_ic']})")
        for v in VARYANT:
            x = s["varyant"][v]
            print(f"    {v:<11} n={x['n']}/5  pay %{x['pay_ort']:.1f} +- {x['pay_sap']:.1f}"
                  f"   odul {x['odul_ort']:+.3f} +- {x['odul_sap']:.3f}")
        print(f"  pay bandi  %{s['pay_alt']:.1f}-{s['pay_ust']:.1f}")
        print(f"  odul bandi {s['odul_alt']:+.3f} .. {s['odul_ust']:+.3f}")
        print(f"  azami irtifa {min(s['h_azami']):.1f}-{max(s['h_azami']):.1f} m")
        print(f"  sonlanma {s['neden']}")
        tl = [t for _, _, t in s["tilt"]]
        lim = [t for v, _, t in s["tilt"] if v == "limulus"]
        print(f"  tilt kullanimi tum varyantlar {min(tl):.1f}-{max(tl):.1f} der,"
              f" limulus {min(lim):.1f}-{max(lim):.1f} der")
        print(f"  0,65 kapisini gecen: {s['kapi_gecen'] or 'yok'}")
        h_hepsi += s["h_azami"]
        bolum_hepsi += s["bolum_toplam"]
        ic_hepsi += s["n_ic"]

    print("\n=== KURAL 2, varyant ciftleri ===")
    K = kural2(A)
    hepsi_yok = True
    for dizin, ciftler in K.items():
        print(f"\n{A[dizin]['ad']}")
        for a, b, fark, esik, yok in ciftler:
            print(f"    {a:<11} - {b:<11} fark {fark:5.1f} esik {esik:5.1f}"
                  f"  -> {'FARK YOK' if yok else 'FARK VAR'}")
            hepsi_yok &= yok
        print(f"    en buyuk fark {max(c[2] for c in ciftler):.1f},"
              f" esik araligi {min(c[3] for c in ciftler):.1f}"
              f"-{max(c[3] for c in ciftler):.1f}")
    n = sum(len(c) for c in K.values())
    print(f"\n  --- {n} ciftin {sum(1 for c in K.values() for x in c if x[4])}"
          f" tanesinde FARK YOK ---")

    print(f"\n  --- Bolum A toplami: {bolum_hepsi} degerlendirme bolumu,"
          f" azami irtifa {min(h_hepsi):.4f}-{max(h_hepsi):.4f} m ---")
    print(f"  --- merkez bulgu: 64 (v5) + {bolum_hepsi} = {64 + bolum_hepsi} bolum ---")

    print("\n=== BOLUM B, T3 kusurlu ortami (karar 52) ===")
    for t, b in bolum_b().items():
        print(f"  t{t}  n={b['n']} kayit, {b['adim']} adim")
        print(f"      odul {b['odul_ilk']:+.3f} -> {b['odul_son']:+.3f}"
              f"   bolum uzunlugu {b['uzunluk_ilk']:.0f} -> {b['uzunluk_son']:.0f}"
              f"   r = {b['r']:+.3f}")

    if a.fig3:
        print("\n=== fig3_veri.json ===")
        fig3_guncelle(A)


if __name__ == "__main__":
    main()
