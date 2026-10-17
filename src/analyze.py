"""Score all ATE tools, then relate description flags to the ATE judge's match_quality labels.
Uncertainty: cluster bootstrap over servers (mcp_id), since tools from one server share authors/style."""
import json, sys, numpy as np, pandas as pd
sys.path.insert(0, "src"); from metrics import score, FLAGS
SEED = 0; rng = np.random.default_rng(SEED)
t = pd.read_parquet("data/raw/tools.parquet", columns=["tool_id", "mcp_id", "tool_name", "description", "in_analysis_set"])
F = pd.DataFrame([score(n, d) for n, d in zip(t.tool_name, t.description)]); t = pd.concat([t.reset_index(drop=True), F], axis=1)
m = pd.read_parquet("data/raw/onet_matches.parquet", columns=["tool_id", "match_quality", "cosine_similarity"]).dropna(subset=["match_quality"])
m = m.drop_duplicates("tool_id"); j = t.merge(m, on="tool_id", how="inner"); j["bad"] = (j.match_quality == "bad").astype(int); j["good"] = (j.match_quality == "good").astype(int)
s = pd.read_parquet("data/raw/servers.parquet", columns=["mcp_id", "github_stargazers_count", "source"])
out = dict(seed=SEED, n_tools=len(t), n_matched=len(j), n_servers=int(t.mcp_id.nunique()),
           match_quality_dist=j.match_quality.value_counts(normalize=True).round(4).to_dict(),
           prevalence={f: round(float(t[f].mean()), 4) for f in FLAGS}, median_words=float(t.n_words.median()))
# cluster bootstrap over servers
srv = j.mcp_id.unique(); g = {k: v.index.values for k, v in j.groupby("mcp_id")}; B = 200
def rates(df):
    r = {}
    for f in FLAGS:
        a, b = df[df[f]], df[~df[f]]
        r[f] = (a.bad.mean() if len(a) else np.nan, b.bad.mean(), a.good.mean() if len(a) else np.nan, b.good.mean())
    r["risk"] = [df[df.risk_score == k].good.mean() if (df.risk_score == k).any() else np.nan for k in range(5)]
    return r
point = rates(j); boots = []
for _ in range(B):
    idx = np.concatenate([g[k] for k in rng.choice(srv, len(srv))]); boots.append(rates(j.loc[idx]))
def ci(vals): v = np.array([x for x in vals if not np.isnan(x)]); return [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)]
assoc = {}
for f in FLAGS:
    p = point[f]; bd = [b[f][0] - b[f][1] for b in boots]; gd = [b[f][2] - b[f][3] for b in boots]
    assoc[f] = dict(n_flagged=int(j[f].sum()), bad_if_flag=round(float(p[0]), 4), bad_if_not=round(float(p[1]), 4), bad_diff=round(float(p[0]-p[1]), 4), bad_diff_ci95=ci(bd),
                    good_if_flag=round(float(p[2]), 4), good_if_not=round(float(p[3]), 4), good_diff=round(float(p[2]-p[3]), 4), good_diff_ci95=ci(gd))
out["association_with_match_quality"] = assoc
out["good_rate_by_risk_score"] = {k: dict(n=int((j.risk_score == k).sum()), good=round(float(point["risk"][k]), 4), ci95=ci([b["risk"][k] for b in boots])) for k in range(5) if (j.risk_score == k).any()}
# baseline: does description length alone explain it? good rate by length quintile
j["len_q"] = pd.qcut(j.n_words.rank(method="first"), 5, labels=False)
out["baseline_length_quintiles"] = j.groupby("len_q").agg(words=("n_words", "median"), good=("good", "mean"), bad=("bad", "mean")).round(4).reset_index().to_dict("records")
# server popularity vs underspecification
ts = t.groupby("mcp_id").agg(under=("underspecified", "mean"), n=("tool_id", "size")).join(s.set_index("mcp_id"))
ts["star_bin"] = pd.cut(ts.github_stargazers_count.fillna(-1), [-2, -0.5, 9, 99, 999, 1e9], labels=["no repo", "0-9", "10-99", "100-999", "1000+"])
out["underspecified_by_server_stars"] = ts.groupby("star_bin", observed=True).agg(servers=("n", "size"), tools=("n", "sum"), underspecified=("under", "mean")).round(4).reset_index().astype({"star_bin": str}).to_dict("records")
json.dump(out, open("results/metrics.json", "w"), indent=1)
t[["tool_id", "mcp_id", "tool_name"] + FLAGS + ["n_words", "risk_score"]].to_parquet("results/tool_flags.parquet")
print(json.dumps({k: out[k] for k in ("n_tools", "n_matched", "prevalence", "match_quality_dist")}, indent=1))
