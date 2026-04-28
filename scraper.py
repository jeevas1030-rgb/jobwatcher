import hashlib
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# Playwright (headless browser for JS-heavy sites)
# ---------------------------------------------------------------------------
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}
JSON_HEADERS = {"User-Agent": "JobWatchPro/1.0", "Accept": "application/json"}

# ---------------------------------------------------------------------------
# COMPANY → ATS SLUG MAPS  (Greenhouse & Lever public APIs, no auth needed)
# ---------------------------------------------------------------------------
GREENHOUSE_COMPANIES = {
    # Unicorns / Top Startups
    "freshworks": "freshworks",
    "razorpay": "razorpay",
    "zepto": "zepto",
    "groww": "groww",
    "meesho": "meesho",
    "chargebee": "chargebee",
    "clevertap": "clevertap",
    "browserstack": "browserstack",
    "postman": "postmanlabs",
    "hasura": "hasura",
    "khatabook": "khatabook",
    "unacademy": "unacademy",
    "cred": "dreamplug",
    "darwinbox": "darwinbox",
    "sprinklr": "sprinklr",
    "swiggy": "swiggy",
    "slice": "slicecard",
    "jupiter": "jupitermoney",
    "kreditbee": "kreditbee",
    "moneyview": "moneyview",
    "lendingkart": "lendingkart",
    "spinny": "spinny",
    "urban company": "urbanclap",
    "purplle": "purplle",
    "milkbasket": "milkbasket",
    # Chennai / South India
    "aspire": "aspiresystems",
    "payoda": "payoda",
    "m2p": "m2pfintech",
    # Service Companies
    "coforge": "coforge",
    "nagarro": "nagarro",
    "zensar": "zensar",
    "happiest minds": "happiestminds",
    # AI
    "yellow": "yellowmessenger",
    "haptik": "haptik",
    "uniphore": "uniphore",
    "observe": "observeai",
}

LEVER_COMPANIES = {
    "flipkart": "flipkart",
    "phonepe": "phonepe",
    "nykaa": "nykaa",
    "sharechat": "sharechat",
    "moengage": "moengage",
    "innovaccer": "innovaccer",
    "locus": "locus",
    "leadsquared": "leadsquared",
    "ather": "ather-energy",
    "zomato": "zomato",
    "licious": "licious",
    "physics wallah": "physicswallah",
    "bharatpe": "bharatpe",
    "fi money": "epifi",
    "tata elxsi": "tata-elxsi",
    "sasken": "sasken",
    "birlasoft": "birlasoft",
    "cyient": "cyient",
    "gnani": "gnani",
    "koinx": "koinx",
    "navi": "navi",
    "jar": "jar-app",
    "fibe": "earlysalary",
    "rupeek": "rupeek",
    "dunzo": "dunzo",
}

# ---------------------------------------------------------------------------
# JS-RENDERED SITES — need Playwright headless browser
# ---------------------------------------------------------------------------
JS_SITES = [
    "accenture.com",
    "wipro.com",
    "careers.tcs.com", "tcs.com",
    "infosys.com", "career.infosys.com",
    "cognizant.com",
    "capgemini.com",
    "techmahindra.com",
    "hcltech.com",
    "ltimindtree.com",
    "naukri.com",
    "amazon.jobs",
    "careers.microsoft.com",
    "careers.google.com",
    "linkedin.com",
    "mphasis.com",
    "hexaware.com",
    "slkgroup.com",
    "itcinfotech.com",
    "zoho.com",
    "kpit.com",
    "sonata-software.com",
    "kellton.com",
    "trigent.com",
    "ramco.com",
    "solitontech.com",
    "movate.com",
]

# ---------------------------------------------------------------------------
# KEYWORD FILTERS
# ---------------------------------------------------------------------------
# Jobs must contain at least one of these
JOB_KEYWORDS = [
    "software engineer", "software developer", "sde", "swe",
    "web developer", "web engineer", "full stack", "fullstack",
    "frontend", "front-end", "backend", "back-end",
    "application developer", "application engineer",
    "data scientist", "data analyst", "data engineer",
    "machine learning", "ml engineer", "ai engineer", "deep learning",
    "devops", "cloud engineer", "site reliability", "sre",
    "android developer", "ios developer", "mobile developer",
    "flutter", "react native", "react developer", "angular", "vue",
    "python developer", "java developer", ".net developer", "golang",
    "ui developer", "ux designer", "ui/ux", "product designer",
    "qa engineer", "test engineer", "sdet", "automation engineer",
    "security analyst", "security engineer", "cybersecurity",
    "network engineer", "infrastructure engineer",
    "sql developer", "database", "etl developer",
    "salesforce", "sap developer", "rpa developer",
    "intern", "internship", "trainee", "fresher",
    "graduate engineer", "graduate trainee",
    "junior developer", "junior engineer",
    "associate developer", "associate engineer", "associate software",
    "entry level", "entry-level",
    "technology analyst", "it analyst", "technical analyst",
    "specialist programmer", "programmer analyst",
    "business analyst", "systems engineer", "systems analyst",
    "developer", "engineer", "analyst", "programmer",
]

# Titles containing these words are SENIOR roles — reject them
SENIOR_WORDS = {
    "senior", "sr", "lead", "manager", "architect",
    "principal", "director", "vp", "chief", "head",
    "distinguished", "fellow", "staff", "expert",
    "consultant",  # usually requires 3+ yrs
}

# Garbage UI text — reject these
GARBAGE = [
    "terms and conditions", "terms of use", "cookie policy",
    "privacy policy", "cookie consent", "functional cookie",
    "required cookie", "fraud awareness", "legal notice",
    "disclaimer", "copyright",
    "home", "log in", "sign in", "sign up", "register",
    "explore now", "know more", "read more", "learn more",
    "view all", "show all", "load more", "join now",
    "join our", "talent network", "follow us", "subscribe",
    "search jobs", "filter", "sort by", "filters -",
    "life at", "about us", "contact us", "our culture",
    "diversity", "inclusion", "sustainability",
    "experienced professional", "early careers page",
    "uk and ireland", "germany and austria", "southern europe",
    "benelux", "nordics", "romania", "portugal", "poland",
    "français", "español", "deutsch", "italiano", "português",
    "polski", "العرب", "日本語", "简体中文",
    "wipro.com", "apply now", "save job",
    "job alerts", "email me", "set up alert",
    "back to results", "return to search",
]

# ---------------------------------------------------------------------------
# REGEX
# ---------------------------------------------------------------------------
EXP_RE = re.compile(
    r'(\d+)\s*[-–to]+\s*(\d+)\s*(?:years?|yrs?)|'
    r'(\d+)\s*\+?\s*(?:years?|yrs?)|'
    r'\bfresher\b|\bentry.?level\b',
    re.IGNORECASE
)

DATE_WORDS_RE = re.compile(
    r'(\d+)\s*(day|hour|hr|minute|min|week|month)s?\s*ago|'
    r'\btoday\b|\bjust\s*now\b|\bposted\s*today\b',
    re.IGNORECASE
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def fingerprint(text: str) -> str:
    return hashlib.md5(text.strip().lower().encode()).hexdigest()


def is_garbage(text: str) -> bool:
    lower = text.lower().strip()
    if len(lower) < 8 or len(lower) > 220:
        return True
    if len(lower.split()) < 2:
        return True
    for phrase in GARBAGE:
        if phrase in lower:
            return True
    if sum(1 for c in lower if c.isascii() and c.isalpha()) < 5:
        return True
    if "\n" in text or "\t" in text:
        return True
    return False


def is_senior(title: str) -> bool:
    """Reject titles that are clearly senior/experienced roles."""
    words = set(re.sub(r"[^\w\s]", " ", title.lower()).split())
    return bool(words & SENIOR_WORDS)


def matches_job(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in JOB_KEYWORDS)


def get_exp(text: str) -> str | None:
    m = EXP_RE.search(text)
    if not m:
        return None
    if m.group(1) is not None and m.group(2) is not None:
        lo, hi = int(m.group(1)), int(m.group(2))
        return f"{lo}-{hi} yrs"
    if m.group(3) is not None:
        n = int(m.group(3))
        return f"{n} yr" if n == 1 else f"{n} yrs"
    lower = text.lower()
    if "fresher" in lower:
        return "Fresher"
    if "entry" in lower:
        return "Entry Level"
    return None


def is_fresher_friendly(exp: str) -> bool:
    """
    Allow if experience STARTS from 0 or 1:
      0-2 ✅  0-5 ✅  0-8 ✅  1-3 ✅  1 yr ✅  Fresher ✅
      2-5 ❌  3-6 ❌  2 yrs ❌  5+ yrs ❌
    """
    if not exp or exp in ("Fresher", "Entry Level", "Not specified"):
        return True
    # Range like "0-5 yrs"
    range_m = re.search(r"(\d+)\s*-\s*(\d+)", exp)
    if range_m:
        return int(range_m.group(1)) <= 1
    # Single value like "2 yrs"
    single_m = re.search(r"(\d+)", exp)
    if single_m:
        return int(single_m.group(1)) <= 1
    return True


def clean_description(raw: str, max_len: int = 200) -> str:
    """Strip HTML, return first N chars of clean text."""
    if not raw:
        return ""
    if "<" in raw:
        soup = BeautifulSoup(raw, "html.parser")
        text = soup.get_text(" ", strip=True)
    else:
        text = raw
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0] + "…"
    return text


def format_posted(dt: datetime | None) -> str | None:
    """
    Convert datetime to human label. Returns None = too old (> 2 days).
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = datetime.now(timezone.utc) - dt
    total_minutes = diff.total_seconds() / 60
    if total_minutes < 60:
        m = int(total_minutes)
        return f"{m}m ago" if m > 1 else "Just now"
    if total_minutes < 1440:      # < 24h
        h = int(total_minutes / 60)
        return f"{h}h ago"
    days = diff.days
    if days <= 2:
        return f"{days}d ago"
    return None  # Too old — filter out


def parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def parse_lever_ts(ms) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc)
    except Exception:
        return None


def extract_relative_posted(text: str) -> str | None:
    """Extract and validate a relative date string from page text."""
    m = DATE_WORDS_RE.search(text)
    if not m:
        return None
    full = m.group(0).lower().strip()
    if any(w in full for w in ("today", "just now")):
        return "Today"
    num_s = m.group(1)
    unit  = m.group(2).lower() if m.group(2) else ""
    if not num_s:
        return None
    n = int(num_s)
    if unit in ("minute", "min", "hour", "hr"):
        return f"{n}{'h' if 'h' in unit else 'm'} ago"
    if unit == "day":
        return (f"{n}d ago" if n <= 2 else None)
    return None  # weeks/months = too old


def make_job(
    title: str, exp: str, link: str, fallback_url: str,
    location: str = "", posted: str = "", description: str = ""
) -> dict:
    return {
        "text": title,
        "id": fingerprint(title + location),
        "experience": exp or "Not specified",
        "link": link or fallback_url,
        "location": location,
        "posted": posted,
        "description": clean_description(description),
    }


# ---------------------------------------------------------------------------
# GREENHOUSE API
# ---------------------------------------------------------------------------
def scrape_greenhouse(slug: str, base_url: str) -> tuple[list[dict], str | None]:
    api = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        r = requests.get(api, headers=JSON_HEADERS, timeout=15)
        if r.status_code != 200:
            return [], f"Greenhouse {r.status_code}"
        jobs_raw = r.json().get("jobs", [])
        seen, jobs = set(), []
        for item in jobs_raw:
            title = item.get("title", "")
            if not title or is_garbage(title) or not matches_job(title):
                continue
            if is_senior(title):
                continue
            # Date filter
            posted_dt = parse_iso(item.get("updated_at") or item.get("created_at"))
            posted_label = format_posted(posted_dt)
            # Skip if older than 2 days (but include if date unknown)
            if posted_dt and posted_label is None:
                continue
            # Location
            loc = (item.get("location") or {}).get("name", "")
            # Experience
            content = item.get("content", "")
            exp = get_exp(content) or get_exp(title)
            if exp and not is_fresher_friendly(exp):
                continue
            # Description – first clean paragraph
            desc = clean_description(content)
            link = item.get("absolute_url", base_url)
            fid = fingerprint(title + loc)
            if fid not in seen:
                seen.add(fid)
                jobs.append(make_job(title, exp, link, base_url, loc, posted_label or "", desc))
        return jobs, None
    except Exception as e:
        return [], str(e)


# ---------------------------------------------------------------------------
# LEVER API
# ---------------------------------------------------------------------------
def scrape_lever(slug: str, base_url: str) -> tuple[list[dict], str | None]:
    api = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        r = requests.get(api, headers=JSON_HEADERS, timeout=15)
        if r.status_code != 200:
            return [], f"Lever {r.status_code}"
        jobs_raw = r.json() if isinstance(r.json(), list) else []
        seen, jobs = set(), []
        for item in jobs_raw:
            title = item.get("text") or item.get("title", "")
            if not title or is_garbage(title) or not matches_job(title):
                continue
            if is_senior(title):
                continue
            # Date
            posted_dt = parse_lever_ts(item.get("createdAt"))
            posted_label = format_posted(posted_dt)
            if posted_dt and posted_label is None:
                continue
            # Location
            loc = (item.get("categories") or {}).get("location", "") or item.get("workplaceType", "")
            # Experience
            desc_plain = str(item.get("descriptionPlain", ""))
            lists_text = " ".join(
                " ".join(l.get("content", [])) if isinstance(l, dict) else str(l)
                for l in (item.get("lists") or [])
            )
            exp = get_exp(desc_plain + lists_text) or get_exp(title)
            if exp and not is_fresher_friendly(exp):
                continue
            link = item.get("hostedUrl", base_url)
            desc = clean_description(desc_plain)
            fid = fingerprint(title + loc)
            if fid not in seen:
                seen.add(fid)
                jobs.append(make_job(title, exp, link, base_url, loc, posted_label or "", desc))
        return jobs, None
    except Exception as e:
        return [], str(e)


# ---------------------------------------------------------------------------
# WORKABLE API
# ---------------------------------------------------------------------------
def scrape_workable(subdomain: str, base_url: str) -> tuple[list[dict], str | None]:
    api = f"https://apply.workable.com/api/v3/accounts/{subdomain}/jobs"
    try:
        r = requests.post(
            api,
            json={"query": "", "location": [], "department": [], "worktype": []},
            headers={**JSON_HEADERS, "Content-Type": "application/json"},
            timeout=15,
        )
        if r.status_code != 200:
            return [], None
        jobs_raw = r.json().get("results", [])
        seen, jobs = set(), []
        for item in jobs_raw:
            title = item.get("title", "")
            if not title or is_garbage(title) or not matches_job(title):
                continue
            if is_senior(title):
                continue
            exp = get_exp(title)
            if exp and not is_fresher_friendly(exp):
                continue
            loc = item.get("location", {}).get("city", "") if isinstance(item.get("location"), dict) else ""
            slug = item.get("shortcode", "")
            link = f"https://apply.workable.com/{subdomain}/j/{slug}/" if slug else base_url
            fid = fingerprint(title + loc)
            if fid not in seen:
                seen.add(fid)
                jobs.append(make_job(title, exp, link, base_url, loc))
        return jobs, None
    except Exception as e:
        return [], str(e)


# ---------------------------------------------------------------------------
# GENERIC HTML SCRAPER
# ---------------------------------------------------------------------------
def scrape_html(url: str) -> tuple[list[dict], str | None]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        return [], str(e)

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript",
                     "iframe", "svg", "form", "button", "input", "select",
                     "label", "option", "textarea", "dialog", "aside"]):
        tag.decompose()
    for sel in ["[class*='cookie']", "[class*='consent']", "[class*='banner']",
                "[class*='modal']", "[class*='nav']", "[class*='footer']",
                "[class*='header']", "[class*='sidebar']", "[class*='language']",
                "[role='navigation']", "[role='banner']", "[role='contentinfo']"]:
        for el in soup.select(sel):
            el.decompose()

    SELECTORS = [
        "[class*='job-title']", "[class*='job_title']",
        "[class*='jobTitle']", "[class*='JobTitle']",
        "[class*='position-title']", "[class*='role-title']",
        "[class*='opening-title']", "[class*='posting-title']",
        "[class*='listing-title']", "[class*='vacancy-title']",
        "[data-automation-id='jobTitle']", "[data-job-title]",
        ".job-card h2", ".job-card h3",
        "[class*='job-card'] h2", "[class*='job-card'] h3",
        "[class*='job-item'] h2", "[class*='job-item'] h3",
        "article[class*='job'] h2",
    ]

    seen, jobs = set(), []
    for sel in SELECTORS:
        for el in soup.select(sel):
            raw = el.get_text(separator=" ", strip=True)
            if is_garbage(raw) or not matches_job(raw):
                continue
            if is_senior(raw):
                continue
            title = re.sub(r"\s+", " ", raw).strip()
            parent = el.parent
            parent_text = parent.get_text(" ", strip=True) if parent else ""
            exp = get_exp(parent_text) or get_exp(title)
            if exp and not is_fresher_friendly(exp):
                continue
            # Location hint
            loc = ""
            loc_el = parent.find(attrs={"class": re.compile(r"location|city", re.I)}) if parent else None
            if loc_el:
                loc = loc_el.get_text(" ", strip=True)[:60]
            # Posted hint
            posted = extract_relative_posted(parent_text)
            # Link
            link = None
            a = el if el.name == "a" else el.find("a")
            if a:
                href = a.get("href", "")
                link = href if href.startswith("http") else urljoin(url, href)
            fid = fingerprint(title + loc)
            if fid not in seen:
                seen.add(fid)
                jobs.append(make_job(title, exp, link or url, url, loc, posted or ""))
    return jobs, None


# ---------------------------------------------------------------------------
# PLAYWRIGHT SCRAPER  (JS-rendered sites)
# ---------------------------------------------------------------------------
def scrape_with_playwright(url: str) -> tuple[list[dict], str | None]:
    if not PLAYWRIGHT_AVAILABLE:
        return [], "Playwright not installed"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage",
                      "--disable-blink-features=AutomationControlled"],
            )
            ctx = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 720},
            )
            page = ctx.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
            tag.decompose()

        SELECTORS = [
            "[class*='job-title']", "[class*='jobTitle']",
            "[class*='job_title']", "[class*='position-title']",
            "[class*='role-title']", "[class*='opening-title']",
            "[class*='posting-title']", "[class*='listing-title']",
            "[class*='vacancy-title']", "[class*='result-title']",
            "[data-automation-id='jobTitle']",
            "[data-ph-at-id='job-title']",
            ".job-card h2", ".job-card h3",
            "[class*='job-card'] h2", "[class*='job-card'] h3",
            "[class*='job-card'] a", "[class*='job-list'] h2",
            "[class*='job-list'] a", "[class*='job-item'] h2",
            "[class*='search-result'] h2",
            "article h2", "article h3",
            "li[class*='job'] h2", "li[class*='job'] a",
            "[class*='cmp-teaser__title']",
            "[class*='job-listing-title']",
        ]

        seen, jobs = set(), []
        for sel in SELECTORS:
            for el in soup.select(sel):
                raw = el.get_text(separator=" ", strip=True)
                if is_garbage(raw) or not matches_job(raw):
                    continue
                if is_senior(raw):
                    continue
                title = re.sub(r"\s+", " ", raw).strip()
                parent = el.parent
                parent_text = parent.get_text(" ", strip=True) if parent else ""
                exp = get_exp(parent_text) or get_exp(title)
                if exp and not is_fresher_friendly(exp):
                    continue
                # Location
                loc = ""
                loc_el = (parent.find(attrs={"class": re.compile(r"location|city", re.I)})
                          if parent else None)
                if loc_el:
                    loc = loc_el.get_text(" ", strip=True)[:60]
                # Posted
                posted = extract_relative_posted(parent_text)
                # Link
                link = None
                a = el if el.name == "a" else el.find("a")
                if a:
                    href = a.get("href", "")
                    link = href if href.startswith("http") else urljoin(url, href)
                fid = fingerprint(title + loc)
                if fid not in seen:
                    seen.add(fid)
                    jobs.append(make_job(title, exp, link or url, url, loc, posted or ""))
        return jobs, None
    except Exception as e:
        return [], f"Playwright error: {str(e)[:120]}"


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------
def scrape_jobs(url: str) -> tuple[list[dict], str | None]:
    """
    Routing strategy:
    1. Greenhouse / Lever / Workable  →  public JSON API
    2. Known companies               →  try their ATS first
    3. JS-heavy sites                →  Playwright headless browser
    4. Static HTML                   →  BeautifulSoup scraper
    """
    host = (urlparse(url).hostname or "").lower()
    lower_url = url.lower()

    if "greenhouse.io" in host:
        return scrape_greenhouse(url.rstrip("/").split("/")[-1], url)

    if "jobs.lever.co" in host:
        return scrape_lever(url.rstrip("/").split("/")[-1], url)

    if "workable.com" in host:
        return scrape_workable(url.rstrip("/").split("/")[-1], url)

    for name, slug in GREENHOUSE_COMPANIES.items():
        if name in host or name in lower_url:
            result, _ = scrape_greenhouse(slug, url)
            if result:
                return result, None

    for name, slug in LEVER_COMPANIES.items():
        if name in host or name in lower_url:
            result, _ = scrape_lever(slug, url)
            if result:
                return result, None

    for js_domain in JS_SITES:
        if js_domain in host:
            if PLAYWRIGHT_AVAILABLE:
                return scrape_with_playwright(url)
            return [], None

    return scrape_html(url)
