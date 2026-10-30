"""Shared CSV reading for the bulk imports (units, expenses)."""
from __future__ import annotations

import csv
import io

from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

MAX_ROWS = 500
MAX_BYTES = 1024 * 1024


def read_rows(upload, required: list[str], allowed: list[str]) -> list[dict]:
    """Read an uploaded CSV into dicts keyed by lower-cased header. Raises ValidationError for a bad file.

    Accepts UTF-8 (with or without a BOM, so Excel exports work) and comma or semicolon separators.
    """
    if upload is None:
        raise ValidationError({"file": _("Attach a CSV file.")})
    if upload.size > MAX_BYTES:
        raise ValidationError({"file": _("The file is too large (1 MB at most).")})
    try:
        text = upload.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValidationError({"file": _("Save the file as UTF-8 CSV.")})
    sample = text[:2048]
    delimiter = ";" if sample.count(";") > sample.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = [(h or "").strip().lower() for h in (reader.fieldnames or [])]
    missing = [c for c in required if c not in headers]
    unknown = [h for h in headers if h and h not in allowed]
    if missing:
        raise ValidationError({"file": _("Missing columns: %(cols)s.") % {"cols": ", ".join(missing)}})
    if unknown:
        raise ValidationError({"file": _("Unknown columns: %(cols)s.") % {"cols": ", ".join(unknown)}})
    rows = []
    for raw in reader:
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items() if k}
        if any(row.values()):  # skip blank lines
            rows.append(row)
    if not rows:
        raise ValidationError({"file": _("The file has no rows.")})
    if len(rows) > MAX_ROWS:
        raise ValidationError({"file": _("At most %(n)s rows per file.") % {"n": MAX_ROWS}})
    return rows
