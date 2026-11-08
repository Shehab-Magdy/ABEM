"""
Small, dependency-free helpers for turning a request into something a
human can recognise on a "your signed-in devices" screen: a short
"<Browser> on <OS>" label from the User-Agent header, and the client IP
using the non-spoofable X-Real-IP-then-REMOTE_ADDR convention (also used
by `apps.audit.mixins.log_action`).
"""

from __future__ import annotations

import re

# Order matters: Edge and Opera both also contain "Chrome/" (fake-UA /
# Chromium-based), so they're checked first. Safari's UA also contains
# "Safari/" even on Chrome, so it's matched last via the Version/ marker
# that only genuine Safari sends.
_BROWSER_PATTERNS = [
    ("Edge", re.compile(r"Edg(?:A|iOS)?/")),
    ("Opera", re.compile(r"OPR/|Opera/")),
    ("Chrome", re.compile(r"Chrome/")),
    ("Firefox", re.compile(r"Firefox/")),
    ("Safari", re.compile(r"Version/.*Safari/")),
]

# iPhone/iPad are checked before "Mac OS X" since iOS Safari's UA contains
# the substring "like Mac OS X".
_OS_PATTERNS = [
    ("iPhone", re.compile(r"iPhone")),
    ("iPad", re.compile(r"iPad")),
    ("Android", re.compile(r"Android")),
    ("macOS", re.compile(r"Mac OS X")),
    ("Windows", re.compile(r"Windows")),
    ("Linux", re.compile(r"Linux")),
]


def device_label_from_user_agent(user_agent: str) -> str:
    """
    "Chrome on macOS", "Safari on iPhone", "Firefox on Windows", etc. from a
    raw User-Agent header. Falls back to "Unknown device" when neither a
    browser nor an OS can be recognised (e.g. a bare API client UA).
    """
    user_agent = user_agent or ""
    browser = next(
        (name for name, pat in _BROWSER_PATTERNS if pat.search(user_agent)), None
    )
    os_name = next((name for name, pat in _OS_PATTERNS if pat.search(user_agent)), None)

    if not browser and not os_name:
        return "Unknown device"
    return f"{browser or 'Unknown browser'} on {os_name or 'Unknown OS'}"


def client_ip_from_request(request) -> str | None:
    """
    Best-effort client IP.

    Prefers X-Real-IP, which production nginx sets from the actual TCP
    connection (`proxy_set_header X-Real-IP $remote_addr;`) and therefore
    cannot be spoofed by the client - unlike X-Forwarded-For, which nginx
    only APPENDS to (`$proxy_add_x_forwarded_for`), so a client-sent fake
    first entry would otherwise be trusted. Falls back to REMOTE_ADDR for
    local dev / tests where there's no proxy in front at all.
    """
    real_ip = request.META.get("HTTP_X_REAL_IP")
    if real_ip:
        return real_ip.strip()
    return request.META.get("REMOTE_ADDR")
