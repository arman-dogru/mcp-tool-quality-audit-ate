"""Draw the two v2 validation samples (review N5). Run after the rules are frozen; writes git-ignored files under data/raw/.

- random sample: 100 tools from in_analysis_set == 1, excluding the 40 v1 dev-set tools, pandas .sample(random_state=2026)
- destructive sample: 60 of the remaining tools that rules v2 flag as destructive, .sample(random_state=2026)
The labelling files (blind_*.txt) show only index, tool name and the first 400 characters of the description:
no rule outputs, judge labels or judge notes."""
import argparse
from pathlib import Path

import pandas as pd

from metrics import score

ROOT = Path(__file__).resolve().parent.parent
SEED = 2026


def draw(tools: pd.DataFrame):
    v1 = tools.sample(40, random_state=0)  # the v1 dev set, drawn exactly as in v1 (from all rows)
    a = tools[(tools.in_analysis_set == 1) & ~tools.tool_id.isin(v1.tool_id)].drop_duplicates("tool_id")
    s1 = a.sample(100, random_state=SEED)
    rest = a[~a.tool_id.isin(s1.tool_id)]
    dest = pd.Series([score(n, d)["destructive"] for n, d in zip(rest.tool_name, rest.description)], index=rest.index)
    s2 = rest[dest].sample(60, random_state=SEED)
    return s1, s2


def main(out_dir: Path):
    tools = pd.read_parquet(ROOT / "data/raw/tools.parquet", columns=["tool_id", "tool_name", "description", "in_analysis_set"])
    s1, s2 = draw(tools)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, s in (("underspec", s1), ("destructive", s2)):
        with open(out_dir / f"blind_{name}.txt", "w") as f:
            for i, r in enumerate(s.itertuples()):
                f.write(f"{i}\t{r.tool_name}\t{(r.description or '').strip()[:400]!r}\n")
        s[["tool_id", "tool_name", "description"]].to_parquet(out_dir / f"blind_{name}.parquet")
    print(len(s1), len(s2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "data/raw")
    main(ap.parse_args().out)
