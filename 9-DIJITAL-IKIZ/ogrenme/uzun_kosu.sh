#!/bin/bash
# UZUN BUTCELI KOSU — mufredat seviye 4 hedefi (karar 36 on kaydi).
# 4 varyant x 5 tohum x 3M adim. EMNIYETLI SURUM (05.08.2026):
#   - flock kilidi (karar 30): iki dilim ayni anda kosamaz
#   - dilim basinda/sonunda oksuz egitim surecleri temizlenir (kilit
#     bizde oldugu icin baskasinin sureci olamaz; oldurmek guvenlidir
#     cunku ara kayitlar artik ATOMIK — egitim_v2.py yamasi)
#   - ilerleme defteri: toplam adim sayilir, onceki dilimle kiyaslanir,
#     iki dilim ust uste ilerleme yoksa ALARM yazilir
#   - 20/20 olunca BITTI dosyasi birakilir
# Fizik: LIMULUS_CRUISE_ITKI=1 (lift+cruise 180 kW itici birimle) —
# kosular_v2'den FARKLI dizin (kosular_uzun), karistirilamaz.
cd "$(dirname "$0")"

exec 9>/tmp/limulus_uzun.kilit
if ! flock -n 9; then
    echo "[$(date -u +%d.%H:%M)] ATLANDI · dilim zaten kosuyor (kilit dolu)" >> uzun.log
    exit 0
fi

export LIMULUS_CRUISE_ITKI=1
export LIMULUS_KOSU_DIZINI=kosular_uzun LIMULUS_EGITIM=egitim_v2.py
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p kosular_uzun

# --- oksuz surec temizligi (atomik kayit sayesinde guvenli) ---
pkill -f "egitim_v2.py --varyant" 2>/dev/null && sleep 2

biten=$(ls kosular_uzun/*_gunluk.json 2>/dev/null | wc -l)
if [ "$biten" -ge 20 ]; then
    echo "[$(date -u +%d.%H:%M)] 20/20 BITTI" >> uzun.log
    touch kosular_uzun/BITTI
    exit 0
fi

# --- ilerleme defteri: dilim ONCESI toplam adim ---
adim_topla() {
    python3 - << 'PYEOF'
import json, glob
t = 0
for y in glob.glob("kosular_uzun/*_ara_durum.json"):
    try: t += json.load(open(y))["adim"]
    except Exception: pass
t += 3_000_000 * len(glob.glob("kosular_uzun/*_gunluk.json"))
print(t)
PYEOF
}
once=$(adim_topla)
echo "[$(date -u +%d.%H:%M)] dilim basi · biten $biten/20 · toplam_adim $once" >> uzun.log

timeout --signal=TERM --kill-after=30 "${1:-3000}" \
    python3 deney.py --adim 3000000 --isci 2 --tohum-sayisi 5 >> uzun_kosu.log 2>&1

# dilim bitti — artiklari temizle, ilerlemeyi olc
pkill -f "egitim_v2.py --varyant" 2>/dev/null; sleep 1
sonra=$(adim_topla)
biten2=$(ls kosular_uzun/*_gunluk.json 2>/dev/null | wc -l)
kazanc=$((sonra - once))
echo "[$(date -u +%d.%H:%M)] dilim sonu · biten $biten2/20 · toplam_adim $sonra · kazanc +$kazanc" >> uzun.log

# --- takilma bekcisi: iki dilim ust uste kazanc ~0 ise ALARM ---
if [ "$kazanc" -lt 1000 ] && [ "$biten2" -lt 20 ]; then
    if [ -f kosular_uzun/.ilerleme_yok ]; then
        echo "[$(date -u +%d.%H:%M)] 🔴 ALARM · iki dilimdir ilerleme yok — uzun_kosu.log kuyrugu:" >> uzun.log
        tail -5 uzun_kosu.log >> uzun.log
    else
        touch kosular_uzun/.ilerleme_yok
        echo "[$(date -u +%d.%H:%M)] ⚠️ uyari · bu dilimde ilerleme yok (bir dahakinde tekrarlarsa ALARM)" >> uzun.log
    fi
else
    rm -f kosular_uzun/.ilerleme_yok
fi

[ "$biten2" -ge 20 ] && { echo "[$(date -u +%d.%H:%M)] 20/20 BITTI" >> uzun.log; touch kosular_uzun/BITTI; }
exit 0
