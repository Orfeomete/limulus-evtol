# Decision rules, earlier documents

Summaries of the preregistrations that precede documents 52 and 53. Sources are in `4-KARARLAR/`.

---

## Document 12, training budget

The origin of the **significance rule** used throughout the project. A difference smaller than twice
the sample standard deviation of the more variable group is reported as *no difference*. The same
document sets the seed count at five and fixes the hyperparameter set before any campaign, so that
no tuning can follow an outcome.

It also contains the **nestedness check** that later becomes Rule 1 of the M1 manuscript. A more
general architecture cannot be outperformed by its own restriction at the layer where optimality is
computed. Where it is, the cause is sought in the solver before it is read as an architectural
result. That check caught two solver artifacts during development.

## Document 36, long-budget campaign

Preregisters the twenty-run campaign at three million steps per run that becomes `kosular_uzun/`.
The budget is declared as a limit of the computing environment rather than a convergence criterion,
and the manuscript claims are bounded to it. Results are in document 38.

⚠️ The throughput of this campaign **cannot be recovered from its own logs**, because every one of
its twenty runs was interrupted and resumed and the duration field of a resumed run counts only the
final slice. This is why the reported cost figures come from the uninterrupted runs of the later
campaign instead. The check is in `kampanya_karsilastirma.py`.

## Document 39, curriculum threshold probe

Preregisters the probe that tests whether the curriculum threshold is the bottleneck. Its rules
matter beyond that question.

- **Promotion is not competence.** Reaching a curriculum task and completing it are reported
  separately and never conflated. This becomes a recurring rule.
- **Frozen campaigns stay in the report.** A later campaign is added alongside an earlier one, never
  in place of it, and the two are mixed in no table.
- **A mechanism check is mandatory.** Whatever the headline metric shows, the altitude trace is
  measured, because a satisfied threshold is not evidence of the behaviour it was meant to proxy.

**Outcome.** The threshold was exonerated. A classical cascade controller scores above it at the same
level and completes the full episode, so the threshold is attainable and the bottleneck lies
elsewhere. The corresponding follow-up run was therefore not performed, and the reason is recorded
rather than the run being quietly dropped.

## Document 41, discount horizon probe

Preregisters the probe on the effective horizon after the altitude reward scale was corrected. Adds
the rule that a **learning-independent reference controller must be part of the measurement setup**,
which is the instrument that allows *the policy failed* to be distinguished from *the task is
unsolvable*. Both manuscripts later add this to their transferable conclusions.

**Outcome.** Survival roughly doubled and no policy climbed. The classical controller climbed from
150 m to between 282 and 292 m in the same environment through the same action space.

## Document 47, exploration and curriculum ablation

Preregisters a two-by-two factorial over initial exploration width and curriculum step size, two
seeds per cell, 300,000 steps per run, on the full variant only, because the question is learnability
rather than architecture. Directory `kosular_k47/`.

- **The primary metric is the name of the task reached, not the reward**, because reward scales are
  not comparable across two different curricula.
- **The success threshold is set in advance.** Both seeds of a cell must reach a task beyond the best
  seed of the frozen cell.
- **If the outcome is positive, no hyperparameter search follows.** A third value is not tried.
- **The result is classified as an exploratory hypothesis and a full-scale campaign requires its own
  preregistration.** That is document 53.

**Outcome.** Both cells carrying the wider exploration width passed, and the cell carrying only the
refined curriculum did not.

⚠️ **The design proved partly degenerate, and this was found during measurement rather than after.**
The refined curriculum inserts its new task after the second level, so the first two levels are
identical in both arms and a run that never passes the second level cannot express the factor at
all. The frozen cell and the refined-curriculum cell returned bit-identical rewards and episode
lengths in both seeds, which is what made the degeneracy visible. Three distinct cells were therefore
measured rather than four.

⚠️ **The hypothesis was tested at full scale in document 53 and did not hold.** At three million steps
the narrow setting reaches the same task and stops in the same place. The effect visible at 300,000
steps is an acceleration, not an unlock. See `decision-rules-53.md`.
