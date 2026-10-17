"""Agreement of the `underspecified` heuristic with hand labels on a fixed random sample."""
import json, sys, pandas as pd
sys.path.insert(0, "src"); from metrics import score
L = json.load(open("data/hand_labels.json"))["underspecified"]
t = pd.read_parquet("data/raw/tools.parquet", columns=["tool_name", "description"]).sample(40, random_state=0)
pred = [int(score(n, d)["underspecified"]) for n, d in zip(t.tool_name, t.description)]; gold = [L[str(i)] for i in range(40)]
tp = sum(p and g for p, g in zip(pred, gold)); fp = sum(p and not g for p, g in zip(pred, gold)); fn = sum(g and not p for p, g in zip(pred, gold)); tn = 40 - tp - fp - fn
r = dict(n=40, tp=tp, fp=fp, fn=fn, tn=tn, accuracy=round((tp+tn)/40, 3), precision=round(tp/max(tp+fp, 1), 3), recall=round(tp/max(tp+fn, 1), 3),
         label_rate=sum(gold)/40, pred_rate=sum(pred)/40, disagreements=[i for i in range(40) if pred[i] != gold[i]])
print(json.dumps(r)); json.dump(r, open("results/validation.json", "w"), indent=1)
