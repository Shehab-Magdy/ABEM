"""Playwright helper that drives the app like a person: a visible cursor, click
ripples, element highlights, and a branded "email arrived" overlay.

Environment (defaults match the demo stack in README.md):
    DEMO_URL   app URL                         http://127.0.0.1:5174
    DEMO_LOGS  shell command printing API logs  docker logs abem-demo-backend --since 40s
"""
import os
import re
import subprocess
import time

BASE = os.environ.get("DEMO_URL", "http://127.0.0.1:5174")
LOGS = os.environ.get("DEMO_LOGS", "docker logs abem-demo-backend --since 40s")

INIT_JS = r"""
localStorage.setItem('abem_language','ar');
(() => {
  const add = () => {
    if (document.getElementById('__cur')) return;
    const st = document.createElement('style');
    st.textContent = `
      #__cur{position:fixed;left:0;top:0;width:30px;height:30px;z-index:2147483647;pointer-events:none;
        transform:translate(-100px,-100px);transition:transform .6s cubic-bezier(.4,0,.2,1);filter:drop-shadow(0 2px 3px rgba(0,0,0,.45))}
      .__rip{position:fixed;z-index:2147483646;pointer-events:none;width:14px;height:14px;margin:-7px 0 0 -7px;border-radius:50%;
        background:rgba(226,122,74,.55);animation:__rip .6s ease-out forwards}
      @keyframes __rip{to{transform:scale(5);opacity:0}}
      .__hl{outline:4px solid #E27A4A !important;outline-offset:4px;border-radius:10px;transition:outline .2s}
    `;
    document.head.appendChild(st);
    const c = document.createElement('div'); c.id = '__cur';
    c.innerHTML = '<svg viewBox="0 0 24 24" width="30" height="30"><path d="M4 2l16 9-7 2-3 7z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    document.body.appendChild(c);
    window.__mv = (x, y) => { c.style.transform = `translate(${x}px,${y}px)`; };
    window.__rip = (x, y) => { const r = document.createElement('div'); r.className = '__rip'; r.style.left = x + 'px'; r.style.top = y + 'px'; document.body.appendChild(r); setTimeout(() => r.remove(), 700); };
  };
  if (document.body) add(); else document.addEventListener('DOMContentLoaded', add);
})();
"""


def otp_code(timeout=25):
    """Latest 6-digit sign-in code from the API's console email backend."""
    end = time.time() + timeout
    while time.time() < end:
        out = subprocess.run(LOGS, shell=True, capture_output=True, text=True).stdout
        found = re.findall(r"letter-spacing:8px[^>]*>(\d{6})<", out)
        if found:
            return found[-1]
        time.sleep(1)
    raise RuntimeError("no OTP email found in logs")


class Demo:
    def __init__(self, page):
        self.page = page
        self.t0 = time.monotonic()
        self.fast_ranges = []  # (start, end, speed) on the recording timeline

    def fast(self, speed=3.0):
        """Context manager: whatever happens inside is sped up in the final cut."""
        demo = self

        class _F:
            def __enter__(self):
                self.a = demo.now()

            def __exit__(self, *exc):
                demo.fast_ranges.append((self.a, demo.now(), speed))

        return _F()

    def saved(self, since):
        """Seconds the fast ranges after `since` remove from the final cut."""
        return sum((b - a) * (1 - 1 / s) for a, b, s in self.fast_ranges if a >= since)

    # ── timeline ────────────────────────────────────────────────────────
    def now(self):
        return time.monotonic() - self.t0

    def wait(self, s):
        time.sleep(s)

    def wait_until(self, t):
        left = t - self.now()
        if left > 0:
            time.sleep(left)

    # ── pointer ─────────────────────────────────────────────────────────
    def _center(self, loc):
        loc.scroll_into_view_if_needed()
        b = loc.bounding_box()
        return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2

    def move(self, loc):
        x, y = self._center(loc)
        self.page.evaluate("([x,y]) => window.__mv && window.__mv(x,y)", [x, y])
        time.sleep(0.5)
        return x, y

    def click(self, loc):
        x, y = self.move(loc)
        self.page.evaluate("([x,y]) => window.__rip && window.__rip(x,y)", [x, y])
        loc.click()
        time.sleep(0.25)

    def type(self, loc, text, delay=18):
        self.click(loc)
        loc.press_sequentially(text, delay=delay)
        time.sleep(0.3)

    def highlight(self, loc, secs=2.0):
        loc.scroll_into_view_if_needed()
        h = loc.element_handle()
        self.page.evaluate("e => e.classList.add('__hl')", h)
        time.sleep(secs)
        self.page.evaluate("e => e.classList.remove('__hl')", h)

    def scroll(self, dy, secs=2.5, selector=None):
        steps = 25
        for _ in range(steps):
            self.page.mouse.wheel(0, dy / steps)
            time.sleep(secs / steps)

    # ── overlays ────────────────────────────────────────────────────────
    def email_overlay(self, to, code, secs=2.6):
        html = f"""
        <div id="__mail" style="position:fixed;top:28px;left:50%;transform:translateX(-50%) translateY(-140%);z-index:2147483645;
          width:560px;background:#fff;border-radius:16px;box-shadow:0 18px 50px rgba(0,0,0,.35);overflow:hidden;
          font-family:Cairo,Inter,sans-serif;direction:rtl;transition:transform .6s cubic-bezier(.2,.9,.3,1)">
          <div style="background:#254A80;color:#fff;padding:14px 22px;display:flex;justify-content:space-between;align-items:center">
            <b style="font-size:20px">عِمارة<span style="color:#E27A4A">.كوم</span></b><span style="opacity:.8;font-size:14px">بريد جديد</span></div>
          <div style="padding:18px 24px;color:#3B4354">
            <div style="font-size:15px;color:#6B7589;margin-bottom:6px">إلى: <span dir="ltr">{to}</span></div>
            <div style="font-size:17px;margin-bottom:10px">كود تسجيل الدخول الخاص بك:</div>
            <div dir="ltr" style="text-align:center;font-size:44px;font-weight:700;letter-spacing:12px;color:#254A80;background:#EEF3FA;border-radius:12px;padding:10px">{code}</div>
          </div></div>"""
        self.page.evaluate("h => document.body.insertAdjacentHTML('beforeend', h)", html)
        time.sleep(0.1)
        self.page.evaluate("document.getElementById('__mail').style.transform='translateX(-50%) translateY(0)'")
        time.sleep(secs)
        self.page.evaluate("document.getElementById('__mail').style.transform='translateX(-50%) translateY(-140%)'")
        time.sleep(0.7)
        self.page.evaluate("document.getElementById('__mail')?.remove()")

    def card(self, title, sub="", cta=""):
        """Full-screen branded card over whatever is on screen (intro/outro)."""
        html = f"""
        <div id="__card" style="position:fixed;inset:0;z-index:2147483640;background:linear-gradient(135deg,#345F9C,#152D4F);
          display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;padding-bottom:170px;box-sizing:border-box;color:#fff;font-family:Cairo,Inter,sans-serif;
          opacity:0;transition:opacity .7s">
          <svg viewBox="0 0 512 512" width="190" height="190"><g transform="translate(-30 0)">
            <path fill-rule="evenodd" fill="#fff" d="M184 104H304A28 28 0 0 1 332 132V364A28 28 0 0 1 304 392H184A28 28 0 0 1 156 364V132A28 28 0 0 1 184 104Z M194 140H222A10 10 0 0 1 232 150V178A10 10 0 0 1 222 188H194A10 10 0 0 1 184 178V150A10 10 0 0 1 194 140Z M274 140H302A10 10 0 0 1 312 150V178A10 10 0 0 1 302 188H274A10 10 0 0 1 264 178V150A10 10 0 0 1 274 140Z M194 212H222A10 10 0 0 1 232 222V250A10 10 0 0 1 222 260H194A10 10 0 0 1 184 250V222A10 10 0 0 1 194 212Z M274 212H302A10 10 0 0 1 312 222V250A10 10 0 0 1 302 260H274A10 10 0 0 1 264 250V222A10 10 0 0 1 274 212Z M194 284H222A10 10 0 0 1 232 294V322A10 10 0 0 1 222 332H194A10 10 0 0 1 184 322V294A10 10 0 0 1 194 284Z"/>
            <circle cx="352" cy="336" r="64" fill="#E27A4A" stroke="#1C3B67" stroke-width="14"/>
            <path d="M322 338L344 360L384 312" stroke="#0C1018" stroke-width="20" stroke-linecap="round" stroke-linejoin="round" fill="none"/></g></svg>
          <div style="font-size:76px;font-weight:800">{title}</div>
          <div style="font-size:34px;opacity:.9">{sub}</div>
          {f'<div style="margin-top:14px;background:#E27A4A;color:#0C1018;font-size:34px;font-weight:700;padding:14px 46px;border-radius:14px">{cta}</div>' if cta else ''}
        </div>"""
        self.page.evaluate("h => document.body.insertAdjacentHTML('beforeend', h)", html)
        time.sleep(0.1)
        self.page.evaluate("document.getElementById('__card').style.opacity=1")

    def remove_card(self):
        self.page.evaluate("document.getElementById('__card')?.remove()")
