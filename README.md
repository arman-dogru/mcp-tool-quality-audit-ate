# MCP tool-description quality audit on Cohere Labs ATE

A CPU-only audit of **694,411 MCP tool descriptions** (from 70,927 servers; ATE's `in_analysis_set`) in the public [Cohere Labs ATE dataset](https://huggingface.co/datasets/CohereLabs/ATE). It measures how often descriptions are empty, terse, a restatement of the tool name, or silent about destructive behaviour, and asks whether those flags go with ATE's LLM-judge task-match labels **once description length is held fixed**.

> Independent analysis. It is not affiliated with or endorsed by Cohere Labs, and it reports only numbers computed here. The source announcement is [Cohere: automations' early footprint](https://cohere.com/blog/automations-early-footprint).

## Headline (the Results tables are generated from `results/*.json` by `src/report.py`; numbers quoted here come from them)
1. **Description length, not the "underspecified" flag, carries the signal.** Raw, underspecified tools get a "good" judge label 0.96 pp less often (2.6% base rate), almost exactly what length alone predicts (−0.99 pp). Holding exact word count fixed, the gap flips to **+0.38 pp [+0.05, +0.73]**. All tools under 6 words are flagged by definition, so this estimate comes only from the ~12.8k flagged tools with 6+ words (effectively the `underspecified_content` contrast). It and drops to +0.17 pp [−0.10, +0.52] once duplicate descriptions are removed. The flags add nothing reliable beyond length.
2. **The judge outcome is partly circular.** ATE's judge reads the same name and description that the flags score, and for empty descriptions its notes often say so. So `match_quality` here means *"could an LLM judge confirm a task match from the name and description"*, not tool usefulness.
3. **Prevalence is overstated by the rule.** The rule flags 49% of tools as underspecified; on a fresh sample of 100 tools LLM-labelled by the agent that wrote the rules (not shown rule outputs or judge labels), the labelled rate is 35% [26, 45], and the rule's accuracy equals the majority-class baseline (rule-vs-LLM-annotator κ 0.31, not inter-annotator agreement). A human second-annotator check is pending.
4. **Destructive tools rarely say they are destructive.** On a sample of 60 rule-flagged tools LLM-labelled by the agent that wrote the rules, 87% [74, 94] of those it judged truly destructive carry no safety cue in their prose (an LLM-annotator estimate; human check pending). That is a claim about prose descriptions only: MCP puts behaviour hints such as `destructiveHint` in tool `annotations`, which ATE does not carry.

## Motivation
An agent only sees a tool through its name, description and schema. If the description is empty, a restatement of the name, or vague, the model has to guess what the tool does and which arguments it takes. Destructive tools whose descriptions don't say so are a separate design risk. ATE includes LLM-judge labels (`match_quality`: good/partial/bad) for whether each tool performs its best-matched O\*NET task. This project checks how far those labels relate to description quality, and is explicit about what they can and cannot show.

## Approach
- **Data:** ATE `tools` (name, description; filtered to `in_analysis_set == 1`, which removes 1,876 duplicate tool_id rows and 4 others), `onet_matches` (one judge label per tool, rank 1), `servers` (GitHub stars). Pinned to dataset revision `4b567ba9` with sha256 checks; downloaded to the git-ignored `data/raw/`. Verbatim descriptions are not redistributed.
- **Heuristics (`src/metrics.py`, rules v2):** deterministic regex and lexicon rules.
  - `is_empty`, `too_short` (< 6 words; Unicode-aware word count; Han/kana/Thai counted as characters / 2), `name_echo` (description only restates the name), `vague`, `overclaim` (pruned to promotional terms in v2), `no_io_spec` (no mention of inputs or outputs), `non_latin_script` (>50% non-Latin letters; a script measure, not language ID).
  - `underspecified_content` = name_echo OR (vague AND no_io_spec): the part of the composite that is not a length threshold. **`underspecified`** = is_empty OR too_short OR underspecified_content.
  - `destructive` (delete/remove/drop/overwrite/kill/send/email/publish/transfer/pay/deploy… with inflections, in the description or the name), `mutating` (create/update/write/run/execute… and not destructive), `safety_cue` (irreversible, permanent, cannot be undone, confirmation, dry-run, warning…, in the name or description).
- **Primary analysis:** for each flag, the difference in good and bad rates between flagged and unflagged tools **within exact word-count strata** (0..40+), combined with Mantel-Haenszel weights. 95% CIs from a **cluster bootstrap over servers** (multinomial server weights, B=500, seed 0). Raw differences are shown for comparison.
- **Sensitivity:** (a) exact (name, description) duplicates removed; (b) tools whose judge notes say the description is missing or thin removed.
- **Description-independent outcome:** server GitHub stars (≥10), stratified by the server's median description length. This is popularity, not usefulness, but it does not come from reading the description.
- **Validation (`src/sample_blind.py`, `src/validate.py`, `data/hand_labels_v2.json`):** rules v2 were committed (d1e14ad) **before** two fresh samples were drawn (`src/sample_blind.py` redraws them exactly), disjoint from the v1 sample: a random 100 tools (underspecified, destructive) and 60 rule-flagged destructive tools (truly destructive?, safety cue?). Labels are keyed by `tool_id` and checked against a hash of name+description. **The labels are LLM labels, not human labels:** the single annotator is the Developer agent, which also wrote the rules. It was not shown rule outputs, judge labels or judge notes, but it knows the rules (6-word threshold, lexicons), and all 60 destructive-sample items were rule-flagged by construction, so "blind" is weak. The file name `hand_labels_v2.json` is historical. κ values are rule-vs-LLM-annotator agreement, not inter-annotator agreement. A human second annotation (30-50 items, blind to LLM labels and rule outputs) is pending.
- **History note:** in v1, the CJK word-count rule was changed *after* the first 40 tools were labelled, using one of those labelled items. The v1 README claimed the rule was fixed before labelling; that was wrong. Those 40 labels are kept only as a dev set (`data/hand_labels_v1_dev.json`) and are not used as a held-out estimate.

## Results
<!-- RESULTS:START (generated by src/report.py; do not edit by hand) -->
### Primary result: description flags vs ATE judge labels, holding description length fixed
Each row compares flagged and unflagged tools **of the same exact word count** (strata 0..40+ words, Mantel-Haenszel risk difference over strata with ≥20 tools in each arm). 95% CIs: cluster bootstrap over servers, B=500. `n_words` alone defines `is_empty` and `too_short`, so they have no within-length estimate.

| Flag | n flagged | Δgood raw | **Δgood, length held fixed** [95% CI] | Δbad raw | **Δbad, length held fixed** [95% CI] |
|---|---|---|---|---|---|
| underspecified | 340,956 | -0.96 pp | **+0.38 pp** [+0.05, +0.73] | +1.68 pp | **+0.98 pp** [+0.35, +1.67] |
| underspecified_content | 85,327 | -0.26 pp | **+0.23 pp** [+0.11, +0.35] | +1.27 pp | **+0.49 pp** [+0.12, +0.83] |
| name_echo | 71,808 | -0.49 pp | **+0.16 pp** [+0.05, +0.28] | +1.43 pp | **+0.38 pp** [-0.03, +0.75] |
| vague | 17,415 | +0.98 pp | **+0.20 pp** [-0.10, +0.49] | -0.13 pp | **+0.61 pp** [-0.06, +1.38] |
| overclaim | 2,583 | +2.25 pp | **+0.94 pp** [+0.14, +1.76] | -0.44 pp | **+0.50 pp** [-0.80, +1.84] |
| no_io_spec | 558,725 | -0.15 pp | **+0.67 pp** [+0.53, +0.81] | +1.56 pp | **+2.14 pp** [+1.87, +2.42] |
| destructive | 53,334 | -0.48 pp | **-0.51 pp** [-0.65, -0.37] | +7.33 pp | **+7.29 pp** [+6.86, +7.71] |
| mutating | 115,803 | +2.41 pp | **+2.32 pp** [+2.19, +2.44] | -1.49 pp | **-1.43 pp** [-1.68, -1.20] |
| destructive_no_safety_cue | 50,734 | -0.45 pp | **-0.47 pp** [-0.62, -0.33] | +7.03 pp | **+6.98 pp** [+6.54, +7.42] |
| non_latin_script | 33,249 | +0.26 pp | **+0.33 pp** [+0.08, +0.63] | -1.56 pp | **-1.83 pp** [-2.35, -1.27] |
| too_short | 279,158 | -0.95 pp | **n/a** | +1.50 pp | **n/a** |
| is_empty | 48,980 | -0.45 pp | **n/a** | +0.89 pp | **n/a** |

Length alone predicts a raw gap of -0.99 pp in good and +1.61 pp in bad for `underspecified`; the observed raw gaps are -0.96 pp and +1.68 pp. Within-length estimates use only strata where both arms exist: for `underspecified` that is 12,784 of 340,956 flagged tools (all 6+ words, since every tool under 6 words is flagged). 96.2% of underspecified tools are empty or under 6 words.

**Sensitivity checks** (length held fixed, B=100):

| Subset | n | underspecified Δgood | underspecified_content Δgood | name_echo Δgood |
|---|---|---|---|---|
| exact (name, description) duplicates removed | 606,636 | +0.17 pp [-0.10, +0.52] | +0.00 pp [-0.12, +0.15] | -0.09 pp [-0.24, +0.05] |
| judge notes do not mention a missing/thin description | 689,236 | +0.39 pp [+0.08, +0.68] | +0.23 pp [+0.12, +0.36] | +0.16 pp [+0.05, +0.28] |

### How much does the judge read the description? (circularity check)
Share of ATE judge notes that say the description is missing/thin or that the judge is inferring from the name: 9.3% for empty descriptions, 0.1% for too_short, 1.5% for underspecified, 0.1% for the rest. When the notes say so, the good rate is 0.66% vs 2.62% otherwise.

### Description-independent outcome: server popularity
Unit = server (69,473 servers with a star count). Outcome = P(stars >= 10). Length held fixed by stratifying on the server's median description length (capped at 20). Stars measure popularity, not usefulness.

| Server group | n | P(≥10 stars) flagged vs not | Δ raw [95% CI] | Δ length held fixed [95% CI] |
|---|---|---|---|---|
| >50% of tools underspecified | 23,230 | 14.8% vs 16.2% | -1.41 pp [-1.91, -0.86] | +4.53 pp [+2.51, +6.62] |
| any name_echo / vague-and-no-IO tool | 21,669 | 17.9% vs 14.8% | +3.03 pp [+2.45, +3.62] | +4.65 pp [+3.99, +5.29] |

### Prevalence (analysis set)
694,411 tools from 70,927 servers (ATE `in_analysis_set == 1`); median description 6 words; 694,406 have a judge label (partial 85.2%, bad 12.2%, good 2.6%).

| Flag | Rule flags | LLM-annotator estimate (random n=100) |
|---|---|---|
| underspecified | 49.1% | 35.0% [26.4, 44.7] |
| is_empty | 7.0% |  |
| too_short | 40.2% |  |
| name_echo | 10.3% |  |
| no_io_spec | 80.5% |  |
| vague | 2.5% |  |
| overclaim | 0.4% |  |
| destructive | 7.7% | 3.0% [1.0, 8.5] |
| mutating | 16.7% |  |
| destructive_no_safety_cue | 7.3% |  |
| non_latin_script | 4.8% |  |

### Safety cues on destructive tools
Rule (corpus, cluster-bootstrap CI): 95.1% [94.9, 95.4] of 53,334 destructive-flagged tools carry no safety cue; 94.5% when the destructive verb is in the description, 98.4% when it is only in the name, and 91.8% [90.8, 92.7] among descriptions of 15+ words.
LLM-annotator check (n=60 sample of rule-flagged tools, labelled by the agent that wrote the rules; human check pending): 46 judged truly destructive (precision 76.7% [64.6, 85.6]); of those, **40/46 = 87.0% [74.3, 93.9] carry no safety cue**.

### Heuristic validation (rules frozen before sampling; labels by an LLM annotator that wrote the rules, not shown rule outputs or judge labels)
| Check | n | Accuracy (majority baseline) | Precision [95% CI] | Recall [95% CI] | Cohen's κ (rule vs LLM annotator) |
|---|---|---|---|---|---|
| underspecified, random sample | 100 | 0.65 (0.65) | 0.50 [0.37, 0.63] | 0.74 [0.58, 0.86] | 0.31 |
| destructive, random sample | 100 | 0.95 (0.97) | 0.33 [0.1, 0.7] | 0.67 [0.21, 0.94] | 0.42 |
| safety_cue, truly destructive tools | 46 | 0.87 (0.87) | 0.50 [0.15, 0.85] | 0.33 [0.1, 0.7] | 0.33 |
| underspecified, v1 dev set (not held out) | 40 | 0.72 (0.60) | 0.60 [0.41, 0.77] | 0.94 [0.72, 0.99] | 0.48 |

Ablation: 6,010 destructive flags (11.3%) are triggered only by "email" forms, mostly the noun (`list_emails`, `get_email`). Without them the rule's no-cue rate is 94.7% (email-only: 98.9%). The lexicon is unchanged so the tables stay comparable; the LLM-annotator 87% is unaffected because its sample was labelled per tool.

### Underspecification by server popularity (tool-weighted, cluster-bootstrap CI)
| GitHub stars | Servers | Tools | Median words | underspecified [95% CI] | underspecified_content [95% CI] |
|---|---|---|---|---|---|
| stars unknown | 1,454 | 15,546 | 6 | 51.6% [48.5, 54.8] | 10.8% [9.4, 12.2] |
| 0-9 | 58,518 | 547,568 | 6 | 49.8% [49.3, 50.2] | 12.4% [12.1, 12.7] |
| 10-99 | 8,836 | 104,741 | 6 | 47.3% [46.0, 48.5] | 12.2% [11.3, 12.9] |
| 100-999 | 1,764 | 22,518 | 6 | 42.0% [39.5, 45.0] | 11.5% [10.2, 13.0] |
| 1000+ | 355 | 4,038 | 7 | 37.9% [32.8, 43.9] | 11.5% [9.0, 14.4] |
<!-- RESULTS:END -->

## Interpretation
1. **Length, not the composite flag, drives the raw association.** Inside exact-length strata the underspecified gap in "good" is small and positive, and it vanishes when duplicate descriptions are removed. `name_echo` and `underspecified_content` behave the same way. The honest summary: *shorter descriptions get fewer "good" labels from ATE's judge; the underspecification flags don't add anything reliable beyond length.*
2. **What the outcome can and can't say.** The judge sees the same text as the flags. With empty descriptions, its notes cite the missing description about 9% of the time, and those tools are almost never rated good. Removing those tools doesn't change the length-controlled result, but the circularity can't be removed from inside ATE, since there is no name-only or execution-based label. These results are about judge confirmability, not usefulness.
3. **Popularity doesn't rescue the flag either.** Once median description length is held fixed, servers whose tools are mostly underspecified are slightly *more* likely to have ≥10 stars, not less. Server size (more tools → more stars, more chances to be flagged) is a likely confounder that isn't controlled here, so read this as "no evidence of a popularity penalty", not as a positive effect.
4. **Destructive tools and safety cues.** The rule says 95% of destructive-flagged tools have no cue, and 92% even among descriptions of 15+ words. The LLM-annotator check (23% of rule hits are not truly destructive; the rule misses some cues such as "moves to trash" and fires on "Send a warning") gives 87% [74, 94]. Expecting "irreversible" wording in a median 6-word description is a high bar, and MCP intends this information to live in `annotations` (`destructiveHint`, `readOnlyHint`) and in client-side confirmation, neither of which ATE records. So the finding is narrower than v1 claimed: **the prose rarely warns**, not "the tools are unsafe".
5. **Popularity gradient is a length gradient.** The composite falls from 50% (0–9 stars) to 38% (1000+ stars), but `underspecified_content`, the part that isn't a length threshold, is flat at 11–12% across tiers.
6. **Other flags.** Destructive tools are rated "bad" about 7 pp more often at any length, and mutating tools are rated "good" about 2 pp more often. That says more about which O\*NET tasks such tools get matched to than about description quality. `overclaim` (now only 0.4% of tools) and `vague` don't behave like risk markers.

## Error analysis (LLM-labelled validation samples)
- **Underspecified false positives** are terse but clear tools: "Get user details" (`get_user`), "Merge a pull request", "Tangent" (`tan`), "Move the robot backward". A 6-word threshold is a recall-oriented screen, not a judgement.
- **Underspecified false negatives** are long but uninformative: server-level marketing blurbs pasted into every tool ("Power your business with #AI…"), or descriptions of a sibling tool.
- **Destructive false positives** come from names or descriptions that mention a destructive verb without doing it: `bulk_transfer_show`, `get_drop_rule`, `wallet_sign_transaction` ("…without sending it"), `list_allowed_directories` (a server blurb listing `write_file`).
- **Safety-cue errors:** the rule misses recoverability cues ("Move emails to trash", "with backup", "using track changes", "safety checks") and fires on non-cues ("Send a **warning** notification", "Deploy … get a **preview** URL").

## Reproduce
Prerequisites: `uv`, `curl`, `sha256sum` (coreutils), bash.
```bash
./reproduce.sh   # pinned deps + dataset revision, sha256 check, tests, validate, analyze (B=500), regenerate README results
```
CPU-only. `src/sample_blind.py` redraws the validation samples (not needed to reproduce the numbers). `analyze.py` takes ~3 CPU-minutes and ~2.1 GB peak RSS (measured with `/usr/bin/time -v`). Python 3.13, versions pinned in `requirements.txt`. `results/tool_flags.parquet` (per-tool flags, ids only) is regenerated locally and is not committed (the v1 19.8 MB copy remains in history at 614c85e; history is not rewritten).

## Limitations
- **Circular outcome:** see Interpretation 2. There is no description-independent usefulness label in ATE.
- The heuristics are lexical. On the LLM-labelled sample, `underspecified` has precision 0.50 [0.37, 0.63] and rule-vs-LLM-annotator κ 0.31.
- **One annotator, and it is an LLM-based agent that also wrote the rules** (the Developer bot that wrote this repo). It was not shown rule outputs or judge labels, but it knows the rules. No human labels and no inter-annotator agreement yet; a human second-annotator check is pending.
- ATE's `tools` table has no input schemas and no MCP `annotations`, so `no_io_spec` and the safety-cue analysis only cover prose.
- `non_latin_script` measures script, not language: French or Portuguese descriptions count as Latin.
- Associations are not causal. Server size is not controlled in the popularity analysis.

## Data and attribution
- Code: MIT (`LICENSE`). The license does not cover the data.
- ATE dataset: CohereLabs/ATE on the Hugging Face Hub, revision `4b567ba98acc6ddf27b2abb9004844581083c5d8`. Its Hub card says the dataset license has not been set yet, so this repo stores only tool_ids, text hashes, labels and aggregate numbers. No descriptions are committed. Note that ATE `tool_id`s embed the tool name (`<hash>:<tool_name>`), so names are recoverable from the ids.
- O\*NET: task statements come from the O\*NET 29.2 Database by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), used under the CC BY 4.0 license. O\*NET® is a trademark of USDOL/ETA.
- Suggested ATE citation (from the dataset card):
```bibtex
@online{agentictaskecosys2026,
  author = {Zanele Munyikwa, Campbell Lund, Thomas Euyang, Aidan Peppin, and Marzieh Fadaee},
  title = {Automation's Early Footprint: Where AI Agents Are (and Aren't) Being Built},
  year = 2026,
  url = {https://cohere.com/blog/automations-early-footprint}
}
```

## Next steps
- **Pending:** a human second annotation of 30-50 items (e.g. 25 from the random 100 and 20 from the 46 destructive), blind to the LLM labels and rule outputs, reporting human-vs-LLM κ and human-vs-rule agreement.
- A description-independent outcome: re-run a judge on **name-only** inputs for a sample, or execute a sample of tools.
- Pull real input schemas and `annotations` from servers' GitHub repos for a sample, to measure schema completeness and `destructiveHint` use directly.
- Control for server size (tool count) in the popularity analysis.
