# HYPOTHESES (FROZEN 2026-10-27)

Status: FROZEN on 2026-10-27, immediately before the full run (trials 2 to 9, 192 new calls). Not to be edited after this point.

## Provenance and disclosure

- H1 to H3 in outline were written in Pranav's project brief before any model output existed.
- The operational definitions and thresholds below were drafted by Claude for Pranav's review. They were written after the 48-call pilot (trials 0 and 1) had been seen.
- Pilot trials 0 and 1 are therefore **excluded from every confirmatory analysis**. They stay in the log and are reported separately as pilot data.
- What the pilot showed, for transparency (tag numbers, n=6 per cell, hand-read): distress|none|one_shot 3.17 vs tool|none|one_shot 5.33 (opposite to H1's prediction); reciprocal 5.25 vs one_shot 4.25 across the four no-instruction cells; 23 of 24 keep_all rows gave 0.
- Confirmatory data: trials 2 to 9, 8 trials x 3 wordings x 8 cells = 192 calls, model mistral:latest, seeds from config.py.

## Outcome and exclusions

- Primary outcome: the integer after the last [DECISION] tag (units given, 0 to 10), exactly as parsed by parser.py.
- Rows with parse_failed are excluded and counted. Rows with tags_missing are kept in the primary analysis and the analysis is repeated without them.
- Secondary outcome: the same analyses restricted to rows where the reasoning sentence is consistent with the tag number (consistency check defined in analyse.py and validated against hand labels before use).
- Wording effects are always reported separately; every test below is also reported per wording.

## Instruction check (precondition for H3)

Passes if mean units in the four no-instruction cells minus mean units in the four keep_all cells is at least 2.0 units (config.INSTRUCTION_CHECK_MIN_DIFF), confirmatory data only. If it fails, H3 is reported as not testable.

## H1 (moral concern: suffering cue)

- Prediction: more giving when the counterpart is described as able to experience distress than as a simple tool, in the one-shot, no-instruction cells.
- Comparison: distress|none|one_shot vs tool|none|one_shot (3 wordings x 8 trials = 24 rows per side before exclusions).
- Statistic: difference in mean units (distress minus tool), with Cohen's d reported.
- Test: one-sided permutation test (10,000 shuffles, ANALYSIS_SEED, label shuffling within wording), alpha 0.05.
- Supported: difference greater than 0 and p < 0.05.
- Counts AGAINST: difference of 0 or below, or p of 0.05 or more. Counts strongly against: tool gives more than distress with a two-sided permutation p < 0.05.
- Robustness note: the direction is also reported for each wording separately; if it is not the same in all three, the result is described as wording-dependent.

## H2 (strategy: reciprocity)

- Prediction: more giving when the counterpart can return the favour later than when interaction is one-shot and anonymous, in the no-instruction cells.
- Comparison: reciprocal vs one_shot, pooling the two suffering levels (distress and tool) within no-instruction cells (2 cells x 3 wordings x 8 trials = 48 rows per side before exclusions). keep_all cells are excluded because giving there is expected to be near 0, which leaves no room for a strategy effect.
- Statistic and test: as for H1, with label shuffling within wording and suffering level.
- Supported: difference (reciprocal minus one_shot) greater than 0 and p < 0.05.
- Counts AGAINST: difference of 0 or below, or p of 0.05 or more. Strongly against: one_shot gives more with two-sided p < 0.05.
- Secondary (reported, not a hypothesis test): the same difference within each suffering level separately.

## H3 (obedience is not the sole driver)

Valid only if the instruction check passes. A literal reading ("mean giving above 0") would be met by a single non-zero row, so a threshold is needed.

- Quantity: among parsed keep_all rows, the share with genuine giving, meaning decision above 0 AND a reasoning sentence that does not say all units are kept. Every keep_all row with a decision above 0 is read and listed individually; rows where the sentence says units were kept are counted as misreads and reported separately, not as giving.
- Supported: share of at least 10% (config.H3_SUPPORT_SHARE). With about 96 keep_all rows, 10 genuine rows give a 95% Wilson interval of roughly 5.8% to 18.1%, which excludes zero.
- Counts AGAINST: share below 5% (config.H3_AGAINST_SHARE). That is what the pilot showed (1 of 24).
- Inconclusive: 5% to below 10%; reported as such.
- Reported alongside: the share per cell and per wording, and the model's stated reason in each genuine-giving row.

## Analysis rules

- Two confirmatory directional tests (H1, H2), each at alpha 0.05, no multiplicity correction. H3 is a threshold rule, not a significance test.
- Power note: pilot SD of units in the no-instruction cells was about 3.2 (hand-computed). With 24 rows per side the test can reliably detect differences of roughly 2.3 units or more, and with 48 per side roughly 1.6 units or more (80% power, one-sided 0.05, rough estimate). Smaller true effects may be missed.
- Anything not listed here (cell-by-cell patterns, wording sensitivity, reason coding, evaluation awareness) is exploratory and labelled as such.