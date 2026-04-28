from scraper import scrape_jobs, PLAYWRIGHT_AVAILABLE

print(f"Playwright available: {PLAYWRIGHT_AVAILABLE}")
print()

print("=== Accenture (JS site via Playwright) ===")
jobs, err = scrape_jobs("https://www.accenture.com/in-en/careers/jobsearch?jk=software+engineer&sb=0&vw=1&is_rj=0")
if err:
    print(f"  ERROR: {err}")
else:
    print(f"  {len(jobs)} jobs found")
    for j in jobs[:8]:
        print(f"  [{j['experience']:>14}]  {j['text'][:70]}")

print()
print("=== Wipro (JS site via Playwright) ===")
jobs2, err2 = scrape_jobs("https://careers.wipro.com/search-jobs/")
if err2:
    print(f"  ERROR: {err2}")
else:
    print(f"  {len(jobs2)} jobs found")
    for j in jobs2[:5]:
        print(f"  [{j['experience']:>14}]  {j['text'][:70]}")

print()
print("=== Freshworks (Static HTML) ===")
jobs3, err3 = scrape_jobs("https://careers.freshworks.com/jobs")
if err3:
    print(f"  ERROR: {err3}")
else:
    print(f"  {len(jobs3)} jobs found")
    for j in jobs3[:5]:
        print(f"  [{j['experience']:>14}]  {j['text'][:70]}")
