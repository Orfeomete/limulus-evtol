# Decision rules, document 52

**Source** `4-KARARLAR/52-m5-revizyon-olcumleri-on-kaydi.md`
**Dated** 11 August 2026, before measurement · **Completed** 12 August 2026, 42 of 42 runs
**Backs** M5 Sections 3.4, 4.3, 5.4, 6 and Tables 2 and 3

Two measurements were opened, both requested by review of the M5 manuscript. Part A repeats two
single-seed probes with five seeds. Part B rebuilds the pre-correction environment so that a
diagnostic signature can be produced from complete logs.

---

## Part A, five-seed repeat of two probes

**Design.** Four variants, seeds 0 to 4, 600,000 steps per run, two probes, forty runs and 24 million
environment steps. Probe A1 carries the altitude-scale correction with discount 0.99, probe A2 adds
the widened discount horizon at 0.999. Directories `kosular_esik_sonda600_s5/` and
`kosular_esik_gamma999_s5/`, separate per document 22.

**Rules, frozen before any result was seen.**

1. **The primary output is the five-seed counterpart of the reported bands.** Survival fraction and
   normalized reward are reported per variant as a mean and a sample deviation. Whatever comes out
   is what goes into the table and the figure.
2. **Ordering between variants may be read now and only under the significance rule.** A difference
   smaller than twice the sample deviation is reported as no difference. **The original single-seed
   bands stay on record and are mixed with the new bands in no table.**
3. **Curriculum precondition.** A run trained for fewer than 200,000 steps at the second level has
   its evaluation flagged out of distribution. **The budget is not increased.** The count of
   out-of-distribution runs is reported per variant and per probe.
4. **A mechanism check is mandatory.** Whatever the bands show, the altitude trace is measured. Peak
   altitude, whether any climb occurred, and tilt channel usage are reported. The measurement does
   not stop because a rule was satisfied.
5. **The central finding is updated in either direction.** If no seed climbs, the claim is restated
   with the larger episode count. If any seed climbs, that changes the manuscript's central result
   and the manuscript is rewritten accordingly. The preregistration commits to no outcome.
6. **Data audit** follows document 30.
7. No hyperparameter search, no budget change, and no interim result enters any manuscript before
   the campaign completes.

⚠️ **Seed 0 is the seed of the original probes and serves as a determinism check.** If the repeat does
not reproduce the original bit for bit, the reason is investigated and written into the results. It
is not passed over.

**Outcome.** No difference in all twelve of the twelve variant pairs, largest difference 12.8 points
against a threshold of 61.6. Three runs missed the curriculum precondition and the budget was not
increased. No policy climbed in any of the 120 episodes. The determinism check did **not** reproduce
bit for bit, and the investigation the rule required found the cause to be a different CPU or BLAS
kernel, diverging at the ninth decimal in the first log record. Document 47's bit-equality result
therefore holds within a machine and not across machines, and this is stated in the results section.

Two observations the preregistration did not anticipate were recorded as scope corrections. Twelve
of sixty episodes in the 0.999 arm ended by running out of time and two policies passed the 0.65
threshold **without climbing**. The full variant used the tilt channel between 2 and 27 degrees where
the single-seed measurement had given 0.0 to 0.3.

---

## Part B, rerun of the pre-correction environment

**Feasibility step, before any run.** A new flag `LIMULUS_ORTAM_V0` restores the pre-correction
environment with three corrections reverted together: absolute action mapping, the stall penalty
firing in hover, and the unpenalized attitude-overrun termination. The three are reverted together
because the diagnostic signature is the product of that whole.

⚠️ **The default is off, and with the flag off the behaviour must be bit-equivalent to the current
code.** The flag is verified at unit level. **If the reconstruction cannot be done reliably, the run
is cancelled**, that outcome is written into the document, and the manuscript's declaration that the
records were only partially retained stays as it is. No invented reconstruction is run.

**Design.** Full variant, two seeds, 300,000 steps per run, directory `kosular_t3_v0/`.

**Rules, frozen before any result was seen.**

1. **The primary output is the trace signature**, the direction of mean reward against mean episode
   length. If reward rises while episode length falls, the signature is confirmed with complete logs
   and the manuscript's numbers are rewritten from the new runs' own logs.
2. **If the signature does not appear, that is written too.** The existing declaration stays, the
   reason is investigated, and if none is found it is recorded as not reproduced. No hyperparameter
   search, no third seed, no longer budget.
3. These numbers feed **only** the relevant manuscript section and the corresponding open item. They
   enter no architectural comparison and no other table.
4. Data audit follows document 30, and no text changes before the runs finish.

**Outcome.** The flag-off regression matched the pre-edit record by hash. A zero-action episode hit
the ground at step 421 where the pre-correction record gives 420, which is an independent indication
that the rebuild reconstructs the right environment and was not foreseen by the preregistration. The
signature appeared in both seeds and at a larger amplitude than the original partially retained
records.
