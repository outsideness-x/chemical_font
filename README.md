# chemical

A hand-drawn marker typeface for Latin, Cyrillic and Hangul.

chemical is drawn as skeletons — the centre line of each stroke — and then inked
by a simulated felt-tip pen: a slightly flat nib held at an angle, pressure that
swells and fades, ink that pools where the pen lands and in tight turns, a
ragged edge where it bleeds into the paper, and a hand that never draws the same
letter twice. Every script, including all 11,172 Hangul syllables, is inked by
the same pen, so text keeps one voice across languages.

## What is in the font

- **Latin**: Basic Latin, Latin-1, Latin Extended-A, Romanian comma-below letters.
- **Cyrillic**: Russian, Ukrainian, Belarusian.
- **Hangul**: all 11,172 syllables, compatibility jamo, and the CJK punctuation
  used in Korean text (「」『』〈〉《》、。※～).
- Figures, punctuation, currencies (₽ ₩ € £ ¥ ¢ $), arrows, ♥ ♡ ★ ☆ ✦ ✓ ✗.

## Features

| feature | on by default | what it does |
|---|---|---|
| `calt` | yes | every letter has four drawings; the one used depends on the letter before it, so doubled letters are never twins |
| `kern` | yes | kerning measured from the ink |
| `ss01` | no | fineliner: now and then a letter is written as a thin-pen capital |
| `ss02` | no | credits: lowercase letters jump to capitals now and then |
| `ss03` | no | hearts: o becomes ♥ |

`ss01` + `ss02` together give the mixed "film credits" look from plain typing.

## Using it

**iOS / macOS (OROT, remn)** — add `chemical-Regular.otf` to the target, list it
under `UIAppFonts` in Info.plist, then:

```swift
Font.custom("chemical", size: 28)
```

Stylistic sets from SwiftUI go through Core Text feature settings
(`kStylisticAlternativesType`, selectors 2 / 4 / 6 for ss01 / ss02 / ss03).

**Web** — for a single file, use `chemical-Regular.woff2`. For real pages use
the unicode-range slices from `tools/webfonts.py`: a page only downloads the
slices its text needs (Latin ≈ 150 KB; Hangul in slices of 240 common
syllables).

```html
<link rel="stylesheet" href="/fonts/chemical/chemical.css">
```

```css
.note { font-family: "chemical", sans-serif; }
.credits { font-feature-settings: "ss01", "ss02"; }
```

**Figma / design tools** — install `chemical-Regular.otf`. Stylistic sets are in
the type details panel.

## Build

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python tools/build.py          # .otf .ttf .woff2 into build/ (~5 min)
.venv/bin/python tools/webfonts.py       # unicode-range slices into build/web/
.venv/bin/python tools/check.py          # OTS, coverage, empty glyphs
```

For quick iterations, `tools/build.py --hangul-sample "텍스트"` builds only the
syllables of that text, and `tools/proof.py out.png "some text"` renders a proof.
Outlines are cached in `.cache/`, so only changed glyphs are re-inked.

`specimen/index.html` shows the font in use; serve the repository root
(`python3 -m http.server`) and open `/specimen/`.

## How it is made

- `src/chemical/skel.py` — skeleton building blocks (lines, curves, splines, bowls)
- `src/chemical/pen.py` — the pen: nib, pressure, pooling, joins, overshoots, ragged edge
- `src/chemical/fit.py` — merged ink back to clean cubic outlines
- `src/chemical/latin.py`, `cyrillic.py`, `marks.py`, `symbols.py` — the letters
- `src/chemical/hangul.py` — jamo and the six syllable layouts
- `src/chemical/features.py`, `kern.py` — OpenType features and kerning
