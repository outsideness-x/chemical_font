"""Importing this module fills the registry with every glyph of the font."""

from . import latin, symbols  # noqa: F401
from . import cyrillic, hangul, marks, thin

marks.build_accented(marks.LATIN_ACCENTED)
cyrillic.register()
thin.register()
hangul.register()
