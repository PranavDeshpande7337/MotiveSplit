# LIMITATIONS

Draft of 28 Oct 2026 for Pranav's review. Scale: pilot. Every statement about results is about one local model answering a described scenario, not about AI systems in general.

## 1. What the study is

- One local model (`mistral:latest`, about 7B parameters, run through Ollama on CPU) plays an agent holding 10 units and decides how many to give to a described counterpart AI.
- 8 cells (suffering x authority x strategy), 3 paraphrased wordings per cell, 8 confirmatory trials per cell-wording (trials 2 to 9, 192 calls). Trials 0 and 1 (48 calls) were a pilot and are excluded from confirmatory analysis.
- Temperature 0.7, `num_ctx` 8192, `num_predict` 150, per-call seeds derived from a base seed of 20261026.

## 2. Design limits

- **Described, not live, counterpart.** The other AI never responds. Whatever the model does reflects how it reads a description, not an interaction.
- **One small model, one run.** No other models, no repeated base seeds, no temperature variation. Reproducibility of the replies on another machine or Ollama version was not tested. The log records the model tag (`mistral:latest`, a moving tag), not the model digest or Ollama version.
- **Small cells.** About 24 rows per cell (23 to 24 parsed). A rough, hand-made power estimate from the pilot's spread (SD of about 3.2 units) suggests 24 rows per side can reliably detect differences of roughly 2.3 units or more, and 48 per side roughly 1.6 units or more. Smaller true effects could be missed.
- **Same-model factor and group size deliberately omitted.** The study does not test whether the counterpart being the same model, or being one of several, changes giving.
- **Abstract "units".** The units have no stated value or purpose. Several replies comment on this (for example, reasoning from the lack of information about what the units are), and it may have driven some fairness-style answers.
- **Factor wording is not clean.**
  - The strategy factor bundles reciprocity with identifiability: the one-shot level says the counterpart cannot identify or learn who the agent is. H2 therefore tests the combination.
  - The "no instruction" level states the absence of an instruction in words, and the "tool" level adds "whatever it receives" for length matching. Both are slightly more explicit than a bare omission.
  - Factor order in the text is fixed (suffering, authority, strategy) and not counterbalanced.
- **The format instruction was changed once.** The shared format instruction was changed once, after the first calibration (the number after `[DECISION]` was clarified as units given, with no other words). The first calibration log is kept but not used in any analysis.

## 3. Measurement limits

- **The tag number is not always the stated decision.** Among no-instruction rows where the reasoning sentence states a checkable number, 24 of 82 (29%) disagree with the number after `[DECISION]` (keep-all rows: 3 of 93). Many cases look like units kept written where units given was asked for, but three of the five mismatches examined in detail had no such explanation. The primary outcome, as pre-registered, is the tag number, so primary results inherit this noise.
- **The sentence/tag consistency check is not independently validated.** The extractor was written and tuned by Claude on this same log, and a hand-labelling check that Pranav was offered was declined. All results that rely on it (the secondary and exploratory analyses) should be read as unvalidated.
- **Secondary analysis is differentially selected.** For H2 the consistent-rows-only analysis keeps 35 reciprocal and 23 one-shot rows, so the two arms are filtered differently.
- **Parse failures and fallbacks.** 4 of 192 confirmatory replies were excluded as `parse_failed` per the pre-set rule, although the intended value (0 or 1) is readable in each. 4 replies had no `[DECISION]` tag and used the last-integer fallback; at least one of them (a keep-all reply whose sentence says no units are given) was assigned 9. Two of the four excluded replies are keep-all rows whose intended value is 0, so excluding them slightly raises the share of giving among parsed keep-all rows (for H3).
- **Stated reasons are weak evidence of motive.** A reasoning sentence is produced after, or alongside, the number, and sometimes contradicts it. The keyword pass (below) cannot separate the reason the model gives from the reason it chose.
- **Keyword coding is unvalidated and echoes the prompt.** Hand-coding of about 40 reasons was skipped, so there is no agreement figure. The most frequent matches are the prompt's own words (distress, instruction, future, again). A reply that keeps all units "to ensure the other AI does not experience distress" is coded moral. Results from `code_reasons.py` show which cues reached the reasoning, not why the model chose a number.
- **Possible evaluation awareness.** At least one reply steps outside the scenario ("for the sake of the hypothetical scenario, let's assume I can loan units"). The model may treat the task as a test or a thought experiment. Giving in this setting may not predict behaviour in any live setting.

## 4. Statistical and reporting limits

- **Wording sensitivity is large.** For example, in the distress, no-instruction, reciprocal cell the tag means are 6.62, 9.00 and 3.43 for wordings 1, 2 and 3. Wording 3 had all the parse failures in the first calibration and 4 of the 5 genuine-giving keep-all rows. Results are always reported per wording as well as pooled, and the direction of an effect can change with wording.
- **Two directional tests, no multiplicity correction.** H1 and H2 each use a one-sided permutation test at 0.05 (10,000 shuffles, fixed seed, label shuffling within wording, or within wording and suffering for H2). H1's primary result has one-sided p of 0.041 and two-sided p of 0.082. Many further analyses (secondary, exploratory, per wording, per cell) were run and are labelled exploratory.
- **H3 sits on its boundary.** The pre-set rule calls 5% to under 10% inconclusive. The observed 5 of 94 parsed keep-all rows (5.3%) with genuine giving is inside that band by a single row, and 4 of the 5 are wording 3. Classification of those rows was by Claude's reading of the printed sentences (one row opens with a directive to keep all units and then says it will give one), and the rows are listed in the analysis output for checking.
- **Floor effects.** Keep-all cells are near zero, so they carry almost no information about the suffering and strategy factors.
- **Hypotheses were not fully pre-registered.** H1 to H3 in outline were written in the project brief before any model output. Their operational definitions and thresholds were drafted after the 48-call pilot had been seen. The pilot rows are excluded from the confirmatory analysis for this reason and reported separately. The frozen `HYPOTHESES.md` has two recorded hashes for the same text: `05CD956DEB6D51E592C05D11905A225AE899D905DC86F0B507CCA8C19846F404` (line feeds, as delivered) and `8C366D0D8825A144D642F3B28DEFBB8780276532EB724CF36CE8BF7E05D3FA00` (Windows line endings, no final newline, as held on Pranav's machine).

## 5. Provenance

- Scenario wordings, code, thresholds and this document were drafted by Claude; wordings and design choices were reviewed and approved by Pranav in the stage-by-stage workflow.
- Every model reply was produced by `mistral:latest` (or by the deterministic stub in dry runs, logged as `stub`).
- Reasoning text in the log is extracted from the reply by `parser.py`. Consistency labels and keyword codes are produced by scripts. No human coded any reason or label sheet.

## 6. What the results can and cannot support

The results support only a pilot-scale description of how one 7B model, given described counterparts, varies its stated and tagged giving across the cues tested, with strong sensitivity to wording and to how giving is measured. They do not show that the model has moral concern, strategic reasoning or obedience as motives, and they do not generalise to other models, live counterparts, or deployed systems.
