import hashlib
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Playwright available for JS-heavy sites
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}

JSON_HEADERS = {
    "User-Agent": "JobWatchPro/1.0",
    "Accept": "application/json",
}

# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ATS API MAPPINGS
# Greenhouse and Lever are public job board APIs — no auth required!
# Many Indian IT companies use these. We fetch JSON directly.
# ══════════════════════════════════════════════════════════════════════════════
GREENHOUSE_COMPANIES = {
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
    "setu": "setu",
    "khatabook": "khatabook",
    "unacademy": "unacademy",
    "udaan": "udaan",
    "cred": "dreamplug",
    "mpl": "mpl",
    "darwinbox": "darwinbox",
    "sprinklr": "sprinklr",
    "gupshup": "gupshup",
    "ola": "ola",
    "swiggy": "swiggy",
    "dunzo": "dunzo",
    "rupeek": "rupeek",
    "orange health": "orangehealth",
}

LEVER_COMPANIES = {
    "flipkart": "flipkart",
    "byju": "byjus",
    "phonepe": "phonepe",
    "paytm": "paytm",
    "nykaa": "nykaa",
    "sharechat": "sharechat",
    "moengage": "moengage",
    "innovaccer": "innovaccer",
    "locus": "locus",
    "leadsquared": "leadsquared",
    "ather": "ather-energy",
}

# ══════════════════════════════════════════════════════════════════════════════
# JS-RENDERED SITES — require Playwright (headless browser) to get real jobs
# ══════════════════════════════════════════════════════════════════════════════
JS_SITES = [
    "accenture.com",
    "wipro.com", "careers.wipro.com",
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
]

# ══════════════════════════════════════════════════════════════════════════════
# IT JOB KEYWORDS
# ══════════════════════════════════════════════════════════════════════════════
JOB_KEYWORDS = [
    "software engineer", "software developer", "sde", "swe",
    "web developer", "web engineer", "full stack", "fullstack",
    "frontend", "front-end", "backend", "back-end",
    "application developer", "application engineer",
    "data scientist", "data analyst", "data engineer",
    "machine learning", "ml engineer", "ai engineer", "deep learning",
    "devops", "cloud engineer", "site reliability",
    "android developer", "ios developer", "mobile developer",
    "flutter", "react native", "react developer", "angular",
    "python developer", "java developer", ".net developer",
    "ui developer", "ux designer", "ui/ux",
    "qa engineer", "test engineer", "sdet", "automation",
    "security analyst", "security engineer",
    "network engineer", "infrastructure",
    "sql developer", "database", "etl developer",
    "salesforce", "sap developer", "rpa",
    "intern", "internship", "trainee", "fresher",
    "graduate engineer", "graduate trainee",
    "junior developer", "junior engineer",
    "associate developer", "associate engineer",
    "entry level", "entry-level",
    "specialist programmer", "technology analyst",
    "it analyst", "business analyst", "systems engineer",
    "technical analyst", "programmer", "developer", "engineer",
]

# ══════════════════════════════════════════════════════════════════════════════
# GARBAGE FILTER
# ══════════════════════════════════════════════════════════════════════════════
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
]

EXP_RE = re.compile(
    r'(\d+)\s*[-–to]+\s*(\d+)\s*(?:years?|yrs?)|'
    r'(\d+)\s*\+?\s*(?:years?|yrs?)|'
    r'\bfresher\b|\bentry.?level\b',
    re.IGNORECASE
)


def fingerprint(text: str) -> str:
    return hashlib.md5(text.strip().lower().encode()).hexdigest()


def is_garbage(text: str) -> bool:
    lower = text.lower().strip()
    if len(lower) < 8 or len(lower) > 150:
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


def matches_job(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in JOB_KEYWORDS)


def get_exp(text: str):
    m = EXP_RE.search(text)
    if not m:
        return None
    if m.group(1) and m.group(2):
        return f"{m.group(1)}-{m.group(2)} yrs"
    if m.group(3):
        return f"{m.group(3)} yrs"
    return "Fresher"


def is_fresher_friendly(exp: str) -> bool:
    if not exp or exp == "Fresher":
        return True
    m = re.search(r'(\d+)', exp)
    return int(m.group(1)) <= 2 if m else True


def make_job(title: str, exp: str, link: str, fallback_url: str) -> dict:
    return {
        "text": title,
        "id": fingerprint(title),
        "experience": exp or "Not specified",
        "link": link or fallback_url,
    }


# ══════════════════════════════════════════════════════════════════════════════
# GREENHOUSE API — Public, no auth needed
# URL: https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true
# ══════════════════════════════════════════════════════════════════════════════
def scrape_greenhouse(company_slug: str, base_url: str) -> tuple[list[dict], str | None]:
    api = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs?content=true"
    try:
        r = requests.get(api, headers=JSON_HEADERS, timeout=15)
        if r.status_code != 200:
            return [], f"Greenhouse API returned {r.status_code}"
        data = r.json()
        jobs_raw = data.get("jobs", [])
        seen = set()
        jobs = []
        for item in jobs_raw:
            title = item.get("title", "")
            if not title or is_garbage(title) or not matches_job(title):
                continue
            # Experience from job content
            content = item.get("content", "")
            exp = get_exp(content) or get_exp(title)
            if exp and not is_fresher_friendly(exp):
                continue
            link = item.get("absolute_url", base_url)
            fid = fingerprint(title)
            if fid not in seen:
                seen.add(fid)
                jobs.append(make_job(title, exp, link, base_url))
        return jobs, None
    except Exception as e:
        return [], str(e)


# ══════════════════════════════════════════════════════════════════════════════
# LEVER API — Public, no auth needed
# URL: https://api.lever.co/v0/postings/{company}?mode=json
# ══════════════════════════════════════════════════════════════════════════════
def scrape_lever(company_slug: str, base_url: str) -> tuple[list[dict], str | None]:
    api = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"
    try:
        r = requests.get(api, headers=JSON_HEADERS, timeout=15)
        if r.status_code != 200:
            return [], f"Lever API returned {r.status_code}"
        jobs_raw = r.json()
        seen = set()
        jobs = []
        for item in (jobs_raw if isinstance(jobs_raw, list) else []):
            title = item.get("text", "") or item.get("title", "")
            if not title or is_garbage(title) or not matches_job(title):
                continue
            # Check experience from lists/description
            desc = str(item.get("descriptionPlain", "")) + str(item.get("lists", ""))
            exp = get_exp(desc) or get_exp(title)
            if exp and not is_fresher_friendly(exp):
                continue
            link = item.get("hostedUrl", base_url)
            fid = fingerprint(title)
            if fid not in seen:
                seen.add(fid)
                jobs.append(make_job(title, exp, link, base_url))
        return jobs, None
    except Exception as e:
        return [], str(e)


# ══════════════════════════════════════════════════════════════════════════════
# WORKABLE API — Public job listings for companies using Workable
# ══════════════════════════════════════════════════════════════════════════════
def scrape_workable(subdomain: str, base_url: str) -> tuple[list[dict], str | None]:
    api = f"https://apply.workable.com/api/v3/accounts/{subdomain}/jobs"
    try:
        r = requests.post(api, json={"query": "", "location": [], "department": [], "worktype": []},
                          headers={**JSON_HEADERS, "Content-Type": "application/json"}, timeout=15)
        if r.status_code != 200:
            return [], None
        data = r.json()
        jobs_raw = data.get("results", [])
        seen = set()
        jobs = []
        for item in jobs_raw:
            title = item.get("title", "")
            if not title or is_garbage(title) or not matches_job(title):
                continue
            exp = get_exp(title)
            if exp and not is_fresher_friendly(exp):
                continue
            slug = item.get("shortcode", "")
            link = f"https://apply.workable.com/{subdomain}/j/{slug}/" if slug else base_url
            fid = fingerprint(title)
            if fid not in seen:
                seen.add(fid)
                jobs.append(make_job(title, exp, link, base_url))
        return jobs, None
    except Exception as e:
        return [], str(e)


# ══════════════════════════════════════════════════════════════════════════════
# GENERIC HTML SCRAPER (for static job boards)
# ══════════════════════════════════════════════════════════════════════════════
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

    seen = set()
    jobs = []
    for sel in SELECTORS:
        for el in soup.select(sel):
            raw = el.get_text(separator=" ", strip=True)
            if is_garbage(raw) or not matches_job(raw):
                continue
            title = re.sub(r'\s+', ' ', raw).strip()
            parent_text = el.parent.get_text(" ", strip=True) if el.parent else ""
            exp = get_exp(parent_text) or get_exp(title)
            if exp and not is_fresher_friendly(exp):
                continue
            link = None
            if el.name == "a":
                link = el.get("href", "")
            elif el.find("a"):
                link = el.find("a").get("href", "")
            if link and not link.startswith("http"):
                link = urljoin(url, link)
            fid = fingerprint(title)
            if fid not in seen:
                seen.add(fid)
                jobs.append(make_job(title, exp, link, url))
    return jobs, None


# ══════════════════════════════════════════════════════════════════════════════
# PLAYWRIGHT SCRAPER — renders JavaScript, gets real job listings
# Works for: Accenture, Wipro, TCS, Infosys, Naukri, etc.
# ══════════════════════════════════════════════════════════════════════════════
def scrape_with_playwright(url: str) -> tuple[list[dict], str | None]:
    """Use headless Chromium to render JS pages and extract real job listings."""
    if not PLAYWRIGHT_AVAILABLE:
        return [], "Playwright not installed"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            ctx = browser.new_context(
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/124.0.0.0 Safari/537.36"),
                viewport={"width": 1280, "height": 720},
            )
            page = ctx.new_page()

            # Go to page and wait for job content to load
            page.goto(url, wait_until="networkidle", timeout=30000)

            # Extra wait for lazy-loaded job cards
            page.wait_for_timeout(3000)

            # Try to scroll to trigger lazy loading
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

            html = page.content()
            browser.close()

        # Parse the fully-rendered HTML
        soup = BeautifulSoup(html, "html.parser")

        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "noscript", "iframe"]):
            tag.decompose()

        # Job title selectors — broad since we're in rendered HTML
        SELECTORS = [
            # Generic job title patterns
            "[class*='job-title']", "[class*='jobTitle']",
            "[class*='job_title']", "[class*='position-title']",
            "[class*='role-title']", "[class*='opening-title']",
            "[class*='posting-title']", "[class*='listing-title']",
            "[class*='vacancy-title']", "[class*='result-title']",
            # Data attributes (Workday, ATS systems)
            "[data-automation-id='jobTitle']",
            "[data-ph-at-id='job-title']",
            "[id*='job-title']",
            # Card patterns
            ".job-card h2", ".job-card h3",
            ".job-card a[class*='title']",
            "[class*='job-card'] h2",
            "[class*='job-card'] h3",
            "[class*='job-card'] a",
            "[class*='job-list'] h2",
            "[class*='job-list'] a",
            "[class*='job-item'] h2",
            "[class*='search-result'] h2",
            # Article-based
            "article h2", "article h3",
            "li[class*='job'] h2",
            "li[class*='job'] a",
            # Accenture specific
            "[class*='cmp-teaser__title']",
            "[class*='job-listing-title']",
            ".title-text",
        ]

        seen = set()
        jobs = []
        for sel in SELECTORS:
            for el in soup.select(sel):
                raw = el.get_text(separator=" ", strip=True)
                if is_garbage(raw) or not matches_job(raw):
                    continue
                title = re.sub(r"\s+", " ", raw).strip()
                parent_text = el.parent.get_text(" ", strip=True) if el.parent else ""
                exp = get_exp(parent_text) or get_exp(title)
                if exp and not is_fresher_friendly(exp):
                    continue
                link = None
                if el.name == "a":
                    link = el.get("href", "")
                elif el.find("a"):
                    link = el.find("a").get("href", "")
                if link and not link.startswith("http"):
                    link = urljoin(url, link)
                fid = fingerprint(title)
                if fid not in seen:
                    seen.add(fid)
                    jobs.append(make_job(title, exp, link or url, url))

        return jobs, None

    except Exception as e:
        return [], f"Playwright error: {str(e)[:100]}"


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def scrape_jobs(url: str) -> tuple[list[dict], str | None]:
    """
    Smart multi-strategy scraper:
    1. Greenhouse/Lever/Workable → public JSON API (fastest)
    2. Known JS sites → Playwright headless browser (renders JS)
    3. Everything else → HTML scraper (fastest, static sites)
    """
    host = urlparse(url).hostname or ""
    lower_url = url.lower()

    # ── Strategy 1: Greenhouse API ──
    if "greenhouse.io" in host:
        slug = url.rstrip("/").split("/")[-1]
        return scrape_greenhouse(slug, url)

    # ── Strategy 2: Lever API ──
    if "jobs.lever.co" in host:
        slug = url.rstrip("/").split("/")[-1]
        return scrape_lever(slug, url)

    # ── Strategy 3: Workable API ──
    if "workable.com" in host:
        slug = url.rstrip("/").split("/")[-1]
        return scrape_workable(slug, url)

    # ── Strategy 4: Known companies → try their ATS APIs first ──
    for name, slug in GREENHOUSE_COMPANIES.items():
        if name in host or name in lower_url:
            result, err = scrape_greenhouse(slug, url)
            if result:
                return result, None

    for name, slug in LEVER_COMPANIES.items():
        if name in host or name in lower_url:
            result, err = scrape_lever(slug, url)
            if result:
                return result, None

    # ── Strategy 5: JS-heavy sites → Playwright headless browser ──
    for js_domain in JS_SITES:
        if js_domain in host:
            if PLAYWRIGHT_AVAILABLE:
                return scrape_with_playwright(url)
            else:
                return [], None  # No browser available, return clean empty

    # ── Strategy 6: Generic HTML scraper ──
    return scrape_html(url)
