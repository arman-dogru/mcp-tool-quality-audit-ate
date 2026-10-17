"""Regenerate the results block of README.md (between the RESULTS markers) from results/metrics.json and results/validation.json."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def pp(x):
    return "n/a" if x is None else f"{x * 100:+.2f} pp"


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def cip(c):
    return "" if not c or c[0] is None else f" [{c[0] * 100:+.2f}, {c[1] * 100:+.2f}]"


def cipct(c, d=1):
    return f" [{c[0] * 100:.{d}f}, {c[1] * 100:.{d}f}]"


def build(M: dict, V: dict) -> str:
    A = M["association"]; L = []
    a = A["underspecified"]
    L += ["### Primary result: description flags vs ATE judge labels, holding description length fixed",
          f"Each row compares flagged and unflagged tools **of the same exact word count** (strata 0..{M['len_cap']}+ words, "
          f"Mantel-Haenszel risk difference over strata with ≥{M['min_arm']} tools in each arm). 95% CIs: cluster bootstrap over servers, "
          f"B={M['bootstrap_B']}. `n_words` alone defines `is_empty` and `too_short`, so they have no within-length estimate.", "",
          "| Flag | n flagged | Δgood raw | **Δgood, length held fixed** [95% CI] | Δbad raw | **Δbad, length held fixed** [95% CI] |",
          "|---|---|---|---|---|---|"]
    for f in ["underspecified", "underspecified_content", "name_echo", "vague", "overclaim", "no_io_spec", "destructive", "mutating",
              "destructive_no_safety_cue", "non_latin_script", "too_short", "is_empty"]:
        r = A[f]
        L.append(f"| {f} | {r['n_flagged']:,} | {pp(r['good_diff_raw'])} | **{pp(r['good_diff_len'])}**{cip(r['good_diff_len_ci95'])} "
                 f"| {pp(r['bad_diff_raw'])} | **{pp(r['bad_diff_len'])}**{cip(r['bad_diff_len_ci95'])} |")
    lo = M["length_only_prediction"]["underspecified"]
    L += ["", f"Length alone predicts a raw gap of {pp(lo['good'])} in good and {pp(lo['bad'])} in bad for `underspecified`; "
          f"the observed raw gaps are {pp(a['good_diff_raw'])} and {pp(a['bad_diff_raw'])}. "
          f"Within-length estimates use only strata where both arms exist: for `underspecified` that is {a['n_flagged_in_used_strata']:,} of {a['n_flagged']:,} flagged tools "
          "(all 6+ words, since every tool under 6 words is flagged). "
          f"{pct(M['underspecified_share_lt6_words'])} of underspecified tools are empty or under 6 words.", ""]
    sd, sn = M["sensitivity_dedup_name_desc"], M["sensitivity_notes_not_citing_description"]
    L += ["**Sensitivity checks** (length held fixed, B=100):", "",
          "| Subset | n | underspecified Δgood | underspecified_content Δgood | name_echo Δgood |", "|---|---|---|---|---|"]
    for name, s in (("exact (name, description) duplicates removed", sd), ("judge notes do not mention a missing/thin description", sn)):
        r = s["association"]
        L.append(f"| {name} | {s['n']:,} | {pp(r['underspecified']['good_diff_len'])}{cip(r['underspecified']['good_diff_len_ci95'])} "
                 f"| {pp(r['underspecified_content']['good_diff_len'])}{cip(r['underspecified_content']['good_diff_len_ci95'])} "
                 f"| {pp(r['name_echo']['good_diff_len'])}{cip(r['name_echo']['good_diff_len_ci95'])} |")
    J = M["judge_notes_cite_description"]
    L += ["", "### How much does the judge read the description? (circularity check)",
          f"Share of ATE judge notes that say the description is missing/thin or that the judge is inferring from the name: "
          f"{pct(J['is_empty'])} for empty descriptions, {pct(J['too_short'])} for too_short, {pct(J['underspecified'])} for underspecified, "
          f"{pct(J['not_underspecified'])} for the rest. When the notes say so, the good rate is {pct(J['good_rate_when_cited'], 2)} "
          f"vs {pct(J['good_rate_when_not_cited'], 2)} otherwise.", ""]
    S = M["server_adoption"]
    L += ["### Description-independent outcome: server popularity",
          f"Unit = server ({S['n_servers_with_stars']:,} servers with a star count). Outcome = {S['outcome']}. "
          "Length held fixed by stratifying on the server's median description length (capped at 20). Stars measure popularity, not usefulness.", "",
          "| Server group | n | P(≥10 stars) flagged vs not | Δ raw [95% CI] | Δ length held fixed [95% CI] |", "|---|---|---|---|---|"]
    for k, lab in (("majority_underspecified", ">50% of tools underspecified"), ("any_underspecified_content", "any name_echo / vague-and-no-IO tool")):
        r = S[k]
        L.append(f"| {lab} | {r['n_flagged']:,} | {pct(r['p_if_flag'])} vs {pct(r['p_if_not'])} | {pp(r['diff_raw'])}{cip(r['diff_raw_ci95'])} "
                 f"| {pp(r['diff_len'])}{cip(r['diff_len_ci95'])} |")
    L += ["", "### Prevalence (analysis set)", f"{M['n_tools']:,} tools from {M['n_servers']:,} servers (ATE `in_analysis_set == 1`); "
          f"median description {M['median_words']:.0f} words; {M['n_matched']:,} have a judge label "
          f"({', '.join(f'{k} {pct(v)}' for k, v in M['match_quality_dist'].items())}).", "",
          "| Flag | Rule flags | LLM-annotator estimate (random n=100) |", "|---|---|---|"]
    U = V["underspecified_random_n100"]; Dr = V["destructive_random_n100"]
    for f in ["underspecified", "is_empty", "too_short", "name_echo", "no_io_spec", "vague", "overclaim", "destructive", "mutating",
              "destructive_no_safety_cue", "non_latin_script"]:
        h = {"underspecified": f"{pct(U['label_rate'])}{cipct(U['label_rate_ci95'])}",
             "destructive": f"{pct(Dr['label_rate'])}{cipct(Dr['label_rate_ci95'])}"}.get(f, "")
        L.append(f"| {f} | {pct(M['prevalence'][f])} | {h} |")
    D = M["destructive_safety_cue"]; H = V["hand_no_cue_among_truly_destructive"]; P = V["destructive_flag_precision_n60"]
    L += ["", "### Safety cues on destructive tools",
          f"Rule (corpus, cluster-bootstrap CI): {pct(D['all_destructive']['no_cue'])}{cipct(D['all_destructive']['no_cue_ci95'])} of "
          f"{D['all_destructive']['n']:,} destructive-flagged tools carry no safety cue; {pct(D['trigger_in_description']['no_cue'])} when the "
          f"destructive verb is in the description, {pct(D['trigger_in_name_only']['no_cue'])} when it is only in the name, and "
          f"{pct(D['description_15plus_words']['no_cue'])}{cipct(D['description_15plus_words']['no_cue_ci95'])} among descriptions of 15+ words.",
          f"LLM-annotator check (n={P['n']} sample of rule-flagged tools, labelled by the agent that wrote the rules; human check pending): {P['k']} judged truly destructive (precision {pct(P['precision'])}{cipct(P['ci95'])}); "
          f"of those, **{H['k']}/{H['n']} = {pct(H['share'])}{cipct(H['ci95'])} carry no safety cue**.", "",
          "### Heuristic validation (rules frozen before sampling; labels by an LLM annotator that wrote the rules, not shown rule outputs or judge labels)",
          "| Check | n | Accuracy (majority baseline) | Precision [95% CI] | Recall [95% CI] | Cohen's κ (rule vs LLM annotator) |", "|---|---|---|---|---|---|"]
    for k, lab in (("underspecified_random_n100", "underspecified, random sample"), ("destructive_random_n100", "destructive, random sample"),
                   ("safety_cue_rule_vs_hand_on_truly_destructive", "safety_cue, truly destructive tools"),
                   ("v1_dev_set_underspecified_n40_NOT_HELD_OUT", "underspecified, v1 dev set (not held out)")):
        r = V[k]
        L.append(f"| {lab} | {r['n']} | {r['accuracy']:.2f} ({r['majority_class_accuracy']:.2f}) | {r['precision']:.2f} {[round(x, 2) for x in r['precision_ci95']]} "
                 f"| {r['recall']:.2f} {[round(x, 2) for x in r['recall_ci95']]} | {r['kappa']:.2f} |")
    E = D["email_only_ablation"]
    L += ["", f"Ablation: {E['n_email_only']:,} destructive flags ({pct(E['share_of_destructive'])}) are triggered only by \"email\" forms, mostly the noun "
          f"(`list_emails`, `get_email`). Without them the rule's no-cue rate is {pct(E['no_cue_without_email'])} (email-only: {pct(E['no_cue_email_only'])}). "
          "The lexicon is unchanged so the tables stay comparable; the LLM-annotator 87% is unaffected because its sample was labelled per tool."]
    L += ["", "### Underspecification by server popularity (tool-weighted, cluster-bootstrap CI)",
          "| GitHub stars | Servers | Tools | Median words | underspecified [95% CI] | underspecified_content [95% CI] |", "|---|---|---|---|---|---|"]
    for r in M["underspecified_by_server_stars"]:
        L.append(f"| {r['bin']} | {r['servers']:,} | {r['tools']:,} | {r['median_words']:.0f} | {pct(r['underspecified'])}{cipct(r['underspecified_ci95'])} "
                 f"| {pct(r['underspecified_content'])}{cipct(r['underspecified_content_ci95'])} |")
    return "\n".join(L)


def main():
    M = json.loads((ROOT / "results/metrics.json").read_text()); V = json.loads((ROOT / "results/validation.json").read_text())
    p = ROOT / "README.md"; s = p.read_text()
    block = "<!-- RESULTS:START (generated by src/report.py; do not edit by hand) -->\n" + build(M, V) + "\n<!-- RESULTS:END -->"
    s2 = re.sub(r"<!-- RESULTS:START.*?<!-- RESULTS:END -->", lambda _: block, s, flags=re.S)
    assert s2 != s or block in s, "RESULTS markers not found in README.md"
    p.write_text(s2)


if __name__ == "__main__":
    main()
