#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEMEL KONTROLCU — kaskad PID + kontrol dagitimi

Iki islevi var.

1. TESISI DOGRULAR. Acik cevrimde dort rotorlu bir VTOL yunuslamada
   kararsizdir ve devrilir. Bu bir model hatasi degildir, o yuzden
   "model calisiyor mu" sorusu ancak bir kontrolcu ile yanitlanabilir.

2. KARSILASTIRMA TABANIDIR. Pekistirmeli ogrenme ajaninin "iyi" olup
   olmadigi ancak klasik bir kontrolcuye gore soylenebilir. Ajan bunu
   gecemiyorsa katki iddiasi kurulamaz.

YAPI
    dis halka   konum ve hiz  -> tutum komutu      (yavas, GNSS bandi)
    ic halka    tutum         -> moment komutu     (hizli, IMU bandi)
    dagitim     moment + itki -> dort pod komutu

KONTROL DAGITIMI. Dort pod, uc eksende (dusey kuvvet, yatis, yunuslama)
otorite uretir. Cozum en kucuk kareler ile yapilir, bu da fazlaligi
otomatik kullanir.

⚠️ TILT KANALI (F1, 04.08.2026). Ilk surumde tilt yalnizca acik cevrim
programlaniyordu, yani kontrolcu tilt'i bir KONTROL GIRISI olarak hic
kullanmiyordu. Karar 14 bunun neden yanlis oldugunu gosterdi.

    dM/dT_i     = +x_i cos(theta)      -> 90 derecede SIFIR
    dM/dtheta_i = -x_i T_i sin(theta)  -> 90 derecede AZAMI

Yani cruise'da yunuslama otoritesi kaybolmuyor, itki sutunundan tilt
sutununa geciyor. Yalniz itki sutununu kullanan bir dagitici cruise'da
otoritesiz kaliyor ve arac 32 dereceye kadar burun yukari gidiyordu.

Simdi dagitim SEKIZ girisli: dort itki + dort tilt sapmasi. Jakobiyen
rejim harmanini kendiliginden yapar, elle katsayi yok — hover'da tilt
sutunlari sifir oldugu icin kullanilmaz, cruise'da itki sutunlari sifira
gittigi icin tilt zorunlu olarak devreye girer.

VARYANT KISITI. Tilt sapmasi varyantin serbestlik derecesinde cozulur.
Senkron tiltte dort pod ayni acida oldugu icin diferansiyel tilt
uretilemez, lift+cruise'da tilt ekseni hic yoktur. Yani bu kanal
mimarinin kendisine bagli — karsilastirmanin adil olmasi icin temel
kontrolcunun de bu kanali kullanabilmesi gerekir.
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field

import numpy as np

_BURASI = os.path.dirname(os.path.abspath(__file__))
_DIN = os.path.normpath(os.path.join(_BURASI, "..", "dinamik"))
if _DIN not in sys.path:
    sys.path.insert(0, _DIN)

from arac import Limulus                                # noqa: E402


@dataclass
class PID:
    kp: float
    ki: float = 0.0
    kd: float = 0.0
    limit: float = 1e9
    i_limit: float = 1e9
    _i: float = 0.0
    _onceki: float | None = None

    def __call__(self, hata: float, dt: float, turev: float | None = None) -> float:
        self._i = float(np.clip(self._i + hata * dt, -self.i_limit, self.i_limit))
        d = turev if turev is not None else (
            0.0 if self._onceki is None else (hata - self._onceki) / dt)
        self._onceki = hata
        return float(np.clip(self.kp * hata + self.ki * self._i + self.kd * d,
                             -self.limit, self.limit))

    def sifirla(self):
        self._i = 0.0
        self._onceki = None


class TemelKontrolcu:
    """Kaskad PID. Hover, dikey manevra, gecis ve cruise'u kapsar."""

    def __init__(self, ac: Limulus, tilt_kanali: bool = False):
        self.ac = ac
        self.dt = ac.dt
        W = ac.W
        # ⚠️ VARSAYILAN KAPALI (04.08.2026). F1 denemesi BASARISIZ.
        # Bes ayri kurgu denendi, hicbiri kapali cevrimde kazanim
        # vermedi ve son kurgu 400-1000 Nm bozucu bandinda araci zarf
        # disina cikardi — itki-tek kontrolcunun hayatta kaldigi yerde.
        # Ayrinti ve sayilar 4-KARARLAR/20.
        #
        # Kanal olcum icin korunuyor: _jakobiyen ile otorite
        # hesaplanabiliyor ve o sonuc GECERLI. Kapali cevrimde
        # kullanilmasi icin once kararlilik sorunu cozulmeli.
        self.tilt_kanali = tilt_kanali
        # ic halka: tutum -> acisal ivme komutu
        self.pid_phi = PID(kp=8.0, ki=0.0, kd=2.5, limit=3.0)
        self.pid_th = PID(kp=8.0, ki=0.5, kd=3.0, limit=3.0, i_limit=1.0)
        self.pid_psi = PID(kp=3.0, ki=0.0, kd=1.5, limit=1.5)
        # dis halka
        self.pid_h = PID(kp=0.30, ki=0.02, kd=0.0, limit=5.0, i_limit=40.0)
        self.pid_w = PID(kp=0.80, ki=0.12, kd=0.0, limit=3.0, i_limit=15.0)
        self.pid_u = PID(kp=0.020, ki=0.0015, kd=0.0,
                         limit=math.radians(10.0), i_limit=60.0)
        self.pid_V = PID(kp=0.12, ki=0.010, kd=0.0, limit=1.2, i_limit=40.0)
        # cruise'da irtifa tutumla tutulur: tirmanma orani -> pitch acisi
        self.pid_gama = PID(kp=0.030, ki=0.004, kd=0.0,
                            limit=math.radians(12.0), i_limit=60.0)
        self.tilt_tavan = ac.k["THETA_CRUISE"]   # 85 derece, otorite korunur

        # --- tilt kanalinin varyant kisiti ---
        # G[p, j] = 1  <=>  p pod'u j serbestlik derecesine bagli.
        # Senkron tiltte tek sutun kalir, lift+cruise'da hic sutun yok.
        v = ac.var
        if v.sabit_tilt is not None:
            self.G_tilt = np.zeros((4, 0))
        else:
            n = len(v.tilt_gruplari)
            self.G_tilt = np.zeros((4, n))
            for j, grup in enumerate(v.tilt_gruplari):
                for p in grup:
                    self.G_tilt[p, j] = 1.0
        # --- DIFERANSIYEL KIP TABANI ---
        # ⚠️ Tilt sapmasi ORTAK KIP ICEREMEZ. Ortak kip (dort pod ayni
        # yone) tilt programinin isidir, program hiza gore acar. Serbest
        # birakilirsa cozucu onu irtifa kontrolu icin kullanir: 85
        # derecede dFz/dtheta, dFz/dT'nin 900 katidir. Ilk denemede tam
        # bu oldu, tutum sapmasi 11,8 -> 71,6 dereceye cikti.
        #
        # n serbestlik derecesinden ortak kip cikarilinca n-1 diferansiyel
        # kip kalir. Bu dogrudan mimarinin sonucudur:
        #     limulus 4 eksen -> 3 kip · ikili 2 -> 1 · senkron 1 -> 0
        # Senkron tiltte diferansiyel tilt kontrolu YOKTUR.
        n = self.G_tilt.shape[1]
        if n >= 2:
            bir = np.ones((n, 1)) / math.sqrt(n)
            Q, _ = np.linalg.qr(np.hstack([bir, np.eye(n)]))
            self.M_dif = Q[:, 1:n]                  # ortak kipe dik taban
        else:
            self.M_dif = np.zeros((n, 0))
        # --- YUNUSLAMA KIPI ---
        # Diferansiyel kipler arasindan yunuslama uretenini sec: on grup
        # bir yone, arka grup ters yone. DOF uzayinda pod x kolunun
        # isareti bunu belirler.
        if n >= 2:
            x_dof = (self.G_tilt.T @ ac.pod[:, 0]) / np.maximum(
                self.G_tilt.sum(axis=0), 1.0)
            ham = np.sign(x_dof)
            ham = ham - ham.mean()                  # ortak kipi at
            nrm = np.linalg.norm(ham)
            self.yunuslama_kipi = ham / nrm if nrm > 1e-9 else np.zeros(n)
        else:
            self.yunuslama_kipi = np.zeros(n)
        # tilt sutunlarini boyutsuzlastiran olcek — yalniz olcum icin
        # (_jakobiyen). Kapali cevrimde kullanilmiyor, orada yavas trim
        # halkasi var.
        self.tilt_olcek = math.radians(10.0)
        # aktuator oran limiti, komut bunu asamaz
        self.tilt_oran = ac.tilt[0].hiz_limiti
        self.tilt_sapma_tavan = math.radians(12.0)
        # yavas trim halkasi — hizli halka itkide kalir
        self.pid_tilt = PID(kp=0.25, ki=0.06, kd=0.0,
                            limit=math.radians(12.0), i_limit=2.0)
        self._trim_genlik = 0.0
        self._son_trim = 0.0

    # -----------------------------------------------------------------
    def _jakobiyen(self, tilt: np.ndarray, T: np.ndarray) -> np.ndarray:
        """[dFz dFx dMx dMy] / d[T_1..T_4, dtheta_1..dtheta_n]

            Fz = -sum T_i cos th_i        Fx = +sum T_i sin th_i
            Mx = -sum y_i T_i cos th_i    My = +sum x_i T_i cos th_i

        ⚠️ Fx SATIRI ZORUNLU. Ilk denemede yalniz [Fz Mx My] alinmisti.
        Cozucu tilt sutunlarini dusey kuvvet icin kullandi, yatay kuvvet
        serbest kaldi ve arac 60 saniyede 293 m irtifa kaybetti. Tilt
        sapmasi bir kuvvet organi degil MOMENT organidir — dort satirin
        tamami hedeflenince bu yapisal olarak garanti altina alinir,
        cozucu sapmayi kendiliginden diferansiyel (sifir toplamli)
        bicimde uretir.
        """
        p = self.ac.pod
        c = np.cos(tilt)
        s = np.sin(tilt)
        # itki sutunlari
        J_T = np.zeros((4, 4))
        J_T[0, :] = -c                    # dFz/dT
        J_T[1, :] = s                     # dFx/dT
        J_T[2, :] = -p[:, 1] * c          # dMx/dT
        J_T[3, :] = p[:, 0] * c           # dMy/dT
        if self.G_tilt.shape[1] == 0 or not self.tilt_kanali:
            return J_T
        # tilt sutunlari, pod uzayinda
        J_th_pod = np.zeros((4, 4))
        J_th_pod[0, :] = T * s            # dFz/dth
        J_th_pod[1, :] = T * c            # dFx/dth
        J_th_pod[2, :] = p[:, 1] * T * s  # dMx/dth
        J_th_pod[3, :] = -p[:, 0] * T * s  # dMy/dth
        # varyantin serbestlik derecesine indir, sonra ortak kipi at
        J_th = J_th_pod @ self.G_tilt @ self.M_dif
        return np.hstack([J_T, J_th * self.tilt_olcek])

    # -----------------------------------------------------------------
    def _dagitim_matrisi(self, tilt: np.ndarray) -> np.ndarray:
        """[Fz; Mx; My] = B(tilt) @ [T1..T4]

        ⚠️ B tilt acisina BAGLIDIR ve tilt 90 dereceye giderken moment
        satirlari cos(tilt) ile sifira gider. Yani cruise'da podlarin
        yunuslama otoritesi YOKTUR. Ilk surumde B tilt=0 kabulu ile
        sabit alinmisti ve cruise'da kontrolcu otorite sandigi seyi
        kullanamayip araci 32 dereceye kadar burun yukari birakiyordu.

        Bu, bulgu F3'un dinamik kanitidir: podlar cruise'da yunuslama
        momenti uretemez, cunku kaldiraç kolu cos(tilt) ile carpilir.
        Tezin cruise tilt acisini 85 derece (90 degil) secmesi bu
        otoritenin bir kismini korur — cos(85) = 0,087.
        """
        p = self.ac.pod
        B = np.zeros((3, 4))
        for i in range(4):
            c = math.cos(float(tilt[i]))
            B[0, i] = -c                  # dusey kuvvet
            B[1, i] = -p[i, 1] * c        # yatis momenti
            B[2, i] = p[i, 0] * c         # yunuslama momenti
        return B

    def sifirla(self):
        for a in vars(self).values():
            if isinstance(a, PID):
                a.sifirla()
        self._trim_genlik = 0.0
        self._son_trim = 0.0

    # -----------------------------------------------------------------
    def __call__(self, durum: np.ndarray, h_hedef: float, V_hedef: float,
                 tilt_hedef: float) -> tuple[np.ndarray, np.ndarray]:
        """Kaskad kontrol + en kucuk kareler dagitim.

        Gerekli kuvvet dusey ve yatay bilesenlere ayrilir, sonra tilt
        eksenine IZDUSURULUR:
            T = F_dusey cos(tilt) + F_yatay sin(tilt)
        Hover'da (tilt=0) T = F_dusey, cruise'da (tilt=90) T = F_yatay
        olur, arada yumusak gecer. Boylece tek bir bagintiyla tum
        rejim kapsanir ve cruise'da 1/cos(tilt) patlamasi olmaz.
        """
        ac, dt = self.ac, self.dt
        u, v, w = durum[0:3]
        p, q, r = durum[3:6]
        phi, th, psi = durum[6:9]
        h = -durum[11]

        # --- dis halka: irtifa -> tirmanma orani -> dusey ivme ---
        c = -w                                        # tirmanma orani, +yukari
        c_komut = self.pid_h(h_hedef - h, dt)
        a_z = self.pid_w(c_komut - c, dt)             # m/s2, +yukari

        # --- REJIM HARMANI ---
        # Hover ve cruise'da kontrol tahsisi TERSTIR.
        #   hover   irtifa <- itki      · hiz <- tutum (burun asagi hizlanir)
        #   cruise  irtifa <- tutum     · hiz <- itki
        # Ilk surumde her iki rejimde de hover tahsisi kullanildi ve arac
        # gecisten sonra 300 m'den yere kadar dalisa gecti. Harman
        # katsayisi sin(tilt) — fiziksel olarak itkinin dusey bileseninin
        # ne kadar kayboldugunu olcer.
        s_rej = math.sin(min(max(tilt_hedef, 0.0), math.pi / 2))
        hiz_hata = V_hedef - u
        th_hover = -self.pid_u(hiz_hata, dt)          # burun asagi -> hizlan
        th_cruise = self.pid_gama(c_komut - c, dt)    # burun yukari -> tirman
        th_komut = (1.0 - s_rej) * th_hover + s_rej * th_cruise
        phi_komut = 0.0

        # --- gerekli kuvvetler ---
        V, alfa, _ = self._hava(u, v, w)
        qd = 0.5 * 1.225 * V * V
        CL, CD = ac.kanat.katsayilar(alfa)
        L_kanat = qd * ac.kanat.S * CL
        D_kanat = qd * ac.kanat.S * CD

        kap = max(math.cos(phi) * math.cos(th), 0.4)
        # dusey ivme talebi yalniz hover rejiminde itkiye yuklenir
        F_dusey = (ac.m * (ac.g + (1.0 - s_rej) * a_z) / kap
                   - L_kanat) * ac.k["DOWNLOAD"]
        a_x = self.pid_V(hiz_hata, dt) * s_rej
        F_yatay = D_kanat + ac.m * a_x

        T_toplam = max(F_dusey * math.cos(tilt_hedef)
                       + F_yatay * math.sin(tilt_hedef), 0.0)

        # --- ic halka: tutum -> moment ---
        a_phi = self.pid_phi(phi_komut - phi, dt, turev=-p)
        a_th = self.pid_th(th_komut - th, dt, turev=-q)
        Mx = ac.I[0, 0] * a_phi
        My = ac.I[1, 1] * a_th

        # --- dagitim: itki kanali (hizli halka) ---
        tilt_v = np.full(4, tilt_hedef)
        B = self._dagitim_matrisi(tilt_v)
        hedef = np.array([-T_toplam * math.cos(tilt_hedef), Mx, My])
        # agirlikli en kucuk kareler: dusey kuvvet momentlerden onceliklidir
        Wd = np.diag([3.0, 1.0, 1.0])
        T = np.linalg.pinv(Wd @ B, rcond=1e-6) @ (Wd @ hedef)
        # tilt 90'a yaklasirken B tekilleseceginden itki dogrudan verilir
        if math.cos(tilt_hedef) < 0.05:
            T = np.full(4, T_toplam / 4.0)
        T = np.clip(T, 0.0, ac.W / 2.0)

        # --- tilt kanali: YAVAS TRIM HALKASI (F1) ---
        sapma = self._tilt_trim(th_komut - th, tilt_hedef, dt)

        n_cikti = max(ac.var.n_tilt, 1)
        tilt = np.full(n_cikti, tilt_hedef)
        if sapma.size:
            tilt = tilt + sapma[:n_cikti]
            tilt = np.clip(tilt, ac.k["THETA_MIN"], ac.k["THETA_MAX"])
        return T, tilt

    # -----------------------------------------------------------------
    def _tilt_trim(self, th_hata: float, tilt_hedef: float,
                   dt: float) -> np.ndarray:
        """Diferansiyel tiltle yunuslama TRIMI. Moment kontrolu degil.

        ⚠️ TASARIM GEREKCESI — uc basarisiz denemeden sonra yazildi.
        Tilt once dagitim matrisine bir kontrol sutunu olarak eklendi
        (dort itki + tilt sapmalari, sonumlu en kucuk kareler). Uc kez
        arac zarf disina cikti. Sebep tek bir cumleyle su.

            Tilt aktuatoru 15 derece/s oran limitlidir. Yunuslama
            halkasi 10 ms bandinda calisir. Oran limitli yavas bir
            organi hizli bir halkanin icine koymak, kontrolcunun
            ulasamayacagi bir otoriteyi varsaymasidir.

        Dogru kurgu: itki HIZLI momenti uretir, tilt YAVAS trimi devralir.
        Kazanc sin(theta) ile programlanir — hover'da kanal kapali,
        cruise'da acik. Bu, dM/dtheta = -x T sin(theta) bagintisinin
        dogrudan karsiligidir.
        """
        n = self.M_dif.shape[1]
        if n == 0 or not self.tilt_kanali:
            return np.zeros(0)
        # yalniz yunuslama kipi kullanilir: on grup +, arka grup -
        kazanc = math.sin(min(max(tilt_hedef, 0.0), math.pi / 2))
        if kazanc < 0.15:                       # hover bandinda kapali
            self._trim_genlik *= 0.98           # yumusak birak
        else:
            self._trim_genlik += (self.pid_tilt(th_hata, dt) * kazanc
                                  - self._trim_genlik) * min(dt / 0.5, 1.0)
        azami = self.tilt_oran * dt
        d = float(np.clip(self._trim_genlik - self._son_trim, -azami, azami))
        self._son_trim = float(np.clip(
            self._son_trim + d, -self.tilt_sapma_tavan, self.tilt_sapma_tavan))
        return self.yunuslama_kipi * self._son_trim

    @staticmethod
    def _hava(u, v, w):
        V = math.sqrt(u * u + v * v + w * w)
        if V < 0.5:
            return V, 0.0, 0.0
        return V, math.atan2(w, u), math.asin(float(np.clip(v / V, -1, 1)))


# =====================================================================
def gecis_profili(t: float, t_bas: float = 5.0, sure: float = 12.0,
                  tilt_son: float = math.radians(90.0)) -> float:
    """Zamana bagli acik cevrim tilt programi. Basit ama kirilgan."""
    if t < t_bas:
        return 0.0
    x = min((t - t_bas) / sure, 1.0)
    return tilt_son * (x * x * (3.0 - 2.0 * x))          # yumusak adim


def hiz_programli_tilt(V: float, V_bas: float = 18.0, V_son: float = 58.0,
                       tilt_son: float = math.radians(85.0)) -> float:
    """Hiza bagli tilt programi. Zamana bagli olandan belirgin ustun.

    Rotorlar ancak kanat tasima uretmeye basladiktan sonra egilir.
    Zamana bagli programda arac gecis ortasinda 250 m irtifa
    kaybediyordu, cunku tilt kanattan once ilerliyordu.
    """
    x = float(np.clip((V - V_bas) / max(V_son - V_bas, 1e-6), 0.0, 1.0))
    return tilt_son * (x * x * (3.0 - 2.0 * x))


def kos(ac: Limulus, sure: float, h_hedef: float, V_profili,
        tilt_profili, kayit_araligi: int = 25, tilt_kanali: bool = True):
    """Kapali cevrim benzetim. Kayit dondurur."""
    kk = TemelKontrolcu(ac, tilt_kanali=tilt_kanali)
    kk.sifirla()
    n = int(sure / ac.dt)
    kayit = []
    for i in range(n):
        t = ac.t
        T, tilt = kk(ac.durum, h_hedef, V_profili(t), tilt_profili(t))
        _, bilgi = ac.adim(T, tilt)
        if i % kayit_araligi == 0:
            d = ac.durum
            kayit.append(dict(t=t, h=-d[11], u=d[0], w=d[2],
                              th=math.degrees(d[7]), phi=math.degrees(d[6]),
                              V=bilgi["V"], P=bilgi["P_batarya"],
                              tilt=float(np.degrees(bilgi["tilt"]).mean()),
                              T=float(np.mean(bilgi["T"])),
                              enerji=bilgi["enerji"]))
        if -ac.durum[11] <= 0.0 or abs(ac.durum[7]) > math.radians(80):
            kayit.append(dict(t=ac.t, h=-ac.durum[11], hata="zarf disi"))
            break
    return kayit


if __name__ == "__main__":
    print("1. HOVER TUTMA  (100 m, 30 s)")
    ac = Limulus(sensor_etkin=False)
    ac.sifirla(durum=np.array([0.] * 11 + [-100.0]), tilt0=0.0, T0=ac.W / 4)
    k = kos(ac, 30.0, 100.0, lambda t: 0.0, lambda t: 0.0)
    for r in k[::6]:
        if "hata" in r:
            print(f"  t={r['t']:5.1f}  {r['hata']}")
        else:
            print(f"  t={r['t']:5.1f}  h={r['h']:7.2f}  th={r['th']:+6.2f} deg  "
                  f"P={r['P']/1e3:6.0f} kW  T={r['T']:.0f} N")
    son = k[-1]
    print(f"  SONUC irtifa hatasi {son.get('h', 0) - 100:+.3f} m  "
          f"pitch {son.get('th', 0):+.3f} deg")

    print("\n2. DIKEY TIRMANIS  (100 -> 150 m)")
    ac = Limulus(sensor_etkin=False)
    ac.sifirla(durum=np.array([0.] * 11 + [-100.0]), tilt0=0.0, T0=ac.W / 4)
    k = kos(ac, 30.0, 150.0, lambda t: 0.0, lambda t: 0.0)
    for r in k[::6]:
        if "hata" not in r:
            print(f"  t={r['t']:5.1f}  h={r['h']:7.2f}  w={-r['w']:+6.2f} m/s  "
                  f"P={r['P']/1e3:6.0f} kW")
    print(f"  SONUC irtifa hatasi {k[-1].get('h',0) - 150:+.3f} m")

    print("\n3. GECIS  (hover -> cruise, tilt programi ile)")
    ac = Limulus(sensor_etkin=False)
    ac.sifirla(durum=np.array([0.] * 11 + [-300.0]), tilt0=0.0, T0=ac.W / 4)
    V_hedef = 68.9
    k = kos(ac, 60.0, 300.0,
            lambda t: V_hedef * min(max((t - 5.0) / 25.0, 0.0), 1.0),
            lambda t: hiz_programli_tilt(ac.durum[0]))
    for r in k[::8]:
        if "hata" in r:
            print(f"  t={r['t']:5.1f}  {r['hata']}")
        else:
            print(f"  t={r['t']:5.1f}  h={r['h']:7.2f}  V={r['V']:5.1f}  "
                  f"tilt={r['tilt']:5.1f} deg  th={r['th']:+6.2f}  "
                  f"P={r['P']/1e3:6.0f} kW")
    son = k[-1]
    if "hata" not in son:
        print(f"  SONUC V={son['V']:.1f} m/s (hedef {V_hedef})  "
              f"h={son['h']:.1f} m  enerji {son['enerji']/3.6e6:.2f} kWh")
