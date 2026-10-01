"""تنظیمات ربات: منابع خبری، کلمات کلیدی و آستانه‌ی اهمیت."""

# ---------------------------------------------------------------------------
# منابع خبری (همه رایگان، از طریق RSS)
# bonus = امتیاز اضافه برای منابع رسمی (بانک‌های مرکزی)
# summary = آیا خلاصه‌ی خبر از RSS برداشته شود
# ---------------------------------------------------------------------------
GNEWS = "https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US:en&q="

FEEDS = [
    # بانک‌های مرکزی
    {"name": "Federal Reserve", "url": "https://www.federalreserve.gov/feeds/press_all.xml", "bonus": 3, "summary": True},
    {"name": "ECB", "url": "https://www.ecb.europa.eu/rss/press.html", "bonus": 3, "summary": True},
    {"name": "Bank of England", "url": "https://www.bankofengland.co.uk/rss/news", "bonus": 2, "summary": True},
    {"name": "Federal Reserve", "url": "https://www.federalreserve.gov/feeds/speeches.xml", "bonus": 3, "summary": False},
    {"name": "Federal Reserve", "url": "https://www.federalreserve.gov/feeds/testimony.xml", "bonus": 3, "summary": False},
    {"name": "Bank of England", "url": "https://www.bankofengland.co.uk/rss/speeches", "bonus": 1, "summary": False},
    {"name": "Bank of Japan", "url": "https://www.boj.or.jp/en/rss/whatsnew.xml", "bonus": 2, "summary": False},
    # اقتصاد و بازارها
    {"name": "Investing.com", "url": "https://www.investing.com/rss/news_14.rss", "bonus": 0, "summary": False},
    {"name": "Investing.com", "url": "https://www.investing.com/rss/news_95.rss", "bonus": 0, "summary": False},
    {"name": "Investing.com", "url": "https://www.investing.com/rss/news_1.rss", "bonus": 0, "summary": False},
    {"name": "Investing.com", "url": "https://www.investing.com/rss/news_287.rss", "bonus": 0, "summary": False},
    {"name": "CNBC", "url": "https://www.cnbc.com/id/20910258/device/rss/rss.html", "bonus": 0, "summary": True},
    {"name": "CNBC", "url": "https://www.cnbc.com/id/100727362/device/rss/rss.html", "bonus": 0, "summary": True},
    {"name": "FXStreet", "url": "https://www.fxstreet.com/rss/news", "bonus": 0, "summary": False},
    {"name": "OilPrice", "url": "https://oilprice.com/rss/main", "bonus": 0, "summary": True},
    {"name": "BBC", "url": "https://feeds.bbci.co.uk/news/business/rss.xml", "bonus": 0, "summary": True},
    # ژئوپلیتیک
    {"name": "BBC", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "bonus": 0, "summary": True},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "bonus": 0, "summary": True},
    {"name": "Iran International", "url": "https://www.iranintl.com/en/feed", "bonus": 0, "summary": False},
    # Reuters و جستجوهای هدفمند از طریق Google News
    {"name": "Google News", "url": GNEWS + "site:reuters.com+when:1h", "bonus": 0, "summary": False},
    {"name": "Google News", "url": GNEWS + "Iran+(oil+OR+sanctions+OR+Hormuz+OR+strike+OR+nuclear)+when:1h", "bonus": 0, "summary": False},
    {"name": "Google News", "url": GNEWS + "(Fed+OR+ECB+OR+%22Bank+of+Japan%22)+rate+when:1h", "bonus": 0, "summary": False},
    {"name": "Google News", "url": GNEWS + "(Warsh+OR+Powell+OR+Lagarde+OR+Ueda+OR+%22Andrew+Bailey%22+OR+%22Fed%27s%22+OR+%22ECB%27s%22+OR+%22BOJ%27s%22)+(says+OR+speech+OR+interview)+when:1h", "bonus": 0, "summary": False},
]

# از نتایج Google News فقط این رسانه‌های معتبر پذیرفته می‌شوند
TRUSTED_GNEWS_SOURCES = {
    "Reuters", "Bloomberg", "Bloomberg.com", "Financial Times", "The Wall Street Journal", "WSJ",
    "AP News", "Associated Press", "CNBC", "BBC", "Al Jazeera", "Axios", "Politico", "The Guardian",
    "MarketWatch", "Barron's", "Nikkei Asia", "The Economist", "Yahoo Finance", "Investing.com",
    "Iran International", "The New York Times", "The Washington Post", "Financial Post", "barchart.com",
}

# تقویم اقتصادی (ForexFactory) — فقط رویدادهای High Impact
CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
CALENDAR_REMINDER_MINUTES = 40   # یادآوری حدوداً X دقیقه قبل از انتشار دیتا
CALENDAR_DIGEST_HOUR = 7         # ساعت ارسال تقویم روزانه (به وقت تهران)

TIMEZONE = "Asia/Tehran"

# مدل‌های Gemini برای ترجمه، به ترتیب (فقط اگر GEMINI_API_KEY تنظیم شده باشد)
GEMINI_MODELS = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]

# ---------------------------------------------------------------------------
# فیلتر اهمیت
# ---------------------------------------------------------------------------
MIN_SCORE = 5            # خبرهایی با امتیاز کمتر پست نمی‌شوند
MAX_AGE_HOURS = 3        # خبرهای قدیمی‌تر نادیده گرفته می‌شوند
MAX_POSTS_PER_RUN = 6    # جلوگیری از سیل پیام در هر اجرا
DUPLICATE_SIMILARITY = 0.5

# سخنرانی و مصاحبه‌ی مقامات بانک‌های مرکزی
CB_SPEAKERS = (
    r"\b(warsh|powell|jefferson|waller|bowman|miran|kashkari|goolsbee|musalem|hammack|"
    r"lagarde|schnabel|villeroy|nagel|de guindos|kazaks|"
    r"ueda|himino|uchida|"
    r"andrew bailey|lombardelli|dhingra|catherine mann|huw pill|"
    r"macklem|bullock|pan gongsheng|schlegel)\b"
    r"|\b(fed|ecb|boj|boe|rba|boc|snb|bundesbank)(’s|'s) [a-z]+"
    r"|\b(fed|ecb|boj|boe|central bank) (chair|chief|governor|president|vice chair|official|policymaker)s?\b"
)

# (الگوی regex، امتیاز)
KEYWORDS = [
    (CB_SPEAKERS, 3),
    (r"\b(speech|interview|testimony|testifies|remarks|press conference)\b", 2),
    # سیاست پولی و دیتاهای کلیدی
    (r"\brate (cut|hike|decision)s?\b|\b(cuts|raises|holds|hikes) (interest )?rates?\b", 4),
    (r"\bfomc\b|\bpowell\b|\blagarde\b|\bueda\b|\bbailey\b", 3),
    (r"\bnon-?farm\b|\bpayrolls?\b|\bjobs report\b", 4),
    (r"\bcpi\b|\binflation\b|\bpce\b|\bppi\b", 3),
    (r"\bgdp\b|\brecession\b|\bunemployment\b|\bjobless\b|\bretail sales\b|\bpmi\b", 3),
    (r"\bfed\b|\bfederal reserve\b|\becb\b|\bboj\b|\bbank of (japan|england|canada)\b|\bpboc\b|\bsnb\b|\brba\b", 2),
    (r"\bintervention\b|\bintervene\b", 3),
    (r"\btreasury yields?\b|\bbond (rout|selloff|sell-off)\b|\bdebt rout\b", 2),
    (r"\bdefault\b|\bbank (run|failure|collapse)\b|\bdowngrade[sd]?\b", 3),
    (r"\btariffs?\b|\btrade war\b|\bexport ban\b", 3),
    # انرژی و کالاها
    (r"\bopec\+?\b|\bcrude\b|\boil (prices?|supply|output|exports?)\b|\bbrent\b|\bwti\b", 3),
    (r"\bgold\b|\bnatural gas\b|\blng\b", 1),
    # ژئوپلیتیک و جنگ
    (r"\bhormuz\b|\bred sea\b|\bhouthis?\b", 4),
    (r"\bmissiles?\b|\bair ?strikes?\b|\bbombing\b|\binvasion\b|\binvade\b|\bdrone attack\b|\bwar\b|\bceasefire\b|\bnuclear\b|\bmilitary\b|\bescalat|\battack(s|ed)?\b|\bstrik(e|es|ing)\b|\baircraft carrier\b|\btroops\b", 3),
    (r"\bsanctions?\b|\bembargo\b", 3),
    (r"\biran(ian)?\b|\bisrael\b|\bsaudi\b|\brussia\b|\bukraine\b|\bputin\b|\btaiwan\b|\bnorth korea\b", 2),
    (r"\btrump\b|\bxi\b|\bwhite house\b|\bkremlin\b", 1),
    (r"\bchina\b|\bjapan\b|\byen\b|\beurozone\b|\bdollar\b|\byuan\b", 1),
    # فوری
    (r"\b(jumps?|soars?|tumbles?|slumps?|sinks?|spikes?|rall(y|ies)|slides?)\b", 2),
    (r"\d+(\.\d+)?%|\bhighest (level|since)|\blowest (level|since)|\bmulti-(year|decade)\b", 1),
    (r"\bbreaking\b|\bexclusive\b|\bemergency\b|\bsurge[sd]?\b|\bplunge[sd]?\b|\bcrash(es|ed)?\b|\bmulti-decade\b|\brecord (high|low)\b", 2),
]

# الگوهایی که امتیاز منفی دارند (تحلیل تکنیکال، سرگرمی و…)
NEGATIVE = [
    (r"price (forecast|prediction|analysis)|technical analysis|elliott wave|live levels|trapped in|chart of the|\bpodcast\b|\bvideo\b|\bopinion\b|\bquiz\b|how to\b|\bsports?\b|\bfootball\b|\bcelebrity\b|\bmovie\b|\bexecution\b", -6),
]

# ---------------------------------------------------------------------------
# برچسب‌ها
# ---------------------------------------------------------------------------
COUNTRY_FLAGS = [
    (r"\b(us|u\.s|united states|american|fed|federal reserve|powell|wall street|treasury|white house|trump)\b", "🇺🇸"),
    (r"\b(japan|japanese|boj|bank of japan|yen|ueda|tokyo)\b", "🇯🇵"),
    (r"\b(euro ?zone|ecb|lagarde|euro|eu|european)\b", "🇪🇺"),
    (r"\b(uk|britain|british|bank of england|boe|sterling|pound)\b", "🇬🇧"),
    (r"\b(china|chinese|pboc|yuan|beijing|xi)\b", "🇨🇳"),
    (r"\b(germany|german)\b", "🇩🇪"),
    (r"\b(canada|canadian|bank of canada)\b", "🇨🇦"),
    (r"\b(australia|australian|rba)\b", "🇦🇺"),
    (r"\b(iran|iranian|tehran)\b", "🇮🇷"),
    (r"\b(israel|israeli)\b", "🇮🇱"),
    (r"\b(russia|russian|putin|kremlin)\b", "🇷🇺"),
    (r"\b(ukraine|ukrainian|zelensky)\b", "🇺🇦"),
    (r"\b(saudi)\b", "🇸🇦"),
]

CATEGORIES = [
    (CB_SPEAKERS, "🎙 سخنرانی بانک مرکزی"),
    (r"\b(fed|federal reserve|ecb|boj|bank of|pboc|fomc|rate (cut|hike|decision)s?|powell|lagarde|ueda)\b", "🏦 بانک مرکزی"),
    (r"\b(war|missiles?|air ?strikes?|military|invasion|ceasefire|nuclear|attack|houthis?|hormuz|drone)\b", "⚔️ ژئوپلیتیک"),
    (r"\b(opec|crude|oil|brent|wti|natural gas|lng|gold)\b", "🛢 انرژی و کالا"),
    (r"\b(cpi|inflation|gdp|payrolls?|non-?farm|unemployment|jobless|pmi|retail sales|ppi|pce)\b", "📊 دیتای اقتصادی"),
    (r"\b(sanctions?|tariffs?|trade war|export ban|embargo)\b", "🚫 تحریم و تعرفه"),
]
DEFAULT_CATEGORY = "📈 بازارها"

CURRENCY_FLAGS = {
    "USD": "🇺🇸", "JPY": "🇯🇵", "EUR": "🇪🇺", "GBP": "🇬🇧", "CNY": "🇨🇳",
    "CAD": "🇨🇦", "AUD": "🇦🇺", "NZD": "🇳🇿", "CHF": "🇨🇭", "ALL": "🌍",
}
