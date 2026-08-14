#!/bin/bash
# KARAR 47 SONDASI — 2x2 carpan tasarimi, hucre basina iki tohum.
# On kayit 4-KARARLAR/47. Kurallar kosudan once donduruldu.
# ⚠️ Ayri dizine yazar, tamamlanmis kampanyalari EZMEZ (karar 22).
set -u
ADIM=300000
cd "$(dirname "$0")"
kos () {  # hucre log_std0 ince tohum
  local h=$1 ls=$2 ince=$3 t=$4
  local d="kosular_k47/$h"
  mkdir -p "$d"
  LIMULUS_MUFREDAT_INCE=$ince python3 egitim_v2.py \
      --varyant limulus --adim $ADIM --tohum $t \
      --log-std0 $ls --cikti "$d" \
      > "$d/kosu_t$t.log" 2>&1
  echo "  $h tohum $t bitti  rc=$?"
}
# ⚠️ SIRALI KOSULUYOR, PARALEL DEGIL. Olculdu: tek surecte 585 adim/s,
# iki surec paralelde her biri 95 adim/s, yani toplam 190. Torch zaten iki
# cekirdegi kullandigi icin iki surec asiri abone oluyor ve TOPLAM verim
# uc kat DUSUYOR. Sirali kosum 300 bin adimi ~8,5 dakikada bitiriyor,
# sekiz kosu ~70 dakika.
echo "KARAR 47 sondasi basliyor, 8 kosu x $ADIM adim, SIRALI"
for t in 0 1; do
  kos A -1.5 0 $t
  kos B -0.5 0 $t
  kos C -1.5 1 $t
  kos D -0.5 1 $t
done
echo "SONDA BITTI"
