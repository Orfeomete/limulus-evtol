#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M1 FIGURLERI — uzun butceli kampanyanin ogrenme egrileri ve tohum dagilimi.

⚠️ BU BETIK 10.08.2026'DA YAZILDI ve bir eksigi kapatiyor. M1'in iki figuru
onceki surumlerde uretilmis fakat URETEC BETIK PAKETTE SAKLANMAMISTI, yani
figurler yeniden uretilemiyordu. M5 ve M6 paketlerinde uretec var, M1'de
yoktu. Danisman geridonusunun yeniden uretilebilirlik kalemi bunu da
kapsiyor.

⚠️ IKINCI DEGISIKLIK, BANT ARTIK MIN-MAX DEGIL STANDART SAPMA. Onceki figur
altyazisi "min-max band" diyordu. Bes tohumla min-max, tek bir aykiri tohumun
bandin tamamini belirlemesine izin verir ve dagilim hakkinda yaniltici bir
genislik gosterir. Standart sapma bandi istatistiksel olarak daha savunulabilir
ve tezin kendi figuru (`9-DIJITAL-IKIZ/figurler.py`) zaten oyle yapiyor, yani
bu degisiklik ayni zamanda tez ile makale arasindaki bir tutarsizligi da
kapatiyor.

⚠️ SAYI URETMEZ, VERIDEN OKUR. Butun degerler kosu gunluklerinden gelir,
hicbiri elle yazilmaz. Kural G.

Kosum
    cd 10-MAKALELER/M1_.../02_MAKALE_AKTIF/figurler && python3 fig_uret.py
Cikti
    fig1_learning_curves.pdf ve .png   (vektorel + 300 dpi)
    fig2_final_reward_seeds.pdf ve .png
"""
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42        # ZORUNLU, gomulu metin
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt
import numpy as np

_BURASI = os.path.dirname(os.path.abspath(__file__))
_KOK = os.path.abspath(os.path.join(_BURASI, "..", "..", "..", ".."))
KOSU = os.path.join(_KOK, "9-DIJITAL-IKIZ", "ogrenme", "kosular_uzun")

# ⚠️ IKI DIL (10.08.2026). Danisman geridonusleri M2, M5 ve M6 figurlerinin
# Turkce metinde Turkce etiketlenmesini istedi, M1 portfoyde son kalan paketti.
# Ingilizce ciktilar eski adlarini korur, cunku gonderim metni Ingilizcedir,
# Turkce ciktilar `_TR` ekiyle uretilir. Sayilar iki dilde AYNIDIR, yalniz
# etiket ve ondalik ayirici degisir.
_DIL = "en"

VAR_AD_DIL = {
    "en": {"limulus": "LIMULUS (full)", "ikili": "Paired tilt",
           "senkron": "Synchronous tilt", "liftcruise": "Lift-cruise"},
    # ⚠️ Adlar M1_TR metninin KENDI kullanimindan alindi, tezin figur
    # betiginden degil. Metin "Lift-cruise" yaziyor (dokuz kez), tez ise
    # "Lift + cruise". Ayni belgede iki ad kullanmak okuyucuya iki sey
    # gostermek olur, dolayisiyla figur metne uyar.
    "tr": {"limulus": "LIMULUS (tam)", "ikili": "İkili tilt",
           "senkron": "Senkron tilt", "liftcruise": "Lift-cruise"},
}
METIN = {
    "en": dict(ek="",
               f1x="Environment steps (millions)",
               f1y="Normalized episode reward",
               f1b="Training reward, mean of five seeds with $\\pm 1$ SD band",
               f1esik="curriculum threshold {v}",
               f2y="Final reward, mean of last 100k steps",
               f2b="Final reward per seed, with variant mean and $\\pm 1$ SD"),
    "tr": dict(ek="_TR",
               f1x="Çevre adımı (milyon)",
               f1y="Normalize bölüm ödülü",
               f1b="Eğitim ödülü, beş tohumun ortalaması ve $\\pm 1$ SS bandı",
               f1esik="müfredat eşiği {v}",
               f2y="Son ödül, son 100 bin adımın ortalaması",
               f2b="Tohum bazında son ödül, varyant ortalaması ve $\\pm 1$ SS"),
}


def T(k):
    return METIN[_DIL][k]


def AD(v):
    return VAR_AD_DIL[_DIL][v]


def sayi(x, basamak=2):
    """⚠️ Turkce ondalik ayirici VIRGUL. Eksen etiketlerine de uygulanir,
    cunku gövde metni virgul kullanirken eksenin nokta kullanmasi ayni
    belgede iki ayri yazim demek olur."""
    s = f"{x:.{basamak}f}".rstrip("0").rstrip(".")
    if s in ("", "-"):
        s = "0"
    return s if _DIL == "en" else s.replace(".", ",")


def _eksen_bicimi(ax, eksen="xy"):
    """Turkce ciktilarda eksen sayilarini virgulle yazar.

    ⚠️ `eksen` parametresi ZORUNLU oldu. Ilk surumde fonksiyon her iki eksene
    de bicimleyici koyuyordu ve Sekil 2'nin KATEGORIK x eksenindeki varyant
    adlarini 0, 1, 2, 3 sayilariyla eziyordu. Kusur gozle dogrulamada
    yakalandi. Kategorik eksene bicimleyici konmaz.
    """
    if _DIL != "tr":
        return
    from matplotlib.ticker import FuncFormatter
    f = FuncFormatter(lambda x, _p: sayi(x, 2))
    if "x" in eksen:
        ax.xaxis.set_major_formatter(f)
    if "y" in eksen:
        ax.yaxis.set_major_formatter(f)
VAR_RENK = {"limulus": "#1f4e79", "ikili": "#2e8b57",
            "senkron": "#b8860b", "liftcruise": "#8b3a3a"}
SIRA = ("limulus", "ikili", "senkron", "liftcruise")
ESIK = 0.65                      # mufredat esigi, dondurulmus


def oku():
    """Her varyant icin tohum listesi. Gunlukten okur, sayi uydurmaz."""
    d = {}
    for y in sorted(glob.glob(os.path.join(KOSU, "*_gunluk.json"))):
        ad = os.path.basename(y).split("_t")[0]
        with open(y, encoding="utf-8") as f:
            d.setdefault(ad, []).append(json.load(f)["gunluk"])
    if not d:
        sys.exit(f"kosu gunlugu bulunamadi: {KOSU}")
    return d


def fig1(veri):
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    n_kosu = 0
    for v in SIRA:
        if v not in veri:
            continue
        ks = veri[v]
        n_kosu += len(ks)
        n = min(len(k) for k in ks)
        adim = np.array([k["adim"] for k in ks[0][:n]], float)
        M = np.array([[k["odul"] for k in kk[:n]] for kk in ks], float)
        M = np.where(np.isfinite(M), M, np.nan)
        ort = np.nanmean(M, axis=0)
        sd = np.nanstd(M, axis=0, ddof=1) if len(ks) > 1 else np.zeros_like(ort)
        # yumusatma, yalniz GORSEL, sayilar tabloya buradan gitmiyor
        w = 25
        cek = np.ones(w) / w
        ort_s = np.convolve(ort, cek, mode="valid")
        sd_s = np.convolve(sd, cek, mode="valid")
        ad_s = adim[w - 1:]
        ax.fill_between(ad_s / 1e6, ort_s - sd_s, ort_s + sd_s,
                        color=VAR_RENK[v], alpha=0.16, linewidth=0)
        ax.plot(ad_s / 1e6, ort_s, lw=1.9, color=VAR_RENK[v],
                label=f"{AD(v)} (n={len(ks)})")
    ax.axhline(ESIK, color="#7a7a7a", ls="--", lw=1.1)
    ax.text(ax.get_xlim()[1] * 0.99, ESIK + 0.015,
            T("f1esik").format(v=sayi(ESIK)), ha="right", fontsize=8,
            color="#7a7a7a")
    ax.set_xlabel(T("f1x"))
    ax.set_ylabel(T("f1y"))
    ax.set_title(T("f1b"), fontsize=10.5)
    ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    ax.grid(alpha=0.18, lw=0.6)
    _eksen_bicimi(ax)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    for u in ("pdf", "png"):
        fig.savefig(os.path.join(_BURASI, f"fig1_learning_curves{T(chr(101)+chr(107))}.{u}"),
                    dpi=300 if u == "png" else None, bbox_inches="tight")
    plt.close(fig)
    return n_kosu


def fig2(veri):
    """Son odul, tohum basina. Son 100 bin adimin ortalamasi."""
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    for i, v in enumerate(SIRA):
        if v not in veri:
            continue
        son = []
        for kk in veri[v]:
            adim = np.array([k["adim"] for k in kk], float)
            odul = np.array([k["odul"] for k in kk], float)
            m = adim >= (adim[-1] - 100_000)
            son.append(float(np.nanmean(odul[m])))
        x = np.full(len(son), i, float) + np.linspace(-0.13, 0.13, len(son))
        ax.scatter(x, son, s=34, color=VAR_RENK[v], zorder=3,
                   edgecolor="white", linewidth=0.7)
        ort = float(np.mean(son))
        sd = float(np.std(son, ddof=1)) if len(son) > 1 else 0.0
        ax.plot([i - 0.24, i + 0.24], [ort, ort], color=VAR_RENK[v], lw=2.2)
        ax.errorbar(i, ort, yerr=sd, color=VAR_RENK[v], capsize=4,
                    lw=1.2, zorder=2)
    ax.set_xticks(range(len(SIRA)))
    ax.set_xticklabels([AD(v) for v in SIRA], fontsize=9)
    ax.set_ylabel(T("f2y"))
    ax.set_title(T("f2b"), fontsize=10.5)
    ax.axhline(0.0, color="#bbbbbb", lw=0.8)
    ax.grid(axis="y", alpha=0.18, lw=0.6)
    _eksen_bicimi(ax, "y")   # ⚠️ x KATEGORIK, varyant adlari duruyor
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    for u in ("pdf", "png"):
        fig.savefig(os.path.join(_BURASI, f"fig2_final_reward_seeds{T(chr(101)+chr(107))}.{u}"),
                    dpi=300 if u == "png" else None, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# SEKIL 3 (14.08.2026'da eklendi). Iki kampanyanin karsilastirmasi.
#
# ⚠️ BU FIGUR BIR HATANIN URUNUDUR. Karar 53'un SONUCLAR bolumu iki kampanyayi
# karsilastirirken donmus kampanyanin sayilarini gunlukten degil METINDEN aldi
# ve "seviye 2'de plato" ifadesini "gecis gorevine ulasamadi" diye okudu. Bu
# figur iki kampanyayi da ayni koddan gecirir, dolayisiyla ayni hata bir daha
# yapilamaz. Sag panel iki kampanyanin ULASILAN SEVIYE dagiliminin BIREBIR AYNI
# oldugunu, sol panel ise tek olculen farkin VARIS ZAMANI oldugunu gosterir.
# ---------------------------------------------------------------------------
KOSU_GENIS = os.path.join(_KOK, "9-DIJITAL-IKIZ", "ogrenme", "kosular_genis_kesif")
KAMPANYA_RENK = ("#8b3a3a", "#1f4e79")

METIN["en"].update(
    f3ad=("Long budget\nlog sd0 = -1.5", "Wide exploration\nlog sd0 = -0.5"),
    f3sol="Steps to reach the transition task (thousands)",
    f3sag="Runs (highest curriculum level reached)",
    f3solb="Arrival at the transition task",
    f3sagb="Highest curriculum level reached",
    f3sev="Level {s}",
    f3ortanca="median {v}k")
METIN["tr"].update(
    f3ad=("Uzun bütçe\nlog ss0 = -1,5", "Geniş keşif\nlog ss0 = -0,5"),
    f3sol="Geçiş görevine varış adımı (bin)",
    f3sag="Koşu (ulaşılan en yüksek müfredat seviyesi)",
    f3solb="Geçiş görevine varış",
    f3sagb="Ulaşılan en yüksek müfredat seviyesi",
    f3sev="Seviye {s}",
    f3ortanca="ortanca {v}k")


def oku_dizin(dizin):
    """Bir kampanyanin butun kosularini okur. Sekil 3 icin."""
    ks = []
    for y in sorted(glob.glob(os.path.join(dizin, "*_gunluk.json"))):
        with open(y, encoding="utf-8") as f:
            g = json.load(f)["gunluk"]
        varis = [k["adim"] for k in g if k["seviye"] >= 2]
        ks.append(dict(ad=os.path.basename(y).replace("_gunluk.json", ""),
                       seviye=max(k["seviye"] for k in g),
                       varis=min(varis) if varis else None))
    if not ks:
        sys.exit(f"kosu gunlugu bulunamadi: {dizin}")
    return ks


def fig3():
    kamp = [oku_dizin(KOSU), oku_dizin(KOSU_GENIS)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 4.2))
    ad = list(T("f3ad"))
    ortanca, tepe = [], 0.0

    for i, ks in enumerate(kamp):
        v = np.array([k["varis"] for k in ks], float) / 1000.0
        x = np.full(len(v), i, float) + np.linspace(-0.15, 0.15, len(v))
        a1.scatter(x, v, s=34, color=KAMPANYA_RENK[i], zorder=3,
                   edgecolor="white", linewidth=0.7)
        a1.plot([i - 0.26, i + 0.26], [v.mean()] * 2,
                color=KAMPANYA_RENK[i], lw=2.2, zorder=4)
        a1.errorbar(i, v.mean(), yerr=v.std(ddof=1), color=KAMPANYA_RENK[i],
                    capsize=4, lw=1.2, zorder=2)
        ortanca.append((i, float(np.median(v))))
        tepe = max(tepe, float(v.max()))
    # ⚠️ Etiketler ORTAK bir yukseklige konur, yoksa uzun butce sutununun
    # aykiri tohumu etiketi baslik hizasina itiyor ve ustune biniyor.
    a1.set_ylim(top=tepe * 1.16)
    for i, m in ortanca:
        a1.text(i, tepe * 1.07, T("f3ortanca").format(v=sayi(m, 0)),
                ha="center", fontsize=9.5, weight="semibold",
                color=KAMPANYA_RENK[i])
    a1.set_xticks(range(2))
    a1.set_xticklabels(ad, fontsize=9)
    a1.set_xlim(-0.55, 1.55)
    a1.set_ylabel(T("f3sol"))
    a1.set_title(T("f3solb"), fontsize=10.5)
    a1.grid(axis="y", alpha=0.18, lw=0.6)
    _eksen_bicimi(a1, "y")     # ⚠️ x KATEGORIK

    seviyeler = sorted({k["seviye"] for c in kamp for k in c})
    tonlar = dict(zip(seviyeler, ("#7FB3EC", "#1B4C8C", "#B04A2E")))
    alt = np.zeros(2)
    x = np.arange(2)
    for s in seviyeler:
        h = np.array([sum(1 for k in c if k["seviye"] == s) for c in kamp], float)
        a2.bar(x, h, 0.46, bottom=alt, color=tonlar[s], edgecolor="white",
               linewidth=1.0, label=T("f3sev").format(s=s), zorder=3)
        for xi, hi, ai in zip(x, h, alt):
            if hi > 0:
                a2.text(xi, ai + hi / 2, f"{int(hi)}", ha="center", va="center",
                        color="white" if s != min(seviyeler) else "#222222",
                        fontsize=11, weight="semibold", zorder=4)
        alt += h
    a2.set_xticks(x)
    a2.set_xticklabels(ad, fontsize=9)
    a2.set_ylabel(T("f3sag"))
    a2.set_title(T("f3sagb"), fontsize=10.5)
    a2.set_ylim(0, max(alt) * 1.22)
    a2.legend(frameon=False, fontsize=9, ncol=len(seviyeler), loc="upper center")
    a2.grid(axis="y", alpha=0.18, lw=0.6)
    _eksen_bicimi(a2, "y")     # ⚠️ x KATEGORIK
    for ax in (a1, a2):
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.tight_layout()
    for u in ("pdf", "png"):
        fig.savefig(os.path.join(_BURASI, f"fig3_campaign_compare{T(chr(101)+chr(107))}.{u}"),
                    dpi=300 if u == "png" else None, bbox_inches="tight")
    plt.close(fig)
    return [{s: sum(1 for k in c if k["seviye"] == s) for s in seviyeler}
            for c in kamp]


if __name__ == "__main__":
    import sys
    _diller = ("en", "tr")
    if "--dil" in sys.argv:
        _diller = (sys.argv[sys.argv.index("--dil") + 1],)
    for _d in _diller:
        globals()["_DIL"] = _d
        veri = oku()
        n = fig1(veri)
        fig2(veri)
        d3 = fig3()
        print(f"uc figur uretildi, {n} kosu okundu, "
              f"{sum(len(v) for v in veri.values())} gunluk")
        for v in SIRA:
            if v in veri:
                print(f"  {v:<11}n={len(veri[v])}")
        print(f"  SEKIL 3 seviye dagilimi  uzun {d3[0]}  genis {d3[1]}"
              f"  -> {'AYNI' if d3[0] == d3[1] else 'FARKLI'}")
