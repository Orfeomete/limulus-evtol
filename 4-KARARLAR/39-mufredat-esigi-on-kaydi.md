# 39 — Müfredat eşiği incelemesi ön kaydı: eşik suçsuz çıktı, kusur ödül tanımında

**Tarih:** 08.08.2026 · **Sınıf:** **ön kayıt**, koşu sonucu görülmeden yazıldı
**Statü:** ⏸️ **onay bekliyor** (Mete). Aşama 1 teşhisi tamam, Aşama 2 koşusu onayla başlar
**Teşhis betiği:** `9-DIJITAL-IKIZ/testler/dogrulama_mufredat_esigi.py`
**Öncül:** karar `38` bekleyen kalem "müfredat eşiği incelemesi (gevşetilmiş eşikle)"

---

## Bu belge neden bu hâlde

Karar 38 bekleyen kalemi "gevşetilmiş eşikle bir koşu" diye yazmıştı. Bu belge o koşuyu
tarif etmek için açıldı. Koşuyu tarif etmeden önce kapının kendisi ölçüldü ve **reçetenin
yanlış hastalığa yazıldığı görüldü.** Ön kayıt bu yüzden gevşetilmiş eşik koşusunu değil,
ölçülen kusurun düzeltilmesini önerir.

Aşağıdaki teşhis sayılarının tamamı **var olan yapıtlardan ve dondurulmuş sabitlerden**
gelir. Yeni bir eğitim koşusu yapılmadı. Kaynak, `kosular_uzun/` günlükleri, `kosular_uzun/`
politika ağırlıkları, `ortam.py` ödül tanımı ve `egitim_v2.py` hiperparametreleridir.

---

## Aşama 1 — teşhis, dört ölçüm

### A0. Kapı aynı zamanda bir hayatta kalma kapısıdır

Bölüm ödülü, bölümün **azami** uzunluğuna bölünerek normalize edilir
(`egitim_v2.py`, `bolum_odul / n_azami`). Adım başına ödül üstsınırı 2,50 ve çökme cezası
100,0 olduğuna göre, çökmeyle biten bir bölümde toplam ödül en çok `2,50 n − 100` olabilir.
Kapıyı geçmek için gereken alt sınır kapalı formda çıkar.

| Seviye | Görev | Azami adım | Gereken adım | Hayatta kalma payı |
|---|---|---:|---:|---:|
| 0 | hover | 1000 | 300 | %30,0 |
| 1 | dikey | 1250 | 365 | %29,2 |
| 2 | geçiş | 2000 | 560 | %28,0 |
| 3 | cruise | 2000 | 560 | %28,0 |
| 4 | gust geçiş | 2000 | 560 | %28,0 |
| 5 | OEI hover | 1250 | 365 | %29,2 |

Bu pay, izleme **mükemmel** olsa bile gereken alt sınırdır. Yani 0,65 eşiği bir izleme
ölçüsü değil, izleme ile hayatta kalmanın çarpımıdır.

### A1. Eylem uzayının tilt erişimi ankrajla sınırlıdır

Eylemler trim ankrajına göre artımsaldır (karar `15`, T1 düzeltmesi) ve ankraj bölümün
**başlangıç** koşulunda bir kez hesaplanır. Tilt komutu `ankraj ± 30°` ile sınırlıdır.

| Seviye | Başlangıç hızı | Ankraj tilt | Erişilebilir tilt | Cruise 85° erişilir mi |
|---|---:|---:|---:|---|
| 0 hover | 0 m/s | 0,0° | 0,0 – 30,0° | hayır |
| 1 dikey | 0 m/s | 0,0° | 0,0 – 30,0° | hayır |
| 2 geçiş | 0 m/s | 0,0° | 0,0 – 30,0° | **hayır** |
| 3 cruise | 60 m/s | 90,0° | 60,0 – 90,0° | evet |
| 4 gust geçiş | 0 m/s | 0,0° | 0,0 – 30,0° | **hayır** |
| 5 OEI hover | 0 m/s | 0,0° | 0,0 – 30,0° | hayır |

Geçiş görevi hover'da başladığı için politika bölüm boyunca 30 dereceden fazla tilt
komutu veremez. Bu bir sınırdır, tek başına bir kusur değildir, çünkü taban
kontrolcü aynı sınır altında görevi tamamlıyor (A2).

### A2. Taban kontrolcü kapıyı geçiyor, yani kapı ulaşılabilir

Kaskad PID kontrolcü öğrenmeden bağımsız bir yetkinlik referansıdır. Aynı ortamda, aynı
artımsal eylem uzayından sürüldü ve normalize ödülü ölçüldü.

| Seviye | limulus | ikili | senkron | lift+cruise | Hayatta kalma (tilt varyantları) |
|---|---:|---:|---:|---:|---|
| 0 hover | 2,065 | 2,065 | 2,065 | 2,065 | %100 |
| 1 dikey | 1,551 | 1,549 | 1,548 | 1,545 | %100 |
| **2 geçiş** | **0,859** | **0,866** | **0,877** | −0,160 | **%100** |
| 3 cruise | 0,477 | 0,349 | 1,621 | 1,527 | kısmi |
| 4 gust geçiş | 0,955 | 0,976 | 0,970 | −0,202 | %100 |
| 5 OEI hover | 0,345 | 0,345 | 0,345 | 0,345 | %22 |

Seviye 2'de üç tilt varyantının tabanı kapıyı **geçiyor** (0,86–0,88 karşılığında eşik
0,65) ve bölümün tamamını tamamlıyor. Komutlarının %81'i eylem uzayı tarafından kırpılmasına
rağmen. **Kapı ulaşılabilirdir, dolayısıyla kapı kusurlu değildir.**

### A3. Eğitilmiş politikaların tamamı yere çarpıyor

Kırk bölüm, dört varyant, beş tohum, 3M politikalar, deterministik değerlendirme,
seviye 2.

| Varyant | Normalize ödül | Bölüm uzunluğu | Hayatta kalma payı | Sonlanma |
|---|---:|---:|---:|---|
| limulus | 0,136 – 0,143 | 536 | %27 | 5/5 yere çarpma |
| ikili | 0,114 – 0,139 | 490 – 536 | %24 – 27 | 5/5 yere çarpma |
| senkron | −0,363 – 0,137 | 478 – 536 | %24 – 27 | 5/5 yere çarpma |
| lift+cruise | 0,131 – 0,135 | 536 | %27 | 5/5 yere çarpma |

**40 bölümün 40'ı yere çarpmayla bitiyor** ve bölüm uzunluğu dört mimaride birbirinin
aynı. Seviye 4'e ulaşan tek politika (senkron t2) da çarpıyor, farkı daha dik dalıp
çarpmadan önce 55 m/s'ye ulaşmasıdır.

---

## Kusur — T4, irtifa ödülünün ölü bölgesi

İrtifa hatası sabit bir 50 m ölçeğiyle normalize edilir, `e_irt = |h − h_hedef| / 50`, ve
ödüle `exp(−e_irt²)` olarak girer. Görevlerin başlangıç irtifa hatası şudur.

| Seviye | Başlangıç irtifa | Hedef | Hata | İrtifa terimi |
|---|---:|---:|---:|---:|
| 0 hover | 100 m | 100 m | 0 m | 1,00 |
| 1 dikey | 100 m | 150 m | 50 m | 0,37 |
| **2 geçiş** | 150 m | 300 m | 150 m | **1,2 × 10⁻⁴** |
| 3 cruise | 300 m | 300 m | 0 m | 1,00 |
| **4 gust geçiş** | 150 m | 300 m | 150 m | **1,2 × 10⁻⁴** |
| 5 OEI hover | 100 m | 100 m | 0 m | 1,00 |

**Ölü bölge tam olarak iki seviyede var ve o iki seviye, Kısım III'ü tıkayan iki
seviyedir.** Seviye 2, 19/20 koşunun platoya oturduğu duvar. Seviye 4, bozucu reddi
ekseninin hiçbir kampanyada ölçülemediği seviye (karar `28`, `38`).

### Mekanizma, tek bir bölümde ölçüldü

limulus t0 politikası, seviye 2, deterministik.

| t (s) | İrtifa | Hız | Tilt | Takip ödülü | Adım ödülü |
|---:|---:|---:|---:|---:|---:|
| 0,02 | 150,0 m | 0,0 m/s | 0,2° | 0,868 | +0,629 |
| 3,62 | 129,2 m | 11,4 m/s | 0,0° | 0,881 | +0,717 |
| 7,22 | 73,3 m | 19,2 m/s | 0,0° | 0,918 | +0,733 |
| 9,62 | 24,3 m | 22,0 m/s | 0,0° | 0,927 | +0,733 |
| 10,74 | −0,4 m | 22,9 m/s | 0,0° | 0,927 | −99,270 |

Araç düşerken **takip ödülü yükseliyor.** İrtifa terimi baştan sıfırda olduğu için
alçalmanın ödülde karşılığı yok, hız terimi ise alçalmayla birlikte iyileşiyor. Politika
tilt kanalına hiç dokunmuyor, yalnız yavaşça öne düşüyor.

### Düşmek ödül-optimal

İndirim katsayısı 0,99. Beş yüz otuz yedi adım boyunca adım başına +0,73 birikimi
indirimli olarak 72,7 değerinde. Aynı ufukta çökme cezasının indirimli değeri 0,45, yani
**toplam getirinin %0,6'sı.** Politika açısından dalmak neredeyse bedelsizdir.

---

## Reçete neden değişti

Karar 38'in yazdığı reçete "eşiği gevşet" idi. Ölçüm şunu gösteriyor.

- Eşik ulaşılabilir, taban kontrolcü 0,86 ile geçiyor.
- Politikaların 0,14'te kalması izleme başarısızlığı değil, **hayatta kalma**
  başarısızlığı. Adım başına takip ödülleri 0,73, bölümün yalnız %27'sini yaşıyorlar.
- Eşik 0,14'ün altına indirilse ne olurdu. Yere çarpan politikalar seviye 3'e terfi
  ederdi. Karar 38 bunun sonucunu zaten ölçtü, seviye 4'e terfi eden tek politika gust
  altında geçişi 0/8 tamamladı. **Terfi yetkinlik değildir.**

Bu yüzden ön kayıt eşiğe dokunmaz. Eşik **0,65'te dondurulmuş kalır** ve karar 12 §4'ün
kuralı korunur.

---

## Aşama 2 — ön kayıtlı düzeltme, yalnız bir kalem

| # | Değişiklik | Gerekçe | Hipotezle ilgisi |
|---|---|---|---|
| **F1** | İrtifa hatası ölçeği, görevin **başlangıç hatasıyla** tabanlanır. `e_irt = \|h − h_hedef\| / max(50, \|h_0 − h_hedef\|)` | Ölü bölge yapısal olarak kalkar. Başlangıçta terim 0,37 olur ve araç hedefe yaklaştıkça sıkışır. Elli metre ölçeği alt sınır olarak kalır, hover ve cruise hassasiyeti değişmez | yok, dört varyantı aynı biçimde etkiler |

**Neden bu biçim.** Üç aday vardı. Ölçeği topluca büyütmek (50 metreden 150 metreye) hover ve cruise
hassasiyetini de bozardı. Potansiyel tabanlı ödül şekillendirmesi teorik olarak daha
temiz ama ödüle yeni bir terim ekler ve 0,65 eşiğinin ölçeğini kaydırır. F1 her terimi
`[0, 1]` aralığında bırakır, yeni katsayı getirmez ve ölü bölgeyi her seviyede kaldırır.

### Değişmeyecekler, bilerek donduruldu

- **Müfredat eşiği 0,65.**
- Müfredatın altı seviyesi, sıralaması, süreleri ve hedefleri.
- Diğer bütün ödül ağırlıkları, çökme cezası 100 dahil.
- Eylem uzayı, trim ankrajı, KT_YETKI ve KTH_YETKI.
- PPO hiperparametreleri, tohum seti, gözlem normalizasyonu.
- Fizik modelinin hiçbir parametresi. Eklem cezası 28 kN'da kalır.
- `LIMULUS_CRUISE_ITKI=1`, yani lift+cruise 180 kW itici birimle koşar.

### Çökme cezasının indirimi — bu ön kaydın DIŞINDA

Çökmenin toplam getiriye oranının %0,6 çıkması ikinci bir aday kusurdur. **Bu ön kayıt
ona dokunmaz.** F1 tek başına çarpmayı durdurmazsa, sonlanma cezası ölçeği ayrı bir ön
kayıtla ele alınır. Bir turda bir değişken.

---

## Karar kuralları, sonuç görülmeden sabitlendi

1. **Aşama 2a, git/gitme sondası.** 4 varyant × 1 tohum × 300.000 adım, dizin
   `kosular_esik_sonda/`. Tek soru, seviye 2 bölümleri yere çarpmayı bırakıyor mu.
   - Dört varyantta da hayatta kalma payı %28'in üstüne çıkarsa Aşama 2b'ye geçilir
   - Çıkmazsa F1 yetersiz ilan edilir, kayıt olarak kalır ve yeni ön kayıt açılır.
     **Aşama 2b bu durumda koşulmaz.**
2. **Aşama 2b, tam kampanya.** 4 varyant × 5 tohum × 1.000.000 adım, dizin
   `kosular_esik/`. Ayrı dizin kuralı karar `22`.
3. **İç içe geçmişlik.** Karar 12 §5/1 aynen geçerli. LIMULUS senkron tiltten anlamlı
   biçimde kötü çıkarsa bu mimari bulgu değil eniyileme kusurudur.
4. **Anlamlılık.** Fark, beş tohumun standart sapmasının iki katından küçükse **fark yok**
   yazılır.
5. **Terfi yetkinlik değildir.** Bir politika seviye 4'e ulaşırsa bozucu reddi ekseni
   karar 28'in düzeltilmiş metriğiyle ayrıca ölçülür. Terfi tek başına ölçüm sayılmaz.
6. **Dondurulmuş kampanyalar raporda kalır.** `kosular_v2` ve `kosular_uzun` sonuçları
   mimari karşılaştırmasının **kayıtlı sonucudur** ve silinmez. Düzeltilmiş kampanya
   onların yerine geçmez, yanına **ayrı bölüm** olarak girer ve hangi ödül tanımıyla
   üretildiği her tabloda yazılır. İki set hiçbir tabloda karıştırılmaz.
7. **Veri denetimi** karar 30 protokolüyle yapılır. Adım sayısı, kayıt sayısı, tek yönlü
   artış.
8. Koşu bitmeden hiçbir ara sonuç tez metnine girmez.

---

## Mevcut sonuçlara etkisi — neyin geçerli kaldığı

| Sonuç kümesi | Durum | Gerekçe |
|---|---|---|
| Politikadan bağımsız beş metrik (trim zarfı, geçiş koridoru, arıza toleransı, enerji, asimetrik trim) | ✅ **etkilenmedi** | Trim çözücüden gelir, öğrenmeye hiç girmez |
| Tasarım noktası, menzil, kütle, yapı, itki | ✅ **etkilenmedi** | Ödül tanımıyla ilgisi yok |
| Öğrenme ekseni "fark yok" sonucu | ⚠️ **yeniden yorumlanmalı** | Dört varyant da aynı dalış davranışına yakınsıyor. Ölçülen şey mimari değil, ödülün ortak kusuru |
| Öğrenme verimi ekseni | ⚠️ **yeniden yorumlanmalı** | 0,5 eşiğine ulaşma adımı, aynı dalış rejiminde ölçüldü |
| A2 bozucu reddi "ölçülemedi" | ✅ **sonuç ayakta, gerekçesi netleşti** | Nedeni bütçe değil, seviye 4'ün ölü bölgesi |
| F2 tilt kanalı ablasyonu | ⚠️ **kısmen** | Politikalar tilt kanalına hiç dokunmuyor. Kanalın kullanılmaması bulgusu ayakta, ama nedeni mimari değil ödül olabilir |
| Kararlılık hipotezi | ⏸️ **beklemede** | Aynı ödülle ölçülen varyans, düzeltmeden sonra yeniden ölçülmeli |

**Tezde ne yapılacak.** Aşama 2a sonucundan önce tez metnine dokunulmaz. Kurala uyulur,
koşu bitmeden ara sonuç girmez. Aşama 2a olumlu çıkarsa Kısım III'e T4 kaydı
`sec:ortam-duzeltmeleri` desenine göre eklenir, T1-T3 nasıl yazıldıysa öyle.

---

## Yürütme ve maliyet

Ölçülen hız, uzun kampanyanın dilim defterinden, iki işçiyle ~770 çevre adımı/s.

| Aşama | Kurgu | Adım | Tahmini süre |
|---|---|---:|---:|
| 2a sonda | 4 × 1 × 300k | 1,2M | ~30 dk |
| 2b kampanya | 4 × 5 × 1M | 20M | ~7,5 saat |

Bekçi protokolü v2 uygulanır. İki dakikada kendini yeniden kuran `send_later` zinciri,
dilim başına 5 × 580 s bash uykusu ve `pgrep 'egitim_v2.p[y] --varyant'` deseni. Köşeli
parantez öz-eşleşmeyi önler, v1'deki 66 dakikalık kayıp bundandı.

---

## Bu kayıtla açılan yeni kalemler

1. **Seviye 3 cruise, taban kontrolcü bağımsız tiltte tamamlayamıyor** (limulus 0,477 ·
   ikili 0,349 · senkron 1,621). Cruise ankrajında itki bandı ±%35 ve cruise itkisi
   hover'ın %6'sı olduğu için dikey otorite dar. İncelenmeli, bu ön kaydın dışında.
2. **Seviye 5 OEI, taban kontrolcü 280 adımda tutum sınırını aşıyor.** Taban kontrolcü
   OEI için ayarlanmadı, yine de kaydedilir.
3. **Çökme cezasının indirim altında görünmezliği** (%0,6). Ayrı ön kayıt konusu.
4. **Eylem uzayının ankraj erişimi** (A1). Geçiş görevinde 30 derece tavan var ve taban
   kontrolcü komutlarının %81'i kırpılıyor. Kusur olarak açılmadı çünkü taban görevi bu
   sınır altında tamamlıyor, ancak öğrenme için zorluk kaynağı olabilir.

---

*Kayıt 08.08.2026 · Teşhis `9-DIJITAL-IKIZ/testler/dogrulama_mufredat_esigi.py` ·
İlgili `12`, `15`, `22`, `28`, `30`, `36`, `38` · Protokol `LIMULUS_ELESTIRI_PROTOKOLU.md`*

---

## ✅ BAŞLATILDI — 08.08.2026 00 39 UTC (Mete onayı), Aşama 2a

Betik `9-DIJITAL-IKIZ/ogrenme/esik_sonda.sh`, dizin `kosular_esik_sonda/`, bayraklar
`LIMULUS_CRUISE_ITKI=1` ve `LIMULUS_IRTIFA_TABAN=1`. Bekçi protokolü v2 kuruldu, iki dakikada
kendini yeniden kuran `send_later` zinciri. Ölçülen hız iki işçiyle ~700 çevre adımı/s.

F1 bayrağının regresyon denetimi başlatmadan önce yapıldı. Bayrak kapalıyken irtifa ölçeği
altı seviyenin hepsinde 50 metre, yani donmuş kampanyaların davranışı korunuyor. Bayrak
açıkken yalnız seviye 2 ve seviye 4 değişiyor, ölçek 150 metre oluyor ve başlangıç irtifa
terimi 1,2 × 10⁻⁴ değerinden 0,368'e çıkıyor. Seviye 0, 1, 3 ve 5 dokunulmadan kalıyor.

## TADİLAT 1 — 08.08.2026, sonda sürerken, sonuç görülmeden

Bu belge "belgede yazılmayan hiçbir değişiklik yapılmayacaktır, yapılırsa buraya tarihiyle
eklenecektir" disiplinine karar 12'den devrediyor. Bir gözlem çıktı ve buraya ekleniyor.

**Gözlenen.** Sondanın ilk iki koşusu (limulus t0 ve ikili t0) 300 bin adımı tamamladı ve
ikisi de müfredatın **birinci seviyesinde** bitti, ikinci seviyeye ulaşmadı. Donmuş
kampanyada ikinci seviyeye ulaşma adımı 149 bin ile 354 bin arasındaydı, dolayısıyla bu
aralığın içinde bir sonuçtur, gecikme değildir.

**Sonucu.** Sondanın sorusu ikinci seviyedeki hayatta kalmadır. Eğitim ikinci seviyeye
ulaşmadıysa, o seviyedeki değerlendirme **dağılım dışıdır** ve zayıf bir işarettir.

**Önceden konan kural.** Sonda bittiğinde dört koşunun ulaştığı seviye raporlanır ve
okuma buna göre yapılır.

- Dördü de ikinci seviyeye ulaştıysa, karar kuralı 1 doğrudan uygulanır.
- Ulaşamayan koşu varsa, o koşuların ikinci seviye değerlendirmesi **dağılım dışı** olarak
  işaretlenir ve sonda **sonuçsuz** ilan edilir. Bu durumda tek düzeltme, bütçenin 300
  binden 600 bine çıkarılmasıdır. Gerekçesi tamamen terfi zamanlamasıdır, ikinci seviyedeki
  hayatta kalma sonucuna bakılmamıştır ve bakılmadan yazılmıştır.
- Bütçe artırımı dışında hiçbir ayar değişmez. F1, eşik 0,65, ödül ağırlıkları, eylem uzayı
  ve hiperparametreler dondurulmuş kalır.

**Bu tadilat yazılırken elde olan.** İki koşunun tamamlandığı, ikisinin de seviye 1'de
bittiği ve senkron ile lift+cruise koşularının sürdüğü bilgisi. Hiçbir ikinci seviye
değerlendirmesi yapılmamıştı.

---

## AŞAMA 2A SONUCU — 08.08.2026 01 09 UTC, sonda 4/4 tamamlandı

**Veri denetimi (karar 30 protokolü): 4/4 GEÇTİ.** Her koşu 147 kayıt, son adım 301.056,
adım sayacı tek yönlü artıyor.

### Eğitimin ulaştığı seviye

| Koşu | Son seviye | Seviye 2'ye varış |
|---|---:|---:|
| limulus t0 | 1 | ulaşmadı |
| ikili t0 | 1 | ulaşmadı |
| senkron t0 | **2** | 202.752 |
| lift+cruise t0 | **2** | 161.792 |

Dördün ikisi eğitimde ikinci seviyeye ulaşmadı. **Tadilat 1'in koşulu oluştu.**

### Seviye 2 değerlendirmesi, deterministik, üç bölüm

| Varyant | Donmuş 3M | F1 sondası | Eğitim seviyesi | Normalize ödül | Sonlanma | Okuma |
|---|---:|---:|---:|---:|---|---|
| limulus | %27 | %13 | 1 | −0,010 | tutum sınırı | **dağılım dışı** |
| ikili | %26 | %8 | 1 | −0,123 | tutum sınırı | **dağılım dışı** |
| senkron | %26 | **%48** | 2 | **+0,393** | yere çarpma | eşik üstü |
| lift+cruise | %27 | **%44** | 2 | **+0,381** | yere çarpma | eşik üstü |

### Karar kuralı 1 uygulanıyor

Kural, **dört varyantta da** hayatta kalma payının %28'in üstüne çıkmasını istiyor. İki
varyantta çıktı, iki varyantta çıkmadı. Çıkmayan ikisi eğitimde ikinci seviyeyi görmediği
için değerlendirmeleri dağılım dışıdır ve yetkinlik ölçüsü sayılmaz.

> **Sonda SONUÇSUZ.** Kural 1 ne sağlandı ne çürütüldü. Tadilat 1 gereği tek düzeltme,
> bütçenin 300 binden 600 bine çıkarılmasıdır.

### Dağılım içi işaret, kayda geçiyor

Eğitimde ikinci seviyeyi gören iki koşuda F1 açıkken şu değişti.

- Hayatta kalma payı %26 ile %27 bandından **%44 ile %48** bandına çıktı, yani yaklaşık
  **1,7 kat**.
- Normalize ödül 0,13 mertebesinden **0,38 mertebesine** çıktı, yani yaklaşık **üç kat**.
- Bölüm uzunluğu, donmuş kampanyanın dört mimaride birbirinin aynı çıkan 536 adımlık
  değerinden **872 ve 968 adıma** çıktı. Donmuş kampanyada yirmi koşunun yirmisi 478 ile
  536 arasına toplanmıştı, bu tekdüzelik kırıldı.

**Bu işaret olumlu, ama kural gereği sonuç sayılmıyor.** İki koşu, iki varyant ve tek tohumdur.
Ayrıca ikisi de hâlâ yere çarpıyor ve ikisi de 0,65 kapısının altında. F1'in çarpmayı
tamamen durdurup durdurmadığı, ancak dört varyantın da ikinci seviyede gerçekten eğitildiği
bir sondayla söylenebilir.

### Sıradaki adım, Mete onayına bağlı

Bütçe 600 bine çıkarılıp sonda tekrarlanır. Kurgu 4 varyant × 1 tohum × 600.000 adım, dizin
`kosular_esik_sonda600/`, tahmini süre bir saat. F1, eşik 0,65, ödül ağırlıkları, eylem uzayı
ve hiperparametreler dondurulmuş kalır. Bütçe dışında hiçbir ayar değişmez.

**Tez metnine dokunulmadı.** Mete'nin 08.08.2026 kararı gereği sonda kesin sonuç verene kadar
Kısım III'e T4 kaydı girmiyor.

---

## ✅ İKİNCİ SONDA BAŞLATILDI — 08.08.2026 01 51 UTC (Mete onayı)

Tadilat 1'in öngördüğü tek düzeltme uygulandı, bütçe 300 binden **600 bine** çıkarıldı.
Kurgu 4 varyant × 1 tohum × 600.000 adım, dizin `kosular_esik_sonda600/`. Tahmini süre
bir saat, iki dilim.

**Bütçe dışında hiçbir ayar değişmedi.** F1 açık, eşik 0,65, ödül ağırlıkları, çökme cezası,
eylem uzayı, trim ankrajı, PPO hiperparametreleri, tohum ve `LIMULUS_CRUISE_ITKI=1` aynı.

`esik_sonda.sh` bütçe ve dizini çevre değişkeninden alacak biçimde parametreleştirildi.
**Varsayılanlar 300 binlik koşunun değerleridir ve değiştirilmedi**, dolayısıyla ilk sonda
aynı komutla yeniden üretilebilir. İlk sondanın verisi `kosular_esik_sonda/` altında
duruyor, ayrıca `kosular_esik_sonda_yedek_08082026.tgz` olarak yedeklendi ve masaüstüne
işlendi. İki sonda **hiçbir tabloda karıştırılmaz**, karar 22 kuralı geçerli.

Karar kuralı 1 ikinci sondaya olduğu gibi uygulanır. Dört varyantın da hayatta kalma payı
%28'in üstüne çıkarsa Aşama 2b'ye geçilir, çıkmazsa F1 yetersiz ilan edilir ve yeni ön kayıt
açılır. **Bütçe bir kez daha artırılmayacaktır.** Tadilat 1 tek bir artırım öngördü ve o
kullanıldı.

---

## İKİNCİ SONDA SONUCU — 08.08.2026 02 30 UTC, 4/4 tamamlandı

**Veri denetimi (karar 30 protokolü): 4/4 GEÇTİ.** Her koşu 293 kayıt, son adım 600.064,
adım sayacı tek yönlü artıyor.

### Bütçe artırımı amacına ulaştı, dördü de ikinci seviyede eğitildi

| Koşu | Seviye 2'ye varış | Seviye 2'de eğitim adımı | 300 binlik sondada |
|---|---:|---:|---|
| limulus t0 | 346.112 | 253.952 | ulaşmamıştı |
| ikili t0 | 354.304 | 245.760 | ulaşmamıştı |
| senkron t0 | 202.752 | 397.312 | ulaşmıştı |
| lift+cruise t0 | 161.792 | 438.272 | ulaşmıştı |

Dağılım dışı okuma sorunu kapandı. Dört varyantın dördü de ikinci seviyede en az 245 bin adım
eğitildi.

### Karar kuralı 1 uygulanıyor

Seviye 2, deterministik, üç bölüm.

| Varyant | Hayatta kalma payı | Normalize ödül | Bölüm uzunluğu | Kapı 0,65 | Sonlanma |
|---|---:|---:|---:|---|---|
| limulus | **%41** | 0,310 | 823 | geçmez | yere çarpma |
| ikili | **%51** | 0,503 | 1015 | geçmez | yere çarpma |
| senkron | **%30** | 0,212 | 601 | geçmez | yere çarpma |
| lift+cruise | **%55** | 0,432 | 1105 | geçmez | yere çarpma |

> **Dört varyantın dördünde de hayatta kalma payı %28'in üstünde. KARAR KURALI 1 SAĞLANDI.**
> Ön kayıt gereği Aşama 2b'ye geçiş uygundur.

Donmuş kampanyayla karşılaştırma. Hayatta kalma payı %24 ile %27 bandından **%30 ile %55**
bandına, normalize ödül 0,015 ile 0,143 bandından **0,212 ile 0,503** bandına çıktı. Donmuş
kampanyada yirmi koşunun yirmisinin 478 ile 536 arasına toplandığı tekdüzelik kırıldı.

### ⚠️ Mekanizma denetimi, kural sağlandı ama F1 amacına TAM ULAŞMADI

Kural sağlanınca durulmadı ve F1'in tanımlandığı işi yapıp yapmadığı ayrıca ölçüldü. F1'in
gerekçesi, irtifa teriminin ölü olması yüzünden **alçalmanın ödülde karşılığı olmamasıydı**.

| Ölçüt | Donmuş 3M | Sonda 600k |
|---|---|---|
| İrtifa ödül terimi ortalaması | 2,3 × 10⁻⁵ | **0,17 ile 0,20** |
| İrtifa tek yönlü azalıyor mu | evet | **evet, hâlâ** |
| Ulaşılan azami irtifa | 150 m (başlangıç) | **150 m (başlangıç)** |
| Tilt kanalı azami kullanımı | 0,0° | **0,0 ile 0,3°** |
| Yere çarpan bölüm | 40/40 | **12/12** |

**İrtifa terimi canlandı, davranış canlanmadı.** Dört politika da hâlâ 150 metreden yere
iniyor, hiçbiri tırmanmıyor ve hiçbiri tilt kanalına dokunmuyor. F1'in yaptığı şey alçalmayı
**yavaşlatmak** oldu, durdurmak değil.

Bunun tırmanmanın mümkün olmamasından kaynaklanmadığı biliniyor. Taban kontrolcü aynı ortamda,
aynı eylem uzayından, aynı seviyede bölümün tamamını tamamlıyor ve 0,86 alıyor (Aşama 1, A2).
Yani tırmanma ulaşılabilir, politika bulamıyor.

### İkinci aday kusur artık baskın şüpheli

Karar 39 ana metni çökme cezasının indirim altında görünmezliğini ikinci aday kusur olarak
ayırmış ve "bir turda bir değişken" diyerek bu ön kaydın dışında bırakmıştı. Sonda o kalemi
**güçlendirdi**.

| Kampanya | Bölüm uzunluğu | İndirimli çökme cezası | Toplam getiriye payı |
|---|---:|---:|---:|
| donmuş 3M | 537 | 0,453 | %0,62 |
| sonda 600k limulus | 823 | 0,026 | %0,03 |
| sonda 600k ikili | 1004 | 0,004 | %0,01 |
| sonda 600k lift+cruise | 1105 | 0,002 | **%0,00** |

İndirim katsayısı 0,99 olduğu için bölüm uzadıkça çökmenin bedeli **küçülüyor.** F1 hayatta
kalmayı uzatarak çarpmanın cezasını fiilen ortadan kaldırdı. Politika açısından "olabildiğince
uzun süre alçalarak uç, sonunda çarp" hâlâ ödül-optimal, üstelik eskisinden daha fazla.

### Sonuç ve Mete'ye sorulan

Ön kayıtlı kural Aşama 2b'ye geçişe izin veriyor. Mekanizma denetimi ise Aşama 2b'nin
büyük olasılıkla **daha hassas ölçülmüş bir başarısızlık** üreteceğini söylüyor, çünkü
alçalmayı ödüllendiren yapı ayakta. İki seçenek Mete'ye sunuldu ve karar onun.

1. Aşama 2b ön kayıtta yazıldığı gibi koşulur (4 × 5 × 1M, ~7,5 saat).
2. Aşama 2b beklemeye alınır, önce sonlanma cezası ölçeği için ayrı bir ön kayıt açılır ve
   tek değişkenli bir sonda daha koşulur.

**Tez metnine dokunulmadı.**
