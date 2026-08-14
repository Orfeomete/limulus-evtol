# Decision rules, document 53

**Source** `4-KARARLAR/53-genis-kesif-kampanyasi-on-kaydi.md`
**Dated** 11 August 2026, before measurement · **Completed** 13 August 2026, 20 of 20 runs
**Corrected** 14 August 2026, see the end of this file
**Backs** M1 Sections 4.3, 4.4, 5.8, 5.9 and Tables 6 and 7, and M5 Section 5.5

---

## Why this campaign was preregistered separately

Document 47 isolated a candidate cause of the learning failure, the exploration width, but its own
rules classified the result as an exploratory hypothesis and required a separate preregistration
before any full-scale campaign. Running the campaign first and writing the rules afterwards would
have invalidated the frozen rules of the campaign already reported. The correct order is
preregistration, approval, then campaign, and this document is the first step of it.

## Frozen hypothesis

Raising the initial policy log standard deviation from −1.5 to −0.5 carries policies to the
transition task at full budget. **Two questions are open and the campaign measures them.** Whether
the policy merely reaches the task or completes it, and whether the learning axis can distinguish
architectures for the first time. The preregistration commits to neither answer.

## Design

Four variants, five seeds, 3,000,000 steps per run, twenty runs and 60 million environment steps.
The **only** thing changed from the frozen campaign is `log_std0`. The curriculum is the base
six-level one, the two reward corrections are disabled, discount stays at 0.99. Directory
`kosular_genis_kesif/`, separate per document 22.

⚠️ Three reasons for keeping the reward corrections off. One variable per round. Comparability with
the frozen campaign across a single difference. And the hypothesis was formed under this setting in
document 47, so it is tested under this setting.

## Rules, frozen before any result was seen

1. **The primary metric is the name of the task reached, not the reward.** The task name is
   reported, not the level index. The count of seeds per variant reaching the transition task is
   what is compared.
2. **Promotion is not competence.** Reaching the task and **completing** it are reported separately.
   Completion means the termination reason in deterministic evaluation is timeout and the 0.65
   threshold is passed. The threshold stays frozen at 0.65.
3. **Architectural comparison gate.** The learning axis is declared comparable only if at least
   three seeds of all four variants are measured on the transition task. In that case the
   significance rule applies and a difference below twice the sample deviation is reported as no
   difference.
4. **Nestedness check.** If the full architecture comes out meaningfully worse than synchronous
   tilt, that is an optimization defect and not an architectural finding, and it is written as such.
5. **A mechanism check is mandatory.** Whatever rule is satisfied, the altitude trace, peak altitude,
   tilt channel usage and the distribution of termination reasons are measured.
6. **If no seed completes the task, the following sentence goes into force.** *Exploration width
   carries the policy to the transition task but does not make it complete the task even at full
   budget. The learning axis has not entered a regime capable of distinguishing architectures in
   this campaign either, and the five policy-free metrics remain the only evidence about
   architecture.* The manuscript's inconclusive verdict is replaced by this measured verdict, in
   whichever direction it comes out.
7. **Frozen campaigns stay in the report.** This campaign replaces none of them, it is added
   alongside as its own section, and the `log_std0` value is written in every table. The two sets are
   mixed in no table.
8. **No hyperparameter search.** No third value of `log_std0`, no budget increase, and the entropy
   coefficient and learning rate stay untouched, with that fact declared in the manuscript.
9. **Data audit** follows document 30, with the `ayar` field carrying the `log_std0` value.

## Outcome

Twenty of twenty runs completed, data audit passed 20 of 20, wall time 38.2 hours. No policy passed
the 0.65 threshold, all sixty evaluation episodes ended in ground impact, and peak altitude stayed at
150.0 m in all sixty, so rule 6's frozen sentence went into force. The comparison gate of rule 3
opened for the first time and no difference came out in all six variant pairs, largest difference 0.9
points. Rule 4's nestedness check was clean at 0.0 points.

---

## ⛔ Correction, 14 August 2026

**The rule 1 reading in the results section was wrong, and the erroneous sentences were left in
place in the Turkish document rather than deleted.**

The results section stated that document 47's exploratory hypothesis had been confirmed at full
scale, on the grounds that all twenty runs reached the transition task while the frozen campaign had
nineteen runs sitting on a plateau. That comparison was made from prose rather than from the frozen
campaign's logs. When both campaigns were read through one script, the plateau turned out to sit
**above** the transition task, not below it.

| Measure | Frozen, `log_std0 = -1.5` | Wide, `log_std0 = -0.5` |
|---|---|---|
| Distribution of task reached | 19 transition, 1 transition under gust | **identical** |
| Run that went further | synchronous tilt, seed 2 | **same seed** |
| Arrival at the transition task, median | 197,632 steps | 156,672 steps |
| Arrival, mean | 216,371 ± 58,231 | 161,382 ± 41,461 |
| Policies passing the 0.65 gate | 0 of 20 | 0 of 20 |
| Peak altitude | 150.0 m | 150.0 m |

The 54,989-step difference between the means is below the project's two-deviation threshold of
116,463 steps.

**Corrected verdict. The two campaigns cannot be told apart on the preregistration's primary metric.
The only measured effect of wide exploration is the time of arrival. Widening exploration
accelerates rather than unlocks, and document 47's hypothesis is not confirmed at full scale.**

Rule 6's frozen sentence remains in force because its condition, that no seed completes the task,
was met. Its first clause narrows under this measurement, and both manuscripts print the sentence
together with the correction rather than either alone.

The script that reads both campaigns through one code path is
`10-MAKALELER/M1_DIJITAL_IKIZ_CERCEVESI/02_MAKALE_AKTIF/figurler/kampanya_karsilastirma.py`, and it
exists so that this particular error cannot recur.
