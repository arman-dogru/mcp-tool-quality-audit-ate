"""Render the README figures from the committed results files (no data download, no recomputation).

Inputs : results/metrics.json, results/validation.json
Outputs: docs/figures/*.png
Usage  : .venv/bin/python scripts/make_figures.py   (matplotlib is pinned in requirements.txt)
Every plotted number is read from the JSON files; nothing is hand-typed.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures"
M = json.loads((ROOT / "results" / "metrics.json").read_text())
V = json.loads((ROOT / "results" / "validation.json").read_text())

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False, "svg.hashsalt": "0",
})
RAW, ADJ, ACC = "#9aa5b1", "#1f6feb", "#d1495b"


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=110, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)
    print("wrote", (OUT / name).relative_to(ROOT))


def pp(x):
    return 100.0 * x


def fig_length_controlled():
    """Raw vs length-held-fixed difference in P(judge = good) per flag, with 95% cluster-bootstrap CIs."""
    A = M["association"]
    flags = [f for f in ["underspecified", "underspecified_content", "name_echo", "vague", "overclaim",
                         "no_io_spec", "destructive", "destructive_no_safety_cue", "mutating", "non_latin_script"]
             if A[f]["good_diff_len"] is not None]
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    for i, f in enumerate(flags):
        a = A[f]
        for dy, key, col, lab in [(-0.17, "good_diff_raw", RAW, "raw (no length control)"),
                                  (0.17, "good_diff_len", ADJ, "same exact word count (Mantel-Haenszel)")]:
            lo, hi = a[key + "_ci95"]
            ax.errorbar(pp(a[key]), i + dy, xerr=[[pp(a[key] - lo)], [pp(hi - a[key])]], fmt="o", color=col,
                        ms=5, capsize=2.5, lw=1.4, label=lab if i == 0 else None)
    ax.axvline(0, color="#444", lw=0.8)
    ax.set_yticks(range(len(flags)))
    ax.set_yticklabels([f"{f}  (n={A[f]['n_flagged']:,})" for f in flags])
    ax.invert_yaxis()
    ax.set_xlabel("Δ P(judge label = good), flagged − unflagged  [pp, 95% CI]")
    ax.set_title("Holding description length fixed flips the 'underspecified' gap")
    ax.legend(loc="lower right", frameon=False, fontsize=8.5)
    ax.text(0, -0.2, f"Base rate of 'good' = {pp(M['match_quality_dist']['good']):.1f}%. CIs: cluster bootstrap over servers, "
            f"B={M['bootstrap_B']}. Source: results/metrics.json", transform=ax.transAxes, fontsize=7.5, color="#555")
    save(fig, "length_controlled_effects.png")


def fig_prevalence():
    """Rule prevalence vs LLM-annotator estimate on a random n=100 sample."""
    P = M["prevalence"]
    flags = ["no_io_spec", "underspecified", "too_short", "mutating", "underspecified_content", "name_echo",
             "destructive", "destructive_no_safety_cue", "is_empty", "non_latin_script", "vague", "overclaim"]
    llm = {"underspecified": V["underspecified_random_n100"], "destructive": V["destructive_random_n100"]}
    n_tools_k = f"{M['n_tools'] // 1000}k"
    rule_us = f"{pp(P['underspecified']):.0f}"
    llm_us = f"{pp(llm['underspecified']['label_rate']):.0f}"
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    y = range(len(flags))
    ax.barh(list(y), [pp(P[f]) for f in flags], color=ADJ, height=0.6, label=f"rule flags (all {n_tools_k} tools)")
    for i, f in enumerate(flags):
        right = max(pp(P[f]), pp(llm[f]["label_rate_ci95"][1]) if f in llm else 0)
        ax.text(right + 0.8, i, f"{pp(P[f]):.1f}%", va="center", fontsize=8)
        if f in llm:
            v = llm[f]; lo, hi = v["label_rate_ci95"]
            ax.errorbar(pp(v["label_rate"]), i, xerr=[[pp(v["label_rate"] - lo)], [pp(hi - v["label_rate"])]],
                        fmt="D", color=ACC, ms=6, capsize=3, lw=1.6,
                        label="LLM-annotator estimate, random n=100 (95% CI)" if f == "underspecified" else None)
    ax.set_yticks(list(y)); ax.set_yticklabels(flags); ax.invert_yaxis()
    ax.set_xlabel("share of tools flagged [%]"); ax.set_xlim(0, 92)
    ax.set_title(f"Prevalence: the rule over-flags 'underspecified' ({rule_us}% vs {llm_us}%)")
    ax.legend(loc="lower right", frameon=False, fontsize=8.5)
    ax.text(0, -0.2, "LLM labels come from the agent that wrote the rules (not human labels). "
            "Source: results/metrics.json, results/validation.json", transform=ax.transAxes, fontsize=7.5, color="#555")
    save(fig, "prevalence_rule_vs_llm.png")


def fig_stars():
    """Underspecified share by server popularity tier: composite vs the non-length part."""
    rows = [r for r in M["underspecified_by_server_stars"] if r["bin"] != "stars unknown"]
    x = range(len(rows))
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for key, col, lab in [("underspecified", ADJ, "underspecified (includes < 6 words)"),
                          ("underspecified_content", ACC, "underspecified_content (name echo / vague + no I/O)")]:
        v = [pp(r[key]) for r in rows]
        lo = [pp(r[key] - r[key + "_ci95"][0]) for r in rows]
        hi = [pp(r[key + "_ci95"][1] - r[key]) for r in rows]
        ax.errorbar(list(x), v, yerr=[lo, hi], marker="o", color=col, capsize=3, lw=1.8, label=lab)
    ax.set_xticks(list(x)); ax.set_xticklabels([f"{r['bin']} stars\n{r['servers']:,} servers" for r in rows], fontsize=8.5)
    ax.set_ylabel("share of tools [%] (95% CI)"); ax.set_ylim(0, 60)
    ax.set_title("The popularity gradient is a length gradient")
    ax.legend(frameon=False, fontsize=8.5, loc="center right")
    ax.text(0, -0.28, "Tool-weighted, cluster-bootstrap CIs over servers. Source: results/metrics.json",
            transform=ax.transAxes, fontsize=7.5, color="#555")
    save(fig, "underspecified_by_stars.png")


def fig_safety():
    """Share of destructive tools with no safety cue: rule on the corpus vs LLM-annotator check."""
    S = M["destructive_safety_cue"]; h = V["hand_no_cue_among_truly_destructive"]
    rows = [("rule: all destructive-flagged", S["all_destructive"]),
            ("rule: verb in description", S["trigger_in_description"]),
            ("rule: verb only in name", S["trigger_in_name_only"]),
            ("rule: descriptions of 15+ words", S["description_15plus_words"])]
    labels = [f"{a}\n(n={r['n']:,})" for a, r in rows] + [f"LLM annotator: truly destructive\n(n={h['n']}, {h['k']}/{h['n']} no cue)"]
    vals = [pp(r["no_cue"]) for _, r in rows] + [pp(h["share"])]
    cis = [r["no_cue_ci95"] for _, r in rows] + [h["ci95"]]
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    y = list(range(len(vals)))
    ax.barh(y, vals, color=[ADJ] * 4 + [ACC], height=0.6,
            xerr=[[v - pp(c[0]) for v, c in zip(vals, cis)], [pp(c[1]) - v for v, c in zip(vals, cis)]], capsize=3)
    for i, v in enumerate(vals):
        ax.text(2, i, f"{v:.1f}%", va="center", color="white", fontsize=9, fontweight="bold")
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8.5); ax.invert_yaxis()
    ax.set_xlim(0, 100); ax.set_xlabel("destructive tools whose prose has no safety cue [%] (95% CI)")
    ax.set_title("Destructive tools rarely warn in their description")
    ax.text(0, -0.25, "Prose only: ATE has no MCP `annotations` (destructiveHint). Source: results/metrics.json, results/validation.json",
            transform=ax.transAxes, fontsize=7.5, color="#555")
    save(fig, "destructive_no_safety_cue.png")


if __name__ == "__main__":
    fig_length_controlled(); fig_prevalence(); fig_stars(); fig_safety()
