import hashlib
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── IT/Fresher Job Keywords ───────────────────────────────────────────────────
# A scraped item MUST contain at least one of these keywords to be considered a real job
JOB_KEYWORDS = [
    # Core roles
    "software engineer", "software developer", "sde", "swe",
    "custom software", "application engineer",
    "web developer", "full stack", "fullstack", "full-stack",
    "frontend", "front-end", "front end",
    "backend", "back-end", "back end",
    "developer", "programmer", "engineer", "coder",
    "data scientist", "data analyst", "data engineer",
    "machine learning", "ml engineer", "ai engineer", "deep learning",
    "nlp", "computer vision", "generative ai",
    "devops", "cloud engineer", "site reliability", "sre",
    "qa engineer", "test engineer", "sdet", "quality assurance", "automation tester",
    "mobile developer", "android developer", "ios developer", "flutter developer",
    "react developer", "angular developer", "node developer", "vue developer",
    "python developer", "java developer", ".net developer", "c++ developer",
    "golang developer", "rust developer", "php developer", "ruby developer",
    "ui developer", "ux designer", "ui/ux", "interaction designer",

    # Entry-level & fresher titles
    "intern", "internship", "trainee", "apprentice",
    "graduate", "fresher", "fresh graduate",
    "entry level", "entry-level", "entrylevel",
    "associate", "junior", "jr.", "jr ",
    "level 1", "level i", "l1", "grade 1",
    "0-1 year", "0-2 year", "0 - 1", "0 - 2", "0 to 2",
    "analyst", "consultant",
    "specialist programmer", "systems engineer",
    "application developer", "technology analyst",
    "packaged app development", "test analyst",
    "staff engineer", "member technical",

    # Company-specific fresher programs (India IT)
    "ase", "act", "genesis", "launchpad", "ignite",
    "campus", "early career", "new grad", "stepping stone",
    "ninja", "digital nurture", "smart hire", "codevita",
    "nqt", "tcs", "infosys", "wipro", "cognizant",
    "hcl", "tech mahindra", "capgemini", "accenture",
    "mindtree", "mphasis", "persistent", "ltimindtree",

    # More IT roles
    "technology", "tech lead", "architect",
    "product engineer", "platform engineer",
    "solutions engineer", "support engineer",
    "it analyst", "business analyst", "business intelligence",
    "cyber security", "security analyst", "security engineer",
    "network engineer", "infrastructure engineer",
    "embedded", "firmware", "iot developer",
    "database", "dba", "sql developer",
    "etl developer", "bi developer", "tableau", "power bi",
    "scrum master", "project manager", "program manager",
    "technical writer", "technical support",
    "api developer", "microservices", "blockchain",
    "rpa developer", "automation engineer",
    "salesforce developer", "servicenow", "sap consultant",
    "graphics programmer", "game developer",
]

# ── Experience Level Patterns ─────────────────────────────────────────────────
# Matches things like "0-2 years", "0 - 3 yrs", "1-2 Years", "Fresher"
EXP_PATTERN = re.compile(
    r'(\d+)\s*[-–to]+\s*(\d+)\s*(?:years?|yrs?|yr)|'
    r'(\d+)\s*\+?\s*(?:years?|yrs?|yr)|'
    r'fresher|entry.?level|0\s*(?:years?|yrs?)',
    re.IGNORECASE
)

# ── Noise / Garbage Blacklist ─────────────────────────────────────────────────
# Lines containing these are NOT job titles — filter them out
BLACKLIST = [
    "cookie", "privacy", "accept", "decline", "subscribe",
    "sign in", "sign up", "login", "log in", "register",
    "filter", "sort by", "search", "apply filter",
    "clear all", "reset", "show more", "load more", "view all",
    "back to top", "scroll", "menu", "navigation",
    "terms", "conditions", "disclaimer", "copyright",
    "follow us", "connect with us", "social media",
    "about us", "contact us", "careers at", "life at",
    "our culture", "our values", "our mission", "our story",
    "diversity", "inclusion", "sustainability",
    "select", "choose", "browse", "explore",
    "page", "next", "previous", "results",
    "share this", "bookmark", "save job", "email alert",
    "no results", "no jobs", "try again",
    "skip to", "jump to", "go to",
]

# Better CSS selectors that target actual job listing elements
JOB_SELECTORS = [
    # Specific job listing patterns (most career sites)
    "[class*='job-title']", "[class*='job-name']", "[class*='job_title']",
    "[class*='position-title']", "[class*='position-name']",
    "[class*='role-title']", "[class*='role-name']",
    "[class*='opening-title']", "[class*='vacancy-title']",
    "[class*='listing-title']", "[class*='posting-title']",
    "[class*='result-title']", "[class*='card-title']",
    "[data-job-title]", "[data-automation-id='jobTitle']",
    "[class*='jobTitle']", "[class*='JobTitle']",

    # Accenture-specific
    "[class*='cmp-teaser__title']", ".card__title",

    # Generic structured elements (fallback)
    "h2 a", "h3 a", "h4 a",
    "li h2", "li h3", "li h4",
    ".job-card h2", ".job-card h3",
    "article h2", "article h3",
    "tr td:first-child a",
]


def fingerprint(text: str) -> str:
    """Create a unique hash for a job text."""
    return hashlib.md5(text.strip().lower().encode()).hexdigest()


def is_noise(text: str) -> bool:
    """Check if text is navigation/UI noise, not a real job."""
    lower = text.lower().strip()

    # Too short or too long
    if len(lower) < 5 or len(lower) > 200:
        return True

    # Contains newlines (likely multi-element scrape)
    if "\n" in text:
        return True

    # Pure numbers or dates
    if re.match(r'^[\d\s/\-.,]+$', lower):
        return True

    # Starts with common noise patterns
    noise_starts = ["view ", "show ", "sort ", "filter", "search", "page ", "clear"]
    if any(lower.startswith(s) for s in noise_starts):
        return True

    # Contains blacklisted phrases
    for bl in BLACKLIST:
        if bl in lower:
            return True

    return False


def matches_job_keywords(text: str) -> bool:
    """Check if text contains at least one relevant IT job keyword."""
    lower = text.lower()
    return any(kw in lower for kw in JOB_KEYWORDS)


def extract_experience(text: str) -> str | None:
    """Try to extract experience requirement from nearby text."""
    match = EXP_PATTERN.search(text)
    if not match:
        return None
    if match.group(1) and match.group(2):
        return f"{match.group(1)}-{match.group(2)} yrs"
    if match.group(3):
        return f"{match.group(3)} yrs"
    return "Fresher"


def is_fresher_friendly(exp_text: str | None, full_text: str = "") -> bool:
    """Check if a job is suitable for freshers (0-2 years experience)."""
    # If no experience mentioned, could be fresher-friendly
    if not exp_text:
        lower = full_text.lower()
        fresher_hints = ["fresher", "entry level", "entry-level", "intern",
                         "trainee", "graduate", "campus", "0 year", "new grad",
                         "junior", "jr.", "associate"]
        return any(h in lower for h in fresher_hints) or True  # Default: include

    # Parse the experience range
    match = re.search(r'(\d+)', exp_text)
    if match:
        min_exp = int(match.group(1))
        return min_exp <= 2  # 0, 1, or 2 years minimum

    return True


def scrape_jobs(url: str) -> tuple[list[dict], str | None]:
    """
    Scrape a careers page for IT job listings relevant to freshers.
    Returns (jobs_list, error_string).
    jobs_list is a list of {"text": title, "id": hash, "experience": exp_str, "link": url}
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        return [], str(e)

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove noise elements
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript",
                     "iframe", "svg", "form", "button", "input", "select"]):
        tag.decompose()

    seen_texts = set()
    jobs = []

    for sel in JOB_SELECTORS:
        for el in soup.select(sel):
            title = el.get_text(separator=" ", strip=True)

            # Skip noise
            if is_noise(title):
                continue

            # Must match at least one IT job keyword
            if not matches_job_keywords(title):
                continue

            # Clean up the title
            title = re.sub(r'\s+', ' ', title).strip()

            # Try to find experience info in parent/sibling elements
            parent_text = ""
            if el.parent:
                parent_text = el.parent.get_text(separator=" ", strip=True)

            exp = extract_experience(parent_text) or extract_experience(title)

            # Fresher filter: skip jobs requiring 3+ years
            if exp and not is_fresher_friendly(exp):
                continue

            # Extract link
            link = None
            if el.name == "a" and el.get("href"):
                link = el["href"]
            elif el.find("a"):
                link = el.find("a").get("href", "")

            # Make link absolute
            if link and not link.startswith("http"):
                from urllib.parse import urljoin
                link = urljoin(url, link)

            # Deduplicate
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
