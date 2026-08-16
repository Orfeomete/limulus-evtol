# 54 — Müfredat basamak büyüklüğü ön kaydı: geniş keşif kolunda ince müfredat

**Tarih:** 15.08.2026 · **Sınıf:** **ön kayıt** — sonuç görülmeden yazıldı
**Statü:** ✅ **TAMAMLANDI 15.08.2026.** 5/5 koşu, veri denetimi geçti, sonuçlar en altta
**Öncül:** karar `47` tasarım dejenerasyonu bölümü (müfredat çarpanı yalnız geniş keşif kolunda
sınanabilir) ve karar `53` düzeltmesi (keşif genişliği bir hızlandırmadır, bir açma değildir)
**Kod:** `LIMULUS_MUFREDAT_INCE=1 python3 9-DIJITAL-IKIZ/ogrenme/egitim_v2.py --log-std0 -0.5`
**Dizin:** `kosular_ince_mufredat/` (yeni ve ayrı, karar `22`)

> ⚠️ **Bu belge sonuçlar görülmeden yazılmıştır.** Karar kuralları ölçümden önce sabitlenmiştir.
> Sonuçlar ayrı bölüm olarak eklenecek, bu bölüm değiştirilmeyecektir. Tadilat gerekirse tarihli
> ve sonuç görülmeden eklenir.

---

## Neden açıldı ve neden sırası budur

Geçiş görevinin öğrenilememesinin nedeni olarak **beş aday sınandı ve beşi de elendi**. Ödül
tanımına yapılan iki müdahale davranışı değiştirmedi, üç kat bütçe örüntüyü birebir tekrarladı,
kararlılık hipotezi eldeki veriyle çürütüldü, keşif genişliği ise tam ölçekte ayırt edilemedi.
Geriye **sınanmamış tek aday** kalmıştır, müfredat basamaklarının büyüklüğü.

Taban müfredatta seviye 1 (`dikey`, hedef hız 0) ile seviye 2 (`gecis`, hedef hız 60 m/s)
arasındaki basamak, hedef hızı tek adımda sıfırdan altmışa çıkarmaktadır. Kaynak `ortam.py`
satır 95-103, doğrulandı.

⛔ **Bu aday bir kez sınandı sanılıyor, sanılmamalıdır.** Karar 47'nin $2\times2$ sondasında C
hücresi (ince müfredat, dar keşif) taban hücresinin **bit düzeyinde tekrarı** çıktı, çünkü
`LIMULUS_MUFREDAT_INCE=1` yeni görevi indeks 2'ye ekliyor ve seviye 0 ile 1 iki kolda birebir
aynı kalıyor. Seviye 1'i geçemeyen bir koşuda müfredat çarpanı **atıl** kalmaktadır. Karar 47
bunu kendi sonuçlar bölümünde şöyle yazmıştır, *"C geçmedi satırı ince müfredatın başarısız
olduğunun kanıtı değildir, o satırın anlamı ince müfredatın dar keşif altında hiç sınanmamış
olmasıdır"*.

Dolayısıyla müfredat çarpanının sınanabileceği tek yer **geniş keşif koludur** ve orada da yalnız
300 bin adımlık bir sondayla, iki tohumla, tek varyantla bakılmıştır. Bu ön kayıt o boşluğu tam
ölçekte kapatır.

## Dondurulmuş hipotez

Seviye 1 ile seviye 2 arasına 30 m/s hedefli bir ara basamak konması, geniş keşif kolunda tam
bütçede politikaları `gecis` görevini **tamamlar** hâle getirir.

**İki soru açıktır ve kampanya onları ölçer.** Ara basamak `gecis` görevine varış oranını
değiştiriyor mu, ve varanların görevi tamamlama oranını değiştiriyor mu. Ön kayıt bu iki sorunun
cevabını taahhüt etmez. ⚠️ Hipotezin yanlışlanması da bir sonuçtur ve öyle raporlanır, ince
müfredat işi **kötüleştirirse** o da yazılır.

## Kurgu

| Kalem | Değer |
|---|---|
| Varyant | **1 (`limulus`)** · ~~4 varyant~~, onayda indirildi |
| Tohum | 5 (0-4) |
| Bütçe | 3.000.000 adım/koşu, toplam **15M adım, 5 koşu** |
| Değişen tek şey | `LIMULUS_MUFREDAT_INCE=1` (7 seviye, `gecis_yarim` indeks 2'de) |
| Keşif | `log_std0 = −0,5`, karar 53 ile **aynı** |
| Bayraklar | `LIMULUS_CRUISE_ITKI=1` · **F1 ve F2 KAPALI** (öntanım) · γ 0,99 |
| Dizin | `kosular_ince_mufredat/` |
| Bekçi | protokol v2, saatlik dilim, atomik ara kayıt |

## ⛔ Karşılaştırma tabanı yeniden koşulmayacaktır

Karar 53 kampanyası (`kosular_genis_kesif/`) tam olarak bu kurguyu **taban müfredatla** koşmuştur.
Doğrulandı, o ön kaydın kurgu tablosu *"Müfredat, taban, 6 seviye. İnce müfredat kullanılmaz"*
diyor ve `log_std0 = −0,5`, 4 varyant, 5 tohum, 3M adım.

Yani bu kampanya karar 53 ile **yalnız müfredat farkıyla** yan yana okunur ve tek değişken kuralı
korunur. Taban kolu yeniden koşmak yirmi koşu daha demektir ve **hiçbir yeni bilgi getirmez**.

⚠️ **Bunun bir bedeli vardır ve peşinen yazılır.** İki kampanya farklı günlerde koşmuştur,
dolayısıyla makine ve yük farkı vardır. Karar 53 determinizmin makine bağımlı olduğunu zaten
ölçmüştür. Bu, **duvar saati ve adım/s karşılaştırmasını geçersiz kılar** fakat görev, ödül ve
sonlanma nedeni karşılaştırmasını etkilemez, çünkü bunlar tohum ve ayar tarafından belirlenir.
Duvar saati bu kampanyada **karşılaştırma metriği olarak kullanılmayacaktır**.

## Karar kuralları — sonuç görülmeden donduruldu

1. **Birincil metrik ulaşılan görev ADIDIR, seviye indisi değildir.** ⛔ İki müfredat arasında
   seviye indisi karşılaştırılamaz, çünkü indisler aynı görevi göstermez. Kaynak `ortam.py`
   satır 111-112'deki kendi uyarısı. Varyant başına kaç tohumun `gecis` görevine ulaştığı sayılır.

2. **Ulaşmak ile tamamlamak ayrı raporlanır** (karar 39). Tamamlama ölçütü deterministik
   değerlendirmede sonlanma nedeninin *"süre doldu"* olması ve 0,65 kapısının geçilmesidir.
   Eşik **0,65 dondurulmuş kalır**.

3. **Karşılaştırma karar 12 ile yapılır.** Bir fark, daha oynak grubun **örneklem** standart
   sapmasının (ddof=1) iki katından küçükse **FARK YOK** yazılır. ⛔ Onayla daraltıldı, karşılaştırma
   **`limulus` karşısında `limulus`**, beş tohum karşısında beş tohum yapılır. Diğer üç varyant
   bu kampanyada yoktur.

4. ⛔ **Eşit bütçede ince kol yapı gereği geridedir ve bu bir bulgu sayılmaz.** Ara basamak
   eklendiği için ince kolun `gecis`e varması bir seviye daha gerektirir. Bu nedenle *"ince kol
   daha düşük seviyede kaldı"* biçiminde hiçbir hüküm yazılmaz. Karşılaştırma **yalnız ortak
   görev olan `gecis` üzerinden** yapılır, varış ve tamamlama olarak.

5. **Dejenerasyon denetimi zorunludur.** Her koşu için, kolların ayrıştığı seviyeye ulaşılıp
   ulaşılmadığı ölçülür. Bir koşu seviye 1'i geçmemişse o koşuda müfredat çarpanı **atıldır** ve
   o koşu *"ince müfredat başarısız"* diye değil **"ince müfredat sınanmadı"** diye raporlanır.
   Bu kural karar 47'nin dersidir ve bu kez ölçümden önce yazılmıştır.

6. **Mekanizma denetimi zorunlu** (karar 41). Hangi kural sağlanırsa sağlansın irtifa izi, azami
   irtifa, tilt kanalı kullanımı, `gecis_yarim` görevinde geçirilen adım sayısı ve sonlanma nedeni
   dağılımı ölçülür. Kural sağlandı diye durulmaz.

7. **Hiçbir tohum `gecis` görevini tamamlayamazsa şu cümle yürürlüğe girer.** *Müfredat basamak
   büyüklüğü de geçiş görevinin öğrenilememesinin nedeni değildir. Öğrenilemezliğin nedeni olarak
   sınanan altı adayın altısı elenmiş, dolayısıyla neden bu çalışmanın ölçtüğü eksenlerin dışında
   kalmıştır ve tez bunu açık kalem olarak bırakmaktadır.* Tez Bölüm~`sec:sonuc-bekleyen` ve M5
   §6 bu ölçülmüş hükümle güncellenir.

8. **Hiperparametre aranmaz.** Üçüncü bir müfredat tanımı denenmez, ara basamağın hedef hızı
   30 m/s'te sabittir, bütçe artırılmaz, entropi katsayısı ve öğrenme oranı dokunulmaz kalır ve
   dokunulmadığı makalede beyan edilir.

9. **Dondurulmuş kampanyalar raporda kalır** (karar 39 kural 6). `kosular_genis_kesif` silinmez,
   bu kampanya onun yerine geçmez, yanına ayrı bölüm olarak girer ve müfredat tanımı her tabloda
   yazılır. İki set hiçbir tabloda karıştırılmaz.

10. **Veri denetimi** karar 30 protokolüyle. `ayar` alanı müfredat bayrağını taşımalıdır.
    ⚠️ Bu doğrulanacaktır, taşımıyorsa kampanya başlamadan önce günlükleyici düzeltilir. Koşu
    bitmeden hiçbir ara sonuç makale ve tez metnine girmez.

## Maliyet — ölçülü, tahmin değil

| Kalem | Değer | Dayanak |
|---|---:|---|
| Duvar saati | **~9,6 saat** (5 koşu) | aşağıdaki iki bağımsız ölçümden |
| Koşu başına, ölçüm A | **1,82 saat** | 15.08.2026 kalibrasyonu, 60.000 adım 131 saniyede, **458 adım/s** |
| Koşu başına, ölçüm B | **1,91 saat** | karar 53'ün kendi kaydı, 20 koşu 38,21 saat duvar saati |
| İki ölçümün farkı | **%5** | kalibrasyon kayıttaki 421-551 bandının ortasında, makine aynı sınıf |

⚠️ Kalibrasyon koşusu `/tmp` altına yazıldı ve **silindi**, hiçbir kampanya dizinine dokunmadı.

⚠️ İnce müfredat bir seviye daha tanımlar fakat **adım bütçesi değişmez**, dolayısıyla maliyetin
aynı mertebede kalması beklenir. Sapma çıkarsa ölçülen değer raporlanır, bu satır düzeltilmez.

## Makaleye ve teze etkisi

Bu, tezin Kısım III'ünde **açık bırakılmış tek bilimsel kalemdir**. Tamamlandığında iki şeyden
biri olur. Ya öğrenilemezliğin nedeni bulunur ve tezin merkez olumsuz sonucu bir olumlu sonuca
dönüşür, ya da altıncı aday da elenir ve tez *"neden bu çalışmanın ölçtüğü eksenlerin dışındadır"*
diyebilecek duruma gelir. **İkisi de yayımlanabilir bir sonuçtur**, ikincisi bugünkü hâlden daha
güçlüdür çünkü bugün liste tamamlanmamıştır.

⚠️ **M1 ve M5 hakem sürecindedir.** Bu kampanya ikisinin de revizyon turunda sorulacak ilk soruya
cevap üretir. Revizyon mektubu yazılırken başlatılırsa 38 saat gecikme doğar, o yüzden sıra
şimdidir. Sonuç geldiğinde M5 §6 ve M1 §5.8 ölçülmüş hükme çevrilir, tez Kısım III'e ayrı bölüm
olarak işlenir, TR ikizler aynı turda eşitlenir.

---

## ✅ ONAY KAYDI — 15.08.2026

Ön kayıt taslak olarak yazıldı, üç soru soruldu, Mete cevapladı ve **koşu ondan sonra başlatıldı**.

| Soru | Cevap |
|---|---|
| Taban kol yeniden koşulsun mu | **Hayır.** Karar 53'ün `limulus` kolu karşılaştırma tabanıdır |
| Ara basamağın hedef hızı | **30 m/s**, karar 47 ile sürekli |
| Kaç varyant | ⛔ **Tek varyant, `limulus`.** Dört varyanttan indirildi |

**Kapsam indiriminin gerekçesi ve bedeli.** Gerekçe bir bütçe kısıntısı değildir, karar 47 sondası
da tam bu gerekçeyle tek varyant koşmuştur, çünkü **soru mimari karşılaştırma değil
öğrenilebilirliktir**. Bedeli açıkça yazılır, bu kampanya **öğrenme ekseninin mimarileri ayırt
edip etmediği hakkında hiçbir şey söylemeyecektir**. Karar 53'ün o eksendeki hükmü (FARK YOK)
yürürlükte kalır ve bu kampanya onu ne doğrular ne çürütür.

⚠️ **Kural 3 buna göre daraltılır.** Karşılaştırma `limulus` karşısında `limulus`, beş tohum
karşısında beş tohum yapılır. Diğer üç varyant bu kampanyada yoktur ve tablolarda yer almaz.

**Bir şey çıkarsa dört varyantlık tam sürüm ayrı bir ön kayıtla açılır**, bu belgenin kapsamı
genişletilmez.

---

## ⛔ Onay kapısı — kapandı

✅ **Kapandı 15.08.2026.** Üç soru soruldu, cevaplandı, kampanya ondan sonra başlatıldı. Onay
öncesi tek koşu başlatılmamıştır. Aşağıdaki üç nokta kayıt için bırakılmıştır.

1. **Taban kolun yeniden koşulmaması** kabul ediliyor mu. Yirmi koşu tasarrufu var fakat iki
   kampanya farklı günlerde koştu.
2. **Ara basamağın hedef hızı 30 m/s** doğru mu. Karar 47 bu değeri kullandı, bu ön kayıt onu
   sürdürüyor. Başka bir değer istenirse **şimdi** söylenmelidir, sonra değiştirilemez.
3. **Dört varyantın hepsi mi koşsun.** Soru öğrenilebilirliktir, mimari karşılaştırma değildir.
   Tek varyant (`limulus`) yeterli görülürse maliyet dörtte bire iner, fakat karar 53 ile
   karşılaştırma o zaman yalnız bir varyantta yapılabilir.

---

## ✅ Yürütme kaydı — 15.08.2026

**Kampanya 15.08.2026 saat 23:58 UTC'de başlatıldı.** Betik `kampanya_54.sh`, yeniden
başlatılabilir, biten koşuyu atlar, kilitli. Her koşudan sonra kendi yedeğini alır.

**Analiz betiği kampanya BİTMEDEN yazıldı**, `9-DIJITAL-IKIZ/testler/degerlendirme_k54.py`.
Gerekçe ön kayıt disiplininin kendisidir, sonuç görüldükten sonra analiz tasarlama olasılığı
böylece ortadan kalkar. Betik on kuralın doğrudan gerçeklemesidir.

⛔ **Betik iki kol için ayrı ayrı koşar ve bunun teknik bir zorunluluğu vardır.** `MUFREDAT`
ortam değişkeniyle içe aktarım anında seçilmektedir, dolayısıyla iki kol aynı süreçte
değerlendirilemez. Betik `--kol ince` ve `--kol taban` olarak çağrılır, sonra `--karsilastir`.

### Betik taban kolunda sınandı ve karar 53'ün bulgusunu yeniden üretti

Sınama yeni bir sonuç göstermez, yalnız betiğin doğru çalıştığını gösterir. Taban kolun beş
koşusu üzerinde koşuldu ve şu çıktı.

| Kalem | Sonuç |
|---|---|
| Karar 30 veri denetimi | **5/5 geçti** |
| `gecis` görevine ulaşan | **5/5** |
| `gecis` görevini tamamlayan | **0/5** |
| Müfredat çarpanı | 5/5 koşuda **sınandı** |

İlk üç satır karar 53'ün kendi bulgusuyla birebir aynıdır, yani betik bilinen sonucu bağımsız
olarak yeniden üretmektedir.

⚠️ **Dördüncü satır bu kampanyanın ön koşuludur ve tutmuştur.** Kural 5'in dejenerasyon denetimi,
beş koşunun beşinin de kolların ayrıştığı seviyeye ulaştığını göstermektedir. Karar 47'de ince
müfredat kolu dar keşif altında bu seviyeye hiç ulaşamadığı için atıl kalmıştı. Geniş keşif
kolunda o sorun **yoktur**, dolayısıyla müfredat çarpanı bu kampanyada gerçekten sınanacaktır.

---

*Kayıt 15.08.2026 · İlgili `12`, `22`, `30`, `36`, `39`, `41`, `47`, `52`, `53` ·
Protokol `LIMULUS_ELESTIRI_PROTOKOLU.md` · Bekçi protokolü v2*

---

# SONUÇLAR — 15.08.2026, 5/5 koşu tamamlandı

> Bu bölüm kampanya bittikten sonra yazıldı. Yukarıdaki ön kayıt bölümüne **dokunulmadı**.
> Sayılar `degerlendirme_k54.py` çıktısındandır ve o betik **kampanya bitmeden önce** yazılmıştır.

## Yürütme ve veri denetimi (kural 10)

Beş koşu da tamamlandı, `kosular_ince_mufredat/`. **Karar 30 denetimini 5/5 geçti**, `ayar` alanı
her koşuda `mufredat_ince = True`, `log_std0 = −0,5`, γ 0,99, `cruise_itki = True`,
`irtifa_taban = False`, adım dizisi kesintisiz artan ve bütçe tam.

⚠️ Kampanya kesintili koştu, konteyner atıl kalınca süreç ölüyor ve betik ara kayıttan devam
ediyordu. Bu, ön kayıtta yazıldığı gibi **duvar saatini karşılaştırma metriği olmaktan çıkarır**,
görev ve ödül ölçümlerini etkilemez.

## ⛔ Kural 5, dejenerasyon denetimi — ÖNCE BU

**Beş koşunun beşi de kolların ayrıştığı seviyeye ulaştı**, yani müfredat çarpanı bu kampanyada
**gerçekten sınandı**. Karar 47'de sınanamamıştı, orada ince müfredat kolu ayrım seviyesine hiç
varamadığı için çarpan atıl kalmış ve hücre taban hücresinin bit düzeyinde tekrarı çıkmıştı.

Bu satır olmadan aşağıdaki hiçbir sonuç okunamaz.

## Kural 1 ve kural 4, ortak görev üzerinden karşılaştırma

⛔ Seviye indisi karşılaştırılmadı. Karşılaştırma **yalnız ortak görev `gecis` üzerinden** yapıldı.

| | `gecis`e ULAŞAN | `gecis`i TAMAMLAYAN |
|---|---:|---:|
| Taban müfredat (karar 53, `kosular_genis_kesif`) | **5/5** | **0/5** |
| İnce müfredat (bu kampanya) | **0/5** | **0/5** |

**Dondurulmuş hipotez yanlışlandı.** Ara basamak, politikaları `gecis` görevini tamamlar hâle
getirmedi. Getirmediği gibi göreve **vardırmadı** da.

⚠️ **İkinci satır kural 4 gereği tek başına bir hüküm taşımaz.** İnce kolun `gecis`e varması yapı
gereği bir seviye daha gerektirir, dolayısıyla *"ince kol daha geride kaldı"* denemez. Ne
denebileceği aşağıdaki mekanizma ölçümündedir.

## Kural 6, mekanizma denetimi — kampanyanın asıl bulgusu burada

Her iki kol da `hover` ve `dikey` seviyelerini geçmekte, sonra **üçüncü seviyede duvara
çarpmaktadır**. Değişen tek şey duvarın nerede durduğudur.

| | Üçüncü seviyeye varış | Orada harcanan adım | Bütçenin oranı |
|---|---:|---:|---:|
| Taban, duvar `gecis` (60 m/s) | 163.840 - 296.960 | **2.793.062** ± 50.900 | **%93** |
| İnce, duvar `gecis_yarim` (30 m/s) | ~120.000 - 200.000 | **2.847.949** ± 38.276 | **%95** |

**Karar 12 ile plato büyüklüğü karşılaştırıldı, fark 54.886, eşik 101.800, hüküm FARK YOK.**

⛔ **Ölçülen şudur, hedef hızın yarıya indirilmesi duvarı kaldırmamıştır.** Politika her iki kolda
da tam olarak iki terfi almakta ve üçüncü seviyede bütçesinin yaklaşık **yüzde doksan dördünü**
harcayıp terfi edememektedir. Duvar 60 m/s'te de 30 m/s'te de aynı yerdedir, yani engel **hedef
hızın büyüklüğü değildir**.

**Taban kolun deterministik değerlendirmesi bunu tamamlıyor.** `gecis` görevinde on beş bölümün
on beşinde ödül **0,490 ile 0,532** arasında, 0,65 kapısının **altında** ve dar bir bantta.
Bölümler 519-536 adımda sonlanıyor, on beş bin adımlık süre sınırının çok altında, yani
**hiçbiri süre doldurarak bitmiyor**. Azami irtifa on beş bölümün on beşinde **tam 150 m**, yani
başlangıç irtifası, **tırmanma yok**. Tilt kanalı üç tohumda hiç kullanılmıyor (0,0°), iki tohumda
sınırına kadar kullanılıyor (30,0°).

## ⛔ Kural 7 yürürlüğe girdi

Hiçbir tohum `gecis` görevini tamamlayamadı. Ön kayıtta dondurulan cümle aynen geçerlidir.

> *Müfredat basamak büyüklüğü de geçiş görevinin öğrenilememesinin nedeni değildir.
> Öğrenilemezliğin nedeni olarak sınanan altı adayın altısı elenmiş, dolayısıyla neden bu
> çalışmanın ölçtüğü eksenlerin dışında kalmıştır ve tez bunu açık kalem olarak bırakmaktadır.*

## Bu kampanyanın ne söylediği ve ne söylemediği

**Söylediği.** Altıncı ve son aday elendi. Liste artık **tamamlanmıştır**, ödül tanımı, bütçe,
kararlılık, keşif genişliği, müfredat basamak büyüklüğü ve ara basamak eklenmesi sınanmış ve
hiçbiri geçiş görevini öğrenilebilir kılmamıştır. Ayrıca **engelin hedef hızın büyüklüğü olmadığı**
ölçülmüştür, bu yeni ve daraltıcı bir bilgidir.

**Söylemediği.** Engelin ne olduğunu söylemez. Ayrıca ⛔ **bu kampanya öğrenme ekseninin mimarileri
ayırt edip etmediği hakkında hiçbir şey söylemez**, çünkü onayda kapsam tek varyanta indirildi.
Karar 53'ün o eksendeki FARK YOK hükmü yürürlükte kalır.

## Etkilenen belgeler

Tez Bölüm `sec:sonuc-bekleyen`'deki *"geriye sınanmamış tek aday müfredat basamaklarının
büyüklüğüdür"* cümlesi ölçülmüş hükümle değiştirilir. M5 §6 ve M1 §5.8 aynı turda eşitlenir.
`kosular_genis_kesif` silinmez, bu kampanya onun yerine geçmez, yanına ayrı bölüm olarak girer ve
müfredat tanımı her tabloda yazılır (kural 9).

---

*Sonuçlar 15.08.2026 · Betik `9-DIJITAL-IKIZ/testler/degerlendirme_k54.py`, kampanya bitmeden
yazıldı · Çıktılar `k54_ince.json`, `k54_taban.json`, `k54_karsilastirma.json`*
