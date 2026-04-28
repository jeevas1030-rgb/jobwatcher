import hashlib
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone

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
# PUBLIC ATS API MAPPINGS (Extensively Expanded)
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
    "kissflow": "kissflow",
    "hexaware": "hexaware",
    "thoughtworks": "thoughtworks",
    "mindtickle": "mindtickle",
    "druva": "druva",
    "eightfold": "eightfoldai",
    "zscaler": "zscaler",
    "nutanix": "nutanix",
    "appdynamics": "appdynamics",
    "rubrik": "rubrik",
    "cohesity": "cohesity",
    "confluent": "confluent",
    "databricks": "databricks",
    "snowflake": "snowflake",
    "mongodb": "mongodb",
    "neo4j": "neo4j",
    "redis": "redis",
    "elastic": "elastic",
    "stripe": "stripe",
    "plaid": "plaid",
    "brex": "brex",
    "ramp": "ramp",
    "gusto": "gusto",
    "rippling": "rippling",
    "deel": "deel",
    "remote": "remote",
    "gitlab": "gitlab",
    "github": "github",
    "asana": "asana",
    "monday": "monday",
    "smartsheet": "smartsheet",
    "notion": "notion",
    "figma": "figma",
    "canva": "canva",
    "miro": "miro",
    "lucid": "lucid",
    "slk": "slksoftware",
    "zoho": "zoho"
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
# JS-RENDERED SITES 
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
# IT JOB KEYWORDS & BLOCKS
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

BLOCK_KEYWORDS = [
    "senior", "lead", "manager", "architect", "principal", "director", "vp", 
    "sr.", "sr", "head", "staff", "experienced", "staff engineer"
]

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
    # Anti-senior filter check
    for kw in BLOCK_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', lower):
            return False
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
    
    # Needs to match exactly start digit
    # Extracted format is usually "X-Y yrs" or "X yrs"
    m_range = re.match(r'(\d+)-(\d+)', exp)
    if m_range:
        min_yr = int(m_range.group(1))
        # "only have 0 to some numbers, or 1 year. dont have 2-5 years"
        # So min_yr must be 0 or 1.
        return min_yr <= 1
    
    m_single = re.match(r'(\d+)', exp)
    if m_single:
        val = int(m_single.group(1))
        return val <= 1

    return True

def clean_desc(html: str) -> str:
    """Extract clean concise text snippet for the job description."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r'\s+', ' ', text)
    if len(text) > 150:
        return text[:147] + "..."
    return text

def make_job(title: str, exp: str, link: str, fallback_url: str, location: str = "Not specified", posted_date: str = "Recent", desc: str = "") -> dict:
    return {
        "text": title,
        "id": fingerprint(title + link),
        "experience": exp or "Not specified",
        "link": link or fallback_url,
        "location": location,
        "posted_date": posted_date,
        "description": desc
    }

def check_date_within_days(date_str: str, max_days: int = 3) -> tuple[bool, str]:
    """Check if date is within X days and format it."""
    try:
        if not date_str:
            return True, "Recent"
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = (now - dt).days
        if diff > max_days:
            return False, ""
        if diff == 0:
            return True, "Today"
        elif diff == 1:
            return True, "Yesterday"
        else:
            return True, f"{diff} days ago"
    except Exception:
        return True, "Recent"  # If we can't parse it, let it through

# ══════════════════════════════════════════════════════════════════════════════
# GREENHOUSE API 
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
            
            # Extract posted date and filter
            updated_at = item.get("updated_at", "")
            is_recent, posted_str = check_date_within_days(updated_at, max_days=3)
            if not is_recent:
                continue

            # Extract location
            loc = item.get("location", {}).get("name", "Remote/Unspecified")

            content = item.get("content", "")
            desc = clean_desc(content)
            exp = get_exp(content) or get_exp(title)
            
            if exp and not is_fresher_friendly(exp):
                continue
            
            link = item.get("absolute_url", base_url)
            fid = fingerprint(title + link)
            if fid not in seen:
                seen.add(fid)
                jobs.append(make_job(title, exp, link, base_url, loc, posted_str, desc))
        return jobs, None
    except Exception as e:
        return [], str(e)

# ══════════════════════════════════════════════════════════════════════════════
# LEVER API 
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

            created_at = item.get("createdAt", None)
            posted_str = "Recent"
            if created_at:
                try:
                    dt = datetime.fromtimestamp(created_at / 1000.0, timezone.utc)
                    now = datetime.now(timezone.utc)
                    diff = (now - dt).days
                    if diff > 3:
                        continue
                    if diff == 0: posted_str = "Today"
                    elif diff == 1: posted_str = "Yesterday"
                    else: posted_str = f"{diff} days ago"
                except Exception:
                    pass

            desc_raw = str(item.get("descriptionPlain", "")) + str(item.get("lists", ""))
            desc = desc_raw[:150] + "..." if len(desc_raw) > 150 else desc_raw
            exp = get_exp(desc_raw) or get_exp(title)
            if exp and not is_fresher_friendly(exp):
                continue
            
            loc = item.get("categories", {}).get("location", "Unspecified")
            link = item.get("hostedUrl", base_url)
            fid = fingerprint(title + link)
            
            if fid not in seen:
                seen.add(fid)
                jobs.append(make_job(title, exp, link, base_url, loc, posted_str, desc))
        return jobs, None
    except Exception as e:
        return [], str(e)

# ══════════════════════════════════════════════════════════════════════════════
# WORKABLE API 
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

            posted_date = item.get("published_on", "")
            is_recent, posted_str = check_date_within_days(posted_date, max_days=3)
            if not is_recent:
                continue

            loc = f"{item.get('city', '')}, {item.get('country', '')}".strip(", ")
            exp = get_exp(title)
            if exp and not is_fresher_friendly(exp):
                continue
            
            slug = item.get("shortcode", "")
            link = f"https://apply.workable.com/{subdomain}/j/{slug}/" if slug else base_url
            desc = "Requirements: " + ", ".join(item.get("skills", [])[:5])
            
            fid = fingerprint(title + link)
            if fid not in seen:
                seen.add(fid)
                jobs.append(make_job(title, exp, link, base_url, loc, posted_str, desc))
        return jobs, None
    except Exception as e:
        return [], str(e)

# ══════════════════════════════════════════════════════════════════════════════
# GENERIC HTML SCRAPER
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
        ".job-card h2", ".job-card h3", "[class*='job-card'] h2", "[class*='job-card'] h3",
        "[class*='job-item'] h2", "[class*='job-item'] h3", "article[class*='job'] h2",
        "[class*='job-title']", "[class*='job_title']", "[class*='jobTitle']", 
        "[class*='JobTitle']", "[class*='position-title']", "[class*='role-title']",
        "[class*='opening-title']", "[class*='posting-title']", "[class*='listing-title']", 
        "[class*='vacancy-title']", "[data-automation-id='jobTitle']", "[data-job-title]",
    ]
    seen = set()
    jobs = []
    
    html_text = soup.get_text(" ", strip=True).lower()
    # If the page literally says "posted X days ago" and X > 3, we might risk it, but better to check per job card.

    for sel in SELECTORS:
        for el in soup.select(sel):
            raw = el.get_text(separator=" ", strip=True)
            if is_garbage(raw) or not matches_job(raw):
                continue
            title = re.sub(r'\s+', ' ', raw).strip()
            
            parent = el.parent or el
            parent_text = parent.get_text(" ", strip=True)
            
            # Try to grab posted date from text visually around the job
            m_days = re.search(r'posted (\d+) days? ago', parent_text.lower())
            if m_days and int(m_days.group(1)) > 3:
                continue # Skip jobs older than 3 days
                
            posted_str = "Recent"
            if "today" in parent_text.lower() or "hours ago" in parent_text.lower():
                posted_str = "Today"
            elif m_days:
                posted_str = f"{m_days.group(1)} days ago"

            exp = get_exp(parent_text) or get_exp(title)
            if exp and not is_fresher_friendly(exp):
                continue
            
            link = None
            if el.name == "a": link = el.get("href", "")
            elif el.find("a"): link = el.find("a").get("href", "")
            if link and not link.startswith("http"): link = urljoin(url, link)
            
            desc = clean_desc(str(parent))
            
            fid = fingerprint(title + str(link))
            if fid not in seen:
                seen.add(fid)
                jobs.append(make_job(title, exp, link, url, "View Listing for details", posted_str, desc))
    return jobs, None

# ══════════════════════════════════════════════════════════════════════════════
# PLAYWRIGHT SCRAPER
# ══════════════════════════════════════════════════════════════════════════════
def scrape_with_playwright(url: str) -> tuple[list[dict], str | None]:
    if not PLAYWRIGHT_AVAILABLE:
        return [], "Playwright not installed"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"],
            )
            ctx = browser.new_context(
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/124.0.0.0 Safari/537.36"),
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
            "[class*='job-title']", "[class*='jobTitle']", "[class*='job_title']", 
            "[class*='position-title']", "[class*='role-title']", "[class*='opening-title']",
            "[class*='posting-title']", "[class*='listing-title']", "[class*='vacancy-title']", 
            "[class*='result-title']", "[data-automation-id='jobTitle']", "[data-ph-at-id='job-title']",
            "[id*='job-title']", ".job-card h2", ".job-card h3", ".job-card a[class*='title']",
            "[class*='job-card'] h2", "[class*='job-card'] h3", "[class*='job-card'] a",
            "[class*='job-list'] h2", "[class*='job-list'] a", "[class*='job-item'] h2",
            "[class*='search-result'] h2", "article h2", "article h3", "li[class*='job'] h2",
            "li[class*='job'] a", "[class*='cmp-teaser__title']", "[class*='job-listing-title']", ".title-text",
        ]
        seen = set()
        jobs = []
        for sel in SELECTORS:
            for el in soup.select(sel):
                raw = el.get_text(separator=" ", strip=True)
                if is_garbage(raw) or not matches_job(raw):
                    continue
                title = re.sub(r"\s+", " ", raw).strip()
                parent_html = el.parent or el
                parent_text = parent_html.get_text(" ", strip=True)
                
                # Check date
                m_days = re.search(r'(\d+)\s+days?\s+ago', parent_text.lower())
                if m_days and int(m_days.group(1)) > 3:
                    continue
                
                posted_str = "Recent"
                if "today" in parent_text.lower() or "hours ago" in parent_text.lower():
                    posted_str = "Today"
                elif m_days:
                    posted_str = f"{m_days.group(1)} days ago"

                exp = get_exp(parent_text) or get_exp(title)
                if exp and not is_fresher_friendly(exp):
                    continue
                
                link = None
                if el.name == "a": link = el.get("href", "")
                elif el.find("a"): link = el.find("a").get("href", "")
                if link and not link.startswith("http"): link = urljoin(url, link)
                
                desc = clean_desc(str(parent_html))
                # Extra loc attempt
                loc_match = re.search(r'(Chennai|Bangalore|Hyderabad|Pune|Mumbai|Delhi|Gurgaon|Noida|Remote)', parent_text, re.IGNORECASE)
                loc = loc_match.group(1) if loc_match else "Unspecified"

                fid = fingerprint(title + str(link))
                if fid not in seen:
                    seen.add(fid)
                    jobs.append(make_job(title, exp, link or url, url, loc, posted_str, desc))
        return jobs, None
    except Exception as e:
        return [], f"Playwright error: {str(e)[:100]}"

# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def scrape_jobs(url: str) -> tuple[list[dict], str | None]:
    host = urlparse(url).hostname or ""
    lower_url = url.lower()
    if "greenhouse.io" in host: return scrape_greenhouse(url.rstrip("/").split("/")[-1], url)
    if "jobs.lever.co" in host: return scrape_lever(url.rstrip("/").split("/")[-1], url)
    if "workable.com" in host: return scrape_workable(url.rstrip("/").split("/")[-1], url)
    for name, slug in GREENHOUSE_COMPANIES.items():
        if name in host or name in lower_url:
            result, err = scrape_greenhouse(slug, url)
            if result: return result, None
    for name, slug in LEVER_COMPANIES.items():
        if name in host or name in lower_url:
            result, err = scrape_lever(slug, url)
            if result: return result, None
    for js_domain in JS_SITES:
        if js_domain in host:
            if PLAYWRIGHT_AVAILABLE: return scrape_with_playwright(url)
            else: return [], None
    return scrape_html(url)
