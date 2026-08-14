#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROTOR MODELI — momentum teorisi + egik akis duzeltmesi

Tezin Bolum 4'teki modeli hover icindir. Dijital ikiz gecis rejimini de
kapsamak zorunda oldugu icin genel indukleme hizi denklemi kullanilir.

Hover     v_i = sqrt(T / (2 rho A))
Genel     v_i^2 = ... Glauert'in kapali olmayan bagintisi, iteratif cozulur
Eksenel   v_i = -V/2 + sqrt((V/2)^2 + T/(2 rho A))

Egik akis (tilt gecisinde rotor akisa egik calisir) Glauert bagintisiyla
ele alinir. Bu tezde YOK, dijital ikizin genislettigi yerdir ve
LIMULUS_DURUSTLUK_CERCEVESI §3 uyarinca "analitik tahmin" seviyesindedir.

Koaksiyel duzen: iki pal seti tek disk olarak modellenir.

GUC AYRISTIRMASI (v0.2, ileri ucus icin zorunlu)
Tezin FoM = 0,75 degeri hover icin toplu bir kayip carpanidir. Ileri
ucusta indukleme gucu duserken profil gucu mu ile hizla buyudugu icin
tek carpan yetmez. Guc iki terime ayrilir.

    P = T * V_dik  +  kappa * T * v_i  +  P_profil(mu)
    P_profil = (sigma cd0 / 8) rho A V_uc^3 (1 + 4,65 mu^2)

Birinci terim faydali itki gucudur ve kayipsizdir. kappa YALNIZ
indukleme terimine uygulanir. Ilk surumde kappa ikisine birden
uygulanmisti, bu cruise'da pervane verimini 0,62'ye dusuruyordu
(tezin kabulu 0,80). Duzeltildi.

kappa hover'da tezin 913 kW sonucunu BIREBIR verecek sekilde
kalibre edilir, dolayisiyla tezle celismez. mu bagimliligi modelin
genislettigi yerdir.

Bu ayristirma olmadan cozucu, rotorlari ileri ucusta neredeyse
bedava bir tasima kaynagi gibi kullanip fiziksel olmayan bir trim
noktasi buluyordu (tilt 12 derece, guc 193 kW). Hata boyle yakalandi.

SOLIDITE. Tezde pal veteri ya da solidite verilmiyor. Hover blade
loading degerinin C_T/sigma = 0,14 olmasi kosulundan sigma = 0,308
turetilir. Bu deger ducted fan ve rim-drive araliginda (0,3-0,5)
kalir, helikopter araliginda (0,05-0,12) degil. Rim-drive mimarisi
zaten yuksek soliditeli bir fan oldugundan tutarlidir. C_T = 0,043
tek basina yuksek gorunur, dusuk pal ucu hizi (153 m/s, Mach 0,45)
ile birlikte okunmalidir.

⚠️ IKI SAYININ DOGRULANMA DURUMU FARKLIDIR, karistirilmasin.

  CTs_tasarim = 0,14   DOGRULANMIS TASARIM DEGERI. NASA rotorcraft
      tasarim calismalari bu degeri acikca taban tasarim parametresi
      olarak vermektedir (Yeo & Johnson 2006, Johnson/Yeo/Acree 2007;
      LCTR tiltrotor hover noktalari 0,149 ve 0,156). Kaynak
      kaynakcada yeo2006 ve johnson2022 anahtarlariyla.

  CTs_tavan = 0,16     TASARIM PAYI SECIMI, atifli sinir DEGIL.
      09.08.2026'da sistematik literatur taramasi yapildi ve deger
      DOGRULANAMADI. Tam kayit `4-KARARLAR/44`. Taramanin bulduklari:

        Bousman NASA/TM-2000-209601  0,18   hover tavani, M_T 0,65, SC1095
        Acree/Yeo/Sinsay 2008        0,166  LCTR2'nin GERCEKLESEN hover
                                            tasarim noktasi, solidite 0,130
        Blaesser NASA/TM-20240002116 0,12   proprotor ust siniri (Leishman)
        Johnson & Silva 2022         0,12   flapping rotor, 90 kt, mu 0,36
        NDARC NASA/TP-20220000355    YOK    NASA'nin kendi kodu bu buyukluk
                                            icin sayisal ONTANIM VERMIYOR

      Hicbir yazar 0,16'yi stall siniri olarak vermiyor. Guvenilir bant
      0,12-0,18 ve 0,16 bandin icinde. NDARC satiri en guclu kanit,
      kanonik bir tavan olsaydi NASA'nin kodu onu tasirdi.

      ⚠️ DEGERI DEGISTIRMEYIN. Degistirmek icin de bir kaynak yok ve 25
      tamamlanmis kosu bu degerle egitildi. Degisen sey degerin STATUSU,
      sayinin kendisi degil.

      Savunulabilir taraf bir kimlikten geliyor, atiftan degil. Pal
      yuklemesi pal boyunca integre edilmis kesit tasima katsayisidir
      (Bousman ve Blaesser ikisi de yaziyor), yani C_T/sigma ~ c_l/6.
      0,16 ortalama c_l = 0,96 istiyor, SC1095'in azamisi 1,1 ve bu
      tezin pal ucu Mach'i 0,45 ile Bousman'in 0,65'inin altinda, yani
      kesit stall marji Bousman'in durumundan GENIS.

      ⚠️ UCUNCU BIR VARSAYIM DAHA VAR ve taramada ortaya cikti. Solidite
      0,3 mertebesindeki ducted ya da rim-drive fanlar icin stall sinirli
      pal yuklemesi veren HICBIR birincil kaynak yok, ducted fan
      literaturu bu metrigi kullanmiyor. Helikopter rotorundan turetilmis
      bir tavani bu konfigurasyona tasimak, tavanin kendi degerinden
      BAGIMSIZ olarak ayri bir varsayimdir.

      Duyarlilik: tavan 0,14'e cekilirse hover itki marji %14'ten sifira
      iner, 0,12'ye (taramanin en muhafazakar degeri) cekilirse tasarim
      noktasi sinirin ALTINDA kalir.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class Rotor:
    D: float                       # m, disk capi
    FOM: float = 0.75              # figure of merit (hover, tezden)
    N_PAL: int = 5
    RPM: float = 1044.0
    sigma: float | None = None     # solidite. None -> tasarim noktasindan turetilir
    cd0_pal: float = 0.010         # pal profil suruklemesi   (VARSAYIM)
    mu_max: float = 0.55           # ilerleme orani siniri     (VARSAYIM)
    CTs_tasarim: float = 0.14      # hover blade loading (NASA tasarim degeri)
    CTs_tavan: float = 0.16        # ⚠️ VARSAYIM, dogrulanmadi. Bkz. modul basligi
    T_kalibre: float = 7622.0      # kappa kalibrasyonu icin hover itkisi
    rho_kalibre: float = 1.225

    def __post_init__(self):
        self.A = math.pi * self.D ** 2 / 4.0
        self.omega = self.RPM * 2.0 * math.pi / 60.0
        self.V_uc = self.omega * self.D / 2.0        # pal ucu hizi

        if self.sigma is None:
            CT = self.T_kalibre / (self.rho_kalibre * self.A * self.V_uc ** 2)
            self.sigma = CT / self.CTs_tasarim
        self.pal_veteri = self.sigma * math.pi * (self.D / 2) / self.N_PAL

        # --- kappa kalibrasyonu: hover'da toplam guc tezin FoM'i ile ayni
        vh = math.sqrt(self.T_kalibre / (2 * self.rho_kalibre * self.A))
        P_ideal = self.T_kalibre * vh
        P_tez = P_ideal / self.FOM
        self.P0_ref = (self.sigma * self.cd0_pal / 8.0) * \
            self.rho_kalibre * self.A * self.V_uc ** 3
        self.kappa = (P_tez - self.P0_ref) / P_ideal
        if self.kappa <= 1.0:
            raise ValueError(
                f"kappa = {self.kappa:.3f} <= 1. Profil gucu, FoM'un izin "
                f"verdigi toplam kayiptan buyuk. sigma ya da cd0 gozden "
                f"gecirilmeli.")

    # ---------------------------------------------------------------
    def mu(self, V: float, alfa_disk: float) -> float:
        """Ilerleme orani. Disk duzlemindeki hiz bileseni / pal ucu hizi."""
        return abs(V * math.cos(alfa_disk)) / self.V_uc

    def profil_gucu(self, V: float, alfa_disk: float) -> float:
        return self.P0_ref * (1.0 + 4.65 * self.mu(V, alfa_disk) ** 2)

    def itki_katsayisi_tavani(self, mu: float) -> float:
        """Geri donen pal stall'i nedeniyle C_T/sigma tavani mu ile duser."""
        if mu >= self.mu_max:
            return 0.0
        return self.CTs_tavan * (1.0 - (mu / self.mu_max) ** 2)

    def itki_aerodinamik_tavani(self, rho: float, V: float,
                                alfa_disk: float) -> float:
        """Gucten bagimsiz, pal aerodinamigi kaynakli itki tavani."""
        CTs = self.itki_katsayisi_tavani(self.mu(V, alfa_disk))
        return CTs * self.sigma * rho * self.A * self.V_uc ** 2

    # ---------------------------------------------------------------
    def v_hover(self, T: float, rho: float) -> float:
        """Hover indukleme hizi"""
        return math.sqrt(max(T, 0.0) / (2.0 * rho * self.A))

    def v_ind(self, T: float, rho: float, V: float, alfa_disk: float) -> float:
        """Genel indukleme hizi, Glauert egik akis bagintisi.

        alfa_disk: disk duzlemine gore serbest akis acisi (rad).
                   0    -> akis disk duzleminde (kenar akisi, cruise)
                   pi/2 -> akis diske dik (eksenel, hover tirmanisi)
        Cozum sabit nokta iterasyonu, 40 adimda 1e-9 mertebesine yakinsar.
        """
        if T <= 0.0:
            return 0.0
        vh = self.v_hover(T, rho)
        if V < 0.5:
            return vh
        Vp = V * math.sin(alfa_disk)         # diske dik bilesen
        Vt = V * math.cos(alfa_disk)         # disk duzlemindeki bilesen
        # Newton: f(v) = v * sqrt(Vt^2 + (Vp+v)^2) - vh^2 = 0
        # Sabit nokta iterasyonundan ~5 kat hizli, ayni cozume gider.
        v = vh
        for _ in range(30):
            kok = math.sqrt(Vt * Vt + (Vp + v) ** 2)
            f = v * kok - vh * vh
            df = kok + v * (Vp + v) / max(kok, 1e-9)
            adim = f / max(df, 1e-9)
            v -= adim
            if v < 0.0:
                v = 1e-6
            if abs(adim) < 1e-10:
                break
        return v

    # ---------------------------------------------------------------
    # ROTOR INDUKLEMESININ ITKIYE BAGLANMASI (B7, karar 50)
    # ⚠️ BAYRAK VARSAYILAN KAPALI, LIMULUS_ROTOR_INDUKLEME. Bu fonksiyon
    # cagrilmadikca model bayrak eklenmeden onceki hali ile BIREBIR aynidir.
    #
    # Karar 46 sonumlemeyi TAM SIFIR buldu ve uc yapisal neden teshis etti.
    # Birincisi, itkinin bir GIRDI olmasi, yani durumun fonksiyonu olmamasi.
    # Bu fonksiyon yalniz o nedeni hedefler. Gercek bir rotor sabit
    # kollektif ve sabit devirde calisirken eksenel akis degistiginde
    # itkisini degistirir.
    #
    # Fizik, pal elemani teorisinin sabit veterli ve burulmasiz hali:
    #     C_T = (sigma a / 4) (2 theta_0 / 3 - lambda),  lambda = (Vp+v)/(Omega R)
    # Kollektif sabitken referans noktadan sapma:
    #     C_T = C_T0 - (sigma a / 4) (lambda - lambda_0)
    # Yani duyarliligin TAMAMI sigma*a/4 carpanindadir. sigma modelde
    # zaten tanimli, v de zaten Glauert ile cozuluyor.
    #
    # ⚠️ TEK YENI SAYI pal kesiti tasima egimi a'dir ve INCE KANAT
    # TEORISINDEN alinir, a = 2 pi 1/rad. Bu bir turetmedir, ampirik bir
    # uydurma degildir. Kanadin CL_alfa = 4,90 degeri KULLANILMAZ, o
    # AR=11 sonlu kanadin UC BOYUTLU egimi, pal elemani ise IKI BOYUTLU
    # kesit egimi ister.
    #
    # ⚠️ Gercek pal kesitleri icin a genellikle 5,7 mertebesinde, yani
    # 2 pi bir UST SINIR. Uc kaybi ve burulma da uygulanmiyor, ikisi de
    # egimi dusurur. Sonumleme a ile DOGRUSAL olcekleniyor, dolayisiyla
    # a = 5,7 icin deger 5,7/(2pi) = 0,907 kati. Ön kayit kural 5 ikinci
    # bir deger denenmesini yasakladi.
    A_PAL_2B: float = 2.0 * math.pi        # 1/rad, ince kanat teorisi

    def itki_indukleme_duzeltmesi(self, T_komut: float, rho: float,
                                  V_ref: float, alfa_ref: float,
                                  V_yerel: float, alfa_yerel: float) -> float:
        """Yerel akis referanstan saptiginda ITKIDEKI degisim [N].

        T_komut     kollektifin karsiligi olan referans itki [N]
        V_ref       referans serbest akis hizi [m/s], govde hizi
        alfa_ref    referans disk akis acisi [rad]
        V_yerel     podun gordugu yerel hiz [m/s], omega x r dahil
        alfa_yerel  podun gordugu yerel disk akis acisi [rad]

        Donen deger T_komut'a EKLENIR. Yerel akis referansla ayni oldugunda
        TAM SIFIR doner, dolayisiyla donme hizi sifirken ve bayrak kapaliyken
        model degismez.

        ⚠️ Kollektif denetimi MODELLENMIYOR. Gercek bir kontrolcu itkiyi
        sabit tutmak icin kollektifi ayarlar ve bu geri tepkiyi kismen ya da
        tamamen bastirir. Olculen sey ACIK CEVRIM geri tepkidir, yani
        kontrolcunun karsi koyacagi seyin buyuklugu.
        """
        if T_komut <= 0.0:
            return 0.0
        # indukleme oranlari, lambda = (Vp + v) / V_uc
        vp_ref = V_ref * math.sin(alfa_ref)
        vp_yer = V_yerel * math.sin(alfa_yerel)
        v_ref = self.v_ind(T_komut, rho, V_ref, alfa_ref)
        v_yer = self.v_ind(T_komut, rho, V_yerel, alfa_yerel)
        d_lambda = ((vp_yer + v_yer) - (vp_ref + v_ref)) / self.V_uc
        if d_lambda == 0.0:
            return 0.0
        # dC_T = -(sigma a / 4) d_lambda,  T = C_T rho A V_uc^2
        dCT = -(self.sigma * self.A_PAL_2B / 4.0) * d_lambda
        return dCT * rho * self.A * self.V_uc ** 2

    # ---------------------------------------------------------------
    def guc(self, T: float, rho: float, V: float = 0.0,
            alfa_disk: float = math.pi / 2) -> float:
        """Sase gucu [W] = kappa * indukleme + profil.

        Hover'da (V=0, T=T_kalibre) tezin bagintisini birebir verir:
            P = T/FoM * sqrt(T/(2 rho A))
        """
        if T <= 0.0:
            return self.profil_gucu(V, alfa_disk)
        if V < 0.5:
            return self.kappa * T * self.v_hover(T, rho) + self.P0_ref
        v = self.v_ind(T, rho, V, alfa_disk)
        Vp = V * math.sin(alfa_disk)
        return (T * Vp                        # faydali itki gucu, kayipsiz
                + self.kappa * T * v          # indukleme, kappa buraya
                + self.profil_gucu(V, alfa_disk))

    def itki_limiti(self, P: float, rho: float, V: float = 0.0,
                    alfa_disk: float = math.pi / 2) -> float:
        """Azami itki [N]. Guc VE pal aerodinamigi sinirlarinin kucugu."""
        aero = self.itki_aerodinamik_tavani(rho, V, alfa_disk)
        if P <= self.profil_gucu(V, alfa_disk):
            return 0.0
        # 30 ikiye bolme adimi ~1e-5 N hassasiyet verir. Ilk surumde 80
        # adim vardi ve egitim hizinin ucte ikisini yiyordu.
        alt, ust = 0.0, max(aero, 1.0) * 1.5
        for _ in range(30):
            orta = 0.5 * (alt + ust)
            if self.guc(orta, rho, V, alfa_disk) < P:
                alt = orta
            else:
                ust = orta
        return min(0.5 * (alt + ust), aero)

    # ---------------------------------------------------------------
    def disk_yuklemesi(self, T: float) -> float:
        return T / self.A

    def frekanslar(self) -> dict:
        """Uyarma frekanslari [Hz]. Bolum 8.2 ile ayni set."""
        f1 = self.RPM / 60.0
        return {"1/rev": f1, "N/rev": f1 * self.N_PAL, "2N/rev": f1 * 2 * self.N_PAL}


if __name__ == "__main__":
    from konfigurasyon import KONF as K

    r = Rotor(D=K["D_ROTOR"], FOM=K["FOM"], N_PAL=K["N_PAL"], RPM=K["RPM"])
    rho = K["RHO0"]
    W = K["MTOW"] * K["G"]
    T_eff = W * K["DOWNLOAD"] / 4.0

    print(f"disk alani        {r.A:.3f} m2      (tez 6,158)")
    print(f"disk yuklemesi    {r.disk_yuklemesi(W/4):.0f} N/m2  (tez 1195)")
    print(f"indukleme hizi    {r.v_hover(W/4, rho):.1f} m/s   (tez 22,1)")
    print(f"hover gucu x4     {4*r.guc(T_eff, rho)/1e3:.1f} kW     (tez 913)")
    print(f"pal ucu hizi      {r.V_uc:.1f} m/s   Mach {r.V_uc/340.3:.3f}")
    print("frekanslar        " + "  ".join(
        f"{k}={v:.1f} Hz" for k, v in r.frekanslar().items())
        + "   (tez 17,4 / 87,0)")

    print("\negik akis yakinsamasi (T = 7358 N, rho = 1,225)")
    for V in (0, 10, 20, 40, 68.9):
        for ad, ad_ac in (("eksenel", 90.0), ("egik 45", 45.0), ("kenar", 5.0)):
            v = r.v_ind(7358.0, rho, V, math.radians(ad_ac))
            print(f"  V={V:>5.1f} {ad:<8} v_i={v:6.2f} m/s   "
                  f"P={r.guc(7358.0, rho, V, math.radians(ad_ac))/1e3:6.1f} kW")
        print()
