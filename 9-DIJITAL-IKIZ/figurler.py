#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KISIM II ve III FIGURLERI

Veri kaynagi diskteki olcum dosyalaridir, figur uretimi sirasinda
YENIDEN HESAP YAPILMAZ. Boylece figurler metinde raporlanan
sayilarla birebir ayni veriden gelir.

  ogrenme/metrik_sonuclari.json    politikasiz dort metrik
  ogrenme/kosular/*.json           pilot egitim gunlukleri

Ciktilar  cikti/*.pdf ve *.svg    (tezin figures/ dizinine kopyalanir)

Bicim, 2-CIZIM-MOTORU/analiz_grafikleri.py ile ayni tutulmustur.
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

_BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_BURASI, "dinamik"))
CIKTI = os.path.join(_BURASI, "cikti")
os.makedirs(CIKTI, exist_ok=True)

C = dict(ana="#1F3A5F", ikincil="#2E5E8C", uyari="#B04A2E",
         iyi="#3E7C4A", notr="#8A8A8A", acik="#D8DEE6")
VAR_RENK = {"limulus": C["ana"], "ikili": C["ikincil"],
            "senkron": C["uyari"], "liftcruise": C["notr"]}
VAR_AD = {"limulus": "LIMULUS (tam)", "ikili": "İkili tilt",
          "senkron": "Senkron tilt", "liftcruise": "Lift + cruise"}

plt.rcParams.update({
    # ⚠️ fonttype 42 ZORUNLU, bkz. 4-KARARLAR/29. Ontanimli Type 3 ciktisi
    # Turkce harflerde (s-cedilla, I-nokta, i-noktasiz) metni parcaliyor ve
    # gorunur bosluk birakiyor. 42 ayrica metni aranabilir kiliyor.
    "pdf.fonttype": 42, "svg.fonttype": "none", "pdf.compression": 6,
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
    "axes.edgecolor": "#444444", "axes.linewidth": 0.9,
    "legend.frameon": False, "figure.dpi": 110,
})


def dipnot(fig, metin):
    fig.text(0.99, 0.012, metin, ha="right", va="bottom", fontsize=7.2,
             color="#666666", style="italic")


def kaydet(fig, ad):
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    for uz in ("pdf", "svg"):
        fig.savefig(os.path.join(CIKTI, f"{ad}.{uz}"), bbox_inches="tight")
    plt.close(fig)
    print("  " + ad)


def pilot_bolum_bandi():
    """Pilot kosularin kumulatif ortalama bolum uzunlugu bandi.

    Karar 12 tamlik kaydi. Planlanan yirmi kosudan tamamlanan onu okunur,
    her kosu icin son gunluk kaydindaki adim / bolum orani alinir. Deger
    elle yazilmaz, gunluklerden gelir.
    """
    D = os.path.join(_BURASI, "ogrenme", "kosular")
    v = []
    for f in sorted(glob.glob(os.path.join(D, "*_gunluk.json"))):
        with open(f) as fh:
            d = json.load(fh)
        g = d["gunluk"] if isinstance(d, dict) and "gunluk" in d else d
        s = g[-1]
        v.append(s["adim"] / max(s["n_bolum"], 1))
    if not v:
        raise SystemExit("kosular/ altinda pilot gunlugu yok")
    return min(v), float(np.mean(v)), max(v), len(v)


def v2_bolum_bandi():
    """Bir milyon adimlik kampanyanin kumulatif ortalama bolum uzunlugu.

    Ara kayit bolum sayacini kirpiyordu (karar 25), bu yuzden metrik yalniz
    bolum sayaci tek yonlu kalan kosularda gecerlidir. Kirpilmis kosular
    atlanir, cunku onlarda oran siserek 1838-4431 gibi gorunuyordu.

    Tilt varyantlari ile lift-cruise ayri dondurulur. Sebep fizik: bu
    kampanyada lift-cruise ayri bir cruise itici birimi tasimaz, ileri itki
    uretemez ve ucusu surdurmez, dolayisiyla ayni bant icinde raporlanmasi
    "duzeltmeler bolum uzunlugunu su banda cikardi" cumlesini yaniltir.

    Deger elle yazilmaz, gunluklerden gelir.
    """
    D = os.path.join(_BURASI, "ogrenme", "kosular_v2")
    tilt, lc = [], []
    for f in sorted(glob.glob(os.path.join(D, "*_gunluk.json"))):
        with open(f) as fh:
            d = json.load(fh)
        g = d["gunluk"] if isinstance(d, dict) and "gunluk" in d else d
        nb = [r["n_bolum"] for r in g]
        if any(nb[i] < nb[i - 1] for i in range(1, len(nb))):
            continue
        s = g[-1]
        hedef = lc if os.path.basename(f).startswith("liftcruise") else tilt
        hedef.append(s["adim"] / max(s["n_bolum"], 1))
    if not tilt:
        raise SystemExit("kosular_v2/ altinda gecerli tilt kosusu yok")
    return (min(tilt), float(np.mean(tilt)), max(tilt), len(tilt),
            min(lc), max(lc), len(lc))


def asimetrik_oranlar():
    """Tek pod arizasinda yan kaymasiz trim kapanma oranlari.

    Karar 43'un ince izgarali olcumunu (27 hiz x 4 pod = 108 durum) okur.
    Metrik izgaraya duyarlidir, bu yuzden figur hangi izgarayi cizdigini
    basligina yazar. Olcum dosyasi yoksa karar 21'in kaba izgarasina
    (3 hiz x 2 pod = 6 durum) duser, boylece figur sessizce yanlis
    izgarayla cizilmez.
    """
    y = os.path.join(_BURASI, "cikti_asimetrik", "s1_pod_arizasi.json")
    if not os.path.exists(y):
        return [66.7, 66.7, 0.0, 0.0], "kaba izgara, 6 durum"
    with open(y) as f:
        d = json.load(f)
    K = [k for k in d["kayitlar"] if not k["beta_serbest"]]
    o = []
    for ad in ("limulus", "ikili", "senkron", "liftcruise"):
        alt = [k for k in K if k["varyant"] == ad]
        o.append(100.0 * sum(1 for k in alt if k["basarili"]) / max(len(alt), 1))
    n = len([k for k in K if k["varyant"] == "limulus"])
    return o, f"ince izgara, {n} durum"


def metrikler():
    y = os.path.join(_BURASI, "ogrenme", "metrik_sonuclari.json")
    if not os.path.exists(y):
        raise SystemExit("metrik_sonuclari.json yok. Once "
                         "ogrenme/metrikler.py kosulmali.")
    with open(y) as f:
        return json.load(f)


# =====================================================================
# 1 — TRIM ZARFI HARITASI
# =====================================================================
def f_trim_zarfi(M):
    hizlar = np.arange(0.0, 75.0, 7.5)
    gamalar = np.arange(-9.0, 9.1, 4.5)
    fig, axs = plt.subplots(1, 4, figsize=(11.4, 3.1), sharey=True)
    for ax, (v, d) in zip(axs, M.items()):
        Z = np.array(d["trim_zarfi"]["izgara"], dtype=float)
        ax.pcolormesh(hizlar, gamalar, Z, cmap="Blues", vmin=0, vmax=1.4,
                      shading="nearest", edgecolors="white", linewidth=0.4)
        ax.set_title(f"{VAR_AD[v]}\n{d['trim_zarfi']['deger']:.0f} "
                     r"m/s $\times$ derece",
                     fontsize=9, color=VAR_RENK[v], weight="semibold")
        ax.set_xlabel("Hız (m/s)")
        ax.set_xticks([0, 30, 60])
        ax.set_yticks([-9, -4.5, 0, 4.5, 9])
    axs[0].set_ylabel("Uçuş yolu açısı (derece)")
    fig.suptitle("Trim Zarfı — çözüm bulunan denge noktaları",
                 fontsize=11.5, weight="semibold", y=1.06)
    dipnot(fig, "Koyu hücre trim çözümü bulundu demektir. Üç tilt "
                "konfigürasyonu simetrik uçuşta birebir aynı")
    kaydet(fig, "k2_trim_zarfi")


# =====================================================================
# 2 — GECIS KORIDORU
# =====================================================================
def f_koridor(M):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.0),
                                 gridspec_kw=dict(width_ratios=[1.25, 1]))
    # ⚠️ LIMULUS ile ikili tilt birebir cakisiyor. Bu bir cizim kusuru
    # degil, sonucun kendisi. Ikili kesikli ve kalin cizilip ustte
    # birakiliyor ki iki egrinin ayni oldugu gorunsun.
    stil = {"limulus": dict(lw=3.4, ls="-", alpha=0.95, zorder=2),
            "ikili": dict(lw=1.6, ls=(0, (4, 3)), alpha=1.0, zorder=4),
            "senkron": dict(lw=2.0, ls="-", alpha=0.95, zorder=3),
            "liftcruise": dict(lw=1.8, ls="-", alpha=0.9, zorder=1)}
    for v, d in M.items():
        g = d["gecis_koridoru"]
        a1.plot(g["hizlar"], g["genislikler"], marker="o", ms=4.2,
                color=VAR_RENK[v], label=VAR_AD[v], **stil[v])
    a1.set_xlabel("Hız (m/s)")
    a1.set_ylabel("Trim edilebilir tilt aralığı (derece)")
    a1.set_title("Geçiş koridoru genişliği", fontsize=10.5,
                 weight="semibold")
    a1.axvspan(30, 60, alpha=0.08, color=C["iyi"])
    a1.text(45, a1.get_ylim()[1] * 0.94, "kazanımın toplandığı bant",
            ha="center", fontsize=8, color=C["iyi"], style="italic")
    a1.legend(fontsize=8.4, loc="upper left")
    a1.text(0.5, 0.60, "LIMULUS ve ikili tilt\nbirebir çakışıyor",
            transform=a1.transAxes, fontsize=8.2, color=C["ikincil"],
            style="italic", ha="center")

    adlar = list(M.keys())
    degerler = [M[v]["gecis_koridoru"]["deger"] for v in adlar]
    bar = a2.bar([VAR_AD[v].replace(" ", "\n") for v in adlar], degerler,
                 color=[VAR_RENK[v] for v in adlar], width=0.62)
    for b, x in zip(bar, degerler):
        a2.text(b.get_x() + b.get_width() / 2, x + 0.8, f"{x:.1f}",
                ha="center", fontsize=8.6, weight="semibold")
    taban = M["senkron"]["gecis_koridoru"]["deger"]
    tam = M["limulus"]["gecis_koridoru"]["deger"]
    a2.axhline(taban, color=C["uyari"], ls=":", lw=1.2)
    a2.text(3.35, taban + 0.8, f"+%{(tam/taban-1)*100:.0f}", ha="right",
            fontsize=9, color=C["ana"], weight="semibold")
    a2.set_ylabel("Ortalama koridor genişliği (derece)")
    a2.set_title("Hızlar boyunca ortalama", fontsize=10.5, weight="semibold")
    a2.tick_params(axis="x", labelsize=8)
    dipnot(fig, "Ortalama tilt açısı sabitlenip varyantın kendi serbestlik "
                "derecesine sapma izni verilerek ölçüldü")
    kaydet(fig, "k2_gecis_koridoru")


# =====================================================================
# 3 — KONTROL OTORITESININ TILT BAGIMLILIGI  (bulgu F3)
# =====================================================================
def f_otorite():
    """⚠️ DUZELTILMIS FIGUR (03.08.2026).

    Ilk surum yalniz DIFERANSIYEL ITKI sutununu ciziyor ve "tilt 90'da
    otorite yok" diyordu. Bu YANLIS. Kontrol etkinlik matrisinin iki
    ayri sutunu var ve ters yonde davraniyorlar.

        dM_y/dT   = x cos(th)      itki sutunu, 90 derecede sifirlanir
        dM_y/dth  = -T x sin(th)   tilt sutunu, 90 derecede AZAMI

    Yani bagimsiz tilt cruise'da otoritesini kaybetmez, otorite bir
    sutundan digerine GECER. Ayrinti 4-KARARLAR/14.
    """
    from arac import Limulus
    from konfigurasyon import KONF as K
    from trim import trim
    ac = Limulus()
    td = np.linspace(0, 90, 400)
    th = np.radians(td)
    x = abs(ac.pod[0, 0])
    # Iki itki degeri de trim cozucuden gelir, elle girilmez.
    T_hov = float(np.mean(trim(ac, V=0.0, gama=0.0).T))
    T_cr = float(np.mean(trim(ac, V=K["V_CRUISE"], gama=0.0).T))
    dT = 200.0                      # N, cift basina diferansiyel itki
    dth = np.radians(10.0)          # rad, cift basina diferansiyel tilt

    # Tez sayfasinda 0,98 textwidth'e olceklendigi icin figur DAR tutulur,
    # boylece yazi tipi kucuk basilmaz.
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 3.3))

    for ax, T, ad in ((a1, T_hov, f"hover itkisi (T = {T_hov:.0f} N/pod)"),
                      (a2, T_cr, f"cruise itkisi (T = {T_cr:.0f} N/pod)")):
        M_itki = 4 * x * np.cos(th) * dT / 1e3
        M_tilt = 4 * x * T * np.sin(th) * dth / 1e3
        ax.plot(td, M_itki, lw=2.0, color=C["ana"],
                label=f"diferansiyel itki (±{dT:.0f} N)")
        ax.plot(td, M_tilt, lw=2.0, color=C["iyi"],
                label=f"diferansiyel tilt (±{np.degrees(dth):.0f}°)")
        ax.plot(td, M_itki + M_tilt, lw=1.3, ls=":", color=C["notr"],
                label="toplam")
        ax.axvline(85, color=C["uyari"], ls="--", lw=1.2)
        ax.text(83.5, ax.get_ylim()[1] * 0.97, "cruise tilt", rotation=90,
                fontsize=8.5, color=C["uyari"], ha="right", va="top")
        ax.set_xlabel("Tilt açısı (derece)", fontsize=10)
        ax.set_title(ad, fontsize=10.5, weight="semibold")
        ax.set_xlim(0, 90)
        ax.set_xticks([0, 30, 60, 90])
        ax.tick_params(labelsize=9.5)
    a1.set_ylabel("Yunuslama momenti (kN m)", fontsize=10)

    # Tek ortak gosterge, panellerin altinda. Panel ici yerlestirme
    # "cruise tilt" etiketiyle cakisiyordu.
    fig.legend(*a1.get_legend_handles_labels(), ncol=3, fontsize=9,
               loc="lower center", bbox_to_anchor=(0.5, -0.03))
    fig.suptitle("Kontrol otoritesi kaybolmuyor, sütunlar arasında yer değiştiriyor",
                 fontsize=11, weight="semibold", y=1.03)
    # Dipnot yok. Ayni cumle tezin sekil acikamasinda zaten var, alt
    # bosluga gosterge yerlestirildi.
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    for uz in ("pdf", "svg"):
        fig.savefig(os.path.join(CIKTI, f"k2_kontrol_otoritesi.{uz}"),
                    bbox_inches="tight")
    plt.close(fig)
    print("  k2_kontrol_otoritesi")


# =====================================================================
# 4 — ROTOR GUC AYRISIMI
# =====================================================================
def f_guc_ayrisim():
    from konfigurasyon import KONF as K
    from rotor import Rotor
    r = Rotor(D=K["D_ROTOR"], FOM=K["FOM"], N_PAL=K["N_PAL"], RPM=K["RPM"])
    rho, V = K["RHO0"], K["V_CRUISE"]
    tiltler = np.linspace(0, 90, 60)
    T = 460.0
    ind, prof, fayda = [], [], []
    for td in tiltler:
        ad = math.radians(td)          # tilt=90 -> eksenel
        v = r.v_ind(T, rho, V, ad)
        Vp = V * math.sin(ad)
        fayda.append(T * Vp / 1e3)
        ind.append(r.kappa * T * v / 1e3)
        prof.append(r.profil_gucu(V, ad) / 1e3)

    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    ax.stackplot(tiltler, fayda, ind, prof,
                 colors=[C["ana"], C["ikincil"], C["uyari"]],
                 labels=["faydalı itki gücü", "indükleme (κ dahil)",
                         "profil gücü"], alpha=0.88)
    ax.set_xlabel("Tilt açısı (derece)")
    ax.set_ylabel("Rotor başına şaft gücü (kW)")
    ax.set_title("Cruise hızında rotor güç ayrışımı",
                 fontsize=11.5, weight="semibold", pad=10)
    ax.legend(fontsize=8.4, loc="upper left")
    ax.set_xlim(0, 90)
    dipnot(fig, f"V = {V} m/s, T = {T:.0f} N. Profil gücü ilerleme oranıyla "
                "büyür, düşük tiltte baskındır")
    kaydet(fig, "k2_guc_ayrisim")


# =====================================================================
# 5 — PILOT OGRENME EGRILERI
# =====================================================================
def f_ogrenme():
    dizin = os.path.join(_BURASI, "ogrenme",
                         os.environ.get("LIMULUS_KOSU_DIZINI", "kosular"))
    dosyalar = sorted(glob.glob(os.path.join(dizin, "*_gunluk.json")))
    if not dosyalar:
        print("  (egitim gunlugu yok, atlandi)")
        return
    veri, veri_ad = {}, {}
    for y in dosyalar:
        ad = os.path.basename(y).split("_t")[0]
        with open(y) as f:
            g = json.load(f)["gunluk"]
        veri.setdefault(ad, []).append(g)
        veri_ad.setdefault(ad, []).append(
            (os.path.basename(y).replace("_gunluk.json", ""), g))

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.0))
    for v, kosular in veri.items():
        n = min(len(k) for k in kosular)
        adim = np.array([k["adim"] for k in kosular[0][:n]])
        M = np.array([[k["odul"] for k in ks[:n]] for ks in kosular])
        M = np.where(np.isfinite(M), M, np.nan)
        ort = np.nanmean(M, axis=0)
        a1.plot(adim / 1e3, ort, lw=1.9, color=VAR_RENK[v],
                label=f"{VAR_AD[v]} (n={len(kosular)})")
        if len(kosular) > 1:
            sd = np.nanstd(M, axis=0)
            a1.fill_between(adim / 1e3, ort - sd, ort + sd,
                            color=VAR_RENK[v], alpha=0.14)
    a1.axhline(0.65, color=C["uyari"], ls="--", lw=1.3)
    a1.text(a1.get_xlim()[1] * 0.98, 0.67, "müfredat eşiği 0,65", ha="right",
            fontsize=8, color=C["uyari"])
    a1.set_xlabel("Çevre adımı (bin)")
    a1.set_ylabel("Normalize bölüm ödülü")
    _n_kosu = sum(len(k) for k in veri.values())
    _adim_max = int(max(k[-1]["adim"] for ks in veri.values() for k in ks))
    _sev_max = max(int(k["seviye"]) for ks in veri.values() for kk in ks for k in kk)
    a1.set_title(f"Öğrenme eğrileri — {_n_kosu} koşu, {_adim_max/1e6:.1f}M adım",
                 fontsize=10.5,
                 weight="semibold")
    a1.set_ylim(-0.65, 0.78)
    # ⚠️ Cerceve ACIK. Cercevesiz efsanede egriler yazinin ustunden
    # geciyor ve etiketler okunmuyordu.
    a1.legend(fontsize=8.2, loc="lower left", frameon=True,
              framealpha=0.92, edgecolor="#CCCCCC", facecolor="white")

    # ⚠️ SAG PANEL — bolum uzunlugu YALNIZ kesintisiz kosular icin cizilir.
    # Ara kayit bolum sayacini kirpiyordu, devam eden kosularda bu metrik
    # sisiyor. Ayrinti 4-KARARLAR/25. Odul egrisi etkilenmedi, sol panel
    # butun kosulari gosteriyor.
    KESINTISIZ = {"limulus_t0", "ikili_t0", "senkron_t0", "liftcruise_t0",
                  "limulus_t1", "ikili_t1"}
    cizilen = 0
    for v, kosular in veri_ad.items():
        temiz = [g for ad, g in kosular if ad in KESINTISIZ]
        if not temiz:
            continue
        n = min(len(k) for k in temiz)
        adim = np.array([k["adim"] for k in temiz[0][:n]])
        uz = np.array([[k["adim"] / max(k["n_bolum"], 1) for k in ks[:n]]
                       for ks in temiz]).mean(axis=0)
        a2.plot(adim / 1e3, uz, lw=1.9, color=VAR_RENK[v],
                label=f"{VAR_AD[v]} (n={len(temiz)})")
        cizilen += len(temiz)
    a2.axhline(1000, color=C["iyi"], ls="--", lw=1.3)
    a2.text(a2.get_xlim()[1] * 0.98, 1000 * 1.04, "bölüm azami uzunluğu",
            ha="right", fontsize=8, color=C["iyi"])
    a2.set_yscale("log")
    a2.set_xlabel("Çevre adımı (bin)")
    a2.set_ylabel("Ortalama bölüm uzunluğu (adım)")
    a2.set_title(f"Ajan ne kadar havada kalıyor ({cizilen} kesintisiz koşu)",
                 fontsize=10.5, weight="semibold")
    a2.legend(fontsize=8.2, loc="lower right", frameon=True,
              framealpha=0.92, edgecolor="#CCCCCC", facecolor="white")
    _tam = _n_kosu >= 20
    dipnot(fig, ("TAM SET — " if _tam else "⚠️ KISMİ SET — ")
           + f"{_n_kosu}/20 koşu, {_adim_max/1e6:.1f}M adım, "
           + f"ulaşılan en yüksek müfredat seviyesi {_sev_max}. "
           + ("" if _tam else "Ön kayıt beş tohum şart koşuyor, "
              "bu figür sonuç olarak kullanılamaz. ")
           + "Gölge bant tohumlar arası dağılım. "
           + f"SAĞ PANEL yalnız {cizilen} kesintisiz koşuyu gösterir — ara "
             "kayıt bölüm sayacını kırpıyordu, devam eden koşularda bu metrik "
             "geçersiz (4-KARARLAR/25). Ödül eğrisi etkilenmedi.")
    kaydet(fig, "k3_ogrenme_egrileri")


# =====================================================================
# 6 — METRIK OZETI
# =====================================================================
def f_metrik_ozeti(M):
    eksenler = [("trim_zarfi", "Trim zarfı"),
                ("gecis_koridoru", "Geçiş koridoru"),
                ("ariza_toleransi", "Arıza toleransı"),
                ("enerji", "Enerji")]
    fig, ax = plt.subplots(figsize=(8.6, 4.0))
    x = np.arange(len(eksenler))
    gen = 0.2
    taban = {k: M["senkron"][k]["deger"] for k, _ in eksenler}
    for i, v in enumerate(["limulus", "ikili", "senkron", "liftcruise"]):
        bagil = []
        for k, _ in eksenler:
            d = M[v][k]["deger"]
            t = taban[k]
            if d is None or (isinstance(d, float) and not np.isfinite(d)):
                bagil.append(np.nan)
            elif k == "enerji":
                bagil.append(t / d)          # kucuk iyi -> ters
            else:
                bagil.append(d / t)
        b = ax.bar(x + (i - 1.5) * gen, bagil, gen * 0.9,
                   color=VAR_RENK[v], label=VAR_AD[v])
        for bb, val in zip(b, bagil):
            if not np.isfinite(val):
                ax.text(bb.get_x() + bb.get_width() / 2, 0.05, "görev\nyok",
                        ha="center", fontsize=7, color=C["uyari"],
                        rotation=90, va="bottom")
    ax.axhline(1.0, color="#444444", lw=1.0)
    ax.set_xticks(x); ax.set_xticklabels([a for _, a in eksenler])
    ax.set_ylabel("Senkron tilte göre bağıl başarım")
    ax.set_title("Bağımsız tiltin simetrik uçuşta ölçülen kazanımı",
                 fontsize=11.5, weight="semibold", pad=10)
    ax.legend(fontsize=8.2, ncol=2)
    ax.set_ylim(0, 1.45)
    # Besinci eksen (asimetrik ariza trimi) bu figurde YOK, kendi olcegi
    # 2,7 kat oldugu icin buraya sigmaz. Ayri figur: k3_asimetrik_ariza.
    dipnot(fig, "1,0 çizgisi senkron tilt. Simetrik uçuşun dört ekseni, "
                "beşinci eksen ayrı figürde")
    kaydet(fig, "k3_metrik_ozeti")


# =====================================================================
# 7 — ASIMETRIK ARIZA TRIMI  (karar 21)
# =====================================================================
def f_asimetrik_ariza():
    """Tek pod arizasinda yan kaymasiz trim.

    Ince izgarada ayrim niceliktir (%31 / %33 / %12), yalnız lift+cruise
    satiri (%0) bir nitelik farkidir. Kaba izgaranin %67 / %0 degerleri
    karar 21'de, olcum karar 43'te.
    """
    var = ["limulus", "ikili", "senkron", "liftcruise"]
    eksen = [4, 2, 1, 0]                 # tilt ekseni sayisi
    kip = [3, 1, 0, 0]                   # diferansiyel kip sayisi
    # Oran ARTIK ELLE YAZILMIYOR. Karar 43 olcumu okunur, bulunamazsa
    # karar 21'in kaba izgara degerlerine duser ve figur bunu yazar.
    oran, izgara = asimetrik_oranlar()

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.0))

    y = np.arange(len(var))
    renk = [VAR_RENK[v] for v in var]
    a1.barh(y, oran, color=renk, height=0.6)
    for i, o in enumerate(oran):
        a1.text(o + 2, i, f"%{o:.0f}", va="center", fontsize=10,
                weight="semibold", color=renk[i])
    a1.set_yticks(y, [VAR_AD[v] for v in var])
    a1.invert_yaxis()
    a1.set_xlim(0, 82)
    a1.set_xlabel("Yan kaymasız trim bulunan durum (%)")
    a1.set_title(f"Tek pod arızasında trim ({izgara})", fontsize=10.5,
                 weight="semibold")
    a1.grid(axis="y", visible=False)

    a2.plot(eksen, kip, "o-", color=C["ana"], lw=2, ms=9, zorder=3)
    # ⚠️ Etiket konumlari elle verildi. Ontanimli sag-alt kaydirmada
    # LIMULUS etiketi eksen disina tasip kirpiliyor, lift+cruise ile
    # senkron etiketleri de ust uste biniyordu.
    yer = {"liftcruise": ((6, 7), "left"), "senkron": ((6, -13), "left"),
           "ikili": ((8, -4), "left"), "limulus": ((-10, -4), "right")}
    for e, k, v in zip(eksen, kip, var):
        kay, hiza = yer[v]
        a2.annotate(VAR_AD[v], (e, k), textcoords="offset points",
                    xytext=kay, ha=hiza, fontsize=8, color=C["notr"])
    a2.set_xlabel("Bağımsız tilt ekseni sayısı $n$")
    a2.set_ylabel("Diferansiyel kip sayısı $n-1$")
    a2.set_title("Kip sayısı mimariden gelir", fontsize=10.5,
                 weight="semibold")
    a2.set_xticks([0, 1, 2, 3, 4])
    a2.set_yticks([0, 1, 2, 3])
    a2.set_xlim(-0.3, 4.35)
    a2.set_ylim(-0.4, 3.4)
    dipnot(fig, f"Sol: yan kaymasız trim, {izgara}, karar 43. "
                "Sağ: ortak kip çıkarılınca n−1 diferansiyel kip kalır, "
                "senkron tiltte sıfırdır.")
    kaydet(fig, "k3_asimetrik_ariza")


# =====================================================================
# 8 — TILT KANALININ POLITIKA TARAFINDAN KULLANIMI  (karar 27)
# =====================================================================
def f_tilt_kullanimi():
    var = ["limulus", "ikili", "senkron"]
    itki = [0.786, 0.958, 0.749]
    tilt = [0.370, 0.480, 0.345]
    tstd = [0.368, 0.096, 0.116]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.0))

    x = np.arange(len(var)); g = 0.36
    a1.bar(x - g/2, itki, g, label="itki kanalı", color=C["acik"],
           edgecolor=C["notr"])
    a1.bar(x + g/2, tilt, g, label="tilt kanalı",
           color=[VAR_RENK[v] for v in var])
    a1.set_xticks(x, [VAR_AD[v] for v in var], fontsize=8.5)
    a1.set_ylabel("Ortalama eylem genliği $|e|$")
    a1.set_title("Kanal boş değil", fontsize=10.5, weight="semibold")
    a1.legend(fontsize=8.2)
    a1.grid(axis="x", visible=False)

    orani = [t / m for t, m in zip(tstd, tilt)]
    bar = a2.bar(x, orani, 0.55, color=[VAR_RENK[v] for v in var])
    a2.axhline(0.3, color=C["uyari"], ls="--", lw=1.3)
    # ⚠️ etiketler cubuklarin sagina alindi, sag ust bosluk serbest
    a2.text(2.42, 0.42, "üstü: duruma bağlı", ha="left", va="bottom",
            fontsize=7.6, color=C["uyari"])
    a2.text(2.42, 0.18, "altı: sabit sapma", ha="left", va="top",
            fontsize=7.6, color=C["uyari"])
    for b, o in zip(bar, orani):
        a2.text(b.get_x() + b.get_width()/2, o + 0.03, f"{o:.2f}",
                ha="center", fontsize=9, weight="semibold")
    a2.set_xticks(x, [VAR_AD[v] for v in var], fontsize=8.5)
    a2.set_ylabel("Tilt eyleminin std / genlik oranı")
    a2.set_ylim(0, 1.25)
    a2.set_xlim(-0.55, 3.35)
    a2.set_title("Kontrol mü, önyargı mı", fontsize=10.5, weight="semibold")
    a2.grid(axis="x", visible=False)
    dipnot(fig, "Müfredat seviyesi 2, deterministik politika, beş bölüm. "
                "İkili tiltte oran 0,20 — politika sabit bir tilt açısı yazıp "
                "bırakıyor. Ablasyon o sabiti kaldırınca beş tohumda da "
                "başarım artıyor.")
    kaydet(fig, "k3_tilt_kullanimi")


# =====================================================================
# 9 — ORTAM DUZELTMELERI  (karar 15, Kisim II'nin tek figuru)
# =====================================================================
def f_ortam_duzeltmeleri():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.0))

    ad = ["T2 · hücum açısı\ncezası", "takip ödülü", "net"]
    deg = [-2.231, 2.497, 0.060]
    renk = [C["uyari"], C["iyi"], C["ana"]]
    b = a1.bar(range(3), deg, 0.55, color=renk)
    for bb, d in zip(b, deg):
        a1.text(bb.get_x() + bb.get_width()/2,
                d + (0.12 if d >= 0 else -0.28), f"{d:+.3f}",
                ha="center", fontsize=9.5, weight="semibold")
    a1.axhline(0, color="#333", lw=0.9)
    a1.set_xticks(range(3), ad, fontsize=8.2)
    a1.set_ylabel("Adım başına ödül (hover trimde)")
    a1.set_ylim(-3.0, 3.2)
    a1.set_title("Hayatta kalmanın getirisi kırkta bire inmişti",
                 fontsize=10.5, weight="semibold")
    a1.grid(axis="x", visible=False)

    # Pilot cubugu ARTIK ELLE YAZILMIYOR. Karar 12'nin tamlik kaydi geregi
    # tamamlanan on kosunun kumulatif ortalama bolum uzunlugu bandi cizilir.
    # Onceki surumde tek bir 79 degeri vardi ve o deger on kayit anindaki
    # kismi kumeden (alti kosu) geliyordu.
    p_alt, p_ort, p_ust, p_n = pilot_bolum_bandi()
    # Duzeltme sonrasi cubuk da ARTIK ELLE YAZILMIYOR. Onceki surumde tek bir
    # 600 degeri vardi. Bant, bolum sayaci tek yonlu kalan tilt kosularindan
    # gelir, lift-cruise ayri beyan edilir (bkz. v2_bolum_bandi aciklamasi).
    d_alt, d_ort, d_ust, d_n, lc_alt, lc_ust, lc_n = v2_bolum_bandi()
    etiket = [f"pilot\n(400k adım, {p_n} koşu)",
              f"düzeltme sonrası\n(1M adım, {d_n} tilt koşusu)"]
    uzunluk = [p_ort, d_ort]
    b2 = a2.bar([0, 1], uzunluk, 0.5, color=[C["notr"], C["ana"]])
    a2.errorbar([0], [p_ort], yerr=[[p_ort - p_alt], [p_ust - p_ort]],
                fmt="none", ecolor="#333333", elinewidth=1.1, capsize=5)
    a2.errorbar([1], [d_ort], yerr=[[d_ort - d_alt], [d_ust - d_ort]],
                fmt="none", ecolor="#333333", elinewidth=1.1, capsize=5)
    a2.text(0, p_ust + 18, f"{p_alt:.0f}–{p_ust:.0f} adım",
            ha="center", fontsize=10, weight="semibold")
    a2.text(1, d_ust + 18, f"{d_alt:.0f}–{d_ust:.0f} adım",
            ha="center", fontsize=10, weight="semibold")
    a2.axhline(1000, color=C["iyi"], ls="--", lw=1.3)
    a2.text(1.45, 1020, "bölüm azami uzunluğu", ha="right", fontsize=7.8,
            color=C["iyi"])
    a2.set_xticks([0, 1], etiket, fontsize=8.5)
    a2.set_ylabel("Ortalama bölüm uzunluğu (adım)")
    a2.set_ylim(0, 1150)
    a2.set_title("Üç ortam düzeltmesinin sonucu", fontsize=10.5,
                 weight="semibold")
    a2.grid(axis="x", visible=False)
    # ⚠️ dipnot TEK SATIR yazar ve satirlamaz. Uzun metin bbox_inches="tight"
    # ile sayfayi yana buyutuyor, tezde \textwidth'e sigdirilinca paneller
    # kuculuyor. Olcum kosullari bu yuzden tez altyazisinda, govde puntosunda.
    p_ad = {10: "on", 20: "yirmi"}.get(p_n, str(p_n))
    dipnot(fig, "Hiçbir PPO hiperparametresi değiştirilmedi. Pilotta "
                f"tamamlanan {p_ad} koşunun hiçbiri müfredatın sıfırıncı "
                "seviyesini geçememişti, düzeltme sonrası yirmi koşunun "
                "tamamı ikinci seviyeye ulaştı. Çubuklar kümülatif ortalama "
                "bölüm uzunluğunun koşular arası bandıdır.")
    kaydet(fig, "k2_ortam_duzeltmeleri")


# =====================================================================
# GIRIS NOKTASI
# ⚠️ Dosyanin EN SONUNDA olmali. Onceden ortadaydi ve sonradan eklenen
# uc figur (asimetrik ariza, tilt kullanimi, ortam duzeltmeleri) toplu
# uretimde atlaniyordu.
# =====================================================================
if __name__ == "__main__":
    print("Kısım II ve III figürleri üretiliyor")
    M = metrikler()
    f_trim_zarfi(M)
    f_koridor(M)
    f_otorite()
    f_guc_ayrisim()
    f_metrik_ozeti(M)
    f_ogrenme()
    f_asimetrik_ariza()
    f_tilt_kullanimi()
    f_ortam_duzeltmeleri()
    print(f"\n{CIKTI} dizinine yazıldı")
