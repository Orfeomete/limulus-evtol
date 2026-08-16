#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARAR 54 DEGERLENDIRMESI — SONUCLAR GORULMEDEN YAZILDI (15.08.2026).

Bu betik karar 54'un on kaydindaki on kuralin dogrudan gerceklemesidir ve
kampanya BITMEDEN once yazilmistir. Amaci, sonuc gorulduxkten sonra analiz
tasarlama olasiligini ortadan kaldirmaktir.

Kullanim, uc adim:
    LIMULUS_MUFREDAT_INCE=1 python3 degerlendirme_k54.py --kol ince
                            python3 degerlendirme_k54.py --kol taban
                            python3 degerlendirme_k54.py --karsilastir

⛔ ONEMLI. MUFREDAT ortam degiskeniyle ICE AKTARIM ANINDA secilir, bu yuzden
iki kol AYNI surecte degerlendirilemez. Betik bu yuzden kol kol calisir.

⛔ Seviye indisi iki kolda AYNI gorevi gostermez. Taban mufredatta `gecis`
indeks 2'dedir, ince mufredatta indeks 3'tedir. Bu betik hicbir yerde indis
karsilastirmaz, GOREV ADI kullanir (kural 1 ve kural 4).
"""
import os, sys, json, argparse

_B = os.path.dirname(os.path.abspath(__file__))
CIKTI = os.path.join(_B, "k54_%s.json")

DIZINLER = {
    "ince":  os.path.join(_B, "..", "ogrenme", "kosular_ince_mufredat"),
    "taban": os.path.join(_B, "..", "ogrenme", "kosular_genis_kesif"),
}
VARYANT = "limulus"          # kural 3, onayla daraltildi
TOHUMLAR = (0, 1, 2, 3, 4)
ESIK = 0.65                  # kural 2, dondurulmus
DT = 0.02
ORTAK_GOREV = "gecis"        # kural 4, karsilastirma yalniz bunun uzerinden


# ---------------------------------------------------------------- kol analizi
def kol_analizi(kol: str) -> dict:
    beklenen_ince = (kol == "ince")
    os.environ["LIMULUS_CRUISE_ITKI"] = "1"
    for _y in ("../dinamik", "../ogrenme"):
        sys.path.insert(0, os.path.normpath(os.path.join(_B, _y)))
    import numpy as np, torch
    from egitim_v2 import KosanNorm, Politika2
    from ortam import MUFREDAT, LimulusOrtami

    adlar = [g.ad for g in MUFREDAT]
    # ⛔ kolun dogru mufredatla acildiginin denetimi, kural 10
    if beklenen_ince and "gecis_yarim" not in adlar:
        raise SystemExit("HATA. ince kol icin LIMULUS_MUFREDAT_INCE=1 verilmeli")
    if (not beklenen_ince) and "gecis_yarim" in adlar:
        raise SystemExit("HATA. taban kol icin LIMULUS_MUFREDAT_INCE ayarlanmamali")

    SEV = adlar.index(ORTAK_GOREV)       # taban 2, ince 3
    AYRIM = 2                            # kollarin ayristigi ilk indis, kural 5
    N_AZ = int(MUFREDAT[SEV].sure / DT)
    dizin = DIZINLER[kol]

    sonuc = {"kol": kol, "gorevler": adlar, "gecis_indisi": SEV, "kosular": []}

    for t in TOHUMLAR:
        kok = os.path.join(dizin, f"{VARYANT}_t{t}")
        if not os.path.exists(kok + "_gunluk.json"):
            sonuc["kosular"].append({"tohum": t, "durum": "EKSIK"})
            continue
        j = json.load(open(kok + "_gunluk.json", encoding="utf-8"))
        g, a = j["gunluk"], j["ayar"]

        # --- kural 10, veri denetimi (karar 30) ---
        adim = [x["adim"] for x in g]
        denetim = {
            "adim_artan": all(b > c for b, c in zip(adim[1:], adim)),
            "butce_tam": g[-1]["adim"] >= 3_000_000,
            "log_std0": abs(a["log_std0"] + 0.5) < 1e-9,
            "gamma": a["gamma"] == 0.99,
            "cruise_itki": a.get("cruise_itki") is True,
            "irtifa_taban": a.get("irtifa_taban") is False,
            "ortam_v0": a.get("ortam_v0") is False,
            "mufredat_ince": a.get("mufredat_ince") is beklenen_ince,
        }

        # --- kural 1, birincil metrik GOREV ADIDIR ---
        en_yuksek = max(x["seviye"] for x in g)
        ulasilan = adlar[en_yuksek] if en_yuksek < len(adlar) else f"?{en_yuksek}"
        gecise_ulasti = en_yuksek >= SEV

        # --- kural 5, dejenerasyon denetimi ---
        # Kollarin ayristigi indise ulasilmadiysa mufredat carpani ATILDIR.
        ayrima_ulasti = en_yuksek >= AYRIM
        carpan_durumu = "sinandi" if ayrima_ulasti else "SINANMADI"

        # --- kural 6, mekanizma, egitim gunlugunden ---
        seviye_adim = {}
        onceki = 0
        for x in g:
            ad = adlar[x["seviye"]] if x["seviye"] < len(adlar) else "?"
            seviye_adim[ad] = seviye_adim.get(ad, 0) + (x["adim"] - onceki)
            onceki = x["adim"]
        gecise_varis_adimi = next((x["adim"] for x in g if x["seviye"] >= SEV), None)

        sonuc["kosular"].append({
            "tohum": t, "durum": "TAM",
            "denetim": denetim, "denetim_gecti": all(denetim.values()),
            "ulasilan_gorev": ulasilan, "gecise_ulasti": gecise_ulasti,
            "ayrima_ulasti": ayrima_ulasti, "mufredat_carpani": carpan_durumu,
            "gecise_varis_adimi": gecise_varis_adimi,
            "seviye_basina_adim": seviye_adim,
            "duvar_saati_s": g[-1]["sure"],
            "son_odul": g[-1]["odul"],
        })

    # --- kural 2, TAMAMLAMA, deterministik degerlendirme ---
    for k in sonuc["kosular"]:
        if k["durum"] != "TAM" or not k["gecise_ulasti"]:
            k["tamamladi"] = False
            k["tamamlama_notu"] = "gecis gorevine ulasmadi, degerlendirilmedi"
            continue
        t = k["tohum"]
        kok = os.path.join(dizin, f"{VARYANT}_t{t}")
        j = json.load(open(kok + "_gunluk.json", encoding="utf-8"))
        o = LimulusOrtami(varyant=VARYANT, seviye=SEV, tohum=t, sensor=True)
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
        bolumler = []
        for b in range(3):
            ham, _ = o.reset(seed=int(1000 * t + b))
            gz = norm(ham) if norm else ham
            toplam, n, h_az, tilt_az = 0.0, 0, -1e9, 0.0
            while True:
                e, _, _ = pol.eylem(gz, ornekle=False)
                ham, r, bitti, kesildi, _ = o.step(np.clip(e, -1.0, 1.0))
                gz = norm(ham) if norm else ham
                toplam += r; n += 1
                h_az = max(h_az, -o.ac.durum[11])
                if o.n_tilt:
                    th = np.array([o.tilt_ank[grp[0]] for grp in o.ac.var.tilt_gruplari])
                    tl = np.array([x.theta for x in o.ac.tilt])[:o.n_tilt]
                    tilt_az = max(tilt_az, float(np.max(np.abs(tl - th[:o.n_tilt]))))
                if bitti or kesildi: break
            bolumler.append({"odul_ort": toplam / max(n, 1), "adim": n,
                             "sure_doldu": n >= N_AZ,
                             "h_azami": h_az, "tilt_azami_derece": tilt_az * 180.0 / 3.141592653589793})
        # kural 2, tamamlama olcutu, sure doldu VE 0,65 kapisi
        k["degerlendirme"] = bolumler
        k["tamamladi"] = all(b["sure_doldu"] and b["odul_ort"] >= ESIK for b in bolumler)
        k["tamamlama_notu"] = f"3 bolumun {sum(1 for b in bolumler if b['sure_doldu'] and b['odul_ort']>=ESIK)}'u gecti"

    json.dump(sonuc, open(CIKTI % kol, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"yazildi  {CIKTI % kol}")
    for k in sonuc["kosular"]:
        if k["durum"] != "TAM":
            print(f"  t{k['tohum']}  EKSIK"); continue
        print(f"  t{k['tohum']}  gorev {k['ulasilan_gorev']:<12} "
              f"carpan {k['mufredat_carpani']:<10} tamamladi {k['tamamladi']} "
              f"denetim {'OK' if k['denetim_gecti'] else 'DUSTU'}")
    return sonuc


# ------------------------------------------------------------ karsilastirma
def karsilastir():
    """Kural 3, karar 12. Kural 4, yalniz ortak gorev uzerinden."""
    import statistics as st
    veri = {}
    for kol in ("ince", "taban"):
        p = CIKTI % kol
        if not os.path.exists(p):
            raise SystemExit(f"once {kol} kolu degerlendirilmeli, {p} yok")
        veri[kol] = json.load(open(p, encoding="utf-8"))

    print("=" * 74)
    print("KARAR 54 KARSILASTIRMASI — limulus, 5 tohum karsisinda 5 tohum")
    print("=" * 74)

    rapor = {"kural_4_notu":
             "Karsilastirma yalniz ortak gorev 'gecis' uzerinden yapildi. "
             "Seviye indisi karsilastirilmadi. Esit butcede ince kol yapi geregi "
             "bir seviye geridedir ve bu bir bulgu sayilmamistir."}

    for kol in ("taban", "ince"):
        ks = [k for k in veri[kol]["kosular"] if k["durum"] == "TAM"]
        ulasan = [k for k in ks if k["gecise_ulasti"]]
        tamamlayan = [k for k in ks if k.get("tamamladi")]
        sinanmayan = [k for k in ks if k["mufredat_carpani"] == "SINANMADI"]
        rapor[kol] = {
            "kosu": len(ks),
            "gecise_ulasan": len(ulasan),
            "gecisi_tamamlayan": len(tamamlayan),
            "carpan_sinanmayan": len(sinanmayan),
            "denetim_dusen": [k["tohum"] for k in ks if not k["denetim_gecti"]],
        }
        print(f"\n{kol.upper():6s}  gecis'e ulasan {len(ulasan)}/{len(ks)}   "
              f"gecis'i TAMAMLAYAN {len(tamamlayan)}/{len(ks)}")
        if sinanmayan:
            print(f"        ⛔ {len(sinanmayan)} kosuda mufredat carpani ATIL, "
                  f"'basarisiz' degil 'SINANMADI' diye raporlanir (kural 5)")

    # karar 12, varis adimi uzerinden nicel karsilastirma
    for alan, ad in (("gecise_varis_adimi", "gecis gorevine varis adimi"),):
        a = [k[alan] for k in veri["taban"]["kosular"]
             if k["durum"] == "TAM" and k.get(alan)]
        b = [k[alan] for k in veri["ince"]["kosular"]
             if k["durum"] == "TAM" and k.get(alan)]
        if len(a) < 2 or len(b) < 2:
            print(f"\n{ad}: karsilastirilamaz, iki kolda da en az iki koşu gerekir")
            continue
        sa, sb = st.stdev(a), st.stdev(b)          # ddof=1, ORNEKLEM sapmasi
        oynak = "taban" if sa >= sb else "ince"
        esik = 2 * max(sa, sb)
        fark = abs(st.mean(a) - st.mean(b))
        hukum = "FARK YOK" if fark < esik else "FARK VAR"
        rapor[alan] = {"taban_ort": st.mean(a), "ince_ort": st.mean(b),
                       "taban_sd": sa, "ince_sd": sb, "daha_oynak": oynak,
                       "fark": fark, "esik": esik, "hukum": hukum}
        print(f"\n{ad}")
        print(f"  taban ort {st.mean(a):>12,.0f}  sd {sa:>12,.0f}")
        print(f"  ince  ort {st.mean(b):>12,.0f}  sd {sb:>12,.0f}")
        print(f"  fark {fark:,.0f}  esik {esik:,.0f} (daha oynak grup {oynak})")
        print(f"  ⇒ {hukum}   (karar 12)")

    # kural 7, dondurulmus cumle
    if rapor["ince"]["gecisi_tamamlayan"] == 0:
        print("\n" + "⛔ " * 24)
        print("KURAL 7 YURURLUKTE. Dondurulmus cumle karar 54'ten aynen alinir:")
        print("  Mufredat basamak buyuklugu de gecis gorevinin ogrenilememesinin")
        print("  nedeni degildir. Ogrenilemezligin nedeni olarak sinanan alti adayin")
        print("  altisi elenmis, dolayisiyla neden bu calismanin olctugu eksenlerin")
        print("  disinda kalmistir ve tez bunu acik kalem olarak birakmaktadir.")
        rapor["kural_7"] = "YURURLUKTE"
    else:
        rapor["kural_7"] = "yururlukte degil, en az bir tohum gecisi tamamladi"

    json.dump(rapor, open(os.path.join(_B, "k54_karsilastirma.json"), "w",
                          encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nyazildi  {os.path.join(_B, 'k54_karsilastirma.json')}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--kol", choices=("ince", "taban"))
    p.add_argument("--karsilastir", action="store_true")
    ar = p.parse_args()
    if ar.karsilastir:
        karsilastir()
    elif ar.kol:
        kol_analizi(ar.kol)
    else:
        p.error("--kol ya da --karsilastir verilmeli")
