"""Record the app for a tutorial video, paced to the narration.

    python record.py admin|owner

Needs: the demo stack from README.md running, and out/<video>/durations.json
from tts.py. Writes out/<video>/raw.webm and out/<video>/marks.json
(scene start/end seconds on the video timeline).
"""
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from demo import BASE, INIT_JS, Demo, otp_code
from scenes_ar import VIDEOS

OUT = Path(__file__).parent / "out"
W, H = 1600, 900
LEAD, TAIL = 0.35, 0.7  # silence before the narration starts / after it ends
STAMP = str(int(time.time()))[-6:]


def R(p):
    return re.compile(p)


# ── shared steps ───────────────────────────────────────────────────────────
def sign_in(d, email, show_mail=True, logout_after=False):
    """Email → code → dashboard, through the real login screen."""
    p = d.page
    d.type(p.get_by_label("البريد الإلكتروني"), email, delay=40)
    d.click(p.get_by_role("button", name="إرسال الكود"))
    p.wait_for_selector("input[autocomplete=one-time-code]")
    code = otp_code()
    if show_mail:
        d.email_overlay(email, code)
    d.type(p.locator("input[autocomplete=one-time-code]"), code, delay=45)
    d.click(p.get_by_role("button", name="تحقق وسجّل الدخول"))
    p.wait_for_url("**/dashboard", timeout=15000)
    d.wait(1.2)


def sign_out(d):
    p = d.page
    d.click(p.get_by_role("button", name="الحساب"))
    d.click(p.get_by_role("menuitem", name="تسجيل الخروج"))
    p.wait_for_url("**/login", timeout=10000)
    d.wait(0.8)


def fresh_browser_state(d):
    """Forget the session (not the trusted-device cookie logic: cleared too)."""
    d.page.context.clear_cookies()
    d.page.evaluate("localStorage.clear(); sessionStorage.clear()")


def goto_link(d, href):
    d.click(d.page.locator(f'a[href="{href}"]').first)
    d.wait(1.5)


def register_account(d, first, last, role_label, email):
    p = d.page
    d.type(p.get_by_label("الاسم الأول"), first)
    d.type(p.get_by_label("اسم العائلة"), last)
    d.type(p.get_by_label("البريد الإلكتروني"), email, delay=16)
    d.click(p.get_by_label(R(role_label)))
    d.click(p.get_by_role("checkbox"))


def submit_register_and_code(d, email):
    p = d.page
    d.click(p.get_by_role("button", name="متابعة"))
    p.wait_for_selector("input[autocomplete=one-time-code]", timeout=15000)
    code = otp_code()
    d.email_overlay(email, code)
    d.type(p.locator("input[autocomplete=one-time-code]"), code, delay=45)
    d.click(p.get_by_role("button", name="تحقق وسجّل الدخول"))
    d.wait(1.5)


# ── admin scenes ───────────────────────────────────────────────────────────
def a01(d):
    p = d.page
    p.goto(BASE + "/landing")
    d.wait(3)
    d.highlight(p.get_by_role("link", name="ابدأ مجاناً").or_(p.get_by_role("button", name="ابدأ مجاناً")), 3)


def a02(d):
    p = d.page
    d.click(p.get_by_role("link", name="ابدأ مجاناً").or_(p.get_by_role("button", name="ابدأ مجاناً")))
    p.wait_for_url("**/register**")
    d.wait(0.6)
    register_account(d, "كريم", "العدل", "مدير", f"karim.{STAMP}@example.com")


def a03(d):
    submit_register_and_code(d, f"karim.{STAMP}@example.com")


def a04(d):
    p = d.page
    d.type(p.get_by_label(R("اسم المبنى")), "برج الياسمين")
    d.type(p.get_by_label(R("العنوان")), "١٢ شارع الجمهورية")
    d.type(p.get_by_label(R("المدينة")), "الإسكندرية")
    d.type(p.get_by_label(R("الطوابق")), "6")
    d.type(p.get_by_label(R("الشقق")), "12")
    d.type(p.get_by_label(R("المحلات")), "2")
    d.click(p.get_by_role("button", name="حفظ ومتابعة"))
    d.wait(1.2)
    d.click(p.get_by_role("button", name="تخطي الآن"))
    d.wait(1.5)


def a05(d):
    p = d.page
    fresh_browser_state(d)
    p.goto(BASE + "/login")
    d.wait(1.0)
    sign_in(d, "admin@abem.test")
    with d.fast(3.0):
        sign_out(d)
    # trusted device: same browser, no code this time
    d.type(p.get_by_label("البريد الإلكتروني"), "admin@abem.test", delay=16)
    d.click(p.get_by_role("button", name="إرسال الكود"))
    p.wait_for_url("**/dashboard", timeout=15000)
    d.wait(1.0)


def a06(d):
    p = d.page
    d.highlight(p.get_by_text("رصيد الخزينة الحالي").first.locator("xpath=../.."), 2.2)
    d.scroll(520, 2.5)
    d.scroll(-520, 1.2)


def a07(d):
    p = d.page
    goto_link(d, "/buildings")
    d.click(p.get_by_role("button", name="إدارة الوحدات").first)
    d.wait(1.2)
    row = p.get_by_role("row", name=R("201")).first
    d.highlight(row, 1.5)
    d.click(row.locator("button:has(svg[data-testid='SendIcon'])"))
    d.wait(1.5)
    d.highlight(p.get_by_role("button", name=R("واتساب")), 2.5)
    d.wait(1.5)
    d.click(p.get_by_role("button", name="إغلاق"))
    d.wait(0.6)


def a08(d):
    p = d.page
    goto_link(d, "/expenses")
    d.click(p.get_by_role("button", name=R("إضافة مصروف")))
    d.wait(0.8)
    dlg = p.get_by_role("dialog")
    d.type(dlg.get_by_label(R("العنوان")), "صيانة المصعد")
    d.type(dlg.get_by_label(R("المبلغ")), "2500")
    d.click(dlg.locator("[role=combobox]").first)
    d.click(p.get_by_role("option").first)
    d.highlight(dlg.locator("[role=combobox]").nth(1), 2.5)
    d.wait(1)
    d.click(dlg.get_by_role("button", name="إلغاء"))
    d.wait(0.6)


def a09(d):
    p = d.page
    goto_link(d, "/payments")
    d.wait(2)
    goto_link(d, "/dashboard")
    d.highlight(p.get_by_role("button", name="تأكيد").first, 2.5)


def a10(d):
    goto_link(d, "/maintenance")
    d.wait(1.8)
    goto_link(d, "/polls")
    d.wait(1.8)
    goto_link(d, "/notifications")
    d.wait(1.8)


def a11(d):
    goto_link(d, "/statement")
    d.wait(1.5)
    d.scroll(500, 2.5)


def a12(d):
    d.card("عِمارة<span style='color:#E27A4A'>.كوم</span>", "راحة بال ليك ولجيرانك", "ابدأ دلوقتي")
    d.wait(3)


# ── owner scenes ───────────────────────────────────────────────────────────
def make_invites():
    """Create two fresh unit invites in the demo DB: (token, code) for each."""
    code = (
        "from apps.apartments.models import Apartment, UnitInvitation\n"
        "from django.utils import timezone\nfrom datetime import timedelta\n"
        "from apps.authentication.models import User\n"
        "from apps.buildings.models import Building\n"
        "Building.objects.filter(admin__email__endswith='@example.com').delete()  # leftovers of earlier takes\n"
        "User.objects.filter(email__endswith='@example.com').delete()\n"
        "for a in Apartment.objects.filter(building__name='برج النيل', owner__isnull=True)[:2]:\n"
        "    UnitInvitation.objects.filter(apartment=a).delete()\n"
        "    i = UnitInvitation.objects.create(apartment=a, expires_at=timezone.now()+timedelta(days=30))\n"
        "    print('INV', i.token, i.registration_code)"
    )
    out = subprocess.run(
        ["docker", "exec", "abem-demo-backend", "python", "manage.py", "shell", "-c", code],
        capture_output=True, text=True,
    )
    found = re.findall(r"INV ([0-9a-f-]{36}) (\w{8})", out.stdout)
    if len(found) < 2:
        raise RuntimeError(out.stdout + out.stderr)
    return found


def o01(d):
    p = d.page
    p.goto(BASE + "/landing")
    d.wait(3)
    d.highlight(p.get_by_role("link", name="ابدأ مجاناً").or_(p.get_by_role("button", name="ابدأ مجاناً")), 3)


def o02(d):
    p = d.page
    p.goto(BASE + f"/join/{d.invites[0][0]}")
    d.wait(3)
    d.click(p.get_by_role("link", name=R("إنشاء حساب")).or_(p.get_by_role("button", name=R("إنشاء حساب"))))
    p.wait_for_url("**/register**")


def o03(d):
    email = f"mona.{STAMP}@example.com"
    p = d.page
    with d.fast(2.5):
        d.type(p.get_by_label("الاسم الأول"), "منى")
        d.type(p.get_by_label("اسم العائلة"), "سعيد")
        d.type(p.get_by_label("البريد الإلكتروني"), email, delay=16)
        d.click(p.get_by_role("checkbox"))
    submit_register_and_code(d, email)
    d.click(p.get_by_role("button", name=R("انضم إلى وحدتك")))
    d.wait(2)


def o04(d):
    p = d.page
    fresh_browser_state(d)
    p.goto(BASE + "/register")
    d.wait(1)
    email = f"hany.{STAMP}@example.com"
    with d.fast(3.5):
        register_account(d, "هاني", "فتحي", "مالك", email)
        submit_register_and_code(d, email)
    d.type(p.get_by_label(R("كود التسجيل")), d.invites[1][1])
    d.click(p.get_by_role("button", name="تحقق"))
    d.wait(1.5)
    p.screenshot(path=str(OUT / "debug_o04.png"))
    d.wait(1.5)


def o05(d):
    p = d.page
    fresh_browser_state(d)
    p.goto(BASE + "/login")
    d.wait(1.5)
    d.highlight(p.locator("iframe[src*='accounts.google.com']").first, 1.8)
    sign_in(d, "owner@abem.test")
    with d.fast(3.0):
        sign_out(d)
    d.type(p.get_by_label("البريد الإلكتروني"), "owner@abem.test", delay=16)
    d.click(p.get_by_role("button", name="إرسال الكود"))
    p.wait_for_url("**/dashboard", timeout=15000)
    d.wait(1.0)


def o06(d):
    d.scroll(450, 2.5)
    d.scroll(-450, 1.2)


def o07(d):
    goto_link(d, "/expenses")
    d.scroll(300, 2)


def o08(d):
    goto_link(d, "/payments")
    d.wait(3)


def o09(d):
    goto_link(d, "/maintenance")
    d.wait(3)


def o10(d):
    goto_link(d, "/polls")
    d.wait(1.8)
    goto_link(d, "/notifications")
    d.wait(1.8)


def o11(d):
    goto_link(d, "/statement")
    d.scroll(500, 2.5)


def o12(d):
    d.card("عِمارة<span style='color:#E27A4A'>.كوم</span>", "راحة بال ليك ولجيرانك", "ثبّت التطبيق على موبايلك")
    d.wait(3)


SCENES = {k: v for k, v in globals().items() if re.fullmatch(r"[ao]\d\d", k)}


def main(video):
    out = OUT / video
    durs = json.loads((out / "durations.json").read_text())
    only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    vid_dir = out / "rec"
    shutil.rmtree(vid_dir, ignore_errors=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": W, "height": H}, locale="ar-EG",
            record_video_dir=str(vid_dir), record_video_size={"width": W, "height": H},
        )
        ctx.add_init_script(INIT_JS)
        page = ctx.new_page()
        d = Demo(page)
        if video == "owner":
            d.invites = make_invites()
        marks = {}
        page.goto(BASE + "/login")
        d.wait(0.3)
        for sid, _ in VIDEOS[video]:
            if only and sid not in only:
                continue
            start = d.now()
            try:
                SCENES[sid](d)
            except Exception:
                page.screenshot(path=str(out / f"fail_{sid}.png"))
                raise
            end = max(d.now(), start + d.saved(start) + LEAD + durs[sid] + TAIL)
            d.wait_until(end)
            marks[sid] = {"start": round(start, 3), "end": round(end, 3)}
            print(sid, marks[sid])
        ctx.close()
        browser.close()
    (out / "marks.json").write_text(json.dumps({"scenes": marks, "fast": d.fast_ranges}, indent=2))
    webm = next(vid_dir.glob("*.webm"))
    shutil.move(str(webm), out / "raw.webm")
    shutil.rmtree(vid_dir, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1])
