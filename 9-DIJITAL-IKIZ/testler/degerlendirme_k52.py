#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# KARAR 52 DEGERLENDIRMESI — veri denetimi (karar 30) + seviye 2
# deterministik degerlendirme (3 bolum/politika, dogrulama_mufredat_esigi
# ile ayni yontem ve tohumlar) + mekanizma denetimi (kural A4).
import os, sys, json, math, glob
os.environ["LIMULUS_CRUISE_ITKI"] = "1"
os.environ["LIMULUS_IRTIFA_TABAN"] = "1"   # iki sonda da F1 acik egitildi
_B = os.path.dirname(os.path.abspath(__file__))
for _y in ("../dinamik", "../ogrenme"):
    sys.path.insert(0, os.path.normpath(os.path.join(_B, _y)))
import numpy as np, torch
from egitim_v2 import KosanNorm, Politika2
from ortam import MUFREDAT, LimulusOrtami

VARYANTLAR = ("limulus", "ikili", "senkron", "liftcruise")
DT = 0.02
SEV = 2
N_AZ = int(MUFREDAT[SEV].sure / DT)

def denetim_k30(kok, beklenen_gamma):
    j = json.load(open(kok + "_gunluk.json"))
    g = j["gunluk"]; a = j["ayar"]
    adimlar = [x["adim"] for x in g]
    tamam = (g[-1]["adim"] >= 600000 and all(b > c for b, c in zip(adimlar[1:], adimlar))
             and len(g) == 293
             and a.get("irtifa_taban") is True and a.get("cruise_itki") is True
             and abs(a["gamma"] - beklenen_gamma) < 1e-9 and a.get("ortam_v0") is False)
    sev2 = next((x["adim"] for x in g if x["seviye"] >= 2), None)
    sev2_egitim = (600064 - sev2) if sev2 else 0
    return tamam, len(g), sev2, sev2_egitim, a["gamma"]

def degerlendir(kok, varyant, tohum):
    j = json.load(open(kok + "_gunluk.json"))
    o = LimulusOrtami(varyant=varyant, seviye=SEV, tohum=tohum, sensor=True)
    o.seviye = SEV; o.gorev = MUFREDAT[SEV]
    pol = Politika2(o.observation_space.shape[0], o.n_eylem,
                    j["ayar"]["gizli"], j["ayar"]["log_std0"], None)
    pol.load_state_dict(torch.load(kok + ".pt", map_location="cpu")); pol.eval()
    norm = None
    if j.get("gozlem_norm"):
        norm = KosanNorm(o.observation_space.shape[0])
        norm.ort = np.array(j["gozlem_norm"]["ort"])
        norm.var = np.array(j["gozlem_norm"]["var"])
        norm.sayac = j["gozlem_norm"]["sayac"]; norm.acik = False
    boluml = []
    for b in range(3):
        ham, _ = o.reset(seed=int(1000 * tohum + b))
        gz = norm(ham) if norm else ham
        toplam, adim, bilgi = 0.0, 0, {}
        h_azami, tilt_azami = -1e9, 0.0
        while True:
            e, _, _ = pol.eylem(gz, ornekle=False)
            ham, r, bitti, kesildi, bilgi = o.step(np.clip(e, -1.0, 1.0))
            gz = norm(ham) if norm else ham
            toplam += r; adim += 1
            h_azami = max(h_azami, -o.ac.durum[11])
            th_ank = np.array([o.tilt_ank[grp[0]] for grp in o.ac.var.tilt_gruplari]) if o.n_tilt else np.zeros(1)
            tilt = np.array([a2.theta for a2 in o.ac.tilt])
            if o.n_tilt:
                tilt_azami = max(tilt_azami, float(np.max(np.abs(tilt[:o.n_tilt] - th_ank[:o.n_tilt] if len(th_ank)>=o.n_tilt else tilt[:o.n_tilt]))))
            if bitti or kesildi:
                break
        d = o.ac.durum
        if -d[11] <= 0.0: ned = "yere carpma"
        elif abs(d[6]) > math.radians(85) or abs(d[7]) > math.radians(85): ned = "tutum"
        elif bilgi.get("enerji_orani", 0.0) > 1.0: ned = "enerji"
        else: ned = "sure doldu"
        boluml.append(dict(odul=toplam / N_AZ, pay=adim / N_AZ, adim=adim,
                           h_azami=h_azami, tilt_der=math.degrees(tilt_azami), neden=ned))
    return boluml

SONUC = {}
for dizin, gamma in (("kosular_esik_sonda600_s5", 0.99),
                     ("kosular_esik_gamma999_s5", 0.999)):
    yol = os.path.join(_B, "..", "ogrenme", dizin)
    SONUC[dizin] = {}
    print("=" * 88); print(dizin); print("=" * 88)
    for v in VARYANTLAR:
        satirlar = []
        for t in range(5):
            kok = os.path.join(yol, f"{v}_t{t}")
            ok, nk, sev2, sev2_eg, gm = denetim_k30(kok, gamma)
            bl = degerlendir(kok, v, t)
            pay = np.mean([b["pay"] for b in bl]); od = np.mean([b["odul"] for b in bl])
            satirlar.append(dict(tohum=t, k30=ok, sev2_egitim=sev2_eg,
                                 dagilim_disi=sev2_eg < 200000,
                                 pay=float(pay), odul=float(od),
                                 h_azami=float(max(b["h_azami"] for b in bl)),
                                 tilt_der=float(max(b["tilt_der"] for b in bl)),
                                 nedenler=[b["neden"] for b in bl]))
            print(f"{v:<11} t{t} k30={'OK' if ok else 'HATA'} sev2eg={sev2_eg:>7,} "
                  f"{'DAGILIM_DISI' if sev2_eg<200000 else '            '} "
                  f"pay={pay*100:5.1f}% odul={od:+.3f} h_az={max(b['h_azami'] for b in bl):6.1f} "
                  f"tilt={max(b['tilt_der'] for b in bl):4.1f}d {set(b['neden'] for b in bl)}")
        gecerli = [s for s in satirlar if not s["dagilim_disi"]]
        if gecerli:
            p = [s["pay"] for s in gecerli]; o_ = [s["odul"] for s in gecerli]
            print(f"  {v}: n={len(gecerli)} pay ort {np.mean(p)*100:.1f}% sd {np.std(p, ddof=1)*100 if len(p)>1 else 0:.1f}% · "
                  f"odul ort {np.mean(o_):+.3f} sd {np.std(o_, ddof=1) if len(o_)>1 else 0:.3f}")
        SONUC[dizin][v] = satirlar
        print("-" * 88)
json.dump(SONUC, open(os.path.join(_B, "..", "ogrenme", "k52_degerlendirme.json"), "w"), indent=1)
print("kayit: ogrenme/k52_degerlendirme.json")
