"""OpenType features.

calt  every letter exists in four hand-drawn variants; which one appears is
      decided by the letter before it (its identity and its own variant),
      carried across spaces, so a word never repeats a pose mechanically and
      doubled letters are never twins.
ss01  fineliner: now and then a letter is written as a thin-pen capital.
ss02  credits: lowercase letters jump to capitals now and then.
ss03  hearts for o.
kern  class kerning from the outlines (see kern.py).
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


def _alt(n, v):
    return n if v == 0 else f"{n}.alt{v}"


def _bases(present):
    return [n for n, gd in REGISTRY.items() if gd.variants >= N_VARIANTS and n in present]


def _contexts(base):
    """(group, variant) -> glyphs of that group drawn in that variant."""
    ctx = {}
    for g in range(N_VARIANTS):
        members = [n for n in base if _group(n) == g]
        if members:
            for v in range(N_VARIANTS):
                ctx[(g, v)] = [_alt(n, v) for n in members]
    return ctx


def calt(present):
    base = _bases(present)
    if not base:
        return [], []
    lines = [_cls(f"v{v}", [_alt(n, v) for n in base]) for v in range(N_VARIANTS)]
    ctx = _contexts(base)
    for (g, v), members in ctx.items():
        lines.append(_cls(f"g{g}v{v}", members))
    rules = []
    for (g, v) in ctx:
        t = (g + v + 1) % N_VARIANTS
        if t:
            rules.append(f"    sub @g{g}v{v} @v0' by @v{t};")
    if "space" in present:
        for (g, v) in ctx:
            t = (g + v + 2) % N_VARIANTS
            if t:
                rules.append(f"    sub @g{g}v{v} space @v0' by @v{t};")
    return lines + ["", "lookup cycle {"] + rules + ["} cycle;"], ["cycle"]


def _every(base, present, picks, tag):
    """Rules that fire after letters in `picks` (group, variant) contexts."""
    ctx = _contexts(base)
    return [(f"@g{g}v{v}", g, v) for (g, v) in picks if (g, v) in ctx]


def ss01(present):
    from .thin import pairs

    thin = [(b, f"{b}.thin") for b, _, _ in pairs() if b in present and f"{b}.thin" in present]
    if not thin:
        return [], []
    base = _bases(present)
    targets = [b for b, _ in thin if b in base]
    lines = []
    for v in range(N_VARIANTS):
        lines.append(_cls(f"thinsrc{v}", [_alt(b, v) for b in targets]))
    lines.append(_cls("thin", [f"{b}.thin" for b in targets]))
    picks = [(0, 2), (1, 3), (2, 0), (3, 1)]
    rules = []
    for cname, g, v in _every(base, present, picks, "ss01"):
        for k in range(N_VARIANTS):
            rules.append(f"    sub {cname} @thinsrc{k}' by @thin;")
    return lines + ["", "lookup fineliner {"] + rules + ["} fineliner;"], ["fineliner"]


def ss02(present):
    base = set(_bases(present))
    pairs_ = []
    for n in sorted(base):
        gd = REGISTRY[n]
        for u in gd.unicodes:
            ch = chr(u)
            up = ch.upper()
            if ch.islower() and len(up) == 1 and up != ch:
                from .marks import gname

                un = gname(ord(up))
                if un in base:
                    pairs_.append((n, un))
    if not pairs_:
        return [], []
    lines = []
    for v in range(N_VARIANTS):
        lines.append(_cls(f"lc{v}", [_alt(a, v) for a, _ in pairs_]))
        lines.append(_cls(f"uc{v}", [_alt(b, v) for _, b in pairs_]))
    picks = [(0, 0), (0, 3), (1, 1), (1, 2), (2, 2), (2, 1), (3, 3)]
    rules = []
    for cname, g, v in _every(sorted(base), present, picks, "ss02"):
        for k in range(N_VARIANTS):
            rules.append(f"    sub {cname} @lc{k}' by @uc{k};")
    # the first letter of a word is left alone; the rest follow the hand
    return lines + ["", "lookup credits {"] + rules + ["} credits;"], ["credits"]


def ss03(present):
    srcs = [n for n in ("o", "O", "uni043E", "uni041E") if n in present]
    if "heart" not in present or not srcs:
        return [], []
    subs = []
    for n in srcs:
        for v in range(N_VARIANTS):
            g = _alt(n, v)
            if g in present:
                subs.append(f"    sub {g} by heart;")
    return ["lookup hearts {"] + subs + ["} hearts;"], ["hearts"]


def feature_code(present, kern_fea=""):
    head = [
        "languagesystem DFLT dflt;",
        "languagesystem latn dflt;",
        "languagesystem cyrl dflt;",
        "languagesystem hang dflt;",
        "",
    ]
    body = []
    feats = []
    for tag, fn in (("calt", calt), ("ss01", ss01), ("ss02", ss02), ("ss03", ss03)):
        lines, lookups = fn(present)
        if lookups:
            body += lines + [""]
            feats.append((tag, lookups))
    out = head + body
    names = {"ss01": "Fineliner", "ss02": "Credits", "ss03": "Hearts"}
    for tag, lookups in feats:
        out.append(f"feature {tag} {{")
        if tag in names:
            out.append(f'    featureNames {{ name "{names[tag]}"; }};')
        out += [f"    lookup {name};" for name in lookups]
        out += [f"}} {tag};", ""]
    if kern_fea:
        out.append(kern_fea)
    return "\n".join(out)
