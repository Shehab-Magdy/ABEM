"""Every literal string passed to gettext in the backend must have an Arabic translation."""

import ast
from pathlib import Path

import polib

BACKEND = Path(__file__).resolve().parent.parent
PO_PATH = BACKEND / "locale" / "ar" / "LC_MESSAGES" / "django.po"
GETTEXT_NAMES = {"_", "gettext", "gettext_lazy"}


def _source_msgids():
    found = {}
    for root in ("apps", "config"):
        for path in (BACKEND / root).rglob("*.py"):
            if "migrations" in path.parts:
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in GETTEXT_NAMES
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    found.setdefault(node.args[0].value, f"{path.relative_to(BACKEND)}:{node.lineno}")
    return found


def test_every_gettext_string_has_arabic_translation():
    po = polib.pofile(str(PO_PATH))
    translated = {e.msgid for e in po if e.msgstr.strip() and not e.fuzzy}
    missing = {m: where for m, where in _source_msgids().items() if m not in translated}
    assert not missing, "Missing from locale/ar django.po:\n" + "\n".join(f"{w}: {m!r}" for m, w in missing.items())
