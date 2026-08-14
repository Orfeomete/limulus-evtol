#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRIM COZUCU — genel duz ucus dengesi

Cozulen denklem seti (simetrik ucus, yanal eksen kapali)
    Fx = 0     boyuna kuvvet
    Fz = 0     dusey kuvvet
    My = 0     yunuslama momenti      <- tezin hic kurmadigi denklem

Bilinmeyenler varyanta gore degisir.
    LIMULUS      alfa, T_on, T_arka, theta_on, theta_arka   (5)
    Ikili        ayni                                        (5)
    Senkron      alfa, T_on, T_arka, theta                   (4)
    Lift+cruise  alfa, T_dusey, T_cruise                     (3)

Uc denklem, ucten fazla bilinmeyen. Fazla serbestlik derecesi BIR AMAC
FONKSIYONU ile kapatilir — gerekli batarya gucu en aza indirilir.
Boylece her varyant kendi en iyi trim noktasinda calisir ve
karsilastirma adil olur.

Trim zarfi = bir varyantin cozum bulabildigi (V, gama) noktalarinin
kumesi. Karsilastirmanin birinci metrigi budur (4-KARARLAR/09 §4).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize, NonlinearConstraint

import atmosfer as atm
from arac import Limulus


@dataclass
class TrimSonucu:
    basarili: bool
    V: float
    gama: float                  # ucus yolu acisi, rad
    alfa: float = 0.0
    theta_govde: float = 0.0     # govde pitch acisi
    T: np.ndarray = None         # 4 pod itkisi
    tilt: np.ndarray = None      # 4 pod tilt acisi
    P_batarya: float = 0.0
    CL: float = 0.0
    LD: float = 0.0
    artik: float = 1e9           # denklem artiklarinin normu
    T_cruise: float = 0.0        # ayri cruise itici birimi (B4), N
    mesaj: str = ""

    def __str__(self):
        if not self.basarili:
            return (f"V={self.V:5.1f} gama={math.degrees(self.gama):+5.1f}  "
                    f"COZUM YOK ({self.mesaj})")
        return (f"V={self.V:5.1f} gama={math.degrees(self.gama):+5.1f}  "
                f"alfa={math.degrees(self.alfa):+5.2f}  "
                f"tilt={np.degrees(self.tilt).round(1)}  "
                f"T={np.round(self.T / 1e3, 2)} kN  "
                f"P={self.P_batarya / 1e3:6.1f} kW")


def _grup_temsilcileri(ac: Limulus) -> tuple[int, ...]:
    gr = ac.var.tilt_gruplari
    return tuple(g[0] for g in gr) if gr else (0,)


# =====================================================================
def trim(ac: Limulus, V: float, gama: float = 0.0, h: float = 0.0,
         kademe: str = "surekli", baslangic: np.ndarray | None = None,
         guc_agirligi: float = 1e-2) -> TrimSonucu:
    """Verilen hiz ve ucus yolu acisi icin trim cozumu."""
    hava = atm.isa(h)
    var = ac.var
    n_tilt = max(var.n_tilt, 1)
    temsilci = _grup_temsilcileri(ac)
    # ⚠️ AYRI CRUISE ITICI BIRIMI (B4, karar 22 ve 32).
    # Bayrak acikken lift+cruise'un UCUNCU bir tasarim degiskeni olur.
    # Bayrak kapaliyken tasarim vektoru bit bit ayni kalir, yani
    # kosular_v2 sayilari yeniden uretilebilir.
    n_ct = 1 if (ac.cruise_itki_etkin and var.ayri_cruise_itki) else 0
    Tc_tavan = (ac.k['CRUISE_ITKI_P'] * ac.k['CRUISE_ITKI_ETA']
                / max(V, 5.0)) if n_ct else 0.0

    # --- baslangic tahmini ---
    if baslangic is None:
        if V < 5.0:
            x0 = np.array([0.0, ac.W / 4, ac.W / 4] + [0.0] * n_tilt
                          + [0.0] * n_ct)
        else:
            oran = float(np.clip(V / 60.0, 0.0, 1.0))
            t0 = oran * ac.k["THETA_CRUISE"]
            CL = ac.W / max(hava.q(V) * ac.kanat.S, 1e-6)
            x0 = np.array([ac.kanat.alfa_icin_CL(min(CL, ac.kanat.CL_max * 0.9)),
                           ac.W / 6, ac.W / 6] + [t0] * n_tilt
                          + [0.35 * Tc_tavan] * n_ct)
    else:
        x0 = np.array(baslangic, float)

    def ayikla(x):
        alfa = float(x[0])
        T = np.array([x[1], x[1], x[2], x[2]])
        if var.sabit_tilt is not None:
            tilt = np.full(4, var.sabit_tilt)
        else:
            tilt = ac.tilt_esle(np.asarray(x[3:3 + n_tilt]))
        d = np.zeros(12)
        d[0] = V * math.cos(alfa)
        d[2] = V * math.sin(alfa)
        d[7] = alfa + gama                 # duz ucus, yatis yok
        Tc = float(x[3 + n_tilt]) if n_ct else 0.0
        return d, T, tilt, Tc

    def artiklar(x):
        d, T, tilt, Tc = ayikla(x)
        F, M, b = ac.kuvvetler(d, T, tilt, hava, T_cruise=Tc)
        return np.array([F[0], F[2], M[1]]), b

    OLCEK = np.array([100.0, 100.0, 100.0])

    def kisit(x):
        return artiklar(x)[0] / OLCEK

    def amac(x):
        """Gercek amac batarya gucudur. Denklemler KISIT olarak verilir,
        ceza terimi olarak degil. Ceza yaklasimi yerel minimumda
        takiliyordu (cruise'da tilt 12 derece bulunuyordu, dogrusu 85+)."""
        return float(artiklar(x)[1]["P_batarya"] / 1e6)

    # --- sinirlar ---
    # Stall marji: duz ucusta CL_max'a yaslanilmaz. 1,1 V_S1 kurali
    # CL <= CL_max/1,21 demektir. Optimizer aksi halde tum gecis boyunca
    # kanadi stall sinirinda calistirip guc kazaniyor, bu operasyonel
    # olarak kabul edilemez.
    a_max = ac.kanat.alfa_icin_CL(ac.kanat.CL_max / 1.21)
    if V < 1.0:
        # V=0'da hucum acisi tanimsiz. Govde seviyeli tutulur.
        a_max = 1e-9
    T_tavan = ac.rotor.itki_limiti(ac.itki[0].guc_tavani(kademe),
                                   hava.rho, V, math.pi / 2)
    sinirlar = [(-a_max, a_max), (0.0, T_tavan), (0.0, T_tavan)]
    if V < 1.0:
        sinirlar[0] = (-1e-9, 1e-9)
    if var.sabit_tilt is None:
        sinirlar += [(ac.k["THETA_MIN"], ac.k["THETA_MAX"])] * n_tilt
    else:
        sinirlar += [(0.0, 0.0)] * n_tilt
    if n_ct:
        sinirlar += [(0.0, Tc_tavan)]
    alt = np.array([s[0] for s in sinirlar])
    ust = np.array([s[1] for s in sinirlar])

    # ---------------------------------------------------------------
    # COZUM STRATEJISI — IC ICE GECMISLIK (nesting)
    #
    # Senkron tilt, LIMULUS'un bir OZEL HALIDIR. Dolayisiyla LIMULUS'un
    # cozumu senkrondan asla kotu olamaz. Optimizer bunu kendiliginden
    # garanti etmez ve ilk surumde etmedi de — V=69'da senkron 199 kW,
    # LIMULUS 225 kW bulunuyordu. Bu, mimari farki gibi gorunen bir
    # cozucu artefaktidir ve karsilastirmayi gecersiz kilardi.
    #
    # Cozum: once tek serbestlik dereceli (senkron) problem cozulur,
    # sonucu cok serbestlikli probleme baslangic olarak verilir. Boylece
    # daha genel varyant her zaman en az daha kisitli olan kadar iyidir.
    # ---------------------------------------------------------------
    def coz_bir(baslangiclar, n_deg):
        """n_deg serbestlik dereceli tilt ile SLSQP, cok baslangicli."""
        iyi = None
        for xs in baslangiclar:
            xs = np.clip(xs, alt, ust)
            try:
                r = minimize(amac, xs, method="SLSQP", bounds=sinirlar,
                             constraints=[dict(type="eq", fun=kisit)],
                             options=dict(maxiter=200, ftol=1e-10))
            except Exception:
                continue
            rr, b = artiklar(r.x)
            norm = float(np.linalg.norm(rr / OLCEK))
            if norm >= 0.05:
                continue
            if iyi is None or b["P_batarya"] < iyi[0]:
                iyi = (b["P_batarya"], r.x.copy(), rr, b, norm)
        return iyi

    tilt_izgara = (0.0, 0.6, 1.2, ac.k["THETA_MAX"])

    def tc_cesitle(baslangiclar):
        """⚠️ ICE GECMISLIK, cruise itki degiskeni icin (karar 32).

        Daha buyuk bir itici birimin uygun kumesi, kucugunkini KAPSAR.
        Dolayisiyla optimum asla kotulesemez. Cok baslangic verilmezse
        SLSQP bunu garanti etmiyor: 180 kW birim V=50'de 366 kW bulurken
        220 kW birim 469 kW buluyordu. Bu bir fizik sonucu degil, cozucu
        artefaktidir ve mimari karsilastirmasini gecersiz kilardi.
        """
        if not n_ct:
            return baslangiclar
        cikti = []
        for xs in baslangiclar:
            for pay in (0.0, 0.35, 0.7, 1.0):
                # ⚠️ ROTOR ITKISI DE CESITLENIYOR. Yalniz Tc cesitlemek
                # yetmedi: cozucu, buyuk birimde "rotor da tasisin"
                # havzasina dusuyor ve daha kotu bir optimum buluyordu.
                # Dusuk rotor itkili baslangic, "kanat tasisin" havzasini
                # her zaman ornekler.
                for rot in (1.0, 0.12):
                    xd = xs.copy()
                    xd[3 + n_tilt] = pay * Tc_tavan
                    xd[1] = xs[1] * rot
                    xd[2] = xs[2] * rot
                    cikti.append(xd)
        return cikti

    def coz_kademeli(baslangiclar, n_deg):
        """⚠️ Tc TAVANI KADEME KADEME ACILIR (karar 32).

        Dusuk tavanla bulunan bir cozum, yuksek tavanda da UYGUNDUR.
        Dolayisiyla kademelerin en iyisini almak, buyuk birimin kucuk
        birimden kotu cikmasini MATEMATIKSEL OLARAK imkansiz kilar.
        Cok baslangic tek basina bunu garanti etmiyordu.
        """
        if not n_ct:
            return coz_bir(baslangiclar, n_deg)
        # ⚠️ KADEMELER MUTLAK, ORANSAL DEGIL. Oransal kademe (0,4/0,7/1,0)
        # ayni birim icinde tutarli sonuc veriyor fakat FARKLI birim
        # boyutlari arasinda garanti vermiyordu: 180 kW V=68,9'da 276,6 kW
        # bulurken 200 kW 293,6 kW buluyordu. Mutlak kademe kullanilinca
        # buyuk birimin kademeleri kucugunkileri KAPSIYOR ve tekduzelik
        # insaat geregi saglaniyor.
        kademeler = [t for t in (500.0, 1000.0, 1500.0, 2000.0, 3000.0)
                     if t < Tc_tavan] + [Tc_tavan]
        en, onceki = None, None
        for tavan in kademeler:
            sinirlar[-1] = (0.0, tavan)
            ust[-1] = tavan
            bas2 = list(baslangiclar)
            if onceki is not None:
                bas2.insert(0, onceki)
            r = coz_bir(bas2, n_deg)
            if r is not None:
                onceki = np.clip(r[1].copy(), alt, ust)
                if en is None or r[0] < en[0]:
                    en = r
        sinirlar[-1] = (0.0, Tc_tavan)
        ust[-1] = Tc_tavan
        return en

    en_iyi = None

    if var.sabit_tilt is None and n_tilt > 1:
        # 1) senkron on cozum: tum tilt degiskenleri esit tutulur
        eski_grup = var.tilt_gruplari
        object.__setattr__(var, "tilt_gruplari", ((0, 1, 2, 3),))
        try:
            bas = [x0.copy()]
            for t in tilt_izgara:
                xd = x0.copy(); xd[3:3 + n_tilt] = t
                bas.append(xd)
            on = coz_kademeli(tc_cesitle(bas), 1)
        finally:
            object.__setattr__(var, "tilt_gruplari", eski_grup)
        # 2) tam problem, senkron cozumu de baslangic olarak
        bas = [x0.copy()]
        for t in tilt_izgara:
            xd = x0.copy(); xd[3:3 + n_tilt] = t
            bas.append(xd)
        if on is not None:
            xs = on[1].copy()
            xs[3:3 + n_tilt] = on[1][3]
            bas.insert(0, xs)
        en_iyi = coz_kademeli(tc_cesitle(bas), n_tilt)
    else:
        bas = [x0.copy()]
        if var.sabit_tilt is None:
            for t in tilt_izgara:
                xd = x0.copy(); xd[3:3 + n_tilt] = t
                bas.append(xd)
        en_iyi = coz_kademeli(tc_cesitle(bas), n_tilt)

    if en_iyi is None:
        # hicbir baslangic kisitlari saglayamadi
        rr, b = artiklar(np.clip(x0, alt, ust))
        norm = float(np.linalg.norm(rr / OLCEK))
        d, T, tilt, Tc = ayikla(np.clip(x0, alt, ust))
        return TrimSonucu(
            basarili=False, V=V, gama=gama, alfa=float(x0[0]),
            theta_govde=float(x0[0] + gama), T=T, tilt=tilt,
            P_batarya=float(b["P_batarya"]), CL=float(b["CL"]),
            LD=float(b["LD"]), artik=norm,
            mesaj=f"artik {norm:.3f} (Fx={rr[0]:.0f} Fz={rr[1]:.0f} My={rr[2]:.0f})")

    _, x, rr, b, norm = en_iyi
    d, T, tilt, Tc = ayikla(x)
    tamam = norm < 0.05                      # ~5 N ve 5 N m mertebesi
    return TrimSonucu(
        basarili=bool(tamam), V=V, gama=gama, alfa=float(x[0]),
        theta_govde=float(x[0] + gama), T=T, tilt=tilt,
        P_batarya=float(b["P_batarya"]), CL=float(b["CL"]), LD=float(b["LD"]),
        artik=norm, T_cruise=float(Tc),
        mesaj="" if tamam else
        f"artik {norm:.3f} (Fx={rr[0]:.0f} Fz={rr[1]:.0f} My={rr[2]:.0f})")


def _sonraki_baslangic(ac: Limulus, r: TrimSonucu) -> np.ndarray:
    t = _grup_temsilcileri(ac)
    ek = [r.T_cruise] if (ac.cruise_itki_etkin
                          and ac.var.ayri_cruise_itki) else []
    return np.concatenate([[r.alfa, r.T[0], r.T[2]],
                           [r.tilt[i] for i in t], ek])


# =====================================================================
def hiz_taramasi(ac: Limulus, hizlar, gama: float = 0.0, h: float = 0.0):
    """Sirali tarama. Onceki cozum sonrakine baslangic olur."""
    sonuc, onceki = [], None
    for V in hizlar:
        r = trim(ac, float(V), gama, h, baslangic=onceki)
        if r.basarili:
            onceki = _sonraki_baslangic(ac, r)
        sonuc.append(r)
    return sonuc


def trim_zarfi(ac: Limulus, hizlar, gamalar, h: float = 0.0) -> np.ndarray:
    """(V, gama) izgarasinda cozum var mi. Trim zarfi metrigi."""
    Z = np.zeros((len(gamalar), len(hizlar)), dtype=bool)
    for j, g in enumerate(gamalar):
        onceki = None
        for i, V in enumerate(hizlar):
            r = trim(ac, float(V), float(g), h, baslangic=onceki)
            Z[j, i] = r.basarili
            if r.basarili:
                onceki = _sonraki_baslangic(ac, r)
    return Z


def zarf_hacmi(Z: np.ndarray, hizlar, gamalar) -> float:
    """Trim zarfinin alani [m/s x derece]. Karsilastirma metrigi 1."""
    dV = float(np.mean(np.diff(hizlar))) if len(hizlar) > 1 else 1.0
    dg = float(np.mean(np.diff(np.degrees(gamalar)))) if len(gamalar) > 1 else 1.0
    return float(Z.sum()) * dV * dg


# =====================================================================
if __name__ == "__main__":
    ac = Limulus()
    print(ac.ozet())

    print("\n" + "=" * 72)
    print("1. HOVER TRIM")
    print("=" * 72)
    r = trim(ac, 0.0)
    print(" ", r)
    print(f"  artik normu {r.artik:.2e}")
    _hava = atm.isa(0.0)
    _F, _M, _b = ac.kuvvetler(np.zeros(12), r.T, r.tilt, _hava)
    print(f"  sase gucu {_b['P_sase'] / 1e3:.1f} kW   (tez 913 kW)")
    print(f"  download kuvveti {_b['F_download']:.0f} N "
          f"({_b['F_download'] / ac.W * 100:.1f}% agirlik, tez %3,6)")
    print(f"  tez karsiligi  T = W/4 = {ac.W / 4:.0f} N")

    print("\n" + "=" * 72)
    print("2. CRUISE TRIM  —  moment denklemi DAHIL")
    print("=" * 72)
    r = trim(ac, ac.k["V_CRUISE"])
    print(" ", r)
    print(f"  CL = {r.CL:.3f}  (tez 0,78)     L/D = {r.LD:.2f}  (tez 16,1)")
    print(f"  batarya gucu {r.P_batarya / 1e3:.1f} kW   (tez 186,7 kW)")
    print(f"  artik normu {r.artik:.2e}  ->  "
          f"{'DENGELI' if r.basarili else 'DENGESIZ'}")

    print("\n" + "=" * 72)
    print("3. HIZ TARAMASI  —  gecis koridoru")
    print("=" * 72)
    hizlar = np.arange(0.0, 75.0, 10.0)
    print(f"  {'V':>5} {'alfa':>7} {'tilt':>7} {'T_on':>7} {'T_ark':>7} "
          f"{'CL':>6} {'P':>9}  durum")
    for r in hiz_taramasi(ac, hizlar):
        if r.basarili:
            print(f"  {r.V:>5.1f} {math.degrees(r.alfa):>7.2f} "
                  f"{np.degrees(r.tilt).mean():>7.1f} {r.T[0] / 1e3:>7.2f} "
                  f"{r.T[2] / 1e3:>7.2f} {r.CL:>6.3f} "
                  f"{r.P_batarya / 1e3:>7.1f} kW  ok")
        else:
            print(f"  {r.V:>5.1f} {'-':>7} {'-':>7} {'-':>7} {'-':>7} "
                  f"{'-':>6} {'-':>9}  {r.mesaj}")

    print("\n" + "=" * 72)
    print("4. VARYANT KARSILASTIRMASI  —  ayni gorev, farkli kontrol mimarisi")
    print("=" * 72)
    hizlar = np.array([0.0, 20.0, 35.0, 50.0, 68.9])
    print(f"  {'varyant':<17}" + "".join(f"  V={v:<7.0f}" for v in hizlar))
    for ad in ("limulus", "ikili", "senkron", "liftcruise"):
        a = Limulus(varyant_ad=ad)
        satir = []
        for r in hiz_taramasi(a, hizlar):
            satir.append(f"{r.P_batarya / 1e3:7.0f}kW" if r.basarili
                         else "    yok ")
        print(f"  {a.var.ad:<17}" + " ".join(satir))
    print("\n  bos hucre = o hizda trim cozumu bulunamadi")


# =====================================================================
# YANAL-YONEL TRIM (B1, 04.08.2026)
# =====================================================================
#
# Yukaridaki cozucu SIMETRIK ucus varsayar: yanal hiz sifir, yatis sifir,
# itki on/arka olarak ciftlenmis, uc denklem cozuluyor. Bu varsayim
# altinda LIMULUS ile ikili tilt BIREBIR AYNI cikti (bkz. Bolum J).
# Dort bagimsiz eksenin gerekcesi boyuna duzlemde kurulamaz.
#
# Bu bolum alti denklemin tamamini cozer.
#
#     Fx = Fy = Fz = 0        ucuc kuvvet
#     Mx = My = Mz = 0        uc moment
#
# Bilinmeyenler
#     alfa, beta, phi          ucus durumu                      (3)
#     T_1 .. T_4               DORT BAGIMSIZ itki               (4)
#     theta_1 .. theta_n       varyantin tilt serbestlik der.   (n)
#
# Itki artik ciftlenmiyor. Tilt gruplamasi mimarinin degiskenidir,
# itki degildir — dort rotor her varyantta bagimsizdir.
#
# ASIL SORU. Yanal eksende dort bagimsiz tilt, ikiliye gore bir sey
# kazandiriyor mu? Yatis ve sapma momentleri
#     Mx = -sum y_i T_i cos(th_i)      Mz = -sum y_i T_i sin(th_i)
# bagintilariyla uretiliyor. Sol-sag tilt ayrismasi Mz'yi dogrudan
# etkiliyor, ikili tiltte (on cift / arka cift) bu ayrisma YOK.

@dataclass
class YanalTrimSonucu:
    basarili: bool
    V: float
    alfa: float = 0.0
    beta: float = 0.0
    phi: float = 0.0
    T: np.ndarray = None
    tilt: np.ndarray = None
    P_batarya: float = 0.0
    artik: float = 1e9
    mesaj: str = ""

    def __str__(self):
        if not self.basarili:
            return f"V={self.V:5.1f}  COZUM YOK ({self.mesaj})"
        return (f"V={self.V:5.1f}  alfa={math.degrees(self.alfa):+5.2f}  "
                f"beta={math.degrees(self.beta):+5.2f}  "
                f"phi={math.degrees(self.phi):+5.2f}  "
                f"T={np.round(self.T/1e3,2)} kN  "
                f"tilt={np.degrees(self.tilt).round(1)}  "
                f"P={self.P_batarya/1e3:6.1f} kW")


def trim_yanal(ac: Limulus, V: float, h: float = 0.0,
               gama: float = 0.0, kademe: str = "surekli",
               ariza: int | None = None,
               beta_hedef: float | None = None,
               guc_agirligi: float = 1e-2,
               amac_kip: str = "guc",
               tilt_kilit: dict[int, float] | None = None,
               ek_baslangic: "list | None" = None) -> YanalTrimSonucu:
    """Alti denklemli trim. Asimetrik durumlari da cozer.

    ariza        arizali pod indisi (0-3) ya da None. Arizali podun
                 itkisi sifira zorlanir.
    beta_hedef   yan kayma acisi zorlanacaksa (rad). None ise serbest,
                 cozucu amac fonksiyonunu en aza indirirken kendi secer.
    amac_kip     ⚠️ BAYRAK, ONTANIM ESKI DAVRANIS (karar 22 kurali).
                 "guc"      batarya gucunu en aza indirir. Karar 21 ve 43'un
                            tamami bu kiple olculdu, ONTANIM budur.
                 "yankayma" |beta|'yi en aza indirir, guc ikincil terim
                            olarak `guc_agirligi` ile girer. Karar 45.
                 Kip degistirmek TUM sonuclari degistirir. Ontanim
                 disinda kosulan her sayi hangi kiple uretildigini
                 yazmak zorundadir.
    tilt_kilit   ⚠️ BAYRAK, ONTANIM None, yani ESKI DAVRANIS (karar 22).
                 {pod_indisi: aci_rad} sozlugu. Verilen podun tilt acisi
                 SABITLENIR, yani aktuator sikismasi temsil edilir. Kilitli
                 pod cozucunun serbestlik derecesinden cikmaz, cozucu yine
                 komut uretir fakat o pod komutu izlemez. Karar 48.

                 ⚠️ GRUBU CAGIRAN GENISLETIR, bu fonksiyon degil. Verilen
                 pod indisleri neyse yalniz onlar kilitlenir. Iki eksenli
                 kurguda tek aktuator bir CIFTI surdugu icin, o kurguda bir
                 aktuator sikismasi IKI pod indisi verilerek temsil
                 edilmelidir. Bunu burada yapmak, fonksiyonun varyant
                 gruplamasini yeniden yorumlamasi olurdu ve `tilt_esle`
                 ile iki yerde ayni bilgi tutulurdu. Genisletme
                 `testler/olcum_tilt_kilidi.py` icindedir.
    ek_baslangic ⚠️ BAYRAK, ONTANIM None, yani ESKI DAVRANIS (karar 22).
                 Ek baslangic noktalari listesi. Verilenler mevcut baslangic
                 listesinin SONUNA eklenir, mevcut baslangiclar kaldirilmaz ve
                 siralari degismez. Amac karar 51'in sicak baslangicidir, dort
                 eksenli problemi iki eksenli problemin cozumuyle baslatmak.
                 Uzunlugu yanlis olan vektor SESSIZCE ATLANMAZ, ValueError.
    """
    if amac_kip not in ("guc", "yankayma"):
        raise ValueError(f"amac_kip 'guc' ya da 'yankayma' olmali, "
                         f"verilen {amac_kip!r}")
    hava = atm.isa(h)
    var = ac.var
    n_tilt = max(var.n_tilt, 1)

    a_max = ac.kanat.alfa_icin_CL(ac.kanat.CL_max / 1.21)
    if V < 1.0:
        a_max = 1e-9
    T_tavan = ac.rotor.itki_limiti(ac.itki[0].guc_tavani(kademe),
                                   hava.rho, V, math.pi / 2)

    def ayikla(x):
        alfa, beta, phi = float(x[0]), float(x[1]), float(x[2])
        T = np.array(x[3:7], float)
        if ariza is not None:
            T = T.copy()
            T[ariza] = 0.0
        if var.sabit_tilt is not None:
            tilt = np.full(4, var.sabit_tilt)
        else:
            tilt = ac.tilt_esle(np.asarray(x[7:7 + n_tilt]))
        if tilt_kilit:
            # ⚠️ Kilit tilt_esle'DEN SONRA uygulanir, once degil. Gerekce,
            # iki eksenli kurguda bir aktuatorun bir cifti surmesi. Kilit
            # once uygulansaydi cozucu kilitli podu grup uzerinden yine
            # dolayli olarak hareket ettirebilirdi ve sikisma temsil
            # edilmezdi. Sonra uygulaninca kilit fizikte kalir.
            tilt = tilt.copy()
            for _p, _a in tilt_kilit.items():
                tilt[_p] = _a
        d = np.zeros(12)
        ca, sa = math.cos(alfa), math.sin(alfa)
        cb, sb = math.cos(beta), math.sin(beta)
        d[0] = V * ca * cb
        d[1] = V * sb
        d[2] = V * sa * cb
        d[6] = phi
        d[7] = alfa + gama
        return d, T, tilt

    def artiklar(x):
        d, T, tilt = ayikla(x)
        F, M, b = ac.kuvvetler(d, T, tilt, hava)
        return np.array([F[0], F[1], F[2], M[0], M[1], M[2]]), b

    OLCEK = np.array([100.0, 100.0, 100.0, 100.0, 100.0, 100.0])

    def kisit(x):
        r = artiklar(x)[0] / OLCEK
        if beta_hedef is not None:
            r = np.append(r, (x[1] - beta_hedef) * 10.0)
        return r

    def amac(x):
        # ⚠️ "guc" dali karar 21 ve 43'un olctugu daldir, DEGISTIRILMEZ.
        if amac_kip == "guc":
            return float(artiklar(x)[1]["P_batarya"] / 1e6)
        # "yankayma": birincil terim |beta|, guc ikincil. Olcekler bilincli
        # secildi. beta derece mertebesinde, guc MW mertebesinde, carpan
        # 1e-2 ile guc terimi beta'nin yaklasik yuzde biri agirliginda
        # kaliyor — yani guc yalniz beta ESIT oldugunda ayirt ediyor.
        b = artiklar(x)[1]
        return (abs(math.degrees(float(x[1])))
                + guc_agirligi * float(b["P_batarya"]) / 1e6)

    sinirlar = [(-a_max, a_max),
                (math.radians(-25.0), math.radians(25.0)),      # beta
                (math.radians(-35.0), math.radians(35.0))]      # phi
    sinirlar += [(0.0, T_tavan)] * 4
    if var.sabit_tilt is None:
        sinirlar += [(ac.k["THETA_MIN"], ac.k["THETA_MAX"])] * n_tilt
    else:
        sinirlar += [(0.0, 0.0)] * n_tilt
    alt = np.array([s[0] for s in sinirlar])
    ust = np.array([s[1] for s in sinirlar])

    # baslangic: once simetrik trimden al, sonra yanal serbest birak
    on = trim(ac, V, gama=gama, h=h, kademe=kademe)
    t0 = on.tilt[list(_grup_temsilcileri(ac))] if on.tilt is not None \
        else np.zeros(n_tilt)
    T0 = on.T if on.T is not None else np.full(4, ac.W / 4)
    x0 = np.concatenate([[on.alfa, 0.0, 0.0], T0, np.atleast_1d(t0)[:n_tilt]])

    baslangiclar = [x0]
    if ariza is not None:
        # arizali pod sifir, kalan uce yuk dagit
        xa = x0.copy()
        xa[3:7] = T0.sum() / 3.0
        xa[3 + ariza] = 0.0
        xa[2] = math.radians(5.0)          # hafif yatis tahmini
        baslangiclar.append(xa)
        xb = xa.copy(); xb[1] = math.radians(5.0)
        baslangiclar.append(xb)
    if ek_baslangic:
        n_bek = 7 + n_tilt
        for _e in ek_baslangic:
            _e = np.asarray(_e, float).ravel()
            if _e.size != n_bek:
                raise ValueError(f"ek_baslangic uzunlugu {_e.size}, "
                                 f"{n_bek} bekleniyordu")
            baslangiclar.append(_e)

    iyi = None
    for xs in baslangiclar:
        xs = np.clip(xs, alt, ust)
        try:
            r = minimize(amac, xs, method="SLSQP", bounds=sinirlar,
                         constraints=[dict(type="eq", fun=kisit)],
                         options=dict(maxiter=400, ftol=1e-10))
        except Exception:
            continue
        rr, b = artiklar(r.x)
        norm = float(np.linalg.norm(rr / OLCEK))
        if norm >= 0.05:
            continue
        # ⚠️ Baslangiclar arasindaki secim AMAC FONKSIYONUYLA ayni olmali.
        # "guc" kipinde bu P_batarya'dir ve eski davranisla birebir aynidir.
        # "yankayma" kipinde guc ile secmek, cozucunun en aza indirdiginden
        # farkli bir buyuklukle secmek olurdu.
        skor = (b["P_batarya"] if amac_kip == "guc" else amac(r.x))
        if iyi is None or skor < iyi[0]:
            iyi = (skor, r.x.copy(), rr, b, norm)

    if iyi is None:
        rr, b = artiklar(np.clip(x0, alt, ust))
        norm = float(np.linalg.norm(rr / OLCEK))
        d, T, tilt = ayikla(np.clip(x0, alt, ust))
        return YanalTrimSonucu(
            basarili=False, V=V, alfa=float(x0[0]), beta=float(x0[1]),
            phi=float(x0[2]), T=T, tilt=tilt,
            P_batarya=float(b["P_batarya"]), artik=norm,
            mesaj=f"artik {norm:.3f}")

    _, x, rr, b, norm = iyi
    d, T, tilt = ayikla(x)
    return YanalTrimSonucu(
        basarili=bool(norm < 0.05), V=V, alfa=float(x[0]), beta=float(x[1]),
        phi=float(x[2]), T=T, tilt=tilt,
        P_batarya=float(b["P_batarya"]), artik=norm,
        mesaj="" if norm < 0.05 else f"artik {norm:.3f}")


# =====================================================================
# KOORDINELI DONUS TRIMI — KALDIRILDI (karar 43, Mete onayi 09.08.2026)
# =====================================================================
# `trim_donus()` fonksiyonu karar 43'un S3 senaryosu icin yazildi, kabul
# testinden gecmedi ve on kayit geregi model degisikligi GERI ALINDI.
# Kaldirilan yaklasim ve neden calismadigi karar 43'un sonuc bolumunde
# ayrintili olarak durmaktadir, kabul testi de
# 7-ARSIV/kayit-dosyalari-09082026/dogrulama_donus_kabul.py altindadir.
#
# Ozeti: kalici donusun dogru kosulu F = m(omega x v) ve M = omega x (I omega)
# olarak kuruldu ve phi=0'da bu fonksiyon trim_yanal'i BIREBIR yeniden
# uretti. Engel baska yerdeydi. `kuvvetler()` donme hizlarina hic bagli
# degil, yani aerodinamik sonum terimleri (C_mq, C_lp, C_nr) modelde yok.
# Bu yuzden "donus trimi kapanmiyor" sonucunun fizikten mi eksik model
# katmanindan mi geldigi ayrilamiyordu. Sayi uretmek mumkundu, o sayinin
# neyi olctugunu soylemek degil.
#
# Yeniden denemek isteyen once sonum terimlerini modele eklemeli.
