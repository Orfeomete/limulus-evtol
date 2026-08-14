#!/bin/bash
# KARAR 53 KAMPANYASI — genis kesif, log_std0 = -0,5, 20 x 3M, sirali, kilitli.
# Bayraklar: LIMULUS_CRUISE_ITKI=1, F1 ve F2 KAPALI (ontanim), gamma 0,99.
set -u
cd "$(dirname "$0")"
exec 9>/tmp/kampanya_53.kilit
flock -n 9 || { echo "kilit alinamadi"; exit 1; }
LOG=kampanya_53.log
ts(){ date -u +"%Y-%m-%d %H:%M:%S"; }
mkdir -p kosular_genis_kesif
for V in limulus ikili senkron liftcruise; do
  for T in 0 1 2 3 4; do
    if [ -f "kosular_genis_kesif/${V}_t${T}.pt" ]; then
      echo "$(ts) atla ${V}_t${T} (bitmis)" >> $LOG; continue
    fi
    echo "$(ts) basla ${V}_t${T}" >> $LOG
    LIMULUS_CRUISE_ITKI=1 python3 egitim_v2.py --varyant $V --adim 3000000 \
      --tohum $T --log-std0 -0.5 --cikti kosular_genis_kesif \
      >> kosular_genis_kesif/kosu_${V}_t${T}.log 2>&1
    echo "$(ts) bitti ${V}_t${T} rc=$?" >> $LOG
  done
done
echo "$(ts) KAMPANYA 53 TAMAM" >> $LOG
touch KAMPANYA_53_BITTI
