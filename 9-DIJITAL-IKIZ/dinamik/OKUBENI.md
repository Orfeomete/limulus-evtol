# 9-DIJITAL-IKIZ / dinamik

Kısım II'nin fizik katmanı. Python tabanlı 6-DOF dinamik motor.

## Araç kararı

Pekiştirmeli öğrenme eğitimi **Unity üzerinden geçmez**. Yüksek lisans tezinde Unity zorunluydu
çünkü ajanın algısı görsel ve ışın-tabanlıydı. Burada gözlem bir durum vektörüdür, dolayısıyla
Python içinde eğitim 50-100 kat hızlıdır ve fizik denetlenebilir kalır. Unity, dijital ikizin
sunum katmanı olarak kalır. Bu ayrım bilimsel katkıyı araçtan bağımsız hale getirir.

## Dosyalar

| Dosya | Ne |
|---|---|
| `limulus_dynamics.py` | 6-DOF çekirdek. Durum 12, kontrol 8 (4 itki + 4 tilt). `KONF` sözlüğü Rev. D değerlerini, `VARSAYIMLAR` sözlüğü tezde bulunmayıp modelde ilk kez tanımlanan beş değeri taşır. |
| `trim.py` | Trim çözücü ve tezin sayılarıyla çapraz doğrulama. Çıktısı `trim_ciktisi.txt`. |

## İki ayrı x ekseni var, karıştırma

```
x_ist   "istasyon"   burun x=0, geriye artar     geometri.py ve tez bu ekseni kullanır
x_b     "gövde"      CG x=0, İLERİYE artar       dinamik denklemler bu ekseni kullanır
donusum x_b = x_cg − x_ist        ->  Limulus.govde_x()
```

v0.1'de bu dönüşüm atlanmıştı ve yunuslama momentlerinin işareti tersti. `trim.py` §0'daki işaret
birim testi bunu yakaladı ve dosyada kalıcı olarak duruyor. Modele yeni bir kuvvet eklenirken
önce o test koşulur.

## Modelin doğrulanma durumu

Tezin iki bağımsız sonucunu birebir üretiyor.

| Büyüklük | Model | Tez |
|---|---|---|
| Hover gücü | 913,8 kW | 913 kW |
| OEI kaldırma oranı (simetrik kabul) | %90,7 | %90,7 |
| Cruise C_L | 0,767 | 0,78 |
| Cruise L/D | 16,06 | 16,1 |

Aynı model boyuna moment dengesini hiçbir rejimde kapatamadı. Dört bulgu:
`4-KARARLAR/10-dinamik-model-bulgulari.md`.

## Çalıştırma

```bash
python3 trim.py
```

Bağımlılık: numpy, scipy. Tezden hiçbir sayı elle kopyalanmaz, hepsi `KONF` üzerinden gelir.

## Sıradaki

Fizik katmanının kalan parçaları F1-F4 kararı verildikten sonra kurulur — integratör, aktüatör ve
sensör modelleri, atmosfer ve gust, Gymnasium sarmalayıcı, Unity köprüsü. Trim edilemeyen bir
konfigürasyon simüle edilmez.
