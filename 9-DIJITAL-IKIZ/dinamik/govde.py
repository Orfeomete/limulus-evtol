#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RIJIT GOVDE — alti serbestlik dereceli hareket denklemleri

Durum vektoru (12)
    0:3   [u v w]        govde ekseninde hiz              m/s
    3:6   [p q r]        govde ekseninde acisal hiz       rad/s
    6:9   [phi th psi]   Euler acilari                    rad
    9:12  [x y z]        yer ekseninde konum, z ASAGI     m

⚠️ IKI AYRI x EKSENI VAR, KARISTIRILMAZ
    x_ist  "istasyon"  burun x=0, GERIYE artar    geometri.py ve tez
    x_b    "govde"     CG x=0, ILERIYE artar      dinamik denklemler
    donusum  x_b = x_cg - x_ist                   govde_x()

Bu donusum ilk surumde atlandi ve yunuslama momentlerinin isareti
tersti. testler/test_isaret.py bunu kalici olarak kontrol eder.

Integrator: klasik dorduncu derece Runge-Kutta. Sabit adim. Adim
bagimsizligi test_integrator.py'de dogrulanir.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


# =====================================================================
# DONUSUMLER
# =====================================================================
def govde_yer_matrisi(phi: float, th: float, psi: float) -> np.ndarray:
    """Govde ekseninden yer eksenine donusum (R_yer<-govde)."""
    sp, cp = math.sin(phi), math.cos(phi)
    st, ct = math.sin(th), math.cos(th)
    ss, cs = math.sin(psi), math.cos(psi)
    return np.array([
        [ct * cs, sp * st * cs - cp * ss, cp * st * cs + sp * ss],
        [ct * ss, sp * st * ss + cp * cs, cp * st * ss - sp * cs],
        [-st,     sp * ct,                cp * ct],
    ])


def euler_hizi(phi: float, th: float, p: float, q: float, r: float) -> np.ndarray:
    """Govde acisal hizindan Euler aci turevlerine."""
    sp, cp = math.sin(phi), math.cos(phi)
    ct = math.cos(th)
    ct = math.copysign(max(abs(ct), 1e-6), ct if ct != 0 else 1.0)
    tt = math.tan(th)
    return np.array([
        p + (q * sp + r * cp) * tt,
        q * cp - r * sp,
        (q * sp + r * cp) / ct,
    ])


def yercekimi_govde(phi: float, th: float, m: float, g: float) -> np.ndarray:
    """Agirligin govde eksenlerindeki bilesenleri."""
    return m * g * np.array([-math.sin(th),
                             math.sin(phi) * math.cos(th),
                             math.cos(phi) * math.cos(th)])


# =====================================================================
# ATALET
# =====================================================================
def capraz(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """3 boyutlu vektorel carpim. np.cross genel amaclidir ve bu boyutta
    yaklasik 10 kat yavastir. Dogru sonuc testler/test_govde.py'de
    np.cross ile karsilastirilarak dogrulanir."""
    return np.array([a[1] * b[2] - a[2] * b[1],
                     a[2] * b[0] - a[0] * b[2],
                     a[0] * b[1] - a[1] * b[0]])


def atalet_matrisi(Ixx: float, Iyy: float, Izz: float, Ixz: float) -> np.ndarray:
    return np.array([[Ixx, 0.0, -Ixz],
                     [0.0, Iyy, 0.0],
                     [-Ixz, 0.0, Izz]])


# =====================================================================
# HAREKET DENKLEMLERI
# =====================================================================
def turev(durum: np.ndarray, F: np.ndarray, M: np.ndarray,
          m: float, I: np.ndarray, I_inv: np.ndarray) -> np.ndarray:
    """Durum turevi. F ve M govde ekseninde, agirlik F'ye DAHIL."""
    u, v, w = durum[0:3]
    p, q, r = durum[3:6]
    phi, th, psi = durum[6:9]

    om = np.array([p, q, r])
    vel = np.array([u, v, w])

    acc = F / m - capraz(om, vel)
    omd = I_inv @ (M - capraz(om, I @ om))
    eul = euler_hizi(phi, th, p, q, r)
    yer = govde_yer_matrisi(phi, th, psi) @ vel
    return np.concatenate([acc, omd, eul, yer])


# =====================================================================
# INTEGRATOR
# =====================================================================
def rk4(f, durum: np.ndarray, dt: float) -> np.ndarray:
    """Klasik RK4. f(durum) -> turev. Bir adim boyunca kontrol sabit."""
    k1 = f(durum)
    k2 = f(durum + 0.5 * dt * k1)
    k3 = f(durum + 0.5 * dt * k2)
    k4 = f(durum + dt * k3)
    return durum + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def euler_ileri(f, durum: np.ndarray, dt: float) -> np.ndarray:
    """Karsilastirma icin. Uretimde kullanilmaz."""
    return durum + dt * f(durum)


# =====================================================================
# YARDIMCILAR
# =====================================================================
def aci_sar(a: float) -> float:
    """Aciyi [-pi, pi] araligina sarar."""
    return (a + math.pi) % (2 * math.pi) - math.pi


V_ESIK_ALT = 0.3
V_ESIK_UST = 1.0


def _yumusak(x: float) -> float:
    """Turevi de surekli olan 0-1 gecis fonksiyonu."""
    x = min(max(x, 0.0), 1.0)
    return x * x * (3.0 - 2.0 * x)


def hava_acilari(u: float, v: float, w: float) -> tuple[float, float, float]:
    """(V, alfa, beta). Dusuk hizda hucum acisi tanimsizdir.

    ⚠️ Gecis KESKIN OLMAMALI. Ilk surumde V < 0,5 icin sert bir anahtar
    vardi. Bu, turevde bir sicrama dogurdugu icin RK4'un dorduncu
    derece yakinsamasini bozuyordu — adim yariya inince hata 16 kat
    degil yalnizca 3 kat kuculuyordu. testler/test_dinamik.py
    test_rk4_adim_bagimsizligi bunu yakaladi. Anahtar yumusak bir
    harmana cevrildi.
    """
    V = math.sqrt(u * u + v * v + w * w)
    if V <= V_ESIK_ALT:
        return V, 0.0, 0.0
    agirlik = _yumusak((V - V_ESIK_ALT) / (V_ESIK_UST - V_ESIK_ALT))
    alfa = math.atan2(w, u) * agirlik
    beta = math.asin(float(np.clip(v / V, -1.0, 1.0))) * agirlik
    return V, alfa, beta


def yuk_faktoru(F_aero_itki: np.ndarray, m: float, g: float) -> float:
    """n = aerodinamik + itki kuvvetlerinin dusey bileseni / agirlik."""
    return float(-F_aero_itki[2] / (m * g))


if __name__ == "__main__":
    print("DONUSUM KONTROLLERI")
    R = govde_yer_matrisi(0.0, 0.0, 0.0)
    print(f"  R(0,0,0) birim mi          {np.allclose(R, np.eye(3))}")
    for _ in range(20):
        a = np.random.default_rng(0).uniform(-1, 1, 3)
    R = govde_yer_matrisi(0.3, -0.2, 1.1)
    print(f"  R ortogonal mi             {np.allclose(R @ R.T, np.eye(3))}")
    print(f"  det(R) = {np.linalg.det(R):.10f}")

    print("\nATALET")
    I = atalet_matrisi(578.0, 5284.0, 5301.0, 555.0)
    print(f"  simetrik mi                {np.allclose(I, I.T)}")
    oz = np.linalg.eigvalsh(I)
    print(f"  ozdegerler {oz.round(1)}  hepsi pozitif mi {bool((oz > 0).all())}")

    print("\nSERBEST DUSUS TESTI (kuvvet yok, yalniz yercekimi)")
    m, g = 3000.0, 9.81
    I_inv = np.linalg.inv(I)
    d = np.zeros(12)
    dt, T = 0.005, 5.0
    for _ in range(int(T / dt)):
        F = yercekimi_govde(d[6], d[7], m, g)
        d = rk4(lambda s: turev(s, F, np.zeros(3), m, I, I_inv), d, dt)
    print(f"  {T} s sonra dusey hiz  {d[2]:8.4f} m/s   analitik {g*T:8.4f}")
    print(f"  {T} s sonra irtifa     {d[11]:8.4f} m     analitik {0.5*g*T*T:8.4f}")
    print(f"  bagil hata             {abs(d[11]-0.5*g*T*T)/(0.5*g*T*T):.2e}")
