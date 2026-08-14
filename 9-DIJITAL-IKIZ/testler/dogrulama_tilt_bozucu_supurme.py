import sys, math, os, numpy as np
_B='/home/claude/limulus/9-DIJITAL-IKIZ'
for y in ('dinamik','ogrenme'):
    sys.path.insert(0, os.path.join(_B,y))
from arac import Limulus
from temel_kontrolcu import TemelKontrolcu

def kalici(v, M, kanal):
    ac = Limulus(varyant_ad=v, sensor_etkin=False)
    th_c = ac.k["THETA_CRUISE"]
    d0=np.zeros(12); d0[0]=68.9; d0[11]=-300.0
    ac.sifirla(durum=d0, tilt0=th_c, T0=500.0)
    kk=TemelKontrolcu(ac, tilt_kanali=kanal); kk.sifirla()
    izi=[]
    for i in range(int(30.0/ac.dt)):
        T,tilt = kk(ac.durum, 300.0, 68.9, th_c)
        ac.adim(T,tilt,M_dis=np.array([0.,M,0.]))
        izi.append(math.degrees(ac.durum[7]))
        if abs(ac.durum[7])>math.radians(80): return 999.0, math.degrees(abs(kk._son_trim))
    return float(np.mean(izi[-int(5.0/ac.dt):])), math.degrees(abs(kk._son_trim))

print("KALICI TUTUM HATASI, BOZUCU MOMENTE GORE  (cruise 85 derece, 30 s)")
print("="*78)
print(f"{'M_bozucu':>10} | {'limulus kapali':>15}{'acik':>9} | {'ikili acik':>12} | {'senkron acik':>14}")
print("-"*78)
for M in (200, 400, 600, 800, 1000, 1500):
    a,_ = kalici('limulus', M, False)
    b,sb = kalici('limulus', M, True)
    c,_ = kalici('ikili',   M, True)
    d,_ = kalici('senkron', M, True)
    f=lambda x: "ZARF DISI" if x>900 else f"{x:+7.2f}d"
    print(f"{M:>8} Nm | {f(a):>15}{f(b):>9} | {f(c):>12} | {f(d):>14}")
print()
print("Not: senkron tiltte diferansiyel kip yok, sutunu 'kapali' ile ayni olmali.")
