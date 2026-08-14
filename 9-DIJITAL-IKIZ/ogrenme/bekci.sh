#!/bin/bash
# KOSU BEKCISI — deney.py iki kez sessizce oldurulunce yazildi.
# deney.py zaten tamamlanmis kosulari atliyor, dolayisiyla yeniden
# baslatmak en fazla yarim kalan tek kosuyu tekrarlatir.
cd "$(dirname "$0")"
export LIMULUS_KOSU_DIZINI=kosular_v2 LIMULUS_EGITIM=egitim_v2.py
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
HEDEF=20
for deneme in $(seq 1 40); do
  n=$(ls kosular_v2/*_gunluk.json 2>/dev/null | wc -l)
  if [ "$n" -ge "$HEDEF" ]; then
    echo "[bekci] $HEDEF kosunun hepsi tamam, cikiliyor." >> bekci.log
    break
  fi
  echo "[bekci] deneme $deneme · $n/$HEDEF tamam · deney.py baslatiliyor $(date -u +%H:%M)" >> bekci.log
  python3 deney.py --adim 1000000 --tohum-sayisi 5 --isci 2 >> tam_kosu_v2.log 2>&1
  echo "[bekci] deney.py cikti, kod $? · $(ls kosular_v2/*_gunluk.json 2>/dev/null|wc -l)/$HEDEF $(date -u +%H:%M)" >> bekci.log
  sleep 5
done
