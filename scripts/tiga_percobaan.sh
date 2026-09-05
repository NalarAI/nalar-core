#!/bin/sh
# Tiga percobaan berurutan supaya tidak berebut GPU.
#   1  penuh, tarif resmi, K3 diperluas
#   2  ablasi tabel tarif, untuk menguji dugaan bahwa tabel tarif yang
#      menyebabkan uji keadilan berubah dari gagal menjadi lulus
#   3  ablasi pralatih, untuk menjawab target T4
P="./.venv/Scripts/python.exe -u scripts/percobaan.py"
D="--peserta 20000 --tahun 3 --fktp 900 --fkrtl 150 --batch 128 --d 256 --lapis 8 --kepala 8 --dff 1024"
$P $D --langkah 3000 --keluaran runs/p6_penuh.json          > runs/p6_penuh.log 2>&1
echo "SELESAI 1"
$P $D --langkah 3000 --tarif-cadangan --keluaran runs/p6_ablasi_tarif.json > runs/p6_ablasi_tarif.log 2>&1
echo "SELESAI 2"
$P $D --langkah 30   --keluaran runs/p6_ablasi_pralatih.json > runs/p6_ablasi_pralatih.log 2>&1
echo "SELESAI 3"
