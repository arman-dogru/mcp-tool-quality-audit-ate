"""Deterministic, CPU-only heuristics for MCP tool-description quality.

Each flag is a transparent regex/lexicon rule so results are reproducible and auditable.
They are *heuristics*, validated against a hand-labelled sample (see src/validate.py)."""
import re

OVERCLAIM = re.compile(r"\b(best|ultimate|perfect(ly)?|guarantee[sd]?|always|never fails?|any(thing)?|every(thing)?|all (kinds|types|of)|"
                       r"seamless(ly)?|effortless(ly)?|powerful|comprehensive|complete(ly)?|fully|instantly|100%|world'?s|most advanced|"
                       r"state[- ]of[- ]the[- ]art|unlimited|universal|accurate(ly)?|reliabl[ey])\b", re.I)
VAGUE = re.compile(r"\b(etc\.?|and more|and so on|various|stuff|things|something|misc(ellaneous)?|general[- ]purpose|whatever|"
                   r"handles?|manages?|process(es)?|deals? with|works? with|helps? (with|you)|does)\b", re.I)
IO_SPEC = re.compile(r"\b(returns?|outputs?|responds? with|yields?|input|parameters?|params?|args?|arguments?|accepts?|takes?|"
                     r"requires?|given (a|an|the)|required|optional|json|string|integer|boolean|list of|array|id\b|url\b|path\b)", re.I)
SIDE_EFFECT = re.compile(r"\b(delete|remove|drop|send|post|publish|transfer|pay|purchase|execute|run|write|overwrite|update|create|deploy|"
                         r"kill|terminate|modify|submit|email)\b", re.I)
SAFETY_CUE = re.compile(r"\b(confirm(ation)?|irreversibl[ey]|permanent(ly)?|cannot be undone|dry[- ]run|preview|warning|caution|"
                        r"requires? (approval|permission)|read[- ]only|destructive)\b", re.I)
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+")

def words(t): return WORD.findall(t or "")
def name_tokens(name): return {w.lower() for w in re.split(r"[_\-\s.]+|(?<=[a-z])(?=[A-Z])", name or "") if len(w) > 2}
def ascii_ratio(t): return sum(c.isascii() for c in t) / len(t) if t else 1.0

def score(name: str, desc: str) -> dict:
    d = (desc or "").strip(); w = words(d); n = len(w)
    nt = name_tokens(name); dl = d.lower()
    f = dict(
        n_words=n,
        empty=n == 0,
        too_short=0 < n < 6,
        non_english=bool(d) and ascii_ratio(d) < 0.8,
        overclaim=bool(OVERCLAIM.search(d)),
        vague=bool(VAGUE.search(d)),
        no_io_spec=n > 0 and not IO_SPEC.search(d),
        name_echo=n > 0 and n <= len(nt) + 2 and all(t in dl for t in nt),   # description just restates the name
        side_effect=bool(SIDE_EFFECT.search(d) or SIDE_EFFECT.search((name or "").replace("_", " "))),
    )
    f["side_effect_no_safety_cue"] = f["side_effect"] and not SAFETY_CUE.search(d)
    # composite "hallucination-prone" = underspecified enough that a model must guess what the tool does or takes
    f["underspecified"] = f["empty"] or f["too_short"] or f["name_echo"] or (f["vague"] and f["no_io_spec"])
    f["risk_score"] = sum(int(f[k]) for k in ("underspecified", "overclaim", "no_io_spec", "side_effect_no_safety_cue"))
    return f

FLAGS = ["empty", "too_short", "non_english", "overclaim", "vague", "no_io_spec", "name_echo", "side_effect", "side_effect_no_safety_cue", "underspecified"]
