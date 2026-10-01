"""ربات خبری اقتصاد و ژئوپلیتیک برای تلگرام.

هر بار اجرا:
  1. اخبار را از منابع RSS می‌خواند
  2. خبرهای مهم را با سیستم امتیازدهی جدا می‌کند و تکراری‌ها را حذف می‌کند
  3. به فارسی ترجمه می‌کند و در کانال تلگرام پست می‌کند
  4. تقویم اقتصادی (رویدادهای High Impact) را یادآوری می‌کند

متغیرهای محیطی:
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID  — اجباری (مگر در حالت DRY_RUN)
  GEMINI_API_KEY  — اختیاری؛ ترجمه‌ی باکیفیت‌تر با Gemini (رایگان)
  DRY_RUN=1  — به جای ارسال، پیام‌ها را چاپ می‌کند
"""

import calendar
import hashlib
import html
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import feedparser
import requests

import config

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state", "seen.json")
USER_AGENT = "Mozilla/5.0 (compatible; EconNewsBot/1.0)"
DRY_RUN = os.environ.get("DRY_RUN") == "1"
TZ = ZoneInfo(config.TIMEZONE)
NOW = datetime.now(timezone.utc)

STOPWORDS = set("the a an of to in on for and or at by with from as is are be after over says said will its it that this new us".split())

CALENDAR_GLOSSARY = {
    "CPI": "تورم مصرف‌کننده (CPI)",
    "Core CPI": "تورم هسته (Core CPI)",
    "Non-Farm Employment Change": "اشتغال غیرکشاورزی (NFP)",
    "Unemployment Rate": "نرخ بیکاری",
    "Federal Funds Rate": "نرخ بهره‌ی فدرال رزرو",
    "FOMC Statement": "بیانیه‌ی FOMC",
    "FOMC Press Conference": "کنفرانس خبری FOMC",
    "FOMC Meeting Minutes": "صورت‌جلسه‌ی FOMC",
    "Main Refinancing Rate": "نرخ بهره‌ی بانک مرکزی اروپا",
    "Official Bank Rate": "نرخ بهره‌ی بانک مرکزی انگلیس",
    "BOJ Policy Rate": "نرخ بهره‌ی بانک مرکزی ژاپن",
    "Advance GDP": "تولید ناخالص داخلی (GDP) – اولیه",
    "GDP": "تولید ناخالص داخلی (GDP)",
    "Retail Sales": "خرده‌فروشی",
    "Core PCE Price Index": "شاخص قیمت PCE هسته",
    "ISM Manufacturing PMI": "PMI تولیدی ISM",
    "ISM Services PMI": "PMI خدماتی ISM",
    "Unemployment Claims": "مدعیان بیکاری هفتگی",
    "Average Hourly Earnings": "میانگین دستمزد ساعتی",
    "JOLTS Job Openings": "فرصت‌های شغلی JOLTS",
    "PPI": "تورم تولیدکننده (PPI)",
    "CPI m/m": "تورم ماهانه (CPI)",
    "CPI y/y": "تورم سالانه (CPI)",
    "Core CPI m/m": "تورم هسته‌ی ماهانه (Core CPI)",
    "Core PCE Price Index m/m": "شاخص قیمت PCE هسته – ماهانه",
    "Average Hourly Earnings m/m": "میانگین دستمزد ساعتی – ماهانه",
    "Cash Rate": "نرخ بهره",
    "Final GDP q/q": "تولید ناخالص داخلی (GDP) – نهایی",
    "Advance GDP q/q": "تولید ناخالص داخلی (GDP) – اولیه",
    "Retail Sales m/m": "خرده‌فروشی – ماهانه",
    "Core Retail Sales m/m": "خرده‌فروشی هسته – ماهانه",
    "PPI m/m": "تورم تولیدکننده (PPI) – ماهانه",
}


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_state(state):
    cutoff = (NOW - timedelta(days=3)).timestamp()
    state["seen"] = {k: v for k, v in state["seen"].items() if v > cutoff}
    day_cutoff = (NOW - timedelta(hours=24)).timestamp()
    state["recent_titles"] = [t for t in state["recent_titles"] if t[1] > day_cutoff]
    state["calendar_sent"] = {k: v for k, v in state["calendar_sent"].items() if v > cutoff}
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def item_id(link, title):
    return hashlib.sha1((link or title).encode("utf-8")).hexdigest()[:16]


def clean_text(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def shorten(text, limit=350):
    """خلاصه را در انتهای یک جمله کوتاه می‌کند."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = cut.rfind(". ")
    return cut[: end + 1] if end > 100 else cut.rsplit(" ", 1)[0] + "…"


def title_words(title):
    words = re.findall(r"[a-z0-9]+", title.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def is_duplicate(title, recent_titles):
    words = title_words(title)
    if not words:
        return False
    for other in recent_titles:
        other_words = set(other)
        overlap = len(words & other_words) / max(1, min(len(words), len(other_words)))
        if overlap >= config.DUPLICATE_SIMILARITY and len(words & other_words) >= 3:
            return True
    return False


def score(text, bonus):
    text = text.lower()
    total = bonus
    for pattern, points in config.KEYWORDS + config.NEGATIVE:
        if re.search(pattern, text):
            total += points
    return total


def first_match(text, rules, default=""):
    text = text.lower()
    for pattern, label in rules:
        if re.search(pattern, text):
            return label
    return default


def flags_for(text):
    text = text.lower()
    found = []
    for pattern, flag in config.COUNTRY_FLAGS:
        if re.search(pattern, text) and flag not in found:
            found.append(flag)
    return "".join(found[:3]) or "🌍"


def published_at(entry):
    for key in ("published_parsed", "updated_parsed"):
        if entry.get(key):
            return datetime.fromtimestamp(calendar.timegm(entry[key]), timezone.utc)
    return None


GEMINI_PROMPT = (
    "Translate this financial/geopolitical news text into fluent, simple Persian (Farsi) "
    "in a news-agency style. Keep tickers, numbers and percentages exact. "
    "Output only the translation.\n\n"
)


def translate_gemini(text):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    for model in config.GEMINI_MODELS:
        try:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": key},
                json={
                    "contents": [{"parts": [{"text": GEMINI_PROMPT + text}]}],
                    "generationConfig": {"thinkingConfig": {"thinkingLevel": "low"}},
                },
                timeout=60,
            )
            resp.raise_for_status()
            parts = resp.json()["candidates"][0]["content"]["parts"]
            result = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
            if result:
                return result
        except Exception as e:  # noqa: BLE001
            print(f"  gemini {model} failed: {e}", file=sys.stderr)
    return None


def translate_google(text):
    resp = requests.get(
        "https://translate.googleapis.com/translate_a/single",
        params={"client": "gtx", "sl": "en", "tl": "fa", "dt": "t", "q": text[:4500]},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    resp.raise_for_status()
    return "".join(part[0] for part in resp.json()[0] if part[0])


def translate_mymemory(text):
    params = {"q": text[:480], "langpair": "en|fa"}
    if os.environ.get("MYMEMORY_EMAIL"):
        params["de"] = os.environ["MYMEMORY_EMAIL"]  # سهمیه‌ی روزانه را ۱۰ برابر می‌کند
    resp = requests.get(
        "https://api.mymemory.translated.net/get",
        params=params,
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("responseStatus") != 200 or data.get("quotaFinished"):
        raise RuntimeError(data.get("responseDetails") or "quota finished")
    return data["responseData"]["translatedText"]


def translate(text):
    """ترجمه با زنجیره‌ی سرویس‌های رایگان. در صورت شکست همه، None برمی‌گرداند."""
    if not text:
        return ""
    for name, fn in (("gemini", translate_gemini), ("google", translate_google), ("mymemory", translate_mymemory)):
        try:
            result = fn(text)
            if result:
                time.sleep(0.5)
                return result
        except Exception as e:  # noqa: BLE001
            print(f"  translate via {name} failed: {e}", file=sys.stderr)
    return None


def send(text):
    if DRY_RUN:
        print("-" * 60 + "\n" + text + "\n")
        return True
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
        timeout=20,
    )
    if resp.status_code == 429:
        wait = resp.json().get("parameters", {}).get("retry_after", 30)
        time.sleep(wait)
        return send(text)
    if not resp.ok:
        print(f"  telegram error {resp.status_code}: {resp.text}", file=sys.stderr)
    time.sleep(3)
    return resp.ok


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------
def fetch_candidates():
    items = []
    for feed in config.FEEDS:
        try:
            raw = requests.get(feed["url"], headers={"User-Agent": USER_AGENT}, timeout=20).content
            parsed = feedparser.parse(raw)
        except Exception as e:  # noqa: BLE001
            print(f"feed error {feed['url']}: {e}", file=sys.stderr)
            continue
        for entry in parsed.entries:
            title = clean_text(entry.get("title"))
            source = feed["name"]
            if source == "Google News" and " - " in title:
                title, source = title.rsplit(" - ", 1)
                if source not in config.TRUSTED_GNEWS_SOURCES:
                    continue
            summary = clean_text(entry.get("summary")) if feed["summary"] else ""
            if summary.lower().startswith(title.lower()[:40]):
                summary = ""
            items.append({
                "id": item_id(entry.get("link"), title),
                "title": title,
                "summary": shorten(summary),
                "link": entry.get("link", ""),
                "source": source,
                "published": published_at(entry),
                "score": score(f"{title} {summary}", feed["bonus"]),
            })
    return items


def format_news(item, title_fa, summary_fa):
    text = f"{item['title']} {item['summary']}"
    category = first_match(text, config.CATEGORIES, config.DEFAULT_CATEGORY)
    urgent = "🔴 فوری | " if item["score"] >= 9 else ""
    lines = [f"{urgent}{category} {flags_for(text)}", "", f"<b>{html.escape(title_fa)}</b>"]
    if summary_fa:
        lines += ["", html.escape(summary_fa)]
    lines += ["", f"📰 منبع: {html.escape(item['source'])}"]
    return "\n".join(lines)


def process_news(state):
    items = fetch_candidates()
    print(f"fetched {len(items)} items")
    max_age = NOW - timedelta(hours=config.MAX_AGE_HOURS)
    candidates = []
    for it in items:
        if it["id"] in state["seen"]:
            continue
        if it["published"] and it["published"] < max_age:
            state["seen"][it["id"]] = NOW.timestamp()
            continue
        if it["score"] < config.MIN_SCORE:
            state["seen"][it["id"]] = NOW.timestamp()
            continue
        candidates.append(it)

    candidates.sort(key=lambda x: x["score"], reverse=True)
    recent = [t[0] for t in state["recent_titles"]]
    posted = 0
    for it in candidates:
        if posted >= config.MAX_POSTS_PER_RUN:
            break  # بقیه در اجرای بعدی بررسی می‌شوند
        if is_duplicate(it["title"], recent):
            state["seen"][it["id"]] = NOW.timestamp()
            continue
        title_fa = translate(it["title"])
        if title_fa is None:
            print("translation unavailable, stopping this run", file=sys.stderr)
            break  # ترجمه در دسترس نیست؛ اجرای بعدی دوباره تلاش می‌کند
        summary_fa = translate(it["summary"]) or ""
        print(f"[{it['score']}] {it['title']}")
        if send(format_news(it, title_fa, summary_fa)):
            words = sorted(title_words(it["title"]))
            recent.append(words)
            state["recent_titles"].append([words, NOW.timestamp()])
            state["seen"][it["id"]] = NOW.timestamp()
            posted += 1
    print(f"posted {posted} news")


# ---------------------------------------------------------------------------
# Economic calendar
# ---------------------------------------------------------------------------
def event_name(title):
    return CALENDAR_GLOSSARY.get(title, title)


def fetch_calendar():
    try:
        resp = requests.get(config.CALENDAR_URL, headers={"User-Agent": USER_AGENT}, timeout=20)
        resp.raise_for_status()
        events = resp.json()
    except Exception as e:  # noqa: BLE001
        print(f"calendar error: {e}", file=sys.stderr)
        return None
    out = []
    for ev in events:
        if ev.get("impact") != "High":
            continue
        try:
            ev["dt"] = datetime.fromisoformat(ev["date"]).astimezone(timezone.utc)
        except (KeyError, ValueError):
            continue
        out.append(ev)
    return out


def process_calendar(state):
    events = fetch_calendar()
    if events is None:
        return  # تقویم در دسترس نیست؛ اجرای بعدی دوباره تلاش می‌کند
    local_now = NOW.astimezone(TZ)
    today = local_now.date().isoformat()

    # تقویم روزانه — یک بار در روز
    if local_now.hour >= config.CALENDAR_DIGEST_HOUR and state.get("digest_date") != today:
        todays = [e for e in events if e["dt"].astimezone(TZ).date() == local_now.date()]
        lines = [f"📅 <b>تقویم اقتصادی امروز — رویدادهای پرتأثیر</b>", f"({today}، به وقت تهران)", ""]
        if todays:
            for e in sorted(todays, key=lambda x: x["dt"]):
                t = e["dt"].astimezone(TZ).strftime("%H:%M")
                flag = config.CURRENCY_FLAGS.get(e["country"], "🌍")
                extra = []
                if e.get("forecast"):
                    extra.append(f"پیش‌بینی: {e['forecast']}")
                if e.get("previous"):
                    extra.append(f"قبلی: {e['previous']}")
                suffix = f" — {' | '.join(extra)}" if extra else ""
                lines.append(f"⏰ {t} {flag} <b>{html.escape(event_name(e['title']))}</b>{html.escape(suffix)}")
        else:
            lines.append("امروز رویداد اقتصادی پرتأثیری در تقویم نیست.")
        if send("\n".join(lines)):
            state["digest_date"] = today

    # یادآوری قبل از انتشار هر دیتا
    for e in events:
        minutes = (e["dt"] - NOW).total_seconds() / 60
        key = item_id(None, f"{e['country']}|{e['title']}|{e['date']}")
        if 0 < minutes <= config.CALENDAR_REMINDER_MINUTES and key not in state["calendar_sent"]:
            flag = config.CURRENCY_FLAGS.get(e["country"], "🌍")
            t = e["dt"].astimezone(TZ).strftime("%H:%M")
            lines = [
                f"⏳ <b>یادآوری دیتای مهم</b> {flag}",
                "",
                f"<b>{html.escape(event_name(e['title']))}</b> ({e['country']})",
                f"🕐 ساعت {t} به وقت تهران (حدود {int(minutes)} دقیقه دیگر)",
            ]
            if e.get("forecast"):
                lines.append(f"🎯 پیش‌بینی: {html.escape(e['forecast'])}")
            if e.get("previous"):
                lines.append(f"↩️ قبلی: {html.escape(e['previous'])}")
            if send("\n".join(lines)):
                state["calendar_sent"][key] = NOW.timestamp()


# ---------------------------------------------------------------------------
def main():
    state = load_state()
    if state is None or not state.get("seen"):
        # اجرای اول: همه‌ی خبرهای فعلی را «دیده‌شده» علامت می‌زنیم تا کانال پر از خبر قدیمی نشود
        state = {"seen": {}, "recent_titles": [], "calendar_sent": {}, "digest_date": None}
        for it in fetch_candidates():
            state["seen"][it["id"]] = NOW.timestamp()
        save_state(state)
        print(f"bootstrap: marked {len(state['seen'])} items as seen")
        if not os.environ.get("SKIP_BOOTSTRAP_MSG"):
            send("✅ ربات خبری فعال شد. از این لحظه اخبار مهم اقتصادی و ژئوپلیتیک اینجا منتشر می‌شود.")
        return

    process_calendar(state)
    process_news(state)
    save_state(state)


if __name__ == "__main__":
    main()
