# 53 — Geniş keşif kampanyası ön kaydı: log_std0 = −0,5 ile yirmi koşu

**Tarih:** 11.08.2026 · **Sınıf:** **ön kayıt** — sonuç görülmeden yazıldı
**Statü:** ✅ **TAMAMLANDI (13.08.2026).** 20/20 koşu, veri denetimi geçti, sonuçlar en altta
**Öncül:** karar `47` kural 4 (keşifsel hipotez, tam ölçekli kampanya ayrı ön kayıt ister) ve
M1 danışman geridönüşü PHASE 1 kalem 1 (DO NOT SUBMIT YET'in tek açık kalemi)
**Kod:** `9-DIJITAL-IKIZ/ogrenme/egitim_v2.py --log-std0 -0.5`
**Dizin:** `kosular_genis_kesif/` (yeni ve ayrı, karar `22`)

> ⚠️ **Bu belge sonuçlar görülmeden yazılmıştır.** Karar kuralları ölçümden önce
> sabitlenmiştir. Sonuçlar ayrı bölüm olarak eklenecek, bu bölüm değiştirilmeyecektir.
> Tadilat gerekirse tarihli ve sonuç görülmeden eklenir.

---

## Neden açıldı ve neden sırası budur

Karar 47 sondası öğrenilemezliğin nedenini yalıttı, keşif genişliği. Fakat kural 4 sonucu
keşifsel hipotez olarak sınıflandırdı ve tam ölçekli kampanya için ayrı ön kayıt şart koştu.
Danışman aynı kampanyayı istiyor. Sonucu gördükten sonra ayar arayıp koşmak, raporlanmış yirmi
koşuluk kampanyanın dondurulmuş karar kurallarını geçersiz kılardı. Doğru sıra şudur, önce bu
ön kayıt, onay, sonra kampanya. Bu belge o sıranın birinci adımıdır.

## Dondurulmuş hipotez

Başlangıç politika standart sapmasının log_std0 = −1,5'ten **−0,5'e** çıkarılması, tam bütçede
(3M adım) politikaları `gecis` görevine taşır. **İki soru açıktır ve kampanya onları ölçer.**
Politika göreve ulaşmakla kalmayıp görevi tamamlıyor mu, ve öğrenme ekseni mimarileri ilk kez
ayırt edebiliyor mu. Ön kayıt bu iki sorunun cevabını taahhüt etmez.

## Kurgu

| Kalem | Değer |
|---|---|
| Varyant | 4 (limulus, ikili, senkron, lift+cruise) |
| Tohum | 5 (0-4) |
| Bütçe | 3.000.000 adım/koşu, toplam **60M adım, 20 koşu** |
| Değişen tek şey | `log_std0 = −0,5` (donmuş kampanyada −1,5) |
| Müfredat | **taban, 6 seviye.** İnce müfredat kullanılmaz, karar 47 katkısını gösteremedi |
| Bayraklar | `LIMULUS_CRUISE_ITKI=1` · **F1 ve F2 KAPALI** (öntanım) · γ 0,99 |
| Dizin | `kosular_genis_kesif/` |
| Bekçi | protokol v2, saatlik dilim, atomik ara kayıt (karar 36'nın emniyetli sürümü) |

⚠️ **Neden F1 ve F2 kapalı.** Üç gerekçe. Birincisi tek değişken kuralı, bir turda bir şey
değişir ve fark tek kaynağa bağlanabilir. İkincisi karşılaştırılabilirlik, bu kampanya
`kosular_uzun` (karar 38) ile yalnız log_std0 farkıyla yan yana okunacak. Üçüncüsü karar 47
sondasının kendisi de bu ayarla koştu, hipotez bu ayarda kuruldu ve bu ayarda sınanır. F1 ile
F2'nin "kısmen yeterli" düzeltmeleriyle birleşik bir kampanya ayrı bir karar olur ve bu ön
kaydın kapsamı dışındadır.

## Karar kuralları — sonuç görülmeden donduruldu

1. **Birincil metrik ulaşılan görev adıdır, ödül değil** (karar 47 kural 1). Seviye indisi
   değil görev adı raporlanır. Varyant başına kaç tohumun `gecis` görevine ulaştığı sayılır.
2. **Terfi yetkinlik değildir** (karar 39 kural 5). `gecis` görevine ulaşmak ayrı, görevi
   **tamamlamak** ayrı raporlanır. Tamamlama ölçütü, deterministik değerlendirmede sonlanma
   nedeninin "süre doldu" olması ve 0,65 kapısının geçilmesidir. Eşik 0,65 dondurulmuş kalır.
3. **Mimari karşılaştırma kapısı.** Öğrenme ekseni ancak dört varyantın da en az üç tohumu
   `gecis` görevinde ölçülebilirse karşılaştırılabilir ilan edilir. O durumda fark, beş tohumun
   standart sapmasının iki katından küçükse **fark yok** yazılır (karar 12 §5 ve 39 kural 4).
4. **İçe geçmişlik denetimi** (karar 12 §5/1). LIMULUS senkron tiltten anlamlı biçimde kötü
   çıkarsa bu mimari bulgu değil eniyileme kusurudur ve öyle yazılır.
5. **Mekanizma denetimi zorunlu** (karar 41 kural 2). Hangi kural sağlanırsa sağlansın irtifa
   izi, azami irtifa, tilt kanalı kullanımı ve sonlanma nedeni dağılımı ölçülür. Kural
   sağlandı diye durulmaz.
6. **Hiçbir tohum görevi tamamlayamazsa şu cümle yürürlüğe girer.** *Keşif genişliği politikayı
   geçiş görevine ulaştırmakta fakat tam bütçede dahi görevi tamamlatmamaktadır. Öğrenme
   ekseni bu kampanyada da mimarileri ayırt edebileceği bir rejime girmemiş ve politikadan
   bağımsız beş metrik mimari hakkındaki tek kanıt olarak kalmıştır.* M1 Bölüm 5.8'in
   "belirsiz" hükmü bu ölçülmüş hükümle değiştirilir, hangi yönde çıkarsa o yönde.
7. **Dondurulmuş kampanyalar raporda kalır** (karar 39 kural 6). `kosular_v2`, `kosular_uzun`
   ve sondalar silinmez, bu kampanya onların yerine geçmez, yanına ayrı bölüm olarak girer ve
   log_std0 değeri her tabloda yazılır. İki set hiçbir tabloda karıştırılmaz.
8. **Hiperparametre aranmaz** (karar 47 kural 6'nın devri). Üçüncü bir log_std0 değeri
   denenmez, bütçe artırılmaz, entropi katsayısı ve öğrenme oranı dokunulmaz kalır ve
   dokunulmadığı makalede beyan edilir.
9. **Veri denetimi** karar 30 protokolüyle, `ayar` alanı log_std0 değerini taşır. Koşu
   bitmeden hiçbir ara sonuç makale ve tez metnine girmez.

## Maliyet — ölçülü, tahmin değil

| Kalem | Değer | Dayanak |
|---|---:|---|
| Duvar saati | **42,5 saat** | karar 38 kampanyası, birebir aynı büyüklük (20 × 3M), ölçülü |
| Bekçi uyanması | **~52** | aynı kampanyanın ölçülü sayısı |
| Saf hesap | ~41 saat | 60M adım, iki işçi ~770 çevre adımı/s dilim defteri |

⚠️ M1 §4.4'ün mevcut dört sayısı (283 adım/s, üç saat, altmış saat, 190 toplam) 10.08
denetiminde günlüklerle çelişik bulundu (denetim kalemi 1.5, karar Mete'de). Bu kampanya
bittiğinde §4.4 ve maliyet beyanı **bu kampanyanın kendi günlüklerinden** yazılır, kaynak
"yirmi koşunun kendi günlükleri" olarak belirtilir ve 1.5 kalemi de böylece tutarlı kapanır.

## Makaleye ve teze etkisi

Tamamlanırsa danışmanın PHASE 1 kalem 1'i kapanır, M1'in gönderim kapısındaki tek engel kalkar.
Kampanya M1'e ayrı bölüm olarak girer, Bölüm 5.8 ölçülmüş hükme çevrilir, Tablo ve figürler
yeni kampanyanın verisiyle genişler, iki figürün standart sapma bandı beş tohumdan beslenir.
Tez Kısım III'e ayrı bölüm olarak işlenir ve `sec:sonuc-ogrenilebilirlik` ile ilişkisi yazılır.
TR ikizler aynı turda eşitlenir.

---

*Kayıt 11.08.2026 · İlgili `12`, `22`, `30`, `36`, `38`, `39`, `41`, `47`, `52` ·
Protokol `LIMULUS_ELESTIRI_PROTOKOLU.md` · Bekçi protokolü v2*

---

# SONUÇLAR — 13.08.2026, 20/20 koşu tamamlandı

> ⛔ **BU BÖLÜMÜN KURAL 1 KISMI HATALIDIR, en alttaki 14.08.2026 tarihli DÜZELTME'ye
> bakınız.** Hatalı cümleler silinmedi, kayıtta bırakıldı.

> Bu bölüm ölçümden sonra yazılmıştır, ön kayıt değiştirilmemiştir.
> Veri `kosular_genis_kesif/`, değerlendirme `9-DIJITAL-IKIZ/ogrenme/k53_degerlendirme.json`,
> betik `testler/degerlendirme_k53.py` (karar 52'nin değerlendirmesiyle aynı yöntem ve tohum
> düzeni).

## Yürütme ve veri denetimi

12.08.2026 08:42 → 13.08.2026 22:54 UTC, **38,2 saat duvar saati** (ölçülü tahmin 42,5 idi).
Kap kampanya boyunca on üç kez süreci öldürdü, on üçünde de atomik ara kayıttan devam edildi ve
**veri kaybı sıfır**. Karar 30 protokolü **20/20 geçti**, dört soyağacı alanı da doğru
(`log_std0 = −0,5`, γ 0,99, `irtifa_taban` false, `cruise_itki` true, `mufredat_ince` false).

⚠️ **Günlükteki `sure` alanı devam eden koşularda yalnız son dilimi sayar.** Koşu başına maliyet
bu yüzden **kesintisiz tamamlanan on üç koşudan** okundu, **1,51-1,98 saat**, hız **421-551
adım/s**, ortalama **480 adım/s**. Kesinti yaşayan yedi koşunun `sure` alanı bir maliyet ölçüsü
olarak kullanılamaz ve kullanılmadı.

## Kural 1 — birincil metrik, ulaşılan görev

**Yirmi koşunun yirmisi `gecis` görevine ulaştı**, varyant başına 5/5. Bir koşu (senkron t2)
daha ileri gidip `gust_gecis` görevine ulaştı. Seviye 2'ye varış 102.400 ile 296.960 adım
arasında, ortanca 156.672.

**Karşılaştırma, donmuş kampanya (karar 38, log_std0 = −1,5, aynı bütçe).** Orada yirmi koşunun
on dokuzu seviye 2'de platoya oturuyor ve yalnız bir koşu (senkron t2) seviye 4'e ulaşıyordu.
Burada erişim tekdüze. **Karar 47'nin keşifsel hipotezinin birinci yarısı tam ölçekte
doğrulandı**, keşif genişliği politikayı geçiş görevine taşıyor.

⚠️ Ve bir tekrar gözlemi: iki kampanyada da daha ileri giden tek koşu **aynı tohum**, senkron t2.

## Kural 2 — terfi yetkinlik değildir, ve bu kez tam ayrıldı

Seviye 2, deterministik, politika başına üç bölüm, toplam 60 bölüm.

| Ölçüt | Sonuç |
|---|---:|
| 0,65 kapısını geçen politika | **0/20** |
| "süre doldu" ile biten bölüm | **0/60** |
| yere çarpmayla biten bölüm | **60/60** |
| normalize ödül bandı | +0,133 ile +0,178 (bir aykırı, ikili t3 −0,407) |
| hayatta kalma payı | %24,8 ile %27,4 |

**Hiçbir politika görevi tamamlamadı.** Kural 6'nın dondurulmuş cümlesi yürürlüğe girdi.

## Kural 5 — mekanizma denetimi

**60 değerlendirme bölümünün 60'ında azami irtifa 150,0 metre**, yani hiçbir politika başlangıç
irtifasının üstüne çıkmadı. Tilt kanalı kullanımı ikili bir davranış gösteriyor, tohumların bir
kısmında tam sıfır, bir kısmında **eylem uzayı tavanı olan 30,0 derece** (limulus t0 ve t4,
ikili t1 ve t3, senkron t2). Kanal doyuma kadar kullanılıyor ve yine kazanım üretmiyor.

## Kural 3 ve 4 — mimari karşılaştırma ilk kez açıldı ve FARK YOK

Dört varyantın da beş tohumu `gecis` görevinde ölçüldü, yani **kural 3'ün karşılaştırma kapısı
ilk kez açıldı.** Öğrenme ekseni bu kampanyada mimarileri ayırt edebileceği rejime en yakın
konuma geldi.

| Varyant | Hayatta kalma payı |
|---|---:|
| limulus | %26,5 ± 0,4 |
| ikili | %25,9 ± 1,1 |
| senkron | %26,4 ± 0,8 |
| lift-cruise | %26,8 ± 0,0 |

**Altı varyant çiftinin altısında da fark iki sapma eşiğinin altında, FARK YOK.** En büyük fark
0,9 puan (ikili ile lift-cruise), en dar eşik 0,8 puan. Kural 4 içe geçmişlik denetimi de temiz,
limulus ile senkron arasındaki fark **0,0 puan**, yani eniyileme kusuru işareti yok.

## Kural 6 — dondurulmuş cümle yürürlükte

> *Keşif genişliği politikayı geçiş görevine ulaştırmakta fakat tam bütçede dahi görevi
> tamamlatmamaktadır. Öğrenme ekseni bu kampanyada da mimarileri ayırt edebileceği bir rejime
> girmemiş ve politikadan bağımsız beş metrik mimari hakkındaki tek kanıt olarak kalmıştır.*

⚠️ **Bir daraltma, ön kaydın öngörmediği ve lehte olan yön.** Bu kampanyada karşılaştırma kapısı
açıldı ve "ölçülemedi" değil **"ölçüldü ve fark çıkmadı"** denebiliyor. Önceki kampanyalarda
öğrenme ekseninden hiçbir hüküm çıkarılamıyordu, şimdi yirmi koşuluk beş tohumlu bir kampanyada
dört mimarinin ayırt edilemediği **ölçülmüş** bir sonuçtur. Bu, merkez bulguyu zayıflatmaz,
kanıt tabanını genişletir.

## Kural 8 — hiperparametre aranmadı

Üçüncü bir log_std0 değeri denenmedi, bütçe artırılmadı, entropi katsayısı ve öğrenme oranı
dokunulmadı.

## M1'e etkisi ve maliyet beyanı

Danışmanın PHASE 1 kalem 1'i **kapandı**, M1'in gönderim kapısındaki tek engel kalktı. Bölüm 5.8
"belirsiz" hükmü ölçülmüş hükümle değiştirilecek. §4.4'ün dört çelişik sayısı (10.08 denetimi
kalem 1.5) bu kampanyanın kendi günlüklerinden yazılacak, kaynak *"yirmi koşunun kendi
günlükleri"*, değerler yukarıdaki ölçülü bandlar.

---

# ⛔ DÜZELTME — 14.08.2026, kural 1 yorumu hatalıydı

> Bu bölüm SONUÇLAR yazıldıktan sonra, M1 paketi hazırlanırken bulunan bir hatayı
> kaydeder. Yukarıdaki hatalı cümleler **silinmemiştir**, karar belgeleri geriye dönük
> temizlenmez. Ön kayıt gövdesine dokunulmamıştır.

## Ne yanlıştı

SONUÇLAR'ın kural 1 kısmı şunu yazıyor.

> *"Yirmi koşunun yirmisi `gecis` görevine ulaştı... Orada yirmi koşunun on dokuzu seviye
> 2'de platoya oturuyor ve yalnız bir koşu seviye 4'e ulaşıyordu. Burada erişim tekdüze.
> Karar 47'nin keşifsel hipotezinin birinci yarısı tam ölçekte doğrulandı."*

Son cümle **ölçümle desteklenmiyor.** Donmuş kampanyanın (karar 38, `kosular_uzun`) günlükleri
açılıp aynı betikle okunduğunda, orada da **yirmi koşunun yirmisi seviye 2'ye, yani `gecis`
görevine ulaşıyor.** "Seviye 2'de platoya oturuyor" ifadesi, platonun `gecis` görevinin
**üstünde** olduğunu söylüyor, `gecis`e ulaşılamadığını değil. Karşılaştırma o gün günlükten
değil metinden yapıldığı için bu iki okuma karıştı.

## Ölçülen karşılaştırma

Kaynak, iki kampanyanın kendi `*_gunluk.json` dosyaları, betik
`10-MAKALELER/M1_.../02_MAKALE_AKTIF/figurler/kampanya_karsilastirma.py`.

| Ölçüt | Donmuş, log_std0 = −1,5 | Geniş keşif, log_std0 = −0,5 |
|---|---|---|
| Ulaşılan en yüksek seviye dağılımı | 19 × sev 2, 1 × sev 4 | **19 × sev 2, 1 × sev 4** |
| Seviye 4'e ulaşan koşu | senkron t2 | **senkron t2** |
| Seviye 2'ye varış, ortanca | 197.632 adım | 156.672 adım |
| Seviye 2'ye varış, ort ± sapma | 216.371 ± 58.231 | 161.382 ± 41.461 |
| Son ödül, varyant ortalamaları | +0,002 ile +0,071 | +0,006 ile +0,072 |
| 0,65 kapısını geçen politika | 0/20 | 0/20 |
| Azami irtifa | 150,0 m | 150,0 m |

## Düzeltilmiş hüküm

**Ön kaydın birincil metriğinde (kural 1, ulaşılan görev adı) iki kampanya ayırt
edilememektedir.** Geniş keşfin ölçülen tek etkisi **varış zamanıdır**, ortanca 40.960 adım
erken, ve bu fark projenin kendi iki sapma eşiğinin (2 × 58.231 = 116.462 adım) altındadır.
Karar 47'nin keşifsel hipotezi **tam ölçekte doğrulanmamıştır.** Doğru ifade şudur, keşif
genişliği bir **hızlandırmadır**, bir **açma** değildir.

⚠️ Kural 6'nın dondurulmuş cümlesi yürürlükte kalmaktadır, çünkü koşulu (hiçbir tohumun görevi
tamamlayamaması) sağlanmıştır. Fakat cümlenin *"keşif genişliği politikayı geçiş görevine
ulaştırmakta"* diyen birinci yarısı bu ölçümle daralmaktadır ve makalelerde cümle, hemen
ardından gelen bu düzeltmeyle birlikte yazılacaktır.

## Neyi güçlendirdiği

Bu, kötü haber değildir. Kalan engeli keşif ayarına yıkan açıklamayı da elemektedir, dolayısıyla
M1 Bölüm 5.8'in hükmü artık "belirsiz" değil, **"iki ayrı keşif ayarında ölçüldü ve birincil
metrikte fark çıkmadı"** olmaktadır. M5'in §5.5 ablasyonu 300 bin adımlık bütçede geçerli
kalmakta, fakat sonuç cümlesinin *"kalan engel bir keşif ayarıdır"* diyen kısmı daralmaktadır.

## Etkilenen belgeler

`CLAUDE.md` güncelleme 35, `M1_*_v8` (§4.3, §4.4, §5.8, yeni §5.9, §6.2, §6.3, §7, Öz),
`M5_*_v6` (§5.5, §6 üçüncü açık kalem, §7, Öz). Hepsi 14.08.2026 turunda işlendi.
