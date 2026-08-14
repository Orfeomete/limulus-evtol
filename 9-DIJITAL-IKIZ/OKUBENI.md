# 9-DIJITAL-IKIZ — Kısım II ve III'ün altyapısı

Tezin fizik katmanı, öğrenme ortamı, karşılaştırma metrikleri, Unity köprüsü ve testleri.

## Araç kararı

**Fizik Python'da, görselleştirme Unity'de.** Pekiştirmeli öğrenme eğitimi Unity'ye hiç uğramaz.
Yüksek lisans tezinde Unity zorunluydu çünkü ajanın algısı görsel ve ışın-tabanlıydı. Burada gözlem
bir durum vektörüdür, dolayısıyla oyun motorunun ne render'ına ne fiziğine ihtiyaç var. Ölçülen
hız saniyede ~680 çevre adımı. Ayrım, bilimsel katkıyı araçtan bağımsız kılar.

## Klasör haritası

```
dinamik/       fizik katmani
  konfigurasyon.py   geometri.py'den okur, VARSAYIMLAR sozlugu, 4 varyant
  atmosfer.py        ISA + Dryden turbulans + 1-cos ayrik gust
  rotor.py           momentum teorisi, egik akis, profil gucu, itki tavani
  aerodinamik.py     kanat polari, stall sonrasi yumusak gecis
  aktuator.py        tilt oran limiti, itki gecikmesi, eklem yuk zarfi
  sensor.py          gurultu, sapma, gecikme, ornekleme
  govde.py           6-DOF hareket denklemleri, RK4
  arac.py            butunlesik arac
  trim.py            genel trim cozucu, zarf, koridor
ogrenme/
  ortam.py           Gymnasium ortami, mufredat, odul
  temel_kontrolcu.py kaskad PID, karsilastirma tabani
  metrikler.py       alti karsilastirma metrigi
  egitim.py          PPO, bagimsiz uygulama
kopru/
  sunucu.py          Python ucu, UDP yayin
  LimulusBridge.cs   Unity ucu
testler/
  test_dinamik.py    43 test
```

## Çalıştırma

```bash
cd dinamik   && python3 trim.py            # trim, hiz taramasi, varyant karsilastirmasi
cd ogrenme   && python3 metrikler.py       # dort politikasiz metrik  (~4 dk)
cd ogrenme   && python3 temel_kontrolcu.py # hover, tirmanis, gecis
cd ogrenme   && python3 egitim.py --duman  # PPO duman testi
cd kopru     && python3 sunucu.py --kendi-kendine-test
cd testler   && python3 test_dinamik.py    # 43/43
```

Bağımlılıklar: numpy, scipy, gymnasium, torch. `geometri.py` tek doğruluk kaynağıdır, tezden
hiçbir sayı elle kopyalanmaz.

## Modelin doğrulanma durumu

Tezin bağımsız hesaplanmış sayılarını yeniden üretiyor.

| Büyüklük | Model | Tez |
|---|---|---|
| Disk alanı | 6,158 m² | 6,158 |
| Disk yüklemesi | 1195 N/m² | 1195 |
| İndükleme hızı | 22,1 m/s | 22,1 |
| Hover gücü | 913,8 kW | 913 |
| Cruise C_L | 0,779 | 0,78 |
| Cruise L/D | 16,07 | 16,1 |
| Cruise / V_S1 | 1,39 | 1,39 |
| 1/rev · pal geçiş | 17,4 · 87,0 Hz | 17,4 · 87,0 |
| OEI kaldırma oranı | %90,7 | %90,7 |

**Bu tutarlılıktır, doğrulama değil.** İki hesap da aynı analitik kabullerden türüyor ve aynı
belirsizliği paylaşıyor. Bağımsız doğrulama CFD, FEM ve uçuş verisi gerektirir.

## ⚠️ İki ayrı x ekseni var

```
x_ist   "istasyon"   burun x=0, geriye artar     geometri.py ve tez
x_b     "gövde"      CG x=0, İLERİYE artar       dinamik denklemler
dönüşüm x_b = x_cg − x_ist        ->  Limulus.govde_x()
```

İlk sürümde bu dönüşüm atlandı ve tüm yunuslama momentlerinin işareti tersti.
`test_isaret_moment_kolu` bunu kalıcı olarak kontrol eder. Modele yeni bir kuvvet eklenirken önce
o test koşulur.

## Kurulum sırasında yakalanan model hataları

Her biri bir testle ya da bir tutarlılık kontrolüyle yakalandı ve kaynak kodda gerekçesiyle
kayıtlı. Kayıt tutuluyor çünkü aynı hatanın tekrar üretilmemesi gerekiyor.

| # | Hata | Nasıl yakalandı | Sonucu |
|---|---|---|---|
| 1 | İstasyon/gövde ekseni karışıklığı | işaret birim testi | tüm pitch momentleri tersti |
| 2 | Taşıma eğrisinde sıçrama (α_stall bağımsız verilmiş) | eğri sürekliliği testi | α_stall artık türetiliyor |
| 3 | İleri uçuşta profil gücü yok | trim çözücü fiziksel olmayan nokta buldu | güç üç terime ayrıldı |
| 4 | κ faydalı itki gücüne de uygulanmış | pervane verimi 0,62 çıktı (tez 0,80) | κ yalnız indükleme terimine |
| 5 | Download kanat çeyrek-veterinde etkitilmiş | hover'da sahte 53 N m moment | pod istasyonlarına dağıtıldı |
| 6 | Kontrol dağıtım matrisi tilt bağımsız | cruise'da 32° tutum sapması | B(tilt) yapıldı, F3'ün kanıtı |
| 7 | Kontrolcü her rejimde hover tahsisi | geçişten sonra 300 m'den yere dalış | sin(tilt) rejim harmanı |
| 8 | Trim çözücü yerel minimumda | LIMULUS senkrondan kötü çıktı | iç içe geçmişlik garantisi |
| 9 | Düşük hızda sert anahtar | RK4 dördüncü derece yakınsamasını kaybetti | yumuşak harman |
| 10 | Geçiş koridoru tilt'i dörde de dayatıyor | dört varyant birebir aynı çıktı | ortalama tilt + sapma |
| 11 | Enerji metriği eksik bacakları atlıyor | uçamayan varyant en verimli çıktı | görev tamamlanamadı işareti |
| 12 | **Kodda değil, yorumda.** `∂M/∂T` ile `∂M/∂θ` tek kanal sanıldı | M4 için yapılan literatür taraması | iki sütun ayrıldı, tam modelde sonlu farkla ölçüldü |

**12. hata diğerlerinden farklıdır ve bu yüzden ayrı okunmalıdır.** Kod doğruydu, sayılar
doğruydu, testler geçiyordu. Yanlış olan yalnız sayıların *açıklamasıydı*. Sayısal denetim bu
sınıfı yakalamaz. Ayrıntı `../4-KARARLAR/14-kontrol-otoritesi-duzeltmesi.md`, doğrulama
`testler/dogrulama_kontrol_otoritesi.py`.

⚠️ Yukarıdaki 6. satırın "F3'ün kanıtı" ifadesi de bu yüzden yanlıştır. 32°'lik sapma mimarinin
değil, dağıtıcının kusuruydu.

## Bilinen sınırlar

- Aerodinamik ve rotor modelleri CFD ile doğrulanmadı. Karşılaştırma **görelidir**.
- C# tarafı bu ortamda derlenmedi ve çalıştırılmadı. Unity'de ilk kez denenecek.
- Yanal-yönel eksen (yatış, sapma) modelde var ama trim ve metrikler simetrik uçuşa odaklı.
- Tam ölçekli PPO koşuları yapılmadı, altyapı hazır.

---

*İlgili `../4-KARARLAR/09-tez-mimarisi-karari.md`, `../4-KARARLAR/10-dinamik-model-bulgulari.md`,
`../LIMULUS_DURUSTLUK_CERCEVESI.md`*
