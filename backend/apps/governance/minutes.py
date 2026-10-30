"""One-page PDF of a meeting's minutes."""
from __future__ import annotations

import html

_LABELS = {
    "en": {"title": "Meeting minutes", "date": "Date", "attendees": "Attendees", "agenda": "Agenda", "notes": "Discussion", "decisions": "Decisions", "footer": "3maracom — 3mara.com"},
    "ar": {"title": "محضر اجتماع", "date": "التاريخ", "attendees": "الحضور", "agenda": "جدول الأعمال", "notes": "ما جرى في الاجتماع", "decisions": "القرارات", "footer": "عِمارة.كوم — 3mara.com"},
}


def render_minutes_pdf(meeting, lang: str) -> bytes:
    from weasyprint import HTML

    lang = lang if lang in _LABELS else "en"
    t, rtl = _LABELS[lang], lang == "ar"
    esc = lambda v: html.escape(str(v)).replace("\n", "<br>")  # noqa: E731
    when = str(meeting.held_on)
    when = when.translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")) if rtl else when

    def section(label, text):
        return f"<h2>{label}</h2><p>{esc(text)}</p>" if text.strip() else ""

    page = f"""<!DOCTYPE html><html dir="{'rtl' if rtl else 'ltr'}" lang="{lang}"><head><meta charset="utf-8"><style>
      @page {{ size: A4; margin: 16mm; }}
      body {{ font-family: "Noto Sans Arabic","Noto Sans","Segoe UI",Tahoma,Arial,sans-serif; font-size: 10.5pt; color: #161B26; }}
      .head {{ background: #254A80; color: #fff; padding: 6mm 8mm; border-radius: 3mm; }}
      .head h1 {{ margin: 0; font-size: 16pt; }} .head p {{ margin: 1mm 0 0; opacity: .85; font-size: 9pt; }}
      h2 {{ color: #254A80; font-size: 11.5pt; margin: 6mm 0 1.5mm; }} p {{ margin: 0; line-height: 1.7; unicode-bidi: plaintext; }}
      .foot {{ margin-top: 10mm; text-align: center; color: #6B7589; font-size: 8pt; }}
    </style></head><body>
      <div class="head"><h1>{esc(meeting.title)}</h1><p>{t['title']} · {esc(meeting.building.name)} · {t['date']}: {when}</p></div>
      {section(t['attendees'], meeting.attendees)}{section(t['agenda'], meeting.agenda)}
      {section(t['notes'], meeting.notes)}{section(t['decisions'], meeting.decisions)}
      <div class="foot">{t['footer']}</div></body></html>"""
    return HTML(string=page).write_pdf()
