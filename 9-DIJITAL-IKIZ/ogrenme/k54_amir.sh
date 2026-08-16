#!/bin/bash
# KARAR 54 AMIRI — iki cekirdegi dolu tutar.
# Kosan egitim sureci 2'den azsa, bitmemis ve kilitsiz bir tohum icin isci baslatir.
# Idempotent, tekrar tekrar cagrilabilir. Hicbir tohum iki kez baslatilmaz.
set -u
cd "$(dirname "$0")"
DIZIN=kosular_ince_mufredat
for i in 1 2; do
  N=$(ps aux | grep -c "[e]gitim_v2.py")
  [ "$N" -ge 2 ] && break
  for T in 0 1 2 3 4; do
    [ -f "${DIZIN}/limulus_t${T}_gunluk.json" ] && continue          # bitmis
    ps aux | grep "[e]gitim_v2.py" | grep -q -- "--tohum $T" && continue  # kosuyor
    ( flock -n 9 || exit 1 ) 9>/tmp/k54_t${T}.kilit 2>/dev/null || continue
    setsid nohup ./kampanya_54_isci.sh "$T" > /tmp/k54_isci_t${T}.log 2>&1 < /dev/null &
    disown
    sleep 6
    break
  done
done
ps aux | grep "[e]gitim_v2.py" | grep -o -- "--tohum [0-9]" | tr '\n' ' '
echo
