#!/bin/bash
# Lift+cruise yeniden egitimi — ayri cruise itki birimi ACIK.
# ⚠️ AYRI DIZIN. kosular_v2 kapali modelle uretildi, karistirilmaz.
#
# ⚠️ KILIT ZORUNLU (04.08.2026, bkz. 4-KARARLAR/30).
# Bir dilim bitmeden ikinci dilim baslatildiginda IKI surec ayni
# kosular_lc/*_ara.pt dosyasina yaziyor. Once baslayan ilerlemis
# durumu, sonra baslayan ESKI durumu kaydediyor ve ilerleme sessizce
# geri gidiyor. flock, ikinci cagriyi calistirmadan dusuruyor.
cd "$(dirname "$0")"

exec 9>/tmp/limulus_lc.kilit
if ! flock -n 9; then
    echo "[$(date -u +%H:%M)] ATLANDI · dilim zaten kosuyor" >> lc.log
    exit 0
fi

export LIMULUS_CRUISE_ITKI=1
export LIMULUS_KOSU_DIZINI=kosular_lc LIMULUS_EGITIM=egitim_v2.py
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
n=$(ls kosular_lc/*_gunluk.json 2>/dev/null | wc -l)
echo "[$(date -u +%H:%M)] lc · $n/5" >> lc.log
[ "$n" -ge 5 ] && exit 0
LIMULUS_VARYANTLAR=liftcruise timeout "${1:-540}" python3 deney.py --adim 1000000 --isci 2 \
    --tohum-sayisi 5 >> lc_kosu.log 2>&1
echo "[$(date -u +%H:%M)] dilim · $(ls kosular_lc/*_gunluk.json 2>/dev/null|wc -l)/5" >> lc.log
