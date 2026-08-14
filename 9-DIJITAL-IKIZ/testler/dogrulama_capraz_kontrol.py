#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tasarim betigi ile dijital ikiz arasindaki eklem yuku capraz kontrolu.

Karar 16'nin uyguladigi kural: `2-CIZIM-MOTORU/geometri.py` ile `9-DIJITAL-IKIZ`
ayni buyuklugu iki yoldan uretiyorsa, ayristigi yerde biri yanlistir. O kayit
dokuz buyuklugun kontrol edildigini ve eklem yukunun listede olmadigini yazmis,
fakat eklem yuku testi hicbir zaman yazilmamisti (bkz. karar 16 Tadilat 1).
Bu dosya o eksigi kapatir.

Yontem: arka pod ultimate yuku IKI AYRI parametre kaynagindan ayni formulle
hesaplanir ve karsilastirilir. Kaynaklar `geometri.py` icindeki `G`/`P` sozlukleri
ile `9-DIJITAL-IKIZ/dinamik/konfigurasyon.py` icindeki `KONF` sozlugudur. Formul
ayni oldugu icin test parametrelerin ayrismasini yakalar, fizigi dogrulamaz.

    l_f = x_cg - x_rotor_on,  l_r = x_rotor_arka - x_cg
    T_arka = W * l_f / (2 (l_f + l_r))          # boyuna denge
    ultimate = T_arka * download * n_limit * j

⚠️ KAPASITELER BILINCLI OLARAK FARKLIDIR. Tez ve tasarim betigi 29 kN (tasarim
hedefi, karar 16), simulator 28 kN (muhafazakar, tamamlanmis kosular gecerli
kalsin diye). Test bu farki HATA saymaz, farkin hala bilincli oldugunu dogrular.

⚠️ ASIM YUZDESI: bu test kapali formulden %2,2 ve adim basina -0,043 buluyor,
karar 16 ise simulatorun hover trim noktasindan %2,3 ve -0,046 kaydetmisti. Fark
formul ile trim cozumu arasindaki farktir, ikisi de dogrudur ve birini digerine
UYDURMA. Testin isi mertebeyi ve isareti korumaktir, ondalik esitlemek degil.

Kosum:
    cd 9-DIJITAL-IKIZ && python3 testler/dogrulama_capraz_kontrol.py
Cikis kodu 0 ise tum kalemler gecti.
"""
import os
import sys

_BURASI = os.path.dirname(os.path.abspath(__file__))
_KOK = os.path.dirname(_BURASI)                       # 9-DIJITAL-IKIZ
_PROJE = os.path.dirname(_KOK)                        # LIMULUS-eVTOL
_CIZIM = os.path.join(_PROJE, "2-CIZIM-MOTORU")
sys.path.insert(0, os.path.join(_KOK, "dinamik"))

TOLERANS = 0.005          # bagil, %0,5. Iki hesap ayni kabullerden turuyor.
IKIZ_KAPASITE_BEKLENEN = 28.0      # kN, karar 16
TASARIM_KAPASITE_BEKLENEN = 29.0   # kN, karar 16


def ultimate_kN(mtow, g, x_on, x_arka, x_kanat, mac, cg_yuzde, dl, n, j):
    """Arka pod ultimate yuku, kN. Iki kaynak icin de ayni formul."""
    W = mtow * g
    le = x_kanat - 0.25 * mac
    xcg = le + cg_yuzde / 100.0 * mac
    lf, lr = xcg - x_on, x_arka - xcg
    T_arka = W * lf / (2.0 * (lf + lr))
    return T_arka * dl * n * j / 1e3


def tasarim_tarafi():
    """geometri.py sozluklerinden hesaplar. Dosya yoksa None doner."""
    if not os.path.isdir(_CIZIM):
        return None, None
    sys.path.insert(0, _CIZIM)
    try:
        import geometri as gm
    except Exception as e:                             # noqa: BLE001
        print(f"  UYARI  geometri.py ice aktarilamadi: {e}")
        return None, None
    G, P = gm.G, gm.P
    yuk = ultimate_kN(P["MTOW"], 9.81, G["X_ROTOR_ON"], G["X_ROTOR_ARKA"],
                      G["X_KANAT"], G["VECHILE"], G["CG_MAC_YUZDE"],
                      1.036, 2.5, 1.5)
    # kapasite betigin kendi kaynak metninden okunur, kopyalanmaz
    kap = None
    with open(os.path.join(_CIZIM, "geometri.py"), encoding="utf-8") as f:
        for satir in f:
            if satir.strip().startswith("RDPIF ="):
                kap = float(satir.split("=")[1].split("#")[0])
                break
    return yuk, kap


def ikiz_tarafi():
    import konfigurasyon as K
    k = K.KONF
    yuk = ultimate_kN(k["MTOW"], k["G"], k["X_ROTOR_ON"], k["X_ROTOR_ARKA"],
                      k["X_KANAT"], k["MAC"], k["CG_MAC_YUZDE"],
                      k["DOWNLOAD"], k["N_LIMIT"], k["J_EMNIYET"])
    return yuk, k["RDPIF_DUSEY"] / 1e3


def _rotor_pali() -> int:
    """Solidite ve pal veteri iki kaynakta ayni mi. Hata sayisini doner.

    Simulator ikisini de tasarim noktasindan TURETIR, tasarim betigi ise
    SABIT olarak tasir. Sabit bir deger turetmeyle birlikte kaymaz, yani
    rotor capi, devir ya da hover itkisi degistiginde simulator yeni sayiyi
    uretir ve betik eski sayida kalir. Bu iki kalem o ayrismayi yakalar.
    """
    if not os.path.isdir(_CIZIM):
        print("  ATLANDI  rotor pali — 2-CIZIM-MOTORU erisilebilir degil")
        return 0
    sys.path.insert(0, _CIZIM)
    try:
        import geometri as gm
        from rotor import Rotor
    except Exception as e:                                 # noqa: BLE001
        print(f"  UYARI  rotor pali karsilastirilamadi: {e}")
        return 0

    G, P = gm.G, gm.P
    r = Rotor(D=G["D_ROTOR"], N_PAL=P["N_PAL"], RPM=P["RPM"],
              CTs_tasarim=P["CTS_TASARIM"])

    hata = 0
    for ad, betik, ikiz, birim, tol in (
            ("solidite sigma", P["SIGMA"], r.sigma, "", 5e-4),
            ("pal veteri", P["PAL_VETERI"], r.pal_veteri, " m", 5e-4)):
        ok = abs(betik - ikiz) <= tol
        hata += 0 if ok else 1
        print(f"  {'GECTI ' if ok else 'HATA  '} {ad:<16}"
              f"   betik {betik:.4f}{birim} · ikiz {ikiz:.4f}{birim}"
              f"   (fark {abs(betik - ikiz):.5f}, tolerans {tol})")
        if not ok:
            print("     ⚠️ Simulator turetiyor, betik sabit tasiyor. Once "
                  "hangisinin girdisi degisti diye bakilir, sayilar "
                  "birbirine UYDURULMAZ.")
    return hata


def main():
    print("CAPRAZ KONTROL — eklem yuku, tasarim betigi ile dijital ikiz")
    print("=" * 70)
    hata, atlanan = 0, 0

    t_yuk, t_kap = tasarim_tarafi()
    i_yuk, i_kap = ikiz_tarafi()

    # --- 1) tasinan yuk ayni mi ------------------------------------
    if t_yuk is None:
        print("  ATLANDI  tasinan yuk — 2-CIZIM-MOTORU erisilebilir degil")
        atlanan += 1
    else:
        fark = abs(t_yuk - i_yuk) / i_yuk
        ok = fark <= TOLERANS
        hata += 0 if ok else 1
        print(f"  {'GECTI ' if ok else 'HATA  '} tasinan ultimate yuk"
              f"   tasarim {t_yuk:.2f} kN · ikiz {i_yuk:.2f} kN"
              f"   (bagil fark %{fark * 100:.2f})")

    # --- 2) tasarim kapasitesi 29 kN mi ----------------------------
    if t_kap is None:
        print("  ATLANDI  tasarim kapasitesi — RDPIF satiri okunamadi")
        atlanan += 1
    else:
        ok = abs(t_kap - TASARIM_KAPASITE_BEKLENEN) < 1e-9
        hata += 0 if ok else 1
        print(f"  {'GECTI ' if ok else 'HATA  '} tasarim kapasitesi"
              f"   {t_kap:.2f} kN (beklenen {TASARIM_KAPASITE_BEKLENEN:.2f},"
              f" karar 16 revizyonu)")

    # --- 3) simulator kapasitesi 28 kN'da mi kaldi -----------------
    ok = abs(i_kap - IKIZ_KAPASITE_BEKLENEN) < 1e-9
    hata += 0 if ok else 1
    print(f"  {'GECTI ' if ok else 'HATA  '} simulator kapasitesi"
          f"   {i_kap:.2f} kN (beklenen {IKIZ_KAPASITE_BEKLENEN:.2f},"
          f" karar 16 geregi muhafazakar)")
    if not ok:
        print("     ⚠️ Bu deger degistiyse tamamlanmis 25 kosu gecersizdir."
              " Karar 16'yi okumadan duzeltme.")

    # --- 4) iki katmanin farki hala ayni yonde mi ------------------
    if t_kap is not None:
        ok = t_kap > i_kap
        hata += 0 if ok else 1
        print(f"  {'GECTI ' if ok else 'HATA  '} katman farkinin yonu"
              f"   tasarim {t_kap:.2f} > simulator {i_kap:.2f} kN"
              " (siki kisitla egitilen politika gevsek kisitta gecerlidir)")

    # --- 5) simulatorde asim hala ceza uretiyor mu -----------------
    asim = max(0.0, (i_yuk - i_kap) / i_kap)
    ok = asim > 0
    hata += 0 if ok else 1
    print(f"  {'GECTI ' if ok else 'HATA  '} hover asimi"
          f"   %{asim * 100:.1f} · adim basina ceza -{2.0 * asim:.3f}"
          " (kosularin egitildigi kosul)")

    # --- 6) tasarim tarafinda marj pozitif mi ---------------------
    if t_kap is not None and t_yuk is not None:
        marj = (t_kap / t_yuk - 1.0) * 100
        ok = marj > 0
        hata += 0 if ok else 1
        print(f"  {'GECTI ' if ok else 'HATA  '} tasarim marji"
              f"   %{marj:.1f} (dar, RDP-IF detay FEM dogrulamali)")

    # --- 7, 8) rotor pali: solidite ve pal veteri -----------------
    # 09.08.2026'da eklendi. Iki sayi simulatorde hover blade loading
    # kosulundan turetiliyor, tasarim betiginde ise 09.08'e kadar HIC
    # yoktu ve sonradan sabit olarak yazildi. Sabit yazilan bir deger
    # turetmeyle birlikte kaymaz, o yuzden bu iki kalem gerekli.
    hata += _rotor_pali()

    print("=" * 70)
    if hata == 0:
        print(f"SONUC: TUM KALEMLER GECTI"
              + (f" ({atlanan} kalem atlandi)" if atlanan else ""))
    else:
        print(f"SONUC: {hata} KALEM HATALI")
    return 0 if hata == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
