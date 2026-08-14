# 47 — Geçiş görevinin öğrenilebilir kılınması, ön kayıt

**Tarih:** 09.08.2026 · **Sınıf:** **ön kayıt** · **Etkilenen:** Bölüm 16, M5, bekleyen
hesaplamalı kalemler
**Kod:** `ogrenme/ortam.py` → `MUFREDAT_INCE`, bayrak `LIMULUS_MUFREDAT_INCE` ·
`ogrenme/egitim_v2.py` → `--log-std0`, `--cikti`
**Durum:** ⬜ kurallar donduruldu, sonda koşuluyor

> ⚠️ **Bu bölüm sonuçlar görülmeden yazılmıştır.** Karar kuralları ölçümden önce sabitlenmiştir.
> Sonuçlar ayrı bir bölüm olarak eklenecek, bu bölüm değiştirilmeyecektir.

---

## Neden açıldı

Karar 41'in bulgusu şuydu. Ödül tanımında iki kusur bulundu (irtifa ölü bölgesi ve iskonto ufku),
ikisi düzeltildi ve **hiçbir politika geçiş görevini yine öğrenmedi.** Aynı ortamda klasik
kontrolcü görevi tamamladı, yani görev ulaşılabilir, eylem uzayı yeterli ve fizik engel değil.

Buradan çıkan tespit şuydu — ödül tanımına yapılan iki müdahale davranışı değiştirmediğine göre
sıra **keşif kurgusu** ile **müfredat basamaklarının büyüklüğüne** gelmiştir. Kalem bekleyenler
listesinde bu ifadeyle duruyordu ve Mete onayladı.

## İki aday açıklama

**Keşif genişliği.** Politikanın başlangıç eylem sapması `log_std0 = -1,5` değerindedir, yani
sapma yaklaşık $0{,}22$. Bu değer D2 düzeltmesiyle $-0{,}5$ değerinden düşürülmüştü, gerekçesi
başlangıçta aracın kontrolsüz savrulmasını engellemekti. Fakat düşük sapma, geçiş görevinin
gerektirdiği büyük tilt yönelimlerinin hiç denenmemesi anlamına da gelebilir. Yani D2, hover'ı
öğretirken geçişi öğrenilemez kılmış olabilir.

**Müfredat basamağı.** Taban müfredatta seviye 1 (`dikey`, hedef hız 0) ile seviye 2 (`gecis`,
hedef hız 60 m/s) arasındaki basamak, hedef hızı bir adımda sıfırdan altmışa çıkarmaktadır. Hiçbir
koşu bu basamağı geçmemiştir. Basamak bölünürse geçilebilir olabilir.

## Yöntem

**2 × 2 çarpan tasarımı**, her hücrede iki tohum, yani sekiz koşu. Varyant tek tutulmuştur
(`limulus`), çünkü soru mimari karşılaştırma değil öğrenilebilirliktir.

| Hücre | `log_std0` | Müfredat | Koşu |
|---|---:|---|---:|
| A (taban) | $-1{,}5$ | taban, 6 seviye | 2 |
| B (geniş keşif) | $-0{,}5$ | taban, 6 seviye | 2 |
| C (ince müfredat) | $-1{,}5$ | ince, 7 seviye | 2 |
| D (ikisi birlikte) | $-0{,}5$ | ince, 7 seviye | 2 |

Bütçe koşu başına **300 bin adım**. Gerekçe, 300 bin adımda taban kurgunun seviye 1'e ulaştığının
ölçülmüş olmasıdır, yani bütçe seviye ilerlemesini görmeye yetmektedir. Bu bir **sonda**dır, tam
ölçekli kampanya değildir.

İnce müfredat aynı iki seviyenin arasına 30 m/s hedefli bir ara basamak koyar, başka hiçbir şey
değişmez. Seviye sayısı 6'dan 7'ye çıkar.

⚠️ **İki bayrak da öntanım olarak eski davranışı verir** (karar 22). Sonda koşuları ayrı dizine
yazılır, tamamlanmış kampanyaların günlükleri değişmez.

## Karar kuralları — sonuçlar görülmeden donduruldu

**Kural 1 — birincil metrik ulaşılan seviyedir, ödül değil.** Soru "politika daha çok ödül
topluyor mu" değil, "geçiş görevine varıyor mu" biçimindedir. Ödül ölçekleri müfredat
değiştiğinde karşılaştırılamaz hâle gelmektedir.

⚠️ **Seviye indisi iki müfredat arasında doğrudan karşılaştırılamaz**, çünkü ince müfredatta
indisler 2'den sonra bir kayar. Karşılaştırma **görev adıyla** yapılır. Başarı ölçütü,
`gecis` görevine (hedef hız 60 m/s) ulaşılmasıdır.

**Kural 2 — başarı eşiği.** Bir hücrenin taban hücreyi geçtiği söylenebilmesi için, o hücrenin
**iki tohumunun ikisinin de** taban hücrenin en iyi tohumundan daha ileri bir göreve ulaşması
şarttır. Tek tohumluk ilerleme, gözlem olarak kaydedilir fakat sonuç sayılmaz.

**Kural 3 — `gecis` görevine hiçbir hücrede ulaşılamazsa şu cümle yürürlüğe girer.** *Keşif
genişliği ve müfredat basamak büyüklüğü, geçiş görevinin öğrenilememesinin nedeni değildir. İki
müdahale de üç yüz bin adımlık bütçede davranışı değiştirmemiştir. Öğrenilemezliğin nedeni bu
sondanın kapsamı dışındadır.*

**Kural 4 — bir hücre `gecis`e ulaşırsa sonuç keşifseldir, hüküm değil.** Sekiz koşu ve iki tohum,
bir mimari iddia için yeterli değildir. Ulaşılırsa bu bir **hipotez** olarak kaydedilir ve tam
ölçekli kampanya için ayrı bir ön kayıt yazılır. Kısım III'ün olumsuz sonucu bu sondayla geri
alınmaz.

**Kural 5 — bütçe kısıtı beyan edilir.** Sonda iki çekirdekli bir makinede koşulmaktadır ve koşu
başına yaklaşık dokuz dakika sürmektedir. Sekiz koşunun tamamı tamamlanamazsa **kaç koşunun
tamamlandığı ve hangi hücrelerin eksik kaldığı yazılır.** Eksik hücre sessizce atlanmaz.

**Kural 6 — hiperparametre aranmayacaktır.** $-0{,}5$ ve 30 m/s değerleri burada, ölçümden önce
yazılmıştır. Sonuç olumsuz çıkarsa üçüncü bir değer denenmez, sonuç yazılır ve kalem tam ölçekli
bir çalışmaya devredilir.

---

*Tarih 09.08.2026 · Ön kayıt sonda koşulmadan yazıldı · İlgili `41` (iki ödül kusuru ve olumsuz
sonuç), `39` (müfredat eşiği aklanması), `22` (bayrak ve ayrı dizin kuralı), `25` (bölüm uzunluğu
bandı)*

---

# ARA KAYIT — ilk koşum kesildi, kural 5 uygulandı (09.08.2026)

⚠️ **Sekiz koşunun sıfırı tamamlandı.** Ön kaydın beşinci kuralı, sondanın tamamlanamaması hâlinde
kaç koşunun bittiğinin ve hangi hücrelerin eksik kaldığının yazılmasını, eksik hücrenin sessizce
atlanmamasını şart koşuyordu. Kural burada uygulanmaktadır.

**Ne oldu.** Sonda paralel kurgulandı, hücre A ve hücre B tohum 0 ile eşzamanlı başladı ve ikisi de
**71 680 / 300 000 adımda** kesildi. Hücre C ve D hiç başlamadı, tohum 1 hiç başlamadı. Kesilme
nedeni koşum ortamının süreçleri toplaması, bir model ya da kod hatası değil, ara denetim
noktalarının ikisi de tutarlı yazılmış durumda.

**Yorum yapılmayacak.** İki hücrenin kesilme anındaki ara durumu kayda geçirilmektedir fakat
**sonuç sayılmamaktadır**, çünkü bütçenin dörtte biri koşulmuştur ve ön kayıt karşılaştırmayı 300
bin adımda tanımlamıştır.

| Hücre | log_std0 | Müfredat | Kesilme adımı | O andaki görev |
|---|---:|---|---:|---|
| A | $-1{,}5$ | taban | 71 680 | `dikey` (seviye 1), 47 104 adımda geçmiş |
| B | $-0{,}5$ | taban | 71 680 | `hover` (seviye 0) |
| C | $-1{,}5$ | ince | başlamadı | --- |
| D | $-0{,}5$ | ince | başlamadı | --- |

## Kesilmenin yanında ölçülmüş bir başka şey, verim

Kesilme, koşum kurgusunda bir kusur da ortaya çıkardı ve bu düzeltilmiştir.

| Kurgu | Koşu başına verim | Toplam verim | Kaynak |
|---|---:|---:|---|
| Tek süreç, tam koşu | **283 adım/s** | 283 adım/s | sıralı koşumun kendi günlüğü |
| İki süreç paralel | 95 adım/s | **190 adım/s** | kesilen koşumun günlüğü |
| Tek süreç, duman testi | 585 adım/s | --- | 8192 adımlık test, aşağıdaki uyarıya bakınız |

Paralel koşum toplam verimi yaklaşık **bir buçuk kat düşürmektedir.** Nedeni, torch'un zaten iki
çekirdeği kullanması ve iki sürecin aşırı abone olmasıdır. Sonda bu ölçüm üzerine **sıralı** koşuma
çevrilmiştir, betikteki gerekçe yorumuyla birlikte. Sıralı kurguda 300 bin adım yaklaşık **on sekiz
dakika**, sekiz koşu yaklaşık **iki buçuk saat** sürmektedir.

⚠️ **Kendi tahminimi de düzeltmem gerekiyor ve nedeni kayda değer.** Sondayı başlatmadan önce
maliyeti 8192 adımlık bir duman testinden kestirdim, o test 585 adım/s verdi ve buradan koşu başına
sekiz buçuk dakika çıkardım. Tam koşu 283 adım/s veriyor, yani gerçek maliyet **iki kattan fazla**.
Duman testi kısa olduğu için ısınma, gözlem normalizasyonu istatistiklerinin oturması ve müfredat
seviyesi ilerledikçe bölümlerin uzaması gibi maliyetleri hiç görmüyor. Küçük bir örnekten doğrusal
ölçekleme yapmak bu projede daha önce de yanlış çıkmıştı, bu yüzden **kural olarak kaydedilir**, bir
koşum maliyeti duman testinden değil aynı bütçedeki bir koşunun kendi günlüğünden kestirilir.

⚠️ Bu, ön kaydın hiçbir karar kuralını değiştirmemektedir. Değişen şey yalnız koşum sırasıdır, bütçe
ve karşılaştırma tanımı aynıdır.

**Sonda yeniden başlatıldı** ve sonuçları geldiğinde bu belgeye ayrı bir SONUÇLAR bölümü olarak
eklenecektir.

---

# ARA KAYIT 2 — ikinci koşum da bitmedi, kural 5 yine uygulandı (09.08.2026, 23:05)

⚠️ **Bu bir SONUÇLAR bölümü değildir.** Sekiz koşunun **altısı** tamamlanmıştır, iki hücre
eksiktir ve ön kaydın kural 5'i gereği eksik hücreler burada adıyla yazılmaktadır. Toplayıcı betik
`testler/topla_k47.py` eksik veriyle çağrıldığında sonuç bölümü yazılamayacağını bildirmekte ve
tabloyu **ara durum** olarak etiketlemektedir.

## Tamamlanan ve eksik hücreler

| Hücre | Kurgu | Tohum | Adım | Ulaşılan görev | Durum |
|---|---|---:|---:|---|---|
| A | taban | 0 | 301.056 | `dikey` | tamam |
| A | taban | 1 | 301.056 | `dikey` | tamam |
| B | geniş keşif | 0 | 301.056 | `gecis` | tamam |
| B | geniş keşif | 1 | 301.056 | `gecis` | tamam |
| C | ince müfredat | 0 | 301.056 | `dikey` | tamam |
| C | ince müfredat | 1 | 165.888 | `hover` | **EKSİK, koşuyor** |
| D | ikisi birlikte | 0 | 301.056 | `gecis_yarim` | tamam |
| D | ikisi birlikte | 1 | — | — | **EKSİK, başlamadı** |

**Eksik iki hücre C tohum 1 ve D tohum 1'dir.** Kural 2 bu iki hücre için **uygulanamaz**
durumdadır, çünkü kural bir hücrenin iki tohumunun da tamamlanmasını şart koşmaktadır. B hücresi
için kural 2 uygulanabilmiş ve **sağlanmıştır**, iki tohumun ikisi de taban hücrenin en iyi
tohumundan (`dikey`) ileri bir göreve (`gecis`) ulaşmıştır. Bu satır ara kayıt niteliğindedir ve
hüküm doğurmamaktadır, çünkü karşılaştırmanın diğer iki kolu kapanmamıştır.

⚠️ **Görev adları kullanılmıştır, seviye indisleri kullanılmamıştır.** İnce müfredat kolunda
indisler kaymaktadır, `gecis_yarim` görevi indeks 2'ye eklendiği için o koldaki ikinci seviye taban
koldaki ikinci seviyeyle **aynı görev değildir**. Toplayıcı betik eşlemeyi hücre dizin adından
yapmaktadır.

## Süre tahmini üçüncü kez tutmadı, fakat bu kez nedeni farklı

Önceki ara kayıt, koşum maliyetinin duman testinden kestirilmesinin yanlış olduğunu yazmış ve
**283 adım/s** değerini doğru taban olarak kaydetmişti. Bu kez o taban tutmuş, tutmayan şey
**makinenin boş olduğu varsayımı** olmuştur.

| Koşu | Süre | Eşzamanlı başka ölçüm |
|---|---:|---|
| A t0 | 966 s | yok |
| B t0 | **2752 s** | karar 48 tilt kilidi ölçümü |
| C t0 | **2341 s** | karar 48 tilt kilidi ölçümü |
| D t0 | 1075 s | yok |
| A t1 | 948 s | yok |
| B t1 | 972 s | yok |

Boş makinede dört koşu **948 ile 1075 saniye** arasında, yani ortalama 990 saniye ve yaklaşık
304 adım/s. Karar 48 ölçümü (1080 çözüm, 57 dakika) eşzamanlı koştuğunda aynı iş **2,4 ile 2,8 kat**
yavaşlamıştır. Yani "18 dakika ve sekiz koşu 2,5 saat" tahmini **boş makine için doğruydu**.

⚠️ **Bu, aynı oturumda ölçüp yazdığım bir kuralı kendi elimle ihlal etmemdir.** Sonda betiği
paralel koşarken iki sürecin toplam veriminin üç kat düştüğü **ölçülmüş** ve betik tam bu yüzden
sıralı hâle getirilmişti, gerekçesi de betiğin içine yazılmıştı. Sonra karar 48 ölçümünü aynı
makinede sondanın yanına başlattım. Sonda kendi içinde sıralıydı, **ölçümler arasında sıralı
değildi**. Kural bu yüzden bir seviye yukarı taşınarak yeniden yazılır.

> **Bir makinede aynı anda yalnız bir ölçüm koşar.** Sıralılık bir betiğin içinde değil, bütün
> ölçümler kümesinde sağlanır. İkinci bir ölçüm başlatılacaksa ya birincisinin bitmesi beklenir ya
> da başlatma anı ve süresi koşu günlüğüne yazılır, yoksa süreler karşılaştırılamaz hâle gelir.

Bu ihlalin **sonuçlara etkisi yoktur** ve nedeni yazılıdır, PPO'nun gördüğü adım sayısı, tohum,
ödül tanımı ve müfredat eşzamanlılıktan etkilenmemektedir, etkilenen tek şey duvar saati süresidir.
Bütçe adım cinsinden tanımlıdır, saniye cinsinden değil.

## Beklenen kalan süre

C tohum 1 şu an 165.888 adımda ve boş makine hızıyla yaklaşık **7 dakikada** bitmektedir. Ardından
D tohum 1 yaklaşık **17 dakika** almaktadır. Toplam kalan yaklaşık **24 dakika** olup bu tahmin
boş makine ölçümüne dayanmaktadır ve makine şu an boştur.

**Sonda bitince SONUÇLAR bölümü ayrı bir bölüm olarak eklenecektir.** Bu ara kayıt ve yukarıdaki
ön kayıt o zaman da değiştirilmeyecektir.

*Ara kayıt 2 tarihi 09.08.2026 23:05 · Toplayıcı `testler/topla_k47.py` · Günlük `/tmp/k47b.log`*

---

# SONUÇLAR — 09.08.2026, sekiz koşu tamamlandı

> Bu bölüm ölçümden **sonra** yazılmıştır. Ön kayıt, ARA KAYIT ve ARA KAYIT 2 bölümleri
> değiştirilmemiştir. Toplayıcı `testler/topla_k47.py`, günlük `/tmp/k47b.log`, veri
> `ogrenme/kosular_k47/{A,B,C,D}/`.

## Kural 5 — sekizin sekizi tamamlandı

| Hücre | Kurgu | Tohum | Adım | Ulaşılan görev | Son ödül | Ort. bölüm |
|---|---|---:|---:|---|---:|---:|
| A | taban | 0 | 301.056 | `dikey` | $+0{,}500$ | 734 |
| A | taban | 1 | 301.056 | `dikey` | $+0{,}324$ | 731 |
| B | geniş keşif | 0 | 301.056 | **`gecis`** | $-0{,}287$ | 555 |
| B | geniş keşif | 1 | 301.056 | **`gecis`** | $-0{,}062$ | 608 |
| C | ince müfredat | 0 | 301.056 | `dikey` | $+0{,}500$ | 734 |
| C | ince müfredat | 1 | 301.056 | `dikey` | $+0{,}324$ | 731 |
| D | ikisi birlikte | 0 | 301.056 | `gecis_yarim` | $-0{,}035$ | 558 |
| D | ikisi birlikte | 1 | 301.056 | `gecis_yarim` | $+0{,}213$ | 612 |

Eksik hücre yoktur. Kural 1 gereği birincil metrik **ulaşılan görev adıdır**, ödül sütunu yalnız
kayıt içindir ve aşağıda neden karşılaştırılamaz olduğu yazılmaktadır.

## Kural 2 — iki hücre tabanı geçti, biri geçmedi

Taban hücrenin en iyi tohumu `dikey` görevine ulaşmaktadır. Eşik, bir hücrenin **iki tohumunun
ikisinin de** bundan ileri bir göreve varmasıdır.

| Hücre | Tohumların ulaştığı görev | Kural 2 |
|---|---|---|
| B geniş keşif | `gecis`, `gecis` | **GEÇTİ** |
| C ince müfredat | `dikey`, `dikey` | geçmedi |
| D ikisi birlikte | `gecis_yarim`, `gecis_yarim` | **GEÇTİ** |

Geçen iki hücrenin **ortak yanı geniş keşiftir**, $\log\sigma_0 = -0{,}5$. Geçmeyen hücre ise tek
başına ince müfredatı taşıyan hücredir. İki tohumun da aynı göreve varması dört hücrenin
dördünde gerçekleşmiştir, yani sonuç tohumlar arasında oynak değildir.

## Kural 4 yürürlüğe girdi, kural 3 girmedi

`gecis` görevine **B hücresinin iki tohumunda da ulaşılmıştır**, dolayısıyla kural 3'ün
dondurulmuş cümlesi **yürürlüğe girmemektedir**. Kural 4 işlemektedir ve hükmü şudur, sekiz koşu
ve iki tohum bir mimari iddia için yeterli değildir, sonuç bir **hipotez** olarak kaydedilir.

> **Keşifsel hipotez.** Geçiş görevinin üç yüz bin adımlık bütçede öğrenilememesinde belirleyici
> etken **keşif genişliğidir**, müfredat basamak büyüklüğü değildir. Başlangıç politika standart
> sapmasını $\log\sigma_0 = -1{,}5$'ten $-0{,}5$'e çıkarmak, tek başına, iki tohumun ikisinde de
> politikayı `dikey` görevinden `gecis` görevine taşımaktadır. Müfredat basamağını incelten
> müdahale ise tek başına hiçbir ilerleme üretmemektedir.

⚠️ **Bu bir hüküm değildir ve Kısım III'ün olumsuz sonucunu geri almamaktadır.** Sonda,
politikanın `gecis` görevine ulaşabildiğini göstermektedir, o görevi **başardığını**
göstermemektedir. Ulaşmak müfredat kapısının açılması demektir, ödül eşiğinin bir pencere boyunca
tutulmasıdır, görevin tamamlanması değildir. Tam ölçekli bir kampanya için ayrı bir ön kayıt
yazılacaktır ve kural 6 gereği üçüncü bir $\log\sigma_0$ değeri **aranmamıştır**.

## Tasarım dejenerasyonu — ölçüm sırasında bulundu, ön kayıtta yok

⚠️ Aşağıdaki bulgu ön kayıtta bulunmamaktadır. **Ölçüm sırasında ve sonuçlar yorumlanmadan önce**
bulunmuş, koddan doğrulanmış ve buraya yazılmıştır. Ön kayıt değiştirilmemiştir.

`LIMULUS_MUFREDAT_INCE=1` bayrağı yeni görevi **indeks 2'ye** eklemektedir. Dolayısıyla seviye 0
(`hover`) ve seviye 1 (`dikey`) iki kolda **birebir aynıdır**, ayrım ancak seviye 2'de
başlamaktadır.

Sonucu şudur. **Seviye 1'i geçemeyen bir koşuda müfredat çarpanı atıl kalmaktadır** ve o hücre
bağımsız bir ölçüm değil, aynı ölçümün tekrarıdır. Ölçüm bunu en güçlü biçimde doğrulamaktadır.

| Karşılaştırma | Ödül | Bölüm uzunluğu | Görev |
|---|---:|---:|---|
| A t0 karşısında C t0 | $+0{,}500$ ve $+0{,}500$ | 734 ve 734 | `dikey` ve `dikey` |
| A t1 karşısında C t1 | $+0{,}324$ ve $+0{,}324$ | 731 ve 731 | `dikey` ve `dikey` |

**İki tohumda da birebir aynı.** Yani C hücresi A hücresinin bit düzeyinde bir tekrarıdır ve
$2\times2$ çarpan tasarımı **etkide tam çaprazlanmamaktadır**, bir çarpan diğerinin başarısına
koşulludur. Etkin olarak üç ayrı hücre ölçülmüştür, A ile C aynı hücredir.

**Bunun kural 2 yorumuna etkisi vardır ve yazılması gerekir.** Tabloda *"C geçmedi"* satırı, ince
müfredatın başarısız olduğunun kanıtı **değildir**. O satırın anlamı, ince müfredatın dar keşif
altında **hiç sınanmamış** olmasıdır, çünkü politika kolların ayrıştığı seviyeye hiç ulaşmamıştır.
Müfredat çarpanının sınandığı tek yer geniş keşif kolu, yani B ile D karşılaştırmasıdır.

⚠️ **Bu bir kod kusuru değildir.** Bayrak çalışmaktadır ve doğrulanmıştır, çevre değişkeni 0 iken
altı görev, 1 iken yedi görev tanımlanmaktadır. Dejenerasyon müfredat tanımının doğal sonucudur.
Ön kayıt indislerin kaydığını görmüş ve karşılaştırmanın görev adıyla yapılmasını şart koşmuştu,
fakat **ilk iki seviyenin özdeş olmasının çarpanı atıl kılacağını** görmemişti.

## B ile D karşılaştırması, ödül tuzağı

D hücresinin ödülleri B hücresinden yüksektir, $-0{,}035$ karşısında $-0{,}287$ ve $+0{,}213$
karşısında $-0{,}062$. **Bu bir iyileşme değildir** ve nedeni görevlerin farklı olmasıdır.

| Kol | Seviye 2'deki görev | Hedef hız |
|---|---|---:|
| Taban (B) | `gecis` | \SI{60}{\meter\per\second} |
| İnce (D) | `gecis_yarim` | \SI{30}{\meter\per\second} |

D, aynı seviye indisinde **yarı hedef hızlı** bir görevde çalışmaktadır. Ödül izleme hatasının
fonksiyonu olduğuna göre, daha kolay bir hedefi izleyen bir koşu daha yüksek ödül alır. Kural 1
tam olarak bunu öngörmüş ve *"ödül ölçekleri müfredat değiştiğinde karşılaştırılamaz hâle
gelmektedir"* diye yazmıştı.

Bölüm uzunlukları bu okumayı desteklemektedir, 555 karşısında 558 ve 608 karşısında 612, yani
davranış aynı mertebede kalmaktadır ve değişen şey görevin zorluğudur.

**Dolayısıyla ince müfredatın ölçülen katkısı yoktur ve görünen katkısı bir yapaylıktır.** Geniş
keşif kolunda ince müfredat, politikayı `gecis`e taşımak yerine **daha kolay bir ara görevde
durdurmuştur**. Bu, ince müfredatın zararlı olduğunu kanıtlamaz, çünkü D hücresi bütçesini ara
basamakta harcamış olabilir, fakat **yararlı olduğunu da göstermez**.

## Kural 6 — hiperparametre aranmadı

$-0{,}5$ ve \SI{30}{\meter\per\second} değerleri ön kayıtta yazılmıştı. Sonuç bir kolda olumlu
çıktığında üçüncü bir $\log\sigma_0$ değeri **denenmemiştir** ve ince müfredat için ikinci bir ara
hız **denenmemiştir**. Kalem tam ölçekli bir çalışmaya devredilmektedir.

## Bu sondanın kapattığı ve açık bıraktığı

**Kapanan.** Karar 41'in bıraktığı *"öğrenilemezliğin nedeni ne"* sorusu bir yönde daraldı. Neden
müfredat basamağı değil, **keşif genişliği** yönünde. Karar 39 müfredat eşiğini aklamıştı, bu sonda
müfredat **basamağını** da aklıyor, ikisi aynı yönde.

**Açık kalan.** `gecis` görevine ulaşmak onu başarmak değildir, tam ölçekli bütçede ne olduğu
bilinmemektedir. İnce müfredatın dar keşif altındaki etkisi **hiç ölçülmemiştir** ve dejenerasyon
nedeniyle bu sondayla ölçülemez. Üçüncü bir $\log\sigma_0$ değeri denenmemiştir. Sonda, Kısım III'ün
politikadan bağımsız beş metrikteki sonucunu değiştirmemektedir.

⚠️ **Bir kayıt eksiği.** `ayar` sözlüğü `mufredat_ince` alanını taşımamaktadır, dolayısıyla bir
koşunun günlüğünden hangi kolda olduğu okunamamaktadır. Kol, hücre dizin adından kurtarılmaktadır
ve toplayıcı betik bunu böyle çözmektedir, veri kaybı yoktur. Alan kampanya bittikten sonra
eklenmiştir, ortasında eklenmemiştir, çünkü o durumda sekiz koşunun bir kısmı alanı taşır bir kısmı
taşımaz ve kampanya kendi içinde tutarsız olur.

---

*Sonuçlar 09.08.2026'da yazıldı · Sekiz koşu, 2.408.448 adım · Toplayıcı `testler/topla_k47.py`
· Dejenerasyon bulgusu keşifsel, ön kayıtta yok*
