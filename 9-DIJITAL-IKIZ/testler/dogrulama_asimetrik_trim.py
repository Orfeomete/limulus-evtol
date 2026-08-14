import sys, math, numpy as np
sys.path.insert(0,'/home/claude/limulus/9-DIJITAL-IKIZ/dinamik')
from arac import Limulus
from trim import trim_yanal
VAR=('limulus','ikili','senkron','liftcruise')
print("POD ARIZASINDA YAN KAYMASIZ TRIM  (beta = 0 zorunlu)")
print("="*80)
print("Soru: bir pod kapaliyken arac YAN KAYMADAN duz ucabiliyor mu?")
print("Yan kayma suruklemeyi ve yapisal yani yuku artirir, kacinilmasi gerekir.")
print()
print(f"{'varyant':<12}{'V':>6}{'ariza':>7} | {'trim':>6}{'phi':>8}"
      f"{'tilt yayilimi':>15}{'itki yayilimi':>15}")
print("-"*80)
tablo={}
for v in VAR:
    ok=0; n=0
    for V in (45.0, 60.0, 68.9):
        for ar in (0, 2):
            ac=Limulus(varyant_ad=v,sensor_etkin=False)
            r=trim_yanal(ac,V,ariza=ar,beta_hedef=0.0)
            n+=1; ok+=int(r.basarili)
            ty=float(np.degrees(r.tilt).max()-np.degrees(r.tilt).min()) if r.tilt is not None else 0
            iy=float(r.T.max()-r.T.min())/1e3 if r.T is not None else 0
            print(f"{v:<12}{V:>6.1f}{ar:>7} | {'evet' if r.basarili else 'HAYIR':>6}"
                  f"{math.degrees(r.phi):>+8.2f}{ty:>14.1f}d{iy:>14.2f}kN")
    tablo[v]=(ok,n)
    print("-"*80)
print()
print("OZET")
for v in VAR:
    o,n=tablo[v]; print(f"  {v:<12}{o}/{n}  ({100*o/n:.0f}%)")
