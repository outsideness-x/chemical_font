"""Importing this module fills the registry with every glyph of the font."""

from . import latin, symbols  # noqa: F401
from . import cyrillic, hangul, marks

marks.build_accented(marks.LATIN_ACCENTED)
cyrillic.register()
hangul.register()
