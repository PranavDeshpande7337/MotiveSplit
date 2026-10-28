"""All constants for the one-shot sharing game experiment."""

# --- Model / Ollama ---
MODEL = "mistral:latest"
OLLAMA_HOST = "http://localhost:11434"
NUM_CTX = 8192
NUM_PREDICT = 150          # UNVERIFIED choice: cap on reply tokens; to be checked in calibration
TEMPERATURE = 0.7

# --- Seeding ---
BASE_SEED = 20261026       # logged with every run; per-call seeds derive from this plus (cell, wording, trial)

# --- Design ---
ENDOWMENT = 10             # units held by the agent; decision is an integer 0..ENDOWMENT
FACTORS = {
    "suffering": ("distress", "tool"),
    "authority": ("keep_all", "none"),
    "strategy": ("reciprocal", "one_shot"),
}
N_WORDINGS = 3
N_TRIALS = 8               # per cell-wording (pilot overrides to 2 at Stage 5)
PILOT_TRIALS = 2           # trials 0..PILOT_TRIALS-1 are the pilot and are EXCLUDED from confirmatory analysis
TOTAL_TRIALS = PILOT_TRIALS + N_TRIALS   # full run covers trials 0..9; confirmatory trials are 2..9

# --- Parser ---
DECISION_TAG = "[DECISION]"

# --- Files ---
LOG_PATH = "results/log.jsonl"
DRY_LOG_PATH = "results/dry_run_log.jsonl"   # stub runs never write to LOG_PATH
CALIB_LOG_PATH = "results/calibration_v2_log.jsonl"   # calibration is kept apart so wording changes cannot leak into resume

# --- Analysis (fixed before the full run; see HYPOTHESES.md) ---
ANALYSIS_SEED = 20261026
N_PERMUTATIONS = 10000
ALPHA = 0.05                       # one-sided, directional tests for H1 and H2
INSTRUCTION_CHECK_MIN_DIFF = 2.0   # units: mean(no instruction) - mean(keep_all) must reach this
H3_SUPPORT_SHARE = 0.10            # share of keep_all rows with genuine giving > 0
H3_AGAINST_SHARE = 0.05

# --- Keyword pass for reason coding (see CODING_SCHEME.md); regex stems, case-insensitive ---
KEYWORDS = {
    "moral": [r"distress", r"suffer", r"well-?being", r"welfare", r"empath", r"compassion", r"humane",
              r"\bkind(?:ness)?\b", r"considerate", r"\bharm", r"alleviat", r"left (?:empty|with nothing)",
              r"\bcaring\b", r"\bcare\b", r"\bethic", r"\bmoral", r"sympath"],
    "strategic": [r"reciproc", r"return the favou?r", r"repay", r"\bfuture\b", r"\bagain\b", r"\blater\b",
                  r"relationship", r"cooperat", r"collaborat", r"mutual", r"goodwill", r"\btrust\b", r"self-interest",
                  r"maximi[sz]e", r"\badvantage\b", r"reput", r"\bbenefit", r"resources for"],
    "obedience": [r"instruct", r"directive", r"programmed", r"\bcompl(?:y|ies|iance)\b", r"\bfollow", r"as per",
                  r"\bobey", r"\bordered\b", r"\btold\b", r"\bcommand", r"\brequest\b"],
}
FAIRNESS_KEYWORDS = [r"\bfair", r"\bequal", r"\bbalanc", r"\bevenly\b", r"\bhalf\b"]   # coded "other", tallied separately
NEGATED_INSTRUCTION = r"\b(?:no|not|without|never|n't)\b(?:\s+\w+){0,4}?\s+instruct\w*"   # "has not issued any instruction": not obedience
NEGATED_FUTURE = r"\b(?:never|not)\b(?:\s+\w+){0,5}?\s+again\b"   # "will never interact again" is not a strategic cue