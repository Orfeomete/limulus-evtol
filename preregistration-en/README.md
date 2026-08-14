# Preregistration, English summaries

The preregistration documents themselves are in `4-KARARLAR/`, in Turkish, unmodified. The files
here summarise the frozen decision rules of each campaign so that a reader can check what was
committed to before measurement without reading Turkish. They are summaries and not translations.
Where a rule governs a number reported in a manuscript, the summary names the document it came from.

## The protocol

Four properties define what preregistration means in this project, and they are worth stating
plainly because they are stronger than the word usually implies.

**Rules are frozen before measurement.** Each campaign has a dated document written before any run
starts. It states the design, the budget, the seed count, the primary metric, and the rule by which
each possible outcome will be read. The document commits to no outcome.

**Results are appended, never merged.** When a campaign finishes, its results are written as a
separate section of the same document. The preregistration body is not edited. A reader can see
exactly what was decided in advance and what was learned afterwards, because the two are physically
separate parts of one file.

**Amendments are dated and written before results are seen.** If a design has to change mid-campaign,
the change is appended as a dated amendment before the outcome is known.

**Errors found later are corrected in place with the error left visible.** A results section that
turns out to be wrong gets a dated correction appended and a pointer at its head. The erroneous
sentences are not deleted. `4-KARARLAR/53` is the instance of this and the correction is dated
14 August 2026.

## Two rules that recur

**The significance rule.** A difference smaller than twice the sample standard deviation of the more
variable of the two groups is reported as *no difference*. It comes from `4-KARARLAR/12` and is
applied unchanged in `39`, `41`, `52` and `53`.

**Promotion is not competence.** Curriculum progress is defined by a reward threshold held over a
window. Reaching a curriculum task and completing it are reported separately and never conflated.
The rule comes from `4-KARARLAR/39` and it is the reason both manuscripts report the fraction of
policies that reached a task and the fraction that completed it as two different numbers.

## Index

| Summary | Document | Campaign |
|---|---|---|
| [`decision-rules-early.md`](decision-rules-early.md) | `12`, `36`, `38` | budget calibration, long-budget campaign |
| [`decision-rules-early.md`](decision-rules-early.md) | `39`, `41` | curriculum threshold probe, discount horizon probe |
| [`decision-rules-early.md`](decision-rules-early.md) | `47` | exploration and curriculum ablation |
| [`decision-rules-52.md`](decision-rules-52.md) | `52` | five-seed repeat of two probes, pre-correction environment rerun |
| [`decision-rules-53.md`](decision-rules-53.md) | `53` | wide-exploration full campaign, **carries a correction** |

Supporting decisions that are not preregistrations but govern how data is handled are `15` (action
space correction), `22` (a separate data directory per flag configuration), and `30` (the data audit
protocol applied to every campaign: step count, record count, monotonic counters, and flag lineage
read from the `ayar` field of each run log).
