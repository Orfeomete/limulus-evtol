#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENSOR MODELI — gurultu, sapma (bias), gecikme, ornekleme

Ajanin gordugu sey aracin GERCEK durumu degil, sensorlerin OLCTUGU
durumdur. Bu ayrim gozardi edilirse egitilen politika gercekte var
olmayan bir bilgiye dayanir.

Modellenen bozulmalar.
  beyaz gurultu       her okumada bagimsiz
  rastgele yuruyus    IMU sapmasi, yavas kayan
  gecikme             tasima gecikmesi, halka tampon ile
  ornekleme           sensor hizi cozum hizindan dusuk

⚠️ Buradaki sayilarin hicbiri tezde yok. Ticari taktik sinif IMU ve
GNSS mertebesinde secilmistir (VARSAYIMLAR["SENSOR"]). Mutlak
sonuclar bu secime kosulludur, dort varyant ayni sensor setini
paylastigi icin KARSILASTIRMA etkilenmez.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

import numpy as np

# ---------------------------------------------------------------------
# Sensor spesifikasyonu — hepsi VARSAYIM
# ---------------------------------------------------------------------
SPEK = {
    "imu_acisal_hiz": dict(gurultu=0.002, sapma_yuruyus=1e-5, hiz=200.0,
                           gecikme=0.005, birim="rad/s"),
    "imu_ivme":       dict(gurultu=0.02,  sapma_yuruyus=1e-4, hiz=200.0,
                           gecikme=0.005, birim="m/s2"),
    "tutum":          dict(gurultu=0.003, sapma_yuruyus=2e-6, hiz=100.0,
                           gecikme=0.010, birim="rad"),
    "hava_verisi":    dict(gurultu=0.5,   sapma_yuruyus=1e-4, hiz=20.0,
                           gecikme=0.050, birim="m/s"),
    "gnss_konum":     dict(gurultu=1.5,   sapma_yuruyus=1e-3, hiz=10.0,
                           gecikme=0.100, birim="m"),
    "gnss_hiz":       dict(gurultu=0.05,  sapma_yuruyus=1e-4, hiz=10.0,
                           gecikme=0.100, birim="m/s"),
}


@dataclass
class Kanal:
    """Tek bir sensor kanali (skaler ya da vektor)."""
    n: int
    gurultu: float
    sapma_yuruyus: float
    hiz: float
    gecikme: float
    dt: float
    tohum: int | None = None

    def __post_init__(self):
        self._rng = np.random.default_rng(self.tohum)
        self._sapma = np.zeros(self.n)
        self._son = np.zeros(self.n)
        self._sayac = 0.0
        d = max(1, int(round(self.gecikme / self.dt)))
        self._tampon: deque = deque([np.zeros(self.n)] * d, maxlen=d)
        self._periyot = 1.0 / self.hiz

    def __call__(self, gercek: np.ndarray) -> np.ndarray:
        gercek = np.asarray(gercek, dtype=float).reshape(self.n)
        # ornekleme: sensor hizi cozum hizindan dusukse deger tutulur
        self._sayac += self.dt
        if self._sayac >= self._periyot:
            self._sayac = 0.0
            self._sapma += self.sapma_yuruyus * math.sqrt(self.dt) \
                * self._rng.standard_normal(self.n)
            self._son = (gercek + self._sapma
                         + self.gurultu * self._rng.standard_normal(self.n))
        self._tampon.append(self._son.copy())
        return self._tampon[0].copy()

    def sifirla(self):
        self._sapma = np.zeros(self.n)
        self._son = np.zeros(self.n)
        self._sayac = 0.0
        self._tampon = deque([np.zeros(self.n)] * self._tampon.maxlen,
                             maxlen=self._tampon.maxlen)


@dataclass
class SensorPaketi:
    """Tam sensor seti. Gercek durumu alir, olculen durumu dondurur."""
    dt: float = 0.02
    tohum: int | None = None
    etkin: bool = True

    def __post_init__(self):
        r = np.random.default_rng(self.tohum)
        def kanal(ad, n):
            s = SPEK[ad]
            return Kanal(n=n, gurultu=s["gurultu"],
                         sapma_yuruyus=s["sapma_yuruyus"], hiz=s["hiz"],
                         gecikme=s["gecikme"], dt=self.dt,
                         tohum=int(r.integers(0, 2**31)))
        self.k = {
            "acisal_hiz": kanal("imu_acisal_hiz", 3),
            "tutum": kanal("tutum", 3),
            "hava_hizi": kanal("hava_verisi", 3),
            "konum": kanal("gnss_konum", 3),
            "hiz": kanal("gnss_hiz", 3),
        }

    def __call__(self, durum: np.ndarray) -> np.ndarray:
        """durum: 12 elemanli gercek durum -> olculen 12 elemanli durum."""
        if not self.etkin:
            return np.asarray(durum, dtype=float).copy()
        d = np.asarray(durum, dtype=float)
        o = d.copy()
        o[0:3] = self.k["hava_hizi"](d[0:3])
        o[3:6] = self.k["acisal_hiz"](d[3:6])
        o[6:9] = self.k["tutum"](d[6:9])
        o[9:12] = self.k["konum"](d[9:12])
        return o

    def sifirla(self):
        for k in self.k.values():
            k.sifirla()

    def azami_gecikme(self) -> float:
        return max(s["gecikme"] for s in SPEK.values())


if __name__ == "__main__":
    print("SENSOR SPESIFIKASYONU  (hepsi VARSAYIM, tezde yok)")
    print(f"  {'kanal':<16} {'gurultu':>9} {'sapma/s':>10} {'hiz':>7} "
          f"{'gecikme':>9}  birim")
    for ad, s in SPEK.items():
        print(f"  {ad:<16} {s['gurultu']:>9.4f} {s['sapma_yuruyus']:>10.1e} "
              f"{s['hiz']:>6.0f}Hz {s['gecikme']*1000:>7.0f}ms  {s['birim']}")

    dt = 0.02
    sp = SensorPaketi(dt=dt, tohum=7)
    gercek = np.zeros(12)
    gercek[0] = 68.9

    print("\nGECIKME DOGRULAMASI (hava hizi kanali, 50 ms gecikme = 2,5 adim)")
    sp.sifirla()
    for i in range(12):
        o = sp(gercek)
        if i < 8:
            print(f"  adim {i:>2} (t={i*dt*1000:>4.0f} ms)  olculen u = {o[0]:6.2f}")

    print("\nGURULTU ISTATISTIGI (20.000 adim, sabit gercek durum)")
    sp = SensorPaketi(dt=dt, tohum=7)
    kayit = np.array([sp(gercek) for _ in range(20000)])
    for ad, i, hedef in (("hava hizi u", 0, SPEK["hava_verisi"]["gurultu"]),
                         ("acisal hiz p", 3, SPEK["imu_acisal_hiz"]["gurultu"]),
                         ("tutum phi", 6, SPEK["tutum"]["gurultu"]),
                         ("konum x", 9, SPEK["gnss_konum"]["gurultu"])):
        v = kayit[200:, i] - gercek[i]
        print(f"  {ad:<14} std {v.std():.4f}  (gurultu {hedef:.4f} + sapma kaymasi)")

    print(f"\nazami tasima gecikmesi {sp.azami_gecikme()*1000:.0f} ms (GNSS konum)")
    ic = SPEK["tutum"]["gecikme"]
    print(f"tutum halkasi gecikmesi {ic*1000:.0f} ms")
    print("  Tezin Bolum 10 hedefi omega_BW = 5,8 rad/s. Bu frekansta")
    print(f"  tutum halkasinin faz gecikmesi {math.degrees(5.8*ic):.1f} derece,")
    print(f"  GNSS halkasinin ise {math.degrees(5.8*sp.azami_gecikme()):.1f} derece.")
    print("  Ic halka (tutum) hedefle uyumlu, dis halka (konum) yavas — bu")
    print("  ayrim kaskad kontrol yapisini zorunlu kilar, tek halka yetmez.")
