# 41 — İskonto ufku ön kaydı: sonlanma cezası da suçsuz, bağlayıcı kalem ufkun kendisi

**Tarih:** 08.08.2026 · **Sınıf:** **ön kayıt**, koşu sonucu görülmeden yazıldı
**Statü:** ✅ Mete onaylı (08.08.2026), Aşama 3 sondası başlatıldı
**Öncül:** karar `39` ikinci sonda sonucu, "ikinci aday kusur" kalemi
**Teşhis:** `9-DIJITAL-IKIZ/testler/dogrulama_mufredat_esigi.py` ve bu belgedeki ölçümler

---

## Bu belge neden bu hâlde

Karar 39, çökme cezasının indirim altında görünmezliğini ikinci aday kusur olarak ayırmış ve
"bir turda bir değişken" diyerek kendi kapsamının dışında bırakmıştı. İkinci sonda o kalemi
güçlendirdi ve Mete cezayı ele alan ayrı bir ön kayıt istedi.

Ön kaydı yazmadan önce ceza ölçüldü ve **ölçek de suçsuz çıktı.** Ölçüm reçeteyi üçüncü kez
değiştirdi. Bu belge cezanın büyütülmesini değil, iskonto ufkunun görevle uyumlanmasını
önerir.

**Bu, bu program içinde tekrarlayan bir örüntüdür ve yöntemsel ders olarak kaydediliyor.**
Karar 38 "eşiği gevşet" dedi, ölçüm eşiği suçsuz buldu. Karar 39 "cezayı büyüt" dedi, ölçüm
cezayı da suçsuz buldu. İkisinde de reçete, mekanizma ölçülmeden yazılmış bir tahmindi.
Kuralın kendisi şudur. **Bir düzeltme önerilmeden önce, düzelteceği mekanizma ölçülür.**

---

## Ölçüm, üç kalem

### 1. Ufuk uyuşmazlığı yirmi kat

İndirim katsayısı 0,99 olduğunda etkin ufuk `1/(1 − γ)` bağıntısıyla 100 adım, yani
**2 saniye** çıkar. Seviye 2 görevinin süresi **40 saniye**, yani 2000 adımdır.

| γ | Etkin ufuk (adım) | Ufuk (s) | Seviye 2'yi kapsıyor mu |
|---:|---:|---:|---|
| **0,99** (donmuş) | 100 | 2,0 | **hayır** |
| 0,995 | 200 | 4,0 | hayır |
| 0,997 | 333 | 6,7 | hayır |
| **0,999** (bu sondada) | 1000 | 20,0 | kısmen |
| 0,9995 | 2000 | 40,0 | evet |

Ajan görevin yirmide birini görmektedir.

### 2. Kritik kör değil, ceza görünmez

limulus t0 politikası, seviye 2, deterministik. Kritiğin değeri ve alçalma oranı.

| t (s) | İrtifa | Alçalma oranı | Kritiğin değeri | Çarpmaya kalan adım |
|---:|---:|---:|---:|---:|
| 0,02 | 150,0 m | 0,0 m/s | **+43,9** | 823 |
| 4,10 | 138,4 m | 5,7 m/s | +31,5 | 619 |
| 8,18 | 105,1 m | 10,3 m/s | +13,4 | 415 |
| 12,26 | 56,7 m | 13,0 m/s | −6,3 | 211 |
| 16,46 | −0,2 m | 13,7 m/s | **−91,7** | 1 |

Kritik durumun bozulduğunu izliyor, dolayısıyla sorun bir temsil körlüğü değil. Buna karşılık
**alçalma kararı 0,2. saniyede veriliyor** ve çarpma 16,5. saniyede geliyor. Aradaki iskonto
çarpanı `0,99^815 = 2,6 × 10⁻⁴`.

### 3. Cezayı büyütmek ölçülebilir etki üretmez

Taahhüt anında çökme cezasının indirimli değeri, cezanın büyüklüğüyle doğrusal ölçeklenir ve
aynı ufukta birikecek ödül 75 mertebesindedir.

| Ceza | Taahhüt anındaki indirimli değeri | Birikecek ödüle oranı |
|---:|---:|---:|
| 100 (mevcut) | 0,026 | %0,03 |
| 1.000 | 0,26 | %0,3 |
| 10.000 | 2,6 | %3,5 |

Cezayı yüz kat büyütmek dahi taahhüt anında yüzde birkaçlık bir sinyal üretir. Üstelik
büyütülen ceza, hayatta kalan bölümlerde de değer ölçeğini bozar. **Ceza ölçeği yanlış
knobdur.**

### 4. F1 sonrası ceza daha da görünmez oldu

| Kampanya | Bölüm uzunluğu | İndirimli çökme cezası | Toplam getiriye payı |
|---|---:|---:|---:|
| donmuş 3M | 537 | 0,453 | %0,62 |
| sonda 600k limulus | 823 | 0,026 | %0,03 |
| sonda 600k ikili | 1004 | 0,004 | %0,01 |
| sonda 600k lift+cruise | 1105 | 0,002 | %0,00 |

F1 hayatta kalmayı uzattı ve bunu yaparken çarpmanın bedelini fiilen ortadan kaldırdı.

---

## Aşama 3 — ön kayıtlı düzeltme, yalnız bir kalem

| # | Değişiklik | Gerekçe | Hipotezle ilgisi |
|---|---|---|---|
| **F2** | İndirim katsayısı 0,99 yerine **0,999**. Çevre değişkeni `LIMULUS_GAMMA` | Etkin ufuk 100 adımdan 1000 adıma, yani 2 saniyeden 20 saniyeye çıkar. Alçalmanın sonucu ajanın ufkuna girer | yok, dört varyantı aynı biçimde etkiler |

**Neden 0,9995 değil.** Görevi tam kapsayan değer 0,9995 olurdu. Seçilmedi, çünkü değer ölçeği
0,99'a göre yirmi kat büyüyor (azami getiri 75'ten 1500'e) ve kritiğin yakınsaması zorlaşıyor.
O durumda sonda başarısızlığı mekanizmadan değil eğitim kararlılığından gelebilir ve ayrım
kurulamaz. 0,999 ile ölçek on kat büyüyor (75'ten 750'ye), ufuk görevin yarısını kapsıyor ve
alçalma taahhüdü ile çarpma arasındaki çarpan `0,999^815 = 0,44` oluyor, yani ceza görünür
hâle geliyor. Sonda olumluysa 0,9995 ayrı bir kalem olarak tartışılabilir.

**Neden ceza ölçeği değil.** Yukarıdaki üçüncü ölçüm. Mete bu ön kaydı ceza ölçeği için
istemişti, ölçüm karşıt çıktı ve sapma onayıyla kaydedildi.

### Kritik nokta, metrik değişmiyor

Raporlanan ödül metriği `bolum_odulu / n_azami` bağıntısıyla **indirimsiz** hesaplanır.
Dolayısıyla γ değişikliği şunları **değiştirmez**.

- Müfredat eşiği 0,65 ve onun anlamı.
- Kampanyalar arası karşılaştırılabilirlik, çünkü aynı indirimsiz metrik kullanılıyor.
- A0 aritmetiği, yani kapının hayatta kalma payı karşılığı.

γ yalnız **öğrenme sinyalini** etkiler. Bu, F2'yi F1'den daha güvenli bir değişiklik yapıyor.

### Değişmeyecekler, bilerek donduruldu

- **F1 açık kalır** (`LIMULUS_IRTIFA_TABAN=1`). İki düzeltme birlikte sınanır, çünkü F1'in
  kaldırdığı ölü bölge geri gelirse ufuk düzeltmesinin etkisi ölçülemez.
- Müfredat eşiği 0,65, altı seviye, süreler ve hedefler.
- Bütün ödül ağırlıkları, **çökme cezası 100 dahil**.
- Eylem uzayı, trim ankrajı, KT_YETKI, KTH_YETKI.
- Diğer bütün PPO hiperparametreleri. GAE lambda 0,95, öğrenme oranı, kırpma, devir, yığın.
- Fizik modelinin hiçbir parametresi. `LIMULUS_CRUISE_ITKI=1`.
- Tohum seti ve gözlem normalizasyonu.

---

## Karar kuralları, sonuç görülmeden sabitlendi

1. **Birincil soru.** Seviye 2 bölümleri yere çarpmayı bırakıyor mu. Ölçüt, deterministik
   değerlendirmede hayatta kalma payı ve sonlanma nedeni dağılımıdır.
   - Dört varyantta da **sonlanma nedeni "süre doldu" olursa** F2 amacına ulaştı sayılır.
   - Hayatta kalma payı dördünde de %28'in üstünde kalır ama çarpma sürerse, F2 **kısmen
     yeterli** ilan edilir ve ölçülen pay kayda geçer.
   - Pay dördünde de %28'in altına düşerse F2 **zararlı** ilan edilir ve geri alınır.
2. **Mekanizma denetimi zorunlu.** Kural 1 sağlansa dahi irtifa izi ölçülür. Araç tırmanıyor
   mu, azami irtifa başlangıç değerinin üstüne çıkıyor mu. **Kural sağlandı diye durulmaz.**
   Bu kural, karar 39'da kuralın sağlanıp mekanizmanın tutmadığı durumdan öğrenilerek konuyor.
3. **Müfredat önkoşulu.** Dört koşunun da seviye 2'de en az 200 bin adım eğitilmiş olması
   gerekir. Olmayan koşunun değerlendirmesi dağılım dışı işaretlenir. Bütçe 600 bindir ve
   **artırılmayacaktır**.
4. **Terfi yetkinlik değildir.** Bir koşu seviye 3'e terfi ederse bu tek başına başarı
   sayılmaz, o seviyedeki hayatta kalma ayrıca ölçülür.
5. **Tek tohum karşılaştırma değildir.** Varyantlar arası sıralama bu sondadan okunmaz.
   Karar kuralı 2 (iki standart sapma) tek tohumla uygulanamaz ve uygulanmayacaktır.
6. **Dondurulmuş kampanyalar raporda kalır.** `kosular_v2`, `kosular_uzun` ve iki eşik sondası
   silinmez, düzeltilmiş koşu onların yerine geçmez. Ayrı dizin, karar 22.
7. **Veri denetimi** karar 30 protokolüyle yapılır.
8. Koşu bitmeden hiçbir ara sonuç tez metnine girmez.

---

## Yürütme

| Kalem | Değer |
|---|---|
| Kurgu | 4 varyant × 1 tohum × 600.000 adım |
| Dizin | `kosular_esik_gamma999/` |
| Bayraklar | `LIMULUS_GAMMA=0.999` · `LIMULUS_IRTIFA_TABAN=1` · `LIMULUS_CRUISE_ITKI=1` |
| Tahmini süre | bir saat, iki dilim |
| Bekçi | protokol v2 |

`egitim_v2.py` içinde γ çevre değişkeninden okunacak biçimde yazıldı. **Varsayılan 0,99'dur ve
değiştirilmedi**, dolayısıyla donmuş kampanyalar aynı komutla yeniden üretilebilir. Kullanılan
γ değeri her koşunun günlüğüne `ayar` alanı içinde yazılır, yani veri kendi soyağacını taşır.

---

*Kayıt 08.08.2026 · İlgili `12`, `15`, `30`, `38`, `39` · Protokol `LIMULUS_ELESTIRI_PROTOKOLU.md`*

---

## AŞAMA 3 SONUCU — 08.08.2026 14 45 UTC, 4/4 tamamlandı

Karar kuralları yazıldığı sırayla uygulandı.

### (a) Veri denetimi ve soyağacı

**Karar 30 protokolü: 4/4 GEÇTİ.** Her koşu 293 kayıt, son adım 600.064, adım sayacı tek
yönlü artıyor. Dört günlüğün `ayar.gamma` alanı da **0,999** yazıyor, yani veri kendi
soyağacını taşıyor ve bayrağın gerçekten etkin olduğu koşu dosyasından teyit edilebiliyor.

### (b) Kural 3 önkoşulu, biri dağılım dışı

| Koşu | Seviye 2'ye varış | Seviye 2'de eğitim adımı | Önkoşul (≥ 200 bin) |
|---|---:|---:|---|
| ikili t0 | 262.144 | 337.920 | sağlandı |
| senkron t0 | 204.800 | 395.264 | sağlandı |
| lift+cruise t0 | 249.856 | 350.208 | sağlandı |
| **limulus t0** | 442.368 | **157.696** | **DAĞILIM DIŞI** |

Bütçe artırılmadı. Ön kayıt bunu yasaklıyordu ve yasak uygulandı.

### (c) ve (d) Kural 1 uygulanıyor

Seviye 2, deterministik, üç bölüm.

| Varyant | Hayatta kalma payı | Normalize ödül | Bölüm uzunluğu | Sonlanma nedeni |
|---|---:|---:|---:|---|
| limulus (dağılım dışı) | %39 | 0,272 | 776 | yere çarpma |
| ikili | %67 | 0,548 | 1341 | yere çarpma |
| senkron | %49 | 0,412 | 979 | yere çarpma |
| lift+cruise | %47 | 0,378 | 934 | yere çarpma |

Kural 1'in üç dalı vardı. Sonlanma nedeni **dördünde de "yere çarpma"**, yani "süre doldu"
dalı oluşmadı. Hayatta kalma payı dördünde de %28'in üstünde, yani "zararlı" dalı da oluşmadı.

> **F2 KISMEN YETERLİ.** Hayatta kalma arttı, çarpma sürüyor. 12/12 bölüm yere çarpmayla
> bitiyor ve hiçbiri 0,65 kapısını geçmiyor.

### (e) Kural 2, zorunlu mekanizma denetimi

Kural sağlandı diye durulmadı. İrtifa izi ölçüldü.

| Varyant | Bölüm | Başlangıç irtifa | **Azami irtifa** | Son irtifa | Tırmandı mı | Son hız | Kritik V(s₀) |
|---|---:|---:|---:|---:|---|---:|---:|
| limulus | 776 | 150 m | **150,0 m** | −0,3 m | hayır | 17,2 m/s | +106,8 |
| ikili | 1343 | 150 m | **150,0 m** | −0,1 m | hayır | 9,0 m/s | +260,2 |
| senkron | 978 | 150 m | **150,0 m** | −0,1 m | hayır | 29,8 m/s | +313,9 |
| lift+cruise | 934 | 150 m | **150,0 m** | −0,1 m | hayır | 16,6 m/s | +312,1 |

Kritiğin başlangıç değeri 43,9'dan 107 ile 314 bandına çıktı, yani γ değişikliği değer
fonksiyonuna beklendiği gibi yansıdı ve uzun ufku temsil ediyor. **Buna karşılık davranış
değişmedi.** Dört varyantın hiçbiri başlangıç irtifasının üstüne çıkmıyor, azami irtifa
dördünde de tam olarak 150,0 metre.

### Üç yapılandırmanın karşılaştırması

| Yapılandırma | Bölüm uzunluğu | Hayatta kalma | Azami irtifa | Tırmanma | Çarpma |
|---|---:|---:|---:|---|---:|
| donmuş 3M (γ 0,99 · F1 kapalı) | 478–536 | %24–27 | 150,0 m | yok | 40/40 |
| sonda 600k (γ 0,99 · F1 açık) | 601–1105 | %30–55 | 150,0 m | yok | 12/12 |
| sonda 600k (γ 0,999 · F1 açık) | 776–1343 | %39–67 | 150,0 m | yok | 12/12 |

İki bağımsız ve ilkeli düzeltme hayatta kalmayı 536 adımdan 1341 adıma, yani **iki buçuk
kata** çıkardı. **Hiçbiri tırmanma üretmedi.** Altmış dört değerlendirme bölümünde araç bir
kez bile başlangıç irtifasının üstüne çıkmadı.

### Karşıt referans, görev ulaşılabilir

Aynı ortamda, aynı artımsal eylem uzayından sürülen kaskad PID kontrolcü.

| | Bölüm | Azami irtifa | Son hız | Azami tilt | Sonlanma |
|---|---:|---:|---:|---:|---|
| taban limulus | **2000** | **282,2 m** | 67,1 m/s | 30,0° | süre doldu |
| taban senkron | **2000** | **292,4 m** | 66,5 m/s | 30,0° | süre doldu |

Taban kontrolcü 150 metreden 282 ile 292 metreye tırmanıyor, hedef hızı (60 m/s) aşıyor,
eylem uzayının 30 derecelik tilt tavanını sonuna kadar kullanıyor ve bölümün tamamını
tamamlıyor. **Görev ulaşılabilir, eylem uzayı yeterli, fizik engel değil.** Politika bulamıyor.

### (f) Kural 5

Varyantlar arası sıralama bu sondadan **okunmamıştır.** Tek tohumla iki standart sapma kuralı
uygulanamaz. ikili'nin %67 ile en yüksek payı alması bir mimari bulgu değildir.

---

## Değerlendirme ve Mete'ye sorulan

Üç sonda, iki ilkeli düzeltme ve altmış dört değerlendirme bölümü sonrasında örüntü tutarlı.
**Ödül knoblarını tek tek çevirmek hayatta kalmayı uzatıyor, öğrenmeyi görevin kendisine
yaklaştırmıyor.** Bu noktada bir dördüncü knob önermek, aynı yolun devamı olur.

Ortaya çıkan şey bir başarısızlık kaydı değil, **sınırları belirlenmiş bir bulgudur.** Üç
yapılandırmada, dört mimaride, altmış dört bölümde hiçbir politika geçiş görevini
öğrenmemiştir. Aynı ortamda klasik bir kontrolcü görevi tamamlamaktadır. Bunun tezin merkez
karşılaştırması için doğrudan bir sonucu var. **Öğrenme ekseni, mimarileri ayırt edebileceği
bir rejimde hiç bulunmamıştır**, çünkü hiçbir kampanyada hiçbir politika görevi
öğrenmemiştir. Kısım III'ün "öğrenme koşularında fark yok" sonucu bu ışıkta yeniden
yazılmalıdır, ve politikadan bağımsız beş metrik mimari hakkındaki tek kanıt olarak kalır.

Karar Mete'de ve seçenekler şunlar.

1. **Sonda dizisi kapatılır, bulgu yazılır.** Karar 39 ve 41 birleştirilerek Kısım III'e
   T4 ile F2 kaydı girer, "öğrenme ekseni ayırt edici rejimde bulunmadı" sonucu açıkça
   yazılır. Ek hesap yok.
2. **Bir sonda daha, farklı sınıftan.** Ödül knobu değil, öğrenme kurgusu değişir. Örneğin
   taban kontrolcünün taklit edilmesiyle ön eğitim, ya da müfredata gerçekten öğrenilebilir
   bir ara basamak eklenmesi. Bu bir ön kayıt daha gerektirir ve ödül tanımına dokunmaz.
3. **Aşama 2b yine de koşulur** (4 × 5 × 1M, ~7,5 saat). Beş tohumla ölçülmüş bir olumsuz
   sonuç, tek tohumluk sondalardan daha güçlü bir kayıt olur.

**Birinci seçenek öneriliyor**, ikincisi ona ek olarak sonra düşünülebilir. Gerekçe, bulgunun
zaten üç yapılandırmada tekrarlanmış olması ve dördüncü knobun aynı sınıfta kalması.

**Tez metnine dokunulmadı.**

---

## ✅ KAPANDI — sonda dizisi kapatıldı (08.08.2026, Mete kararı)

Mete birinci seçeneği seçti. **Sonda dizisi kapatılmıştır.** Dördüncü bir ödül knobu
denenmeyecek, Aşama 2b koşulmayacak ve bulgu Kısım III'e yazılacaktır.

### Kapanış kaydı

| Kalem | Durum |
|---|---|
| Karar 39 F1 (irtifa ölü bölgesi) | uygulandı, **kısmen yeterli**, bayrak arkasında kalıcı |
| Karar 41 F2 (iskonto ufku) | uygulandı, **kısmen yeterli**, bayrak arkasında kalıcı |
| Karar 39 Aşama 2b (4 × 5 × 1M) | **koşulmadı**, Mete kararıyla iptal |
| Ceza ölçeği ön kaydı | **açılmadı**, ölçüm knobu suçsuz buldu |
| Üç sonda verisi | `kosular_esik_sonda/` · `kosular_esik_sonda600/` · `kosular_esik_gamma999/`, üçü de tgz olarak yedekli |

**Bayraklar kalıcı ve varsayılan KAPALI.** `LIMULUS_IRTIFA_TABAN` ve `LIMULUS_GAMMA`
varsayılanları donmuş kampanyaların değerleridir, dolayısıyla `kosular_v2` ve `kosular_uzun`
aynı komutla yeniden üretilebilir. Üç sondanın her günlüğü kullanılan bayrak değerini `ayar`
alanında taşır.

### Teze giren sonuç

Kısım III'e yeni bir bölüm eklendi, `sec:sonuc-ogrenilebilirlik`. İçeriği şudur. Üç
yapılandırmada, dört mimaride ve altmış dört değerlendirme bölümünde hiçbir politika geçiş
görevini öğrenmemiştir. Aynı ortamda, aynı artımsal eylem uzayından sürülen kaskad PID
kontrolcü görevi tamamlamaktadır. Dolayısıyla **öğrenme ekseni, mimarileri ayırt edebileceği
bir rejimde hiç bulunmamıştır** ve politikadan bağımsız beş metrik mimari hakkındaki tek kanıt
olarak kalır.

Ayrıca `sec:sonuc-kararlilik` karar `40`'a göre düzeltildi ve Bekleyen Koşular tablosundan iki
kalem düştü.

### Sonraki oturuma bırakılan, ön kayıt gerektirir

Karar 41'in ikinci seçeneği kapatılmadı, **ertelendi.** Ödül knobu değil öğrenme kurgusu
değiştiren bir sonda hâlâ meşru bir adımdır. İki aday, taban kontrolcünün taklidiyle ön eğitim
ve müfredata gerçekten öğrenilebilir bir ara basamak eklenmesi. Yapılırsa kendi ön kaydıyla
yapılır ve bu belge onun öncülü olur.

---

*Kapanış 08.08.2026 · Veri üç ayrı dizinde ve üç tgz yedeğinde · Teze işlendi
`J_sonuclar` `sec:sonuc-ogrenilebilirlik`*
