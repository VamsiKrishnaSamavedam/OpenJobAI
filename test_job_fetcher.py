from backend.services.job_fetcher import fetch_remoteok_jobs


jobs = fetch_remoteok_jobs(limit=5)

print("Number of jobs fetched:", len(jobs))

for job in jobs:
    print("-" * 80)
    print("Title:", job["title"])
    print("Company:", job["company"])
    print("Location:", job["location"])
    print("Apply URL:", job["apply_url"])
    print("Description preview:", job["description"][:300])