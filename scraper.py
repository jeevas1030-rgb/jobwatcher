import hashlib
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ══════════════════════════════════════════════════════════════════════════════
# SITES THAT LOAD JOBS VIA JAVASCRIPT — scraping their HTML gives only garbage
# For these, we return [] cleanly. User should add Naukri/LinkedIn search URLs.
# ══════════════════════════════════════════════════════════════════════════════
JS_ONLY_SITES = [
    "wipro.com", "careers.wipro.com",
    "accenture.com",
    "careers.tcs.com",
    "infosys.com", "career.infosys.com",
    "cognizant.com",
    "capgemini.com",
    "careers.techmahindra.com",
    "hcltech.com",
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
]

# ══════════════════════════════════════════════════════════════════════════════
# JOB TITLE KEYWORDS — text MUST contain one of these to be treated as a job
# ══════════════════════════════════════════════════════════════════════════════
JOB_KEYWORDS = [
    # Software roles
    "software engineer", "software developer", "sde", "swe",
    "custom software engineer",
    "web developer", "web engineer",
    "full stack", "fullstack", "full-stack",
    "frontend developer", "frontend engineer", "front-end developer",
    "backend developer", "backend engineer", "back-end developer",
    "application developer", "application engineer",
    # Data / AI / ML
    "data scientist", "data analyst", "data engineer",
    "machine learning engineer", "ml engineer",
    "ai engineer", "ai developer",
    "deep learning", "nlp engineer", "computer vision",
    # DevOps / Cloud / QA
    "devops engineer", "cloud engineer", "site reliability engineer",
    "qa engineer", "test engineer", "sdet",
    "automation tester", "automation engineer",
    "quality assurance engineer", "quality assurance analyst",
    # Mobile / Specific stacks
    "android developer", "ios developer",
    "flutter developer", "react native developer",
    "react developer", "angular developer", "node developer",
    "python developer", "java developer", ".net developer",
    "ui developer", "ux designer", "ui/ux developer",
    # Support roles
    "product engineer", "platform engineer",
    "solutions engineer", "support engineer",
    "security analyst", "security engineer",
    "network engineer", "infrastructure engineer",
    "database administrator", "sql developer",
    "etl developer", "bi developer",
    "api developer", "rpa developer",
    "salesforce developer", "sap developer",
    "technical writer",
    # Fresher / Entry-level titles
    "software intern", "tech intern", "engineering intern",
    "developer intern", "sde intern",
    "software trainee", "developer trainee", "engineering trainee",
    "technology trainee", "it trainee",
    "fresher engineer", "fresher developer",
    "graduate engineer trainee", "graduate trainee",
    "junior software", "junior developer", "junior engineer",
    "associate software", "associate developer", "associate engineer",
    "entry level software", "entry-level developer",
    "specialist programmer",
    "technology analyst", "it analyst",
    "business analyst",
    "systems engineer",
    "member of technical staff",
    "technical analyst",
    # Internship
    "internship", "summer intern", "winter intern",
    # Programs
    "early career program", "campus hiring",
    "new grad", "fresh graduate program",
    "digital nurture", "launchpad", "ignite",
]

# ══════════════════════════════════════════════════════════════════════════════
# GARBAGE PHRASES — if text contains ANY of these, reject immediately
# ══════════════════════════════════════════════════════════════════════════════
GARBAGE = [
    # Legal
    "terms and conditions", "terms of use", "terms of service",
    "cookie policy", "privacy policy", "cookie consent",
    "functional cookie", "required cookie", "cookie manager",
    "fraud awareness", "legal notice", "disclaimer",
    "copyright", "gdpr", "data protection",
    # Navigation
    "home", "careers", "life at", "about us", "contact us",
    "explore all jobs", "search jobs", "sign in", "sign up",
    "log in", "register",
    "explore now", "know more", "read more", "learn more",
    "view all", "show more", "load more",
    "join now", "join our", "talent network",
    "follow us", "connect with", "subscribe",
    # Locations (nav dropdowns)
    "wipro.com", "wipro locations",
    "uk and ireland", "germany and austria",
    "southern europe", "northern europe",
    "benelux", "nordics",
    "romania", "portugal", "poland", "switzerland",
    # Languages
    "français", "español", "deutsch", "italiano", "português",
    "polski", "română", "العرب", "日本語", "简体中文",
    "english (united", "french (", "spanish (", "german (",
    # Corporate fluff
    "our culture", "our values", "our mission", "our story",
    "who we are", "why work", "why join", "why wipro",
    "diversity", "inclusion", "sustainability",
    "annual report", "investor", "life at wipro",
    "experienced professionals", "early careers",
    "talent community", "talent pool", "stay connected",
    "e-posting", "lca ", "h1b ",
    "because we care", "opportunity to reinvent",
    "explore open roles", "match your interests",
    "enhance your job search",
    "h1b lca", "e-postings",
]

EXP_PATTERN = re.compile(
    r'(\d+)\s*[-–to]+\s*(\d+)\s*(?:years?|yrs?)|'
    r'(\d+)\s*\+?\s*(?:years?|yrs?)',
    re.IGNORECASE
)


def fingerprint(text: str) -> str:
    return hashlib.md5(text.strip().lower().encode()).hexdigest()


def is_garbage(text: str) -> bool:
    lower = text.lower().strip()

    # Length check — job titles are 10–120 chars
    if len(lower) < 10 or len(lower) > 120:
        return True

    # Must have 2+ words
    if len(lower.split()) < 2:
        return True

    # Contains any garbage phrase
    for phrase in GARBAGE:
        if phrase in lower:
            return True

    # Mostly non-ASCII (language selector items)
    ascii_alpha = sum(1 for c in lower if c.isascii() and c.isalpha())
    if ascii_alpha < 6:
        return True

    # Multi-line (scraped multiple elements)
    if "\n" in text or "\t" in text:
        return True

    # Pure numbers / dates
    if re.match(r'^[\d\s/\-.,()]+$', lower):
        return True

    # Ends with navigation arrows
    if lower.rstrip().endswith((">>", ">", "›", "→", "↗", "...")):
        return True

    return False


def matches_job(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in JOB_KEYWORDS)


def extract_experience(text: str):
    m = EXP_PATTERN.search(text)
    if not m:
        return None
    if m.group(1) and m.group(2):
        return f"{m.group(1)}-{m.group(2)} yrs"
    if m.group(3):
        return f"{m.group(3)} yrs"
    return None


def is_fresher_friendly(exp: str) -> bool:
    if not exp:
        return True
    m = re.search(r'(\d+)', exp)
    return int(m.group(1)) <= 2 if m else True


def scrape_jobs(url: str) -> tuple[list[dict], str | None]:
    """
    Main entry point.
    - Blocks known JS-only career sites (returns [] immediately — no garbage).
    - For all other sites, does aggressive HTML scraping.
    """
    host = urlparse(url).hostname or ""

    # Block JS-only sites — they never have jobs in their HTML
    for js_site in JS_ONLY_SITES:
        if js_site in host:
            return [], None  # Clean empty — not an error, just unsupported

    return _html_scrape(url)


def _html_scrape(url: str) -> tuple[list[dict], str | None]:
    """
    HTML scraper for sites that render job listings in static HTML.
    Works great with: Naukri, Freshworks, Zoho, Razorpay, Persistent, etc.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        return [], str(e)

    soup = BeautifulSoup(resp.text, "html.parser")

    # Step 1: Nuke ALL non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript",
                     "iframe", "svg", "form", "button", "input", "select",
                     "label", "option", "textarea", "dialog", "aside",
                     "meta", "link"]):
        tag.decompose()

    # Step 2: Nuke noisy sections by class/id/role
    for sel in [
        "[class*='cookie']", "[class*='Cookie']",
        "[class*='consent']", "[class*='banner']",
        "[class*='modal']", "[class*='popup']",
        "[class*='nav']", "[class*='Nav']",
        "[class*='footer']", "[class*='Footer']",
        "[class*='header']", "[class*='Header']",
        "[class*='sidebar']", "[class*='language']",
        "[class*='locale']", "[class*='social']",
        "[role='navigation']", "[role='banner']",
        "[role='contentinfo']", "[role='dialog']",
    ]:
        for el in soup.select(sel):
            el.decompose()

    # Step 3: Find job elements using targeted selectors only
    # (NO generic h2 a / h3 a — too noisy)
    TARGETED_SELECTORS = [
        # Explicit job title classes
        "[class*='job-title']", "[class*='job_title']",
        "[class*='jobTitle']", "[class*='JobTitle']",
        "[class*='position-title']", "[class*='position_title']",
        "[class*='role-title']", "[class*='role_title']",
        "[class*='opening-title']", "[class*='posting-title']",
        "[class*='listing-title']", "[class*='result-title']",
        "[class*='vacancy-title']", "[class*='requisition']",
        # Data attributes used by ATSes
        "[data-automation-id='jobTitle']",
        "[data-job-title]",
        "[data-field='title']",
        # Common card patterns
        ".job-card h2", ".job-card h3",
        ".job-listing h2", ".job-listing h3",
        ".job-result h2", ".job-result h3",
        ".opening h2", ".opening h3",
        "[class*='job-card'] h2", "[class*='job-card'] h3",
        "[class*='job-item'] h2", "[class*='job-item'] h3",
        "[class*='job-row'] td:first-child",
        # Table-based job boards
        "table.jobs td:first-child a",
        "article[class*='job'] h2", "article[class*='job'] h3",
    ]

    seen = set()
    jobs = []

    for sel in TARGETED_SELECTORS:
        for el in soup.select(sel):
            raw = el.get_text(separator=" ", strip=True)

            if is_garbage(raw):
                continue
            if not matches_job(raw):
                continue

            title = re.sub(r'\s+', ' ', raw).strip()

            # Check experience from parent context
            parent_text = el.parent.get_text(" ", strip=True) if el.parent else ""
            exp = extract_experience(parent_text) or extract_experience(title)
            if exp and not is_fresher_friendly(exp):
                continue

            # Get link
            link = None
            if el.name == "a" and el.get("href"):
                link = el["href"]
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

    return jobs, None
