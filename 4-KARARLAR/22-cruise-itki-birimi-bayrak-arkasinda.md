# 22 — B4: lift+cruise'a ayrı itici birim eklendi, bayrak arkasında kapalı

**Tarih:** 04.08.2026 · **Sınıf:** deney hijyeni kararı · **Statü:** kod hazır, **kapalı**

---

## Sorun

`liftcruise` varyantı `ayri_cruise_itki=True` olarak tanımlanmıştı fakat **bu alan kodun hiçbir
yerinde okunmuyordu**. Yani varyant dört rotoru dikey kilitli, ileri itki üreten hiçbir organı
olmadan koşuyordu.

Sonuçları ölçüldü ve tezde raporlandı.

| Metrik | Lift+cruise sonucu |
|---|---|
| Trim zarfı | 304 (diğerleri 1485) |
| Geçiş koridoru | 1,07° (diğerleri 31-37°) |
| Enerji | görevi tamamlayamıyor |
| Asimetrik arıza trimi | 0/6 |
| Kapalı çevrim cruise hızı | 25,6 m/s (hedef 68,9) |

**Bu sonuçlar mimarinin değil, eksik modelin sonucudur.** Gerçek lift+cruise araçlarında (Beta
Alia, Archer Midnight) ayrı bir itici pervane vardır. Karşılaştırmanın adilliği zedelenmiş
durumda ve `LIMULUS_ELESTIRI_PROTOKOLU` bunu B-tipi bulgu sayar.

---

## Yapılan

Ayrı itici birim modele eklendi.

| Parametre | Değer | Statü |
|---|---|---|
| Sürekli güç | 120 kW | ⚠️ **VARSAYIM** — cruise sürükleme gücünden (68,9 m/s'de ~110 kW) türetildi, %10 marj |
| Pervane verimi | 0,80 | ⚠️ **VARSAYIM** — tipik sabit hatveli itici, kaynak yok |
| Kuru kütle | 45 kg | ⚠️ **VARSAYIM** — bileşen bazında kaba tahmin |

Üçü de `VARSAYIMLAR` sözlüğüne gerekçesiyle yazıldı. Kuvvet gövde ekseninde, CG hizasında, moment
kolu yok. Güç batarya bütçesine giriyor.

---

## 🔴 Neden KAPALI

**Tam ölçekli eğitim koşuları şu anda devam ediyor.** Tohum 0'ın dört varyantı bitmiş durumda,
tohum 1-4 koşuyor.

Lift+cruise fiziğini şimdi değiştirmek şu anlama gelirdi.

> Tohum 0 eski modelle, tohum 1-4 yeni modelle eğitilmiş olur. Beş tohumun ortalaması iki farklı
> hava aracının karışımı olur ve standart sapma fiziksel bir şey ölçmez.

Bu, sonucu sessizce bozan türden bir hatadır ve tam olarak bu programın yakalamaya çalıştığı
sınıfa girer.

**Bayrak:** `Limulus(cruise_itki_etkin=False)` — varsayılan. Açıldığında yalnız
`ayri_cruise_itki=True` olan varyantı etkiler, diğer üçü bit düzeyinde aynı kalır. Regresyon
doğrulandı: limulus, ikili ve senkron V=68,9'da aynı trimi ve aynı gücü (199,3 kW) veriyor,
43 test geçiyor.

---

## Bayrak ne zaman açılacak — sıra

1. ✅ Tam ölçekli koşular bitti (20/20, `kosular_v2`, karar 26)
2. ✅ Bayrak bağlandı — `LIMULUS_CRUISE_ITKI=1` ortam değişkeni `ortam.py` içinden
   `Limulus(cruise_itki_etkin=...)` çağrısına geçiyor
3. ⬜ **Politikadan bağımsız dört metrik yeniden hesaplansın** — trim zarfı, geçiş koridoru,
   arıza toleransı, enerji. Dördü de lift+cruise için değişecek.
4. ⬜ Asimetrik arıza trimi yeniden koşulsun
5. 🔄 Lift+cruise için eğitim koşuları **yeniden yapılıyor** (5 tohum, ~3 saat) —
   `ogrenme/lc_yeniden.sh`, çıktı **ayrı dizine** (`kosular_lc/`) yazılıyor
6. ⬜ Tezdeki bütün lift+cruise sayıları güncellensin, eski değerler kayıt olarak kalsın

### ⚠️ Ayrı dizin kuralı

`kosular_v2` **kapalı bayrakla** üretilmiştir. Yeni koşular `kosular_lc` dizinine yazılır ve
ikisi hiçbir tabloda karıştırılmaz. Karşılaştırma yapılacaksa hangi dizinden geldiği yazılır.
Bu, karar 25'teki kesintili/kesintisiz koşu ayrımıyla aynı disiplindir.

**Adım 5 pahalıdır ve atlanamaz.** Yeni fizikle eğitilmemiş bir politikanın sonucu, yeni fizikle
ölçülen metriklerle aynı tabloda gösterilemez.

---

## Beklenen etki

Lift+cruise varyantının bütün metriklerinde iyileşme bekleniyor. Bu, karşılaştırmayı LIMULUS
aleyhine değiştirebilir ve **değiştirmelidir** — mevcut tablo o varyanta haksızlık ediyor.

Tezin geçiş koridoru bulgusu (LIMULUS %21 üstün) senkron tilte karşı ölçülmüştür, lift+cruise'a
karşı değil. Dolayısıyla bu düzeltme merkez iddiayı doğrudan etkilemiyor. Etkilediği yer enerji
metriği ve "lift+cruise görevi tamamlayamıyor" ifadesidir — o ifade düzeltmeden sonra büyük
olasılıkla **geri çekilecektir**.

---

*Kayıt 04.08.2026 · Kod `9-DIJITAL-IKIZ/dinamik/arac.py` (`cruise_itki_etkin`),
`konfigurasyon.py` (CRUISE_ITKI_*) · İlgili `11-yapilacaklar-v2.md` B4,
`../LIMULUS_ELESTIRI_PROTOKOLU.md`*
