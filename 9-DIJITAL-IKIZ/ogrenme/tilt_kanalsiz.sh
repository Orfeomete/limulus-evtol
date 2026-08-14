#!/bin/bash
# TILT KANALSIZ LIMULUS — karar 27'nin acik kalemi.
# Politika tilt eylemini HIC gormeden sifirdan egitilir.
# ⚠️ AYRI DIZIN (kosular_tk). kosular_v2 kanal ACIKKEN uretildi.
# ⚠️ KILIT ZORUNLU, bkz. 4-KARARLAR/30.
cd "$(dirname "$0")"

exec 9>/tmp/limulus_tk.kilit
if ! flock -n 9; then
    echo "[$(date -u +%H:%M)] ATLANDI · dilim zaten kosuyor" >> tk.log
    exit 0
fi

export LIMULUS_TILT_KANALI=0
export LIMULUS_KOSU_DIZINI=kosular_tk LIMULUS_EGITIM=egitim_v2.py
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
n=$(ls kosular_tk/*_gunluk.json 2>/dev/null | wc -l)
echo "[$(date -u +%H:%M)] tk · $n/5" >> tk.log
[ "$n" -ge 5 ] && exit 0
LIMULUS_VARYANTLAR=limulus timeout "${1:-540}" python3 deney.py --adim 1000000 --isci 2 \
    --tohum-sayisi 5 >> tk_kosu.log 2>&1
echo "[$(date -u +%H:%M)] dilim · $(ls kosular_tk/*_gunluk.json 2>/dev/null|wc -l)/5" >> tk.log
