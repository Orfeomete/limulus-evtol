#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M1 v8 SAYI TURETICI — donmus kampanya ile genis kesif kampanyasini AYNI
BETIKLE, iki kampanyanin kendi kosu gunluklerinden okur.

⚠️ BU BETIK 14.08.2026'DA YAZILDI ve bir hatayi kapatiyor. Karar 53 SONUCLAR
bolumu iki kampanyayi karsilastirirken donmus kampanyanin sayisini GUNLUKTEN
degil METINDEN almisti. "On dokuz kosu seviye 2'de platoya oturuyor" ifadesi
"on dokuz kosu gecis gorevine ulasamiyor" diye okundu, oysa plato gecis
gorevinin USTUNDE oturuyor. Bu betik her iki kampanyayi da ayni koddan gecirir,
dolayisiyla ayni hata bir daha yapilamaz.

Kaynaklar
    9-DIJITAL-IKIZ/ogrenme/kosular_uzun/         (karar 38, log_std0 = -1,5)
    9-DIJITAL-IKIZ/ogrenme/kosular_genis_kesif/  (karar 53, log_std0 = -0,5)
    9-DIJITAL-IKIZ/ogrenme/k53_degerlendirme.json

Kosum
    cd 10-MAKALELER/M1_.../02_MAKALE_AKTIF/figurler
    python3 kampanya_karsilastirma.py
"""
import glob
import json
import os
import statistics as st

_B = os.path.dirname(os.path.abspath(__file__))
_KOK = os.path.abspath(os.path.join(_B, "..", "..", "..", ".."))
KOSU = os.path.join(_KOK, "9-DIJITAL-IKIZ", "ogrenme")

VARYANT = ("limulus", "ikili", "senkron", "liftcruise")
KAMPANYA = (("donmus", "kosular_uzun", -1.5),
            ("genis", "kosular_genis_kesif", -0.5))
SEVIYE_GOREV = {0: "hover", 1: "dikey", 2: "gecis", 3: "cruise",
                4: "gust_gecis", 5: "motor_arizasi"}


def _kosu(dizin, varyant=None, tohum=None):
    kalip = f"{varyant or '*'}_t{tohum if tohum is not None else '*'}_gunluk.json"
    return sorted(glob.glob(os.path.join(KOSU, dizin, kalip)))


def _oku(yol):
    g = json.load(open(yol, encoding="utf-8"))
    gl = g["gunluk"]
    sev = max(r["seviye"] for r in gl)
    varis = min([r["adim"] for r in gl if r["seviye"] >= 2] or [None])
    son = gl[-1]["adim"]
    odul = st.mean([r["odul"] for r in gl if r["adim"] > son - 100000])
    return dict(ad=os.path.basename(yol).replace("_gunluk.json", ""),
                ayar=g["ayar"], kayit=len(gl), adim=son,
                seviye=sev, gorev=SEVIYE_GOREV.get(sev, f"sev{sev}"),
                sev2_varis=varis, son_odul=odul,
                sure=gl[-1]["sure"], hiz=son / gl[-1]["sure"])


def kampanya(dizin):
    ks = [_oku(y) for y in _kosu(dizin)]
    d = {}
    for k in ks:
        d.setdefault(k["ad"].split("_t")[0], []).append(k)
    return ks, d


def maliyet(ks):
    """⚠️ Gunlukteki `sure` alani DEVAM ETTIRILEN kosularda yalniz son dilimi
    sayar, dolayisiyla bir maliyet olcusu DEGILDIR. Kesintisiz tamamlanan
    kosular, turetilen hizin makul ust sinirin (600 adim/s) altinda kalmasiyla
    ayirt edilir, cunku kesinti yiyen bir kosuda adim/sure orani sisirilir."""
    kes = [k for k in ks if k["hiz"] < 600]
    if not kes:
        return None
    return dict(n=len(kes), n_toplam=len(ks),
                sa_alt=min(k["sure"] for k in kes) / 3600,
                sa_ust=max(k["sure"] for k in kes) / 3600,
                hiz_alt=min(k["hiz"] for k in kes),
                hiz_ust=max(k["hiz"] for k in kes),
                hiz_ort=st.mean([k["hiz"] for k in kes]))


def main():
    ozet = {}
    for ad, dizin, log_std0 in KAMPANYA:
        ks, d = kampanya(dizin)
        print(f"\n=== {dizin}  (log_std0 = {log_std0})  {len(ks)} kosu ===")
        gercek = {k["ayar"].get("log_std0") for k in ks}
        print(f"  gunlukten okunan log_std0 {gercek}"
              f"   mufredat_ince {({k['ayar'].get('mufredat_ince') for k in ks})}"
              f"   gamma {({k['ayar'].get('gamma') for k in ks})}")
        sev = {}
        for k in ks:
            sev[k["gorev"]] = sev.get(k["gorev"], 0) + 1
        print(f"  ULASILAN GOREV (kural 1'in birincil metrigi): {sev}")
        ileri = [k["ad"] for k in ks if k["seviye"] > 2]
        print(f"  seviye 2'nin otesine gecen: {ileri or 'yok'}")
        v = [k["sev2_varis"] for k in ks]
        print(f"  seviye 2'ye varis  ortanca {st.median(v):.0f}"
              f"  ort {st.mean(v):.0f} +- {st.stdev(v):.0f}"
              f"  bant {min(v)}-{max(v)}")
        for var in VARYANT:
            o = [k["son_odul"] for k in d[var]]
            print(f"    {var:<11} son odul {st.mean(o):+.3f} +- {st.stdev(o):.3f}")
        bant = [st.mean([k["son_odul"] for k in d[var]]) for var in VARYANT]
        print(f"  son odul, varyant ortalamalari bandi"
              f" {min(bant):+.3f} ile {max(bant):+.3f}")
        m = maliyet(ks)
        if m:
            print(f"  MALIYET, kesintisiz {m['n']}/{m['n_toplam']} kosudan"
                  f"  {m['sa_alt']:.2f}-{m['sa_ust']:.2f} sa/kosu,"
                  f"  {m['hiz_alt']:.0f}-{m['hiz_ust']:.0f} adim/s"
                  f"  (ort {m['hiz_ort']:.0f})")
        else:
            print("  MALIYET OLCULEMEZ, kosularin tamami devam ettirilmis,"
                  " `sure` alani yalniz son dilimi sayiyor")
        print(f"  toplam cevre adimi {sum(k['adim'] for k in ks)}")
        ozet[ad] = dict(sev=sev, varis=v, ileri=ileri)

    print("\n=== KARSILASTIRMA ===")
    a, b = ozet["donmus"], ozet["genis"]
    print(f"  ulasilan gorev dagilimi  donmus {a['sev']}  genis {b['sev']}"
          f"  -> {'AYNI' if a['sev'] == b['sev'] else 'FARKLI'}")
    print(f"  ileri giden kosu         donmus {a['ileri']}  genis {b['ileri']}"
          f"  -> {'AYNI TOHUM' if a['ileri'] == b['ileri'] else 'FARKLI'}")
    fark = st.mean(a["varis"]) - st.mean(b["varis"])
    esik = 2 * max(st.stdev(a["varis"]), st.stdev(b["varis"]))
    print(f"  seviye 2 varis farki     {fark:.0f} adim,  iki sapma esigi {esik:.0f}"
          f"  -> {'FARK YOK' if abs(fark) < esik else 'FARK VAR'}")
    print(f"  ortanca varis farki      "
          f"{st.median(a['varis']) - st.median(b['varis']):.0f} adim")

    print("\n=== KURAL 2, genis kesif kampanyasi degerlendirmesi ===")
    D = json.load(open(os.path.join(KOSU, "k53_degerlendirme.json"), encoding="utf-8"))
    import itertools
    m = {}
    for v in VARYANT:
        pay = [k["pay"] * 100 for k in D[v]]
        m[v] = (st.mean(pay), st.stdev(pay))
        print(f"  {v:<11} hayatta kalma %{m[v][0]:.1f} +- {m[v][1]:.1f}")
    for x, y in itertools.combinations(VARYANT, 2):
        f = abs(m[x][0] - m[y][0])
        e = 2 * max(m[x][1], m[y][1])
        print(f"    {x:<11} - {y:<11} fark {f:4.1f} esik {e:4.1f}"
              f" -> {'FARK YOK' if f < e else 'FARK VAR'}")
    neden, h, tilt, kapi = {}, [], [], 0
    for v in VARYANT:
        for k in D[v]:
            for n in k["nedenler"]:
                neden[n] = neden.get(n, 0) + 1
            h.append(k["h_azami"])
            tilt.append(k["tilt_der"])
            kapi += 1 if k["kapi"] else 0
    print(f"  sonlanma {neden}   0,65 kapisini gecen {kapi}/20")
    print(f"  azami irtifa {min(h):.4f}-{max(h):.4f} m")
    print(f"  tilt kullanimi {sorted(round(t, 1) for t in tilt)}")


if __name__ == "__main__":
    main()
