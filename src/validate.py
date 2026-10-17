"""Agreement of the v2 heuristics with blind hand labels (data/hand_labels_v2.json), plus the v1 dev set for reference.
Labels are keyed by tool_id and verified against a hash of name+description, so they cannot silently drift."""
import hashlib
import json
import math
from pathlib import Path

import pandas as pd

from metrics import score

ROOT = Path(__file__).resolve().parent.parent


def text_sha1(name, desc) -> str:
    return hashlib.sha1(f"{name}\x1f{desc}".encode()).hexdigest()[:12]


def wilson(k: int, n: int, z: float = 1.96) -> list:
    if n == 0:
        return [None, None]
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(c - h, 3), round(c + h, 3)]


def kappa(pred, gold) -> float:
    n = len(gold); po = sum(p == g for p, g in zip(pred, gold)) / n
    pp, pg = sum(pred) / n, sum(gold) / n; pe = pp * pg + (1 - pp) * (1 - pg)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else float("nan")


def agreement(pred, gold) -> dict:
    n = len(gold)
    tp = sum(p and g for p, g in zip(pred, gold)); fp = sum(p and not g for p, g in zip(pred, gold))
    fn = sum(g and not p for p, g in zip(pred, gold)); tn = n - tp - fp - fn
    return dict(n=n, tp=tp, fp=fp, fn=fn, tn=tn, accuracy=round((tp + tn) / n, 3), accuracy_ci95=wilson(tp + tn, n),
                majority_class_accuracy=round(max(sum(gold), n - sum(gold)) / n, 3),
                precision=round(tp / max(tp + fp, 1), 3), precision_ci95=wilson(tp, tp + fp),
                recall=round(tp / max(tp + fn, 1), 3), recall_ci95=wilson(tp, tp + fn), kappa=kappa(pred, gold),
                label_rate=round(sum(gold) / n, 3), label_rate_ci95=wilson(sum(gold), n), pred_rate=round(sum(pred) / n, 3))


def lookup(items, tools):
    t = tools.set_index("tool_id").loc[[i["tool_id"] for i in items]]
    for i, (n, d) in zip(items, zip(t.tool_name, t.description)):
        assert text_sha1(n, d) == i["text_sha1"], f"label/text mismatch for {i['tool_id']}"
    return [score(n, d) for n, d in zip(t.tool_name, t.description)]


def main():
    tools = pd.read_parquet(ROOT / "data/raw/tools.parquet", columns=["tool_id", "tool_name", "description"]).drop_duplicates("tool_id")
    L = json.loads((ROOT / "data/hand_labels_v2.json").read_text())
    r = dict(rules_version=L["rules_version"])
    rs = L["random_sample"]; f = lookup(rs, tools)
    r["underspecified_random_n100"] = agreement([int(x["underspecified"]) for x in f], [i["underspecified"] for i in rs])
    r["destructive_random_n100"] = agreement([int(x["destructive"]) for x in f], [i["destructive"] for i in rs])
    ds = L["destructive_sample"]; f = lookup(ds, tools)
    true = [i for i in ds if i["destructive"]]
    ft = [x for x, i in zip(f, ds) if i["destructive"]]
    r["destructive_flag_precision_n60"] = dict(k=len(true), n=len(ds), precision=round(len(true) / len(ds), 3), ci95=wilson(len(true), len(ds)))
    r["hand_no_cue_among_truly_destructive"] = dict(k=sum(1 - i["safety_cue"] for i in true), n=len(true),
                                                     share=round(sum(1 - i["safety_cue"] for i in true) / len(true), 3),
                                                     ci95=wilson(sum(1 - i["safety_cue"] for i in true), len(true)))
    r["safety_cue_rule_vs_hand_on_truly_destructive"] = agreement([int(x["safety_cue"]) for x in ft], [i["safety_cue"] for i in true])
    v1 = json.loads((ROOT / "data/hand_labels_v1_dev.json").read_text())["items"]; f = lookup(v1, tools)
    r["v1_dev_set_underspecified_n40_NOT_HELD_OUT"] = agreement([int(x["underspecified"]) for x in f], [i["underspecified"] for i in v1])
    (ROOT / "results/validation.json").write_text(json.dumps(r, indent=1))
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
