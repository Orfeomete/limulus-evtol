#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARSILASTIRMA METRIKLERI — alti eksenin sayisallastirilmasi

4-KARARLAR/09 §4 alti ekseni TANIMLADI ama olculebilir hale
getirmedi. Bu dosya o boslugu kapatir. Her metrik icin
    ne olculuyor · nasil hesaplaniyor · hangi yonde iyi
acikca yazilir.

⚠️ Politikadan bagimsiz metrik sayisi BESTIR (09.08.2026, karar 43).
Trim zarfi, gecis koridoru, ariza toleransi, enerji ve asimetrik ariza
trimi dogrudan fizikten olculur ve pekistirmeli ogrenme gerektirmez.
Yalniz bozucu reddi ve ogrenme verimi egitilmis politika ister. Bu
ayrim onemlidir: bes metrik egitim yapilmadan da rapor edilebilir.

⚠️ Ilk dort metrik SIMETRIK ucus varsayimiyla calisir, ucuncu ve
altinci denklemi (yanal kuvvet, yatis ve sapma momenti) hic kurmaz.
Besinci metrik o varsayimi kaldirir ve `trim_yanal` uzerinden alti
denklemin tamamini cozer. Iki metrik ailesi bu yuzden ayni tabanda
DEGILDIR ve tabloda ayni sutunda karsilastirilirken bu yazilir.
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

import atmosfer as atm                                   # noqa: E402
from arac import Limulus                                 # noqa: E402
from trim import (_sonraki_baslangic, trim, trim_yanal,  # noqa: E402
                  trim_zarfi, zarf_hacmi)


# =====================================================================
# 1. TRIM ZARFI
# =====================================================================
def _arac(varyant: str) -> Limulus:
    """⚠️ B4 BAYRAGI TEK YERDEN OKUNUR (karar 22, 32).

    LIMULUS_CRUISE_ITKI=1 verildiginde lift+cruise varyanti ayri cruise
    itici birimiyle kurulur. Bayrak dort metrigin DORDUNDE de ayni
    sekilde okunmalidir, yoksa bir metrik yeni fizikle digeri eski
    fizikle hesaplanir ve tablo kendi icinde tutarsiz olur.
    """
    _b = os.environ.get("LIMULUS_CRUISE_ITKI", "0") == "1"
    return Limulus(varyant_ad=varyant, cruise_itki_etkin=_b)


def metrik_trim_zarfi(varyant: str, hizlar=None, gamalar=None) -> dict:
    """Erisilebilir denge durumlarinin hacmi. Buyuk iyi.

    Birim: m/s x derece. Bagimsiz tiltin DOGRUDAN iddiasi budur —
    daha genis bir trim zarfi.
    """
    hizlar = np.arange(0.0, 75.0, 7.5) if hizlar is None else hizlar
    gamalar = np.radians(np.arange(-9.0, 9.1, 4.5)) if gamalar is None else gamalar
    ac = _arac(varyant)
    Z = trim_zarfi(ac, hizlar, gamalar)
    return dict(metrik="trim_zarfi", varyant=varyant,
                deger=zarf_hacmi(Z, hizlar, gamalar),
                birim="m/s x derece", yon="buyuk iyi",
                izgara=Z.tolist(), n_cozum=int(Z.sum()), n_nokta=int(Z.size))


# =====================================================================
# 2. GECIS KORIDORU
# =====================================================================
def metrik_gecis_koridoru(varyant: str, hizlar=None,
                          tilt_izgara=None) -> dict:
    """Her hizda trim edilebilir tilt araliginin genisligi. Buyuk iyi.

    Koridor daralirsa gecis kirilgan olur. Genis koridor, kontrolcuye
    hata payi birakir.
    """
    hizlar = np.arange(10.0, 70.1, 10.0) if hizlar is None else hizlar
    # ⚠️ IZGARA 2,5 DERECE, 7,5 DEGIL. Bkz. 4-KARARLAR/23.
    # Kaba izgarada LIMULUS'un koridoru bir adim FAZLA, senkronunki bir
    # adim EKSIK olculuyordu ve kazanim %20,7 cikiyordu. Ince izgarada
    # gercek deger %15,9. Ontanimi degistirmenin nedeni, tez metni ile
    # figurun ayni sayidan uretilmesini garanti etmektir.
    tilt_izgara = np.radians(np.arange(0.0, 90.1, 2.5)) \
        if tilt_izgara is None else tilt_izgara
    ac = _arac(varyant)
    hava = atm.isa(0.0)
    genislikler, harita = [], []
    for V in hizlar:
        satir = []
        for th in tilt_izgara:
            satir.append(_ortalama_tilt_trim_var_mi(ac, V, th, hava))
        harita.append(satir)
        n = sum(satir)
        genislikler.append(n * float(np.degrees(np.mean(np.diff(tilt_izgara)))))
    return dict(metrik="gecis_koridoru", varyant=varyant,
                deger=float(np.mean(genislikler)),
                birim="derece (hizlar boyunca ortalama)", yon="buyuk iyi",
                hizlar=[float(v) for v in hizlar],
                genislikler=[float(g) for g in genislikler],
                harita=harita)


def _ortalama_tilt_trim_var_mi(ac: Limulus, V: float, tilt_ort: float,
                               hava, sapma_azami: float = math.radians(20.0)
                               ) -> bool:
    """ORTALAMA tilt verildiginde varyant trim kurabiliyor mu.

    ⚠️ Kritik tasarim karari. Ilk surumde tilt DORT PODA DA ayni deger
    olarak dayatiliyordu. Bu, tam olarak karsilastirilan serbestligi
    yok ediyordu ve dort varyant birebir ayni sonucu veriyordu.
    Dogrusu, ortalama tilt kisitlanip varyantin kendi serbestlik
    derecesinin bu ortalama etrafinda sapmasina izin vermektir.

        LIMULUS   on ve arka cift bagimsiz sapabilir
        Ikili     ayni (iki eksen)
        Senkron   sapma YOK, dort pod ortalamada kilitli
        Lift+cr.  tilt yok, yalniz tilt_ort = 0'da cozum olabilir
    """
    from scipy.optimize import minimize
    a_max = ac.kanat.alfa_icin_CL(ac.kanat.CL_max / 1.21)
    T_tav = ac.rotor.itki_limiti(ac.itki[0].guc_tavani("surekli"),
                                 hava.rho, V, math.pi / 2)
    var = ac.var

    if var.sabit_tilt is not None:
        if abs(tilt_ort - var.sabit_tilt) > 1e-6:
            return False
        n_sap = 0
    elif var.n_tilt <= 1:
        n_sap = 0                       # senkron, sapma yok
    else:
        n_sap = 1                       # on/arka ortak sapma tek parametre

    # ⚠️ AYRI CRUISE ITICI BIRIMI (B4, karar 32). Bayrak acikken
    # lift+cruise'un bir tasarim degiskeni daha olur. Bu eklenmezse
    # koridor metrigi bayragi GORMEZ ve "guncellendi" denen sayi eski
    # fizikten gelmis olur.
    n_ct = 1 if (ac.cruise_itki_etkin and var.ayri_cruise_itki) else 0
    Tc_tav = (ac.k["CRUISE_ITKI_P"] * ac.k["CRUISE_ITKI_ETA"]
              / max(V, 5.0)) if n_ct else 0.0

    def kur(x):
        alfa, T1, T2 = x[0], x[1], x[2]
        if n_sap:
            d_t = x[3]
            tilt = np.array([tilt_ort + d_t, tilt_ort + d_t,
                             tilt_ort - d_t, tilt_ort - d_t])
            tilt = np.clip(tilt, ac.k["THETA_MIN"], ac.k["THETA_MAX"])
        else:
            tilt = np.full(4, tilt_ort)
        d = np.zeros(12)
        d[0] = V * math.cos(alfa); d[2] = V * math.sin(alfa); d[7] = alfa
        Tc = float(x[3 + n_sap]) if n_ct else 0.0
        return d, np.array([T1, T1, T2, T2]), tilt, Tc

    def artik(x):
        d, T, tilt, Tc = kur(x)
        F, M, _ = ac.kuvvetler(d, T, tilt, hava, T_cruise=Tc)
        return (F[0] / 100) ** 2 + (F[2] / 100) ** 2 + (M[1] / 100) ** 2

    sinir = [(-a_max, a_max), (0, T_tav), (0, T_tav)]
    x0_taban = [0.0, ac.W / 8, ac.W / 8]
    if n_sap:
        sinir.append((-sapma_azami, sapma_azami))
        x0_taban.append(0.0)
    if n_ct:
        sinir.append((0.0, Tc_tav))
        x0_taban.append(0.5 * Tc_tav)

    en_iyi = 1e18
    tc_paylari = (0.0, 0.5, 1.0) if n_ct else (0.0,)
    for a0 in (0.0, 0.08, a_max * 0.9):
        for pay in tc_paylari:
            x0 = list(x0_taban); x0[0] = a0
            if n_ct:
                x0[3 + n_sap] = pay * Tc_tav
            r = minimize(artik, x0, method="L-BFGS-B", bounds=sinir,
                         options=dict(maxiter=400, ftol=1e-15))
            en_iyi = min(en_iyi, float(r.fun))
            if en_iyi < 1e-6:
                break
        if en_iyi < 1e-6:
            break
    return bool(en_iyi < 2.5e-3)


# =====================================================================
# 3. ARIZA TOLERANSI
# =====================================================================
def metrik_ariza_toleransi(varyant: str) -> dict:
    """Bir motor kaybinda saglanabilen kaldirma orani. Buyuk iyi.

    Bolum 9.8'in %90,7 sonucuyla ayni tabanda, ama tum pod
    kombinasyonlari ve varyant kisitlari altinda.
    """
    from scipy.optimize import linprog
    ac = _arac(varyant)
    hava = atm.isa(0.0)
    T_ariza = ac.rotor.itki_limiti(ac.k["P_MOTOR_SUREKLI"], hava.rho)
    T_tavan = ac.rotor.itki_limiti(ac.itki[0].guc_tavani("oei"), hava.rho)
    W_eff = ac.W * ac.k["DOWNLOAD"]

    kol_x = ac.pod[:, 0]
    kol_y = ac.pod[:, 1]
    oranlar = {}
    for idx in range(4):
        ust = np.full(4, T_tavan); alt_ = np.zeros(4)
        ust[idx] = alt_[idx] = T_ariza
        r = linprog(c=-np.ones(4), A_eq=np.vstack([kol_x, kol_y]),
                    b_eq=[0.0, 0.0], bounds=list(zip(alt_, ust)),
                    method="highs")
        oranlar[f"pod{idx + 1}"] = float(r.x.sum() / W_eff) if r.success else 0.0
    en_kotu = min(oranlar.values())
    return dict(metrik="ariza_toleransi", varyant=varyant,
                deger=en_kotu, birim="kaldirma orani (en kotu pod)",
                yon="buyuk iyi", podlar=oranlar,
                T_ariza=float(T_ariza), T_tavan=float(T_tavan))


# =====================================================================
# 4. ENERJI
# =====================================================================
def metrik_enerji(varyant: str, gorev=None) -> dict:
    """Referans gorev icin trim tabanli enerji. Kucuk iyi.

    Gorev profili tezin Bolum 2 misyonuyla ayni fazlari kullanir.
    """
    # Bolum 2 gorev profiliyle ayni taban: toplam 2 dk hover (Rev.D karari)
    gorev = gorev or [(0.0, 60.0), (20.0, 30.0), (40.0, 30.0),
                      (68.9, 900.0), (20.0, 30.0), (0.0, 60.0)]
    ac = _arac(varyant)
    E, ayrinti, onceki = 0.0, [], None
    eksik = []
    for V, sure in gorev:
        r = trim(ac, V, baslangic=onceki)
        if not r.basarili:
            ayrinti.append(dict(V=V, sure=sure, durum="trim yok"))
            eksik.append(V)
            continue
        # ⚠️ Baslangic vektoru trim.py'nin kendi yardimcisindan alinir.
        # Elle kurulan surum, cruise itki degiskeni eklenince (karar 32)
        # bir eleman EKSIK kaliyor ve metrik "index 4 out of bounds"
        # hatasiyla dusuyordu.
        onceki = _sonraki_baslangic(ac, r)
        E += r.P_batarya * sure
        ayrinti.append(dict(V=V, sure=sure, P=r.P_batarya / 1e3,
                            E=r.P_batarya * sure / 3.6e6))
    # ⚠️ Trim bulunamayan bacak varsa gorev TAMAMLANAMIYOR demektir.
    # Eksik bacaklari atlayip dusuk enerji raporlamak, gorevi ucamayan
    # varyanti en verimli gostermek olurdu. Ilk surumde lift+cruise
    # tam da bu sekilde 68,6 kWh ile birinci cikiyordu.
    if eksik:
        return dict(metrik="enerji", varyant=varyant, deger=float("nan"),
                    birim="kWh", yon="kucuk iyi", ayrinti=ayrinti,
                    gorev_tamamlanamadi=True, eksik_bacaklar=eksik,
                    batarya_kWh=ac.k["E_BATT"] / 3.6e6)
    return dict(metrik="enerji", varyant=varyant, deger=E / 3.6e6,
                birim="kWh", yon="kucuk iyi", ayrinti=ayrinti,
                gorev_tamamlanamadi=False,
                batarya_kWh=ac.k["E_BATT"] / 3.6e6,
                kullanim_orani=E / ac.k["E_BATT"])


# =====================================================================
# 5. BOZUCU REDDI  (politika gerektirir)
# =====================================================================
def metrik_bozucu_reddi(politika, varyant: str, tohumlar=range(8),
                        gust_siddeti="orta", sure=30.0) -> dict:
    """Gust altinda yorunge sapmasinin RMS'i. Kucuk iyi.

    ⚠️ DUZELTILDI 04.08.2026 — ilk surum ERKEN OLMEYI ODULLENDIRIYORDU.
    Ham RMS, bolum kisa bittiginde kucuk cikar cunku sapma birikmeye
    vakit bulamaz. Olcumde LIMULUS cruise gorevinde 153 adimda dusup
    11,5 aldi, ikili tilt 955 adim hayatta kalip 123,4 aldi — yani
    dusen konfigurasyon metrikte KAZANIYORDU. Ayrinti 4-KARARLAR/28.

    Duzeltme: RMS yalnizca gorevi TAMAMLAYAN bolumler uzerinden
    hesaplanir. Hayatta kalma orani ayri dondurulur ve dusuk bir RMS,
    hayatta kalma orani dusukse bir basari olarak okunmaz.
    """
    from ortam import Gorev, LimulusOrtami
    sapmalar, tamlar = [], []
    for t in tohumlar:
        g = Gorev("gust_cruise", sure, 68.9, 300.0, gust=gust_siddeti,
                  baslangic_V=68.9, baslangic_h=300.0)
        o = LimulusOrtami(varyant=varyant, gorev=g, tohum=int(t))
        gz, _ = o.reset(seed=int(t))
        h_hata, V_hata = [], []
        while True:
            e = politika(gz)
            gz, r, bitti, kesildi, bi = o.step(e)
            h_hata.append(bi["irtifa_hatasi"])
            V_hata.append(bi["hiz_hatasi"])
            if bitti or kesildi:
                break
        rms = math.sqrt(np.mean(np.square(h_hata))
                        + np.mean(np.square(V_hata)))
        tam = len(h_hata) >= int(sure / o.ac.dt) * 0.95
        sapmalar.append(rms)
        tamlar.append(tam)

    tam_sapma = [s for s, t in zip(sapmalar, tamlar) if t]
    hk = 100.0 * sum(tamlar) / max(len(tamlar), 1)
    if not tam_sapma:
        return dict(metrik="bozucu_reddi", varyant=varyant,
                    deger=None, birim="RMS yorunge sapmasi",
                    yon="kucuk iyi", std=None, n_tohum=len(sapmalar),
                    hayatta_kalma=hk, n_tam=0,
                    not_="hicbir bolum tamamlanmadi, metrik hesaplanamaz")
    return dict(metrik="bozucu_reddi", varyant=varyant,
                deger=float(np.mean(tam_sapma)),
                birim="RMS yorunge sapmasi (yalniz tamamlananlar)",
                yon="kucuk iyi", std=float(np.std(tam_sapma)),
                n_tohum=len(sapmalar), hayatta_kalma=hk,
                n_tam=len(tam_sapma))


# =====================================================================
# 6. OGRENME VERIMI  (egitim gunlugu gerektirir)
# =====================================================================
def metrik_ogrenme_verimi(gunluk: list[dict], esik_odul: float) -> dict:
    """Esik odule ulasmak icin gereken ornek sayisi. Kucuk iyi.

    ⚠️ 4-KARARLAR/09 §4 bu eksenin TERS yonde cikabilecegini
    yaziyor. Daha fazla kontrol serbestligi daha zengin bir kontrol
    uzayi ama ayni zamanda daha zor bir kesif problemi demektir.
    Bulgu o yonde cikarsa gizlenmez, mimarinin maliyeti olarak yazilir.
    """
    for kayit in gunluk:
        if kayit["odul"] >= esik_odul:
            return dict(metrik="ogrenme_verimi", deger=float(kayit["adim"]),
                        birim="cevre adimi", yon="kucuk iyi", ulasti=True,
                        esik=esik_odul)
    son = gunluk[-1] if gunluk else dict(adim=0, odul=float("-inf"))
    return dict(metrik="ogrenme_verimi", deger=float("inf"),
                birim="cevre adimi", yon="kucuk iyi", ulasti=False,
                esik=esik_odul, ulasilan_odul=son["odul"])


# =====================================================================
# 5. ASIMETRIK ARIZA TRIMI  (karar 43, 09.08.2026)
# =====================================================================
# ⚠️ IZGARA DONDURULMUSTUR. Asagidaki iki sabit karar 43'un on kaydinda
# olculmeden once yazildi ve tezin Tablo 16.5'i bu izgarayla uretildi.
# Metrik izgaraya DUYARLIDIR — ayni olcum uc hiz ve iki pod ile %67/%0,
# yirmi yedi hiz ve dort pod ile %31/%33/%12/%0 vermektedir. Ikisi
# celismiyor, kaba izgaranin uc hizi senkronun kapattigi noktalarin
# hicbirine denk gelmemis. Izgara degistirilirse tezdeki sayilar da
# degisir, once karar 43'u okuyun.
ASIM_HIZLAR = tuple(5.0 + 2.5 * i for i in range(27))    # 5 ... 70 m/s
ASIM_PODLAR = (0, 1, 2, 3)


def metrik_asimetrik_trim(varyant: str, hizlar=None, podlar=None,
                          beta_serbest: bool = False) -> dict:
    """Tek pod arizasinda yan kaymasiz duz ucus trimi. Buyuk iyi.

    Ilk dort metrikten farkli olarak alti denklemin tamamini cozer
    (F_x = F_y = F_z = 0, M_x = M_y = M_z = 0). Yan kayma hem suruklemeyi
    hem yanal yapisal yuku artirdigi icin beta = 0 zorunlu tutulur,
    `beta_serbest=True` ile cozucuye birakilabilir fakat tezin raporladigi
    sayi zorunlu haldir.

    Deger, denenen durumlarin kacinda trim kapandiginin oranidir. Ayrica
    ilk kapanan hiz ve azami tilt yayilimi dondurulur — ikincisi cozucunun
    fazladan serbestlik derecelerini gercekten kullanip kullanmadigini
    gosterir ve karar 21'in "hic kullanmiyor" tespitinin bir izgara kusuru
    oldugunu bu alan ortaya cikardi.
    """
    ac = _arac(varyant)
    hizlar = tuple(ASIM_HIZLAR if hizlar is None else hizlar)
    podlar = tuple(ASIM_PODLAR if podlar is None else podlar)

    kapanan, ilk_V, yayilim, paylar = 0, None, 0.0, []
    n = 0
    for pod in podlar:
        for V in hizlar:
            n += 1
            r = trim_yanal(ac, V, ariza=pod,
                           beta_hedef=None if beta_serbest else 0.0)
            if not r.basarili:
                continue
            kapanan += 1
            ilk_V = V if ilk_V is None else min(ilk_V, V)
            if r.tilt is not None and len(r.tilt):
                t = np.degrees(np.asarray(r.tilt, float))
                yayilim = max(yayilim, float(t.max() - t.min()))
            tav = ac.rotor.itki_limiti(ac.itki[0].guc_tavani("surekli"),
                                       atm.isa(0.0).rho, V, math.pi / 2)
            if tav > 0:
                paylar.append(1.0 - float(np.max(r.T)) / tav)

    return dict(metrik="asimetrik_trim", varyant=varyant,
                deger=kapanan / n if n else float("nan"),
                birim="kapanan durum orani", yon="buyuk iyi",
                kapanan=kapanan, denenen=n,
                ilk_kapanan_V=ilk_V,
                azami_tilt_yayilimi_derece=yayilim,
                ortalama_kontrol_payi=(sum(paylar) / len(paylar)
                                       if paylar else float("nan")),
                beta_serbest=beta_serbest,
                izgara=f"{len(hizlar)} hiz x {len(podlar)} pod")


# =====================================================================
POLITIKASIZ = (metrik_trim_zarfi, metrik_gecis_koridoru,
               metrik_ariza_toleransi, metrik_enerji,
               metrik_asimetrik_trim)


def politikasiz_tumu(varyantlar=("limulus", "ikili", "senkron", "liftcruise")
                     ) -> dict:
    """Egitim gerektirmeyen BES metrigi tum varyantlar icin hesaplar.

    ⚠️ Besinci metrik varyant basina 108 trim cozumu istiyor, yani bu
    fonksiyon artik saniyeler degil dakikalar suruyor.
    """
    out = {}
    for v in varyantlar:
        out[v] = {}
        for f in POLITIKASIZ:
            try:
                r = f(v)
                out[v][r["metrik"]] = r
            except Exception as e:                       # pragma: no cover
                out[v][f.__name__] = dict(hata=str(e))
    return out


if __name__ == "__main__":
    import json
    import time

    t0 = time.time()
    print("POLITIKADAN BAGIMSIZ METRIKLER")
    print("Egitim gerektirmez, dogrudan fizikten olculur.\n")
    sonuc = politikasiz_tumu()

    basliklar = ["trim_zarfi", "gecis_koridoru", "ariza_toleransi", "enerji",
                 "asimetrik_trim"]
    print(f"{'varyant':<17}" + "".join(f"{b:>19}" for b in basliklar))
    print(f"{'':<17}" + f"{'m/s x derece':>19}{'derece':>19}"
          f"{'kaldirma orani':>19}{'kWh':>19}{'kapanma orani':>19}")
    print("-" * 112)
    for v, d in sonuc.items():
        satir = f"{d[basliklar[0]]['varyant']:<17}"
        for b in basliklar:
            x = d.get(b, {})
            satir += f"{x.get('deger', float('nan')):>19.3f}"
        print(satir)

    print("\nAYRINTI — ariza toleransi (pod bazinda kaldirma orani)")
    for v, d in sonuc.items():
        p = d["ariza_toleransi"]["podlar"]
        print(f"  {v:<12} " + "  ".join(f"{k}={x*100:5.1f}%" for k, x in p.items()))

    print("\nAYRINTI — asimetrik ariza trimi (karar 43 izgarasi)")
    for v, d in sonuc.items():
        a = d.get("asimetrik_trim", {})
        if "hata" in a:
            print(f"  {v:<12} HATA {a['hata']}")
            continue
        ilk = a.get("ilk_kapanan_V")
        print(f"  {v:<12} {a['kapanan']:>3}/{a['denenen']:<4} "
              f"%{100*a['deger']:<5.0f} ilk kapanan V="
              f"{(f'{ilk:.1f}' if ilk else '—'):>5}  "
              f"azami tilt yayilimi={a['azami_tilt_yayilimi_derece']:>6.2f}°  "
              f"ort kontrol payi=%{100*a['ortalama_kontrol_payi']:.0f}")

    print("\nAYRINTI — gecis koridoru genisligi (derece)")
    for v, d in sonuc.items():
        g = d["gecis_koridoru"]
        print(f"  {v:<12} " + "  ".join(
            f"V={h:>4.0f}:{w:>5.1f}" for h, w in zip(g["hizlar"], g["genislikler"])))

    with open("metrik_sonuclari.json", "w") as f:
        json.dump(sonuc, f, indent=1, ensure_ascii=False)
    print(f"\nmetrik_sonuclari.json yazildi   ({time.time()-t0:.0f} s)")
