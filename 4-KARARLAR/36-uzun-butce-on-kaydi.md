# 36 — Uzun bütçeli koşu ön kaydı: 3M adım, seviye 4 hedefi

**Tarih:** 05.08.2026 · **Sınıf:** **ön kayıt** — sonuç görülmeden yazıldı
**Statü:** ⏸️ **hazır, başlatılmadı** (Mete kararı 05.08.2026) — betik ve kurallar bekliyor, "uzun koşuyu başlat" denince yürür
**Betik:** `9-DIJITAL-IKIZ/ogrenme/uzun_kosu.sh` · **Dizin:** `kosular_uzun/` (ayrı)

---

## Neden

Karar 28: bozucu reddi ölçülemedi, çünkü 20 politikadan yalnız biri müfredat seviye 4'e
(gust) ulaştı. Reçete "daha uzun bütçe" idi ve müfredat sırası dondurulmuştu.

Bu koşu o reçetenin uygulanmasıdır: **4 varyant × 5 tohum × 3.000.000 adım** (1M'in üç katı).

## Fizik — kosular_v2'den BİR fark var, kayıtlı

`LIMULUS_CRUISE_ITKI=1`: lift+cruise **180 kW itici birimle** eğitilir (karar 32'nin fiziği).
`kosular_v2` bu birim kapalıyken üretilmişti. İki set **hiçbir tabloda karıştırılmaz** —
bu, karar 22'de konan ayrı dizin kuralının uygulamasıdır. Diğer her şey (ödül, müfredat,
hiperparametreler, eklem cezası 28 kN) `kosular_v2` ile birebir aynıdır.

## Sonuç görülmeden konan karar kuralları

1. **Birincil soru:** her varyanttan en az bir tohum seviye 4'e ulaşıyor mu?
   - Ulaşırsa → bozucu reddi, karar 28'in düzeltilmiş metriğiyle (yalnız tamamlanan
     bölümler + hayatta kalma ayrı) ölçülür ve karar kuralı 2 (fark < 2σ → "fark yok") uygulanır
   - Bir varyant ulaşamazsa → o varyant için eksen yine **"ölçülemedi"** yazılır, sonuç
     3M bütçenin de yetmediği bilgisiyle raporlanır
2. Öğrenme verimi ekseni 3M bütçeyle **yeniden** değerlendirilir, 1M sonuçları kayıt olarak kalır
3. Karar 34'ün açık ihtimali sınanır: LIMULUS'un tilt kanalı **daha uzun bütçede** kazanç
   üretmeye başlıyor mu (F2 ablasyonu 3M politikalarıyla tekrarlanır)
4. Veri denetimi karar 30 protokolüyle yapılır: adım sayısı, kayıt sayısı, tek yönlü artış
5. Koşu bitmeden hiçbir ara sonuç tez metnine girmez

## Yürütme

~60M çevre adımı ≈ 30 saat saf hesap. Saatlik zamanlanmış görev dilim koşar
(`uzun_kosu.sh`, kilitli), 20/20 olunca kendini sonlandırır ve özet geçer. Tahmini duvar
saati 1,5-2 gün.

---

*Kayıt 05.08.2026 · İlgili `12-egitim-butcesi-on-kaydi.md`, `28`, `30`, `32`, `34`*

---

## ✅ BAŞLATILDI — 05.08.2026 23:48 UTC (Mete emri), EMNİYETLİ SÜRÜM

Başlatmadan önce iki gerçek açık kapatıldı ve test edildi:

1. **Ara kayıt atomik değildi** — timeout tam `torch.save` sırasında keserse `_ara.pt` bozulur,
   koşu "bastan" derdi. Yama: `.tmp` + `os.replace` (egitim_v2.py). Ayrıca her kayıtta ucuz
   `_ara_durum.json` (adım sayacı) yazılır.
2. **Bitiş sırası terstiydi** — ara kayıt, nihai `.pt` ve günlük yazılmadan ÖNCE siliniyordu;
   tam o pencerede kesinti 3M adımı sıfırlardı. Yama: önce nihai dosyalar atomik, ara en son.

**Test (kosular_emniyet_testi):** 60k adımlık koşu 22.528 adımda SIGKILL ile kesildi →
yeniden başlatmada `[devam] 22,528 adimdan suruyor` → 61.440'ta temiz bitiş. ✅

**Dilim düzeni:** saatlik görev `trig_01MrZBAf4YybNEMAMPXjdZrG`, `uzun_kosu.sh 3000`
(50 dk dilim, flock kilidi, dilim başı/sonu öksüz süreç temizliği, iki dilim üst üste
ilerleme yoksa ALARM). 20/20 → `BITTI` işareti → görev kendini siler, push bildirimi düşer.
İlk dilim bu oturumdan elle başlatıldı; 2. dakikada 2 işçi ~370k adım toplamıştı.

## ⚠️ OLAY ve DÜZELTME — 06.08.2026

Saatlik görevin taze oturumlarında Bash izni yokmuş: 9 ateşleme hiçbir şey çalıştıramadı, konteyner de
oturumlar arası uyuduğu için ilk dilim 00:24'te dondu (~9 saat duvar kaybı, **veri kaybı sıfır** —
atomik checkpoint 903k adımı korudu, koşu kaldığı yerden sürdü). Düzeltme: bekçi görevi **bu oturuma
bağlandı** (persist_session, Bash tam yetkili), her uyanışta dilimi garantiler, `sleep` zinciriyle
konteyneri ~50 dk uyanık tutar ve kendini 2 dk arayla yeniden kurar. Boş ateşlenen görev silindi.


## ✅ KAPANDI — 07.08.2026

Koşu 07.08.2026 18:17 UTC'de 20/20 tamamlandı. Veri denetimi (karar 30) 20/20 geçti.
Karar kurallarının uygulanması ve sonuçlar **karar 38**'de, tez karşılığı `J_sonuclar`
"Uzun Bütçeli Koşular" bölümünde. Özet: seviye 4'e yine yalnız senkron t2 ulaştı, bozucu
reddi üç varyant için "3M de yetmedi" nitelemesiyle ölçülemedi, teşhis müfredat eşiğine
kaydı. Kural 3 (F2-3M ablasyonu) henüz koşulmadı, Bekleyen Koşular tablosunda.
