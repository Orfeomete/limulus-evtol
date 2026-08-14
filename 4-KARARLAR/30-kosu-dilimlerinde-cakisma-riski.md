# 30 — Koşu dilimleri kilitsizdi, iki süreç aynı ara kayda yazabiliyordu

**Tarih:** 04.08.2026 · **Sınıf:** **altyapı kusuru** + tamamlanan verinin denetimi
**Dosyalar:** `9-DIJITAL-IKIZ/ogrenme/lc_yeniden.sh`, `devam.sh`, `gece_kosusu.sh`

---

## Kusur

Üç sürdürücü betiğin hiçbirinde **karşılıklı dışlama** yoktu. Bir dilim bitmeden ikinci dilim
başlatıldığında iki `deney.py` süreci aynı anda çalışıyor ve **aynı** `*_ara.pt` dosyasına
yazıyordu.

Sonucu şudur. İkinci süreç, birincinin ilerlemiş durumunu değil, **başlarken okuduğu eski
durumu** kaydeder. Birinci sürecin arada kaydettiği ilerleme silinir.

```
18:47  dilim A basladi, ara kayit 376.832 adimdan okundu
18:49  dilim B basladi, ara kayit 376.832 adimdan okundu     ← cakisma
18:50  dilim A kaydetti  → 400.000
18:51  dilim B kaydetti  → 385.000                            ← geri gitti
```

**Hata vermez. Uyarı vermez. Yalnız yavaşlar.** Kayıp, geçen sürenin bir kısmının yeniden
koşulmasıdır.

### Nasıl yakalandı

Bir dilim daha başlatmadan önce `ps` çıktısına bakıldığında **dört** `deney.py` süreci
görüldü, oysa iki olmalıydı. İki dilim üst üste binmişti. Fazla dilim on üç saniyelikken
öldürüldü.

Sebebi benim hatamdır — bir önceki dilimin bitmesini beklemeden yenisini başlattım. Fakat asıl
kusur, betiğin buna izin vermesidir. **İnsan hatasını bir betik tasarımı yakalayabilecekken
yakalamamıştır.**

---

## Düzeltme

Üç betiğe de `flock` tabanlı bir kilit eklendi.

```bash
exec 9>/tmp/limulus_v2.kilit
if ! flock -n 9; then
    echo "[$(date -u +%H:%M)] ATLANDI · dilim zaten kosuyor" >> devam.log
    exit 0
fi
```

- `devam.sh` ve `gece_kosusu.sh` **aynı** kilidi paylaşır — ikisi de `kosular_v2` dizinine yazar
- `lc_yeniden.sh` **ayrı** kilit kullanır — `kosular_lc` dizinine yazar, çakışmaz

Kilit iki kez sınandı.

**Yalıtılmış sınama.** İki süreç aynı kilit dosyasına aynı anda gitti, ikincisi `ATLANDI`
yazıp çıktı, birincisi kesintisiz tamamladı.

**Gerçek koşuda.** Bir dilim çalışırken ikinci dilim başlatıldı ve `lc.log` şunu yazdı.

```
[19:05] lc · 0/5
[19:13] ATLANDI · dilim zaten kosuyor
```

Yani kusur gerçek koşulda tekrar denendiğinde artık **kendiliğinden engelleniyor.** Aynı
dizide iki `deney.py` süreci bir daha görülmedi.

---

## ⚠️ Tamamlanmış 20/20 koşusu etkilendi mi — denetlendi

Kusur, `kosular_v2` üretilirken de yürürlükteydi. `devam.log` incelendiğinde en az bir şüpheli
nokta bulundu: `09:58` başlayan `devam.sh` süreci `exec` kullandığı için bitiş kaydı bırakmıyor
ve `10:35` başlayan `gece_kosusu.sh` dilimiyle örtüşmüş olabilir.

Bu yüzden **verinin kendisi denetlendi**, günlüğe güvenilmedi.

| Denetim | Beklenen | Bulunan |
|---|---|---|
| Yirmi koşunun tamamı 1M adıma ulaştı mı | 20/20 | **20/20**, hepsi 1.001.472 adım |
| Kayıt sayısı tutarlı mı | eşit | **489**, yirmisinde de |
| Adım dizisi tek yönlü artıyor mu | evet | **yirmisinde de evet** |
| Geri sıçrama var mı | yok | **yok** |

Bir çakışma yaşandıysa bile **ara kayıttan geri dönüş, o kısmın yeniden koşulmasıyla
kapanmıştır.** Nihai modeller hedef adım sayısına ulaşmıştır ve günlükler kendi içinde
tutarlıdır. Çakışmanın bedeli **yalnız duvar saati** olmuştur.

Bozulma da mümkün değildi: `torch.save` yazması yarıda kalsaydı `torch.load` **hata verirdi**,
sessizce yanlış değer döndürmezdi. Yirmi dosya da sorunsuz okunuyor.

**Sonuç: tam ölçekli koşunun verisi kullanılabilir durumdadır.** Karar 26'daki bulgular
etkilenmemiştir.

---

## Karar 25 ile ilişkisi

Karar 25, ara kayıtta bölüm sayacının kırpıldığını bulmuştu. İkisi de **aynı yerin** —
kesinti/devam mekanizmasının — kusurlarıdır ve ikisi de aynı biçimde davranmıştır.

> Kod çalışır, çıktı üretir, çıktı makul görünür, ölçüm sessizce bozulur.

Devam mekanizması bu projede **iki kez** kusur çıkarmıştır. Üçüncü bir kusur olabileceği
varsayılmalıdır. Bu yüzden yeni lift+cruise koşuları bittiğinde de aynı üç denetim
tekrarlanacaktır — adım sayısı, kayıt sayısı, dizinin tek yönlü artışı.

---

## Ders

Bir betiğin "yanlış kullanılabilmesi" bir kullanım hatası değil, **betiğin kusurudur.** Kilit
üç satırdır ve baştan yazılabilirdi. Yazılmadığı için hatayı yalnız `ps` çıktısına bakma
alışkanlığı yakaladı.

---

*Kayıt 04.08.2026 · İlgili `24-kosu-altyapisi-ara-kayit.md`,
`25-ara-kayit-bolum-sayaci-hatasi.md`, `26-tam-kosu-on-kayit-degerlendirmesi.md`*
