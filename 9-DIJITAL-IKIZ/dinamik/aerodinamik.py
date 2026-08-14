#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AERODINAMIK MODEL — kanat + merkez govde

Tezin Bolum 4'teki suruklenme polari kullanilir.
    CL = CL_alfa * (alfa - alfa_0)     stall oncesi
    CD = CD0 + CL^2 / (pi AR e)

Stall sonrasi duz plaka modeline yumusak gecis yapilir. Bu, egitim
sirasinda ajanin zarf disina ciktigi durumlarda modelin patlamasini
onler ve fiziksel olarak da dogru yondedir.

Aerodinamik kuvvet NOTR NOKTADA etkitilir. Tez notr noktayi %33 MAC
olarak veriyor ve bu deger govde ile nacelle katkilarini zaten iceriyor.
Kanat ceyrek-veterinde (%25 MAC) etkitmek govde katkisini iki kez
saymak olurdu.

⚠️ Bu model CFD ile dogrulanmamistir. Tezin Bolum 14.4'teki gecerlilik
sinirlari burada da gecerlidir. Karsilastirma GORELIDIR — dort varyant
ayni belirsizligi paylasir.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class Kanat:
    S: float                  # m2
    AR: float
    MAC: float
    CD0: float = 0.027
    e: float = 0.82
    CL_alfa: float = 4.90     # 1/rad   (VARSAYIM)
    CL_max: float = 1.50
    alfa_stall: float | None = None   # None -> CL_max/CL_alfa'dan turetilir
    alfa_0: float = 0.0       # sifir-tasima hucum acisi
    Cm0: float = 0.0          # (VARSAYIM)

    def __post_init__(self):
        # alfa_stall bagimsiz bir varsayim DEGILDIR. CL_max ve CL_alfa
        # verildiginde tek tutarli deger vardir. Ayri verilirse egride
        # sicrama olusur, bu ilk surumde yakalandi.
        turetilen = self.alfa_0 + self.CL_max / self.CL_alfa
        if self.alfa_stall is None:
            self.alfa_stall = turetilen
        elif abs(self.alfa_stall - turetilen) > math.radians(0.2):
            raise ValueError(
                f"alfa_stall ({math.degrees(self.alfa_stall):.2f} deg) "
                f"CL_max/CL_alfa ile tutarsiz "
                f"({math.degrees(turetilen):.2f} deg). Egride sicrama olur.")

    def katsayilar(self, alfa: float) -> tuple[float, float]:
        """(CL, CD) verilen hucum acisi icin. Stall sonrasi dahil."""
        a = float(alfa)
        a_s = self.alfa_stall
        if abs(a) <= a_s:
            CL = self.CL_alfa * (a - self.alfa_0)
            CL = float(np.clip(CL, -self.CL_max, self.CL_max))
            CD = self.CD0 + CL ** 2 / (math.pi * self.AR * self.e)
            return CL, CD
        # stall sonrasi: duz plaka. a_s'te surekli olacak sekilde harmanla
        isaret = 1.0 if a >= 0 else -1.0
        CL_plaka = 2.0 * math.sin(a) * math.cos(a)
        CD_plaka = 2.0 * math.sin(a) ** 2 + self.CD0
        # 5 derecelik gecis bandi
        band = math.radians(8.0)
        w = float(np.clip((abs(a) - a_s) / band, 0.0, 1.0))
        w = w * w * (3.0 - 2.0 * w)          # yumusak adim, turevi de surekli
        CL_lin = isaret * self.CL_max
        CD_lin = self.CD0 + self.CL_max ** 2 / (math.pi * self.AR * self.e)
        CL = (1 - w) * CL_lin + w * CL_plaka
        CD = (1 - w) * CD_lin + w * CD_plaka
        return CL, CD

    def kuvvet(self, q: float, alfa: float) -> tuple[float, float, float]:
        """Govde eksenlerinde (X, Z, M_ac). q dinamik basinc."""
        CL, CD = self.katsayilar(alfa)
        L = q * self.S * CL
        D = q * self.S * CD
        X = -D * math.cos(alfa) + L * math.sin(alfa)
        Z = -D * math.sin(alfa) - L * math.cos(alfa)
        M = self.Cm0 * q * self.S * self.MAC
        return X, Z, M

    def LD(self, alfa: float) -> float:
        CL, CD = self.katsayilar(alfa)
        return CL / CD if CD > 1e-9 else 0.0

    def alfa_icin_CL(self, CL_hedef: float) -> float:
        return self.alfa_0 + CL_hedef / self.CL_alfa

    def V_stall(self, W: float, rho: float) -> float:
        return math.sqrt(2.0 * W / (rho * self.S * self.CL_max))


@dataclass
class Govde:
    """Merkez govde (karapas) yanal kuvvet ve yaw momenti.

    Boyuna katkisi notr nokta konumuna zaten dahildir, burada
    tekrar sayilmaz. Yalniz yanal eksende modellenir.
    ⚠️ K_y tezde yok, mertebe tahmini (VARSAYIMLAR["K_GOVDE_Y"]).
    """
    S_yan: float = 4.4
    K_y: float = 0.55

    def kuvvet(self, q: float, beta: float) -> tuple[float, float]:
        """(Y, N) yanal kuvvet ve yaw momenti katsayi tabanli."""
        Y = -q * self.S_yan * self.K_y * math.sin(2.0 * beta) / 2.0 * 2.0
        return Y, 0.0


if __name__ == "__main__":
    from konfigurasyon import KONF as K

    kn = Kanat(S=K["S_KANAT"], AR=K["AR"], MAC=K["MAC"], CD0=K["CD0"],
               e=K["OSWALD"], CL_alfa=K["CL_ALFA"], CL_max=K["CL_MAX"],
               Cm0=K["CM0"])
    rho, V = K["RHO0"], K["V_CRUISE"]
    q = 0.5 * rho * V ** 2
    W = K["MTOW"] * K["G"]

    CL_cr = W / (q * kn.S)
    CL, CD = kn.katsayilar(kn.alfa_icin_CL(CL_cr))
    print(f"cruise CL     {CL:.3f}   (tez 0,78)")
    print(f"cruise CD     {CD:.4f}  (tez 0,048)")
    print(f"cruise L/D    {CL/CD:.2f}   (tez 16,1)")
    print(f"stall hizi    {kn.V_stall(W, rho):.1f} m/s")
    print(f"alfa_stall    {math.degrees(kn.alfa_stall):.2f} deg  (CL_max/CL_alfa'dan turetildi)")
    print(f"cruise / V_S1 {V/kn.V_stall(W, rho):.2f}   (tez 1,39)")

    print("\nkatsayi egrisi")
    print("  alfa     CL      CD     L/D")
    for ad in (-5, 0, 4, 8, 12, 16, 18, 25, 45, 90):
        CL, CD = kn.katsayilar(math.radians(ad))
        print(f"  {ad:>4}   {CL:6.3f}  {CD:6.4f}  {CL/CD:6.2f}")

    print("\nstall gecisi surekli mi (alfa_stall civarinda)")
    for ad in (16.5, 17.0, 17.5, 17.6, 18.0, 19.0):
        CL, CD = kn.katsayilar(math.radians(ad))
        print(f"  {ad:>5.1f}   CL={CL:.4f}  CD={CD:.4f}")
