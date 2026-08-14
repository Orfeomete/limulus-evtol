#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPO EGITIM BETIGI — bagimsiz uygulama, PyTorch

Neden hazir kutuphane degil. Uc gerekce var.
  1  Bagimlilik zinciri kisa kalir, tez ekinde tam kod verilebilir.
  2  Mufredat ve varyant kisitlarina dogrudan mudahale edilebilir.
  3  Ogrenme verimi metrigi (metrikler.py §6) egitim gunlugunun tam
     kontrolunu gerektirir.

Uygulama, Schulman ve ark. (2017) PPO-clip algoritmasidir. Genellestirilmis
avantaj kestirimi (GAE-lambda) ile birlikte kullanilir. Surekli eylem
uzayinda kosegen Gauss politikasi, ogrenilebilir log-std.

MUFREDAT. Ajan seviye 0'da baslar. Son N bolumun ortalama odulu esigi
gecerse bir ust seviyeye gecer. YL tezinde (YOK 855246) ayni zincir
calisti, oradan devralinmistir.

DENEY TASARIMI. Karsilastirma icin her varyant ayni tohum setiyle,
ayni hiperparametrelerle ve ayni mufredatla egitilir. Tek degisken
kontrol mimarisidir.
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

from ortam import MUFREDAT, LimulusOrtami                # noqa: E402


# =====================================================================
@dataclass
class Ayar:
    varyant: str = "limulus"
    toplam_adim: int = 300_000
    rulo: int = 2048              # her guncelleme oncesi toplanan adim
    devir: int = 10               # her rulo icin epoch
    yigin: int = 256
    gamma: float = 0.99
    lam: float = 0.95
    kirpma: float = 0.2
    lr: float = 3e-4
    entropi: float = 0.004
    deger_katsayi: float = 0.5
    grad_kirp: float = 0.5
    gizli: int = 128
    tohum: int = 0
    mufredat_esigi: float = 0.65   # gorev suresine gore normalize odul
    mufredat_pencere: int = 20
    sensor: bool = True
    cihaz: str = "cpu"


# =====================================================================
class Politika(nn.Module):
    def __init__(self, n_gozlem: int, n_eylem: int, gizli: int = 128):
        super().__init__()
        def govde():
            return nn.Sequential(
                nn.Linear(n_gozlem, gizli), nn.Tanh(),
                nn.Linear(gizli, gizli), nn.Tanh())
        self.aktor_govde = govde()
        self.aktor_bas = nn.Linear(gizli, n_eylem)
        self.elestirmen = nn.Sequential(govde(), nn.Linear(gizli, 1))
        self.log_std = nn.Parameter(torch.full((n_eylem,), -0.5))
        # kucuk cikis katmani, baslangicta politika neredeyse deterministik
        nn.init.orthogonal_(self.aktor_bas.weight, gain=0.01)
        nn.init.zeros_(self.aktor_bas.bias)

    def dagilim(self, g: torch.Tensor):
        ort = self.aktor_bas(self.aktor_govde(g))
        return torch.distributions.Normal(ort, self.log_std.exp())

    def deger(self, g: torch.Tensor) -> torch.Tensor:
        return self.elestirmen(g).squeeze(-1)

    @torch.no_grad()
    def eylem(self, g: np.ndarray, ornekle: bool = True):
        t = torch.as_tensor(g, dtype=torch.float32).unsqueeze(0)
        d = self.dagilim(t)
        a = d.sample() if ornekle else d.mean
        return (a.squeeze(0).numpy(),
                d.log_prob(a).sum(-1).item(),
                self.deger(t).item())


# =====================================================================
def gae(oduller, degerler, bitisler, son_deger, gamma, lam):
    n = len(oduller)
    avantaj = np.zeros(n, dtype=np.float32)
    onceki = 0.0
    for i in reversed(range(n)):
        sonraki_v = son_deger if i == n - 1 else degerler[i + 1]
        surer = 1.0 - bitisler[i]
        delta = oduller[i] + gamma * sonraki_v * surer - degerler[i]
        onceki = delta + gamma * lam * surer * onceki
        avantaj[i] = onceki
    return avantaj, avantaj + np.asarray(degerler, dtype=np.float32)


# =====================================================================
def egit(a: Ayar, cikti_dizin: str = "kosular") -> dict:
    torch.manual_seed(a.tohum)
    np.random.seed(a.tohum)

    ortam = LimulusOrtami(varyant=a.varyant, seviye=0, tohum=a.tohum,
                          sensor=a.sensor)
    n_g = ortam.observation_space.shape[0]
    n_e = ortam.action_space.shape[0]
    pol = Politika(n_g, n_e, a.gizli)
    opt = torch.optim.Adam(pol.parameters(), lr=a.lr, eps=1e-5)

    gozlem, _ = ortam.reset(seed=a.tohum)
    gunluk, bolum_odulleri, son_oduller = [], [], []
    bolum_odul, bolum_adim, toplam = 0.0, 0, 0
    t0 = time.time()

    while toplam < a.toplam_adim:
        G, E, LP, R, D, V = [], [], [], [], [], []
        for _ in range(a.rulo):
            e, lp, v = pol.eylem(gozlem)
            yeni, odul, bitti, kesildi, _ = ortam.step(e)
            G.append(gozlem); E.append(e); LP.append(lp)
            R.append(odul); D.append(float(bitti)); V.append(v)
            bolum_odul += odul
            bolum_adim += 1
            toplam += 1
            gozlem = yeni
            if bitti or kesildi:
                # gorev suresine gore normalize odul, seviyeler arasi
                # karsilastirilabilir olsun diye
                n_azami = max(int(ortam.gorev.sure / ortam.dt), 1)
                bolum_odulleri.append(bolum_odul / n_azami)
                son_oduller.append(bolum_odul / n_azami)
                bolum_odul, bolum_adim = 0.0, 0
                gozlem, _ = ortam.reset()

        with torch.no_grad():
            son_v = pol.deger(torch.as_tensor(
                gozlem, dtype=torch.float32).unsqueeze(0)).item()
        avantaj, getiri = gae(R, V, D, son_v, a.gamma, a.lam)

        tG = torch.as_tensor(np.array(G), dtype=torch.float32)
        tE = torch.as_tensor(np.array(E), dtype=torch.float32)
        tLP = torch.as_tensor(np.array(LP), dtype=torch.float32)
        tA = torch.as_tensor(avantaj)
        tR = torch.as_tensor(getiri)
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
                kayip_pol = -torch.min(k1, k2).mean()
                kayip_deg = ((pol.deger(tG[i]) - tR[i]) ** 2).mean()
                entropi = d.entropy().sum(-1).mean()
                kayip = (kayip_pol + a.deger_katsayi * kayip_deg
                         - a.entropi * entropi)
                opt.zero_grad()
                kayip.backward()
                nn.utils.clip_grad_norm_(pol.parameters(), a.grad_kirp)
                opt.step()

        ort = float(np.mean(son_oduller[-a.mufredat_pencere:])) \
            if son_oduller else float("-inf")
        gunluk.append(dict(adim=toplam, odul=ort, seviye=ortam.seviye,
                           n_bolum=len(bolum_odulleri),
                           sure=time.time() - t0))

        # --- mufredat ilerlemesi ---
        if (len(son_oduller) >= a.mufredat_pencere
                and ort >= a.mufredat_esigi
                and ortam.seviye < len(MUFREDAT) - 1):
            ortam.seviye_yukselt()
            son_oduller = []
            gozlem, _ = ortam.reset()
            print(f"  [{toplam:>7}] seviye -> {ortam.seviye} "
                  f"({MUFREDAT[ortam.seviye].ad})")

        if len(gunluk) % 10 == 0:
            print(f"  [{toplam:>7}] seviye {ortam.seviye} "
                  f"odul {ort:+.3f}  {toplam/(time.time()-t0):.0f} adim/s")

    os.makedirs(cikti_dizin, exist_ok=True)
    kok = os.path.join(cikti_dizin, f"{a.varyant}_t{a.tohum}")
    torch.save(pol.state_dict(), kok + ".pt")
    with open(kok + "_gunluk.json", "w") as f:
        json.dump(dict(ayar=asdict(a), gunluk=gunluk), f, indent=1)
    return dict(gunluk=gunluk, politika=pol, yol=kok)


# =====================================================================
def politika_yukle(yol: str, varyant: str):
    ortam = LimulusOrtami(varyant=varyant)
    pol = Politika(ortam.observation_space.shape[0],
                   ortam.action_space.shape[0])
    pol.load_state_dict(torch.load(yol, map_location="cpu"))
    pol.eval()
    def f(g):
        return pol.eylem(g, ornekle=False)[0]
    return f


# =====================================================================
if __name__ == "__main__":
    p = argparse.ArgumentParser(description="LIMULUS PPO egitimi")
    p.add_argument("--varyant", default="limulus",
                   choices=["limulus", "ikili", "senkron", "liftcruise"])
    p.add_argument("--adim", type=int, default=300_000)
    p.add_argument("--tohum", type=int, default=0)
    p.add_argument("--duman", action="store_true",
                   help="kisa duman testi, 6000 adim")
    ar = p.parse_args()

    ayar = Ayar(varyant=ar.varyant, tohum=ar.tohum,
                toplam_adim=6000 if ar.duman else ar.adim,
                rulo=512 if ar.duman else 2048,
                devir=4 if ar.duman else 10)
    print(f"PPO egitimi  varyant={ayar.varyant}  tohum={ayar.tohum}  "
          f"adim={ayar.toplam_adim}")
    s = egit(ayar)
    g = s["gunluk"]
    print(f"\nbitti. {len(g)} guncelleme, son odul {g[-1]['odul']:+.3f}, "
          f"seviye {g[-1]['seviye']}, {g[-1]['sure']:.0f} s")
    print(f"kayit: {s['yol']}.pt")
