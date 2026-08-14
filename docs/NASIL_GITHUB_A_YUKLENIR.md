# GitHub'a nasıl yüklenir

*14.08.2026 · CDSA deseniyle aynı, `Orfeomete/cdsa-bb3` ve kardeşlerinde uygulanan yol.*

⛔ **Sıra önemlidir.** Önce GitHub, sonra Zenodo bağlantısı, **en son** release. Release'i erken
açarsan DOI'yi metadata düzeltmeden önce mühürlemiş olursun.

---

## 1. Repoyu aç

1. github.com → **New repository**
2. **Owner** `Orfeomete` · **Repository name** `limulus-evtol`
3. **Public** seç. Zenodo yalnız public repoyu görebilir
4. **Add a README file** işaretini **KOY MA**, README zaten pakette
5. **Add .gitignore** ve **Choose a license** de **BOŞ** bırak, ikisi de pakette
6. **Create repository**

## 2. Dosyaları yükle

En kolayı tarayıcıdan sürükle bırak, fakat 39 MB ve yüzlerce dosya var, dolayısıyla **git komut
satırı daha güvenilir.**

```bash
cd <limulus-evtol klasorunun oldugu yer>
git init
git add .
git commit -m "LIMULUS-eVTOL v1.0.0: digital twin, preregistered campaigns and complete run records"
git branch -M main
git remote add origin https://github.com/Orfeomete/limulus-evtol.git
git push -u origin main
```

⚠️ **Kimlik doğrulama.** GitHub parola kabul etmiyor, kişisel erişim jetonu (personal access token)
gerekiyor. Zaten CDSA repoları için bir tane ürettiysen o çalışır. Yoksa
github.com/settings/tokens → **Generate new token (classic)** → `repo` yetkisi → jetonu parola
yerine yapıştır.

Tarayıcıdan yüklemeyi tercih edersen, **Add file → Upload files** her seferinde en fazla 100 dosya
alıyor, dolayısıyla klasör klasör yüklemen gerekir ve klasör yapısı korunmaz. Git yolunu öneririm.

## 3. Yüklemeyi doğrula

Repo sayfasında şunlar görünmeli.

- [ ] Kök dizinde `README.md` render olmuş, üç rozet görünüyor (DOI rozeti henüz kırık, normal)
- [ ] `LICENSE` sağ panelde **MIT License** olarak tanınmış
- [ ] `CITATION.cff` sağ üstte **Cite this repository** düğmesi üretmiş
- [ ] `9-DIJITAL-IKIZ/ogrenme/` altında on bir koşu dizini var
- [ ] `4-KARARLAR/` altında on bir ön kayıt belgesi var
- [ ] `preregistration-en/` altında dört dosya var

⚠️ **`CITATION.cff` düğmesi çıkmadıysa** dosyada YAML hatası vardır. GitHub sayfanın üstünde sarı
bir uyarı gösterir, hatayı orada okuyabilirsin.

## 4. Sonra ne olacak

Bu adım bittiğinde **release AÇMA.** Sıradaki iş Zenodo bağlantısı,
[`NASIL_ZENODO_DOI_ALINIR.md`](NASIL_ZENODO_DOI_ALINIR.md). Zenodo'yu bağlamadan release açarsan o
release DOI üretmez ve ikinci bir release açman gerekir, o da makaleye yazılacak DOI'yi karıştırır.
