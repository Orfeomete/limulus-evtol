#!/bin/bash
# Zamanlanmis gorevin cagirdigi surdurucu.
# Ara kayit sayesinde her kesinti kaldigi yerden devam eder.
# ⚠️ KILIT ZORUNLU (04.08.2026, bkz. 4-KARARLAR/30). Kilitsiz surumde
# ikinci dilim birincisi bitmeden baslayabiliyor ve iki surec ayni
# *_ara.pt dosyasina yaziyor. Sonra baslayan ESKI durumu kaydedip
# ilerlemeyi sessizce geri aliyor.
cd "$(dirname "$0")"

exec 9>/tmp/limulus_v2.kilit
if ! flock -n 9; then
    echo "[$(date -u +%H:%M)] ATLANDI · dilim zaten kosuyor" >> devam.log
    exit 0
fi
export LIMULUS_KOSU_DIZINI=kosular_v2 LIMULUS_EGITIM=egitim_v2.py
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
n=$(ls kosular_v2/*_gunluk.json 2>/dev/null | wc -l)
echo "[$(date -u +%H:%M)] gece · $n/20" >> devam.log
[ "$n" -ge 20 ] && { echo "[$(date -u +%H:%M)] 20/20 BITTI" >> devam.log; exit 0; }
timeout "${1:-540}" python3 deney.py --adim 1000000 --tohum-sayisi 5 --isci 2 >> tam_kosu_v2.log 2>&1
echo "[$(date -u +%H:%M)] dilim bitti · $(ls kosular_v2/*_gunluk.json 2>/dev/null|wc -l)/20" >> devam.log
