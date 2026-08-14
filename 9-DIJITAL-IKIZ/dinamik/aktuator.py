#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AKTUATOR MODELLERI — tilt ekseni ve itki zinciri

Iki ayri gecikme kaynagi var ve ikisi de kontrol tasariminda belirleyici.

Tilt      elektromekanik aktuator, ORAN limitli (15 derece/s). Komut ile
          gerceklesen aci arasinda buyuk bir gecikme dogurur. Hover'dan
          cruise'a gecis en az 90/15 = 6 saniye surer.
Itki      inverter + motor + rotor ataleti. Birinci dereceden gecikme,
          zaman sabiti 0,08 s.

Aktuator dinamigi olmadan egitilen bir ajan, gercekte var olmayan bir
bant genisligini kullanmayi ogrenir. Bu, sim-to-real farkinin en yaygin
kaynagidir ve bu yuzden modelin ic parcasidir, sonradan eklenen bir
duzeltme degildir.

Eklem yuku, tezin Bolum 8.1 zarfiyla ayni tabandan hesaplanir ve
RDP-IF kapasitesi asilirsa isaretlenir.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class TiltAktuatoru:
    """Oran limitli tilt ekseni.

    theta_min / theta_max     mekanik limitler (rad)
    hiz_limiti                azami acisal hiz (rad/s)
    """
    theta_min: float = 0.0
    theta_max: float = math.radians(90.0)
    hiz_limiti: float = math.radians(15.0)
    theta: float = 0.0
    theta_p: float = 0.0            # gerceklesen acisal hiz

    def adim(self, komut: float, dt: float) -> float:
        hedef = float(np.clip(komut, self.theta_min, self.theta_max))
        fark = hedef - self.theta
        azami = self.hiz_limiti * dt
        adim = float(np.clip(fark, -azami, azami))
        self.theta += adim
        self.theta_p = adim / dt if dt > 0 else 0.0
        return self.theta

    def sifirla(self, theta0: float = 0.0):
        self.theta = float(np.clip(theta0, self.theta_min, self.theta_max))
        self.theta_p = 0.0

    @property
    def doygun(self) -> bool:
        """Aktuator oran limitinde mi calisiyor"""
        return abs(abs(self.theta_p) - self.hiz_limiti) < 1e-6

    def gecis_suresi(self) -> float:
        """Tam zarfi katetme suresi [s]. Kontrol otoritesinin ust siniri."""
        return (self.theta_max - self.theta_min) / self.hiz_limiti


@dataclass
class ItkiZinciri:
    """Bir podun itki uretim zinciri.

    Motor sayisi, guc anma kademesi ve birinci dereceden tepki gecikmesi.
    Anma kademeleri Bolum 9'dan, LIMULUS_ADLANDIRMA_SOZLUGU'ndeki dort
    kademe tablosuyla birebir.
    """
    n_motor: int = 2
    P_surekli: float = 134e3
    P_oei: float = 160e3
    P_pik: float = 190e3
    tau: float = 0.08
    T: float = 0.0                   # gerceklesen itki
    arizali_motor: int = 0           # kac motor devre disi

    def guc_tavani(self, kademe: str = "surekli") -> float:
        P = {"surekli": self.P_surekli, "oei": self.P_oei,
             "pik": self.P_pik}[kademe]
        return P * (self.n_motor - self.arizali_motor)

    def adim(self, T_komut: float, T_tavan: float, dt: float) -> float:
        hedef = float(np.clip(T_komut, 0.0, T_tavan))
        a = dt / max(self.tau + dt, 1e-9)
        self.T += a * (hedef - self.T)
        return self.T

    def sifirla(self, T0: float = 0.0):
        self.T = max(T0, 0.0)
        self.arizali_motor = 0


@dataclass
class EklemYuku:
    """Tilt ekleminin tasidigi yuk ve RDP-IF kapasitesi kontrolu.

    Bolum 8.1 ile ayni taban: limit yuk faktoru 2,5 · emniyet 1,5.
    """
    n_limit: float = 2.5
    j_emniyet: float = 1.5
    kapasite_dusey: float = 28e3

    def ultimate(self, T: float) -> float:
        return T * self.n_limit * self.j_emniyet

    def asim(self, T: float) -> float:
        """Kapasite asimi orani. 0 ise asim yok."""
        u = self.ultimate(T)
        return max(0.0, (u - self.kapasite_dusey) / self.kapasite_dusey)


if __name__ == "__main__":
    from konfigurasyon import KONF as K

    print("TILT AKTUATORU")
    t = TiltAktuatoru(theta_max=K["THETA_MAX"], hiz_limiti=K["THETA_HIZ"])
    print(f"  tam zarf gecis suresi {t.gecis_suresi():.1f} s "
          f"({math.degrees(K['THETA_MAX']):.0f} derece / "
          f"{math.degrees(K['THETA_HIZ']):.0f} derece/s)")
    dt = 0.02
    t.sifirla(0.0)
    komut = K["THETA_CRUISE"]
    izlem = []
    for i in range(500):
        izlem.append(math.degrees(t.adim(komut, dt)))
    varis = next(i for i, v in enumerate(izlem)
                 if abs(v - math.degrees(komut)) < 0.01)
    print(f"  0 -> 85 derece komutu {varis*dt:.2f} s'de tamamlandi "
          f"(teorik {math.degrees(komut)/math.degrees(K['THETA_HIZ']):.2f} s)")
    print(f"  limit asimi var mi: {'hayir' if max(izlem) <= 90.001 else 'EVET'}")

    print("\nITKI ZINCIRI")
    z = ItkiZinciri(n_motor=K["N_MOTOR_POD"], P_surekli=K["P_MOTOR_SUREKLI"],
                    P_oei=K["P_MOTOR_OEI"], P_pik=K["P_MOTOR_PIK"],
                    tau=K["TAU_MOTOR"])
    for kad in ("surekli", "oei", "pik"):
        print(f"  {kad:<8} pod guc tavani {z.guc_tavani(kad)/1e3:.0f} kW")
    z.arizali_motor = 1
    print(f"  bir motor arizali, surekli tavan {z.guc_tavani()/1e3:.0f} kW")
    z.sifirla()

    # basamak tepkisi, %63,2 noktasi tau'ya esit olmali
    hedef = 7358.0
    izlem = [z.adim(hedef, 1e9, dt) for _ in range(200)]
    i63 = next(i for i, v in enumerate(izlem) if v >= 0.632 * hedef)
    print(f"  basamak tepkisi %63,2 noktasi {i63*dt:.3f} s  "
          f"(tau = {K['TAU_MOTOR']:.3f} s)")

    print("\nEKLEM YUKU")
    e = EklemYuku(kapasite_dusey=K["RDPIF_DUSEY"])
    W = K["MTOW"] * K["G"]
    for ad, T in (("Rev.D arka pod (F2)", 7867.0), ("Rev.E hover", W / 4),
                  ("manevra 2,5 g", W / 4 * 2.5 / 2.5)):
        print(f"  {ad:<22} T={T/1e3:.2f} kN -> ultimate "
              f"{e.ultimate(T)/1e3:5.2f} kN   asim {e.asim(T)*100:+.1f}%")
