#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATMOSFER ve BOZUCU MODELI

Iki parca.
  ISA        standart atmosfer, 0-11 km troposfer
  Ruzgar     sabit ruzgar + Dryden turbulans + 1-cos ayrik gust

Dryden ve 1-cos parametreleri MIL-HDBK-1797 dusuk irtifa modelinden
alinmistir. Tezde bu degerler yok, VARSAYIMLAR["GUST"] altinda kayitli.

Isaret sistemi: ruzgar YER ekseninde uretilir, arac tarafinda govde
eksenine cevrilir. Pozitif w_z asagi dogru ruzgar demektir.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# ISA sabitleri
T0 = 288.15          # K
P0 = 101325.0        # Pa
RHO0 = 1.225         # kg/m3
L_LAPSE = 0.0065     # K/m
R_GAZ = 287.05287    # J/(kg K)
G0 = 9.80665         # m/s2


@dataclass(frozen=True)
class Hava:
    h: float          # m
    T: float          # K
    p: float          # Pa
    rho: float        # kg/m3
    a: float          # m/s, ses hizi

    def q(self, V: float) -> float:
        """Dinamik basinc"""
        return 0.5 * self.rho * V * V


def isa(h: float) -> Hava:
    """ISA standart atmosfer. h metre, 0-11.000 m gecerli."""
    h = float(np.clip(h, -500.0, 11000.0))
    T = T0 - L_LAPSE * h
    p = P0 * (T / T0) ** (G0 / (L_LAPSE * R_GAZ))
    rho = p / (R_GAZ * T)
    a = math.sqrt(1.4 * R_GAZ * T)
    return Hava(h=h, T=T, p=p, rho=rho, a=a)


# =====================================================================
# DRYDEN TURBULANS
# =====================================================================
@dataclass
class Dryden:
    """Dryden surekli turbulans, birinci dereceden yaklasim.

    Tam Dryden filtresi u icin birinci, v ve w icin ikinci derecedir.
    Burada u, v, w icin birinci dereceden Markov yaklasimi kullanilmistir.
    Bu yaklasim spektrumun dusuk frekans bolgesini dogru, yuksek frekans
    kuyrugunu yumusak verir. Ucus dinamigi bant genisligi icin yeterlidir
    ve durum uzayini kucuk tutar.

    siddet: "hafif" 1,5 m/s · "orta" 3,0 m/s · "siddetli" 6,0 m/s (RMS)
    """
    siddet: str = "orta"
    h: float = 300.0                       # m, irtifa
    tohum: int | None = None
    _rng: np.random.Generator = field(init=False, repr=False)
    _v: np.ndarray = field(init=False, repr=False)

    SIDDET = {"yok": 0.0, "hafif": 1.5, "orta": 3.0, "siddetli": 6.0}

    def __post_init__(self):
        if self.siddet not in self.SIDDET:
            raise KeyError(f"siddet {self.siddet!r} taninmiyor. "
                           f"Secenekler: {list(self.SIDDET)}")
        self._rng = np.random.default_rng(self.tohum)
        self._v = np.zeros(3)

    # --- olcek uzunluklari, MIL-HDBK-1797 dusuk irtifa ----------------
    def olcekler(self) -> tuple[float, float, float]:
        h = max(self.h, 10.0)
        if h < 305.0:                       # 1000 ft alti
            Lw = h
            Lu = Lv = h / (0.177 + 0.000823 * h) ** 1.2
        else:
            Lu = Lv = Lw = 533.0
        return Lu, Lv, Lw

    def sigmalar(self) -> tuple[float, float, float]:
        """RMS siddetler [su, sv, sw], m/s.

        MIL-HDBK-1797 dusuk irtifa modelinde referans DUSEY bilesendir.
        Yatay bilesenler irtifaya bagli bir carpanla daha buyuktur.
        SIDDET sozlugundeki deger sigma_w olarak tanimlanmistir.
        """
        sw = self.SIDDET[self.siddet]
        h = max(self.h, 10.0)
        if h < 305.0:
            su = sv = sw / (0.177 + 0.000823 * h) ** 0.4
            return su, sv, sw
        return sw, sw, sw

    def adim(self, dt: float, V: float) -> np.ndarray:
        """Bir zaman adimi turbulans hizi [u, v, w], yer ekseninde m/s."""
        if self.SIDDET[self.siddet] == 0.0:
            return np.zeros(3)
        V = max(V, 5.0)
        L = np.array(self.olcekler())
        sig = np.array(self.sigmalar())
        tau = L / V                          # korelasyon zamani
        beta = np.exp(-dt / np.maximum(tau, 1e-3))
        q = sig * np.sqrt(1.0 - beta ** 2)
        self._v = beta * self._v + q * self._rng.standard_normal(3)
        return self._v.copy()

    def sifirla(self):
        self._v = np.zeros(3)


# =====================================================================
# AYRIK GUST  (1-cos, CS-25.341 / SC-VTOL bicimi)
# =====================================================================
@dataclass
class AyrikGust:
    """1-cos bicimli ayrik gust.

    U(s) = (Uds/2) * (1 - cos(pi*s/H))     0 <= s <= 2H
    s: gust icinde katedilen mesafe, H: yari gust uzunlugu
    """
    Uds: float = 7.5          # m/s, tepe gust hizi
    H: float = 60.0           # m, yari gust uzunlugu
    eksen: str = "w"          # "u", "v" ya da "w"
    t0: float = 2.0           # s, baslangic ani

    def __call__(self, t: float, V: float) -> np.ndarray:
        g = np.zeros(3)
        if t < self.t0:
            return g
        s = (t - self.t0) * max(V, 1.0)
        if s > 2.0 * self.H:
            return g
        u = 0.5 * self.Uds * (1.0 - math.cos(math.pi * s / self.H))
        g[{"u": 0, "v": 1, "w": 2}[self.eksen]] = u
        return g


# =====================================================================
@dataclass
class Ruzgar:
    """Sabit ruzgar + turbulans + ayrik gust toplami."""
    sabit: np.ndarray = field(default_factory=lambda: np.zeros(3))
    dryden: Dryden | None = None
    gust: AyrikGust | None = None

    def __call__(self, t: float, h: float, V: float, dt: float) -> np.ndarray:
        w = np.array(self.sabit, dtype=float).copy()
        if self.dryden is not None:
            self.dryden.h = max(h, 10.0)
            w += self.dryden.adim(dt, V)
        if self.gust is not None:
            w += self.gust(t, V)
        return w

    def sifirla(self):
        if self.dryden is not None:
            self.dryden.sifirla()


SAKIN = Ruzgar()


if __name__ == "__main__":
    print("ISA")
    for h in (0, 300, 1000, 3000):
        a = isa(h)
        print(f"  h={h:>5} m  T={a.T:6.2f} K  rho={a.rho:.4f}  a={a.a:.1f} m/s")

    print("\nDryden RMS dogrulamasi (400.000 adim, dt=0,02 s, V=68,9 m/s, h=300 m)")
    print("  SIDDET sozlugu sigma_w'yi tanimlar, yatay bilesenler daha buyuk olur.")
    for s in ("hafif", "orta", "siddetli"):
        d = Dryden(siddet=s, h=300.0, tohum=42)
        hedef = d.sigmalar()
        v = np.array([d.adim(0.02, 68.9) for _ in range(400000)])
        print(f"  {s:<9} hedef u={hedef[0]:.2f} v={hedef[1]:.2f} w={hedef[2]:.2f}"
              f"   olculen u={v[:,0].std():.2f} v={v[:,1].std():.2f} w={v[:,2].std():.2f}")
    d = Dryden(siddet="orta", h=300.0)
    print(f"  olcek uzunluklari h=300 m: Lu={d.olcekler()[0]:.0f} Lv={d.olcekler()[1]:.0f} "
          f"Lw={d.olcekler()[2]:.0f} m")

    print("\n1-cos ayrik gust tepe kontrolu")
    g = AyrikGust(Uds=7.5, H=60.0, t0=0.0)
    tepe = max(g(t, 68.9)[2] for t in np.arange(0, 4, 0.001))
    print(f"  hedef {7.5:.2f} m/s   olculen {tepe:.3f} m/s")
