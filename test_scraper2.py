from scraper import scrape_jobs
import json

urls = [
    "https://careers.freshworks.com/jobs",
    "https://careers.wipro.com/search-jobs/",
    "https://www.accenture.com/in-en/careers/jobsearch?jk=software+engineer&sb=0&vw=1&is_rj=0"
]

for u in urls:
    print(f"\nScraping {u}...")
    jobs, err = scrape_jobs(u)
    if err:
        print("ERROR:", err)
    else:
        print(f"Found {len(jobs)} jobs")
        for j in jobs[:3]:
            print(json.dumps(j, indent=2))
