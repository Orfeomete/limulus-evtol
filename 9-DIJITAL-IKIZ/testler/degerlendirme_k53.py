#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# KARAR 53 DEGERLENDIRMESI — veri denetimi (karar 30) + ulasilan gorev adi
# (kural 1) + seviye 2 deterministik degerlendirme (kural 2 tamamlama) +
# mekanizma denetimi (kural 5). Yontem ve tohum duzeni karar 52 ile ayni.
import os, sys, json, math
os.environ["LIMULUS_CRUISE_ITKI"] = "1"   # kampanya bu bayrakla kosuldu
# F1 ve F2 KAPALI (ontanim), karar 53 kurgusu
_B = os.path.dirname(os.path.abspath(__file__))
for _y in ("../dinamik", "../ogrenme"):
    sys.path.insert(0, os.path.normpath(os.path.join(_B, _y)))
import numpy as np, torch
from egitim_v2 import KosanNorm, Politika2
from ortam import MUFREDAT, LimulusOrtami

VARYANTLAR = ("limulus", "ikili", "senkron", "liftcruise")
DIZIN = os.path.join(_B, "..", "ogrenme", "kosular_genis_kesif")
DT, SEV, ESIK = 0.02, 2, 0.65
N_AZ = int(MUFREDAT[SEV].sure / DT)

def denetim_k30(kok):
    j = json.load(open(kok + "_gunluk.json")); g = j["gunluk"]; a = j["ayar"]
    adim = [x["adim"] for x in g]
    ok = (g[-1]["adim"] >= 3_000_000 and all(b > c for b, c in zip(adim[1:], adim))
          and abs(a["log_std0"] + 0.5) < 1e-9 and a["gamma"] == 0.99
          and a.get("irtifa_taban") is False and a.get("cruise_itki") is True
          and a.get("ortam_v0") is False and a.get("mufredat_ince") is False)
    en_yuksek = max(x["seviye"] for x in g)
    gorev = MUFREDAT[en_yuksek].ad
    sev2 = next((x["adim"] for x in g if x["seviye"] >= 2), None)
    return ok, len(g), en_yuksek, gorev, sev2, (3_000_320 - sev2 if sev2 else 0), g[-1]["sure"]

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
        norm.ort = np.array(j["gozlem_norm"]["ort"]); norm.var = np.array(j["gozlem_norm"]["var"])
        norm.sayac = j["gozlem_norm"]["sayac"]; norm.acik = False
    bl = []
    for b in range(3):
        ham, _ = o.reset(seed=int(1000 * tohum + b))
        gz = norm(ham) if norm else ham
        toplam, adim, bilgi, h_az, tilt_az = 0.0, 0, {}, -1e9, 0.0
        while True:
            e, _, _ = pol.eylem(gz, ornekle=False)
            ham, r, bitti, kesildi, bilgi = o.step(np.clip(e, -1.0, 1.0))
            gz = norm(ham) if norm else ham
            toplam += r; adim += 1
            h_az = max(h_az, -o.ac.durum[11])
            if o.n_tilt:
                th_ank = np.array([o.tilt_ank[grp[0]] for grp in o.ac.var.tilt_gruplari])
                tilt = np.array([a2.theta for a2 in o.ac.tilt])[:o.n_tilt]
                tilt_az = max(tilt_az, float(np.max(np.abs(tilt - th_ank[:o.n_tilt]))))
            if bitti or kesildi: break
        d = o.ac.durum
        if -d[11] <= 0.0: ned = "yere carpma"
        elif abs(d[6]) > math.radians(85) or abs(d[7]) > math.radians(85): ned = "tutum"
        elif bilgi.get("enerji_orani", 0.0) > 1.0: ned = "enerji"
        else: ned = "sure doldu"
        bl.append(dict(odul=toplam / N_AZ, pay=adim / N_AZ, h_azami=h_az,
                       tilt_der=math.degrees(tilt_az), neden=ned))
    return bl

SONUC = {}
print("=" * 96)
print("KARAR 53 — kosular_genis_kesif, log_std0 = -0,5, 20 x 3M")
print("=" * 96)
for v in VARYANTLAR:
    SONUC[v] = []
    for t in range(5):
        kok = os.path.join(DIZIN, f"{v}_t{t}")
        ok, nk, sev, gorev, sev2, sev2eg, sure = denetim_k30(kok)
        bl = degerlendir(kok, v, t)
        pay = float(np.mean([b["pay"] for b in bl])); od = float(np.mean([b["odul"] for b in bl]))
        kapi = od >= ESIK
        SONUC[v].append(dict(tohum=t, k30=ok, kayit=nk, en_yuksek_seviye=sev, gorev=gorev,
                             sev2_adim=sev2, sev2_egitim=sev2eg, sure_sa=sure/3600,
                             pay=pay, odul=od, kapi=kapi,
                             h_azami=float(max(b["h_azami"] for b in bl)),
                             tilt_der=float(max(b["tilt_der"] for b in bl)),
                             nedenler=[b["neden"] for b in bl]))
        print(f"{v:<11} t{t} k30={'OK' if ok else 'HATA'} gorev={gorev:<11} sev2@{sev2 or 0:>9,} "
              f"pay={pay*100:5.1f}% odul={od:+.3f} {'KAPI GECTI' if kapi else '          '} "
              f"h_az={max(b['h_azami'] for b in bl):6.1f} tilt={max(b['tilt_der'] for b in bl):4.1f}d "
              f"{sorted(set(b['neden'] for b in bl))}")
    p = [s["pay"] for s in SONUC[v]]; o_ = [s["odul"] for s in SONUC[v]]
    print(f"  {v}: pay {np.mean(p)*100:.1f}% ± {np.std(p, ddof=1)*100:.1f} · "
          f"odul {np.mean(o_):+.3f} ± {np.std(o_, ddof=1):.3f}")
    print("-" * 96)
json.dump(SONUC, open(os.path.join(_B, "..", "ogrenme", "k53_degerlendirme.json"), "w"), indent=1)
print("kayit: ogrenme/k53_degerlendirme.json")
