# 38 — Uzun bütçeli koşu sonuçları: 20/20 tamamlandı, seviye 4 yine 1/20

**Tarih:** 07.08.2026 · **Sınıf:** sonuç kaydı (karar 36 ön kaydının kapanışı)
**Veri:** `9-DIJITAL-IKIZ/ogrenme/kosular_uzun/` · 20 günlük dosyası · toplam 60.000.000 adım
**Teze işlendi:** `J_sonuclar` yeni bölüm "Uzun Bütçeli Koşular" (`sec:sonuc-uzun-butce`) + Bekleyen Koşular tablosu + `Z_sentez` hesaplamalı kalemler listesi

---

## Koşu kimliği

4 varyant × 5 tohum × 3.000.000 adım, `LIMULUS_CRUISE_ITKI=1` (180 kW birim, karar 32 fiziği).
05.08.2026 23:48 UTC başladı, 07.08.2026 18:17 UTC bitti (~42,5 saat duvar, ~2 kesinti dahil).
Bekçi zinciri oturuma bağlı `send_later` protokolüyle taşındı (karar 36 olay kaydının devamı).

**Veri denetimi (karar 30 protokolü): 20/20 GEÇTİ.** Her koşu 1465 kayıt, son adım 3.000.320,
adım sayacı tek yönlü artıyor.

## Sonuçlar — karar 36'nın ön kayıtlı kurallarına göre

### Kural 1 (birincil soru): her varyanttan ≥1 tohum seviye 4'e ulaştı mı? **HAYIR**

| Varyant | Ulaşılan seviyeler (5 tohum) | Seviye 4 |
|---|---|---|
| limulus | 2,2,2,2,2 | ✗ |
| ikili | 2,2,2,2,2 | ✗ |
| senkron | 2,2,**4**,2,2 | ✓ yalnız t2 (870k → sev.3, 899k → sev.4) |
| liftcruise | 2,2,2,2,2 | ✗ |

Üç varyant için bozucu reddi ekseni yine **ölçülemedi**, artık "3M bütçe de yetmedi" nitelemesiyle.
1M kampanyasıyla örüntü birebir aynı (orada da yalnız senkron t2). **Teşhis bütçeden eşiğe kaydı:**
19/20 koşu seviye 2'ye 149k–354k adımda çıkıp kalan bütçenin tamamını platoda geçiriyor. Darboğaz
0,65'lik seviye 3 eşiği (keşifsel, ön kayıtta kurala bağlanmamıştı).

### Kural 2: öğrenme verimi (0,5 eşiği, aynı metodoloji) — fark yok

| Varyant | Son ödül (son 100k, günlük) | σ | Verim (ort adım) | σ |
|---|---|---|---|---|
| liftcruise | **+0,071** | 0,002 | 89.702 | 35.425 |
| limulus | +0,020 | 0,002 | 118.784 | 54.877 |
| ikili | +0,020 | 0,009 | 113.050 | 37.017 |
| senkron | +0,002 | **0,058** | 116.736 | 39.686 |

Verim farkları 2σ'nın çok altında → kural 2 gereği üstünlük iddia edilemez, 1M bulgusu korunuyor.
Son ödül günlük tabanlıdır, 1M tablosundaki değerlendirme ödülüyle **karşılaştırılamaz**.

### Kural 3: F2 ablasyonunun 3M politikalarıyla tekrarı — **HENÜZ KOŞULMADI**

Tilt kanalı bulgusunun ("oynaklığı üreten kanalın kendisi") uzun bütçe sınaması bekliyor.
Tezdeki ihtimal açık bırakıldı. Bekleyen Koşular tablosuna girdi.

### Keşifsel notlar (kurala bağlı değil)

- 1M'de LIMULUS'a atfedilen yüksek tohumlar arası oynaklık (σ 0,225) bu kampanyada **görülmedi**
  (günlük son ödülde σ 0,002). Fizik ve metrik farklı → karşılaştırmalı bulgu değil, kararlılık
  hipotezi koşusuna not.
- Senkronun iki-rejim davranışı (bir tohum −0,098 çöküş, bir tohum seviye 4) varyansın kaynağına
  dair incelemeye değer.
- Seviye 4'e ulaşan tek koşunun iki kampanyada da senkron t2 olması dikkat çekici, tohum-mimari
  etkileşimi olabilir.

## Bu kayıtla kapanan/açılan kalemler

**Kapandı:** karar 36 ön kaydı (uygulama tamam) · tez Bekleyen tablosunun "lift+cruise yeniden
eğitimi" ve "uzun bütçeli koşu" kalemleri · M1 ve M5 makalelerinin "tam ölçekli koşular" blokajı.

**Açıldı / bekliyor:** F2-3M ablasyonu (kural 3) · senkron t2 bozucu ölçümü (karar 28 düzeltilmiş
metrik, 8 bozucu tohumu) · kararlılık hipotezi bağımsız koşusu · müfredat eşiği incelemesi
(gevşetilmiş eşikle, kendi ön kaydıyla).

**Analiz raporu:** `9-DIJITAL-IKIZ/ogrenme/uzun_kosu_analiz.html` (etkileşimli eğriler, tohum
dağılımları, seviye zaman çizelgesi).

---

*Kayıt 07.08.2026 · İlgili `26`, `28`, `30`, `32`, `34`, `36`*


## ➕ F2-UZUN TEKRARI KOŞULDU — 07.08.2026 (kural 3 kapandı)

Betik `9-DIJITAL-IKIZ/testler/dogrulama_f2_uzun.py` (orijinalin kosular_uzun + LIMULUS_CRUISE_ITKI=1
sürümü, metodoloji birebir). Sonuç:

| | tilt/itki | tilt std | ablasyon etkisi |
|---|---|---|---|
| limulus | 0,31 | 0,127 | **%0,1** |
| ikili | 0,29 | 0,063 | **%0,2** |
| senkron t1/t3/t4 | 0,23 | 0,048 | küçük |
| senkron t0 (çöken) | 1,00 | 0,061 | −728 → −2140, çöküş derinleşiyor |
| senkron t2 (seviye 4) | 0,91 | **0,678** | **+74 → −353, kanala bağımlı** |

**Yorum.** Uzun bütçe LIMULUS'a tilt kanalını ÖĞRETMEDİ — 1M'de "kullanıyor ama kararsız" olan
kanal, 3M'de fiilen etkisizleşmiş (ablasyon ‰1). Karar 34'ün açık ihtimali bu kampanya için
OLUMSUZ kapandı. Buna karşılık seviye 4'e ulaşan tek politika (senkron t2) tek tilt kanalını
gerçekten kullanıyor ve ona bağımlı. Tek serbestlik derecesi öğreniliyor, dört bağımsız kanal
3M'de bile öğrenilemiyor — keşif yükü kanal sayısıyla ölçekleniyor (keşifsel, uçlar birer tohum).

Teze işlendi: `sec:sonuc-f2` yeni "Uzun bütçe tekrarı" paragrafı + `tab:sonuc-f2-uzun`,
Bekleyen Koşular 4 → 3 kalem.


## ➕ A2-UZUN BOZUCU ÖLÇÜMÜ KOŞULDU — 07.08.2026 (bekleyen kalem kapandı)

Betik `9-DIJITAL-IKIZ/testler/dogrulama_a2_uzun.py` (kosular_uzun + LIMULUS_CRUISE_ITKI=1,
düzeltilmiş metrik, 8 bozucu tohumu, log `/tmp/a2_uzun.log` → tez tablosu `tab:sonuc-bozucu-uzun`).

**Geçiş+gust (birincil, dağıtım içi): 0/160 — DÖRT varyant da %0.** Bölümler ~11. saniyede
(508-545 adım) ölüyor. **Senkron t2 (seviye 4) dahi 0/8** — 1M'de 3/8 tamamlıyordu.
Tohum dökümü: t2 ort 508 adım, diğer senkron tohumları 534-545.

**Cruise+gust (ikincil, dağıtım dışı): ilk kez ölçüm üretti.**
| | tamamlama | RMS(tam) | 1M karşılığı |
|---|---|---|---|
| limulus | 0/40 | — | 0/40 |
| ikili | 6/40 (%15) | 145,1 | 16/40 (%40), 131,1 |
| senkron | 29/40 (%72) | 134,0 | 8/40 (%20), 88,7 |
| liftcruise | 13/40 (%32) | 153,9 | 0/40 (120 kW'la) |
Kural 2: üç ikili karşılaştırma da FARK YOK. Senkron tohum dökümü (cruise): t0 8/8 · t1 8/8 ·
t2 8/8 (RMS 138) · t3 5/8 · t4 0/8.

**Yorumlar.** (1) Karar 28'in "gust görmek → tamamlama" mekanizması zayıfladı: t2 seviye 4'te
~2,1M adım eğitildi ama gust'lu geçişi tamamlamıyor — müfredat eşiği ödül tabanlı, eğitim
bölümleri de görev süresinin altında. Keşifsel not olarak teze işlendi. (2) lc'nin cruise'da
ilk kez tamamlama üretmesi 180 kW birimle tutarlı. (3) LIMULUS iki görevde de 0/80 — eksen bu
konfigürasyon için hiçbir koşulda ölçüm üretmiyor.

Bekleyen Koşular 3 → 2 kalem (kararlılık hipotezi, müfredat eşiği incelemesi).

---

## Tadilat 1 — senkron σ yuvarlaması (09.08.2026)

Yukarıdaki sonuç tablosunda senkron tiltin son ödül standart sapması **0,058** yazılmıştır.
Ölçülen değer `kosular_uzun/` günlüklerinden yeniden hesaplandığında **0,0586** çıkmakta,
dolayısıyla üç ondalığa doğru yuvarlanmış hâli **0,059** olmaktadır. Yazılan değer yuvarlama
değil kırpmadır.

Karar dosyaları yerinde düzeltilmediği için yukarıdaki tablo olduğu gibi bırakılmış, düzeltme
bu tadilata kaydedilmiştir. Türetilmiş ürünlerde değer 0,059 olarak eşitlenmiştir: tez
`tab:sonuc-uzun-butce`, M1 v5 (TR ve EN) Tablo 2, `CLAUDE.md` durum tablosu.

Diğer üç varyantın hem ortalaması hem sapması yeniden ölçümde birebir doğrulanmıştır:
liftcruise +0,0708 ± 0,0022 · limulus +0,0203 ± 0,0020 · ikili +0,0204 ± 0,0090 ·
senkron +0,0016 ± 0,0586. Sapma beş tohumun örneklem sapmasıdır (n−1), bu tanım M1 Tablo 2
altyazısına da yazılmıştır. Senkronun sapmasının büyük olması bir hata değil bulgudur, t0
tohumu −0,0996 ile çökmüş, t2 tohumu +0,0528 ile en yükseği vermiştir.

**Kararlara etkisi yok.** Kural 2'nin anlamlılık kıyaslaması sapmaların büyüklük mertebesiyle
çalışmakta, 0,058 ile 0,059 arasındaki fark hiçbir kuralın sonucunu değiştirmemektedir.
