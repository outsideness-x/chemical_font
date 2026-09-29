# chemical

A hand-drawn marker typeface for Latin, Cyrillic and Hangul.

chemical is drawn as skeletons — the centre line of each stroke — and then inked
by a simulated felt-tip pen: a slightly oval nib, a little pressure at the start
of every stroke, a hand that never draws the same line twice. Every script,
including all 11,172 Hangul syllables, is inked by the same pen, so the colour
of the text stays even across languages.

## Build

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python tools/build.py
```

Fonts are written to `build/`.
