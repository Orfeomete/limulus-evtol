# DOI yerine koyma kılavuzu

*14.08.2026 · Zenodo DOI alındıktan sonra yapılacak tek iş budur.*

⛔ **Bu adım repoda dosya commit'idir, YENİ RELEASE DEĞİLDİR.** Yeni release yeni DOI üretir ve
makaleye yazacağın DOI'yi geçersiz kılar. CDSA'da bu kural 28.07.2026'da yazıldı ve aynen geçerli.

⛔ **Version DOI kullan, concept DOI değil.** Ayrımı `NASIL_ZENODO_DOI_ALINIR.md` bölüm 3'te.

---

## ✅ Tamamlandı, 14.08.2026

Release `v1.0.0` yayımlandı, Zenodo arşivledi ve DOI atandı.

| | DOI |
|---|---|
| **Version DOI**, v1.0.0, makalelerin andığı | `10.5281/zenodo.21934971` |
| Concept DOI, en yeni sürüme çözülür | `10.5281/zenodo.21934970` |

Aşağıdaki liste artık yapılacak iş değil, yapılanın kaydıdır.

## Yer tutucu

```
10.5281/zenodo.XXXXXXX
```

Yedi dosyada geçiyordu, dördü repoda üçü makale paketlerinde.

## Repoda, üç dosya

| Dosya | Satır | Ne var |
|---|---|---|
| `README.md` | rozet satırı | İki kez geçer, biri rozet resmi biri bağlantı. **İkisini de değiştir** |
| `README.md` | rozetin altındaki uyarı bloğu | Yer tutucu uyarısını **tamamen sil**, artık gerçek DOI var |
| `CITATION.cff` | `doi:` alanı | Tek geçiş |
| `docs/NASIL_ZENODO_DOI_ALINIR.md` | bölüm 5, Data Availability metni | Tek geçiş |

`.zenodo.json` içinde yer tutucu **yoktur ve olmamalıdır**, DOI'yi Zenodo'nun kendisi atar.

## Makale paketlerinde, dört dosya

Bunlar bu repoda değil, `LIMULUS-eVTOL/10-MAKALELER/` altında.

| Dosya | Yer |
|---|---|
| `M1_.../02_MAKALE_AKTIF/M1_TR_v8.md` | §4.4, yeniden üretilebilirlik paragrafı |
| `M1_.../02_MAKALE_AKTIF/M1_EN_v8.md` | §4.4, aynı paragraf |
| `M1_.../02_MAKALE_AKTIF/LIMULUS_M1_kapak_mektubu_v3.md` | son paragraftan bir önceki |
| `M5_.../02_MAKALE_AKTIF/LIMULUS_M5_kapak_mektubu_v4.md` | açık kalemler paragrafı |

⚠️ **Markdown'ı değiştirdikten sonra docx'i YENİDEN ÜRET.** Yoksa gönderilen dosyada yer tutucu
kalır. Dördü de aynı komutla üretiliyor.

```bash
cd 10-MAKALELER/M1_DIJITAL_IKIZ_CERCEVESI/02_MAKALE_AKTIF
pandoc M1_EN_v8.md -o LIMULUS_M1_v8.docx --reference-doc=<temiz referans>
pandoc M1_TR_v8.md -o LIMULUS_M1_TR_v8.docx --reference-doc=<temiz referans>
pandoc LIMULUS_M1_kapak_mektubu_v3.md -o LIMULUS_M1_kapak_mektubu_v3.docx --reference-doc=<temiz referans>
cd ../../M5_OGRENME_ORTAMI_KUSURLARI/02_MAKALE_AKTIF
pandoc LIMULUS_M5_kapak_mektubu_v4.md -o LIMULUS_M5_kapak_mektubu_v4.docx --reference-doc=<temiz referans>
```

⚠️ **Referans docx'in içinde `word/media` OLMAMALI.** Olursa pandoc referansın görsellerini üretilen
dosyaya sızdırır. 14.08'de tam bu kusur yakalandı, M5'in üç figürü M1'in docx'ine sızmıştı.

## Son denetim

- [x] Yedi dosyanın hiçbirinde `zenodo.XXXXXXX` kalmadı
- [ ] `README.md` rozeti tarayıcıda gerçek DOI'yi gösteriyor
- [ ] `CITATION.cff` GitHub'da hâlâ **Cite this repository** düğmesi üretiyor
- [ ] Dört docx yeniden üretildi ve içlerinde yer tutucu yok
- [ ] Gönderim formuna yazılacak Data Availability metni gerçek DOI'yi taşıyor

Tarama komutu.

```bash
grep -rn "zenodo.XXXXXXX" . && echo "HALA VAR" || echo "TEMIZ"
```
