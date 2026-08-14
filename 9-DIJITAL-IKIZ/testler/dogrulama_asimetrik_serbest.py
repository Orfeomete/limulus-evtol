import sys, math, os, numpy as np
sys.path.insert(0,'/home/claude/limulus/9-DIJITAL-IKIZ/dinamik')
from arac import Limulus
from trim import trim_yanal
V_LISTE=(30.0,45.0,60.0,68.9)
VAR=('limulus','ikili','senkron','liftcruise')
print("TEK POD ARIZASI — alti denklemli trim, pod 0 (on sol) kapali")
print("="*84)
print(f"{'varyant':<12}{'V':>6} | {'basarili':>9}{'beta':>8}{'phi':>8}"
      f"{'tilt yayilimi':>15}{'guc kW':>9}")
print("-"*84)
ozet={}
for v in VAR:
    ok=0
    for V in V_LISTE:
        ac=Limulus(varyant_ad=v,sensor_etkin=False)
        r=trim_yanal(ac,V,ariza=0)
        yay = float(np.degrees(r.tilt).max()-np.degrees(r.tilt).min()) if r.tilt is not None else 0.0
        ok += int(r.basarili)
        print(f"{v:<12}{V:>6.1f} | {'evet' if r.basarili else 'HAYIR':>9}"
              f"{math.degrees(r.beta):>+8.2f}{math.degrees(r.phi):>+8.2f}"
              f"{yay:>14.1f}d{r.P_batarya/1e3:>9.1f}")
    ozet[v]=ok
    print("-"*84)
print()
print("OZET — kac hizda trim bulundu (4 uzerinden)")
for v in VAR: print(f"  {v:<12}{ozet[v]}/4")
