# 15 — Öğrenme ortamının eylem uzayı düzeltmesi

**Tarih:** 03.08.2026 · **Tetikleyen:** düzeltilmiş eğitim betiğinin (v2) sonda koşusu da
müfredat seviye 0'ı geçemedi · **Sınıf:** D — deney kurgusunu değiştirir
**Etkilenen:** `9-DIJITAL-IKIZ/ogrenme/ortam.py`, tüm PPO koşuları, ön kayıt belgesi (12)

---

## Belirti

Yirmi pilot koşunun **hiçbiri** müfredat seviye 0'ı (20 saniye hover tutma) geçemedi. Ortalama
bölüm uzunluğu 1000 adımlık üst sınıra karşılık 60-90 adım. Beş düzeltme uygulanmış eğitim
betiği (v2 — trim sapmalı başlangıç, log_std −1,5, gözlem normalizasyonu, 1M adım, faz-bağıl
enerji cezası) ile yapılan sonda koşusunda tablo değişmedi.

```
limulus  [ 51200] sev 0 odul -0,055 bolum_uz 90
limulus  [102400] sev 0 odul -0,015 bolum_uz 71     <- kisaliyor
senkron  [ 51200] sev 0 odul -0,025 bolum_uz 64
senkron  [102400] sev 0 odul +0,003 bolum_uz 60
```

Bölüm uzunluğunun **kısalması**, hiperparametre sorunu olmadığının işaretiydi.

---

## Kök neden — eylem uzayının trim noktası köşedeydi

Eski eşleme mutlaktı.

```python
T_komut    = (e[:4] + 1) * 0.5 * T_olcek           # T_olcek = 11036 N/pod
tilt_komut = (e[4:] + 1) * 0.5 * THETA_MAX         # THETA_MAX = 90 derece
```

Buradan çıkan sayılar şunlar.

| Eylem | İtki | Tilt |
|---:|---:|---:|
| −1,000 | 0 N | 0° |
| **0,000** | **5518 N** | **45°** |
| +0,333 | 7358 N | 60° |
| +1,000 | 11036 N | 90° |

Hover için gereken nokta **(+0,333, +0,333, +0,333, +0,333, −1, −1, −1, −1)**.

İki ayrı sorun var ve ikincisi öldürücü.

1. **İtki kanallarının trimi merkezde değil.** Politika, herhangi bir şey öğrenmeden önce dört
   kanalda sabit bir +0,333 kayması bulmak zorunda. Bu, keşfin ilk aşamasının tamamını
   düşmekle geçirmesi demek.

2. **Tilt kanallarının trimi eylem uzayının SINIRINDA.** Hover'da doğru tilt 0 derece, yani
   eylem tam olarak −1,000. **Gauss politikası bir sınıra kütle yerleştiremez.** Ortalamayı
   büyük negatife itip σ'yı küçültmesi gerekir, ama σ'yı küçültmek diğer kanallardaki keşfi de
   öldürür. Ayrıca sıfır eylem 45 derece tilt komutu demek — hover görevinde araç ilk adımda
   itkisinin yarısını ileri çeviriyor ve düşüyor.

Sıfır eylemle bölüm uzunluğu 420 adım, iniş hızı 37 m/s, çarpma. Rastgele politikayla 54 adım.
Yani **ortam, eylem uzayının merkezinde uçamıyordu.**

---

## Düzeltme — trime göre artımsal eşleme

```python
T_komut    = clip(T_trim * (1 + 0.35 * e[:4]), 0, T_olcek)
tilt_komut = clip(th_trim + radians(30) * e[4:], 0, THETA_MAX)
```

`T_trim` ve `th_trim` görevin **başlangıç koşulunda** trim çözücüden gelir ve
`(varyant, V, h)` anahtarıyla önbelleklenir. Çözücü 0,1-3 s sürüyor, müfredat sonlu sayıda
görev tanımladığı için toplam maliyet ihmal edilebilir. Çözüm bulunamazsa hover itkisine ve
varyantın sabit tiltine düşer — lift+cruise varyantı ileri hızda trim bulamıyor, bu bilinen
eksiklik (yapılacaklar B4) ve gizlenmiyor.

**Sıfır eylem artık trimi korur.** Doğrulama `ortam.py` içine kalıcı bir öz-test olarak kondu.

```
limulus     1000 adim  irtifa hatasi -0,06 m  odul +59,5  1033 kW  sure doldu
ikili       1000 adim  irtifa hatasi -0,06 m  odul +59,5  1033 kW  sure doldu
senkron     1000 adim  irtifa hatasi -0,06 m  odul +59,5  1033 kW  sure doldu
liftcruise  1000 adim  irtifa hatasi -0,06 m  odul +59,5  1033 kW  sure doldu
```

Eski eşlemede aynı test **−75,7 ödül ve 54 adımda çarpma** veriyordu.

Rastgele politika hâlâ çarpıyor (54 adım) ve bu **doğru davranıştır**. ±%35 itki ve ±30 derece
tilt gürültüsü gerçekten kararsızlaştırıcıdır. Değişen şey, öğrenilebilir noktanın artık eylem
uzayının merkezinde olmasıdır.

### Yan etki — kontrol eforu cezası da düzeldi

Ödül fonksiyonundaki `kontrol_eforu` terimi `mean(e²)` ile ceza veriyor. Eski eşlemede bu,
hover'da gereken itkinin kendisini cezalandırıyordu. Yeni eşlemede **trimden sapmayı**
cezalandırıyor, yani terimin amacı ile davranışı ilk kez örtüşüyor.

### Yetki katsayılarının seçimi

| Katsayı | Değer | Gerekçe |
|---|---|---|
| `KT_YETKI` | 0,35 | Hover trimi 7626 N, tavan 11036 N. +%35 → 10295 N, tavanın altında kalıyor. −%35 → 4957 N, serbest düşüşe yetecek kadar aşağı. |
| `KTH_YETKI` | 30° | Geçiş koridoru ölçümlerinde gözlenen genişlik 31-38°. Politikanın koridoru tek adımda taramasına gerek yok, ankraj zaten görev boyunca kayıyor. |

İkisi de **varsayımdır**, ölçülmüş değildir. Duyarlılık taraması yapılmadı.

---

## Ön kayıt belgesine etkisi

`12-egitim-butcesi-on-kaydi.md` tam ölçekli koşulardan **önce** yazıldı ve hangi
hiperparametrelerin sabitlendiğini kaydediyor. Eylem uzayı eşlemesi o belgede bir
hiperparametre olarak değil, ortamın tanımı olarak duruyordu.

**Bu bir değişiklik ve gizlenmemeli.** Ön kayda bir tadilat notu eklendi. Değişikliğin
meşruiyeti şuna dayanır: pilot koşular ön kayıtta açıkça pilot olarak tanımlanmıştı ve amaçları
tam da bu sınıf sorunları bulmaktı. Değişiklik **sonuçlara bakılarak değil, hiçbir koşu seviye
0'ı geçemediği için** yapıldı, yani konfigürasyonlar arası karşılaştırmadan bağımsızdır.
Dördünün de eşlemesi aynı biçimde değişti.

---

## Ne öğrenildi

Bu, aynı gün içinde bulunan **ikinci** yorum hatasıdır (birincisi kontrol otoritesi,
`4-KARARLAR/14`). İkisinin ortak yanı şu: kod çalışıyordu, testler geçiyordu, sayılar
tutarlıydı. Yanlış olan, kodun ne yaptığına dair **zihinsel modeldi**.

Uygulanan kural: bir öğrenme ortamı kurulduğunda, **sıfır eylemin ne yaptığı** açıkça test
edilir. Bu test artık `ortam.py` içinde kalıcıdır ve dört varyantı da kapsar.

---

*Kayıt 03.08.2026 · Öz-test `9-DIJITAL-IKIZ/ogrenme/ortam.py` `__main__` bloğu ·
İlgili `12-egitim-butcesi-on-kaydi.md`, `14-kontrol-otoritesi-duzeltmesi.md`*
