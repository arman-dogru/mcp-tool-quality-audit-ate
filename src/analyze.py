"""Score all ATE analysis-set tools, then relate description flags to the ATE judge's match_quality labels.

Primary result: length-controlled (exact word-count strata, Mantel-Haenszel risk difference).
Uncertainty: cluster bootstrap over servers (mcp_id), implemented as multinomial server weights."""
import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from metrics import FLAGS, LENGTH_DEFINED, RULES_VERSION, score

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RES = ROOT / "results"
SEED = 0
LEN_CAP = 40          # stratum = min(n_words, LEN_CAP)
MIN_ARM = 20          # a stratum contributes only if both arms have >= MIN_ARM tools
# Judge notes that say the description is missing/thin, or that infer behaviour from the name alone.
NOTES_CITE_DESC = re.compile(
    r"\b(?:no|missing|without(?: a)?|lacks?(?: a)?|lacking(?: a)?|absent|empty|vague|minimal|sparse|brief|unclear|generic|terse)"
    r" (tool )?description|description (is|was) (missing|empty|absent|vague|unclear|minimal|brief|generic)"
    r"|(tool )?name (alone|only)|only (the|its) (tool )?name|(based|inferred) (only |solely )?(on|from) (the|its) (tool )?name"
    r"|name suggests", re.I)


def load_tools(path=RAW / "tools.parquet") -> pd.DataFrame:
    t = pd.read_parquet(path, columns=["tool_id", "mcp_id", "tool_name", "description", "in_analysis_set"])
    return t[t.in_analysis_set == 1].reset_index(drop=True)


def add_flags(t: pd.DataFrame) -> pd.DataFrame:
    F = pd.DataFrame([score(n, d) for n, d in zip(t.tool_name, t.description)])
    return pd.concat([t.reset_index(drop=True), F], axis=1)


def join_labels(t: pd.DataFrame, m: pd.DataFrame) -> pd.DataFrame:
    """Inner-join tools to one judge label per tool_id. Duplicate tool_ids on either side are dropped (first kept)."""
    m = m.dropna(subset=["match_quality"]).drop_duplicates("tool_id")
    j = t.drop_duplicates("tool_id").merge(m, on="tool_id", how="inner")
    j["bad"] = (j.match_quality == "bad").astype(np.int8)
    j["good"] = (j.match_quality == "good").astype(np.int8)
    return j.reset_index(drop=True)


def server_weights(codes: np.ndarray, n_servers: int, rng) -> np.ndarray:
    """One cluster-bootstrap draw: each server's multiplicity (resampled with replacement), mapped to its rows."""
    mult = np.bincount(rng.integers(0, n_servers, n_servers), minlength=n_servers).astype(np.float64)
    return mult[codes]


def raw_diff(y, x, w):
    """Weighted P(y|x) - P(y|not x)."""
    a, b = (w * x).sum(), (w * (1 - x)).sum()
    if a == 0 or b == 0:
        return np.nan
    return (w * x * y).sum() / a - (w * (1 - x) * y).sum() / b


def mh_diff(y, x, s, w, keep, n_strata):
    """Mantel-Haenszel risk difference of y between x=1 and x=0 within strata s, over strata `keep`."""
    n1 = np.bincount(s, w * x, n_strata); n0 = np.bincount(s, w * (1 - x), n_strata)
    y1 = np.bincount(s, w * x * y, n_strata); y0 = np.bincount(s, w * (1 - x) * y, n_strata)
    ok = keep & (n1 > 0) & (n0 > 0)
    if not ok.any():
        return np.nan
    wt = n1[ok] * n0[ok] / (n1[ok] + n0[ok])
    return float((wt * (y1[ok] / n1[ok] - y0[ok] / n0[ok])).sum() / wt.sum())


def eligible_strata(x, s, n_strata, min_arm=MIN_ARM):
    n1 = np.bincount(s, x, n_strata); n0 = np.bincount(s, 1 - x, n_strata)
    return (n1 >= min_arm) & (n0 >= min_arm)


def ci(v):
    v = np.asarray(v, float); v = v[~np.isnan(v)]
    return [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)] if len(v) else [None, None]


def associations(j: pd.DataFrame, flags, B: int, seed: int = SEED) -> dict:
    rng = np.random.default_rng(seed)
    codes, uniq = pd.factorize(j.mcp_id)
    S = len(uniq)
    s = np.minimum(j.n_words.to_numpy(), LEN_CAP)
    ns = LEN_CAP + 1
    ys = {o: j[o].to_numpy(np.float64) for o in ("good", "bad")}
    xs = {f: j[f].to_numpy(np.float64) for f in flags}
    keep = {f: eligible_strata(xs[f], s, ns) for f in flags}
    one = np.ones(len(j))

    def est(w):
        r = {}
        for f in flags:
            for o, y in ys.items():
                r[(f, o, "raw")] = raw_diff(y, xs[f], w)
                r[(f, o, "len")] = np.nan if f in LENGTH_DEFINED else mh_diff(y, xs[f], s, w, keep[f], ns)
        return r

    point = est(one)
    boots = [est(server_weights(codes, S, rng)) for _ in range(B)]
    out = {}
    for f in flags:
        x = xs[f].astype(bool)
        d = dict(n_flagged=int(x.sum()), length_strata_used=int(keep[f].sum()),
                 tools_in_used_strata=int(np.isin(s, np.flatnonzero(keep[f])).sum()))
        for o in ("good", "bad"):
            d[f"{o}_if_flag"] = round(float(ys[o][x].mean()), 4) if x.any() else None
            d[f"{o}_if_not"] = round(float(ys[o][~x].mean()), 4)
            for k in ("raw", "len"):
                p = point[(f, o, k)]
                d[f"{o}_diff_{k}"] = None if np.isnan(p) else round(float(p), 4)
                d[f"{o}_diff_{k}_ci95"] = None if np.isnan(p) else ci([b[(f, o, k)] for b in boots])
        out[f] = d
    return out


def length_only_prediction(j: pd.DataFrame, flag: str) -> dict:
    """What the flagged/unflagged gap would be if outcome depended on length stratum alone."""
    s = np.minimum(j.n_words, LEN_CAP)
    out = {}
    for o in ("good", "bad"):
        pred = s.map(j.groupby(s)[o].mean())
        out[o] = round(float(pred[j[flag]].mean() - pred[~j[flag]].mean()), 4)
    return out


def server_adoption(t: pd.DataFrame, srv: pd.DataFrame, B: int, seed: int = SEED) -> dict:
    """Description-independent outcome: server GitHub stars (popularity, not usefulness) vs underspecified share,
    within bins of server median description length. Servers are the unit; bootstrap over servers."""
    g = t.groupby("mcp_id").agg(under=("underspecified", "mean"), content=("underspecified_content", "mean"),
                                med_words=("n_words", "median"), n=("tool_id", "size"))
    g = g.join(srv.set_index("mcp_id")[["github_stargazers_count"]], how="left")
    g = g[g.github_stargazers_count.notna()]
    g["y"] = (g.github_stargazers_count >= 10).astype(float)
    g["s"] = np.minimum(g.med_words.round().astype(int), 20)
    rng = np.random.default_rng(seed)
    res = {"n_servers_with_stars": int(len(g)), "outcome": "P(stars >= 10)"}
    for col, name in (("under", "majority_underspecified"), ("content", "any_underspecified_content")):
        x = (g[col] > 0.5).to_numpy(float) if col == "under" else (g[col] > 0).to_numpy(float)
        y, s = g.y.to_numpy(), g.s.to_numpy()
        keep = eligible_strata(x, s, 21)
        one = np.ones(len(g))
        pr, pl = raw_diff(y, x, one), mh_diff(y, x, s, one, keep, 21)
        bw = [rng.multinomial(len(g), np.full(len(g), 1 / len(g))).astype(float) for _ in range(B)]
        res[name] = dict(n_flagged=int(x.sum()), p_if_flag=round(float(y[x == 1].mean()), 4), p_if_not=round(float(y[x == 0].mean()), 4),
                         diff_raw=round(pr, 4), diff_raw_ci95=ci([raw_diff(y, x, w) for w in bw]),
                         diff_len=round(pl, 4), diff_len_ci95=ci([mh_diff(y, x, s, w, keep, 21) for w in bw]))
    return res


def stars_table(t: pd.DataFrame, srv: pd.DataFrame, B: int, seed: int = SEED) -> list:
    st = srv.set_index("mcp_id").github_stargazers_count
    x = t[["mcp_id", "underspecified", "underspecified_content", "n_words"]].copy()
    x["bin"] = pd.cut(x.mcp_id.map(st).fillna(-1), [-2, -0.5, 9, 99, 999, 1e12],
                      labels=["stars unknown", "0-9", "10-99", "100-999", "1000+"])
    rng = np.random.default_rng(seed)
    rows = []
    for b, d in x.groupby("bin", observed=True):
        codes, u = pd.factorize(d.mcp_id)
        yu, yc = d.underspecified.to_numpy(float), d.underspecified_content.to_numpy(float)
        boots = [server_weights(codes, len(u), rng) for _ in range(B)]
        rows.append(dict(bin=str(b), servers=len(u), tools=len(d), median_words=float(d.n_words.median()),
                         underspecified=round(yu.mean(), 4), underspecified_ci95=ci([(w * yu).sum() / w.sum() for w in boots]),
                         underspecified_content=round(yc.mean(), 4),
                         underspecified_content_ci95=ci([(w * yc).sum() / w.sum() for w in boots])))
    return rows


def destructive_cue(t: pd.DataFrame, B: int, seed: int = SEED) -> dict:
    """Share of rule-flagged destructive tools with no safety cue, overall and by where the trigger was found."""
    d = t[t.destructive]
    rng = np.random.default_rng(seed)
    out = {}
    subsets = {"all_destructive": d, "trigger_in_description": d[d.destructive_desc],
               "trigger_in_name_only": d[~d.destructive_desc], "description_15plus_words": d[d.n_words >= 15]}
    for k, sub in subsets.items():
        codes, u = pd.factorize(sub.mcp_id)
        y = sub.destructive_no_safety_cue.to_numpy(float)
        out[k] = dict(n=len(sub), no_cue=round(float(y.mean()), 4),
                      no_cue_ci95=ci([(w * y).sum() / w.sum() for w in (server_weights(codes, len(u), rng) for _ in range(B))]))
    out["mutating_share_of_tools"] = round(float(t.mutating.mean()), 4)
    return out


def main(B: int = 500):
    t = add_flags(load_tools())
    m = pd.read_parquet(RAW / "onet_matches.parquet", columns=["tool_id", "match_quality", "match_notes"])
    j = join_labels(t, m)
    j["notes_cite_desc"] = j.match_notes.fillna("").str.contains(NOTES_CITE_DESC.pattern, case=False, regex=True)
    j = j.drop(columns=["match_notes", "description"])
    srv = pd.read_parquet(RAW / "servers.parquet", columns=["mcp_id", "github_stargazers_count"])
    out = dict(rules_version=RULES_VERSION, seed=SEED, bootstrap_B=B, len_cap=LEN_CAP, min_arm=MIN_ARM,
               n_tools=len(t), n_matched=len(j), n_servers=int(t.mcp_id.nunique()),
               match_quality_dist=j.match_quality.value_counts(normalize=True).round(4).to_dict(),
               prevalence={f: round(float(t[f].mean()), 4) for f in FLAGS}, median_words=float(t.n_words.median()),
               underspecified_share_lt6_words=round(float((t[t.underspecified].n_words < 6).mean()), 4))
    out["association"] = associations(j, FLAGS, B)
    out["length_only_prediction"] = {f: length_only_prediction(j, f) for f in ("underspecified", "name_echo")}
    # sensitivity 1: exact (name, description) duplicates removed
    t_dd = t.drop_duplicates(["tool_name", "description"])
    jd = j[j.tool_id.isin(t_dd.tool_id)]
    out["sensitivity_dedup_name_desc"] = dict(n=len(jd), association=associations(jd, ["underspecified", "name_echo", "underspecified_content"], 100))
    # sensitivity 2: tools whose judge notes do not cite a missing/thin description (circularity check)
    out["judge_notes_cite_description"] = {k: round(float(j[j[k]].notes_cite_desc.mean()), 4) for k in ("is_empty", "too_short", "underspecified")}
    out["judge_notes_cite_description"]["not_underspecified"] = round(float(j[~j.underspecified].notes_cite_desc.mean()), 4)
    out["judge_notes_cite_description"]["good_rate_when_cited"] = round(float(j[j.notes_cite_desc].good.mean()), 4)
    out["judge_notes_cite_description"]["good_rate_when_not_cited"] = round(float(j[~j.notes_cite_desc].good.mean()), 4)
    jn = j[~j.notes_cite_desc]
    out["sensitivity_notes_not_citing_description"] = dict(n=len(jn), association=associations(jn, ["underspecified", "name_echo", "underspecified_content"], 100))
    out["server_adoption"] = server_adoption(t, srv, B)
    out["underspecified_by_server_stars"] = stars_table(t, srv, 200)
    out["destructive_safety_cue"] = destructive_cue(t, B)
    RES.mkdir(exist_ok=True)
    (RES / "metrics.json").write_text(json.dumps(out, indent=1))
    t[["tool_id", "mcp_id"] + FLAGS + ["n_words"]].to_parquet(RES / "tool_flags.parquet")  # git-ignored
    print(json.dumps({k: out[k] for k in ("n_tools", "n_matched", "prevalence")}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=500, help="cluster-bootstrap resamples")
    main(ap.parse_args().B)
