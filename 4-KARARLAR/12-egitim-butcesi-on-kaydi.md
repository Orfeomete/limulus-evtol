# Eğitim Koşusu Ön Kaydı — pilot deney ve düzeltilmiş koşu

**Tarih:** 03.08.2026 · **Statü:** ön kayıt, tam sonuçlar görülmeden yazıldı

---

## Bu belge neden var

Pekiştirmeli öğrenme deneylerinde en yaygın geçerlilik sorunu şudur. Sonuç beklendiği gibi
çıkmayınca hiperparametre ayarlanır, koşu tekrarlanır ve beğenilen sonuç raporlanır. Bu, hipotezi
veriye göre ayarlamaktır ve o noktadan sonra hiçbir sayı savunulamaz.

Bu belge o riski kapatmak için yazıldı. **Düzeltilmiş koşunun her ayarı, pilot deneyin tam
sonuçları görülmeden burada sabitlenmiştir.** Belgede yazılmayan hiçbir değişiklik yapılmayacaktır.
Yapılırsa buraya tarihiyle eklenecektir.

---

## 1. Pilot deneyin durumu

**Kurgu.** 4 konfigürasyon × 5 tohum × 400.000 çevre adımı, altı seviyeli müfredat, eşik 0,65.

**Bu belge yazılırken elde olan.** İlk tohum setinin dördü ve ikinci tohumun ikisi tamamlanmıştı.
Kalan koşular sürüyordu, hiçbir toplu karşılaştırma yapılmamıştı.

**Gözlenen.** Hiçbir koşu müfredatın birinci seviyesini geçemedi. Ortalama bölüm uzunluğu, azami
1000 adıma karşılık **79 adım** çıktı. Yani ajan yaklaşık 1,6 saniye sonra düşüyor.

Öğrenme eğrisi düz değil, yükseliyor (−0,169 → +0,290) ama çok yavaş. Sorun ajanın öğrenememesi
değil, **öğrenmeye hiç fırsat bulamaması**. Bölüm bu kadar erken bittiğinde takip ödülü
toplanamıyor, gradyan büyük ölçüde çökme cezasından geliyor.

---

## 2. Teşhis

Kök neden başlangıç koşullarıdır ve doğrudan hesaplanabilir.

Politikanın çıkış katmanı sıfıra yakın başlatılmıştır, dolayısıyla ilk eylem ortalaması sıfırdır.
Eylem ölçeği `T_olcek = 1,5 × W/4 = 11.036 N` olduğundan sıfır eylem, pod başına
`(0+1)/2 × 11.036 = 5.518 N` itki demektir. Dört pod toplam **22,1 kN** üretir, oysa hover
download dahil **30,5 kN** ister. Ajan ilk adımdan itibaren düşmektedir.

Buna ek olarak başlangıç `log_std = −0,5`, yani standart sapma 0,6'dır. Normalize eylem uzayı
$[-1, 1]$ olduğuna göre bu, tüm zarfın üçte birini kapsayan bir gürültüdür. Dört itki ve dört tilt
ekseninde bu ölçekte gürültü, aracı her adımda zarf dışına atmaktadır.

Üçüncü etken, gözlem normalizasyonunun bulunmamasıdır. Gözlem vektöründeki bileşenlerin ölçekleri
birbirinden çok farklıdır ve normalize edilmemiş girdi, değer ağının yakınsamasını
yavaşlatmaktadır.

**Bunların hiçbiri hipotezle ilgili değildir.** Üçü de uygulama ayrıntısıdır ve dört konfigürasyonu
aynı biçimde etkiler.

---

## 3. Düzeltilmiş koşuda DEĞİŞECEK olanlar

Aşağıdaki beş madde dışında hiçbir şey değiştirilmeyecektir.

| # | Değişiklik | Gerekçe | Hipotezle ilgisi |
|---|---|---|---|
| **D1** | Politika çıkış katmanının sapması, ilk eylemin **hover trim noktası** olacağı şekilde başlatılır | Ajan uçabilir bir noktadan başlar. Uçuş kontrolünde yerleşik bir uygulama. | yok, dördü de aynı |
| **D2** | Başlangıç `log_std` −0,5 yerine **−1,5** (standart sapma 0,22) | Keşif gürültüsü zarfın üçte birinden yirmide birine iner | yok, dördü de aynı |
| **D3** | **Gözlem normalizasyonu** eklenir (koşan ortalama ve standart sapma) | Standart PPO bileşeni, ilk sürümde eksikti | yok, dördü de aynı |
| **D4** | Bütçe 400.000 yerine **1.000.000** adım | Pilot, 400 binin birinci seviyeyi bile bitirmediğini gösterdi | yok, dördü de aynı |
| **D5** | Ödül terimlerinden **enerji cezası hover'da sabit bir vergi** olmaktan çıkarılır, görev fazına göre normalize edilir | Hover'da güç ~1 MW olduğundan enerji cezası sabit −0,2 katkı veriyordu ve takip ödülüyle yarışıyordu | yok, dördü de aynı |

### D4 üzerine bir düzeltme, sonuç görülmeden yapıldı

Bu belgenin ilk yazımında bütçe 1.500.000 adım olarak verilmişti. Hesaplama kaynağı ölçüldüğünde
bunun karşılığının iki çekirdekte yaklaşık sekiz saatlik bir koşu olduğu görüldü. Bütçe
**1.000.000 adıma** indirildi.

Gerekçe tamamen hesaplama kaynağıdır, hiçbir sonuca bakılmamıştır. Karşılığı şudur. Beş tohum
korunmuştur, çünkü karar kuralı 2 standart sapmaya dayanıyor ve üç tohumla standart sapma
kestirimi güvenilir olmaz. Tohum sayısını düşürüp adım sayısını korumak, karar kuralını
zayıflatırdı.

**Sonuç olarak.** Müfredatın ikinci seviyesine (geçiş) yine ulaşılamazsa, bunun nedeni bütçe
olabilir ve rapor bunu böyle yazacaktır. Bağlayıcı kısıtın hangisi olduğu, seviye ilerlemesinin
adım sayısına göre eğrisinden okunacaktır.

---

## 4. Düzeltilmiş koşuda DEĞİŞMEYECEK olanlar

Bunlar bilerek dondurulmuştur. Sonuç ne çıkarsa çıksın dokunulmayacaktır.

- **Müfredat eşiği 0,65.** Sonucu gördükten sonra eşiği düşürmek, hipotezi veriye uydurmak olur.
  Eşik yine aşılamazsa bu bir bulgudur ve öyle yazılır.
- **Müfredatın altı seviyesi ve sıralaması.**
- **Ödül ağırlıkları** (D5'teki enerji normalizasyonu dışında).
- **Konfigürasyon tanımları ve tilt eşlemesi.**
- **Tohum seti** (0, 1, 2, 3, 4).
- **PPO hiperparametreleri** — öğrenme oranı, kırpma, GAE lambda, gamma, yığın boyutu.
- **Fizik modelinin hiçbir parametresi.**

---

## 5. Karar kuralları, önceden sabitlenmiş

Sonuç yorumu bu kurallara göre yapılacaktır. Kurallar sonuç görülmeden yazılmıştır.

1. **İç içe geçmişlik kontrolü.** LIMULUS'un ortalama başarımı senkron tiltten anlamlı biçimde
   kötü çıkarsa, bu bir mimari bulgu değil bir eniyileme kusurudur ve koşu geçersiz sayılır.
   Senkron, LIMULUS'un özel hâlidir.
2. **Anlamlılık.** Konfigürasyonlar arası fark, beş tohumun standart sapmasının iki katından
   küçükse "fark yok" olarak raporlanır. Küçük farklar için üstünlük iddia edilmez.
3. **Seviye ilerlemesi.** Bir konfigürasyon müfredatın hangi seviyesine kadar geldiyse
   raporlanır. Seviye 2'ye (geçiş) ulaşılamazsa, bağımsız tiltin geçiş rejimindeki iddiası
   **öğrenme koşularıyla sınanamamış** sayılır ve politikadan bağımsız metrikler tek kanıt olarak
   kalır.
4. **Olumsuz sonuç.** Bağımsız tilt hiçbir eksende kazanım göstermezse bu gizlenmez. Bölüm 17
   zaten dört metrikten üçünde kazanım olmadığını yazmaktadır.

---

## 6. Pilot deneyin kendi değeri

Pilot koşu boşa gitmemiştir ve tezde şu üç şey için kullanılacaktır.

- **Bütçe kalibrasyonu.** 400 bin adımın yetmediği ölçülmüştür, tahmin edilmemiştir.
- **Başlangıç koşullarının belirleyiciliği.** Ortalama bölüm uzunluğunun 79 adım çıkması,
  başlangıç noktası seçiminin bu problemde hiperparametrelerden daha belirleyici olduğunu
  göstermektedir. Bu, yöntem bölümüne giren bir gözlemdir.
- **Tekrarlanabilirlik kaydı.** Beş tohumun tamamı diskte durmaktadır, silinmeyecektir.

---

## TADİLAT 1 — 03.08.2026, tam koşulardan önce

Bu belge "belgede yazılmayan hiçbir değişiklik yapılmayacaktır, yapılırsa buraya tarihiyle
eklenecektir" diyor. Değişiklik yapıldı ve buraya ekleniyor.

**Ne oldu.** Beş düzeltmeli (D1-D5) sonda koşusu da müfredat seviye 0'ı geçemedi. Bölüm
uzunluğu **kısalıyordu** (99 → 84), yani hiperparametre sorunu değildi. Üç yapısal kusur
bulundu, üçü de ortamın tanımındaydı, hiçbiri hiperparametre değildi.

| # | Kusur | Ölçülen bedeli | Düzeltme |
|---|---|---|---|
| **T1** | Eylem uzayı mutlaktı, hover trimi (+0,333 ×4, −1,000 ×n) koordinatındaydı. Tilt kanallarının trimi eylem uzayının **sınırındaydı** ve Gauss politikası sınıra kütle koyamaz. | sıfır eylemle 420 adımda çarpma | trime göre artımsal eşleme, `4-KARARLAR/15` |
| **T2** | Hücum açısı `V → 0` iken ±180° veriyor, hover'da stall cezası **sürekli** ateşleniyordu. | adım başına −2,23, takip ödülünün %89'u | ceza yalnız `V > 25 m/s` iken uygulanır |
| **T3** | Ölümcül sonlanmalardan yalnız yere çarpma cezalıydı. Tutumun 85°'yi aşması **cezasız çıkış kapısıydı**, yani en kısa yol takla atmaktı. | bölüm uzunluğunun eğitim boyunca kısalması | ceza her ölümcül sonlanmaya uygulanır |

**Meşruiyeti neye dayanıyor.** Üç değişiklik de **sonuçlara bakılarak değil, hiçbir koşu
seviye 0'ı geçemediği için** yapıldı. Konfigürasyonlar arası hiçbir karşılaştırma
yapılmamıştı ve dördünün de ortamı aynı biçimde değişti. D1 (trim sapmalı başlangıç) T1'den
sonra gereksizleştiği için sıfır vektöre çevrildi, silinmedi.

**Değişiklik sonrası ilk ölçüm.** Aynı sonda kurgusuyla, 150 bin adımda.

```
limulus  bolum_uz 430 -> 533 -> 591   (artiyor)
senkron  bolum_uz 391 -> 520          139k adimda SEVIYE 1'e gecti
```

Yirmi pilot koşuda bir kez bile görülmeyen şey — seviye ilerlemesi — ilk kez gerçekleşti.

**Sabit kalanlar.** Öğrenme oranı, rulo uzunluğu, devir sayısı, GAE-λ, klip oranı, müfredat
eşiği, tohum sayısı ve raporlama kuralları (§5) değişmedi. Bunlar hâlâ ön kayıtlıdır.

---

## PİLOT SONUÇ RAPORU — §5 kurallarına göre, 03.08.2026

Tam çıktı `9-DIJITAL-IKIZ/ogrenme/pilot_degerlendirme.txt`, üreten betik
`pilot_rapor.py`. Ödül ve bölüm uzunluğu değerleri **son %10'un ortalamasıdır**, tek noktanın
gürültüsünden kaçınmak için.

| Varyant | Koşu | Ödül ort. | std | Bölüm uz. | En yüksek seviye |
|---|---:|---:|---:|---:|---:|
| LIMULUS | 3 | +0,220 | 0,074 | 71 | **0** |
| İkili tilt | 3 | +0,225 | 0,229 | 67 | **0** |
| Senkron tilt | 2 | −0,075 | 0,167 | 48 | **0** |
| Lift + cruise | 2 | +0,264 | 0,023 | 50 | **0** |

**Kural 1 — iç içe geçmişlik.** İhlal yok. LIMULUS +0,220, senkron −0,075, fark +0,295 ve iki
standart sapma eşiği 0,334. Fark eşiğin altında kaldığı için "LIMULUS senkrondan kötü" durumu
oluşmadı, koşu bu kuralla geçersiz sayılmıyor.

**Kural 2 — anlamlılık.** LIMULUS ile ikili tilt arasındaki fark 0,005, eşik 0,457.
**Fark yok.** Politikadan bağımsız metriklerin verdiği sonuçla aynı yönde, ama bu bir doğrulama
değildir — aşağıdaki nedenle.

**Kural 3 — seviye ilerlemesi.** Ulaşılan en yüksek seviye **0**. Seviye 2 (geçiş) ulaşılmadı.
Kural gereği **bağımsız tiltin geçiş rejimindeki iddiası öğrenme koşularıyla sınanamamış
sayılır** ve politikadan bağımsız dört metrik tek kanıt olarak kalır.

**Kural 4 — olumsuz sonuç gizlenmez.** Pilot hiçbir eksende karşılaştırılabilir sonuç üretmedi.
**Üretememesinin nedeni varyant farkı değil, ortamın kusurlarıydı** (T1-T3, yukarıdaki Tadilat 1).
Bu ayrım korunmalıdır. Pilotun ödül sayıları varyantlar arası bir karşılaştırma olarak
**okunamaz**, çünkü dördü de aynı bozuk ödül manzarasında ve aynı ulaşılamaz eylem uzayında
koştu. Tek geçerli okuma şudur: kurgu bu hâliyle çalışmıyordu.

**Tamlık.** 20 koşunun **10'u** tamamlandı. Kalan 10 başlatılmadı. Gerekçe: ilk 10'un tamamı
seviye 0'da takıldı ve kök neden bulundu. Aynı kusurla 10 koşu daha üretmek bilgi katmaz,
yalnız iki saat CPU harcar. Tamamlanan 10 koşunun günlükleri **silinmedi**, `kosular/` altında
duruyor.

---

*Tarih 03.08.2026 · Tadilat 1 aynı gün · İlgili `9-DIJITAL-IKIZ/ogrenme/deney.py`, `egitim.py`,
`11-yapilacaklar-v2.md`, `15-eylem-uzayi-duzeltmesi.md` ·
Protokol `LIMULUS_ELESTIRI_PROTOKOLU.md` §5*
