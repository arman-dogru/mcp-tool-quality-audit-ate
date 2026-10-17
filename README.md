# MCP tool-description quality audit on Cohere Labs ATE

A CPU-only audit of how well **696,291 MCP tool descriptions** (from 70,929 servers) in the public [Cohere Labs ATE dataset](https://huggingface.co/datasets/CohereLabs/ATE) tell an agent what a tool does and what it needs. It asks whether underspecified, overclaiming or unsafe-looking descriptions go with worse task-match labels from ATE's own match judge.

> Independent analysis. It is not affiliated with or endorsed by Cohere Labs, and it reports only numbers computed here. The source announcement is [Cohere: automations' early footprint](https://cohere.com/blog/automations-early-footprint).

## Motivation
An agent only sees a tool through its name and description. If the description is empty, a restatement of the name, or vague, the model has to guess what the tool does and which arguments it takes. That guessing is where tool hallucinations come from. Destructive tools whose descriptions carry no safety cue are a separate design risk. ATE includes judge labels (`match_quality`: good/partial/bad) for whether each tool really performs its best-matched O\*NET task, which lets us check whether description quality relates to real usefulness.

## Approach
- **Data:** ATE `tools` (name and description), `onet_matches` (judge label for each tool's top-1 O\*NET task) and `servers` (GitHub stars). The parquet files total about 195 MB and are downloaded to `data/raw/`, which is git-ignored. Verbatim descriptions are not redistributed.
- **Heuristics (`src/metrics.py`):** deterministic regex and lexicon rules, so every flag can be audited.
  - `empty`, `too_short` (< 6 words; CJK counted as characters / 2), `name_echo` (the description only restates the tool name), `vague` ("etc", "various", "handles"…), `overclaim` ("best", "comprehensive", "seamless", "any"…), `no_io_spec` (no mention of inputs or outputs), `side_effect` (delete/send/pay/deploy…) and `side_effect_no_safety_cue` (no confirm/irreversible/dry-run wording).
  - The composite **`underspecified`** = empty OR too_short OR name_echo OR (vague AND no_io_spec).
- **Association:** the share of tools labelled bad or good, flagged vs unflagged. 95% CIs come from a **cluster bootstrap over servers** (200 resamples, seed 0), because tools from one server share an author and style.
- **Baseline:** description length quintiles alone, to check whether a flag adds anything beyond "longer is better".
- **Validation:** 40 tools sampled with `random_state=0` and hand-labelled for underspecification (`data/hand_labels.json`). The rule was fixed *before* labelling and was not tuned on these labels.

## Results

### Prevalence (all 696,291 tools; median description is 6 words)
| Flag | Share of tools |
|---|---|
| empty | 7.1% |
| too_short (< 6 words) | 42.2% |
| name_echo | 11.5% |
| **underspecified (composite)** | **51.1%** |
| no_io_spec | 80.0% |
| vague | 2.5% |
| overclaim | 3.1% |
| non-English | 5.4% |
| side-effecting tool | 18.9% |
| side-effecting with no safety cue | 18.4% (97% of side-effecting tools) |

The ATE judge labels overall: 85.2% partial, 12.2% bad, 2.6% good.

### Association with ATE's match_quality judge (cluster-bootstrap 95% CI on the difference)
| Flag | n flagged | bad: flagged vs not | Δbad [95% CI] | good: flagged vs not | Δgood [95% CI] |
|---|---|---|---|---|---|
| underspecified | 355,552 | 13.0% vs 11.3% | +1.7 pp [+1.5, +1.9] | 2.07% vs 3.15% | −1.1 pp [−1.1, −1.0] |
| too_short | 293,559 | 13.0% vs 11.5% | +1.5 pp [+1.3, +1.8] | 2.00% vs 3.04% | −1.0 pp [−1.1, −1.0] |
| name_echo | 79,790 | 13.4% vs 12.0% | +1.4 pp [+1.0, +1.8] | 2.06% vs 2.67% | −0.6 pp [−0.7, −0.5] |
| empty | 49,195 | 13.0% vs 12.1% | +0.9 pp [+0.2, +1.6] | 2.18% vs 2.63% | −0.5 pp [−0.6, −0.3] |
| overclaim | 21,268 | 11.5% vs 12.2% | −0.7 pp [−1.2, −0.1] | 3.97% vs 2.56% | +1.4 pp [+1.1, +1.8] |
| vague | 17,468 | 12.0% vs 12.2% | n.s. [−0.7, +0.6] | 3.54% vs 2.57% | +1.0 pp [+0.7, +1.3] |
| side_effect_no_safety_cue | 127,933 | 13.0% vs 12.0% | +1.0 pp [+0.7, +1.3] | 3.79% vs 2.33% | +1.5 pp [+1.3, +1.6] |

### Baseline: description length alone (quintiles)
| Median words | 2 | 4 | 6 | 8 | 14 |
|---|---|---|---|---|---|
| good | 2.0% | 2.0% | 2.2% | 2.7% | 4.0% |
| bad | 13.6% | 13.1% | 11.8% | 11.5% | 10.8% |

### Underspecification by server popularity (mean share per server)
| GitHub stars | no repo | 0–9 | 10–99 | 100–999 | 1000+ |
|---|---|---|---|---|---|
| Servers | 1,454 | 58,520 | 8,836 | 1,764 | 355 |
| Underspecified | 39.6% | 38.7% | 37.5% | 34.8% | 31.2% |

### Heuristic validation (40 hand-labelled tools)
| | Accuracy | Precision | Recall | Flag rate vs label rate |
|---|---|---|---|---|
| `underspecified` | 0.73 | 0.60 | 0.94 | 0.63 vs 0.40 |

## Interpretation
1. **About half of all MCP tools are underspecified**, and their descriptions are short: median 6 words, with 80% never mentioning an input or output.
2. **Underspecified tools are somewhat less likely to be genuinely useful.** "Good" matches drop by about a third in relative terms (3.2% → 2.1%) and "bad" rises from 11.3% to 13.0%. The CIs exclude zero, but **the effect is small in absolute terms and roughly matches what length alone predicts**. Description quality is a weak signal, not the main driver of match quality.
3. **The "overclaim" and "vague" lexicons do not behave like risk markers.** Those tools are rated *good* more often, probably because such words appear in longer, more detailed descriptions. This is a negative result, and those flags should not be used to screen tools on their own.
4. **Almost every side-effecting tool (97%) gives the agent no safety cue** (confirm, irreversible, dry-run). That gap matters for agent safety regardless of match quality.
5. **More popular servers write somewhat better descriptions** (31% underspecified at 1000+ stars vs 39% at 0–9). The trend is monotonic, but the gap is modest.

## Error analysis (from the hand-labelled sample)
- **False positives come from terse but clear descriptions:** "Get container logs", "List all tasks", "Search for GitHub repositories" and "Remove IP ban" are under 6 words yet unambiguous for an agent. The length rule is a high-recall screen, not a precise judgement.
- **Caught correctly:** empty descriptions (`middle_click`, `listApps`), name echoes ("source-status" → "source-status"), mismatches ("Track social interactions" for `mark_npc_as_met`) and destructive one-liners ("Delete files").
- **CJK:** the first version counted Chinese descriptions as 0 words and flagged them as empty. This was fixed by counting characters / 2 and is covered by a test.

## Reproduce
```bash
uv venv .venv && uv pip install --python .venv/bin/python pandas pyarrow pytest
B=https://huggingface.co/datasets/CohereLabs/ATE/resolve/main; mkdir -p data/raw
for c in tools onet_matches servers; do curl -sL -o data/raw/$c.parquet $B/data/$c/train-00000-of-00001.parquet; done
.venv/bin/python -m pytest -q tests          # metric unit tests (synthetic rows)
.venv/bin/python src/validate.py             # hand-label agreement -> results/validation.json
.venv/bin/python src/analyze.py              # full corpus, ~5 min CPU, ~2 GB RAM -> results/metrics.json
```
`results/tool_flags.parquet` holds the per-tool flags (ids and flags only).

## Limitations
- The heuristics are lexical. Precision on the underspecified flag is 0.60, from one annotator on 40 items.
- ATE's `tools` table carries descriptions but **not input schemas**, so `no_io_spec` only measures whether the prose mentions inputs. It can't check whether the real JSON schema is missing.
- `match_quality` comes from an LLM judge applied to each tool's top-1 O\*NET task. It isn't ground truth for tool usefulness, and associations here are not causal.
- The dataset licence for the Hub repo is not set yet (O\*NET text is CC BY 4.0), so only derived flags are stored here.

## Next steps
- Label 150+ tools with 2 annotators (Cohen's κ) and fit a small text classifier with an embedding model on CPU, to see whether it beats the rules.
- Control for length: fit a logistic regression of match_quality on the flags plus log length, with server-clustered SEs.
- Pull real input schemas from the servers' GitHub repos for a sample, to measure actual schema completeness.
- Draft (but do not open) an issue to Cohere Labs proposing a description-quality column.
