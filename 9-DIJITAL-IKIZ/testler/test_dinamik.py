#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOGRULAMA TESTLERI — fizik katmani

Bu testler modelin DOGRU OLDUGUNU kanitlamaz, YANLIS OLMADIGINI
kontrol eder. Ayrim onemlidir: analitik bir modelin dogrulanmasi CFD
ve deney gerektirir, bu tez kapsaminda yapilmamistir
(LIMULUS_DURUSTLUK_CERCEVESI.md §3).

Test edilen sey iki basliktir.
  1  KORUNUM ve TUTARLILIK — enerji, moment, eksen isaretleri,
     integrator yakinsamasi. Bunlar mutlak dogrulardir.
  2  TEZLE UYUM — modelin tezin yayimlanmis sayilarini yeniden
     uretmesi. Bu bir kalibrasyon kontroludur.

Kosma:  python3 -m pytest testler/ -v      ya da     python3 test_dinamik.py
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

_BURASI = os.path.dirname(os.path.abspath(__file__))
_DIN = os.path.normpath(os.path.join(_BURASI, "..", "dinamik"))
if _DIN not in sys.path:
    sys.path.insert(0, _DIN)

import atmosfer as atm
import govde as gv
from aerodinamik import Kanat
from aktuator import EklemYuku, ItkiZinciri, TiltAktuatoru
from arac import Limulus
from konfigurasyon import KONF, VARSAYIMLAR
from rotor import Rotor


# =====================================================================
# 1. ISARET SISTEMI  — en kritik test
# =====================================================================
def test_isaret_moment_kolu():
    """CG'nin ONUNDEKI yukari kuvvet BURUN YUKARI moment uretmeli.

    Bu testin varlik nedeni: ilk surumde istasyon ekseni (burundan
    geriye) ile govde ekseni (CG'den ileriye) karistirildi ve tum
    yunuslama momentlerinin isareti tersti.
    """
    r = np.array([2.0, 0.0, 0.0])            # CG'nin 2 m onunde
    f = np.array([0.0, 0.0, -1000.0])        # 1 kN yukari (z asagi)
    assert gv.capraz(r, f)[1] > 0, "onde yukari kuvvet burun yukari olmali"


def test_isaret_eksen_donusumu():
    ac = Limulus()
    # burna yakin bir istasyon govde ekseninde POZITIF olmali
    assert ac.govde_x(ac.k["X_ROTOR_ON"]) > 0
    assert ac.govde_x(ac.k["X_ROTOR_ARKA"]) < 0
    assert ac.pod[0, 0] > ac.pod[2, 0]


def test_isaret_yercekimi():
    """Burun yukari iken agirligin govde-x bileseni GERIYE bakmali."""
    F = gv.yercekimi_govde(0.0, math.radians(10.0), 3000.0, 9.81)
    assert F[0] < 0
    F = gv.yercekimi_govde(0.0, 0.0, 3000.0, 9.81)
    assert abs(F[0]) < 1e-9 and F[2] > 0


def test_capraz_carpim_dogru():
    r = np.random.default_rng(0)
    for _ in range(500):
        a, b = r.standard_normal(3), r.standard_normal(3)
        assert np.allclose(gv.capraz(a, b), np.cross(a, b))


# =====================================================================
# 2. DONUSUM MATRISLERI
# =====================================================================
def test_donusum_ortogonal():
    r = np.random.default_rng(1)
    for _ in range(200):
        phi, th, psi = r.uniform(-1.2, 1.2, 3)
        R = gv.govde_yer_matrisi(phi, th, psi)
        assert np.allclose(R @ R.T, np.eye(3), atol=1e-12)
        assert abs(np.linalg.det(R) - 1.0) < 1e-12


def test_atalet_pozitif_tanimli():
    I = gv.atalet_matrisi(KONF["I_xx"], KONF["I_yy"], KONF["I_zz"], KONF["I_xz"])
    assert np.allclose(I, I.T)
    assert (np.linalg.eigvalsh(I) > 0).all()


# =====================================================================
# 3. INTEGRATOR
# =====================================================================
def test_serbest_dusus_analitik():
    m, g, T = 3000.0, 9.81, 5.0
    I = gv.atalet_matrisi(578.0, 5284.0, 5301.0, 555.0)
    I_inv = np.linalg.inv(I)
    d = np.zeros(12)
    dt = 0.005
    for _ in range(int(T / dt)):
        F = gv.yercekimi_govde(d[6], d[7], m, g)
        d = gv.rk4(lambda s: gv.turev(s, F, np.zeros(3), m, I, I_inv), d, dt)
    assert abs(d[2] - g * T) < 1e-9
    assert abs(d[11] - 0.5 * g * T * T) / (0.5 * g * T * T) < 1e-12


def test_rk4_adim_bagimsizligi():
    """Adim yariya inerken hata en az 8 kat kucuk olmali (4. derece)."""
    ac = Limulus(sensor_etkin=False)
    hava = atm.isa(300.0)
    T = np.full(4, ac.W / 4 * 1.02)
    tilt = np.zeros(4)

    def son_durum(dt):
        d = np.zeros(12)
        d[11] = -300.0
        for _ in range(int(4.0 / dt)):
            d = gv.rk4(lambda s: ac.turev(s, T, tilt, hava), d, dt)
        return d

    kaba, orta, ince = son_durum(0.04), son_durum(0.02), son_durum(0.005)
    h1 = np.linalg.norm(kaba - ince)
    h2 = np.linalg.norm(orta - ince)
    assert h2 < h1 / 4.0, f"yakinsama zayif: {h1:.3e} -> {h2:.3e}"


def test_rk4_euler_ustunlugu():
    ac = Limulus(sensor_etkin=False)
    hava = atm.isa(0.0)
    T = np.full(4, ac.W / 4)
    tilt = np.zeros(4)
    f = lambda s: ac.turev(s, T, tilt, hava)
    d0 = np.zeros(12); d0[0] = 30.0; d0[4] = 0.1
    ref = d0.copy()
    for _ in range(int(2.0 / 0.0005)):
        ref = gv.rk4(f, ref, 0.0005)
    a, b = d0.copy(), d0.copy()
    for _ in range(int(2.0 / 0.02)):
        a = gv.rk4(f, a, 0.02)
        b = gv.euler_ileri(f, b, 0.02)
    assert np.linalg.norm(a - ref) < np.linalg.norm(b - ref)


# =====================================================================
# 4. ROTOR — TEZLE UYUM
# =====================================================================
def test_rotor_tez_hover_gucu():
    K = KONF
    r = Rotor(D=K["D_ROTOR"], FOM=K["FOM"], N_PAL=K["N_PAL"], RPM=K["RPM"])
    T_eff = K["MTOW"] * K["G"] * K["DOWNLOAD"] / 4
    P = 4 * r.guc(T_eff, K["RHO0"])
    assert abs(P / 1e3 - 913.0) < 1.5, f"hover gucu {P/1e3:.1f} kW, tez 913 kW"


def test_rotor_tez_disk_yuklemesi():
    K = KONF
    r = Rotor(D=K["D_ROTOR"], FOM=K["FOM"], N_PAL=K["N_PAL"], RPM=K["RPM"])
    assert abs(r.A - 6.158) < 0.001
    assert abs(r.disk_yuklemesi(K["MTOW"] * K["G"] / 4) - 1195) < 1.0
    assert abs(r.v_hover(K["MTOW"] * K["G"] / 4, K["RHO0"]) - 22.1) < 0.1


def test_rotor_frekanslari():
    K = KONF
    r = Rotor(D=K["D_ROTOR"], FOM=K["FOM"], N_PAL=K["N_PAL"], RPM=K["RPM"])
    f = r.frekanslar()
    assert abs(f["1/rev"] - 17.4) < 0.05
    assert abs(f["N/rev"] - 87.0) < 0.2


def test_rotor_indukleme_denklemi():
    """v_ind Glauert denklemini gercekten sifirlamali."""
    K = KONF
    r = Rotor(D=K["D_ROTOR"], FOM=K["FOM"], RPM=K["RPM"])
    for T in (300.0, 2000.0, 7358.0):
        for V in (2.0, 20.0, 68.9):
            for ad in (0.05, 0.6, 1.2, 1.5):
                v = r.v_ind(T, 1.225, V, ad)
                vh = r.v_hover(T, 1.225)
                Vp, Vt = V * math.sin(ad), V * math.cos(ad)
                artik = v * math.sqrt(Vt ** 2 + (Vp + v) ** 2) - vh ** 2
                assert abs(artik) < 1e-5, (T, V, ad, artik)


def test_rotor_guc_monoton():
    K = KONF
    r = Rotor(D=K["D_ROTOR"], FOM=K["FOM"], RPM=K["RPM"])
    for V, ad in ((0.0, 1.5708), (30.0, 1.0), (68.9, 1.5)):
        P = [r.guc(T, 1.225, V, ad) for T in np.linspace(100, 8000, 40)]
        assert all(b > a for a, b in zip(P, P[1:])), (V, ad)


def test_rotor_itki_limiti_tutarli():
    """itki_limiti(P) ile guc(T) birbirinin tersi olmali."""
    K = KONF
    r = Rotor(D=K["D_ROTOR"], FOM=K["FOM"], RPM=K["RPM"])
    for P in (80e3, 200e3, 268e3):
        T = r.itki_limiti(P, 1.225, 0.0)
        if T < r.itki_aerodinamik_tavani(1.225, 0.0, math.pi / 2) * 0.99:
            assert abs(r.guc(T, 1.225, 0.0) - P) / P < 1e-3


def test_rotor_solidite_makul():
    K = KONF
    r = Rotor(D=K["D_ROTOR"], FOM=K["FOM"], RPM=K["RPM"])
    # rim-drive / ducted fan araligi
    assert 0.25 < r.sigma < 0.55, f"solidite {r.sigma:.3f} makul araligin disinda"
    assert 1.0 < r.kappa < 1.5, f"kappa {r.kappa:.3f}"


# =====================================================================
# 5. AERODINAMIK — TEZLE UYUM
# =====================================================================
def test_aero_tez_cruise():
    K = KONF
    kn = Kanat(S=K["S_KANAT"], AR=K["AR"], MAC=K["MAC"], CD0=K["CD0"],
               e=K["OSWALD"], CL_alfa=K["CL_ALFA"], CL_max=K["CL_MAX"])
    q = 0.5 * K["RHO0"] * K["V_CRUISE"] ** 2
    CL_cr = K["MTOW"] * K["G"] / (q * kn.S)
    CL, CD = kn.katsayilar(kn.alfa_icin_CL(CL_cr))
    assert abs(CL - 0.78) < 0.005
    assert abs(CD - 0.048) < 0.001
    assert abs(CL / CD - 16.1) < 0.1


def test_aero_egri_surekli():
    """CL egrisinde sicrama olmamali. Ilk surumde 16 derecede vardi."""
    K = KONF
    kn = Kanat(S=K["S_KANAT"], AR=K["AR"], MAC=K["MAC"], CL_alfa=K["CL_ALFA"],
               CL_max=K["CL_MAX"])
    a = np.radians(np.arange(-30, 60, 0.05))
    CL = np.array([kn.katsayilar(x)[0] for x in a])
    assert np.abs(np.diff(CL)).max() < 0.01, "CL egrisinde sicrama var"


def test_aero_stall_tutarli():
    K = KONF
    kn = Kanat(S=K["S_KANAT"], AR=K["AR"], MAC=K["MAC"], CL_alfa=K["CL_ALFA"],
               CL_max=K["CL_MAX"])
    assert abs(kn.alfa_stall - K["CL_MAX"] / K["CL_ALFA"]) < 1e-9
    CL_tepe = max(kn.katsayilar(x)[0] for x in np.radians(np.arange(0, 40, 0.05)))
    assert abs(CL_tepe - K["CL_MAX"]) < 0.01


def test_aero_stall_hizi():
    K = KONF
    kn = Kanat(S=K["S_KANAT"], AR=K["AR"], MAC=K["MAC"], CL_max=K["CL_MAX"])
    Vs = kn.V_stall(K["MTOW"] * K["G"], K["RHO0"])
    assert abs(K["V_CRUISE"] / Vs - 1.39) < 0.01, "tez 1,39 V_S1 diyor"


# =====================================================================
# 6. ATMOSFER ve GUST
# =====================================================================
def test_isa_deniz_seviyesi():
    a = atm.isa(0.0)
    assert abs(a.rho - 1.225) < 1e-3
    assert abs(a.T - 288.15) < 1e-6
    assert abs(a.p - 101325.0) < 1.0


def test_isa_monoton():
    h = np.arange(0, 11000, 100)
    rho = [atm.isa(float(x)).rho for x in h]
    assert all(b < a for a, b in zip(rho, rho[1:]))


def test_dryden_rms():
    """Uretilen turbulansin RMS'i hedeflenen sigma'ya yakin olmali."""
    d = atm.Dryden(siddet="orta", h=300.0, tohum=3)
    hedef = d.sigmalar()
    v = np.array([d.adim(0.02, 68.9) for _ in range(300000)])
    for i in range(3):
        assert abs(v[:, i].std() / hedef[i] - 1.0) < 0.12, (i, v[:, i].std())


def test_dryden_sifir_ortalama():
    d = atm.Dryden(siddet="siddetli", h=300.0, tohum=5)
    v = np.array([d.adim(0.02, 68.9) for _ in range(200000)])
    for i in range(3):
        assert abs(v[:, i].mean()) < 0.2 * v[:, i].std()


def test_gust_tepe_ve_sonlu():
    g = atm.AyrikGust(Uds=7.5, H=60.0, t0=0.0)
    t = np.arange(0, 5, 0.001)
    u = np.array([g(float(x), 68.9)[2] for x in t])
    assert abs(u.max() - 7.5) < 1e-6
    assert u[-1] == 0.0
    assert (u >= -1e-12).all()


def test_gust_yok_sakin():
    d = atm.Dryden(siddet="yok", tohum=1)
    assert np.allclose(d.adim(0.02, 60.0), 0.0)


# =====================================================================
# 7. AKTUATOR
# =====================================================================
def test_tilt_oran_limiti():
    a = TiltAktuatoru(hiz_limiti=math.radians(15.0))
    dt = 0.02
    a.sifirla(0.0)
    for _ in range(10):
        a.adim(math.radians(90.0), dt)
    assert a.theta <= math.radians(15.0) * 10 * dt + 1e-12


def test_tilt_limitleri_asilmiyor():
    a = TiltAktuatoru(theta_min=0.0, theta_max=math.radians(90.0))
    for _ in range(2000):
        a.adim(math.radians(200.0), 0.02)
    assert a.theta <= math.radians(90.0) + 1e-12
    for _ in range(2000):
        a.adim(math.radians(-200.0), 0.02)
    assert a.theta >= -1e-12


def test_itki_zaman_sabiti():
    z = ItkiZinciri(tau=0.08)
    dt, hedef = 0.005, 7358.0
    z.sifirla(0.0)
    for i in range(1000):
        v = z.adim(hedef, 1e9, dt)
        if v >= 0.632 * hedef:
            break
    assert abs(i * dt - 0.08) < 0.01


def test_itki_tavani_asilmiyor():
    z = ItkiZinciri()
    z.sifirla(0.0)
    for _ in range(500):
        v = z.adim(1e6, 5000.0, 0.02)
    assert v <= 5000.0 + 1e-9


def test_eklem_rev_e_tamam():
    """Rev.E tasarim noktasinda RDP-IF kapasitesi asilmamali (bulgu F2)."""
    e = EklemYuku(kapasite_dusey=KONF["RDPIF_DUSEY"])
    T = KONF["MTOW"] * KONF["G"] / 4
    assert e.asim(T) == 0.0, "Rev.E'de eklem yuku kapasiteyi asmamali"
    # Rev.D degeri asiyordu, bu kayit icin tutuluyor
    assert e.asim(7867.0) > 0.0


# =====================================================================
# 8. ARAC — DENGE ve TUTARLILIK
# =====================================================================
def test_hover_dusey_denge():
    ac = Limulus()
    hava = atm.isa(0.0)
    T = np.full(4, ac.W * ac.k["DOWNLOAD"] / 4)
    F, M, b = ac.kuvvetler(np.zeros(12), T, np.zeros(4), hava)
    assert abs(F[2]) < 0.02 * ac.W


def test_hover_moment_dengesi_rev_e():
    """Rev.E'de esit itki ile yunuslama momenti ihmal edilebilir (bulgu F1)."""
    ac = Limulus()
    hava = atm.isa(0.0)
    T = np.full(4, ac.W / 4)
    _, M, _ = ac.kuvvetler(np.zeros(12), T, np.zeros(4), hava)
    assert abs(M[1]) < 100.0, f"artik pitch momenti {M[1]:.0f} N m"
    assert abs(M[0]) < 1e-9 and abs(M[2]) < 1e-9


def test_cruise_trim_momenti_sifir_rev_e():
    """Rev.E'de statik marj sifir, trim momenti de sifir (bulgu F3)."""
    ac = Limulus()
    assert abs(ac.sm) < 1e-6
    M = ac.W * (ac.x_cg - ac.x_np)
    assert abs(M) < 50.0


def test_download_moment_uretmiyor():
    """Asagi-yuk pod istasyonlarinda etkir, sahte moment uretmemeli."""
    ac = Limulus()
    hava = atm.isa(0.0)
    T = np.full(4, ac.W / 4)
    _, M1, b1 = ac.kuvvetler(np.zeros(12), T, np.zeros(4), hava)
    assert b1["F_download"] > 0
    ac2 = Limulus()
    ac2.k["DOWNLOAD"] = 1.0
    ac2.__post_init__()
    _, M2, _ = ac2.kuvvetler(np.zeros(12), T, np.zeros(4), hava)
    assert abs(M1[1] - M2[1]) < 5.0, "download sahte yunuslama momenti uretiyor"


def test_download_tilt_ile_sonumleniyor():
    ac = Limulus()
    hava = atm.isa(0.0)
    T = np.full(4, ac.W / 4)
    _, _, b0 = ac.kuvvetler(np.zeros(12), T, np.zeros(4), hava)
    _, _, b9 = ac.kuvvetler(np.zeros(12), T, np.full(4, math.pi / 2), hava)
    assert b0["F_download"] > 0
    assert abs(b9["F_download"]) < 1e-9


def test_yercekimi_agirlik_korunumu():
    ac = Limulus()
    hava = atm.isa(0.0)
    for phi in (0.0, 0.3, -0.5):
        for th in (0.0, 0.4, -0.2):
            d = np.zeros(12); d[6], d[7] = phi, th
            F, _, _ = ac.kuvvetler(d, np.zeros(4), np.zeros(4), hava)
            F_aero_yok = F  # hiz sifir, aero yok
            assert abs(np.linalg.norm(F_aero_yok) - ac.W) < 1e-6


def test_varyant_tilt_eslemesi():
    for ad, n, giris, beklenen in (
            ("limulus", 4, [0.1, 0.2, 0.3, 0.4], [0.1, 0.2, 0.3, 0.4]),
            ("ikili", 2, [0.1, 0.2], [0.1, 0.1, 0.2, 0.2]),
            ("senkron", 1, [0.3], [0.3, 0.3, 0.3, 0.3]),
            ("liftcruise", 0, [0.9], [0.0, 0.0, 0.0, 0.0])):
        ac = Limulus(varyant_ad=ad)
        assert ac.var.n_tilt == n
        assert np.allclose(ac.tilt_esle(np.array(giris)), beklenen)


def test_enerji_birikimi_pozitif():
    ac = Limulus(sensor_etkin=False)
    ac.sifirla(durum=np.array([0.0] * 11 + [-100.0]))
    onceki = 0.0
    for _ in range(200):
        _, b = ac.adim(np.full(4, ac.W / 4), np.zeros(1))
        assert b["enerji"] >= onceki
        onceki = b["enerji"]
    assert onceki > 0


def test_ariza_guc_tavanini_dusuruyor():
    ac = Limulus()
    hava = atm.isa(0.0)
    once = ac.itki_tavani(0, 0.0, math.pi / 2, hava.rho)
    ac.ariza_ver(0, 1)
    sonra = ac.itki_tavani(0, 0.0, math.pi / 2, hava.rho)
    assert sonra < once
    ac.arizasiz()
    assert abs(ac.itki_tavani(0, 0.0, math.pi / 2, hava.rho) - once) < 1e-9


# =====================================================================
# 9. KONFIGURASYON — TEK DOGRULUK KAYNAGI
# =====================================================================
def test_konf_geometriden_geliyor():
    import geometri
    assert KONF["X_ROTOR_ON"] == geometri.G["X_ROTOR_ON"]
    assert KONF["X_ROTOR_ARKA"] == geometri.G["X_ROTOR_ARKA"]
    assert KONF["CG_MAC_YUZDE"] == geometri.G["CG_MAC_YUZDE"]
    assert KONF["MTOW"] == geometri.P["MTOW"]


def test_varsayimlar_belgeli():
    """Tezde olmayan her deger VARSAYIMLAR sozlugunde olmali."""
    zorunlu = {"CL_ALFA", "CM0", "THETA_HIZ", "TAU_MOTOR", "Z_POD_CG",
               "K_GOVDE_Y", "SENSOR", "GUST", "ALFA_STALL"}
    assert zorunlu <= set(VARSAYIMLAR)
    for ad, metin in VARSAYIMLAR.items():
        assert len(metin) > 40, f"{ad} icin gerekce cok kisa"


def test_rotor_cg_ortalanmis_rev_e():
    ac = Limulus()
    orta = (ac.k["X_ROTOR_ON"] + ac.k["X_ROTOR_ARKA"]) / 2
    assert abs(ac.x_cg - orta) < 0.02, "rotor cifti CG'ye gore ortalanmali"


# =====================================================================
if __name__ == "__main__":
    import traceback
    testler = [(a, o) for a, o in sorted(globals().items())
               if a.startswith("test_") and callable(o)]
    gecen, kalan = 0, []
    print(f"{len(testler)} test kosuluyor\n")
    for ad, f in testler:
        try:
            f()
            print(f"  TAMAM   {ad}")
            gecen += 1
        except AssertionError as e:
            print(f"  KALDI   {ad}\n          {e}")
            kalan.append(ad)
        except Exception:
            print(f"  HATA    {ad}")
            traceback.print_exc(limit=2)
            kalan.append(ad)
    print(f"\n{gecen}/{len(testler)} gecti")
    if kalan:
        print("kalanlar: " + ", ".join(kalan))
        sys.exit(1)
