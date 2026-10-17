"""Deterministic, CPU-only heuristics for MCP tool-description quality.

Each flag is a transparent regex/lexicon rule so results are reproducible and auditable.
They are heuristics. Their agreement with blind hand labels is measured in src/validate.py.
Rule version is frozen in git *before* the labels in data/hand_labels_v2.json were drawn (see README)."""
import math
import re
import unicodedata

RULES_VERSION = "v2"


def _forms(verb: str) -> list[str]:
    """Regular English inflections of a verb: delete -> delete, deletes, deleted, deleting."""
    out = {verb, verb + "s", verb + "ed", verb + "ing"}
    if verb.endswith("e"):
        out |= {verb + "d", verb[:-1] + "ing"}
    if verb.endswith(("s", "sh", "ch", "x")):
        out.add(verb + "es")
    if verb.endswith("y") and verb[-2] not in "aeiou":
        out |= {verb[:-1] + "ies", verb[:-1] + "ied"}
    if re.fullmatch(r".*[^aeiou][aeiou][bdgmnprt]", verb) and len(verb) <= 4:  # drop -> dropped, dropping
        out |= {verb + verb[-1] + "ed", verb + verb[-1] + "ing"}
    return sorted(out, key=len, reverse=True)


def _verb_re(verbs) -> re.Pattern:
    alts = sorted({f for v in verbs for f in _forms(v)}, key=len, reverse=True)
    return re.compile(r"\b(" + "|".join(alts) + r")\b", re.I)


# Prose-level overclaiming. Neutral quantifiers ("any", "every", "complete", "all of") were removed in v2:
# they mostly occur in ordinary, specific descriptions ("Returns any errors").
OVERCLAIM = re.compile(r"\b(best|ultimate|perfect(ly)?|guarantee[sd]?|never fails?|seamless(ly)?|effortless(ly)?|"
                       r"most (advanced|powerful)|state[- ]of[- ]the[- ]art|unlimited|blazing(ly)?[- ]fast|"
                       r"world'?s (best|first|leading|most)|100% (accurate|reliable|safe))\b", re.I)
VAGUE = re.compile(r"\b(etc\.?|and more|and so on|various|stuff|things|something|misc(ellaneous)?|general[- ]purpose|whatever|"
                   r"handles?|manages?|process(es)?|deals? with|works? with|helps? (with|you)|does)\b", re.I)
IO_SPEC = re.compile(r"\b(returns?|returning|outputs?|responds? with|yields?|inputs?|parameters?|params?|args?|arguments?|"
                     r"accepts?|takes?|requires?|given (a|an|the)|required|optional|json|string|integer|boolean|list of|"
                     r"array|ids?|url|path)\b", re.I)
# Destructive or externally visible/irreversible actions (data loss, money, outbound messages, deployments).
DESTRUCTIVE = _verb_re(["delete", "remove", "drop", "destroy", "purge", "wipe", "truncate", "overwrite", "erase", "kill",
                        "terminate", "revoke", "uninstall", "send", "email", "publish", "transfer", "pay", "purchase",
                        "buy", "refund", "deploy", "broadcast", "unsubscribe", "ban"])
# Ablation (review N4): same lexicon without "email", whose noun use (list_emails, get_email) is not destructive.
DESTRUCTIVE_NO_EMAIL = _verb_re(["delete", "remove", "drop", "destroy", "purge", "wipe", "truncate", "overwrite", "erase", "kill",
                                 "terminate", "revoke", "uninstall", "send", "publish", "transfer", "pay", "purchase",
                                 "buy", "refund", "deploy", "broadcast", "unsubscribe", "ban"])
# State-changing but usually recoverable.
MUTATING = _verb_re(["create", "update", "write", "modify", "edit", "insert", "post", "submit", "run", "execute",
                     "rename", "move", "upload", "upsert", "patch", "commit", "merge", "schedule", "cancel"])
SAFETY_CUE = re.compile(r"\b(confirm(s|ed|ation)?|irreversibl[ey]|permanent(ly)?|(cannot|can't|can ?not) be (undone|reversed|recovered)|"
                        r"not reversible|no undo|dry[-_ ]?run|preview|warning|caution|careful|use with care|"
                        r"requires? (explicit )?(approval|permission|confirmation)|destructive|dangerous)\b", re.I)
# Unicode-aware word: a letter followed by letters/digits/apostrophes/hyphens (handles accents, 1-letter words).
WORD = re.compile(r"[^\W\d_](?:[\w'’-]*\w)?")
# Scripts written without spaces: count characters / 2 as a word proxy.
NOSPACE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\u0e00-\u0e7f]")


def _s(x) -> str:
    """Coerce any input (None, NaN, numbers) to a string; missing values become ''."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    return x if isinstance(x, str) else str(x)


def n_words(text: str) -> int:
    text = _s(text)
    k = len(NOSPACE.findall(text))
    rest = NOSPACE.sub(" ", text)
    return len(WORD.findall(rest)) + (max(1, k // 2) if k else 0)


def name_tokens(name: str) -> set[str]:
    parts = re.split(r"[_\-\s.:/]+|(?<=[a-z])(?=[A-Z])", _s(name))
    return {w.lower() for w in parts if len(w) > 2}


def non_latin_share(text: str) -> float:
    """Share of letters that are not Latin script. A script measure, not a language ID."""
    letters = [c for c in _s(text) if c.isalpha()]
    if not letters:
        return 0.0
    return sum("LATIN" not in unicodedata.name(c, "") for c in letters) / len(letters)


def _name_text(name: str) -> str:
    return " ".join(re.split(r"[_\-\s.:/]+|(?<=[a-z])(?=[A-Z])", _s(name)))


def score(name, desc) -> dict:
    name, d = _s(name), _s(desc).strip()
    n = n_words(d)
    nt = name_tokens(name)
    dl = d.lower()
    nm = _name_text(name)
    dest_desc, dest_name = bool(DESTRUCTIVE.search(d)), bool(DESTRUCTIVE.search(nm))
    mut_desc, mut_name = bool(MUTATING.search(d)), bool(MUTATING.search(nm))
    cue = bool(SAFETY_CUE.search(d) or SAFETY_CUE.search(nm))
    f = dict(
        n_words=n,
        is_empty=n == 0,
        too_short=0 < n < 6,
        non_latin_script=bool(d) and non_latin_share(d) > 0.5,
        overclaim=bool(OVERCLAIM.search(d)),
        vague=bool(VAGUE.search(d)),
        no_io_spec=n > 0 and not IO_SPEC.search(d),
        # description only restates the name (guarded: a name with no >2-char token cannot be "echoed")
        name_echo=n > 0 and bool(nt) and n <= len(nt) + 2 and all(t in dl for t in nt),
        destructive=dest_desc or dest_name,
        destructive_desc=dest_desc,
        mutating=(mut_desc or mut_name) and not (dest_desc or dest_name),
        safety_cue=cue,
    )
    f["destructive_no_safety_cue"] = f["destructive"] and not cue
    # content-based underspecification, independent of the length threshold
    f["underspecified_content"] = f["name_echo"] or (f["vague"] and f["no_io_spec"])
    # composite: a model would have to guess what the tool does or takes
    f["underspecified"] = f["is_empty"] or f["too_short"] or f["underspecified_content"]
    return f


FLAGS = ["is_empty", "too_short", "non_latin_script", "overclaim", "vague", "no_io_spec", "name_echo",
         "destructive", "mutating", "destructive_no_safety_cue", "underspecified_content", "underspecified"]
# Flags that are pure functions of length cannot be compared within an exact-length stratum.
LENGTH_DEFINED = {"is_empty", "too_short"}
