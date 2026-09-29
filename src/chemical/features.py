"""OpenType features.

calt: every letter exists in four hand-drawn variants. Which one appears is
decided by the letter before it (its identity and its own variant), carried
across spaces, so a word never repeats a pose mechanically and doubled
letters are never twins.
"""

from .noise import seed_of
from .registry import REGISTRY

N_VARIANTS = 4


def extra_jobs(jobs, filter_fn=None):
    return []


def _cls(name, glyphs):
    return f"@{name} = [{' '.join(glyphs)}];"


def _group(name):
    return seed_of("calt-group", name) % N_VARIANTS


def calt(present):
    base = [n for n, gd in REGISTRY.items() if gd.variants >= N_VARIANTS and n in present]
    if not base:
        return "", []

    def alt(n, v):
        return n if v == 0 else f"{n}.alt{v}"

    lines = []
    for v in range(N_VARIANTS):
        lines.append(_cls(f"v{v}", [alt(n, v) for n in base]))
    ctx = {}
    for g in range(N_VARIANTS):
        members = [n for n in base if _group(n) == g]
        for v in range(N_VARIANTS):
            if members:
                ctx[(g, v)] = f"g{g}v{v}"
                lines.append(_cls(ctx[(g, v)], [alt(n, v) for n in members]))

    rules = []
    for (g, v), cname in ctx.items():
        t = (g + v + 1) % N_VARIANTS
        if t:
            rules.append(f"    sub @{cname} @v0' by @v{t};")
    for (g, v), cname in ctx.items():
        t = (g + v + 2) % N_VARIANTS
        if t and "space" in present:
            rules.append(f"    sub @{cname} space @v0' by @v{t};")
    lookup = ["lookup cycle {"] + rules + ["} cycle;"]
    return "\n".join(lines + [""] + lookup), ["cycle"]


def feature_code(present):
    head = [
        "languagesystem DFLT dflt;",
        "languagesystem latn dflt;",
        "languagesystem cyrl dflt;",
        "languagesystem hang dflt;",
        "",
    ]
    body, lookups = calt(present)
    fea = head + [body, ""]
    if lookups:
        fea += ["feature calt {"] + [f"    lookup {name};" for name in lookups] + ["} calt;", ""]
    return "\n".join(fea)
