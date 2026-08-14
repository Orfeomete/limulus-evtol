#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARAR 47 SONDASI — sonuc toplayici.

Ön kayit `4-KARARLAR/47-ogrenilebilirlik-sondasi-on-kaydi.md`. Bu betik yalniz
o ön kaydin sordugu sayilari cikarir ve karar kurallarini UYGULAR, hicbir esik
ya da yorum eklemez.

⚠️ BIRINCIL METRIK GOREV ADIDIR, SEVIYE INDISI DEGIL. Ince mufredatta indisler
ikiden sonra bir kayiyor, yani ayni indis iki kurguda ayni gorevi gostermiyor.
Betik seviye indisini gorev adina cevirir ve karsilastirmayi ad uzerinden yapar.

⚠️ KURAL 5. Sekiz kosunun tamami tamamlanmadiysa kac kosunun bittigi ve hangi
hucrenin eksik kaldigi yazilir. Eksik hucre SESSIZCE ATLANMAZ, bu betik eksik
hucreyi cikti tablosunda ayri bir satir olarak gosterir.

Kosum
    cd 9-DIJITAL-IKIZ && python3 testler/topla_k47.py
"""
import glob
import json
import os
import sys

_BURASI = os.path.dirname(os.path.abspath(__file__))
_KOK = os.path.dirname(_BURASI)
KOSU = os.path.join(_KOK, "ogrenme", "kosular_k47")

# Ön kayittaki 2x2 tasarim. Sirasi degistirilmez.
HUCRE = {
    "A": dict(log_std0=-1.5, ince=False, ad="taban"),
    "B": dict(log_std0=-0.5, ince=False, ad="geniş keşif"),
    "C": dict(log_std0=-1.5, ince=True, ad="ince müfredat"),
    "D": dict(log_std0=-0.5, ince=True, ad="ikisi birlikte"),
}
TOHUMLAR = (0, 1)
BUTCE = 300_000

# ⚠️ Mufredat ADLARI, ortam.py ile ayni sirada olmali. Elle yazilmasinin
# gerekcesi, sonda kosularinin ortam degiskeniyle iki farkli mufredat
# kullanmasi ve gunlukte yalniz indisin bulunmasidir.
TABAN = ("hover", "dikey", "gecis", "cruise", "gust_gecis", "oei_hover")
INCE = ("hover", "dikey", "gecis_yarim", "gecis", "cruise", "gust_gecis",
        "oei_hover")
# Ilerleme sirasi, iki mufredatin birlesimi. Karsilastirma bu siraya gore.
SIRA = ("hover", "dikey", "gecis_yarim", "gecis", "cruise", "gust_gecis",
        "oei_hover")


def gorev_adi(hucre: str, seviye: int) -> str:
    ad = INCE if HUCRE[hucre]["ince"] else TABAN
    return ad[seviye] if 0 <= seviye < len(ad) else f"?{seviye}"


def kosu_oku(hucre: str, tohum: int) -> dict:
    """Bir kosunun son durumunu doner. Tamamlanmadiysa tamam=False."""
    d = os.path.join(KOSU, hucre)
    tam = glob.glob(os.path.join(d, f"limulus_t{tohum}_gunluk.json"))
    ara = os.path.join(d, f"limulus_t{tohum}_ara_durum.json")
    if tam:
        with open(tam[0], encoding="utf-8") as f:
            g = json.load(f)["gunluk"]
        son = g[-1]
        return dict(tamam=True, adim=son["adim"], seviye=son["seviye"],
                    odul=son.get("odul"),
                    bolum_uz=son.get("ort_bolum_uzunlugu"),
                    en_ust_seviye=max(k["seviye"] for k in g))
    if os.path.exists(ara):
        with open(ara, encoding="utf-8") as f:
            a = json.load(f)
        return dict(tamam=False, adim=a.get("adim"), seviye=a.get("seviye"),
                    odul=None, bolum_uz=None, en_ust_seviye=a.get("seviye"))
    return dict(tamam=False, adim=None, seviye=None, odul=None,
                bolum_uz=None, en_ust_seviye=None)


def main():
    if not os.path.isdir(KOSU):
        raise SystemExit(f"sonda dizini yok: {KOSU}")

    kayit, biten = {}, 0
    for h in HUCRE:
        for t in TOHUMLAR:
            r = kosu_oku(h, t)
            kayit[(h, t)] = r
            biten += 1 if r["tamam"] else 0

    print("KARAR 47 SONDASI — SONUC TOPLAMA")
    print("=" * 78)
    print(f"KURAL 5 — sekiz kosunun {biten} tanesi tamamlandi\n")
    print(f"{'hucre':<7}{'kurgu':<16}{'tohum':>6}{'adim':>10}"
          f"{'en ust gorev':>16}{'durum':>10}")
    print("-" * 78)
    for h, ay in HUCRE.items():
        for t in TOHUMLAR:
            r = kayit[(h, t)]
            g = (gorev_adi(h, r["en_ust_seviye"])
                 if r["en_ust_seviye"] is not None else "—")
            ad = f"{r['adim']:,}" if r["adim"] else "—"
            print(f"{h:<7}{ay['ad']:<16}{t:>6}{ad:>10}{g:>16}"
                  f"{'tamam' if r['tamam'] else 'EKSIK':>10}")

    eksik = [f"{h} t{t}" for (h, t), r in kayit.items() if not r["tamam"]]
    if eksik:
        print(f"\n⚠️ EKSIK KOSULAR ({len(eksik)}): {', '.join(eksik)}")
        print("   Ön kayit kural 5 geregi bu satirlar kayda yazilir, "
              "atlanmaz.")

    # --- KURAL 2 ---
    def en_iyi(h):
        s = [kayit[(h, t)]["en_ust_seviye"] for t in TOHUMLAR
             if kayit[(h, t)]["en_ust_seviye"] is not None]
        if not s:
            return None
        return max(SIRA.index(gorev_adi(h, x)) for x in s)

    def tumu(h):
        s = [kayit[(h, t)]["en_ust_seviye"] for t in TOHUMLAR
             if kayit[(h, t)]["tamam"]]
        if len(s) < len(TOHUMLAR):
            return None
        return [SIRA.index(gorev_adi(h, x)) for x in s]

    taban = en_iyi("A")
    print("\nKURAL 2 — bir hucre tabani gecti mi")
    print("   Sart: iki tohumun IKISI de taban hucrenin EN IYI tohumundan "
          "ileri bir goreve varmali")
    if taban is None:
        print("   UYGULANAMAZ, taban hucrenin hicbir kosusu okunamadi")
    else:
        print(f"   Taban (A) en iyi tohum: {SIRA[taban]}")
        for h in ("B", "C", "D"):
            v = tumu(h)
            if v is None:
                print(f"   {h}: UYGULANAMAZ, iki tohum tamamlanmadi")
                continue
            ok = all(x > taban for x in v)
            print(f"   {h}: tohumlar {[SIRA[x] for x in v]} -> "
                  f"{'GECTI' if ok else 'gecmedi'}")

    # --- KURAL 3 ve 4 ---
    varan = [f"{h} t{t}" for (h, t), r in kayit.items()
             if r["en_ust_seviye"] is not None
             and SIRA.index(gorev_adi(h, r["en_ust_seviye"]))
             >= SIRA.index("gecis")]
    print("\nKURAL 3 ve 4 — `gecis` gorevine ulasan kosu")
    if not varan:
        print("   ULASAN YOK. Kural 3 yururluge girer, dondurulmus cumle "
              "yazilir.")
    else:
        print(f"   ULASAN: {', '.join(varan)}")
        print("   Kural 4 geregi sonuc KESIFSEL hipotez olarak kaydedilir, "
              "hukum yazilmaz.")

    print("=" * 78)
    if biten < len(HUCRE) * len(TOHUMLAR):
        print("SONDA HENUZ BITMEDI. Yukaridaki tablo ara durumdur, "
              "SONUC BOLUMU YAZILMAZ.")
        return 1
    print("Sonda tamamlandi, sonuc bolumu yazilabilir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
