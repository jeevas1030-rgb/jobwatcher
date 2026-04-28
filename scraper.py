import hashlib
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# ══════════════════════════════════════════════════════════════════════════════
# JS-ONLY SITES — these load jobs via JavaScript, HTML scraping gives garbage.
# We block them immediately and return [] so no garbage alerts are sent.
# Users should use Naukri search URLs for these companies instead.
# ══════════════════════════════════════════════════════════════════════════════
JS_ONLY_DOMAINS = [
    "wipro.com", "careers.wipro.com",
    "accenture.com",
    "careers.tcs.com", "ibegin.tcs.com",
    "infosys.com", "career.infosys.com",
    "cognizant.com",
    "capgemini.com",
    "techmahindra.com",
    "hcltech.com", "hcl.com",
    "ltimindtree.com",
    "ibm.com",
    "amazon.jobs",
    "careers.microsoft.com",
    "careers.google.com",
    "jobs.apple.com",
    "careers.oracle.com",
    "careers.sap.com",
    "deloitte.com",
    "kpmg.com",
    "pwc.in",
    "mphasis.com",
    "mindtree.com",
    "hexaware.com",
]

# ══════════════════════════════════════════════════════════════════════════════
# IT JOB KEYWORDS — title MUST contain at least one of these
# ══════════════════════════════════════════════════════════════════════════════
JOB_KEYWORDS = [
    # Core dev roles
    "software engineer", "software developer", "sde", "swe",
    "web developer", "web engineer",
    "full stack", "fullstack", "full-stack",
    "frontend", "front-end", "front end",
    "backend", "back-end", "back end",
    "application developer", "application engineer",
    # Specialised
    "data scientist", "data analyst", "data engineer",
    "machine learning", "ml engineer", "ai engineer",
    "devops", "cloud engineer", "site reliability",
    "android developer", "ios developer", "mobile developer",
    "flutter", "react native",
    "python developer", "java developer", ".net developer",
    "react developer", "angular developer", "node developer",
    "ui developer", "ux designer", "ui/ux",
    "qa engineer", "test engineer", "sdet", "automation engineer",
    "security analyst", "security engineer",
    "network engineer", "infrastructure engineer",
    "sql developer", "database", "etl developer",
    "salesforce", "sap developer", "rpa developer",
    "technical writer",
    # Fresher / junior titles
    "software intern", "developer intern", "tech intern",
    "engineering intern", "sde intern",
    "software trainee", "developer trainee", "engineering trainee",
    "it trainee", "technology trainee",
    "fresher", "fresh graduate",
    "graduate engineer", "graduate trainee",
    "junior developer", "junior engineer", "junior analyst",
    "associate developer", "associate engineer", "associate analyst",
    "entry level", "entry-level",
    "specialist programmer",
    "technology analyst", "it analyst", "business analyst",
    "systems engineer", "member of technical staff",
    "technical analyst", "technical support",
    # Common search terms that appear in real job titles
    "programmer", "developer", "engineer",
]

# ══════════════════════════════════════════════════════════════════════════════
# GARBAGE — reject anything containing these
# ══════════════════════════════════════════════════════════════════════════════
GARBAGE = [
    # Legal / Policy
    "terms and conditions", "terms of use", "cookie policy",
    "privacy policy", "cookie consent", "functional cookie",
    "required cookie", "fraud awareness", "legal notice",
    "disclaimer", "copyright",
    # Nav / UI
    "home", "log in", "sign in", "sign up", "register",
    "explore now", "know more", "read more", "learn more",
    "view all", "show all", "load more",
    "join now", "join our", "talent network", "talent community",
    "follow us", "connect with", "subscribe", "newsletter",
    "search jobs", "filter", "sort by",
    # Company pages (not job listings)
    "life at", "about us", "contact us",
    "our culture", "our values", "our mission",
    "diversity", "inclusion", "sustainability",
    "experienced professional", "early career",
    # Locations (nav dropdown noise)
    "uk and ireland", "germany and austria", "southern europe",
    "benelux", "nordics", "romania", "portugal", "poland",
    "switzerland", "locations",
    # Languages
    "français", "español", "deutsch", "italiano", "português",
    "polski", "română", "العرب", "日本語", "简体中文", "한국어",
    "english (united", "french (canada",
    # Company-specific
    "wipro.com", "life at wipro",
    # Naukri UI noise
    "filters -", "filters-",
    "search result", "jobs found",
    "apply now", "save job",
]

EXP_RE = re.compile(
    r'(\d+)\s*[-–to]+\s*(\d+)\s*(?:years?|yrs?|yr)|'
    r'(\d+)\s*\+?\s*(?:years?|yrs?|yr)|'
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
    ascii_alpha = sum(1 for c in lower if c.isascii() and c.isalpha())
    if ascii_alpha < 5:
        return True
    if "\n" in text or "\t" in text:
        return True
    if re.match(r'^[\d\s/\-.,()]+$', lower):
        return True
    return False


def matches_job(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in JOB_KEYWORDS)


def get_experience(text: str):
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


# ══════════════════════════════════════════════════════════════════════════════
# NAUKRI SCRAPER — Naukri is the best IT fresher job source for India
# Selectors tuned specifically for naukri.com search results
# ══════════════════════════════════════════════════════════════════════════════
def _scrape_naukri(url: str, soup: BeautifulSoup) -> list[dict]:
    jobs = []
    seen = set()

    # Naukri job cards
    selectors = [
        "a.title",                          # Direct job title links
        ".jobTuple h2 a",
        ".job-title a",
        "[class*='jobTitle'] a",
        "article.jobTuple a.title",
        ".list li h2 a",
        ".srp-jobtuple-wrapper a.title",
        "[class*='job-tuple'] h2 a",
    ]

    for sel in selectors:
        for el in soup.select(sel):
            raw = el.get_text(separator=" ", strip=True)
            if is_garbage(raw) or not matches_job(raw):
                continue
            title = re.sub(r'\s+', ' ', raw).strip()

            # Grab experience from the card
            card = el.find_parent(class_=re.compile(r'job|tuple|card', re.I))
            card_text = card.get_text(" ", strip=True) if card else ""
            exp = get_experience(card_text) or get_experience(title)
            if exp and not is_fresher_friendly(exp):
                continue

            href = el.get("href", "")
            if href and not href.startswith("http"):
                href = urljoin(url, href)

            fid = fingerprint(title)
            if fid not in seen:
                seen.add(fid)
                jobs.append({
                    "text": title,
                    "id": fid,
                    "experience": exp or "Not specified",
                    "link": href or url,
                })

    return jobs


# ══════════════════════════════════════════════════════════════════════════════
# GENERIC HTML SCRAPER (for Freshworks, Zoho, Razorpay, Persistent, etc.)
# ══════════════════════════════════════════════════════════════════════════════
def _scrape_generic(url: str, soup: BeautifulSoup) -> list[dict]:
    # Remove noise elements
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
        "[data-automation-id='jobTitle']",
        "[data-job-title]",
        ".job-card h2", ".job-card h3",
        ".job-listing h2", ".job-listing h3",
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
            exp = get_experience(parent_text) or get_experience(title)
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
                jobs.append({
                    "text": title,
                    "id": fid,
                    "experience": exp or "Not specified",
                    "link": link or url,
                })

    return jobs


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def scrape_jobs(url: str) -> tuple[list[dict], str | None]:
    """
    Smart scraper:
    - Blocks JS-only sites immediately (returns [] — no garbage)
    - Uses Naukri-specific parsing for naukri.com URLs
    - Generic HTML scraper for everything else
    """
    host = urlparse(url).hostname or ""

    # Block JS-only career sites — they never have jobs in static HTML
    for js_domain in JS_ONLY_DOMAINS:
        if js_domain in host:
            return [], None  # Clean empty, no error

    # Fetch the page
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        return [], str(e)

    soup = BeautifulSoup(resp.text, "html.parser")

    # Route to the right parser
    if "naukri.com" in host:
        jobs = _scrape_naukri(url, soup)
    else:
        jobs = _scrape_generic(url, soup)

    return jobs, None
