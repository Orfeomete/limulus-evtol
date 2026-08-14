#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIMULUS — BUTUNLESIK ARAC MODELI

Fizik katmanlarini birlestirir.
    konfigurasyon -> geometri.py'den tasarim noktasi
    atmosfer      -> ISA, ruzgar, Dryden, ayrik gust
    rotor         -> momentum teorisi, egik akis
    aerodinamik   -> kanat + govde
    aktuator      -> tilt oran limiti, itki gecikmesi
    sensor        -> gurultu, sapma, gecikme
    govde         -> 6-DOF hareket denklemleri, RK4

Kontrol girisi (8)
    [T1 T2 T3 T4]        pod itki komutlari       N
    [th1 th2 th3 th4]    pod tilt komutlari       rad

Pod numaralandirmasi
    1 on-sol   2 on-sag   3 arka-sol   4 arka-sag
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass, field

import numpy as np

from konfigurasyon import KONF, VARSAYIMLAR, Varyant, varyant
import atmosfer as atm
import govde as gv
from aerodinamik import Kanat, Govde
from aktuator import EklemYuku, ItkiZinciri, TiltAktuatoru
from rotor import Rotor
from sensor import SensorPaketi


@dataclass
class Limulus:
    """Butunlesik arac. Tum alt modeller burada baglanir."""
    k: dict = field(default_factory=lambda: dict(KONF))
    dt: float = 0.02
    varyant_ad: str = "limulus"
    # B4: ayri cruise itki birimi. VARSAYILAN KAPALI — bkz. 4-KARARLAR/22.
    # Acilirsa lift+cruise varyantinin fizigi degisir ve o ana kadar
    # uretilmis butun kosu/metrik sonuclari gecersiz olur.
    cruise_itki_etkin: bool = False
    ruzgar: atm.Ruzgar = field(default_factory=atm.Ruzgar)
    sensor_etkin: bool = False
    tohum: int | None = None

    # -----------------------------------------------------------------
    def __post_init__(self):
        k = self.k
        self.var: Varyant = varyant(self.varyant_ad)

        # --- boyuna referans noktalar (istasyon ekseni) ---
        mac = k["MAC"]
        self.le_mac = k["X_KANAT"] - 0.25 * mac
        self.x_cg = self.le_mac + k["CG_MAC_YUZDE"] / 100 * mac
        self.x_np = self.le_mac + k["NP_MAC_YUZDE"] / 100 * mac
        self.sm = (self.x_np - self.x_cg) / mac

        # --- pod konumlari, GOVDE ekseninde ---
        zp = k["Z_POD_CG"]
        self.pod = np.array([
            [self.govde_x(k["X_ROTOR_ON"]),   -k["Y_MODUL"], zp],
            [self.govde_x(k["X_ROTOR_ON"]),   +k["Y_MODUL"], zp],
            [self.govde_x(k["X_ROTOR_ARKA"]), -k["Y_MODUL"], zp],
            [self.govde_x(k["X_ROTOR_ARKA"]), +k["Y_MODUL"], zp],
        ])
        self.r_np = np.array([self.govde_x(self.x_np), 0.0, 0.0])
        # Govde yan alaninin basinc merkezi. Yan alan boyuna simetrik kabul
        # edilirse merkez govde ortasindadir, kol CG'ye gore olculur.
        # ⚠️ Bu istasyon YALNIZ donme kuplaji bayragi acikken kol olarak
        # kullanilir, bkz. kuvvetler() icindeki not ve karar 46.
        self.r_govde = np.array([self.govde_x(k["L_TOTAL"] / 2.0), 0.0, 0.0])

        # --- DONME HIZI KUPLAJI BAYRAGI (B5, karar 46) ---
        # ⚠️ VARSAYILAN KAPALI. Acildiginda her aerodinamik ve itki
        # istasyonunun yerel hizina omega x r eklenir, yani sonumleme
        # geometriden turer. Kapali oldugunda model bayrak eklenmeden
        # onceki hali ile BIREBIR aynidir, kabul testi bunu dogrular.
        self._donme_kuplaji = (
            os.environ.get("LIMULUS_DONME_KUPLAJI", "0") == "1")
        # ⚠️ B7, karar 50. VARSAYILAN KAPALI. Rotor induklemesini itkiye
        # baglar, yani itkiyi bir GIRDI olmaktan cikarip durumun kismi bir
        # fonksiyonu yapar. Kapaliyken duzeltme HIC HESAPLANMAZ.
        # ⚠️ Donme kuplaji KAPALIYSA bu bayrak da etkisizdir, cunku yerel
        # akis govde akisinin aynisi olur ve duzeltme kimliksel olarak
        # sifir doner. Ikisi birlikte anlamlidir ve bu bilinclidir.
        self._rotor_indukleme = (
            os.environ.get("LIMULUS_ROTOR_INDUKLEME", "0") == "1")

        # --- alt modeller ---
        self.rotor = Rotor(D=k["D_ROTOR"], FOM=k["FOM"], N_PAL=k["N_PAL"],
                           RPM=k["RPM"])
        self.kanat = Kanat(S=k["S_KANAT"], AR=k["AR"], MAC=mac, CD0=k["CD0"],
                           e=k["OSWALD"], CL_alfa=k["CL_ALFA"],
                           CL_max=k["CL_MAX"], Cm0=k["CM0"])
        self.govde_aero = Govde(S_yan=k["S_GOVDE_YAN"], K_y=k["K_GOVDE_Y"])
        self.tilt = [TiltAktuatoru(theta_max=k["THETA_MAX"],
                                   hiz_limiti=k["THETA_HIZ"]) for _ in range(4)]
        self.itki = [ItkiZinciri(n_motor=k["N_MOTOR_POD"],
                                 P_surekli=k["P_MOTOR_SUREKLI"],
                                 P_oei=k["P_MOTOR_OEI"], P_pik=k["P_MOTOR_PIK"],
                                 tau=k["TAU_MOTOR"]) for _ in range(4)]
        self.eklem = EklemYuku(n_limit=k["N_LIMIT"], j_emniyet=k["J_EMNIYET"],
                               kapasite_dusey=k["RDPIF_DUSEY"])
        self.sensorler = SensorPaketi(dt=self.dt, tohum=self.tohum,
                                      etkin=self.sensor_etkin)

        # --- kutle ve atalet ---
        self.m = k["MTOW"]
        self.g = k["G"]
        self.W = self.m * self.g
        self.I = gv.atalet_matrisi(k["I_xx"], k["I_yy"], k["I_zz"], k["I_xz"])
        self.I_inv = np.linalg.inv(self.I)

        self.sifirla()

    # -----------------------------------------------------------------
    def govde_x(self, x_istasyon: float) -> float:
        """Istasyon ekseni (burundan geriye) -> govde ekseni (ileriye)."""
        return self.x_cg - x_istasyon

    # -----------------------------------------------------------------
    def sifirla(self, durum: np.ndarray | None = None,
                tilt0: float = 0.0, T0: float | None = None):
        self.durum = np.zeros(12) if durum is None else np.array(durum, float)
        self.t = 0.0
        self.enerji = 0.0
        T0 = self.W / 4.0 if T0 is None else T0
        for a in self.tilt:
            a.sifirla(tilt0)
        for z in self.itki:
            z.sifirla(T0)
        self.sensorler.sifirla()
        self.ruzgar.sifirla()
        self.son_bilgi: dict = {}

    # -----------------------------------------------------------------
    # KISIT: varyanta gore tilt komutlarini esle
    # -----------------------------------------------------------------
    def tilt_esle(self, komut: np.ndarray) -> np.ndarray:
        """Varyantin serbestlik derecesini dort poda dagitir.

        LIMULUS      4 giris -> 4 pod, birebir
        Ikili        2 giris -> on cift, arka cift
        Senkron      1 giris -> dort pod
        Lift+cruise  0 giris -> hepsi sabit
        """
        v = self.var
        if v.sabit_tilt is not None:
            return np.full(4, v.sabit_tilt)
        komut = np.atleast_1d(np.asarray(komut, float))
        if len(komut) == 4 and v.n_tilt == 4:
            return komut
        out = np.zeros(4)
        for i, grup in enumerate(v.tilt_gruplari):
            deger = komut[i] if i < len(komut) else komut[-1]
            for p in grup:
                out[p] = deger
        return out

    # -----------------------------------------------------------------
    def itki_tavani(self, i: int, V: float, alfa_disk: float,
                    rho: float, kademe: str = "surekli") -> float:
        P = self.itki[i].guc_tavani(kademe)
        return self.rotor.itki_limiti(P, rho, V, alfa_disk)

    # -----------------------------------------------------------------
    def kuvvetler(self, durum: np.ndarray, T: np.ndarray, tilt: np.ndarray,
                  hava: atm.Hava, ruzgar_govde: np.ndarray | None = None,
                  T_cruise: float = 0.0
                  ) -> tuple[np.ndarray, np.ndarray, dict]:
        """Toplam kuvvet ve moment, govde ekseninde. Agirlik dahil."""
        u, v, w = durum[0:3]
        phi, th, psi = durum[6:9]

        # ruzgar bagil hiza girer
        if ruzgar_govde is not None:
            u, v, w = np.array([u, v, w]) - ruzgar_govde

        V, alfa, beta = gv.hava_acilari(u, v, w)
        q_din = hava.q(V)

        # --- DONME HIZI KUPLAJI (B5) ---
        # ⚠️ BAYRAK VARSAYILAN KAPALI. Ayrinti 4-KARARLAR/46.
        # Kapali oldugunda bu bloktan gecen her sey sifir kalir ve model
        # bayrak eklenmeden onceki hali ile BIREBIR aynidir. Acik oldugunda
        # her istasyonun yerel hizina omega x r eklenir, yani sonumleme
        # AMPIRIK BIR KATSAYIDAN DEGIL GEOMETRIDEN gelir. Yeni sayi
        # tanimlanmamistir, bu bilincli bir secimdir — C_mq, C_lp, C_nr
        # gibi kararlilik turevleri icin bu konfigurasyona ait dogrulanmis
        # bir kaynak yoktur ve uydurulmalari yerine turetilmeleri secildi.
        omega = np.asarray(durum[3:6], float) if self._donme_kuplaji \
            else np.zeros(3)
        donme_var = bool(np.any(omega))
        v_govde = np.array([u, v, w], float)

        def _yerel(r_ist):
            """Istasyondaki yerel hiz, hava acilari ve dinamik basinc."""
            if not donme_var:
                return V, alfa, beta, q_din, v_govde
            vl = v_govde + np.cross(omega, np.asarray(r_ist, float))
            Vl, al, bl = gv.hava_acilari(vl[0], vl[1], vl[2])
            return Vl, al, bl, hava.q(Vl), vl

        F = np.zeros(3)
        M = np.zeros(3)
        dT_pod = np.zeros(4)   # B7 kaydi, kapaliyken sifir kalir

        # --- AYRI CRUISE ITKI BIRIMI (B4) ---
        # ⚠️ BAYRAK VARSAYILAN KAPALI. Ayrinti 4-KARARLAR/22.
        # Fizigi kosu ortasinda degistirmek tohum 0 ile tohum 1-4'u
        # farkli modellerle egitmek olurdu. Bayrak ancak butun kosular
        # bittikten sonra acilir ve butun metrikler yeniden hesaplanir.
        P_cruise = 0.0
        if self.cruise_itki_etkin and self.var.ayri_cruise_itki:
            Tc = float(np.clip(T_cruise, 0.0,
                               self.k["CRUISE_ITKI_P"]
                               * self.k["CRUISE_ITKI_ETA"] / max(V, 5.0)))
            # itici birim govde ekseninde, CG hizasinda. Moment kolu yok.
            F += np.array([Tc, 0.0, 0.0])
            P_cruise = Tc * max(V, 1.0) / self.k["CRUISE_ITKI_ETA"]

        # --- rotorlar ---
        P_sase = 0.0
        for i in range(4):
            ct, st = math.cos(tilt[i]), math.sin(tilt[i])
            # itki vektoru: tilt=0 -> -z (yukari), tilt=90 -> +x (ileri)
            f = np.array([T[i] * st, 0.0, -T[i] * ct])
            F += f
            M += gv.capraz(self.pod[i], f)
            # disk duzlemine gore akis acisi
            # disk duzlemine gore akis acisi. Dusuk hizda eksenel kabul
            # edilir, gecis YUMUSAK harmanla yapilir (bkz. govde.hava_acilari)
            n_disk = np.array([st, 0.0, -ct])          # disk normali
            # ⚠️ Yerel hiz: bayrak kapaliyken govde hizinin AYNISI.
            V_i, _, _, _, v_i = _yerel(self.pod[i])
            if V_i > gv.V_ESIK_ALT:
                akis = v_i / V_i
                sin_ad = float(np.clip(-np.dot(akis, n_disk), -1.0, 1.0))
                ham = math.asin(sin_ad)
                ag = gv._yumusak((V_i - gv.V_ESIK_ALT)
                                 / (gv.V_ESIK_UST - gv.V_ESIK_ALT))
                alfa_disk = ag * ham + (1.0 - ag) * (math.pi / 2)
            else:
                alfa_disk = math.pi / 2

            # --- ROTOR INDUKLEMESININ ITKIYE BAGLANMASI (B7, karar 50) ---
            # ⚠️ Duzeltme itki vektorune EKLENIR, dolayisiyla yukarida
            # eklenmis olan f ve momenti geri alinip yeniden eklenir.
            # Donme hizi sifirken ya da bayrak kapaliyken dT tam sifirdir.
            if self._rotor_indukleme and donme_var:
                _, _, _, _, _ = _yerel(self.pod[i])   # yerel zaten hesaplandi
                # referans, GOVDE hizi ve onun disk acisi
                if V > gv.V_ESIK_ALT:
                    akis_r = v_govde / V
                    sin_r = float(np.clip(-np.dot(akis_r, n_disk), -1.0, 1.0))
                    agr = gv._yumusak((V - gv.V_ESIK_ALT)
                                      / (gv.V_ESIK_UST - gv.V_ESIK_ALT))
                    alfa_ref = agr * math.asin(sin_r) + (1.0 - agr) * (math.pi / 2)
                else:
                    alfa_ref = math.pi / 2
                dT = self.rotor.itki_indukleme_duzeltmesi(
                    T[i], hava.rho, V, abs(alfa_ref), V_i, abs(alfa_disk))
                if dT != 0.0:
                    df = np.array([dT * st, 0.0, -dT * ct])
                    F += df
                    M += gv.capraz(self.pod[i], df)
                    dT_pod[i] = dT

            P_sase += self.rotor.guc(T[i], hava.rho, V_i, abs(alfa_disk))

        # --- rotor asagi-yuku (download) ---
        # Wake alttaki yapiya vurdugunda asagi yonlu bir kuvvet dogar.
        # Tez bunu hover icin %3,6 sabit ceza olarak veriyor (Bolum 4.1).
        # Her podun asagi-yuku KENDI ISTASYONUNDA etkir, kanat ceyrek
        # veterinde degil. Ilk surumde kanatta etkitilmisti ve hover'da
        # 53 N m'lik sahte bir burun-asagi momenti doguruyordu.
        # tilt ile sonumlenir: tilt=0 tam etki, tilt=90 etki yok.
        F_dl = 0.0
        for i in range(4):
            f_i = (self.k["DOWNLOAD"] - 1.0) * math.cos(tilt[i]) * T[i]
            F_dl += f_i
            f_v = np.array([0.0, 0.0, +f_i])        # +z = asagi
            F += f_v
            M += gv.capraz(self.pod[i], f_v)

        # --- kanat (notr noktada etkir) ---
        # ⚠️ Yunuslama sonumlemesi burada YAPISAL OLARAK KUCUKTUR, cunku
        # kanat notr noktada etkiyor ve tasarim statik marji sifir, yani
        # x_np = x_cg. Yunuslama hizi kanadin yerel hucum acisini
        # q (x_np - x_cg) / V kadar degistirir ve o kol tasarim noktasinda
        # SIFIRDIR. CG zarfinin uclarinda (+%5,5 ... -%7 MAC) sifir degildir.
        # Bu, bayragin acilmasiyla ortaya cikan bir bulgudur, kusur degil.
        _, alfa_w, _, q_w, _ = _yerel(self.r_np)
        Xw, Zw, Mw = self.kanat.kuvvet(q_w, alfa_w)
        f_aero = np.array([Xw, 0.0, Zw])
        F += f_aero
        M += gv.capraz(self.r_np, f_aero) + np.array([0.0, Mw, 0.0])

        # --- govde yanal ---
        # Sapma sonumlemesi buradan gelir. Sapma hizi govdenin yanal
        # istasyonunda yerel yan kaymayi degistirir, yerel yan kayma da
        # yanal kuvveti ve onun kolu uzerinden sapma momentini uretir.
        _, _, beta_g, q_g, _ = _yerel(self.r_govde)
        Yg, Ng = self.govde_aero.kuvvet(q_g, beta_g)
        f_yanal = np.array([0.0, Yg, 0.0])
        F += f_yanal
        M += np.array([0.0, 0.0, Ng])
        # ⚠️ KOL YALNIZ BAYRAK ACIKKEN GIRER, bilincli bir asimetridir.
        # Eski model yanal kuvveti CG'de etkitiyordu, yani kolu yoktu.
        # Kolu bayrak kapaliyken de eklemek 25 tamamlanmis kosunun fizigini
        # degistirirdi (karar 22). Kolun kalici olarak eklenmesi AYRI bir
        # kalemdir ve karar 46'nin "kapatilmayan" listesinde durur.
        if donme_var:
            M += gv.capraz(self.r_govde, f_yanal)

        F_aero_itki = F.copy()

        # --- yercekimi ---
        F += gv.yercekimi_govde(phi, th, self.m, self.g)

        # --- guc ---
        P_batarya = ((P_sase + P_cruise) / self.k["ETA_AKT"]
                     + self.k["P_OTEL"])

        bilgi = dict(V=V, alfa=alfa, beta=beta, q=q_din,
                     CL=self.kanat.katsayilar(alfa)[0],
                     CD=self.kanat.katsayilar(alfa)[1],
                     LD=self.kanat.LD(alfa),
                     P_sase=P_sase, P_cruise=P_cruise,
                     P_batarya=P_batarya, F_download=F_dl,
                     n_yuk=gv.yuk_faktoru(F_aero_itki, self.m, self.g),
                     eklem_asim=max(self.eklem.asim(t) for t in T),
                     # B7 kaydi, karar 50. Bayrak kapaliyken dordu de sifir.
                     dT_indukleme=dT_pod.copy())
        return F, M, bilgi

    # -----------------------------------------------------------------
    def turev(self, durum: np.ndarray, T: np.ndarray, tilt: np.ndarray,
              hava: atm.Hava, ruzgar_govde: np.ndarray | None = None,
              M_dis: np.ndarray | None = None,
              T_cruise: float = 0.0) -> np.ndarray:
        F, M, _ = self.kuvvetler(durum, T, tilt, hava, ruzgar_govde, T_cruise)
        if M_dis is not None:
            M = M + np.asarray(M_dis, float)
        return gv.turev(durum, F, M, self.m, self.I, self.I_inv)

    # -----------------------------------------------------------------
    def adim(self, T_komut: np.ndarray, tilt_komut: np.ndarray,
             kademe: str = "surekli",
             M_dis: np.ndarray | None = None,
             T_cruise: float = 0.0) -> tuple[np.ndarray, dict]:
        """Bir zaman adimi ilerlet. Olculen durumu dondurur."""
        dt = self.dt
        d = self.durum
        h = max(-d[11], 0.0)                       # z asagi, irtifa = -z
        hava = atm.isa(h)

        V_now = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
        w_yer = self.ruzgar(self.t, h, V_now, dt)
        R = gv.govde_yer_matrisi(d[6], d[7], d[8])
        w_govde = R.T @ w_yer

        # --- aktuatorler ---
        tilt_hedef = self.tilt_esle(tilt_komut)
        tilt = np.array([self.tilt[i].adim(tilt_hedef[i], dt) for i in range(4)])

        T_komut = np.atleast_1d(np.asarray(T_komut, float))
        if T_komut.size == 1:
            T_komut = np.full(4, T_komut[0])
        T = np.zeros(4)
        for i in range(4):
            n_disk = np.array([math.sin(tilt[i]), 0.0, -math.cos(tilt[i])])
            if V_now > 0.5:
                akis = np.array(d[0:3]) / V_now
                ad = abs(math.asin(float(np.clip(-np.dot(akis, n_disk), -1, 1))))
            else:
                ad = math.pi / 2
            tavan = self.itki_tavani(i, V_now, ad, hava.rho, kademe)
            T[i] = self.itki[i].adim(T_komut[i], tavan, dt)

        # --- integrasyon (bir adim boyunca kontrol sabit) ---
        self.durum = gv.rk4(
            lambda s: self.turev(s, T, tilt, hava, w_govde, M_dis,
                                 T_cruise), d, dt)
        self.durum[6] = gv.aci_sar(self.durum[6])
        self.durum[8] = gv.aci_sar(self.durum[8])
        self.t += dt

        _, _, bilgi = self.kuvvetler(self.durum, T, tilt, hava, w_govde,
                                     T_cruise)
        self.enerji += bilgi["P_batarya"] * dt
        bilgi.update(t=self.t, h=h, T=T.copy(), tilt=tilt.copy(),
                     ruzgar=w_yer.copy(), enerji=self.enerji,
                     enerji_orani=self.enerji / self.k["E_BATT"],
                     tilt_doygun=[a.doygun for a in self.tilt])
        self.son_bilgi = bilgi
        return self.sensorler(self.durum), bilgi

    # -----------------------------------------------------------------
    def ariza_ver(self, pod: int, n_motor: int = 1):
        """Bir podun motorlarindan n tanesini devre disi birakir."""
        self.itki[pod].arizali_motor = int(np.clip(n_motor, 0,
                                                   self.k["N_MOTOR_POD"]))

    def arizasiz(self):
        for z in self.itki:
            z.arizali_motor = 0

    # -----------------------------------------------------------------
    def ozet(self) -> str:
        return "\n".join([
            f"varyant           {self.var.ad}  ({self.var.karsiligi})",
            f"tilt serbestligi  {self.var.n_tilt}",
            f"agirlik merkezi   {self.x_cg:.3f} m ({self.k['CG_MAC_YUZDE']:.1f}% MAC)",
            f"notr nokta        {self.x_np:.3f} m ({self.k['NP_MAC_YUZDE']:.1f}% MAC)",
            f"statik marj       {self.sm*100:+.1f}%",
            f"pod kollari       on {self.pod[0,0]:+.3f} m  arka {self.pod[2,0]:+.3f} m",
            f"cozum adimi       {self.dt*1000:.0f} ms ({1/self.dt:.0f} Hz)",
            f"sensor            {'etkin' if self.sensor_etkin else 'ideal (kapali)'}",
        ])


if __name__ == "__main__":
    ac = Limulus()
    print(ac.ozet())

    print("\nHOVER DENGE KONTROLU (T = W/4, tilt = 0)")
    ac.sifirla()
    hava = atm.isa(0.0)
    T = np.full(4, ac.W / 4)
    F, M, b = ac.kuvvetler(np.zeros(12), T, np.zeros(4), hava)
    print(f"  F = {F.round(2)}  N")
    print(f"  M = {M.round(2)}  N m")
    print(f"  dusey artik {F[2]:+.2f} N   pitch artik {M[1]:+.2f} N m")
    print(f"  guc {b['P_sase']/1e3:.1f} kW sase / {b['P_batarya']/1e3:.1f} kW batarya")

    print("\nDOWNLOAD DAHIL")
    T = np.full(4, ac.W * ac.k["DOWNLOAD"] / 4)
    F, M, b = ac.kuvvetler(np.zeros(12), T, np.zeros(4), hava)
    print(f"  guc {b['P_sase']/1e3:.1f} kW   (tez 913 kW)")

    print("\nVARYANT TILT ESLEMESI")
    for ad in ("limulus", "ikili", "senkron", "liftcruise"):
        a = Limulus(varyant_ad=ad)
        giris = np.array([0.1, 0.2, 0.3, 0.4])[: max(a.var.n_tilt, 1)]
        print(f"  {a.var.ad:<16} n={a.var.n_tilt}  giris {np.round(giris,2)} "
              f"-> podlar {np.round(a.tilt_esle(giris), 2)}")
