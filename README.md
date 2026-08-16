# LIMULUS-eVTOL

Digital twin, preregistered reinforcement learning campaigns, and complete run records for a
modular eVTOL design with four independently tilting rotor modules.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Data License: CC BY 4.0](https://img.shields.io/badge/Data%20License-CC%20BY%204.0-lightgrey.svg)](LICENSE-DATA)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21934971.svg)](https://doi.org/10.5281/zenodo.21934971)

> The badge above is the **version DOI** of release v1.0.0, which is the DOI both manuscripts cite,
> because a paper must point at the exact archived state its numbers came from. The **concept DOI**
> [`10.5281/zenodo.21934970`](https://doi.org/10.5281/zenodo.21934970) resolves to whichever version is newest.
>
> The `v1.0.0` archive on Zenodo still carries the placeholder string in its own `README.md` and
> `CITATION.cff`. That is not an oversight. The DOI is minted by the act of archiving, so it cannot
> exist inside the thing being archived. The placeholder was replaced here, on `main`, in a plain
> file commit and **not** in a second release, because a second release would mint a second DOI and
> invalidate the one the manuscripts cite.

---

## What this repository is for

Two manuscripts draw their numbers from this repository, and both are archived here in the state
that produced them.

| Manuscript | Subject | Target journal |
|---|---|---|
| **M1** | Comparing competing eVTOL control architectures as constrained variants of a single simulator | Simulation Modelling Practice and Theory |
| **M5** | Five silent defects in learning environment design for flight control | Robotics and Autonomous Systems |

The two share one codebase, one digital twin and one set of training runs, which is why they share
one repository and one DOI. Neither reproduces the other's sections, tables or figures.

**Every number reported in either manuscript can be regenerated from this repository by running the
scripts under `9-DIJITAL-IKIZ/testler/` and `10-MAKALELER/*/02_MAKALE_AKTIF/figurler/`.** None of
those scripts was edited for archiving. They are byte-identical to the versions that produced the
published numbers, which is also why the directory layout below reproduces the original project
layout rather than a tidier one. The scripts locate their inputs by relative path, and renaming the
directories would have meant editing the evidence.

This was checked rather than asserted. Running `9-DIJITAL-IKIZ/testler/degerlendirme_k53.py` inside
a fresh clone regenerates `k53_degerlendirme.json` **bit-identically** to the file the campaign
itself produced, which is the evaluation output behind M1 Tables 6 and 7. The same check passes
for `degerlendirme_k54.py`, whose comparison stage regenerates `k54_karsilastirma.json`
bit-identically from the two arm files.

## Layout

Directory names are Turkish, because they are the project's own. The mapping is as follows.

| Directory | English | Contents |
|---|---|---|
| `2-CIZIM-MOTORU/` | drawing engine | `geometri.py`, the single source of truth for every dimension and performance value |
| `4-KARARLAR/` | decisions | the preregistration documents, in Turkish, unmodified |
| `9-DIJITAL-IKIZ/dinamik/` | dynamics | six-degree-of-freedom model, rotor, aerodynamics, actuator, sensor, trim solver |
| `9-DIJITAL-IKIZ/ogrenme/` | learning | Gymnasium environment, PPO implementation, classical cascade controller, campaign runners, and the run records |
| `9-DIJITAL-IKIZ/testler/` | tests | verification and evaluation scripts |
| `10-MAKALELER/` | manuscripts | figure generators and figure input data for M1 and M5 |
| `preregistration-en/` | — | English summaries of the frozen decision rules, campaign by campaign |
| `docs/` | — | upload and DOI guides |

## The campaigns

Every run directory carries its own flag lineage in each run log's `ayar` field, so a number can
always be traced back to the configuration that produced it without consulting the manuscripts.

| Directory | Campaign | Runs | Budget per run | Preregistration |
|---|---|---:|---|---|
| `kosular/` | Pilot, pre-correction environment | 10 | 400k | `4-KARARLAR/12` |
| `kosular_v2/` | First corrected campaign | 20 | 1M | `4-KARARLAR/12` |
| `kosular_uzun/` | Long-budget campaign, `log_std0 = -1.5` | 20 | 3M | `4-KARARLAR/36`, results in `38` |
| `kosular_genis_kesif/` | Wide exploration, `log_std0 = -0.5` | 20 | 3M | `4-KARARLAR/53` |
| `kosular_ince_mufredat/` | Finer curriculum at full budget, `log_std0 = -0.5` | 5 | 3M | `4-KARARLAR/54` |
| `kosular_esik_sonda/` | Curriculum threshold probe, one seed | 4 | 300k | `4-KARARLAR/39` |
| `kosular_esik_sonda600/` | Altitude-scale correction, one seed | 4 | 600k | `4-KARARLAR/39` |
| `kosular_esik_gamma999/` | Both reward corrections, one seed | 4 | 600k | `4-KARARLAR/41` |
| `kosular_esik_sonda600_s5/` | Altitude-scale correction, five seeds | 20 | 600k | `4-KARARLAR/52` |
| `kosular_esik_gamma999_s5/` | Both reward corrections, five seeds | 20 | 600k | `4-KARARLAR/52` |
| `kosular_t3_v0/` | Pre-correction environment rebuilt behind a flag | 2 | 300k | `4-KARARLAR/52` |
| `kosular_k47/` | Exploration and curriculum ablation, four cells | 8 | 300k | `4-KARARLAR/47` |
| `kosular_lc/` | Lift-cruise propulsion unit probe | 5 | 1M | `4-KARARLAR/22` |
| `kosular_tk/` | Tilt-channel-free training probe | 5 | 1M | `4-KARARLAR/34` |
| `sonda/kosular_sonda/` | Early configuration probe | 2 | 300k | `4-KARARLAR/12` |

**149 runs in 15 run directories.** Total 42 MB.

Each run directory holds one `*_gunluk.json` training log per run and one `*.pt` policy checkpoint.
The logs record the step counter, episode reward, episode length, curriculum level and elapsed time
per rollout, together with the complete hyperparameter and flag dictionary.

⚠️ **The `sure` field is not a cost measure for resumed runs.** It counts only the final slice after
a checkpoint resume. Every run of `kosular_uzun` was resumed at least once, so that campaign's
throughput cannot be recovered from its own logs. Reported throughput comes from the thirteen
uninterrupted runs of `kosular_genis_kesif`. The script
`10-MAKALELER/M1_.../figurler/kampanya_karsilastirma.py` demonstrates and enforces this.

## Preregistration

The decision rules of every campaign were frozen before measurement and written into a dated
document under `4-KARARLAR/`. Results were appended as separate sections and the preregistration
body was never edited.

⚠️ **One results section carries a dated correction, and it is kept here deliberately.** Document
`53` misread the frozen campaign when comparing the two exploration settings, the error was found
while preparing the manuscripts, and a correction dated 14 August 2026 was appended. The erroneous
sentences were not deleted. A preregistration whose record is silently cleaned is no longer a
preregistration, and the corrected finding, that widening exploration accelerates rather than
unlocks, is what both manuscripts now report.

English summaries of the frozen rules are in `preregistration-en/`. They are summaries and not
translations, and where a rule matters for a reported number they name the file it came from.

## Reproducing the reported numbers

Requires Python 3.11, NumPy, PyTorch, Gymnasium and Matplotlib. See `requirements.txt`. Everything
runs on CPU. No GPU is required and none was used.

```bash
# unit verification of the pre-correction environment flag (M5 Section 3.4)
python3 9-DIJITAL-IKIZ/testler/dogrulama_ortam_v0.py

# deterministic evaluation of the five-seed repeats (M5 Tables 2 and 3)
python3 9-DIJITAL-IKIZ/testler/degerlendirme_k52.py

# deterministic evaluation of the wide-exploration campaign (M1 Tables 6 and 7)
python3 9-DIJITAL-IKIZ/testler/degerlendirme_k53.py

# the two campaigns read through one code path (M1 Section 4.4 and Section 5.9)
python3 10-MAKALELER/M1_DIJITAL_IKIZ_CERCEVESI/02_MAKALE_AKTIF/figurler/kampanya_karsilastirma.py

# every new number in M5 v6, derived from the evaluation output
python3 10-MAKALELER/M5_OGRENME_ORTAMI_KUSURLARI/02_MAKALE_AKTIF/figurler/sayilar_v6.py

# figures, both languages
python3 10-MAKALELER/M1_DIJITAL_IKIZ_CERCEVESI/02_MAKALE_AKTIF/figurler/fig_uret.py
python3 10-MAKALELER/M5_OGRENME_ORTAMI_KUSURLARI/02_MAKALE_AKTIF/figurler/fig_uret.py
```

Training a campaign from scratch is possible but slow. One three-million-step run takes 1.51 to
1.98 hours on two CPU cores, and a twenty-run campaign took 38.2 hours of wall time. The runners are
`9-DIJITAL-IKIZ/ogrenme/kampanya_52.sh` and `kampanya_53.sh`, both locked and resumable.

⚠️ **Determinism is machine-dependent.** Training is deterministic given a seed on one machine, and
the same seed on a different CPU or BLAS kernel diverges at the ninth decimal in the first log
record. Chaotic training dynamics amplify that into different episode counts by 600k steps while the
qualitative outcome is unchanged. Expect to reproduce findings, not bit patterns, across machines.

## What this repository does not contain

No flight data, no wind tunnel data, and no computational fluid dynamics or finite element results.
The dynamic model reproduces nine independent quantities of the conceptual design study it derives
from, which shows consistency with its source and not absolute correctness. Both manuscripts state
this.

## Citation

If you use this work, please cite the software through its DOI and, where relevant, the manuscript
whose results you rely on. See `CITATION.cff`.

## License

Code is MIT licensed. Run records, evaluation outputs, figures and preregistration documents are
CC BY 4.0. See `LICENSE` and `LICENSE-DATA`.

---

*Mete Cantekin · ORCID [0009-0001-6990-6340](https://orcid.org/0009-0001-6990-6340)*
*Nisantasi University, School of Civil Aviation · Istanbul Beykent University, Graduate Education Institute*
