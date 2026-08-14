#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GYMNASIUM ORTAMI — LIMULUS otonom ucus

Gozlem bir DURUM VEKTORUDUR, goruntu degil. Bu, yuksek lisans
calismasindaki Unity3D + ML-Agents kurgusundan ayrildigimiz yerdir.
Gorsel ya da isin-tabanli algi olmadigi icin egitim oyun motoruna
ugramak zorunda degil, Python icinde 50-100 kat hizli koser ve fizik
denetlenebilir kalir. Unity yalniz sunum katmanidir.

GOZLEM (26)
    0:3   govde hizi u v w                     olculen, olceklenmis
    3:6   acisal hiz p q r
    6:9   tutum sin/cos ile (phi, th, psi)     -> 6 eleman
    12:14 irtifa hatasi, dusey hiz
    14:18 pod tilt acilari (gerceklesen)
    18:22 pod itkileri (gerceklesen, olceklenmis)
    22:26 gorev hedefi (V_hedef, h_hedef, faz kodu, kalan sure)

EYLEM (varyanta gore 4-8) — TRIM'E GORE ARTIMSAL, mutlak DEGIL
    4 itki komutu   T   = T_trim * (1 + 0,35 e)
    n tilt komutu   th  = th_trim + 30 derece * e
      n = 4 LIMULUS · 2 ikili · 1 senkron · 0 lift+cruise

    ⚠️ 03.08.2026'da DEGISTI, gerekcesi 4-KARARLAR/15.
    Onceki surum mutlak komut veriyordu:  T = (e+1)/2 * T_tavan.
    O eslemede sifir eylem 5518 N/pod itki ve 45 derece tilt demekti,
    yani hover trim noktasi (7358 N, 0 derece) eylem uzayinda
    (+0,333, ..., -1,000) koordinatindaydi. Tilt kanallarinin trimi
    eylem uzayinin SINIRINA dusuyordu ve Gauss politikasi bir sinira
    kutle yerlestiremez. Yirmi pilot kosunun hicbiri mufredat seviye
    0'i gecemedi, nedeni buydu. Artimsal eslemede sifir eylem trimi
    korur, kesif ucabilir bir nokta etrafinda yapilir.

ODUL
    gorev takibi - kontrol eforu - zarf ihlali - enerji
    Terimler ayri ayri kaydedilir, ODUL_AGIRLIK ile ayarlanir.

MUFREDAT (curriculum)
    0 hover tutma · 1 dikey manevra · 2 gecis · 3 cruise ·
    4 gust altinda gecis · 5 OEI
Yuksek lisans tezinde mufredat ogrenmesi calisti, ayni zincir
korunuyor.
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:                                    # pragma: no cover
    raise SystemExit("gymnasium gerekli:  pip install gymnasium")

_BURASI = os.path.dirname(os.path.abspath(__file__))
_DIN = os.path.normpath(os.path.join(_BURASI, "..", "dinamik"))
if _DIN not in sys.path:
    sys.path.insert(0, _DIN)

import atmosfer as atm                                  # noqa: E402
from arac import Limulus                                # noqa: E402
from konfigurasyon import KONF                          # noqa: E402
from trim import trim as _trim                          # noqa: E402


# =====================================================================
# GOREV FAZLARI ve MUFREDAT
# =====================================================================
@dataclass(frozen=True)
class Gorev:
    ad: str
    sure: float                # s
    V_hedef: float             # m/s
    h_hedef: float             # m
    gust: str = "yok"
    ariza_pod: int | None = None
    ariza_ani: float = 0.0
    baslangic_V: float = 0.0
    baslangic_h: float = 100.0

    @property
    def faz_kodu(self) -> float:
        return {"hover": 0.0, "dikey": 0.2, "gecis": 0.4,
                "cruise": 0.6, "gust": 0.8, "oei": 1.0}.get(
            self.ad.split("_")[0], 0.0)


MUFREDAT_TABAN: tuple[Gorev, ...] = (
    Gorev("hover", 20.0, 0.0, 100.0, baslangic_V=0.0, baslangic_h=100.0),
    Gorev("dikey", 25.0, 0.0, 150.0, baslangic_V=0.0, baslangic_h=100.0),
    Gorev("gecis", 40.0, 60.0, 300.0, baslangic_V=0.0, baslangic_h=150.0),
    Gorev("cruise", 40.0, 68.9, 300.0, baslangic_V=60.0, baslangic_h=300.0),
    Gorev("gust_gecis", 40.0, 60.0, 300.0, gust="orta",
          baslangic_V=0.0, baslangic_h=150.0),
    Gorev("oei_hover", 25.0, 0.0, 100.0, ariza_pod=2, ariza_ani=5.0,
          baslangic_V=0.0, baslangic_h=100.0),
)

# --- INCE MUFREDAT (B6, karar 47) ---
# ⚠️ BAYRAK VARSAYILAN KAPALI. Taban mufredatta seviye 1 ile 2 arasindaki
# basamak hedef hizi 0'dan 60 m/s'ye ciakariyor. Karar 41'de hicbir politika
# bu basamagi gecmedi. Ince mufredat AYNI iki seviyenin arasina 30 m/s'lik
# bir ara basamak koyar, baska hicbir sey degismez — seviye sayisi 6'dan
# 7'ye cikar ve seviye indisleri 2'den sonra bir kayar.
# ⚠️ Bayrak acikken tamamlanmis kosularin gunlukleriyle SEVIYE INDISI
# KARSILASTIRILAMAZ, cunku indisler ayni gorevi gostermez.
MUFREDAT_INCE: tuple[Gorev, ...] = (
    MUFREDAT_TABAN[0],
    MUFREDAT_TABAN[1],
    Gorev("gecis_yarim", 40.0, 30.0, 300.0,
          baslangic_V=0.0, baslangic_h=150.0),
    MUFREDAT_TABAN[2],
    MUFREDAT_TABAN[3],
    MUFREDAT_TABAN[4],
    MUFREDAT_TABAN[5],
)

MUFREDAT: tuple[Gorev, ...] = (
    MUFREDAT_INCE
    if os.environ.get("LIMULUS_MUFREDAT_INCE", "0") == "1"
    else MUFREDAT_TABAN
)

# ---------------------------------------------------------------------
# TRIM ANKRAJI — eylemler bu noktaya gore artimsaldir
# ---------------------------------------------------------------------
KT_YETKI = 0.35                      # itki, trim etrafinda +-%35
KTH_YETKI = math.radians(30.0)       # tilt, trim etrafinda +-30 derece

# Irtifa odul teriminin taban olcegi. F1 bayragi acikken bu deger bir ALT
# SINIR olur ve gorevin baslangic irtifa hatasi daha buyukse o kullanilir.
# Boylece hover ve cruise hassasiyeti degismez, olu bolge ise kalkar.
IRTIFA_OLCEK = 50.0

# Stall cezasinin altinda uygulanmadigi hiz. V_S1 = 49,6 m/s, esik yarisi.
# Bunun altinda kanat agirligin anlamli bir kismini tasimiyor ve hucum
# acisi V -> 0 iken sayisal olarak tanimsizlasiyor.
V_STALL_ESIK = 25.0                  # m/s

_TRIM_ONBELLEK: dict[tuple, tuple] = {}


def trim_ankraji(ac, V: float, h: float) -> tuple[np.ndarray, np.ndarray]:
    """Gorevin baslangic kosulunda trim noktasi. (T dort pod, tilt dort pod)

    Onbelleklenir, cunku mufredat sonlu sayida gorev tanimlar ve trim
    cozucu 0,1-3 s suruyor. Cozum bulunamazsa hover itkisine ve varyantin
    sabit tiltine duser. Lift+cruise varyanti ileri hizda trim bulamaz,
    bu bilinen bir eksiklik (yapilacaklar B4) ve burada gizlenmez.
    """
    anahtar = (ac.varyant_ad, round(V, 2), round(h, 1))
    if anahtar in _TRIM_ONBELLEK:
        return _TRIM_ONBELLEK[anahtar]
    T = np.full(4, ac.W / 4.0)
    th = np.zeros(4) if V < 5.0 else np.full(4, ac.k["THETA_CRUISE"])
    if ac.var.sabit_tilt is not None:
        th = np.full(4, ac.var.sabit_tilt)
    try:
        r = _trim(ac, V=V, gama=0.0, h=h)
        if r.basarili:
            T, th = np.array(r.T, float), np.array(r.tilt, float)
    except Exception:
        pass
    T = np.clip(T, 1.0, None)
    _TRIM_ONBELLEK[anahtar] = (T, th)
    return T, th


ODUL_AGIRLIK = dict(
    hiz=1.0, irtifa=1.0, tutum=0.5,
    kontrol_eforu=0.05, tilt_orani=0.05,
    enerji=0.2, zarf=5.0, cokme=100.0,
)


# =====================================================================
class LimulusOrtami(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, varyant: str = "limulus", seviye: int = 0,
                 dt: float = 0.02, sensor: bool = True,
                 tohum: int | None = None, gorev: Gorev | None = None):
        super().__init__()
        self.varyant = varyant
        self.seviye = int(np.clip(seviye, 0, len(MUFREDAT) - 1))
        self.dt = dt
        self.sensor = sensor
        self._tohum = tohum
        self._gorev_zorla = gorev

        # ⚠️ B4 — ayri cruise itki birimi. Cevre degiskeniyle acilir.
        # Varsayilan KAPALI, cunku 04.08.2026'daki yirmi kosu kapali
        # modelle uretildi. Acik kosular AYRI dizine yazilmalidir, yoksa
        # iki farkli fizikle egitilmis kosular karisir. Karar 22 ve 29.
        _ci = os.environ.get("LIMULUS_CRUISE_ITKI", "0") == "1"
        self.ac = Limulus(dt=dt, varyant_ad=varyant, sensor_etkin=sensor,
                          tohum=tohum, cruise_itki_etkin=_ci)
        self.n_tilt = max(self.ac.var.n_tilt, 0)
        # ⚠️ TILT KANALI KAPATMA (karar 27'nin acik kalemi, 05.08.2026).
        # F2 ablasyonu politikayi tilt kanali ACIKKEN egitip sonradan
        # kanali sifirliyordu, yani egitim dagiliminin DISINA cikariyordu.
        # Temiz olcum, kanal hic verilmeden SIFIRDAN egitilmis bir
        # LIMULUS'tur. Bu bayrak onu kuruyor: tilt EYLEM kanallari eylem
        # uzayindan cikar, tilt acilari ucus programinda kalir.
        # Mimari degismiyor, YALNIZ politikanin erisimi degisiyor.
        self.tilt_kanali_kapali = os.environ.get("LIMULUS_TILT_KANALI",
                                                 "1") == "0"
        self.n_eylem = 4 + (0 if self.tilt_kanali_kapali else self.n_tilt)

        self.action_space = spaces.Box(-1.0, 1.0, (self.n_eylem,), np.float32)
        self.observation_space = spaces.Box(-np.inf, np.inf, (26,), np.float32)

        # ⚠️ F1 — irtifa odul olceginin gorev baslangicina tabanlanmasi.
        # Karar 39 on kaydi. Varsayilan KAPALI, cunku kosular_v2 ve
        # kosular_uzun kampanyalari kapali hâlle uretildi. Acik kosular
        # AYRI dizine yazilir (karar 22).
        self.irtifa_taban = os.environ.get("LIMULUS_IRTIFA_TABAN",
                                           "0") == "1"

        # ⚠️ ORTAM V0 — karar 15 ONCESI kusurlu ortamin yeniden kurulmasi
        # (karar 52, M5 hakem kalemi M-01). Bayrak ACIKKEN uc kusur geri
        # gelir: T1 mutlak eylem eslemesi, T2 hiz esiksiz stall cezasi,
        # T3 cezasiz tutum sonlanmasi. Varsayilan KAPALI ve kapaliyken
        # davranis bugunku koda bit duzeyinde esdegerdir (regresyon
        # denetimi testler/dogrulama_ortam_v0.py). Bu bayrakla uretilen
        # kosular YALNIZ kosular_t3_v0/ dizinine yazilir ve hicbir mimari
        # karsilastirmaya girmez.
        self.ortam_v0 = os.environ.get("LIMULUS_ORTAM_V0", "0") == "1"
        self._v0_cezasiz = False

        # olcekler
        self.T_olcek = self.ac.W / 4.0 * 1.5
        self.V_olcek = 70.0
        self.h_olcek = 300.0
        self.irtifa_olcek = IRTIFA_OLCEK

        self.gorev = self._gorev_sec()
        self.reset(seed=tohum)

    # -----------------------------------------------------------------
    def _gorev_sec(self) -> Gorev:
        return self._gorev_zorla or MUFREDAT[self.seviye]

    def seviye_yukselt(self):
        self.seviye = min(self.seviye + 1, len(MUFREDAT) - 1)
        self.gorev = self._gorev_sec()

    # -----------------------------------------------------------------
    def _gozlem(self, olculen: np.ndarray) -> np.ndarray:
        d = olculen
        g = self.gorev
        h = -d[11]
        tilt = np.array([a.theta for a in self.ac.tilt])
        T = np.array([z.T for z in self.ac.itki])
        o = np.concatenate([
            d[0:3] / self.V_olcek,
            d[3:6],
            [math.sin(d[6]), math.cos(d[6]), math.sin(d[7]),
             math.cos(d[7]), math.sin(d[8]), math.cos(d[8])],
            [(h - g.h_hedef) / self.h_olcek, -d[2] / 10.0],
            tilt / (math.pi / 2),
            T / self.T_olcek,
            [g.V_hedef / self.V_olcek, g.h_hedef / self.h_olcek,
             g.faz_kodu, max(0.0, (g.sure - self.ac.t) / g.sure)],
        ])
        return np.asarray(o, dtype=np.float32)

    # -----------------------------------------------------------------
    def _zarf_ihlali(self, bilgi: dict) -> tuple[float, bool]:
        """Ucus zarfi ihlallerinin cezasi ve olumcul olup olmadigi."""
        ceza, bitti = 0.0, False
        d = self.ac.durum
        h = -d[11]
        # ⚠️ Stall cezasi YALNIZ kanat tasidiginda anlamli, ayrinti
        # 4-KARARLAR/15. V -> 0 iken alfa = atan2(w, u) sayisal olarak
        # +-180 dereceye gidiyor ve hover'da ceza SUREKLI atesleniyordu.
        # Olculen bedeli adim basina -2,23 idi, +2,50 takip odulunun
        # neredeyse tamami. V_S1 = 49,6 m/s, esik onun yarisi.
        V_hava = bilgi["V"]
        # V0: T2 geri gelir, stall cezasi hiz esigi OLMADAN ateslenir.
        if ((V_hava > V_STALL_ESIK or self.ortam_v0)
                and abs(bilgi["alfa"]) > self.ac.kanat.alfa_stall):
            ceza += 1.0
        if abs(d[6]) > math.radians(60) or abs(d[7]) > math.radians(60):
            ceza += 1.0
        if bilgi["n_yuk"] > self.ac.k["N_LIMIT"] or bilgi["n_yuk"] < -1.0:
            ceza += 1.0
        if bilgi["eklem_asim"] > 0.0:
            ceza += 2.0 * bilgi["eklem_asim"]
        bitti_enerji = False
        if bilgi["enerji_orani"] > 1.0:
            ceza += 5.0
            bitti = True
            bitti_enerji = True
        carpma = h <= 0.0
        if carpma:
            bitti = True
        tutum_asimi = (abs(d[6]) > math.radians(85)
                       or abs(d[7]) > math.radians(85))
        if tutum_asimi:
            bitti = True
        # V0: T3 geri gelir, YALNIZ tutum asimiyla biten bolum cokme
        # cezasi TASIMAZ. Bayrak kapaliyken her zaman False, davranis
        # degismez.
        self._v0_cezasiz = (self.ortam_v0 and bitti and tutum_asimi
                            and not carpma and not bitti_enerji)
        return ceza, bitti

    # -----------------------------------------------------------------
    def _odul(self, bilgi: dict, eylem: np.ndarray
              ) -> tuple[float, dict, bool]:
        A = ODUL_AGIRLIK
        g = self.gorev
        d = self.ac.durum
        h = -d[11]
        V_yer = math.hypot(d[0], d[1])

        e_hiz = abs(V_yer - g.V_hedef) / max(g.V_hedef, 10.0)
        # ⚠️ F1 — IRTIFA OLCEGININ TABANLANMASI (karar 39, bayrak arkasinda).
        # Sabit 50 m olcekle, gorev 150 m hatayla basladiginda irtifa terimi
        # exp(-9) = 1,2e-4 oluyor, yani OLU. Bu, seviye 2 ve seviye 4'te
        # gerceklesiyor ve tam olarak o iki seviye Kisim III'u tikiyor.
        # Terim olu oldugu icin alcalmanin odulde karsiligi yok, hiz terimi
        # ise alcalmayla iyilesiyor. Olculen sonuc, 40 bolumun 40'inin yere
        # carpmasi. Ayrinti 4-KARARLAR/39, teshis
        # testler/dogrulama_mufredat_esigi.py.
        # Bayrak KAPALI olan davranis dondurulmus kampanyalarin (kosular_v2,
        # kosular_uzun) davranisidir ve degistirilmedi.
        e_irt = abs(h - g.h_hedef) / self.irtifa_olcek
        e_tut = (abs(d[6]) + abs(d[7])) / math.radians(30)

        r_takip = (A["hiz"] * math.exp(-e_hiz ** 2)
                   + A["irtifa"] * math.exp(-e_irt ** 2)
                   + A["tutum"] * math.exp(-e_tut ** 2))
        c_kontrol = A["kontrol_eforu"] * float(np.mean(np.square(eylem)))
        c_tilt = A["tilt_orani"] * float(
            np.mean([abs(a.theta_p) / self.ac.k["THETA_HIZ"]
                     for a in self.ac.tilt]))
        c_enerji = A["enerji"] * bilgi["P_batarya"] / 1e6
        z, olumcul = self._zarf_ihlali(bilgi)
        c_zarf = A["zarf"] * z
        # ⚠️ Ceza HER olumcul sonlanmaya uygulanir, yalniz yere carpmaya
        # degil. Ayrinti 4-KARARLAR/15. Eski surumde tutumun 85 dereceyi
        # asmasi cezasiz bir cikis kapisiydi, yani politika icin en kisa
        # yol takla atmakti. Bolum uzunlugunun egitim boyunca KISALMASI
        # bunun belirtisiydi.
        c_cokme = (A["cokme"]
                   if olumcul and not self._v0_cezasiz else 0.0)

        r = r_takip - c_kontrol - c_tilt - c_enerji - c_zarf - c_cokme
        parca = dict(takip=r_takip, kontrol=-c_kontrol, tilt=-c_tilt,
                     enerji=-c_enerji, zarf=-c_zarf, cokme=-c_cokme,
                     hiz_hatasi=V_yer - g.V_hedef, irtifa_hatasi=h - g.h_hedef)
        return float(r), parca, olumcul

    # -----------------------------------------------------------------
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        g = self.gorev = self._gorev_sec()

        # F1 — olcek gorev basinda bir kez belirlenir, bolum boyunca sabit.
        self.irtifa_olcek = (
            max(IRTIFA_OLCEK, abs(g.baslangic_h - g.h_hedef))
            if self.irtifa_taban else IRTIFA_OLCEK)

        self.ac.ruzgar = atm.Ruzgar(
            dryden=atm.Dryden(siddet=g.gust, h=g.baslangic_h,
                              tohum=seed) if g.gust != "yok" else None)

        # Trim ankraji, eylemler buna gore artimsal olur.
        self.T_ank, self.tilt_ank = trim_ankraji(
            self.ac, g.baslangic_V, g.baslangic_h)

        d0 = np.zeros(12)
        d0[0] = g.baslangic_V
        d0[11] = -g.baslangic_h
        self.ac.sifirla(durum=d0, tilt0=float(np.mean(self.tilt_ank)),
                        T0=float(np.mean(self.T_ank)))
        self.ac.arizasiz()
        self._ariza_verildi = False

        olculen = self.ac.sensorler(self.ac.durum)
        return self._gozlem(olculen), {}

    # -----------------------------------------------------------------
    def step(self, eylem):
        e = np.clip(np.asarray(eylem, dtype=float), -1.0, 1.0)
        if self.ortam_v0:
            # V0: T1 geri gelir, esleme MUTLAK (karar 15 oncesi).
            # Sifir eylem 5518 N/pod ve 45 derece tilt demektir, tilt
            # kanallarinin trimi eylem uzayinin sinirindadir.
            T_komut = np.clip((e[:4] + 1.0) * 0.5 * self.T_olcek,
                              0.0, self.T_olcek)
            if self.n_tilt > 0:
                tilt_komut = np.clip(
                    (e[4:4 + self.n_tilt] + 1.0) * 0.5
                    * self.ac.k["THETA_MAX"],
                    0.0, self.ac.k["THETA_MAX"])
            else:
                tilt_komut = np.zeros(1)
            return self._step_govde(T_komut, tilt_komut, e)
        # TRIM'E GORE ARTIMSAL. Sifir eylem trimi korur.
        T_komut = np.clip(self.T_ank * (1.0 + KT_YETKI * e[:4]),
                          0.0, self.T_olcek)
        if self.n_tilt > 0 and not self.tilt_kanali_kapali:
            # Varyantin her tilt grubu icin ankraj, grubun ilk podundan
            th_ank = np.array([self.tilt_ank[grup[0]]
                               for grup in self.ac.var.tilt_gruplari])
            tilt_komut = np.clip(th_ank + KTH_YETKI * e[4:4 + self.n_tilt],
                                 0.0, self.ac.k["THETA_MAX"])
        elif self.n_tilt > 0:
            # kanal kapali: tilt ucus programinda kalir, politika dokunmaz
            tilt_komut = np.array([self.tilt_ank[grup[0]]
                                   for grup in self.ac.var.tilt_gruplari])
        else:
            tilt_komut = np.zeros(1)
        return self._step_govde(T_komut, tilt_komut, e)

    def _step_govde(self, T_komut, tilt_komut, e):
        g = self.gorev
        if (g.ariza_pod is not None and not self._ariza_verildi
                and self.ac.t >= g.ariza_ani):
            self.ac.ariza_ver(g.ariza_pod, 1)
            self._ariza_verildi = True

        kademe = "oei" if self._ariza_verildi else "surekli"
        olculen, bilgi = self.ac.adim(T_komut, tilt_komut, kademe)

        odul, parca, olumcul = self._odul(bilgi, e)
        bitti = bool(olumcul)
        kesildi = bool(self.ac.t >= g.sure)

        bilgi = {k: v for k, v in bilgi.items()
                 if k in ("V", "alfa", "P_batarya", "n_yuk", "enerji",
                          "enerji_orani", "eklem_asim", "t")}
        bilgi.update(parca)
        bilgi["gorev"] = g.ad
        bilgi["varyant"] = self.varyant
        return self._gozlem(olculen), odul, bitti, kesildi, bilgi


# =====================================================================
def ortam_yap(varyant="limulus", seviye=0, tohum=None, sensor=True):
    return LimulusOrtami(varyant=varyant, seviye=seviye, tohum=tohum,
                         sensor=sensor)


if __name__ == "__main__":
    print("MUFREDAT")
    for i, g in enumerate(MUFREDAT):
        print(f"  {i}  {g.ad:<12} {g.sure:>5.0f} s  V*={g.V_hedef:>5.1f} "
              f"h*={g.h_hedef:>5.0f}  gust={g.gust:<8} "
              f"ariza={'pod ' + str(g.ariza_pod) if g.ariza_pod is not None else '-'}")

    print("\nORTAM BOYUTLARI")
    for v in ("limulus", "ikili", "senkron", "liftcruise"):
        o = ortam_yap(v)
        print(f"  {o.ac.var.ad:<16} eylem {o.action_space.shape[0]}  "
              f"gozlem {o.observation_space.shape[0]}")

    print("\nRASTGELE POLITIKA — 3 bolum (sanity check)")
    for sev in (0, 2, 5):
        o = ortam_yap("limulus", seviye=sev, tohum=1)
        g, _ = o.reset(seed=1)
        assert g.shape == (26,), g.shape
        top, n = 0.0, 0
        while True:
            g, r, bitti, kesildi, bilgi = o.step(o.action_space.sample())
            top += r
            n += 1
            if bitti or kesildi:
                break
        print(f"  seviye {sev} ({MUFREDAT[sev].ad:<10}) {n:>4} adim  "
              f"toplam odul {top:>9.1f}  "
              f"{'COKTU' if bitti else 'sure doldu'}  "
              f"enerji %{bilgi['enerji_orani']*100:.1f}")

    print("\nSIFIR EYLEM — trim korunuyor mu (artimsal esleme kontrolu)")
    print("  Beklenen: bolum sure doldurarak bitmeli, irtifa hatasi kucuk.")
    print("  Bu test 03.08.2026'dan once GECMIYORDU, ayrinti 4-KARARLAR/15.")
    for v in ("limulus", "ikili", "senkron", "liftcruise"):
        o = ortam_yap(v, seviye=0, tohum=2, sensor=False)
        o.reset(seed=2)
        e = np.zeros(o.n_eylem)
        top = 0.0
        for i in range(int(20.0 / o.dt)):
            gz, r, bitti, kesildi, bilgi = o.step(e)
            top += r
            if bitti or kesildi:
                break
        print(f"  {v:<11} {i+1:>4} adim  irtifa hatasi "
              f"{bilgi['irtifa_hatasi']:+7.2f} m  toplam odul {top:>7.1f}  "
              f"guc {bilgi['P_batarya']/1e3:>5.0f} kW  "
              f"{'COKTU' if bitti else 'sure doldu'}")
