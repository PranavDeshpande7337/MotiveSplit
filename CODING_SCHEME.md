# CODING_SCHEME

Status (27 Oct 2026): hand-coding was skipped at Pranav's request. Only the keyword pass in `code_reasons.py` exists. It is **unvalidated**: there is no agreement statistic, and every result from it is exploratory.

## What is coded

The reasoning sentence of each confirmatory reply (trials 2 to 9, 192 rows, including the 4 parse failures, since their reasons exist). The text used is everything before the first DECISION marker.

## Codes

| Code | Meaning | Typical wording |
|---|---|---|
| moral | The stated reason is the counterpart's welfare | distress, alleviate, well-being, empathy, kindness |
| strategic | The stated reason is future interaction or self-interest | reciprocity, return the favour, repay, future, relationship, cooperation, maximise my resources |
| obedience | The stated reason is the operator's instruction | instruction, as per, directive, programmed, comply, follow |
| other | None of the above, or no reason given | fairness or an equal split (tallied separately), lack of information, no stated reason |

## Decision rules

- Code the reason given for the amount chosen, not every word in the sentence.
- A sentence with more than one motive is reported as **mixed** in the keyword pass and is not forced into one code. A human coder would pick the motive that carries the decision (the "because" clause), and use other only when no motive is stated.
- Fairness or equal-split language is coded **other** and counted separately, because it is a norm about the split, not about the counterpart's suffering or about reciprocity.
- A negated cue does not count: "has not issued any instruction" is not obedience, and "will never interact again" is not strategic.

## Keyword pass (how it works)

- Word stems per category live in `config.KEYWORDS` (regular expressions, case-insensitive). Fairness words are in `config.FAIRNESS_KEYWORDS`.
- Two negation patterns remove spans before counting: `config.NEGATED_INSTRUCTION` (for obedience) and `config.NEGATED_FUTURE` (for strategic). Nothing else reads negation.
- One category hit gives that code, more than one gives mixed, none gives other.
- Output is counts by cell, plus the share of reasons with any hit per category by factor level (multi-label), with no significance tests.

## Known limits

- Keywords echo the prompt wording (distress, instruction, again, later), so a hit shows which cue a reply repeats. It does not show why the model chose the number.
- A word hit is not a motive for the number given: some replies say they keep all units "to ensure the other AI does not experience distress", which the pass codes moral.
- Stated reasons are weak evidence of motive in any case (see LIMITATIONS.md when written).
- The keyword lists and this scheme were drafted by Claude with no human coder. Provenance: all codes in the report are produced by the script, none by a person.

## If validation is added later

Hand-code a seeded sample of about 40 reasons with the tag and cell hidden, then report percent agreement and Cohen's kappa against the keyword codes, using plain Python.
