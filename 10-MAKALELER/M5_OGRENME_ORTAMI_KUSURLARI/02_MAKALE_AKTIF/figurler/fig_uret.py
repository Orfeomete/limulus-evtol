#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M5 FIGURLERI — uc figur, iki dil, tek uretec.

⚠️ BU BETIK 10.08.2026'DA YAZILDI ve iki eksigi kapatiyor.

  1. SEKIL 1 ve SEKIL 2'nin URETECI PAKETTE YOKTU. Yalniz `fig3_uret.py`
     saklanmisti. M1 ve M2 paketlerinde ayni eksik bulundu ve ayni gun
     kapatildi. Danisman geridonusunun L listesi ("kod: Missing") bunu
     kapsiyor. `fig3_uret.py` bu betige tasindi ve arsive alindi.

  2. SEKIL 1 ILE TABLO 1 AYNI ALT KUMEYI KULLANMIYORDU. Tablo 1'in bir
     milyon adimlik sutunu, bolum sayaci tek yonlu kalan SEKIZ tilt
     kosusunu kapsiyor ve bandi 596-793 veriyor. Onceki Sekil 1 ise ayni
     sutunda YIRMI kosunun tamamini cizip "n=20" yaziyordu ve kutusu
     60 ile 3100 arasina yayiliyordu, cunku sayaci kirpilmis yedi kosu
     1838-4431 bandinda sahte deger tasiyor. Yani figur ile tablo ayni
     seyi ayni adla anmiyordu. ⚠️ BU, MAKALENIN KENDI KUSUR SINIFINDAN
     BIR KUSURDUR, hicbir sayi yanlis hesaplanmiyor, olculen sey yanlis.
     Figur artik Tablo 1 ile AYNI alt kumeyi kullanir ve n degerlerini
     sutun etiketine yazar.

⚠️ SEKIL 1 VE 2 SAYI URETMEZ, KOSU GUNLUKLERINDEN OKUR. Butun degerler
`9-DIJITAL-IKIZ/ogrenme/kosular*/` altindaki `*_gunluk.json` dosyalarindan
gelir. SEKIL 3 ise `fig3_veri.json` dosyasindan okur, cunku azami irtifa ile
hayatta kalma payini ureten degerlendirme cagrisinin cikti dosyasi
saklanmamistir. O dosya her degeri kaynak satiriyla birlikte tasir.

Kosum
    cd 10-MAKALELER/M5_.../02_MAKALE_AKTIF/figurler
    python3 fig_uret.py              # her iki dil
    python3 fig_uret.py --dil en     # yalniz Ingilizce
Cikti
    fig1_episode_length.pdf/.png     fig1_episode_length_TR.pdf/.png
    fig2_level_progress.pdf/.png     fig2_level_progress_TR.pdf/.png
    fig3_configurations.pdf/.png     fig3_configurations_TR.pdf/.png
"""
import argparse
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_B = os.path.dirname(os.path.abspath(__file__))
_KOK = os.path.abspath(os.path.join(_B, "..", "..", "..", ".."))
KOSU = os.path.join(_KOK, "9-DIJITAL-IKIZ", "ogrenme")

# --- ev stili, fig3_uret.py'den devralindi ---
MAVI_KOYU, MAVI_ORTA, MAVI_ACIK = "#1B4C8C", "#2A78D6", "#7FB3EC"
VURGU, IZGARA, YESIL = "#B04A2E", "#E2E1DA", "#3E7C4A"
MET, MET_SOLUK = "#222222", "#666666"

plt.rcParams.update({
    # fonttype 42 ZORUNLU, bkz. 4-KARARLAR/29
    "pdf.fonttype": 42, "svg.fonttype": "none",
    "font.family": "DejaVu Sans", "font.size": 11.5,
    "axes.edgecolor": "#9A9A9A", "axes.linewidth": 0.9,
    "figure.dpi": 110,
})

_DIL = "en"


def sayi(x, basamak=0):
    s = f"{x:.{basamak}f}"
    return s if _DIL == "en" else s.replace(".", ",")


METIN = {
    "en": dict(
        ek="",
        f1y="Mean episode length (steps)",
        f1ad=("Pilot\n400k steps", "Corrected\n1M steps", "Long budget\n3M steps"),
        f1n="n={n} runs",
        f1bas="Mean episode length per run, by campaign",
        f2y="Runs (highest curriculum level reached)",
        f2sev="Level {s}",
        f2bas="Highest curriculum level reached per run",
        f3ad=("Frozen\ncampaign", "Altitude\ncorrection", "Both\ncorrections",
              "Classical\ncontroller"),
        f3sol="Episode completed (%)",
        f3sag="Peak altitude reached (m)",
        f3solbas="Episode completion rate by configuration",
        f3sagbas="Peak altitude by configuration",
        f3kapi="gate floor {v}%",
        f3bas="start {v} m", f3hedef="target {v} m",
        f3n="{n} ep."),
    "tr": dict(
        ek="_TR",
        f1y="Ortalama bölüm uzunluğu (adım)",
        f1ad=("Pilot\n400k adım", "Düzeltme sonrası\n1M adım",
              "Uzun bütçe\n3M adım"),
        f1n="n={n} koşu",
        f1bas="Koşu başına ortalama bölüm uzunluğu, kampanyalara göre",
        f2y="Koşu (ulaşılan en yüksek müfredat seviyesi)",
        f2sev="Seviye {s}",
        f2bas="Koşu başına ulaşılan en yüksek müfredat seviyesi",
        f3ad=("Donmuş\nkampanya", "İrtifa\ndüzeltmesi", "İki düzeltme\nbirlikte",
              "Klasik\nkontrolcü"),
        f3sol="Bölümü tamamlama (%)",
        f3sag="Ulaşılan azami irtifa (m)",
        f3solbas="Yapılandırmalara göre bölüm tamamlama oranı",
        f3sagbas="Yapılandırmalara göre azami irtifa",
        f3kapi="kapı payı %{v}",
        f3bas="başlangıç {v} m", f3hedef="hedef {v} m",
        f3n="{n} bölüm"),
}


def _tik(x):
    """Eksen tiki, gereksiz sifirlar atilir ve ondalik ayirici virgul olur."""
    t = f"{x:.2f}".rstrip("0").rstrip(".")
    if t in ("", "-", "-0"):
        t = "0"
    return t.replace(".", ",")


def _eksen_bicimi(ax, eksen):
    """Turkce ciktilarda SAYISAL eksenleri virgulle yazar.

    ⚠️ `eksen` ZORUNLU. M1'de ayni yardimci once her iki eksene uygulanmis ve
    KATEGORIK eksendeki etiketleri sayilarla ezmisti. Bu betikteki UC figurun
    da x ekseni kategoriktir, dolayisiyla hepsinde yalniz "y" verilir.
    """
    if _DIL != "tr":
        return
    from matplotlib.ticker import FuncFormatter
    f = FuncFormatter(lambda x, _p: _tik(x))
    if "x" in eksen:
        ax.xaxis.set_major_formatter(f)
    if "y" in eksen:
        ax.yaxis.set_major_formatter(f)


def _kaydet(fig, ad):
    fig.tight_layout()
    for uz in ("pdf", "png"):
        fig.savefig(os.path.join(_B, f"{ad}{METIN[_DIL]['ek']}.{uz}"),
                    bbox_inches="tight", dpi=300 if uz == "png" else None)
    plt.close(fig)


def _oku(dizin):
    """Bir kampanyanin butun kosu gunluklerini okur."""
    ys = sorted(glob.glob(os.path.join(KOSU, dizin, "*_gunluk.json")))
    if not ys:
        sys.exit(f"kosu gunlugu bulunamadi: {dizin}")
    cikti = []
    for y in ys:
        d = json.load(open(y, encoding="utf-8"))
        g = d["gunluk"]
        varyant = os.path.basename(y).split("_t")[0]
        n = [k["n_bolum"] for k in g]
        monoton = all(b >= a for a, b in zip(n, n[1:]))
        if "ort_bolum_uzunlugu" in g[-1]:
            ort = g[-1]["ort_bolum_uzunlugu"]
        else:                                    # pilot gunlugunde alan yok
            ort = g[-1]["adim"] / g[-1]["n_bolum"]
        cikti.append(dict(dosya=os.path.basename(y), varyant=varyant,
                          ort_bolum=ort, monoton=monoton,
                          azami_seviye=max(k["seviye"] for k in g)))
    return cikti


def _f1_kume(kayitlar, dizin):
    """⚠️ TABLO 1 ILE AYNI ALT KUME. Bir milyon adimlik kampanyada bolum
    sayaci ara kontrol noktasi mekanizmasi yuzunden kirpilmisti, dolayisiyla
    metrik yalniz sayaci tek yonlu kalan tilt kosularinda gecerlidir."""
    if dizin == "kosular_v2":
        return [k for k in kayitlar
                if k["monoton"] and k["varyant"] != "liftcruise"]
    return kayitlar


def fig1(t):
    veri, etiket = [], []
    for ad, dizin in zip(t["f1ad"], ("kosular", "kosular_v2", "kosular_uzun")):
        kume = _f1_kume(_oku(dizin), dizin)
        veri.append([k["ort_bolum"] for k in kume])
        etiket.append(f"{ad}\n{t['f1n'].format(n=len(kume))}")
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    kutu = ax.boxplot(veri, widths=0.5, patch_artist=True, showfliers=True,
                      medianprops=dict(color=MAVI_KOYU, linewidth=2.0),
                      flierprops=dict(marker="o", markersize=4,
                                      markerfacecolor=MAVI_ORTA,
                                      markeredgecolor="white"))
    for kutucuk in kutu["boxes"]:
        kutucuk.set(facecolor="#CDE2FB", edgecolor=MAVI_ORTA, linewidth=1.2)
    for anah in ("whiskers", "caps"):
        for c in kutu[anah]:
            c.set(color=MAVI_ORTA, linewidth=1.2)
    for i, d in enumerate(veri, start=1):
        ax.text(i, max(d) + 0.035 * max(max(v) for v in veri),
                f"{sayi(min(d))}–{sayi(max(d))}", ha="center",
                fontsize=10.5, weight="semibold", color=MET)
    ax.set_xticklabels(etiket, fontsize=10.0)
    ax.set_ylabel(t["f1y"])
    ax.set_title(t["f1bas"], fontsize=12.5, weight="semibold", color=MET, pad=9)
    ax.set_axisbelow(True)
    _eksen_bicimi(ax, "y")   # ⚠️ x KATEGORIK
    ax.yaxis.grid(True, color=IZGARA, linewidth=0.9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    _kaydet(fig, "fig1_episode_length")
    return {e: (min(d), max(d), len(d)) for e, d in zip(("pilot", "1M", "3M"), veri)}


def fig2(t):
    kampanya = [_oku(d) for d in ("kosular", "kosular_v2", "kosular_uzun")]
    seviyeler = sorted({k["azami_seviye"] for c in kampanya for k in c})
    renk = dict(zip(seviyeler, (MAVI_ACIK, MAVI_ORTA, MAVI_KOYU, VURGU)))
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    x = np.arange(3)
    alt = np.zeros(3)
    for s in seviyeler:
        h = np.array([sum(1 for k in c if k["azami_seviye"] == s)
                      for c in kampanya], float)
        ax.bar(x, h, 0.5, bottom=alt, color=renk[s], edgecolor="white",
               linewidth=1.0, label=t["f2sev"].format(s=s), zorder=3)
        for xi, hi, ai in zip(x, h, alt):
            if hi > 0:
                ax.text(xi, ai + hi / 2, f"{int(hi)}", ha="center", va="center",
                        color="white" if s != min(seviyeler) else MET,
                        fontsize=11, weight="semibold", zorder=4)
        alt += h
    ax.set_xticks(x)
    ax.set_xticklabels([a.replace("\n", " ") for a in t["f1ad"]], fontsize=10.0)
    ax.set_ylabel(t["f2y"])
    ax.set_title(t["f2bas"], fontsize=12.5, weight="semibold", color=MET, pad=9)
    ax.set_ylim(0, max(alt) * 1.14)
    ax.legend(frameon=False, fontsize=10, ncol=len(seviyeler),
              loc="upper center", bbox_to_anchor=(0.5, 1.0))
    ax.set_axisbelow(True)
    _eksen_bicimi(ax, "y")   # ⚠️ x KATEGORIK
    ax.yaxis.grid(True, color=IZGARA, linewidth=0.9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    _kaydet(fig, "fig2_level_progress")
    return [{k["dosya"]: k["azami_seviye"] for k in c if k["azami_seviye"] > 2}
            for c in kampanya]


def fig3(t):
    with open(os.path.join(_B, "fig3_veri.json"), encoding="utf-8") as f:
        V = json.load(f)
    S = V["sutunlar"]
    K = V["olcum_kosullari"]
    renk = [MAVI_ACIK, MAVI_ORTA, MAVI_KOYU, VURGU]
    X_SOL, X_CIZGI, X_ETIKET, X_SAG = -0.6, 3.36, 3.44, 4.55
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.6, 4.6))
    x = np.arange(4)

    def sutunlar(ax, alt_a, ust_a, bicim, yuk, ozel=None):
        for i in range(4):
            alt, ust = alt_a[i], ust_a[i]
            ax.bar(i, alt, 0.56, color=renk[i], zorder=3)
            if ust - alt > 1e-6:
                ax.bar(i, ust - alt, 0.56, bottom=alt, color=renk[i],
                       alpha=0.34, edgecolor="white", linewidth=1.4, zorder=3)
            ax.text(i, ust + (ozel or {}).get(i, yuk), bicim(alt, ust),
                    ha="center", fontsize=11.5, weight="semibold", color=MET,
                    zorder=4)

    def cizgi(ax, y, metin, renk_):
        ax.hlines(y, X_SOL + 0.05, X_CIZGI, color=renk_, ls=(0, (5, 3)),
                  lw=1.3, zorder=2)
        ax.text(X_ETIKET, y, metin, ha="left", va="center", fontsize=10.2,
                color=renk_, zorder=4)

    # ⚠️ Sutun etiketi bolum sayisini tasir, boylece n=1 tohumlu sutunlar ile
    # bes tohumlu sutun ayni yerde ayirt edilir. Danisman geridonusu C-01.
    ad = [f"{a}\n{t['f3n'].format(n=s['bolum_toplam'])}"
          for a, s in zip(t["f3ad"], S)]

    def bicimle(ax):
        ax.set_xticks(x)
        ax.set_xticklabels(ad, fontsize=10.0)
        ax.set_xlim(X_SOL, X_SAG)
        ax.set_axisbelow(True)
        _eksen_bicimi(ax, "y")   # ⚠️ x KATEGORIK
        ax.yaxis.grid(True, color=IZGARA, linewidth=0.9)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    pay_alt = [s["hayatta_kalma_alt"] for s in S]
    pay_ust = [s["hayatta_kalma_ust"] for s in S]
    sutunlar(a1, pay_alt, pay_ust,
             lambda a, u: (f"%{sayi(u)}" if _DIL == "tr" else f"{sayi(u)}%")
             if u - a < 0.5 else
             ((f"%{sayi(a)}–{sayi(u)}" if _DIL == "tr"
               else f"{sayi(a)}–{sayi(u)}%")), 2.6, ozel={0: 6.2})
    cizgi(a1, K["kapi_payi_yuzde"],
          t["f3kapi"].format(v=sayi(K["kapi_payi_yuzde"])), MET_SOLUK)
    bicimle(a1)
    a1.set_ylabel(t["f3sol"])
    a1.set_ylim(0, 118)
    a1.set_title(t["f3solbas"], fontsize=12.5, weight="semibold", color=MET,
                 pad=9)

    irt_alt = [s["azami_irtifa_alt"] for s in S]
    irt_ust = [s["azami_irtifa_ust"] for s in S]
    sutunlar(a2, irt_alt, irt_ust,
             lambda a, u: sayi(u, 0) if u - a < 0.5
             else f"{sayi(a, 0)}–{sayi(u, 0)}", 9, ozel={3: 26.0})
    cizgi(a2, K["baslangic_irtifa_m"],
          t["f3bas"].format(v=sayi(K["baslangic_irtifa_m"])), MET_SOLUK)
    cizgi(a2, K["hedef_irtifa_m"],
          t["f3hedef"].format(v=sayi(K["hedef_irtifa_m"])), YESIL)
    bicimle(a2)
    a2.set_ylabel(t["f3sag"])
    a2.set_ylim(0, 350)
    a2.set_title(t["f3sagbas"], fontsize=12.5, weight="semibold", color=MET,
                 pad=9)
    _kaydet(fig, "fig3_configurations")
    return [(s["anahtar"], s["bolum_toplam"], s["hayatta_kalma_alt"],
             s["hayatta_kalma_ust"]) for s in S]


def main():
    global _DIL
    ap = argparse.ArgumentParser()
    ap.add_argument("--dil", choices=("en", "tr", "ikisi"), default="ikisi")
    a = ap.parse_args()
    for d in (("en", "tr") if a.dil == "ikisi" else (a.dil,)):
        _DIL = d
        t = METIN[d]
        b1 = fig1(t)
        b2 = fig2(t)
        b3 = fig3(t)
        print(f"[{d}] uc figur uretildi, ek '{t['ek'] or '(yok)'}'")
        if d == "en":
            print("  --- SEKIL 1, Tablo 1 ile ayni olmali ---")
            for k, (lo, hi, n) in b1.items():
                print(f"    {k:<6} n={n:<3} bant {lo:.0f}-{hi:.0f}")
            print("  --- SEKIL 2 ---")
            print(f"    seviye 2 ustu kosular {b2}")
            print("  --- SEKIL 3, Tablo 2 ile ayni olmali ---")
            for anah, n, lo, hi in b3:
                print(f"    {anah:<8} {n:>2} bolum  hayatta kalma "
                      f"{lo:.1f}-{hi:.1f}%")


if __name__ == "__main__":
    main()
