# 52 — M5 revizyon ölçümleri ön kaydı: iki sondanın beş tohumla tekrarı ve T3 kusurlu ortamının yeniden koşulması

**Tarih:** 11.08.2026 · **Sınıf:** **ön kayıt** — sonuç görülmeden yazıldı
**Statü:** ✅ **TAMAMLANDI (12.08.2026).** 42/42 koşu, veri denetimi geçti, sonuçlar en altta
**Öncül:** M5 danışman geridönüşü, hüküm MAJOR REVISION. Açık iki kalem **C-01** (birinci
yarısı) ve **M-01**, ikisi de hakemin kendi istediği ölçümler. Kayıt
`10-MAKALELER/M5_.../LIMULUS_M5_gonderim_kontrol_v4.md`
**Kod:** `9-DIJITAL-IKIZ/ogrenme/egitim_v2.py` (Bölüm A mevcut bayraklarla koşar) ·
Bölüm B bir yeni bayrak gerektirir, aşağıda
**Dizinler:** `kosular_esik_sonda600_s5/` · `kosular_esik_gamma999_s5/` · `kosular_t3_v0/`
(üçü de yeni ve ayrı, karar `22`)

> ⚠️ **Bu belge sonuçlar görülmeden yazılmıştır.** Karar kuralları ölçümden önce
> sabitlenmiştir. Sonuçlar ayrı bölüm olarak eklenecek, bu bölüm değiştirilmeyecektir.
> Tadilat gerekirse karar 39'un deseniyle, tarihli ve sonuç görülmeden eklenir.

---

## Neden açıldı

Hakem iki ölçüm istiyor ve ikisi de haklı bulunup kabul edildi.

**C-01, birinci yarısı.** Karar 39'un ikinci sondası ile karar 41 sondası varyant başına tek
tohumla koşuldu. Yapılandırmalar arası hayatta kalma karşılaştırması (%24-27 → %30-55 → %39-67)
bu yüzden tek tohuma dayanıyor ve makale bu bantlardan sıralama okumadığını yazsa da bandın
kendisi Tablo 2'de duruyor. Beş tohumlu tekrar, bantlara ilk kez örneklem sapması kazandırır ve
karar 39 kural 4'ün iki sapma eşiği ilk kez uygulanabilir hâle gelir. Ölçülmüş maliyet makalenin
6. bölümünde beyan edilidir, 600 bin adımlık kırk koşu, sıralı koşumda mertebesi bir gün.

**M-01.** Makale §4.3'ün tanı imzası sayıları (bölüm uzunluğu 99'dan 83'e inerken ödül −0,101'den
−0,006'ya yükseliyor) yalnız kısmen korunmuş düzeltme öncesi kayıtlardan geliyor ve sağ kalan
günlüklerden yeniden üretilemiyor. Hakem kusurlu yapılandırmanın yeniden koşulmasını istiyor.
Küçük bütçeli bir koşu bu sayıları eksiksiz günlüklerle değiştirir.

---

## BÖLÜM A — C-01, iki sondanın beş tohumla tekrarı

### Kurgu

| Kalem | Sonda A1 | Sonda A2 |
|---|---|---|
| Tekrarlanan | karar 39 ikinci sondası | karar 41 sondası |
| Bayraklar | `LIMULUS_IRTIFA_TABAN=1` · `LIMULUS_CRUISE_ITKI=1` · γ öntanım 0,99 | aynı artı `LIMULUS_GAMMA=0.999` |
| Varyant | 4 (limulus, ikili, senkron, lift+cruise) | 4 |
| Tohum | **5** (0-4) | **5** (0-4) |
| Bütçe | 600.000 adım/koşu | 600.000 adım/koşu |
| Dizin | `kosular_esik_sonda600_s5/` | `kosular_esik_gamma999_s5/` |
| Değerlendirme | seviye 2, deterministik, politika başına 3 bölüm (orijinalle aynı) | aynı |

Toplam **40 koşu, 24M adım.** İlk 300 binlik sonda (karar 39 Aşama 2a) tekrarlanmaz, çünkü
sonuçsuz ilan edilmişti ve makalenin 64 bölümüne dahil değildir.

⚠️ **Tohum 0 orijinal sondaların tohumudur ve bir determinizm denetimi olarak kullanılır.**
Karar 47'de A ile C hücrelerinin bit düzeyinde aynı çıkması eğitimin tohum verildiğinde
belirlenimci olduğunu gösterdi. Tohum 0 koşuları orijinal günlüklerle karşılaştırılır, birebir
çıkmazsa neden araştırılır ve sonuç bölümüne yazılır, sessizce geçilmez.

### Karar kuralları — sonuç görülmeden donduruldu

1. **Birincil çıktı Tablo 2'nin bantlarının beş tohumlu karşılıklarıdır.** Hayatta kalma payı ve
   normalize ödül, varyant başına ortalama ve örneklem sapmasıyla raporlanır. Sayılar ne çıkarsa
   Tablo 2 ve Şekil 3'e o yazılır.
2. **Varyantlar arası sıralama ancak şimdi ve ancak şu kuralla okunur.** Fark, beş tohumun
   standart sapmasının iki katından küçükse **fark yok** yazılır (karar 12 ve 39'un kuralı).
   Tek tohumlu orijinal bantlar kayıtta kalır ve hiçbir tabloda yeni bantlarla karıştırılmaz.
3. **Müfredat önkoşulu, karar 41 kural 3.** Seviye 2'de en az 200 bin adım eğitilmeyen koşunun
   değerlendirmesi dağılım dışı işaretlenir. Bütçe **artırılmaz.** Dağılım dışı koşu sayısı
   varyant ve sonda bazında raporlanır.
4. **Mekanizma denetimi zorunlu, karar 41 kural 2'nin dersi.** Bantlar ne çıkarsa çıksın irtifa
   izi ölçülür. Azami irtifa, tırmanma olup olmadığı ve tilt kanalı kullanımı yazılır. Kural
   sağlandı diye durulmaz.
5. **Merkez bulgu her iki yönde de güncellenir.** Kırk koşunun hiçbirinde tırmanma çıkmazsa
   "altmış dört bölüm" beyanları yeni bölüm sayısıyla güçlendirilir. Herhangi bir tohum
   tırmanma üretirse bu, makalenin merkez sonucunu değiştirir ve makale ona göre yeniden
   yazılır. Ön kayıt sonucu taahhüt etmez.
6. **Veri denetimi** karar 30 protokolüyle yapılır. Adım sayısı, kayıt sayısı, tek yönlü artış,
   `ayar` alanından bayrak soyağacı.
7. Hiperparametre aranmaz, bütçe değişmez, koşu bitmeden makale ve tez metnine hiçbir ara
   sonuç girmez.

---

## BÖLÜM B — M-01, T3 kusurlu ortamının yeniden koşulması

### B0 — yapılabilirlik adımı, koşudan önce

Düzeltme öncesi davranış bugün bayrak arkasında değil, kontrol listesi v4 bunu açıkça yazıyor.
Önce **yeni bayrak** `LIMULUS_ORTAM_V0=1` kurulur ve düzeltme öncesi ortamı geri getirir,
karar 15'in üç düzeltmesi geri alınmış hâlde: T1 mutlak eylem eşlemesi, T2 hover'da ateşlenen
stall cezası, T3 cezasız tutum sonlanması. Üçü birlikte geri alınır, çünkü §4.3'ün imzası o
bütünün ürünüdür ve makalenin istediği şey "düzeltme öncesi ortamın yeniden kurulması"dır.

⚠️ **Öntanım 0'dır ve 0 iken davranış bugünkü koda bit düzeyinde eşdeğer olmalıdır.** Bayrak
birim düzeyinde doğrulanır: 1 iken hover'da stall cezası ateşleniyor mu, 85 derece sonlanması
cezasız mı, eylem eşlemesi mutlak mı. Doğrulama geçmeden koşu başlamaz. Geri kurma güvenilir
biçimde yapılamazsa **koşu iptal edilir**, bu sonuç buraya yazılır ve §4.3'ün "kısmen korunmuş
kayıt" beyanı yerinde kalır. Uydurma bir yeniden kurgu koşulmaz.

### Kurgu

| Kalem | Değer |
|---|---|
| Varyant | limulus (tam varyant) |
| Tohum | 2 |
| Bütçe | 300.000 adım/koşu |
| Bayrak | `LIMULUS_ORTAM_V0=1` |
| Dizin | `kosular_t3_v0/` |

### Karar kuralları — sonuç görülmeden donduruldu

1. **Birincil çıktı iz imzasıdır.** Eğitim boyunca ortalama ödül ile ortalama bölüm uzunluğunun
   yönü. Ödül yükselirken bölüm uzunluğu düşüyorsa imza eksiksiz günlüklerle doğrulanmış olur
   ve §4.3'ün sayıları yeni koşunun kendi günlüklerinden yeniden yazılır, eski sayılar "kısmen
   korunmuş kayıt" niteliğiyle birlikte metinden çıkar.
2. **İmza çıkmazsa bu da aynen yazılır.** §4.3'ün beyanı yerinde kalır, ayrıca imzanın neden
   üretilemediği araştırılır ve bulunamazsa "üretilemedi" diye kaydedilir. Hiperparametre
   aranmaz, üçüncü tohum ya da daha uzun bütçe denenmez.
3. Bu koşunun sayıları **yalnız §4.3 ve §6'nın ilgili açık kalemini** besler, hiçbir mimari
   karşılaştırmaya ve hiçbir tabloya başka amaçla girmez.
4. Veri denetimi karar 30, koşu bitmeden metin değişmez.

---

## Yürütme sırası ve maliyet

Kural 7 gereği (bir makinede aynı anda yalnız bir ölçüm) her şey **sıralı** koşar ve bu kampanya
sürerken başka hiçbir ölçüm başlatılmaz.

| Sıra | İş | Tahmin | Dayanak |
|---|---|---:|---|
| 1 | B0 yapılabilirlik ve bayrak doğrulaması | ~1 saat | kod işi, koşu değil |
| 2 | Bölüm B, 2 koşu × 300k | ~35 dk | boş makine ~304 adım/s, karar 47 ARA KAYIT 2 |
| 3 | Bölüm A, 40 koşu × 600k | **~22 saat** | aynı ölçüm, makale §6 "mertebesi bir gün" beyanıyla tutarlı |
| 4 | Değerlendirme ve toplama | ~1 saat | politika başına 3 bölüm, deterministik |

Bölüm B öne alınmıştır, çünkü ucuzdur ve bekçi zincirinin duman testi görevini görür. Bekçi
protokolü v2 uygulanır, tahmini uyanma sayısı bir günlük blok için **~30** (karar 38 kampanyası
42,5 saatte 52 uyanma verdi, oran aynı).

## Makaleye etkisi

Tamamlanırsa M5'in iki açık kalemi de kapanır ve paket gönderilebilir hâle gelir. Tablo 2 ile
Şekil 3 yeniden üretilir, üreteç `figurler/fig_uret.py` hazırdır. §4.3 sayıları eksiksiz
günlüklere bağlanır. §6'nın "yapılmamıştır" beyanları "yapılmıştır" olarak güncellenir ve
kapak mektubuna iki ölçümün koşulduğu yazılır. TR ikiz aynı turda eşitlenir.

---

*Kayıt 11.08.2026 · İlgili `12`, `15`, `22`, `30`, `39`, `41`, `47` ·
Protokol `LIMULUS_ELESTIRI_PROTOKOLU.md` · Bekçi protokolü v2*

---

## ✅ B0 TAMAMLANDI ve KAMPANYA BAŞLATILDI — 11.08.2026 18:30 UTC (Mete onayı)

`LIMULUS_ORTAM_V0` bayrağı `ortam.py`'ye eklendi ve üç denetimden geçti
(`testler/dogrulama_ortam_v0.py`).

| Denetim | Sonuç |
|---|---|
| Regresyon, bayrak KAPALI | 400 adımlık sabit tohumlu iz, düzenleme öncesi kayıtla **sha256 birebir aynı** |
| T1 mutlak eşleme | sıfır eylem **421 adımda çarpıyor** — karar 15'in kaydettiği 420 ile örtüşüyor |
| T2 esiksiz stall | V 0,6 m/s iken zarf cezası ateşlendi |
| T3 cezasız sonlanma | tutum aşımı sonlanması cokme **0**, yere çarpma **−100** |

⚠️ Sıfır eylem çarpma adımının karar 15'le birebir örtüşmesi, geri kurmanın doğru
ortamı kurduğunun bağımsız bir işaretidir, ön kayıtta öngörülmemişti ve buraya
ölçüldükten sonra yazıldı.

**Soyağacı genişletildi.** `egitim_v2.py` `Ayar2` artık `irtifa_taban`, `cruise_itki`
ve `ortam_v0` alanlarını günlüğe yazıyor, üçü de ortam değişkeninden okunuyor.

**Yürütme.** Koşucu `ogrenme/kampanya_52.sh`, kilitli ve sıralı. Bu oturumun kabında
ölçülen hız **~589 adım/s** (eski kabın 304'üne karşılık), 600k koşu ~18 dk, kırk koşu
bloğu **~13 saat** bekleniyor. Bekçi protokolü v2 kuruldu.

---

# SONUÇLAR — 12.08.2026, 42/42 koşu tamamlandı

> Bu bölüm ölçümden sonra yazılmıştır. Ön kayıt ve B0 bölümleri değiştirilmemiştir.
> Veri `kosular_t3_v0/`, `kosular_esik_sonda600_s5/`, `kosular_esik_gamma999_s5/`,
> değerlendirme `9-DIJITAL-IKIZ/ogrenme/k52_degerlendirme.json`, betik
> `testler/degerlendirme_k52.py`.

## Yürütme kaydı

11.08.2026 18:30 → 12.08.2026 08:42 UTC, yaklaşık **14,2 saat** (tahmin 22 saatti, yeni kap
~500-590 adım/s verdi). Kap üç kez oturum arasında süreci öldürdü, üçünde de atomik ara
kayıttan devam edildi ve **veri kaybı sıfır**. Bekçi zinciri ~14 uyanma kullandı.

## Veri denetimi — 42/42 GEÇTİ

Karar 30 protokolü, kırk iki koşunun tamamında kayıt sayısı (293 ve 147), son adım, tek yönlü
artış ve `ayar` soyağacı (irtifa_taban, cruise_itki, gamma, ortam_v0) doğru.

## Determinizm denetimi — sonuç MAKİNE BAĞIMLI

Tohum 0, orijinal sondayla **birebir çıkmadı** ve ön kayıt gereği neden araştırıldı. İlk
günlük kaydında fark 2,7e-10 (dokuzuncu ondalık), kaynak farklı CPU/BLAS çekirdeği, torch
sürümü aynı (2.13). Kaotik eğitim dinamiği bu farkı 600k adımda nicel ayrışmaya büyütüyor
(n_bolum 796 karşısında 880), nitel sonuç aynı (ikisi de seviye 2, son ödül 0,040/0,043).
**Karar 47'nin bit eşitliği aynı makine içinde geçerlidir, makineler arası değildir.** Tohum 0
sıradan geçerli bir tohum olarak değerlendirmeye alındı.

## Kural 3 — dağılım dışı koşular

`sonda600_s5` limulus t0 (196.608) ve t3 (174.080), `gamma999_s5` limulus t1 (55.296) seviye
2'de 200 bin adım eşiğinin altında kaldı ve değerlendirmeleri dağılım dışı işaretlendi. Kalan
37 koşu önkoşulu sağladı. Bütçe artırılmadı.

## Kural 1 — beş tohumlu bantlar (seviye 2, deterministik, politika başına 3 bölüm)

| Varyant | Sonda A1 (F1, γ 0,99) | Sonda A2 (F1+F2, γ 0,999) |
|---|---:|---:|
| limulus | %34,3 ± 1,6 (n=3) | %53,8 ± 8,3 (n=4) |
| ikili | %39,5 ± 14,6 | %66,6 ± 30,8 |
| senkron | %31,0 ± 4,9 | %62,4 ± 21,4 |
| lift-cruise | %34,9 ± 4,9 | %61,5 ± 15,7 |

Tek tohumlu orijinal bantlar (%30-55 ve %39-67) kayıtta kalır, karıştırılmadı.

## Kural 2 — on iki çiftin on ikisinde FARK YOK

İki sondada da hiçbir varyant çifti iki sapma eşiğini geçmedi (en büyük fark 12,8 puan,
eşik 31,5-61,6). **Tek tohumlu bantların ima ettiği sıralama beş tohumda kayboldu**, uçlar
örneklem gürültüsüydü. Makalenin "bu bantlardan sıralama okunmaz" beyanı ölçümle doğrulandı.

## Kural 4 — mekanizma denetimi ve kural 5

**120 değerlendirme bölümünün 120'sinde azami irtifa 150,0 m, tırmanma YOK.** Merkez bulgu
("hiçbir politika başlangıç irtifasının üstüne çıkmadı") 64 bölümden **184 bölüme** çıkarak
güçlendi, kural 5'in birinci dalı yürürlükte.

⚠️ İki yeni gözlem kayda geçirildi ve makaleye kapsam düzeltmesi olarak girecek.

1. **γ 0,999 kolunda 12 bölüm "süre doldu" ile bitti** (orijinal tek tohumda 12/12 çarpmaydı)
   ve iki tohum (ikili t3 +1,069, senkron t4 +0,983) 0,65 kapısını **tırmanmadan** geçti.
   Mekanizma, düz uçuşta hız terimini toplamak. Kapının geçilmesi görev öğrenimi değildir
   (karar 39 kural 5, terfi yetkinlik değildir) ve irtifa bileşeni hâlâ öğrenilmiyor.
2. **limulus tohumları tilt kanalını 2-27 derece kullanıyor** (orijinal tek tohumda 0,0-0,3).
   Kanal kullanımının kendisi beş tohumda görünür oldu, kazanım hâlâ yok.

## BÖLÜM B — T3 imzası eksiksiz günlüklerle doğrulandı

k30 2/2 geçti. İki koşuda da ödül yükselirken bölüm uzunluğu kısaldı, kural B1 sağlandı.

| Tohum | Ödül | Ort. bölüm uzunluğu | Korelasyon |
|---|---|---|---:|
| t0 | −0,271 → +0,095 | 93 → 41 | r = −0,674 |
| t1 | −0,169 → +0,084 | 82 → 37 | r = −0,854 |

§4.3'ün sayıları bu günlüklerden yeniden yazılacak, "kısmen korunmuş kayıt" beyanı metinden
çıkacak.

## Sıradaki iş

M5 paketi v6: Tablo 2 beş tohumlu bantlar ve iki yeni satır, Şekil 3 yeniden üretimi, §4.3
yeni imza sayıları, §6 iki açık kalemin kapanışı, iki yeni gözlemin kapsam beyanı, kapak
mektubu güncellemesi. Kampanya 53 (karar 53) 12.08.2026 08:42 UTC'de boşluksuz başlatıldı.
