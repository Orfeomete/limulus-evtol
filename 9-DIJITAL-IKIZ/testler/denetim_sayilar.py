#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROJE GENELI SAYI DENETIMI — tasiyici sayilar ve tuketicileri

NEDEN VAR. Bu projede ayni kusur sekiz kez ayri ayri yakalandi ve hepsi ayni
desende. Bir sayi olculuyor, bir yerde duzeltiliyor, TUKETICILERI SAYILMIYOR
ve eski deger baska bir belgede yasamaya devam ediyor. Karar 23'un uc
tuketicisi vardi, ikisi guncellendi, ucuncusu atlandi. Karar 16'nin yamasi
dort gun bir yan dosyada bekledi. 28/29 kN, senkron %0, bolum uzunlugu bandi,
M4' kodu, M3 uyarisi, M1'in figur satiri, M5'in yol hatasi. Hepsi elle
bulundu.

NE YAPAR. Her tasiyici sayi icin bir KAYIT tutar. Kayitta o sayinin kanonik
degeri, degerin NEREDEN geldigi ve hangi belgelerde GORUNMESI GEREKTIGI yazar.
Betik kanonik degeri kaynagindan HESAPLAR, sonra her tuketici belgede arar.

NE YAPMAZ. Belgelerdeki her sayiyi taramaz, yalniz kayitta yazili olanlari
denetler. Bu bilincli bir sinirdir, cunku her sayiyi taramak yanlis alarm
uretir. Kaydin kendi kapsami cikti sonunda RAPORLANIR, yani "kac sayi
denetlendi" gorunur ve kaydin eksikligi gizlenmez.

⚠️ BU BETIK KURAL G'YI UYGULAMAZ. Uyusmazlik buldugunda hangi tarafin
dogru oldugunu SOYLEMEZ ve hicbir dosyayi degistirmez. Kararı Mete verir.

Kosum
    cd 9-DIJITAL-IKIZ && python3 testler/denetim_sayilar.py
    python3 testler/denetim_sayilar.py --ayrintili     # gecenleri de yazar
Cikis kodu 0 ise butun kayitlar tutarli.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

_BURASI = os.path.dirname(os.path.abspath(__file__))
_IKIZ = os.path.dirname(_BURASI)
_KOK = os.path.dirname(_IKIZ)

TEZ = "1-TEZ/v3-birlesik/bolumler"
MAK = "10-MAKALELER"



# ⚠️ SURUM NUMARASI ICEREN YOLLAR KIRILGANDIR (09.08.2026'da olculdu).
# M6 paketi v1'den v2'ye cikinca bu kayittaki bes desen sessizce ATLANDI ve
# kapsam 29'dan 21'e dustu. Betik bunu yakalandi cunku atlanan kalem sayisini
# kendi ciktisinda raporluyor, yoksa "TUM KAYITLAR TUTARLI" yazip gecerdi.
# Kural, bir makale surum aldiginda bu dosyadaki yollari da guncelle. Daha
# iyisi, yol yerine desen kullanmak, o degisiklik yapilmadi cunku hangi surumun
# denetlendigi bilgisinin kendisi de bir kayittir.


def tr(sayi: str) -> str:
    """Turkce ondalik ayirici IKI BICIMDE yaziliyor, ikisini de kabul et.

    ⚠️ Bu yardimci, denetimin kendi ilk kosumunda ortaya cikti. Tez tablo
    icinde `36,43`, duz yazida ise `36\{,\}43` yaziyor. Ilk desen yalniz
    ikinciyi ariyordu ve tez dogru oldugu halde UYUSMAZLIK bildirdi. Yani
    denetim once kendi kusurunu buldu. Ders, bir denetim yanlis alarm
    verdiginde once denetimin kendisinden suphelenilir.
    """
    tam, ondalik = sayi.split(",")
    # ⚠️ Kacis sayisi dikkat ister. LaTeX kaynagi `36{,}43` yaziyor, yani
    # ters bolu YOK, yalniz suslu parantez var. Ilk denemede desen
    # `\\\{` uretti ve ters bolu de aradi, hicbir yerde bulamadi. Dogru
    # desen `\{,\}` yani yalniz suslu parantezin kacisi.
    return tam + r"(?:,|\{,\})" + ondalik

# =====================================================================
# KANONIK DEGERLERI KAYNAGINDAN HESAPLAYAN OKUYUCULAR
# =====================================================================
def _oku_json(yol):
    with open(os.path.join(_KOK, yol), encoding="utf-8") as f:
        return json.load(f)


def asimetrik():
    """Karar 43 olcumu. Zorunlu beta = 0 alt kumesi."""
    d = _oku_json("9-DIJITAL-IKIZ/cikti_asimetrik/s1_pod_arizasi.json")
    K = [k for k in d["kayitlar"] if not k["beta_serbest"]]
    out = {}
    for v in ("limulus", "ikili", "senkron", "liftcruise"):
        alt = [k for k in K if k["varyant"] == v]
        ok = [k for k in alt if k["basarili"]]
        out[v] = dict(kapanan=len(ok), denenen=len(alt),
                      oran=round(100 * len(ok) / len(alt)))
    out["ilk_V"] = min(k["V"] for k in K if k["basarili"])
    out["azami_yayilim"] = round(
        max(k["tilt_yayilimi"] for k in K if k["basarili"]), 1)
    return out



def yedeklilik():
    """Karar 48 olcumu. Kilit altinda kapanma orani ve goreli dusus.

    Kanonik deger BURADA hesaplanir, hicbir belgeden okunmaz. Ön kayitta
    yazili yontem, kilitlenen aktuator indisi uzerinden ortalamak ve arizali
    podun kilitli grupta bulundugu durumlari ayri saymaktir.
    """
    d = _oku_json("9-DIJITAL-IKIZ/cikti_asimetrik/k48_tilt_kilidi.json")
    K = d["kayitlar"]
    out = {}
    for v in ("limulus", "ikili", "senkron"):
        tab = [k for k in K if k["varyant"] == v and not k["kilit_grup"]]
        kil = [k for k in K if k["varyant"] == v and k["kilit_grup"]
               and not k["arizali_pod_kilitli"]]
        if not kil:                      # senkronda tek grup dort podu kapsar
            kil = [k for k in K if k["varyant"] == v and k["kilit_grup"]]
        o_t = sum(k["basarili"] for k in tab) / len(tab)
        o_k = sum(k["basarili"] for k in kil) / len(kil)
        out[v] = dict(taban_kapanan=sum(k["basarili"] for k in tab),
                      taban_denenen=len(tab),
                      kilit_kapanan=sum(k["basarili"] for k in kil),
                      kilit_denenen=len(kil),
                      dusus=round(100 * (o_t - o_k) / o_t, 1))
    tork = [k["azami_tork_N_m"] for k in K
            if k["basarili"] and k["azami_tork_N_m"] is not None]
    out["azami_tork"] = round(max(tork), 1)
    out["cozum"] = len(K)
    return out


def metrikler():
    """Politikasiz metriklerin son kaydi."""
    return _oku_json("9-DIJITAL-IKIZ/ogrenme/metrik_sonuclari.json")


def geometri():
    """Tasarim betiginin sozlukleri."""
    sys.path.insert(0, os.path.join(_KOK, "2-CIZIM-MOTORU"))
    import geometri as gm
    return gm.G, gm.P


def tez_derleme():
    """Tez PDF'inin sayfa sayisi ve kaynakca kunye sayisi."""
    out = {}
    pdf = os.path.join(_KOK, "1-TEZ/v3-birlesik/main.pdf")
    if os.path.exists(pdf):
        import subprocess
        r = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True)
        m = re.search(r"Pages:\s+(\d+)", r.stdout)
        if m:
            out["sayfa"] = int(m.group(1))
    bbl = os.path.join(_KOK, "1-TEZ/v3-birlesik/main.bbl")
    if os.path.exists(bbl):
        with open(bbl, encoding="utf-8", errors="ignore") as f:
            out["kaynak"] = f.read().count("\\bibitem")
    kararlar = [x for x in os.listdir(os.path.join(_KOK, "4-KARARLAR"))
                if re.match(r"^\d\d-", x)]
    out["karar"] = max(int(x[:2]) for x in kararlar) if kararlar else 0
    return out


# =====================================================================
# KAYIT — her satir bir tasiyici sayi
#   ad          insan icin
#   deger       kanonik deger, KAYNAKTAN hesaplanir
#   kaynak      degerin nereden geldigi, ciktida yazilir
#   desenler    {dosya: [aranacak duz metin ya da regex]}
# =====================================================================
def kayitlari_kur():
    A = asimetrik()
    Y = yedeklilik()
    M = metrikler()
    G, P = geometri()
    T = tez_derleme()

    def yuzde(v):
        return A[v]["oran"]

    kayit = []

    # --- karar 43, asimetrik arıza trimi -----------------------------
    kayit.append(dict(
        ad="Asimetrik trim oranlari (4/2/1/0 eksen)",
        deger=f"%{yuzde('limulus')} / %{yuzde('ikili')} / "
              f"%{yuzde('senkron')} / %{yuzde('liftcruise')}",
        kaynak="cikti_asimetrik/s1_pod_arizasi.json, beta=0 alt kumesi",
        desenler={
            f"{TEZ}/J_sonuclar.tex": [
                rf"34 / 108.*?\\%{yuzde('limulus')}",
                rf"36 / 108.*?\\%{yuzde('ikili')}"],
            f"{TEZ}/Z_sentez.tex": [rf"\\%{yuzde('ikili')}"],
            f"{MAK}/M1_DIJITAL_IKIZ_CERCEVESI/02_MAKALE_AKTIF/M1_EN_v6.md":
                [rf"{yuzde('limulus')}%", rf"{yuzde('ikili')}%"],
            f"{MAK}/M6_TILT_EKSEN_SAYISI/02_MAKALE_AKTIF/M6_EN_v3.md":
                [rf"{yuzde('limulus')} percent", rf"{yuzde('ikili')} percent"],
            "CLAUDE.md": [rf"%{yuzde('limulus')}", rf"%{yuzde('ikili')}"],
        }))

    kayit.append(dict(
        ad="Ilk kapanan hiz",
        deger=f"{A['ilk_V']} m/s",
        kaynak="ayni dosya, basarili kayitlarin en kucuk V degeri",
        desenler={
            f"{TEZ}/J_sonuclar.tex": [tr("47,5")],
            f"{MAK}/M6_TILT_EKSEN_SAYISI/02_MAKALE_AKTIF/M6_EN_v3.md":
                [r"47\.5 m/s"],
        }))

    kayit.append(dict(
        ad="Azami tilt yayilimi",
        deger=f"{A['azami_yayilim']} derece",
        kaynak="ayni dosya, basarili kayitlarin azami tilt_yayilimi",
        desenler={
            f"{TEZ}/J_sonuclar.tex": [tr("75,5")],
            f"{TEZ}/Z_sentez.tex": [tr("75,5")],
            f"{MAK}/M6_TILT_EKSEN_SAYISI/02_MAKALE_AKTIF/M6_EN_v3.md":
                [r"75\.5 degrees"],
            "CLAUDE.md": [r"75,5"],
        }))

    # --- politikasiz metrikler ---------------------------------------
    kor_l = M["limulus"]["gecis_koridoru"]["deger"]
    kor_s = M["senkron"]["gecis_koridoru"]["deger"]
    kayit.append(dict(
        ad="Gecis koridoru genisligi",
        deger=f"{kor_l:.2f} / {kor_s:.2f} derece",
        kaynak="ogrenme/metrik_sonuclari.json",
        desenler={
            f"{TEZ}/J_sonuclar.tex": [tr("36,43"), tr("31,43")],
            f"{MAK}/M6_TILT_EKSEN_SAYISI/02_MAKALE_AKTIF/M6_EN_v3.md":
                [r"36\.43", r"31\.43"],
        }))

    e_l = M["limulus"]["enerji"]["deger"]
    e_c = M["liftcruise"]["enerji"]["deger"]
    kayit.append(dict(
        ad="Referans misyon enerjisi",
        deger=f"{e_l:.1f} / {e_c:.1f} kWh",
        kaynak="ayni dosya",
        desenler={
            f"{TEZ}/J_sonuclar.tex": [tr("124,2")],
            f"{MAK}/M6_TILT_EKSEN_SAYISI/02_MAKALE_AKTIF/M6_EN_v3.md":
                [r"97\.5 kWh", r"124\.2 kWh"],
        }))

    # --- eklem yuku ve kapasiteler -----------------------------------
    kayit.append(dict(
        ad="RDP-IF tasarim kapasitesi",
        deger="29,0 kN",
        kaynak="2-CIZIM-MOTORU/geometri.py RDPIF satiri",
        desenler={
            f"{TEZ}/H_dinamik_model.tex": [r"28,6|28\{,\}6"],
            "CLAUDE.md": [r"29 kN"],
        }))

    kayit.append(dict(
        ad="Rotor solidite ve pal veteri",
        deger=f"{P['SIGMA']} / {P['PAL_VETERI']} m",
        kaynak="geometri.py P sozlugu, simulator turetmesiyle capraz "
               "kontrol edilir (dogrulama_capraz_kontrol.py)",
        desenler={
            f"{TEZ}/H_dinamik_model.tex": [tr("0,308"), tr("0,271")],
        }))

    # --- tez derleme sayilari ----------------------------------------
    if "sayfa" in T:
        kayit.append(dict(
            ad="Tez sayfa sayisi",
            deger=str(T["sayfa"]),
            kaynak="1-TEZ/v3-birlesik/main.pdf",
            desenler={"CLAUDE.md": [rf"{T['sayfa']} sayfa"]}))
    if "kaynak" in T:
        kayit.append(dict(
            ad="Kaynakca kunye sayisi",
            deger=str(T["kaynak"]),
            kaynak="main.bbl icindeki bibitem sayisi",
            desenler={"CLAUDE.md": [rf"{T['kaynak']}"],
                      "LIMULUS_Master_Tracker.xlsx": None}))
    kayit.append(dict(
        ad="Karar belgesi sayisi",
        deger=str(T["karar"]),
        kaynak="4-KARARLAR dizinindeki en buyuk numara",
        desenler={"CLAUDE.md": [rf"\*\*{T['karar']} karar\*\*"],
                  "4-KARARLAR/00-INDEKS.md": None}))

    # --- karar 48, tilt aktuatoru yedekliligi -------------------------
    kayit.append(dict(
        ad="Yedeklilik goreli dusus (4 eksen / 2 eksen)",
        deger=f"%{Y['limulus']['dusus']} / %{Y['ikili']['dusus']}",
        kaynak="cikti_asimetrik/k48_tilt_kilidi.json, kilitlenen indis "
               "uzerinden ortalanmis, arizali pod harici",
        desenler={
            f"{TEZ}/J_sonuclar.tex": [
                tr(f"{Y['limulus']['dusus']:.1f}".replace(".", ",")),
                tr(f"{Y['ikili']['dusus']:.1f}".replace(".", ","))],
            f"{TEZ}/01_cerceve.tex": [tr(f"{Y['limulus']['dusus']:.1f}".replace(".", ","))],
            f"{TEZ}/Z_sentez.tex": [tr(f"{Y['limulus']['dusus']:.1f}".replace(".", ","))],
            f"{MAK}/M6_TILT_EKSEN_SAYISI/02_MAKALE_AKTIF/M6_EN_v3.md":
                [str(Y["limulus"]["dusus"]), str(Y["ikili"]["dusus"])],
            f"{MAK}/M6_TILT_EKSEN_SAYISI/02_MAKALE_AKTIF/M6_TR_v3.md":
                [tr(f"{Y['limulus']['dusus']:.1f}".replace(".", ",")), tr(f"{Y['ikili']['dusus']:.1f}".replace(".", ","))],
            "4-KARARLAR/48-tilt-aktuatoru-yedeklilik-on-kaydi.md":
                [tr(f"{Y['limulus']['dusus']:.1f}".replace(".", ",")), tr(f"{Y['ikili']['dusus']:.1f}".replace(".", ","))],
            "CLAUDE.md": [tr(f"{Y['limulus']['dusus']:.1f}".replace(".", ","))],
        }))

    kayit.append(dict(
        ad="Yedeklilik kapanan sayilari (4 eksen kilitli)",
        deger=f"{Y['limulus']['kilit_kapanan']}/{Y['limulus']['kilit_denenen']}",
        kaynak="cikti_asimetrik/k48_tilt_kilidi.json",
        desenler={
            f"{TEZ}/J_sonuclar.tex":
                [rf"{Y['limulus']['kilit_kapanan']}/{Y['limulus']['kilit_denenen']}"],
            f"{MAK}/M6_TILT_EKSEN_SAYISI/02_MAKALE_AKTIF/M6_EN_v3.md":
                [rf"{Y['limulus']['kilit_kapanan']}/{Y['limulus']['kilit_denenen']}"],
            "4-KARARLAR/48-tilt-aktuatoru-yedeklilik-on-kaydi.md":
                [rf"{Y['limulus']['kilit_kapanan']}/{Y['limulus']['kilit_denenen']}"],
        }))

    kayit.append(dict(
        ad="Azami aktuator torku (alt sinir)",
        deger=f"{Y['azami_tork']} N m",
        kaynak="cikti_asimetrik/k48_tilt_kilidi.json, download bileseni "
               "yalniz, rotor moment katkilari YOK",
        desenler={
            f"{TEZ}/05_yuk_durumlari.tex": [tr(f"{Y['azami_tork']:.1f}".replace(".", ","))],
            f"{MAK}/M6_TILT_EKSEN_SAYISI/02_MAKALE_AKTIF/M6_EN_v3.md":
                [str(Y["azami_tork"])],
            "4-KARARLAR/48-tilt-aktuatoru-yedeklilik-on-kaydi.md":
                [tr(f"{Y['azami_tork']:.1f}".replace(".", ","))],
        }))

    return kayit


# =====================================================================
def denetle(kayit, ayrintili=False):
    hata, atlanan, denetlenen = 0, 0, 0
    for k in kayit:
        satirlar = []
        for dosya, desenler in k["desenler"].items():
            yol = os.path.join(_KOK, dosya)
            if desenler is None:
                satirlar.append(("BILGI", dosya, "elle denetlenir"))
                continue
            if not os.path.exists(yol):
                satirlar.append(("ATLANDI", dosya, "dosya yok"))
                atlanan += 1
                continue
            with open(yol, encoding="utf-8", errors="ignore") as f:
                metin = f.read()
            for d in desenler:
                denetlenen += 1
                if re.search(d, metin, re.S):
                    satirlar.append(("GECTI", dosya, d))
                else:
                    satirlar.append(("BULUNAMADI", dosya, d))
                    hata += 1

        kotu = [s for s in satirlar if s[0] in ("BULUNAMADI", "ATLANDI")]
        if kotu or ayrintili:
            print(f"\n{k['ad']}")
            print(f"  kanonik  {k['deger']}")
            print(f"  kaynak   {k['kaynak']}")
            for durum, dosya, d in satirlar:
                if durum == "GECTI" and not ayrintili:
                    continue
                print(f"  {durum:<12}{dosya}")
                if durum == "BULUNAMADI":
                    print(f"               aranan desen: {d}")
    return hata, atlanan, denetlenen


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ayrintili", action="store_true")
    ar = p.parse_args()

    print("PROJE GENELI SAYI DENETIMI")
    print("=" * 74)
    kayit = kayitlari_kur()
    hata, atlanan, denetlenen = denetle(kayit, ar.ayrintili)

    print("\n" + "=" * 74)
    print(f"KAPSAM  {len(kayit)} tasiyici sayi, {denetlenen} desen denetlendi")
    print("⚠️ Kayitta olmayan sayi denetlenmez. Yeni bir tasiyici sayi "
          "olculdugunde\n   bu betige kaydi eklenir, yoksa tuketicileri "
          "yine elle sayilir.")
    if hata:
        print(f"\nSONUC: {hata} UYUSMAZLIK. Hangi tarafin dogru oldugu "
              "SOYLENMEZ, kural G geregi karar Mete'dedir.")
        return 1
    print(f"\nSONUC: TUM KAYITLAR TUTARLI"
          + (f" ({atlanan} kalem atlandi)" if atlanan else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
