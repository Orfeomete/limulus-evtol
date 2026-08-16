#!/bin/bash
# KARAR 54 KAMPANYASI — ince mufredat, geniz kesif kolunda, tek varyant.
#
#   Varyant  limulus (yalniz)          Tohum  0-4
#   Adim     3.000.000 / kosu          Toplam 15M adim, 5 kosu
#   Bayrak   LIMULUS_MUFREDAT_INCE=1   (7 seviye, gecis_yarim indeks 2'de)
#            LIMULUS_CRUISE_ITKI=1     F1 ve F2 KAPALI (ontanim)  gamma 0,99
#   Kesif    --log-std0 -0.5           karar 53 ile AYNI, tek degisken kurali
#
# Karsilastirma tabani kosular_genis_kesif/limulus_t{0..4} (karar 53), yeniden kosulmaz.
# Yeniden baslatilabilir, biten kosuyu atlar. Kilitli, iki kopya ayni anda kosamaz.
set -u
cd "$(dirname "$0")"
exec 9>/tmp/kampanya_54.kilit
flock -n 9 || { echo "kilit alinamadi, kampanya zaten kosuyor"; exit 1; }

DIZIN=kosular_ince_mufredat
LOG=kampanya_54.log
YEDEK=/home/user/k54_yedek
ts(){ date -u +"%Y-%m-%d %H:%M:%S"; }
mkdir -p "$DIZIN" "$YEDEK"

export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1

echo "$(ts) KAMPANYA 54 BASLADI  ince mufredat  limulus  tohum 0-4" >> $LOG

for T in 0 1 2 3 4; do
  if [ -f "${DIZIN}/limulus_t${T}.pt" ]; then
    echo "$(ts) atla limulus_t${T} (bitmis)" >> $LOG
    continue
  fi
  echo "$(ts) basla limulus_t${T}" >> $LOG
  LIMULUS_CRUISE_ITKI=1 LIMULUS_MUFREDAT_INCE=1 \
  python3 egitim_v2.py --varyant limulus --adim 3000000 \
    --tohum $T --log-std0 -0.5 --cikti "$DIZIN" \
    >> "${DIZIN}/kosu_limulus_t${T}.log" 2>&1
  RC=$?
  echo "$(ts) bitti limulus_t${T} rc=${RC}" >> $LOG
  # Her kosudan sonra kucuk bir yedek, konteyner geri alinirsa kopyalanacak sey hazir olsun.
  tar czf "${YEDEK}/k54_t${T}.tgz" -C . \
      "${DIZIN}/limulus_t${T}.pt" \
      "${DIZIN}/limulus_t${T}_gunluk.json" \
      "${DIZIN}/kosu_limulus_t${T}.log" 2>/dev/null
  echo "$(ts) yedek k54_t${T}.tgz" >> $LOG
done

tar czf "${YEDEK}/k54_tamami.tgz" -C . "$DIZIN" 2>/dev/null
echo "$(ts) KAMPANYA 54 TAMAM" >> $LOG
touch KAMPANYA_54_BITTI
