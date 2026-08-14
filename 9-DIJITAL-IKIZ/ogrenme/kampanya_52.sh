#!/bin/bash
# KARAR 52 KAMPANYASI — sirali, kilitli. Once Bolum B (T3 v0, 2x300k),
# sonra Bolum A (iki sondanin bes tohumla tekrari, 40x600k).
# Kural 7: bu betik kosarken baska olcum baslatilmaz.
set -u
cd "$(dirname "$0")"
exec 9>/tmp/kampanya_52.kilit
flock -n 9 || { echo "kilit alinamadi, zaten kosuyor"; exit 1; }
LOG=kampanya_52.log
ts(){ date -u +"%Y-%m-%d %H:%M:%S"; }

# ---------- BOLUM B — T3 kusurlu ortam, 2 x 300k ----------
mkdir -p kosular_t3_v0
for T in 0 1; do
  if [ -f "kosular_t3_v0/limulus_t${T}.pt" ]; then
    echo "$(ts) B atla limulus_t${T} (bitmis)" >> $LOG; continue
  fi
  echo "$(ts) B basla limulus_t${T} (ORTAM_V0)" >> $LOG
  LIMULUS_ORTAM_V0=1 LIMULUS_CRUISE_ITKI=1 \
    python3 egitim_v2.py --varyant limulus --adim 300000 --tohum $T \
    --cikti kosular_t3_v0 >> kosular_t3_v0/kosu_t${T}.log 2>&1
  echo "$(ts) B bitti limulus_t${T} rc=$?" >> $LOG
done
touch kosular_t3_v0/BITTI

# ---------- BOLUM A — iki sonda, 5 tohum ----------
run_sonda(){
  local DIZIN=$1; shift
  mkdir -p $DIZIN
  for V in limulus ikili senkron liftcruise; do
    for T in 0 1 2 3 4; do
      if [ -f "$DIZIN/${V}_t${T}.pt" ]; then
        echo "$(ts) A atla $DIZIN ${V}_t${T} (bitmis)" >> $LOG; continue
      fi
      echo "$(ts) A basla $DIZIN ${V}_t${T}" >> $LOG
      env "$@" python3 egitim_v2.py --varyant $V --adim 600000 --tohum $T \
        --cikti $DIZIN >> $DIZIN/kosu_${V}_t${T}.log 2>&1
      echo "$(ts) A bitti $DIZIN ${V}_t${T} rc=$?" >> $LOG
    done
  done
  touch $DIZIN/BITTI
}
run_sonda kosular_esik_sonda600_s5 LIMULUS_IRTIFA_TABAN=1 LIMULUS_CRUISE_ITKI=1
run_sonda kosular_esik_gamma999_s5 LIMULUS_IRTIFA_TABAN=1 LIMULUS_CRUISE_ITKI=1 LIMULUS_GAMMA=0.999
echo "$(ts) KAMPANYA 52 TAMAM" >> $LOG
touch KAMPANYA_52_BITTI
