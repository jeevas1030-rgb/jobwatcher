import hashlib
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

JOB_SELECTORS = [
    "[class*='job-title']", "[class*='position-title']", "[class*='role-title']",
    "[class*='job-name']",  "[class*='opening']",        "[class*='vacancy']",
    "[class*='career']",    "[data-job-title]",           "[class*='listing-title']",
    "h1", "h2", "h3", "h4",
    "li a", "td a",
]

def fingerprint(text: str) -> str:
    return hashlib.md5(text.strip().lower().encode()).hexdigest()

def scrape_jobs(url: str) -> tuple[list[dict], str | None]:
    """
    Returns (jobs_list, error_string).
    jobs_list is a list of {"text": ..., "id": ...}
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        return [], str(e)

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove noise
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    seen_texts = set()
    jobs = []

    for sel in JOB_SELECTORS:
        for el in soup.select(sel):
            text = el.get_text(separator=" ", strip=True)
            # Filter: likely job titles are 4–120 chars, no crazy symbols
            if 4 <= len(text) <= 120 and text.count("\n") == 0:
                fid = fingerprint(text)
                if fid not in seen_texts:
                    seen_texts.add(fid)
                    jobs.append({"text": text, "id": fid})

    return jobs, None
