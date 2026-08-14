#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIMULUS DIJITAL IKIZ — KONFIGURASYON

Tek dogruluk kaynagi 2-CIZIM-MOTORU/geometri.py. Bu dosya oradan okur ve
dinamik model icin gereken ek buyuklukleri ekler. Tezden hicbir sayi elle
kopyalanmaz.

Tezde bulunmayan her deger VARSAYIMLAR sozlugunde acikca isaretlenir.
LIMULUS_DURUSTLUK_CERCEVESI.md §3 bunu zorunlu kiliyor.
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field

# --- geometri.py'yi bul ve oku ---------------------------------------
_BURASI = os.path.dirname(os.path.abspath(__file__))
_CIZIM = os.path.normpath(os.path.join(_BURASI, "..", "..", "2-CIZIM-MOTORU"))
if _CIZIM not in sys.path:
    sys.path.insert(0, _CIZIM)

try:
    from geometri import G as _G, P as _P            # type: ignore
    KAYNAK = os.path.join(_CIZIM, "geometri.py")
except ImportError:                                   # pragma: no cover
    raise SystemExit(
        "geometri.py bulunamadi. Beklenen konum: " + _CIZIM + "\n"
        "Dijital ikiz tek dogruluk kaynagindan beslenir, yedek deger tutmaz."
    )


# =====================================================================
# TEZDEN GELEN DEGERLER
# =====================================================================
def _tezden() -> dict:
    """geometri.py'nin G ve P sozluklerinden dinamik modelin ihtiyaci."""
    return dict(
        # --- kutle ve atalet ---
        MTOW=float(_P["MTOW"]),
        # atalet matrisi Bolum 11, Class II. geometri.py'de yok, tezden.
        I_xx=578.0, I_yy=5284.0, I_zz=5301.0, I_xz=555.0,

        # --- geometri ---
        X_ROTOR_ON=_G["X_ROTOR_ON"],
        X_ROTOR_ARKA=_G["X_ROTOR_ARKA"],
        Y_MODUL=_G["Y_MODUL"],
        Z_MODUL=_G["Z_MODUL"],
        X_KANAT=_G["X_KANAT"],
        # Govde toplam uzunlugu. 09.08.2026'da eklendi, yalniz donme
        # kuplaji bayragi (karar 46) govde yan alaninin basinc merkezini
        # buradan turetiyor. Tasarim betiginden gelir, kopyalanmaz.
        L_TOTAL=_G["L_TOTAL"],
        MAC=_G["VECHILE"],
        S_KANAT=_G["S_KANAT"],
        AR=_G["AR"],
        SPAN=_G["SPAN"],
        D_ROTOR=_G["D_ROTOR"],
        CG_MAC_YUZDE=_G["CG_MAC_YUZDE"],
        NP_MAC_YUZDE=_G["NP_MAC_YUZDE"],

        # --- aerodinamik (Bolum 4) ---
        CD0=0.027, OSWALD=0.82, CL_MAX=1.50,

        # --- rotor (Bolum 4) ---
        FOM=0.75, DOWNLOAD=1.036, N_PAL=5,
        RPM=float(_P["RPM"]),

        # --- itki sistemi (Bolum 9) ---
        P_MOTOR_SUREKLI=134e3, P_MOTOR_OEI=160e3, P_MOTOR_PIK=190e3,
        N_MOTOR_POD=2, ETA_AKT=0.90, P_OTEL=12e3,
        E_BATT=float(_P["E_BATT"]) * 3.6e6,        # kWh -> J (kullanilabilir)

        # --- ayri cruise itki birimi (yalniz lift+cruise varyanti) ---
        # ⚠️ VARSAYIM. Tezde bu varyant yok, karsilastirma icin kuruldu.
        CRUISE_ITKI_P=180e3, CRUISE_ITKI_ETA=0.80, CRUISE_ITKI_KUTLE=62.0,

        # --- tilt ---
        THETA_MIN=0.0, THETA_MAX=math.radians(float(_G["THETA_MAX"])),
        THETA_CRUISE=math.radians(float(_G["THETA_CRUISE"])),

        # --- gorev ---
        V_CRUISE=float(_P["V_CRUISE_MS"]),

        # --- yapisal limitler (Bolum 8, 13) ---
        # ⚠️ RDPIF_DUSEY BILINCLI OLARAK 28 kN, DEGISTIRME. Tez Bolum 8.1'de
        # kapasite hedefi 29 kN'a revize edildi (karar 16), simulator ise
        # muhafazakar deger olan 28 kN'da BIRAKILDI. Iki gerekce:
        #   1. Asim, hover triminde adim basina -0,046 ceza uretiyor. 29 kN
        #      yapmak bu cezayi sifirlar, yani fizigi degistirir ve tamamlanmis
        #      25 kosuyu (20 kosular_v2 + 5 kosular_lc) gecersiz kilar.
        #   2. Daha siki bir kisitla egitilmis politikanin gevsetilmis kisit
        #      altinda da gecerli olmasi beklenir, tersi gecerli degildir.
        # Tezi okuyup "29 olmali" diye duzeltmek isteyen icin: karar 16'yi oku.
        N_LIMIT=2.5, J_EMNIYET=1.5, RDPIF_DUSEY=28e3,
    )


# =====================================================================
# TEZDE OLMAYAN, MODELDE ILK KEZ TANIMLANAN DEGERLER
# =====================================================================
VARSAYIMLAR: dict[str, str] = {
    "CRUISE_ITKI_P": "Lift+cruise varyantinin ayri itici birimi 180 kW "
        "surekli guc. Tezde bu varyant yok, kiyas icin kuruldu. "
        "⚠️ ILK DEGER 120 kW IDI VE YETMEDI (4-KARARLAR/32): trim cozucu "
        "yedi hizin besinde cozum bulamiyordu, cunku 68,9 m/s'de gereken "
        "~1840 N itki icin 120 kW yalniz 1393 N verebiliyor. Deger, GEREKEN "
        "itkinin olculmesiyle yeniden turetildi — 180 kW yedi hizin "
        "yedisinde trim veren en kucuk degerdir. Rakip mimariyi ayakta "
        "tutmak icin buyutuldu, yani karsilastirma LIMULUS aleyhine "
        "sikilastirildi. VARSAYIM.",
    "CRUISE_ITKI_ETA": "Itici birim pervane verimi 0,80. Tipik sabit "
        "hatveli itici pervane degeri. Kaynak yok, VARSAYIM.",
    "CRUISE_ITKI_KUTLE": "Itici birim kuru kutlesi 62 kg (motor + pervane "
        "+ yapisal arayuz). 180 kW birim icin, 45 kg/120 kW oranı "
        "korunarak olceklendi (0,375 kg/kW). Bileşen bazinda kaba tahmin. "
        "VARSAYIM.",
    "CL_ALFA":
        "Kanat tasima egimi 4,90 1/rad. Tezde yok. Ince kanat teorisi "
        "2*pi*AR/(AR+2) ile AR=11 icin turetildi.",
    "CM0":
        "Kanat sifir-tasima pitch momenti 0,0. Tezde profil tanimlanmadigi "
        "icin simetrik/reflex kabul edildi. Trim sonucunu dogrudan etkiler.",
    "ALFA_STALL":
        "Stall hucum acisi bagimsiz bir varsayim DEGILDIR, CL_MAX/CL_ALFA "
        "oranindan turetilir (17,54 derece). Ayri deger verilirse "
        "aerodinamik.Kanat hata firlatir. Ilk surumde 16 derece verilmis "
        "ve tasima egrisinde sicrama olusmustu.",
    "THETA_HIZ":
        "Tilt aktuatoru oran limiti 15 derece/s. Tezde yok. Tipik "
        "elektromekanik aktuator degeri.",
    "TAU_MOTOR":
        "Motor itki tepki zaman sabiti 0,08 s. Tezde yok. Aksiyel-aki "
        "PMSM + inverter icin tipik.",
    "Z_POD_CG":
        "Podlarin CG duzlemine gore dusey kacikligi 0,0 m. Tezde CG'nin "
        "dusey konumu verilmemis.",
    "K_GOVDE_Y":
        "Govde yanal kuvvet katsayisi 0,55. Tezde yok. Karapas yan alani "
        "uzerinden mertebe tahmini.",
    "SENSOR":
        "Sensor gurultu ve gecikme degerleri tezde yok. Ticari taktik "
        "sinif IMU ve GNSS mertebesinde secildi. sensor.py'de listeli.",
    "GUST":
        "Dryden turbulans olcek ve siddet degerleri MIL-HDBK-1797 "
        "(1997) dusuk irtifa modelinden. Tezde yok. Belge 2004'te "
        "yururlukten kaldirildi, oncesi MIL-STD-1797A (1990).",
    "CTS_TAVAN":
        "Rotor itki tavani icin blade loading ust siniri 0,16. "
        "DOGRULANMADI. Tasarim degeri 0,14 NASA calismalarindan "
        "dogrulanabiliyor ama tavan icin birincil kaynak bulunamadi. "
        "Johnson & Silva (2022) 90 knot'ta 0,12 gibi daha dusuk bir "
        "sinir veriyor, dolayisiyla 0,16 iyimser olabilir. "
        "Bkz. rotor.py modul basligi.",
}

_EK = dict(
    CL_ALFA=4.90,
    CM0=0.0,
    THETA_HIZ=math.radians(15.0),
    TAU_MOTOR=0.08,
    Z_POD_CG=0.0,
    K_GOVDE_Y=0.55,
    S_GOVDE_YAN=4.4,          # m2, karapas yan izdusumu (L_GOVDE x H_GOVDE)
)


def konf() -> dict:
    """Birlesik konfigurasyon sozlugu."""
    k = _tezden()
    k.update(_EK)
    k["RHO0"] = 1.225
    k["G"] = 9.81
    return k


KONF = konf()


# =====================================================================
# KARSILASTIRMA KONFIGURASYONLARI  (4-KARARLAR/09 §4)
# =====================================================================
@dataclass(frozen=True)
class Varyant:
    """Rakip konfigurasyonlar ayri model degil, ayni simulatorun kisitidir.

    Aerodinamik, kutle, guc sistemi ve gorev profili sabit kalir. Yalniz
    tilt eksenlerinin bagimsizligi degisir. Boylece karsilastirmada tek
    degisken kontrol mimarisidir.
    """
    ad: str
    aciklama: str
    # tilt serbestlik derecesi -> pod eslemesi. Ayni gruptaki podlar
    # ayni tilt acisini paylasir.
    tilt_gruplari: tuple[tuple[int, ...], ...]
    # sabit tilt acisi (radyan) ya da None (serbest)
    sabit_tilt: float | None = None
    # ayri cruise itki birimi var mi (lift + cruise mimarisi)
    ayri_cruise_itki: bool = False
    karsiligi: str = ""

    @property
    def n_tilt(self) -> int:
        return 0 if self.sabit_tilt is not None else len(self.tilt_gruplari)


VARYANTLAR: dict[str, Varyant] = {
    "limulus": Varyant(
        ad="LIMULUS (tam)",
        aciklama="Dort bagimsiz tilt ekseni. Tezin onerdigi mimari.",
        tilt_gruplari=((0,), (1,), (2,), (3,)),
        karsiligi="bu calismanin onerisi",
    ),
    "ikili": Varyant(
        ad="Ikili tilt",
        aciklama="On cift ve arka cift ayri tilt eder. Iki eksen.",
        tilt_gruplari=((0, 1), (2, 3)),
        karsiligi="ara durum",
    ),
    "senkron": Varyant(
        ad="Senkron tilt",
        aciklama="Dort pod ayni acida tilt eder. Tek eksen.",
        tilt_gruplari=((0, 1, 2, 3),),
        karsiligi="V-22 Osprey, Joby S4 sinifi",
    ),
    "liftcruise": Varyant(
        ad="Lift + cruise",
        aciklama="Tilt yok. Rotorlar yalniz dusey, ayri bir cruise itki "
                 "birimi var. Tilt ekseni sifir.",
        tilt_gruplari=(),
        sabit_tilt=0.0,
        ayri_cruise_itki=True,
        karsiligi="Beta Alia, Archer Midnight sinifi",
    ),
}


def varyant(ad: str) -> Varyant:
    if ad not in VARYANTLAR:
        raise KeyError(f"bilinmeyen varyant {ad!r}. Secenekler: "
                       + ", ".join(VARYANTLAR))
    return VARYANTLAR[ad]


# =====================================================================
def ozet() -> str:
    k = KONF
    mac = k["MAC"]
    le = k["X_KANAT"] - 0.25 * mac
    xcg = le + k["CG_MAC_YUZDE"] / 100 * mac
    xnp = le + k["NP_MAC_YUZDE"] / 100 * mac
    s = [
        f"kaynak            {KAYNAK}",
        f"MTOW              {k['MTOW']:.0f} kg",
        f"agirlik merkezi   {xcg:.3f} m  ({k['CG_MAC_YUZDE']:.1f}% MAC)",
        f"notr nokta        {xnp:.3f} m  ({k['NP_MAC_YUZDE']:.1f}% MAC)",
        f"statik marj       {(xnp - xcg) / mac * 100:+.1f}%",
        f"rotor istasyonu   {k['X_ROTOR_ON']:.2f} / {k['X_ROTOR_ARKA']:.2f} m",
        f"varsayim sayisi   {len(VARSAYIMLAR)} (tezde olmayan deger)",
        f"varyant sayisi    {len(VARYANTLAR)}",
    ]
    return "\n".join(s)


if __name__ == "__main__":
    print(ozet())
    print("\nVARSAYIMLAR (tezde yok, modelde ilk kez tanimlandi)")
    for ad, not_ in VARSAYIMLAR.items():
        print(f"  {ad:<12} {not_}")
