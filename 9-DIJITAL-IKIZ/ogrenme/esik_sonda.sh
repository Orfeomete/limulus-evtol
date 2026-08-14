#!/bin/bash
# MUFREDAT ESIGI SONDASI — karar 39 Asama 2a, git/gitme sondasi.
# 4 varyant x 1 tohum. Tek soru: seviye 2 bolumleri yere carpmayi
# birakiyor mu.
#
# Butce ve dizin cevre degiskeniyle verilir. VARSAYILANLAR, 08.08.2026
# 00 39 UTC'de kosan ilk sondanin degerleridir ve DEGISTIRILMEDI, boylece
# o kosu ayni komutla yeniden uretilebilir (karar 39 Asama 2a sonucu).
#   SONDA_ADIM   kosu basina cevre adimi   (varsayilan 300000)
#   SONDA_DIZIN  cikti dizini              (varsayilan kosular_esik_sonda)
# Tadilat 1 geregi ikinci sonda SONDA_ADIM=600000 ve
# SONDA_DIZIN=kosular_esik_sonda600 ile kosar. Butce disinda hicbir ayar
# degismez.
#
# Fizik ve bayraklar:
#   LIMULUS_CRUISE_ITKI=1   kosular_uzun ile ayni fizik (karar 32)
#   LIMULUS_IRTIFA_TABAN=1  F1, irtifa olcegi gorev baslangicina tabanli
#                           (karar 39). Dondurulmus kampanyalar bu bayrak
#                           KAPALI iken uretildi, o yuzden AYRI dizin.
# Ayri dizin kurali karar 22.
#
# Emniyet duzeni uzun_kosu.sh ile aynidir: flock kilidi (karar 30),
# dilim basi ve sonu oksuz surec temizligi (ara kayitlar atomik oldugu
# icin guvenli), ilerleme defteri ve iki dilim ust uste ilerleme yoksa
# ALARM.
cd "$(dirname "$0")"

export SONDA_ADIM="${SONDA_ADIM:-300000}"
export SONDA_DIZIN="${SONDA_DIZIN:-kosular_esik_sonda}"
GUNLUK="${SONDA_DIZIN}.log"
KOSU_GUNLUK="${SONDA_DIZIN}_kosu.log"

exec 9>"/tmp/limulus_${SONDA_DIZIN}.kilit"
if ! flock -n 9; then
    echo "[$(date -u +%d.%H:%M)] ATLANDI · dilim zaten kosuyor (kilit dolu)" >> "$GUNLUK"
    exit 0
fi

export LIMULUS_CRUISE_ITKI=1
export LIMULUS_IRTIFA_TABAN=1
# F2 iskonto ufku (karar 41). Varsayilan 0,99, yani dokunulmamis deger.
export LIMULUS_GAMMA="${LIMULUS_GAMMA:-0.99}"
export LIMULUS_KOSU_DIZINI="$SONDA_DIZIN" LIMULUS_EGITIM=egitim_v2.py
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p "$SONDA_DIZIN"

pkill -f "egitim_v2.py --varyant" 2>/dev/null && sleep 2

biten=$(ls "$SONDA_DIZIN"/*_gunluk.json 2>/dev/null | wc -l)
if [ "$biten" -ge 4 ]; then
    echo "[$(date -u +%d.%H:%M)] 4/4 BITTI" >> "$GUNLUK"
    touch "$SONDA_DIZIN/BITTI"
    exit 0
fi

adim_topla() {
    python3 - << 'PYEOF'
import json, glob, os
d = os.environ["SONDA_DIZIN"]
n = int(os.environ["SONDA_ADIM"])
t = 0
for y in glob.glob(os.path.join(d, "*_ara_durum.json")):
    try: t += json.load(open(y))["adim"]
    except Exception: pass
t += n * len(glob.glob(os.path.join(d, "*_gunluk.json")))
print(t)
PYEOF
}
once=$(adim_topla)
echo "[$(date -u +%d.%H:%M)] dilim basi · biten $biten/4 · butce $SONDA_ADIM · toplam_adim $once" >> "$GUNLUK"

timeout --signal=TERM --kill-after=30 "${1:-3000}" \
    python3 deney.py --adim "$SONDA_ADIM" --isci 2 --tohum-sayisi 1 >> "$KOSU_GUNLUK" 2>&1

pkill -f "egitim_v2.py --varyant" 2>/dev/null; sleep 1
sonra=$(adim_topla)
biten2=$(ls "$SONDA_DIZIN"/*_gunluk.json 2>/dev/null | wc -l)
kazanc=$((sonra - once))
echo "[$(date -u +%d.%H:%M)] dilim sonu · biten $biten2/4 · toplam_adim $sonra · kazanc +$kazanc" >> "$GUNLUK"

if [ "$kazanc" -lt 1000 ] && [ "$biten2" -lt 4 ]; then
    if [ -f "$SONDA_DIZIN/.ilerleme_yok" ]; then
        echo "[$(date -u +%d.%H:%M)] 🔴 ALARM · iki dilimdir ilerleme yok — $KOSU_GUNLUK kuyrugu:" >> "$GUNLUK"
        tail -5 "$KOSU_GUNLUK" >> "$GUNLUK"
    else
        touch "$SONDA_DIZIN/.ilerleme_yok"
        echo "[$(date -u +%d.%H:%M)] ⚠️ uyari · bu dilimde ilerleme yok (bir dahakinde tekrarlarsa ALARM)" >> "$GUNLUK"
    fi
else
    rm -f "$SONDA_DIZIN/.ilerleme_yok"
fi

[ "$biten2" -ge 4 ] && { echo "[$(date -u +%d.%H:%M)] 4/4 BITTI" >> "$GUNLUK"; touch "$SONDA_DIZIN/BITTI"; }
exit 0
