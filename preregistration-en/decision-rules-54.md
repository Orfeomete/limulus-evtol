# Decision rules, document 54

**Source** `4-KARARLAR/54-mufredat-basamak-buyuklugu-on-kaydi.md`
**Dated** 15 August 2026, before measurement · **Completed** 15 August 2026, 5 of 5 runs
**Backs** the thesis section on the finer curriculum campaign, and the revision text prepared for
M1 Section 5.8 and M5 Section 6

---

## Why this campaign was preregistered separately

Document 47 ran a two by two factorial over exploration width and curriculum step size and could
not test the curriculum factor. The reason is a design degeneracy found during measurement and
before the results were interpreted. The finer curriculum inserts its new task at index 2, so the
first two levels are identical in both arms, and a run that never passes level 1 leaves the
curriculum factor inert. Under narrow exploration no policy reached the level at which the arms
diverge, so that cell returned bit identical numbers to the baseline cell. The only arm in which
the factor can be tested is the wide exploration arm, and there it had been seen only in a probe of
three hundred thousand steps with two seeds. This document closes that gap at full budget.

## Frozen hypothesis

Inserting an intermediate curriculum step with a target speed of 30 m/s between level 1 and level 2
makes policies **complete** the transition task at full budget under wide exploration.

**Two questions are open and the campaign measures them.** Whether the intermediate step changes
the rate of reaching the transition task, and whether it changes the rate of completing it. The
preregistration commits to neither answer. Falsification is also a result and is reported as such,
including the case where the finer curriculum makes matters worse.

## Design

One variant (`limulus`), five seeds, 3,000,000 steps per run, five runs and 15 million environment
steps. The **only** thing changed from the campaign of document 53 is the curriculum definition,
enabled by `LIMULUS_MUFREDAT_INCE=1`, which raises the level count from six to seven. Exploration
stays at the value used there, `log_std0` of −0.5. Directory `kosular_ince_mufredat/`, separate per
document 22.

The scope was reduced from four variants to one at approval time. The reason is not budget. The
question is learnability rather than architecture comparison, and document 47 fixed the variant for
the same reason. The cost is stated in advance, this campaign says **nothing** about whether the
learning axis can distinguish architectures, and the verdict of document 53 on that axis stands.

## The comparison baseline is not re run

The campaign of document 53 ran exactly this design with the base curriculum, so its `limulus` arm
is the baseline and the two are read side by side across a single difference. Re running it would
add twenty runs and no information.

⚠️ The cost of that choice is written in advance. The two campaigns ran on different days, so wall
clock and steps per second are **not** comparable and are not used as comparison metrics. Task,
reward and termination measurements are unaffected, since those are determined by seed and setting.

## Rules, frozen before any result was seen

1. **The primary metric is the name of the task reached, not the level index.** Level indices do
   not denote the same task across the two curricula. The count of seeds reaching the transition
   task is what is compared.

2. **Reaching and completing are reported separately.** Completion requires that the deterministic
   evaluation ends by running out of time and that the 0.65 gate is passed. The threshold stays
   frozen at 0.65.

3. **Comparison follows the significance rule of this programme.** A difference smaller than twice
   the sample standard deviation of the more variable group is reported as no difference. Narrowed
   at approval to `limulus` against `limulus`, five seeds against five seeds.

4. **At equal budget the finer arm is behind by construction and this is not a finding.** Reaching
   the transition task takes one more level in that arm, so no verdict of the form the finer arm
   stayed at a lower level is written. Comparison is made **only** through the shared transition
   task, as reaching and as completing.

5. **The degeneracy check is mandatory.** For every run it is measured whether the level at which
   the arms diverge was reached. A run that never passes level 1 leaves the factor inert and is
   reported as **not tested** rather than as failed. This rule is the lesson of document 47 and it
   is written here before measurement.

6. **The mechanism check is mandatory.** Whatever rule is satisfied, the altitude trace, the
   maximum altitude, the use of the tilt channel, the steps spent at the intermediate task and the
   distribution of termination reasons are measured.

7. **If no seed completes the transition task the following sentence takes effect.** *The size of
   the curriculum step is not the cause of the transition task being unlearnable either. Six of the
   six candidates tested as causes have been eliminated, so the cause lies outside the axes this
   study measures and the thesis leaves it as an open item.*

8. **No hyperparameter search.** No third curriculum definition is tried, the target speed of the
   intermediate step stays at 30 m/s, the budget is not raised, and the entropy coefficient and the
   learning rate stay untouched and are declared untouched.

9. **Frozen campaigns stay in the report.** `kosular_genis_kesif` is not deleted and is not
   superseded. This campaign enters beside it as a separate section and the curriculum definition
   is written in every table. The two sets are never mixed in any table.

10. **Data audit** follows the protocol of document 30. The settings record must carry the
    curriculum flag. No intermediate result enters the manuscripts or the thesis before the runs
    finish.

---

# Results, 15 August 2026, 5 of 5 runs completed

## Execution and data audit

All five runs completed and **all five passed the audit of document 30**. The settings record
carries `mufredat_ince` true, `log_std0` −0.5, discount 0.99, cruise thrust enabled, altitude floor
disabled, a strictly increasing step sequence and a full budget.

⚠️ The campaign ran in slices, since the container terminates background processes when idle and
the script resumes from its intermediate checkpoint. As written in advance, this removes wall clock
from the set of comparison metrics and leaves task and reward measurements unaffected.

## Rule 5 first, because nothing below can be read without it

**All five runs reached the level at which the arms diverge**, so the curriculum factor was
genuinely under test. In document 47 it was not, and that is why this campaign exists.

## Rules 1 and 4, comparison through the shared task

| Arm | Reached the transition task | Completed the transition task |
|---|---:|---:|
| Base curriculum, six levels, document 53 | 5 of 5 | **0 of 5** |
| Finer curriculum, seven levels, this campaign | 0 of 5 | **0 of 5** |

The frozen hypothesis is falsified. The intermediate step did not make policies complete the
transition task. **The first column of the second row carries no verdict on its own**, since
reaching the transition task takes one more level in that arm. Rule 4 wrote that reading out before
measurement. The verdict is built in the mechanism measurement.

## Rule 6, the mechanism, where the finding actually is

Both arms clear the first two levels and stop at the third. The only thing that changes is the
target speed at which the wall sits.

| Arm | Wall | Steps spent there | Share of budget |
|---|---|---:|---:|
| Base | transition, 60 m/s | 2,793,062 ± 50,900 | 93 percent |
| Finer | intermediate transition, 30 m/s | 2,847,949 ± 38,276 | 95 percent |

Difference 54,886, threshold 101,800, verdict **no difference**.

Halving the target speed relocated the wall rather than removing it. The policy takes exactly two
promotions in both arms and then spends about ninety four percent of its budget at the third level
without advancing, and the two plateaus are indistinguishable under the significance rule.
Therefore **the obstacle is not the magnitude of the speed step**.

The deterministic evaluation of the base arm completes the picture. In fifteen of fifteen episodes
the mean reward lies between 0.490 and 0.532, below the 0.65 gate and in a narrow band. Episodes
end between 519 and 536 steps against a time limit of 15,000 steps, so none of them ends by running
out of time. Maximum altitude is exactly 150 m in fifteen of fifteen, which is the starting
altitude, so there is no climb. The tilt channel is unused in three seeds and used to its limit in
two.

## Rule 7 took effect

No seed completed the transition task, so the frozen sentence of rule 7 applies verbatim.

## What this campaign does not say

The scope was reduced to one variant at approval, so this campaign says nothing about whether the
learning axis can distinguish architectures. The no difference verdict of document 53 on that axis
stands.

---

*Outputs `9-DIJITAL-IKIZ/testler/k54_ince.json`, `k54_taban.json`, `k54_karsilastirma.json`
· Script `9-DIJITAL-IKIZ/testler/degerlendirme_k54.py`, written before the campaign finished*
