#!/bin/bash
# KARAR 54, ISCI BETIGI — konteynerde iki cekirdek var, iki kosu YAN YANA koşar.
#
# Kullanim:  ./kampanya_54_isci.sh "1 3"     ./kampanya_54_isci.sh "2 4"
#
# Her tohumun KENDI kilidi vardir, ayni tohum iki kez baslatilamaz.
# Kurgu degismedi, yalnizca zamanlama degisti. Her kosu ayri surectir, kendi
# tohumunu ve kendi cikti dosyalarini kullanir, paylasilan durum yoktur.
set -u
cd "$(dirname "$0")"
TOHUMLAR="$1"
DIZIN=kosular_ince_mufredat
LOG=kampanya_54.log
YEDEK=/home/user/k54_yedek
ts(){ date -u +"%Y-%m-%d %H:%M:%S"; }
mkdir -p "$DIZIN" "$YEDEK"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1

for T in $TOHUMLAR; do
  if [ -f "${DIZIN}/limulus_t${T}.pt" ]; then
    echo "$(ts) atla limulus_t${T} (bitmis)" >> $LOG; continue
  fi
  exec 8>/tmp/k54_t${T}.kilit
  flock -n 8 || { echo "$(ts) t${T} kilitli, atlandi" >> $LOG; continue; }
  echo "$(ts) basla limulus_t${T}" >> $LOG
  LIMULUS_CRUISE_ITKI=1 LIMULUS_MUFREDAT_INCE=1 \
  python3 egitim_v2.py --varyant limulus --adim 3000000 \
    --tohum $T --log-std0 -0.5 --cikti "$DIZIN" \
    >> "${DIZIN}/kosu_limulus_t${T}.log" 2>&1
  echo "$(ts) bitti limulus_t${T} rc=$?" >> $LOG
  tar czf "${YEDEK}/k54_t${T}.tgz" -C . \
      "${DIZIN}/limulus_t${T}.pt" "${DIZIN}/limulus_t${T}_gunluk.json" \
      "${DIZIN}/kosu_limulus_t${T}.log" 2>/dev/null
  echo "$(ts) yedek k54_t${T}.tgz" >> $LOG
  flock -u 8
done

# Bes kosu da bittiyse bayrak
if [ "$(ls ${DIZIN}/*_gunluk.json 2>/dev/null | wc -l)" -ge 5 ]; then
  tar czf "${YEDEK}/k54_tamami.tgz" -C . "$DIZIN" 2>/dev/null
  echo "$(ts) KAMPANYA 54 TAMAM" >> $LOG
  touch KAMPANYA_54_BITTI
fi
