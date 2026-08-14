#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIMULUS eVTOL — 6-DOF DINAMIK CEKIRDEK  v0.1

Tez Rev. D parametrelerinden beslenir. Tek dogruluk kaynagi
2-CIZIM-MOTORU/geometri.py, degerler buraya elle kopyalanmaz,
KONF sozlugunde acikca isaretlenir ve kaynak bolum belirtilir.

Durum vektoru (12):
    [u v w]      govde eksenlerinde hiz          m/s
    [p q r]      govde eksenlerinde acisal hiz   rad/s
    [phi th psi] Euler acilari                   rad
    [x y z]      yer ekseninde konum (z asagi)   m

Kontrol vektoru (8):
    [T1..T4]     pod itkileri                    N
    [th1..th4]   pod tilt acilari                rad

Isaret sistemi: govde ekseni x ileri, y saga, z asagi (havacilik standardi).

⚠️ IKI AYRI x EKSENI VAR, KARISTIRILMAZ:
    x_ist  "istasyon"  — burun x=0, geriye dogru artar (geometri.py, tez)
    x_b    "govde"     — CG x=0, ILERIYE dogru artar (dinamik denklemler)
    donusum:  x_b = x_cg - x_ist
Bu donusum v0.1'de atlanmisti ve pitch momentlerinin isareti tersti.
"""
import numpy as np
from dataclasses import dataclass, field

# =====================================================================
# KONFIGURASYON — Rev. D  (kaynak bolum parantez icinde)
# =====================================================================
KONF = dict(
    # --- kutle ve atalet (Bolum 4, 11) ---
    MTOW     = 3000.0,          # kg
    I_xx     = 578.0,           # kg m2   (Bolum 11, Class II)
    I_yy     = 5284.0,
    I_zz     = 5301.0,
    I_xz     = 555.0,

    # --- geometri (geometri.py) ---
    X_ROTOR_ON   = 1.75,        # m, burun x=0
    X_ROTOR_ARKA = 5.00,
    Y_MODUL      = 3.50,
    Z_MODUL      = 1.78,        # yer uzeri
    X_KANAT      = 3.25,        # ceyrek-veter istasyonu
    MAC          = 1.08,
    S_KANAT      = 13.00,       # m2
    AR           = 11.0,
    D_ROTOR      = 2.80,

    # --- agirlik merkezi (Bolum 11) ---
    CG_MAC_YUZDE = 47.0,        # % MAC, tasarim CG
    NP_MAC_YUZDE = 33.0,        # % MAC, notr nokta

    # --- aerodinamik (Bolum 4) ---
    CD0      = 0.027,
    OSWALD   = 0.82,
    CL_MAX   = 1.50,
    CL_ALFA  = 4.90,            # 1/rad, AR=11 icin ~2*pi*AR/(AR+2)

    # --- rotor (Bolum 4) ---
    FOM      = 0.75,
    DOWNLOAD = 1.036,           # kanat uzerine asagi-yuk cezasi %3,6

    # --- itki sistemi (Bolum 9) ---
    P_MOTOR_SUREKLI = 134e3,    # W, motor basina
    P_MOTOR_OEI     = 160e3,    # 30 s
    P_MOTOR_PIK     = 190e3,    # 10 s
    N_MOTOR_POD     = 2,
    ETA_AKT         = 0.90,
    P_OTEL          = 12e3,     # W

    # --- tilt aktuatoru (Bolum 8) ---
    THETA_MIN = 0.0,            # derece
    THETA_MAX = 90.0,
    THETA_HIZ = 15.0,           # derece/s, aktuator oran limiti (VARSAYIM)

    # --- atmosfer ---
    RHO = 1.225,
    G   = 9.81,
)

# ⚠️ VARSAYIM olarak isaretlenenler tezde yok, burada ilk kez tanimlaniyor.
VARSAYIMLAR = {
    "THETA_HIZ": "Tilt aktuatoru oran limiti. Tezde yok. 15 derece/s tipik EMA degeri.",
    "CL_ALFA":   "Kanat tasima egimi. Tezde yok, AR=11 icin ince kanat teorisinden.",
    "Z_POD_CG":  "Podlarin CG duzlemine gore dusey kaciklygi. Tezde CG'nin dusey "
                 "konumu verilmemis. 0 alindi, yani podlar CG duzleminde.",
    "CM0":       "Kanat sifir-tasima pitch momenti katsayisi. Tezde yok. 0 alindi.",
    "X_AERO":    "Aerodinamik kuvvetin etki noktasi. Tezde notr nokta %33 MAC "
                 "olarak verilmis, kanat ceyrek-veteri ise %25 MAC. Model NP'yi "
                 "kullanir cunku govde ve nacelle katkilari NP'ye dahildir.",
}

KONF["Z_POD_CG"] = 0.0
KONF["CM0"] = 0.0


@dataclass
class Limulus:
    k: dict = field(default_factory=lambda: dict(KONF))

    def __post_init__(self):
        k = self.k
        # agirlik merkezi konumu (burun x=0)
        le = k['X_KANAT'] - 0.25*k['MAC']                    # MAC hucum kenari
        self.x_cg = le + (k['CG_MAC_YUZDE']/100)*k['MAC']
        self.x_np = le + (k['NP_MAC_YUZDE']/100)*k['MAC']
        self.sm   = (self.x_np - self.x_cg)/k['MAC']         # statik marj
        # pod konumlari, govde ekseninde  [x_b, y, z] ;  x_b = x_cg - x_ist
        zp = k['Z_POD_CG']
        self.pod = np.array([
            [self.govde_x(k['X_ROTOR_ON']),   -k['Y_MODUL'], zp],  # 1 on-sol
            [self.govde_x(k['X_ROTOR_ON']),   +k['Y_MODUL'], zp],  # 2 on-sag
            [self.govde_x(k['X_ROTOR_ARKA']), -k['Y_MODUL'], zp],  # 3 arka-sol
            [self.govde_x(k['X_ROTOR_ARKA']), +k['Y_MODUL'], zp],  # 4 arka-sag
        ])
        self.A_disk = np.pi*k['D_ROTOR']**2/4
        self.W = k['MTOW']*k['G']
        # atalet matrisi
        self.I = np.array([[k['I_xx'], 0, -k['I_xz']],
                           [0, k['I_yy'], 0],
                           [-k['I_xz'], 0, k['I_zz']]])
        self.I_inv = np.linalg.inv(self.I)

    # ---------- eksen donusumu ----------
    def govde_x(self, x_istasyon):
        """Burun-referansli istasyon (geriye artan) -> govde ekseni (ileriye artan)"""
        return self.x_cg - x_istasyon

    # ---------- rotor ----------
    def rotor_guc(self, T):
        """Momentum teorisi, tek disk. T [N] -> sase gucu [W]"""
        T = np.maximum(T, 1e-6)
        return T*np.sqrt(T/(2*self.k['RHO']*self.A_disk))/self.k['FOM']

    def rotor_itki_limiti(self, P_motor):
        """Motor basina P ile bir podun uretebilecegi azami itki"""
        P_pod = P_motor*self.k['N_MOTOR_POD']
        return (P_pod*self.k['FOM'])**(2/3)*(2*self.k['RHO']*self.A_disk)**(1/3)

    # ---------- aerodinamik ----------
    def kanat_kuvvet(self, V, alfa):
        """Govde eksenlerinde [X, Z] kanat kuvveti ve pitch momenti"""
        k = self.k
        q = 0.5*k['RHO']*V**2
        CL = np.clip(k['CL_ALFA']*alfa, -k['CL_MAX'], k['CL_MAX'])
        CD = k['CD0'] + CL**2/(np.pi*k['AR']*k['OSWALD'])
        L = q*k['S_KANAT']*CL
        D = q*k['S_KANAT']*CD
        # govde eksenine cevir
        X = -D*np.cos(alfa) + L*np.sin(alfa)
        Z = -D*np.sin(alfa) - L*np.cos(alfa)
        # aerodinamik kuvvet notr noktada etkir (govde ekseni kolu)
        r = np.array([self.govde_x(self.x_np), 0.0, 0.0])
        M = np.cross(r, np.array([X, 0.0, Z]))[1]
        M += k['CM0']*q*k['S_KANAT']*k['MAC']
        return X, Z, M, CL, (CL/CD if CD > 0 else 0.0)

    # ---------- kuvvet ve moment toplami ----------
    def kuvvetler(self, durum, kontrol):
        """durum: [u,v,w,p,q,r,phi,th,psi,x,y,z]  kontrol: [T1..T4, th1..th4]"""
        u, v, w = durum[0:3]; p, q, r = durum[3:6]; phi, th, psi = durum[6:9]
        T = np.asarray(kontrol[0:4], float)
        tilt = np.asarray(kontrol[4:8], float)

        V = np.sqrt(u*u + v*v + w*w)
        alfa = np.arctan2(w, u) if V > 0.5 else 0.0

        F = np.zeros(3); M = np.zeros(3)

        # rotor itkisi: tilt=0 -> tamamen -z (yukari), tilt=90 -> tamamen +x (ileri)
        for i in range(4):
            ct, st = np.cos(tilt[i]), np.sin(tilt[i])
            f = np.array([T[i]*st, 0.0, -T[i]*ct])
            F += f
            M += np.cross(self.pod[i], f)

        # kanat
        Xw, Zw, Mw, CL, LD = self.kanat_kuvvet(V, alfa)
        F += np.array([Xw, 0.0, Zw]); M += np.array([0.0, Mw, 0.0])

        # yercekimi (govde eksenlerine)
        g = self.k['G']
        F += self.k['MTOW']*g*np.array([-np.sin(th),
                                        np.sin(phi)*np.cos(th),
                                        np.cos(phi)*np.cos(th)])
        return F, M, dict(V=V, alfa=alfa, CL=CL, LD=LD)

    def turev(self, durum, kontrol):
        """6-DOF hareket denklemleri, durum turevi"""
        u,v,w = durum[0:3]; p,q,r = durum[3:6]; phi,th,psi = durum[6:9]
        m = self.k['MTOW']
        F, M, _ = self.kuvvetler(durum, kontrol)
        om = np.array([p,q,r]); vel = np.array([u,v,w])
        acc = F/m - np.cross(om, vel)
        omd = self.I_inv @ (M - np.cross(om, self.I @ om))
        # Euler kinematigi
        sp, cp = np.sin(phi), np.cos(phi); tt, ct = np.tan(th), np.cos(th)
        eul = np.array([p + (q*sp + r*cp)*tt,
                        q*cp - r*sp,
                        (q*sp + r*cp)/max(ct, 1e-6)])
        # yer eksenine hiz
        st = np.sin(th); cth = np.cos(th); sps, cps = np.sin(psi), np.cos(psi)
        R = np.array([
            [cth*cps, sp*st*cps - cp*sps, cp*st*cps + sp*sps],
            [cth*sps, sp*st*sps + cp*cps, cp*st*sps - sp*cps],
            [-st,     sp*cth,             cp*cth]])
        return np.concatenate([acc, omd, eul, R @ vel])
