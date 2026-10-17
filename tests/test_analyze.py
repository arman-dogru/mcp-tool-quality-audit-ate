import numpy as np
import pandas as pd

import analyze as A


def test_join_drops_duplicate_tool_ids_and_null_labels():
    t = pd.DataFrame(dict(tool_id=["a", "a", "b", "c"], mcp_id=["s1", "s1", "s1", "s2"], x=[1, 1, 0, 0]))
    m = pd.DataFrame(dict(tool_id=["a", "b", "b", "c"], match_quality=["good", "bad", "good", None]))
    j = A.join_labels(t, m)
    assert list(j.tool_id) == ["a", "b"]
    assert list(j.good) == [1, 0] and list(j.bad) == [0, 1]


def test_mh_diff_recovers_within_stratum_effect_under_confounding():
    # Long descriptions are both rarely flagged and more often good; within each stratum the flag adds +0.10.
    rng = np.random.default_rng(0)
    n = 200_000
    s = rng.integers(0, 2, n)
    x = (rng.random(n) < np.where(s == 0, 0.8, 0.2)).astype(float)
    y = (rng.random(n) < 0.1 + 0.4 * s + 0.10 * x).astype(float)
    w = np.ones(n)
    keep = A.eligible_strata(x, s, 2)
    assert A.raw_diff(y, x, w) < 0           # confounded raw contrast has the wrong sign
    assert abs(A.mh_diff(y, x, s, w, keep, 2) - 0.10) < 0.01


def test_server_weights_are_cluster_level():
    codes = np.array([0, 0, 0, 1, 2, 2])
    w = A.server_weights(codes, 3, np.random.default_rng(1))
    # all rows of one server share the same weight
    assert len(set(w[:3])) == 1 and len(set(w[4:])) == 1
    assert sum(np.unique(w[codes == k])[0] for k in range(3)) == 3


def test_cluster_bootstrap_widens_ci_for_clustered_outcome():
    # 200 servers x 50 tools; outcome fully determined at server level -> cluster CI must be wider than naive.
    rng = np.random.default_rng(0)
    S, k = 200, 50
    srv_y = (rng.random(S) < 0.3).astype(np.int8); srv_x = (rng.random(S) < 0.5)
    j = pd.DataFrame(dict(mcp_id=np.repeat(np.arange(S), k), good=np.repeat(srv_y, k), bad=np.repeat(1 - srv_y, k),
                          flag=np.repeat(srv_x, k), n_words=np.full(S * k, 8)))
    r = A.associations(j, ["flag"], B=200)["flag"]
    lo, hi = r["good_diff_raw_ci95"]
    p = j.good.mean(); naive_se = np.sqrt(p * (1 - p) * (1 / j.flag.sum() + 1 / (~j.flag).sum()))
    assert (hi - lo) > 4 * 1.96 * naive_se   # design effect ~ sqrt(50)


def test_length_defined_flags_have_no_stratified_estimate():
    j = pd.DataFrame(dict(mcp_id=np.arange(100) % 10, good=np.arange(100) % 2, bad=0, n_words=np.arange(100) % 10,
                          too_short=(np.arange(100) % 10) < 6))
    j["too_short"] = (j.n_words > 0) & (j.n_words < 6)
    r = A.associations(j, ["too_short"], B=5)["too_short"]
    assert r["good_diff_len"] is None
