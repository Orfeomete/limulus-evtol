#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIMULUS eVTOL — GEOMETRI TANIMI ve SVG CIZIM ALTYAPISI
Rev. 2026-08 (Rev.E) : 4 rotor / 4 RDP modulu konfigurasyonu

Rev.E degisikligi (03.08.2026, bulgu F1-F4):
  agirlik merkezi %47 MAC -> %33 MAC (notr nokta), statik marj -%14 -> 0
  rotor istasyonlari 1,75 / 5,00 -> 1,71 / 4,96  (CG'ye gore ortalandi)
Gerekce 4-KARARLAR/10-dinamik-model-bulgulari.md
"""
import math

# =====================================================================
# GEOMETRI (metre) — trade study sonuclarindan
# =====================================================================
G = dict(
    # Genel
    L_TOTAL      = 6.85,   # Rev.D: rotor arasi 3,00 -> 3,25 m
    SPAN         = 12.00,
    H_TOTAL      = 2.70,   # hover konfig. (Z_MODUL + H_MODUL/2 + 0.52)

    # Karapas govde (kabin)
    L_GOVDE      = 3.80,
    B_GOVDE      = 3.20,
    H_GOVDE      = 1.15,

    # Kanat
    S_KANAT      = 13.00,
    AR           = 11.0,
    VECHILE      = 1.08,   # veter (chord)

    # RDP modulu
    N_MODUL      = 4,
    L_MODUL      = 3.25,
    B_MODUL      = 3.00,
    H_MODUL      = 0.80,
    Y_MODUL      = 3.50,   # lateral konum (+/-)
    L_BOOM       = 6.45,   # boyuna tasiyici kiris (Rev.D)
    D_ROTOR      = 2.80,
    DX_ROTOR     = 3.25,   # on/arka rotor merkezleri arasi (Rev.D: modul cakismasi giderildi)
    H_KUYRUK     = 1.00,

    # Inis takimi
    TRACK        = 2.60,
    WHEELBASE    = 2.40,
    H_INIS       = 0.85,

    # Tilt
    THETA_HOVER  = 0,
    THETA_CRUISE = 85,
    THETA_MAX    = 90,

    # Uzunlamasina yerlesim (burun x=0)
    X_GOVDE_ON   = 0.15,
    X_GOVDE_ARKA = 3.95,
    X_MODUL_ON   = 0.31,
    X_MODUL_ARKA = 6.76,
    X_ROTOR_ON   = 1.71,   # Rev.E: rotor cifti CG'ye gore ortalandi (bulgu F1)
    X_ROTOR_ARKA = 4.96,
    Z_MODUL      = 1.78,   # modul ekseni yer uzeri yukseklik
    X_KANAT      = 3.25,   # kanat ceyrek-veter istasyonu

    # Agirlik merkezi ve notr nokta (Rev.E: CG notr noktaya cekildi, bulgu F3)
    CG_MAC_YUZDE = 33.0,   # Rev.D'de 47,0 idi
    NP_MAC_YUZDE = 33.0,
)

# =====================================================================
# PERFORMANS (metin ve etiketler icin)
# =====================================================================
P = dict(
    MTOW=3000, PAYLOAD=360, PAX=4,
    V_CRUISE_KMH=248, V_CRUISE_MS=68.9,
    MENZIL=93, MENZIL_TLR=90, REZERV="15 dk cruise loiter",
    LD=16.1, CL=0.78,
    N_ROTOR=4, N_MOTOR=8,
    P_MOTOR=134, P_HOVER=913, P_KURULU=1070,   # Rev.D: hover download %3,6 dahil
    DL=1195, DOWNWASH=22.1,
    RPM=1044, F_1REV=17.4, F_BPF=87.0,
    TORK=1226, F_E=348,
    # ⚠️ ROTOR PALI — bu iki sayi tasarim betiginde 09.08.2026'ya kadar YOKTU,
    # yalniz simulatorde (9-DIJITAL-IKIZ/dinamik/rotor.py) turetiliyordu. Iki
    # parametre kaynagi arasinda kapsam farki demek, tez tarafinda goze
    # gorunmeyen bir catlaktir — 28/29 kN kalemi tam bu sekilde dort gun
    # kaybettirdi. Degerler simulatorun turetmesiyle AYNI tabandan gelir:
    #     sigma = C_T / (C_T/sigma)_tasarim,  C_T = T_hover / (rho A V_uc^2)
    #     pal_veteri = sigma * pi * R / N_PAL
    # Ikisi de turetilmis degerdir, olculmus degil. Tez pal veteri ya da
    # soliditeyi vermiyor, kaynak hover blade loading kosuludur.
    # Capraz kontrol: 9-DIJITAL-IKIZ/testler/dogrulama_capraz_kontrol.py
    N_PAL=5,
    SIGMA=0.308, PAL_VETERI=0.271, CTS_TASARIM=0.14,
    M_BATT=659, E_BATT=151,   # Rev.D: 178 kWh brut, 151 kWh kullanilabilir
    M_MODUL=148,
)

# =====================================================================
# SVG ALTYAPI
# =====================================================================
PAL = dict(
    kagit   = "#FFFFFF",
    cerceve = "#D8D4CC",
    govde   = "#E8E0D2",
    govde_k = "#5A5248",
    kanat   = "#DCD5C6",
    modul   = "#F0F0F0",
    modul_k = "#C1502E",
    rotor   = "#8C7A66",
    rotor_k = "#4A4038",
    kuyruk  = "#7E9B76",
    kuyruk_k= "#4A5C45",
    cam     = "#2E4A66",
    teker   = "#2A2A2A",
    olcu    = "#3A3A3A",
    merkez  = "#8A8A8A",
    metin   = "#1A1A1A",
    metin_a = "#5A5A5A",
    vurgu   = "#C1502E",
    ghost   = "#B8B8B8",
)

FONT = "'DejaVu Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif"

class Cizim:
    """Milimetrik teknik cizim uretici. Dunya koordinati = metre."""
    def __init__(self, w, h, olcek, ox, oy, baslik="", altbaslik=""):
        self.w, self.h = w, h
        self.k = olcek          # piksel / metre
        self.ox, self.oy = ox, oy
        self.p = []
        self.baslik = baslik
        self.altbaslik = altbaslik

    # --- koordinat donusumu ---
    def X(self, x): return self.ox + x*self.k
    def Y(self, y): return self.oy - y*self.k
    def L(self, d): return d*self.k

    def add(self, s): self.p.append(s)

    # --- temel primitifler ---
    def cizgi(self, x1,y1,x2,y2, renk=None, kal=1.4, tip=None, opak=1.0, cap="round"):
        renk = renk or PAL['govde_k']
        d = f' stroke-dasharray="{tip}"' if tip else ''
        self.add(f'<line x1="{self.X(x1):.2f}" y1="{self.Y(y1):.2f}" '
                 f'x2="{self.X(x2):.2f}" y2="{self.Y(y2):.2f}" stroke="{renk}" '
                 f'stroke-width="{kal}"{d} stroke-opacity="{opak}" stroke-linecap="{cap}"/>')

    def dikdortgen(self, x,y,w,h, dolgu="none", renk=None, kal=1.4, tip=None, r=0, opak=1.0):
        renk = renk or PAL['govde_k']
        d = f' stroke-dasharray="{tip}"' if tip else ''
        self.add(f'<rect x="{self.X(x):.2f}" y="{self.Y(y+h):.2f}" '
                 f'width="{self.L(w):.2f}" height="{self.L(h):.2f}" rx="{r}" '
                 f'fill="{dolgu}" stroke="{renk}" stroke-width="{kal}"{d} opacity="{opak}"/>')

    def elips(self, cx,cy,rx,ry, dolgu="none", renk=None, kal=1.4, tip=None, opak=1.0, aci=0):
        renk = renk or PAL['govde_k']
        d = f' stroke-dasharray="{tip}"' if tip else ''
        tr = f' transform="rotate({-aci} {self.X(cx):.2f} {self.Y(cy):.2f})"' if aci else ''
        self.add(f'<ellipse cx="{self.X(cx):.2f}" cy="{self.Y(cy):.2f}" '
                 f'rx="{self.L(rx):.2f}" ry="{self.L(ry):.2f}" fill="{dolgu}" '
                 f'stroke="{renk}" stroke-width="{kal}"{d} opacity="{opak}"{tr}/>')

    def yol(self, pts, dolgu="none", renk=None, kal=1.4, kapali=True, tip=None, opak=1.0):
        renk = renk or PAL['govde_k']
        d = f' stroke-dasharray="{tip}"' if tip else ''
        s = f"M {self.X(pts[0][0]):.2f} {self.Y(pts[0][1]):.2f} "
        for x,y in pts[1:]:
            s += f"L {self.X(x):.2f} {self.Y(y):.2f} "
        if kapali: s += "Z"
        self.add(f'<path d="{s}" fill="{dolgu}" stroke="{renk}" stroke-width="{kal}"{d} '
                 f'opacity="{opak}" stroke-linejoin="round"/>')

    def egri(self, d_str, dolgu="none", renk=None, kal=1.4, tip=None, opak=1.0):
        renk = renk or PAL['govde_k']
        d = f' stroke-dasharray="{tip}"' if tip else ''
        self.add(f'<path d="{d_str}" fill="{dolgu}" stroke="{renk}" stroke-width="{kal}"{d} '
                 f'opacity="{opak}" stroke-linejoin="round"/>')

    def yazi(self, x,y,s, boy=11, renk=None, hiza="middle", kalin=False, italik=False,
             piksel=False, aci=0, opak=1.0):
        renk = renk or PAL['metin']
        px = x if piksel else self.X(x)
        py = y if piksel else self.Y(y)
        w = "600" if kalin else "400"
        it = ' font-style="italic"' if italik else ''
        tr = f' transform="rotate({aci} {px:.2f} {py:.2f})"' if aci else ''
        self.add(f'<text x="{px:.2f}" y="{py:.2f}" font-family="{FONT}" font-size="{boy}" '
                 f'font-weight="{w}"{it} fill="{renk}" text-anchor="{hiza}" '
                 f'opacity="{opak}"{tr}>{s}</text>')

    # --- merkez cizgisi (nokta-tire) ---
    def merkez_cizgi(self, x1,y1,x2,y2):
        self.cizgi(x1,y1,x2,y2, PAL['merkez'], 0.8, "10,3,2,3")

    # --- olculendirme ---
    def olcu_yatay(self, x1, x2, y, etiket, ofset=0, ust=True, boy=10):
        yy = y + ofset
        a = 5
        X1,X2,Y = self.X(x1), self.X(x2), self.Y(yy)
        self.add(f'<line x1="{X1}" y1="{Y}" x2="{X2}" y2="{Y}" stroke="{PAL["olcu"]}" stroke-width="0.9"/>')
        for X,s in ((X1,1),(X2,-1)):
            self.add(f'<path d="M {X} {Y} l {s*a} {-a*0.42} M {X} {Y} l {s*a} {a*0.42}" '
                     f'stroke="{PAL["olcu"]}" stroke-width="0.9" fill="none"/>')
        # uzanti cizgileri
        for xv in (x1,x2):
            self.add(f'<line x1="{self.X(xv)}" y1="{self.Y(y)}" x2="{self.X(xv)}" y2="{Y+(4 if not ust else -4)}" '
                     f'stroke="{PAL["olcu"]}" stroke-width="0.6" stroke-dasharray="3,2" stroke-opacity="0.65"/>')
        self.yazi((X1+X2)/2, Y-4 if ust else Y+11, etiket, boy, PAL['olcu'], piksel=True)

    def olcu_dikey(self, y1, y2, x, etiket, ofset=0, sag=True, boy=10, etiket_dy=0):
        xx = x + ofset
        a = 5
        X,Y1,Y2 = self.X(xx), self.Y(y1), self.Y(y2)
        self.add(f'<line x1="{X}" y1="{Y1}" x2="{X}" y2="{Y2}" stroke="{PAL["olcu"]}" stroke-width="0.9"/>')
        for Y,s in ((Y1,1),(Y2,-1)):
            self.add(f'<path d="M {X} {Y} l {-a*0.42} {s*a} M {X} {Y} l {a*0.42} {s*a}" '
                     f'stroke="{PAL["olcu"]}" stroke-width="0.9" fill="none"/>')
        self.yazi(X+(7 if sag else -7), (Y1+Y2)/2+3+etiket_dy, etiket, boy, PAL['olcu'],
                  hiza="start" if sag else "end", piksel=True)

    def olcek_cubugu(self, px, py, metre=1.0, etiket=None):
        w = self.L(metre)
        self.add(f'<line x1="{px}" y1="{py}" x2="{px+w}" y2="{py}" stroke="{PAL["olcu"]}" stroke-width="1.6"/>')
        for t in (px, px+w):
            self.add(f'<line x1="{t}" y1="{py-4}" x2="{t}" y2="{py+4}" stroke="{PAL["olcu"]}" stroke-width="1.6"/>')
        self.add(f'<line x1="{px}" y1="{py}" x2="{px+w/2}" y2="{py}" stroke="{PAL["olcu"]}" stroke-width="4"/>')
        self.yazi(px+w/2, py+14, etiket or f"{metre:.0f} m", 9.5, PAL['olcu'], piksel=True)

    # --- aciklama balonu ---
    def etiket_cizgi(self, x,y, px,py, s, boy=9.5, renk=None, hiza="start", kalin=False):
        renk = renk or PAL['metin_a']
        self.add(f'<line x1="{self.X(x)}" y1="{self.Y(y)}" x2="{px}" y2="{py}" '
                 f'stroke="{renk}" stroke-width="0.7" stroke-opacity="0.8"/>')
        self.add(f'<circle cx="{self.X(x)}" cy="{self.Y(y)}" r="1.8" fill="{renk}"/>')
        dy = -3 if hiza!="middle" else -6
        self.yazi(px + (4 if hiza=="start" else (-4 if hiza=="end" else 0)), py+dy, s,
                  boy, renk, hiza, kalin, piksel=True)

    # --- render ---
    def svg(self):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}">\n'
                f'<rect width="{self.w}" height="{self.h}" fill="{PAL["kagit"]}"/>\n'
                f'<rect x="6" y="6" width="{self.w-12}" height="{self.h-12}" fill="none" '
                f'stroke="{PAL["cerceve"]}" stroke-width="1"/>\n')
        t = ""
        if self.baslik:
            t += (f'<text x="{self.w/2}" y="27" font-family="{FONT}" font-size="14.5" '
                  f'font-weight="650" fill="{PAL["metin"]}" text-anchor="middle">{self.baslik}</text>\n')
        if self.altbaslik:
            t += (f'<text x="{self.w/2}" y="44" font-family="{FONT}" font-size="10" '
                  f'fill="{PAL["metin_a"]}" text-anchor="middle">{self.altbaslik}</text>\n')
        return head + t + "\n".join(self.p) + "\n</svg>"

    def kaydet(self, yol_):
        with open(yol_, "w", encoding="utf-8") as f:
            f.write(self.svg())
        return yol_


def rot(x, y, cx, cy, aci_derece):
    """Nokta dondurme (saat yonu tersi pozitif)"""
    a = math.radians(aci_derece)
    dx, dy = x-cx, y-cy
    return cx + dx*math.cos(a) - dy*math.sin(a), cy + dx*math.sin(a) + dy*math.cos(a)


if __name__ == "__main__":
    print("GEOMETRI TANIMI — Limulus eVTOL Rev.2026-08")
    print("="*58)
    for k,v in G.items():
        print(f"  {k:<14} = {v}")
    print("\nPERFORMANS")
    print("="*58)
    for k,v in P.items():
        print(f"  {k:<14} = {v}")
    # tutarlilik kontrolu
    print("\nKONTROLLER")
    print("="*58)
    veter = G['S_KANAT']/G['SPAN']
    print(f"  Ortalama veter      = {veter:.2f} m  (tanimli {G['VECHILE']})")
    print(f"  AR kontrol          = {G['SPAN']**2/G['S_KANAT']:.2f}  (tanimli {G['AR']})")
    ic_kenar = G['Y_MODUL'] - G['B_MODUL']/2
    print(f"  Modul ic kenari     = {ic_kenar:.2f} m")
    print(f"  Govde yari genislik = {G['B_GOVDE']/2:.2f} m")
    print(f"  ACIKLIK             = {ic_kenar - G['B_GOVDE']/2:.2f} m  {'OK' if ic_kenar>G['B_GOVDE']/2 else 'CAKISMA!'}")
    dis_kenar = G['Y_MODUL'] + G['B_MODUL']/2
    print(f"  Modul dis kenari    = {dis_kenar:.2f} m  / yari aciklik {G['SPAN']/2:.2f} m "
          f"{'OK' if dis_kenar < G['SPAN']/2 else 'TASIYOR!'}")
    print(f"  Modul uzunlugu      = {G['L_MODUL']:.2f} m  (rotor {G['D_ROTOR']:.2f} + cerceve)")
    print(f"  Boom uzunlugu       = {G['L_BOOM']:.2f} m")
    boom_ger = G['X_MODUL_ARKA']-G['X_MODUL_ON']
    print(f"  Boom kontrol        = {boom_ger:.2f} m  {'OK' if abs(boom_ger-G['L_BOOM'])<0.01 else 'UYUMSUZ'}")
    boyuna = G['X_ROTOR_ARKA']-G['X_ROTOR_ON']
    print(f"  Rotor boyuna ara    = {boyuna:.2f} m / cap {G['D_ROTOR']:.2f} m  "
          f"{'OK (cakisma yok)' if boyuna>G['D_ROTOR'] else 'CAKISMA!'}")
    print(f"  Rotor ucu acikligi  = {boyuna-G['D_ROTOR']:.2f} m  "
          f"({100*(boyuna-G['D_ROTOR'])/G['D_ROTOR']:.0f}% cap)")
    # Pal geometrisi TURETILMIS degerdir, tez vermiyor. Kaynak hover blade
    # loading kosulu C_T/sigma = 0,14. Simulator ayni sayiyi kendi turetiyor,
    # capraz kontrol testi ikisini karsilastirir.
    _vuc = P['RPM']*2*math.pi/60*G['D_ROTOR']/2
    _ver_hesap = P['SIGMA']*math.pi*(G['D_ROTOR']/2)/P['N_PAL']
    print(f"  Rotor solidite      = {P['SIGMA']:.3f}  ({P['N_PAL']} pal, "
          f"veter {P['PAL_VETERI']:.3f} m, pal ucu {_vuc:.0f} m/s)  "
          f"{'OK' if abs(_ver_hesap-P['PAL_VETERI'])<5e-4 else 'VETER TUTMUYOR!'}"
          f"  [C_T/sigma = {P['CTS_TASARIM']:.2f} tabaninda turetildi]")
    # MODUL CERCEVESI boyuna cakisma kontrolu (rotor degil, modul govdesi)
    mod_bosluk = boyuna - G['L_MODUL']
    print(f"  Modul boyuna aciklik= {mod_bosluk:+.2f} m  "
          f"{'OK' if mod_bosluk>=0 else 'CAKISMA! on ve arka modul cercevesi ust uste biniyor'}")
    if mod_bosluk < 0:
        print(f"     -> cakismasiz azami modul uzunlugu = {boyuna:.2f} m")
        print(f"     -> ya da gereken rotor arasi = {G['L_MODUL']:.2f} m "
              f"(boom {G['L_BOOM']+ (G['L_MODUL']-boyuna):.2f} m, "
              f"L_toplam {G['L_TOTAL']+(G['L_MODUL']-boyuna):.2f} m)")
    import math as _m
    for th in (30,60,85,90):
        alt = G['Z_MODUL']-(G['D_ROTOR']/2)*_m.sin(_m.radians(th))
        print(f"  theta={th:>2}deg yer acikligi = {alt:.2f} m  {'OK' if alt>0.25 else 'YETERSIZ'}")

    # ---- BOYUNA DENGE (Rev.E, bulgu F1-F4) ----
    print()
    mac = G['VECHILE']; le = G['X_KANAT'] - 0.25*mac
    xcg = le + G['CG_MAC_YUZDE']/100*mac
    xnp = le + G['NP_MAC_YUZDE']/100*mac
    orta = (G['X_ROTOR_ON'] + G['X_ROTOR_ARKA'])/2
    lf, lr = xcg-G['X_ROTOR_ON'], G['X_ROTOR_ARKA']-xcg
    W = P['MTOW']*9.81
    # 2(T_f + T_r) = W  ve  2 l_f T_f = 2 l_r T_r
    T_f = W*lr/(2*(lf+lr)); T_r = W*lf/(2*(lf+lr))
    # ⚠️ Eklem yuku ROTOR ITKISINI tasir, agirligi degil. Hover'da rotor
    # download'u da yenmek zorunda, yani T = W x 1,036 / 4. Rev. E'de F2
    # bu carpan ATLANARAK kapatilmisti, ayrinti 4-KARARLAR/16.
    DL = 1.036                      # download, Bolum 4 ile ayni
    ult = T_r*DL*2.5*1.5/1e3
    M_trim = W*(xcg-xnp)
    print(f"  Agirlik merkezi     = {xcg:.3f} m ({G['CG_MAC_YUZDE']:.1f}% MAC)")
    print(f"  Notr nokta          = {xnp:.3f} m ({G['NP_MAC_YUZDE']:.1f}% MAC)")
    print(f"  Statik marj         = {(xnp-xcg)/mac*100:+.1f}%")
    print(f"  Rotor orta noktasi  = {orta:.3f} m  / CG kacikligi {xcg-orta:+.3f} m  "
          f"{'OK' if abs(xcg-orta)<0.02 else 'ASIMETRIK! bkz. bulgu F1'}")
    print(f"  Hover itki dagilimi = on {T_f:.0f} N / arka {T_r:.0f} N  "
          f"(esit dagilim {W/4:.0f} N, sapma {(T_r-W/4)/(W/4)*100:+.2f}%)")
    # ⚠️ KAPASITE 29 kN (karar 16, Mete 05.08.2026). 28 kN'lik ilk hedef
    # download dahil edilince %2,1 asiliyordu. Kapasite bir tasarim
    # hedefidir, detay FEM dogrulayana kadar acik kalemdir.
    # Simulator (9-DIJITAL-IKIZ) 28 kN'da BIRAKILDI, gerekcesi karar 16'da.
    # Yama 05.08'de geometri_YENI_29kN.py'ye yazilmis, bu dosyaya
    # 09.08.2026'da birlestirildi (karar 16 Tadilat 1).
    RDPIF = 29.0
    print(f"  Arka pod ultimate   = {ult:.2f} kN / RDP-IF kapasite {RDPIF:.2f} kN  "
          f"(download {DL:.3f} dahil)  "
          f"{'OK' if ult<=RDPIF else f'ASIYOR %{(ult/RDPIF-1)*100:.1f}! bkz. karar 16'}"
          f"  [marj %{(RDPIF/ult-1)*100:.1f}]")
    print(f"  Cruise trim momenti = {M_trim:.0f} N m  "
          f"{'OK' if abs(M_trim)<50 else 'KUMANDA ORGANI GEREKIR! bkz. bulgu F3'}")
