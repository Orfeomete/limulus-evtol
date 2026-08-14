# Zenodo DOI nasıl alınır

*14.08.2026 · CDSA'da üç repo için uygulanan yol. Oradaki DOI'ler `10.5281/zenodo.20649672`,
`20649911`, `20649676`.*

⛔ **DONDURULMUŞ KURAL, CDSA'dan devralındı.** *Yeni release = yeni DOI.* Makaleye bir DOI yazdıktan
sonra metadata düzeltmek için **yeni release AÇMA**, yalnız dosya commit'i yap. Yeni release açarsan
makaledeki DOI o sürümü göstermez.

⛔ **İkinci kural.** DOI **gönderimden ÖNCE** alınır. Makaleye "DOI alınacaktır" yazılmaz, ya DOI
vardır ya da depo beyanı yoktur.

---

## 1. Önce sandbox'ta dene

Bu adımı atlama. Zenodo'nun GitHub bağlantısı bir kez yanlış kurulursa gerçek DOI ile uğraşmak zor.

1. https://sandbox.zenodo.org → **Log in with GitHub**
2. Yetkilendirme isteğini onayla
3. https://sandbox.zenodo.org/account/settings/github/ → listede `Orfeomete/limulus-evtol` görünmeli
4. Yanındaki anahtarı **ON** yap
5. GitHub'da `v1.0.0-test` adında bir release aç
6. Sandbox'ta birkaç dakika içinde kayıt oluşmalı. Oluştuysa bağlantı doğru kurulmuş demektir
7. Sandbox kaydını sil, test bitti

⚠️ Repo listede **görünmüyorsa** sayfadaki **Sync now** düğmesine bas. Hâlâ yoksa repo public
değildir.

## 2. Gerçek Zenodo

1. https://zenodo.org → **Log in with GitHub**, aynı hesap
2. https://zenodo.org/account/settings/github/ → `Orfeomete/limulus-evtol` anahtarını **ON** yap
3. **Şimdi release aç.** GitHub'da repo sayfası → **Releases** → **Create a new release**
   - **Tag** `v1.0.0`
   - **Title** `LIMULUS-eVTOL v1.0.0`
   - **Description** aşağıdaki metni yapıştır
   - **Publish release**

```
First archived release. Digital twin, preregistered reinforcement learning campaigns and complete
run records for a modular eVTOL design with four independently tilting rotor modules.

Contents. Six-degree-of-freedom dynamic model with rotor, aerodynamic, actuator and sensor
sub-models and a trim solver. Gymnasium learning environment with a six-level curriculum. PPO
implementation written for this study. Classical cascade reference controller. Preregistration
documents of every campaign with decision rules frozen before measurement, including one dated
correction kept together with the sentences it corrects. One hundred and thirty-two training runs
across eleven campaigns with their logs and policy checkpoints, and the deterministic evaluation
outputs.

Every number reported in the two accompanying manuscripts can be regenerated from the archived
scripts, which were not edited for archiving. Running the evaluation script in a fresh clone
reproduces the evaluation output bit-identically.

No funding is secured for this work at this stage.
```

4. Birkaç dakika içinde Zenodo kaydı oluşur. https://zenodo.org/account/settings/github/ sayfasında
   repo satırında DOI rozeti belirir

## 3. İki DOI vardır, hangisini kullanacağını bil

Zenodo iki tane üretir ve **karıştırılırsa makaleye yanlış olan girer.**

| DOI | Ne gösterir | Nerede kullanılır |
|---|---|---|
| **Concept DOI** | Her zaman **en son** sürümü gösterir | README rozeti, genel atıflar |
| **Version DOI** | Yalnız **v1.0.0**'ı gösterir, değişmez | **Makalelerde ve `CITATION.cff`'te** |

⚠️ **Makaleye version DOI yaz.** Concept DOI yazarsan, ileride v1.1.0 açtığında makaleyi okuyan
kişi makalenin anmadığı bir sürümü görür ve makaledeki sayılarla eşleşmeyebilir.

Zenodo kayıt sayfasında sağ panelde **Versions** kutusu vardır, concept DOI en üstte
"Cite all versions" altında, version DOI ise v1.0.0 satırındadır.

## 4. DOI'yi yerine koy

[`DOI_GUNCELLEME_KILAVUZU.md`](DOI_GUNCELLEME_KILAVUZU.md), yer tutucunun geçtiği her dosyayı
listeliyor. **14.08.2026 itibariyle bu adım tamamlandı**, version DOI `10.5281/zenodo.21934971`, concept DOI `10.5281/zenodo.21934970`. **Bu adım repoda dosya commit'idir, yeni release değildir.**

## 5. Gönderim formunda ne yazılacak

Elsevier gönderim formundaki **Data Availability** alanına.

```
Code, run records and evaluation outputs are openly available at
https://doi.org/10.5281/zenodo.21934971 (GitHub: Orfeomete/limulus-evtol, release v1.0.0).
No third-party data were used.
```

⚠️ **Açık erişim SEÇME.** Dördü de hibrit dergi, abonelik yolu ücretsiz. Zenodo arşivi açık olması
makaleyi açık erişim yapmaz ve APC doğurmaz.
