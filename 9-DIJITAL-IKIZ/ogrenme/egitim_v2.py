#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPO EGITIM v2 — duzeltilmis kosu

`egitim.py` pilot kosuyu uretti ve DEGISTIRILMEDI, cunku o kosunun
sonuclari tekrar uretilebilir kalmali. Bu dosya, pilot sonrasi
duzeltmeleri tasiyan ayri bir surumdur.

DEGISIKLIKLER — hepsi 4-KARARLAR/12-egitim-butcesi-on-kaydi.md
belgesinde, pilot deneyin TAM SONUCLARI GORULMEDEN sabitlendi.

  D1  Politika cikis sapmasi hover trim noktasinda baslatilir
  D2  Baslangic log_std -0,5 yerine -1,5
  D3  Gozlem normalizasyonu (kosan ortalama ve varyans)
  D4  Butce 400k yerine 1M adim
  D5  Enerji cezasi mutlak degil, faz trim gucune GORE

Degismeyenler ayni belgenin §4'unde listeli. Ozellikle mufredat
esigi (0,65), odul agirliklari, PPO hiperparametreleri ve fizik
modelinin hicbir parametresi degistirilmedi.

⚠️ TESHIS — ILK SURUM EKSIKTI. Pilotta ortalama bolum uzunlugu
1000 adimlik azamiye karsilik 79 adim cikti. Ilk teshis "sifir eylem
5.518 N itki veriyor, hover 7.622 N istiyor" idi ve D1 bunu kapatiyordu.
D1 YETMEDI, cunku teshis eksikti. Uc yapisal kusur daha vardi ve ucu de
ORTAMIN tanimindaydi, hiperparametrelerde degil.

  T1  Eylem uzayi mutlakti, tilt kanallarinin trimi eylem uzayinin
      SINIRINDAYDI. Gauss politikasi bir sinira kutle yerlestiremez.
  T2  Hucum acisi V -> 0 iken +-180 derece veriyordu, hover'da stall
      cezasi surekli atesleniyordu. Bedeli adim basina -2,23.
  T3  Tutumun 85 dereceyi asmasi CEZASIZ sonlaniyordu, yani politika
      icin en kisa yol takla atmakti.

Ucu de duzeltildi (4-KARARLAR/15, ortam.py). T1'den sonra D1 gereksiz
hale geldi ve sifir vektore cevrildi. Duzeltme sonrasi ilk olcum:
300 bin adimda limulus seviye 1'e, senkron seviye 2'ye ulasti.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from dataclasses import asdict, dataclass, field

import numpy as np

try:
    import torch
    import torch.nn as nn
except ImportError:                                      # pragma: no cover
    raise SystemExit("PyTorch gerekli:  pip install torch")

_BURASI = os.path.dirname(os.path.abspath(__file__))
if _BURASI not in sys.path:
    sys.path.insert(0, _BURASI)

from egitim import gae                                   # noqa: E402
from ortam import MUFREDAT, LimulusOrtami                # noqa: E402


# =====================================================================
@dataclass
class Ayar2:
    varyant: str = "limulus"
    toplam_adim: int = 1_000_000          # D4
    rulo: int = 2048
    devir: int = 10
    yigin: int = 256
    # ⚠️ F2 — ISKONTO UFKU (karar 41, bayrak arkasinda).
    # gamma 0,99 ile etkin ufuk 1/(1-gamma) = 100 adim, yani 2 saniye.
    # Seviye 2 gorevi 40 saniye, yani ajan gorevin yirmide birini goruyor.
    # Alcalma karari 0,2. saniyede veriliyor, carpma 16,5. saniyede geliyor
    # ve aradaki iskonto carpani 2,6e-04. Bu yuzden sonlanma cezasinin
    # BUYUKLUGU degil, ufkun kendisi baglayici. Ayrinti 4-KARARLAR/41.
    # Varsayilan 0,99'dur ve DEGISTIRILMEDI, dolayisiyla dondurulmus
    # kampanyalar (kosular_v2, kosular_uzun, kosular_esik_sonda*) ayni
    # deger ile yeniden uretilebilir. Acik kosular AYRI dizine yazilir.
    # NOT. Raporlanan odul metrigi (bolum odulu / n_azami) INDIRIMSIZ
    # hesaplanir, dolayisiyla gamma degisikligi 0,65 kapisini ve
    # kampanyalar arasi karsilastirilabilirligi DEGISTIRMEZ.
    gamma: float = float(os.environ.get("LIMULUS_GAMMA", "0.99"))
    lam: float = 0.95
    kirpma: float = 0.2
    lr: float = 3e-4
    entropi: float = 0.004
    deger_katsayi: float = 0.5
    grad_kirp: float = 0.5
    gizli: int = 128
    tohum: int = 0
    mufredat_esigi: float = 0.65          # DONMUS, degistirilmedi
    mufredat_pencere: int = 20
    # ⚠️ HANGI MUFREDAT KOLUNDA KOSULDUGU 09.08.2026'da eklendi.
    # CLAUDE.md kurali, "kullanilan deger her kosunun gunlugunde ayar
    # alaninda". Karar 47 sondasinin sekiz kosusu bu alan OLMADAN kosuldu ve
    # kolun hangisi oldugu yalniz hucre dizin adindan okunabiliyordu. Alan
    # kampanya BITTIKTEN SONRA eklendi, ortasinda eklenmedi, cunku o durumda
    # kosularin bir kismi alani tasir bir kismi tasimaz ve kampanya kendi
    # icinde tutarsiz olur.
    # Deger ortam degiskeninden OKUNUR, ayrica ayarlanmaz, boylece gunluk ile
    # ortamin gordugu mufredat AYNI kaynaktan gelir ve ayrisamaz.
    mufredat_ince: bool = field(
        default_factory=lambda: os.environ.get("LIMULUS_MUFREDAT_INCE", "0") == "1")
    # ⚠️ SOYAGACI (karar 52). Uc ortam bayragi da gunluge yazilir, deger
    # ortam degiskeninden OKUNUR, boylece gunluk ile ortamin gordugu
    # yapilandirma ayni kaynaktan gelir ve ayrisamaz.
    irtifa_taban: bool = field(
        default_factory=lambda: os.environ.get("LIMULUS_IRTIFA_TABAN", "0") == "1")
    cruise_itki: bool = field(
        default_factory=lambda: os.environ.get("LIMULUS_CRUISE_ITKI", "0") == "1")
    ortam_v0: bool = field(
        default_factory=lambda: os.environ.get("LIMULUS_ORTAM_V0", "0") == "1")
    sensor: bool = True
    log_std0: float = -1.5                # D2
    trim_sapmasi: bool = True             # D1
    gozlem_norm: bool = True              # D3


# =====================================================================
class KosanNorm:
    """D3 — kosan ortalama ve varyansla gozlem normalizasyonu.

    Welford guncellemesi. Yalniz egitim rulosu sirasinda guncellenir,
    degerlendirme sirasinda dondurulur.
    """

    def __init__(self, n: int, eps: float = 1e-8):
        self.ort = np.zeros(n, dtype=np.float64)
        self.var = np.ones(n, dtype=np.float64)
        self.sayac = 1e-4
        self.eps = eps
        self.acik = True

    def guncelle(self, x: np.ndarray):
        if not self.acik:
            return
        x = np.atleast_2d(x)
        n = x.shape[0]
        ort_b = x.mean(axis=0)
        var_b = x.var(axis=0)
        fark = ort_b - self.ort
        top = self.sayac + n
        self.ort += fark * n / top
        m_a = self.var * self.sayac
        m_b = var_b * n
        self.var = (m_a + m_b + fark ** 2 * self.sayac * n / top) / top
        self.sayac = top

    def __call__(self, x: np.ndarray) -> np.ndarray:
        return np.clip((x - self.ort) / np.sqrt(self.var + self.eps),
                       -10.0, 10.0).astype(np.float32)

    def kaydet(self) -> dict:
        return dict(ort=self.ort.tolist(), var=self.var.tolist(),
                    sayac=float(self.sayac))


# =====================================================================
class Politika2(nn.Module):
    def __init__(self, n_gozlem: int, n_eylem: int, gizli: int = 128,
                 log_std0: float = -1.5, sapma0: np.ndarray | None = None):
        super().__init__()
        def govde():
            return nn.Sequential(
                nn.Linear(n_gozlem, gizli), nn.Tanh(),
                nn.Linear(gizli, gizli), nn.Tanh())
        self.aktor_govde = govde()
        self.aktor_bas = nn.Linear(gizli, n_eylem)
        self.elestirmen = nn.Sequential(govde(), nn.Linear(gizli, 1))
        self.log_std = nn.Parameter(torch.full((n_eylem,), log_std0))

        nn.init.orthogonal_(self.aktor_bas.weight, gain=0.01)
        # D1 — cikis sapmasi trim noktasinda
        if sapma0 is None:
            nn.init.zeros_(self.aktor_bas.bias)
        else:
            with torch.no_grad():
                self.aktor_bas.bias.copy_(torch.as_tensor(sapma0,
                                                          dtype=torch.float32))

    def dagilim(self, g):
        return torch.distributions.Normal(
            self.aktor_bas(self.aktor_govde(g)), self.log_std.exp())

    def deger(self, g):
        return self.elestirmen(g).squeeze(-1)

    @torch.no_grad()
    def eylem(self, g, ornekle: bool = True):
        t = torch.as_tensor(g, dtype=torch.float32).unsqueeze(0)
        d = self.dagilim(t)
        a = d.sample() if ornekle else d.mean
        return (a.squeeze(0).numpy(),
                d.log_prob(a).sum(-1).item(),
                self.deger(t).item())


# =====================================================================
def trim_sapmasi_hesapla(ortam: LimulusOrtami) -> np.ndarray:
    """D1 — trim noktasina karsilik gelen normalize eylem.

    ⚠️ 03.08.2026'da GEREKSIZ HALE GELDI, ayrinti 4-KARARLAR/15.

    Bu duzeltme, ortamin eylem eslemesi MUTLAK oldugu donemde yazildi.
    O donemde hover trimi (+0,333 x4, -1,000 x n) koordinatindaydi ve
    politikanin baslangic ortalamasi oraya kaydiriliyordu. Esleme artik
    TRIME GORE ARTIMSAL, yani sifir eylem zaten trimi koruyor. Dogru
    baslangic sapmasi SIFIRDIR.

    Fonksiyon silinmedi cunku ön kayit belgesi (4-KARARLAR/12) D1'i
    adiyla listeliyor. Artik sifir vektor donduruyor ve neden dondurdugu
    burada yaziyor.
    """
    return np.zeros(ortam.n_eylem, dtype=np.float32)


def faz_referans_gucu(ortam: LimulusOrtami) -> float:
    """D5 — gorev fazinin trim gucu. Enerji cezasi buna GORE olculur."""
    import atmosfer as atm
    from trim import trim
    try:
        r = trim(ortam.ac, float(ortam.gorev.V_hedef), 0.0,
                 float(ortam.gorev.h_hedef))
        if r.basarili and r.P_batarya > 1e3:
            return float(r.P_batarya)
    except Exception:
        pass
    return float(ortam.ac.W * 0.35)      # kaba yedek, ~1 MW mertebesi


# =====================================================================
def egit2(a: Ayar2, cikti_dizin: str | None = None) -> dict:
    import os as _os
    cikti_dizin = cikti_dizin or _os.environ.get(
        "LIMULUS_KOSU_DIZINI", "kosular_v2")
    torch.manual_seed(a.tohum)
    np.random.seed(a.tohum)

    ortam = LimulusOrtami(varyant=a.varyant, seviye=0, tohum=a.tohum,
                          sensor=a.sensor)
    n_g = ortam.observation_space.shape[0]
    n_e = ortam.action_space.shape[0]

    sapma0 = trim_sapmasi_hesapla(ortam) if a.trim_sapmasi else None
    pol = Politika2(n_g, n_e, a.gizli, a.log_std0, sapma0)
    opt = torch.optim.Adam(pol.parameters(), lr=a.lr, eps=1e-5)
    norm = KosanNorm(n_g) if a.gozlem_norm else None

    # D5 — her seviye icin referans guc, bir kez hesaplanir.
    # ⚠️ Devam ederken YENIDEN HESAPLANMAZ — bu dongu dakikalar suruyor
    # ve her devam basinda odenmesi 10 dakikalik pencerenin besde birini
    # yiyordu. Ara kayittan okunur.
    import os as _o2
    _ara_on = _o2.path.join(cikti_dizin or "kosular_v2",
                            f"{a.varyant}_t{a.tohum}_ara.pt")
    P_ref = None
    if _o2.path.exists(_ara_on):
        try:
            P_ref = {int(k): v for k, v in
                     torch.load(_ara_on, map_location="cpu",
                                weights_only=False)["P_ref"].items()}
        except Exception:
            P_ref = None
    if P_ref is None:
        P_ref = {}
        for i in range(len(MUFREDAT)):
            ortam.seviye = i
            ortam.gorev = MUFREDAT[i]
            P_ref[i] = faz_referans_gucu(ortam)
    ortam.seviye = 0
    ortam.gorev = MUFREDAT[0]

    def hazirla(g):
        return norm(g) if norm is not None else g

    os.makedirs(cikti_dizin, exist_ok=True)
    kok = os.path.join(cikti_dizin, f"{a.varyant}_t{a.tohum}")
    ara_yol = kok + "_ara.pt"

    ham, _ = ortam.reset(seed=a.tohum)
    gozlem = hazirla(ham)
    bolum_odulleri, son_oduller, gunluk = [], [], []
    n_bolum_toplam = 0          # ⚠️ kirpilmayan sayac, bkz. 4-KARARLAR/25
    bolum_odul, toplam = 0.0, 0

    # --- ARA KAYITTAN DEVAM ---
    # ⚠️ Konteyner oturum bostayken hesabi durduruyor ve bir kosu tek
    # seferde bitmiyor. Ara kayit olmadan her kesinti butun isi cope
    # atiyordu. Bkz. 4-KARARLAR/24.
    if os.path.exists(ara_yol):
        try:
            ck = torch.load(ara_yol, map_location="cpu", weights_only=False)
            pol.load_state_dict(ck["pol"])
            opt.load_state_dict(ck["opt"])
            toplam = int(ck["toplam"])
            gunluk = ck["gunluk"]
            bolum_odulleri = ck.get("bolum_odulleri", [])
            n_bolum_toplam = int(ck.get("n_bolum_toplam",
                                        len(bolum_odulleri)))
            son_oduller = ck.get("son_oduller", [])
            ortam.seviye = int(ck["seviye"])
            ortam.gorev = MUFREDAT[ortam.seviye]
            if norm is not None and ck.get("norm"):
                norm.ort[:] = np.array(ck["norm"]["ort"])
                norm.var[:] = np.array(ck["norm"]["var"])
                norm.sayac = float(ck["norm"]["n"])
            torch.set_rng_state(ck["torch_rng"])
            np.random.set_state(ck["np_rng"])
            ham, _ = ortam.reset()
            gozlem = hazirla(ham)
            print(f"  [devam] {ara_yol} · {toplam:,} adimdan suruyor",
                  flush=True)
        except Exception as _e:
            print(f"  [devam] ara kayit okunamadi ({_e}), bastan", flush=True)

    t0 = time.time()
    _son_kayit = time.time()

    while toplam < a.toplam_adim:
        G, E, LP, R, D, V = [], [], [], [], [], []
        hamlar = []
        for _ in range(a.rulo):
            e, lp, v = pol.eylem(gozlem)
            yeni_ham, odul, bitti, kesildi, bilgi = ortam.step(e)

            # D5 — enerji cezasini faz referansina gore yeniden olcekle
            P = bilgi.get("P_batarya", 0.0)
            Pr = P_ref[ortam.seviye]
            odul += -bilgi.get("enerji", 0.0)          # eski terimi geri al
            odul -= 0.2 * max(0.0, (P - Pr)) / max(Pr, 1.0)

            G.append(gozlem); E.append(e); LP.append(lp)
            R.append(odul); D.append(float(bitti)); V.append(v)
            hamlar.append(yeni_ham)
            bolum_odul += odul
            toplam += 1
            gozlem = hazirla(yeni_ham)
            if bitti or kesildi:
                n_azami = max(int(ortam.gorev.sure / ortam.dt), 1)
                bolum_odulleri.append(bolum_odul / n_azami)
                n_bolum_toplam += 1
                son_oduller.append(bolum_odul / n_azami)
                bolum_odul = 0.0
                ham, _ = ortam.reset()
                gozlem = hazirla(ham)

        if norm is not None:
            norm.guncelle(np.array(hamlar))

        with torch.no_grad():
            son_v = pol.deger(torch.as_tensor(
                gozlem, dtype=torch.float32).unsqueeze(0)).item()
        avantaj, getiri = gae(R, V, D, son_v, a.gamma, a.lam)

        tG = torch.as_tensor(np.array(G), dtype=torch.float32)
        tE = torch.as_tensor(np.array(E), dtype=torch.float32)
        tLP = torch.as_tensor(np.array(LP), dtype=torch.float32)
        tA = torch.as_tensor(avantaj); tR = torch.as_tensor(getiri)
        tA = (tA - tA.mean()) / (tA.std() + 1e-8)

        n = len(G)
        for _ in range(a.devir):
            sira = torch.randperm(n)
            for b in range(0, n, a.yigin):
                i = sira[b:b + a.yigin]
                d = pol.dagilim(tG[i])
                lp = d.log_prob(tE[i]).sum(-1)
                oran = (lp - tLP[i]).exp()
                k1 = oran * tA[i]
                k2 = torch.clamp(oran, 1 - a.kirpma, 1 + a.kirpma) * tA[i]
                kayip = (-torch.min(k1, k2).mean()
                         + a.deger_katsayi * ((pol.deger(tG[i]) - tR[i]) ** 2).mean()
                         - a.entropi * d.entropy().sum(-1).mean())
                opt.zero_grad(); kayip.backward()
                nn.utils.clip_grad_norm_(pol.parameters(), a.grad_kirp)
                opt.step()

        ort = float(np.mean(son_oduller[-a.mufredat_pencere:])) \
            if son_oduller else float("-inf")
        n_bol = max(n_bolum_toplam, 1)
        gunluk.append(dict(adim=toplam, odul=ort, seviye=ortam.seviye,
                           n_bolum=n_bolum_toplam,
                           ort_bolum_uzunlugu=toplam / n_bol,
                           sure=time.time() - t0))

        if (len(son_oduller) >= a.mufredat_pencere
                and ort >= a.mufredat_esigi
                and ortam.seviye < len(MUFREDAT) - 1):
            ortam.seviye_yukselt()
            son_oduller = []
            ham, _ = ortam.reset(); gozlem = hazirla(ham)
            print(f"  [{toplam:>8}] seviye -> {ortam.seviye} "
                  f"({MUFREDAT[ortam.seviye].ad})", flush=True)

        if len(gunluk) % 25 == 0:
            print(f"  [{toplam:>8}] sev {ortam.seviye} odul {ort:+.3f} "
                  f"bolum_uz {toplam/n_bol:5.0f} "
                  f"{toplam/(time.time()-t0):.0f} adim/s", flush=True)

        # --- periyodik ara kayit (45 s) — ATOMIK (karar: uzun kosu emniyeti) ---
        # Once .tmp'ye yazilir, sonra os.replace ile tek atomik islemle yerine
        # konur. Boylece timeout/SIGKILL tam yazim sirasinda gelse bile eldeki
        # son SAGLAM kayit korunur, "bastan" senaryosu olusamaz.
        if time.time() - _son_kayit > 45.0:
            _tmp = ara_yol + ".tmp"
            torch.save(dict(pol=pol.state_dict(), opt=opt.state_dict(),
                            toplam=toplam, gunluk=gunluk, seviye=ortam.seviye,
                            bolum_odulleri=bolum_odulleri[-200:],
                            n_bolum_toplam=n_bolum_toplam,
                            son_oduller=son_oduller[-200:],
                            norm=(dict(ort=norm.ort.tolist(),
                                       var=norm.var.tolist(), n=float(norm.sayac))
                                  if norm is not None else None),
                            torch_rng=torch.get_rng_state(),
                            np_rng=np.random.get_state(),
                            P_ref=P_ref), _tmp)
            os.replace(_tmp, ara_yol)
            _dtmp = kok + "_ara_durum.json.tmp"
            with open(_dtmp, "w") as _f:
                json.dump(dict(adim=int(toplam), seviye=int(ortam.seviye),
                               zaman=time.time()), _f)
            os.replace(_dtmp, kok + "_ara_durum.json")
            _son_kayit = time.time()

    # BITIS — sira kritik (uzun kosu emniyeti): once nihai .pt ve gunluk
    # ATOMIK yazilir, ara kayit ancak ikisi de saglam yerdeyken silinir.
    # Eski sirada ara once siliniyordu ve tam o anda kesilen bir kosu
    # 3M adimi sifirdan almak zorunda kalirdi.
    torch.save(pol.state_dict(), kok + ".pt.tmp")
    os.replace(kok + ".pt.tmp", kok + ".pt")
    with open(kok + "_gunluk.json.tmp", "w") as f:
        json.dump(dict(ayar=asdict(a), gunluk=gunluk,
                       gozlem_norm=norm.kaydet() if norm else None,
                       P_ref={str(k): v for k, v in P_ref.items()}), f, indent=1)
    os.replace(kok + "_gunluk.json.tmp", kok + "_gunluk.json")
    for _art in (ara_yol, kok + "_ara_durum.json"):
        if os.path.exists(_art):
            os.remove(_art)
    return dict(gunluk=gunluk, yol=kok)


# =====================================================================
if __name__ == "__main__":
    p = argparse.ArgumentParser(description="LIMULUS PPO v2")
    p.add_argument("--varyant", default="limulus",
                   choices=["limulus", "ikili", "senkron", "liftcruise"])
    p.add_argument("--adim", type=int, default=1_000_000)
    p.add_argument("--tohum", type=int, default=0)
    p.add_argument("--duman", action="store_true")
    # ⚠️ KARAR 47 SONDASI. Ikisi de ONTANIM ESKI DAVRANIS.
    # --log-std0 kesif genisligi, ontanim -1,5 (D2 duzeltmesi).
    # --cikti sonda kosularini ayri dizine yazar (karar 22 ayri dizin kurali).
    # Ince mufredat ORTAM DEGISKENIYLE acilir, LIMULUS_MUFREDAT_INCE=1.
    p.add_argument("--log-std0", type=float, default=None,
                   dest="log_std0")
    p.add_argument("--cikti", default=None,
                   help="sonuc dizini, karar 47 sondasi icin ayri dizin")
    ar = p.parse_args()

    ayar = Ayar2(varyant=ar.varyant, tohum=ar.tohum,
                 toplam_adim=8192 if ar.duman else ar.adim,
                 rulo=1024 if ar.duman else 2048,
                 devir=4 if ar.duman else 10)
    if ar.log_std0 is not None:
        ayar.log_std0 = ar.log_std0
    print(f"PPO v2  {ayar.varyant}  tohum {ayar.tohum}  "
          f"adim {ayar.toplam_adim:,}  log_std0 {ayar.log_std0}  "
          f"trim sapmasi {ayar.trim_sapmasi}  gozlem norm {ayar.gozlem_norm}")
    # Duman testi SONUC DIZININE yazmaz, tam kosuyu ezme riski var.
    s = egit2(ayar, cikti_dizin=("duman" if ar.duman
                                 else (ar.cikti if ar.cikti else None)))
    g = s["gunluk"]
    print(f"\nbitti. son odul {g[-1]['odul']:+.3f}  seviye {g[-1]['seviye']}  "
          f"ort bolum uzunlugu {g[-1]['ort_bolum_uzunlugu']:.0f} adim  "
          f"{g[-1]['sure']:.0f} s")
