import hashlib
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ══════════════════════════════════════════════════════════════════════════════
#  JOB TITLE KEYWORDS — must contain at least one to be a real job
# ══════════════════════════════════════════════════════════════════════════════
JOB_TITLE_KEYWORDS = [
    "software engineer", "software developer", "sde", "swe",
    "custom software", "application engineer", "application developer",
    "web developer", "full stack", "fullstack", "full-stack",
    "frontend developer", "frontend engineer", "front-end",
    "backend developer", "backend engineer", "back-end",
    "data scientist", "data analyst", "data engineer",
    "machine learning", "ml engineer", "ai engineer",
    "deep learning", "nlp", "computer vision", "generative ai",
    "devops engineer", "cloud engineer", "site reliability", "sre",
    "qa engineer", "test engineer", "sdet", "quality assurance",
    "automation tester", "automation engineer",
    "mobile developer", "android developer", "ios developer",
    "flutter developer", "react native",
    "react developer", "angular developer", "node developer",
    "python developer", "java developer", ".net developer",
    "ui developer", "ux designer", "ui/ux",
    "product engineer", "platform engineer",
    "solutions engineer", "support engineer",
    "security analyst", "security engineer", "cyber security",
    "network engineer", "infrastructure engineer",
    "sql developer", "etl developer", "bi developer",
    "api developer", "rpa developer", "salesforce developer",
    "intern", "internship", "trainee", "apprentice",
    "fresher", "fresh graduate", "entry level", "entry-level",
    "junior developer", "junior engineer",
    "associate developer", "associate engineer",
    "specialist programmer", "systems engineer",
    "technology analyst", "it analyst", "business analyst",
    "graduate engineer", "graduate trainee",
    "member technical", "technical writer",
    "early career", "new grad", "campus",
    # match any "<something> developer" or "<something> engineer" patterns
]

# ══════════════════════════════════════════════════════════════════════════════
#  GARBAGE FILTER — aggressive to prevent false positives
# ══════════════════════════════════════════════════════════════════════════════
GARBAGE_CONTAINS = [
    "cookie", "privacy", "terms and", "terms of", "disclaimer",
    "copyright", "gdpr", "consent", "fraud", "legal",
    "about us", "contact us", "our culture", "our values",
    "life at", "why work", "why join", "diversity", "inclusion",
    "social media", "newsletter", "subscribe", "talent network",
    "follow us", "connect with", "join our", "stay connected",
    "select language", "choose language",
    "français", "español", "deutsch", "italiano", "português",
    "polski", "română", "العربية", "日本語", "简体中文",
    "explore now", "know more", "read more", "learn more",
    "show more", "load more", "search jobs", "view all",
    "sign in", "sign up", "log in", "register",
    "because we", "opportunity to", "explore open",
    "match your interest", "enhance your",
    "e-posting", "lca ", "h1b ",
]

# Experience pattern
EXP_PATTERN = re.compile(
    r'(\d+)\s*[-–to]+\s*(\d+)\s*(?:years?|yrs?)|'
    r'(\d+)\s*\+?\s*(?:years?|yrs?)|'
    r'fresher|entry.?level',
    re.IGNORECASE
)


def fingerprint(text: str) -> str:
    return hashlib.md5(text.strip().lower().encode()).hexdigest()


def is_garbage(text: str) -> bool:
    lower = text.lower().strip()
    if len(lower) < 8 or len(lower) > 150:
        return True
    for phrase in GARBAGE_CONTAINS:
        if phrase in lower:
            return True
    if len(lower.split()) <= 1:
        return True
    if "\n" in text:
        return True
    if re.match(r'^[\d\s/\-.,]+$', lower):
        return True
    ascii_count = sum(1 for c in lower if c.isascii() and c.isalpha())
    if ascii_count < 5:
        return True
    return False


def matches_job_title(text: str) -> bool:
    lower = text.lower()
    # Check explicit keywords
    if any(kw in lower for kw in JOB_TITLE_KEYWORDS):
        return True
    # Also accept generic "<word> developer" or "<word> engineer" patterns
    if re.search(r'\b\w+\s+(developer|engineer|analyst|architect|tester|designer)\b', lower):
        return True
    return False


def extract_experience(text: str) -> str | None:
    match = EXP_PATTERN.search(text)
    if not match:
        return None
    if match.group(1) and match.group(2):
        return f"{match.group(1)}-{match.group(2)} yrs"
    if match.group(3):
        return f"{match.group(3)} yrs"
    return "Fresher"


def is_fresher_friendly(exp_text: str | None) -> bool:
    if not exp_text:
        return True
    match = re.search(r'(\d+)', exp_text)
    if match:
        return int(match.group(1)) <= 2
    return True


# ══════════════════════════════════════════════════════════════════════════════
#  SITE-SPECIFIC API SCRAPERS
#  These hit the actual JSON APIs that career sites use internally
# ══════════════════════════════════════════════════════════════════════════════

def _scrape_workday(url: str) -> tuple[list[dict], str | None]:
    """Scrape Workday-based career sites (Accenture, Wipro, many others)."""
    # Workday sites have an API at /wday/cxs/<tenant>/External/jobs
    # We need to detect the tenant from the URL
    parsed = urlparse(url)
    host = parsed.hostname or ""

    # Try to find the Workday API endpoint
    api_url = None
    tenant = ""

    if "accenture" in host:
        api_url = "https://www.accenture.com/api/accenture/jobsearch/result"
        return _scrape_accenture_api(api_url)
    elif "wipro" in host:
        # Wipro uses Phenom People platform
        return _scrape_wipro_api()

    return [], None


def _scrape_accenture_api(api_url: str = None) -> tuple[list[dict], str | None]:
    """Scrape Accenture's career API for fresher-friendly IT jobs in India."""
    url = "https://www.accenture.com/api/accenture/jobsearch/result"
    payload = {
        "keyword": "",
        "location": "India",
        "skill": "",
        "experience": "0to2",
        "sortBy": "postedDate",
        "page": 1,
        "pageSize": 50,
    }
    try:
        r = requests.post(url, json=payload, headers={
            **HEADERS,
            "Content-Type": "application/json",
            "Referer": "https://www.accenture.com/in-en/careers/jobsearch",
        }, timeout=20)

        if r.status_code != 200:
            # Fallback: try the HTML search page
            return _scrape_html("https://www.accenture.com/in-en/careers/jobsearch")

        data = r.json()
        jobs = []
        for item in data.get("data", data.get("jobs", data.get("results", []))):
            title = item.get("title") or item.get("jobTitle") or item.get("name", "")
            if not title or is_garbage(title):
                continue
            if not matches_job_title(title):
                continue
            exp = extract_experience(str(item))
            if exp and not is_fresher_friendly(exp):
                continue
            link = item.get("url") or item.get("applyUrl") or item.get("detailUrl", "")
            if link and not link.startswith("http"):
                link = "https://www.accenture.com" + link

            fid = fingerprint(title)
            jobs.append({
                "text": title,
                "id": fid,
                "experience": exp or "Not specified",
                "link": link or "https://www.accenture.com/in-en/careers/jobsearch",
            })
        return jobs, None
    except Exception as e:
        return _scrape_html("https://www.accenture.com/in-en/careers/jobsearch")


def _scrape_wipro_api() -> tuple[list[dict], str | None]:
    """Scrape Wipro's career API."""
    url = "https://careers.wipro.com/api/jobs"
    params = {
        "limit": 50,
        "page": 1,
        "sortBy": "relevance",
        "descending": "false",
    }
    alt_urls = [
        "https://careers.wipro.com/api/apply/v2/jobs",
        "https://careers.wipro.com/api/jobs/search",
    ]
    try:
        r = requests.get(url, params=params, headers={
            **HEADERS,
            "Accept": "application/json",
        }, timeout=20)

        if r.status_code != 200:
            # Try alternates
            for alt in alt_urls:
                try:
                    r2 = requests.get(alt, params=params, headers={
                        **HEADERS, "Accept": "application/json"
                    }, timeout=15)
                    if r2.status_code == 200:
                        r = r2
                        break
                except:
                    continue

        if r.status_code != 200:
            return _scrape_html("https://careers.wipro.com/search-jobs/")

        data = r.json()
        jobs_raw = data if isinstance(data, list) else data.get("jobs", data.get("data", data.get("results", [])))

        jobs = []
        for item in (jobs_raw if isinstance(jobs_raw, list) else []):
            title = ""
            for key in ["title", "jobTitle", "name", "requisitionTitle", "postingTitle"]:
                if item.get(key):
                    title = item[key]
                    break
            if not title or is_garbage(title):
                continue
            if not matches_job_title(title):
                continue
            exp = extract_experience(str(item))
            if exp and not is_fresher_friendly(exp):
                continue

            link = item.get("url") or item.get("applyUrl") or item.get("canonicalUrl", "")
            if link and not link.startswith("http"):
                link = "https://careers.wipro.com" + link

            fid = fingerprint(title)
            jobs.append({
                "text": title,
                "id": fid,
                "experience": exp or "Not specified",
                "link": link or "https://careers.wipro.com/search-jobs/",
            })
        return jobs, None
    except Exception as e:
        return _scrape_html("https://careers.wipro.com/search-jobs/")


# ══════════════════════════════════════════════════════════════════════════════
#  HTML SCRAPER (fallback for sites without known APIs)
# ══════════════════════════════════════════════════════════════════════════════

def _scrape_html(url: str) -> tuple[list[dict], str | None]:
    """Generic HTML scraper with aggressive filtering."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        return [], str(e)

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove ALL noise elements
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript",
                     "iframe", "svg", "form", "button", "input", "select",
                     "label", "option", "textarea", "dialog", "aside"]):
        tag.decompose()

    # Remove noise by class/id
    noise_selectors = [
        "[class*='cookie']", "[class*='Cookie']",
        "[class*='consent']", "[class*='Consent']",
        "[class*='modal']", "[class*='Modal']",
        "[class*='popup']", "[class*='Popup']",
        "[class*='navigation']", "[class*='navbar']",
        "[class*='sidebar']", "[class*='footer']",
        "[class*='header']", "[class*='language']",
        "[class*='locale']", "[class*='banner']",
        "[role='navigation']", "[role='banner']",
        "[role='contentinfo']", "[role='dialog']",
    ]
    for sel in noise_selectors:
        for el in soup.select(sel):
            el.decompose()

    job_selectors = [
        "[class*='job-title']", "[class*='job_title']", "[class*='jobTitle']",
        "[class*='position-title']", "[class*='role-title']",
        "[class*='listing-title']", "[class*='posting-title']",
        "[data-automation-id='jobTitle']",
        ".job-card h2", ".job-card h3", ".job-card a",
        "[class*='job-card'] a", "[class*='job-list'] a",
        "[class*='job-item'] a", "[class*='search-result'] h2",
        "article h2", "article h3",
        "li h2 a", "li h3 a",
        "h2 a", "h3 a",
    ]

    seen_texts = set()
    jobs = []

    for sel in job_selectors:
        for el in soup.select(sel):
            raw = el.get_text(separator=" ", strip=True)
            if is_garbage(raw):
                continue
            if not matches_job_title(raw):
                continue
            title = re.sub(r'\s+', ' ', raw).strip()
            parent_text = el.parent.get_text(separator=" ", strip=True) if el.parent else ""
            exp = extract_experience(parent_text) or extract_experience(title)
            if exp and not is_fresher_friendly(exp):
                continue
            link = None
            if el.name == "a" and el.get("href"):
                link = el["href"]
            elif el.find("a"):
                link = el.find("a").get("href", "")
            if link and not link.startswith("http"):
                link = urljoin(url, link)
            fid = fingerprint(title)
            if fid not in seen_texts:
                seen_texts.add(fid)
                jobs.append({
                    "text": title,
                    "id": fid,
                    "experience": exp or "Not specified",
                    "link": link or url,
                })

    return jobs, None


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT — routes to the right scraper
# ══════════════════════════════════════════════════════════════════════════════

def scrape_jobs(url: str) -> tuple[list[dict], str | None]:
    """
    Smart scraper that routes to API-based scraping for known sites,
    falls back to HTML scraping for everything else.
    """
    host = urlparse(url).hostname or ""

    # Route known sites to their API scrapers
    if "accenture" in host:
        return _scrape_accenture_api()
    if "wipro" in host:
        return _scrape_wipro_api()

    # Fallback: generic HTML scraper
    return _scrape_html(url)
