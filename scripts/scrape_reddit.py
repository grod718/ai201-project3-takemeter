"""
TakeMeter — Reddit Scraper (no credentials required)
Uses Reddit's public JSON API — no app registration needed.

Run from project root:
  python scripts/scrape_reddit.py
"""

import requests
import pandas as pd
import os
import time
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
SUBREDDITS = [
    "MachineLearning",
    "LocalLLaMA",
    "artificial",
    "ChatGPT",
    "singularity",
]

SORT_METHODS = ["hot", "top", "new"]
POSTS_PER_FETCH = 50
MIN_TEXT_LENGTH = 60
OUTPUT_PATH = "data/raw_posts.csv"

# Mimic a real browser to avoid 403 blocks
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# ── Helpers ───────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    return " ".join(text.split())


def is_usable(text: str) -> bool:
    if not text:
        return False
    if text.strip() in ("[deleted]", "[removed]", ""):
        return False
    if len(text.strip()) < MIN_TEXT_LENGTH:
        return False
    return True


def fetch_posts(subreddit: str, sort: str) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={POSTS_PER_FETCH}&t=month&raw_json=1"
    rows = []

    try:
        resp = SESSION.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"    ⚠ HTTP {resp.status_code} for r/{subreddit}/{sort}")
            return rows

        posts = resp.json().get("data", {}).get("children", [])

        for item in posts:
            p = item.get("data", {})
            title = p.get("title", "")
            selftext = p.get("selftext", "")
            permalink = p.get("permalink", "")
            post_id = p.get("id", "")

            combined = title
            if selftext and selftext not in ("[deleted]", "[removed]"):
                combined += f" {selftext}"
            combined = clean_text(combined)

            if not is_usable(combined):
                continue

            rows.append({
                "id": post_id,
                "source": "post",
                "subreddit": subreddit,
                "sort": sort,
                "text": combined[:1200],
                "score": p.get("score", 0),
                "num_comments": p.get("num_comments", 0),
                "url": f"https://reddit.com{permalink}",
                "scraped_at": datetime.utcnow().isoformat(),
                "label": "",
                "notes": "",
            })

        time.sleep(2)

    except Exception as e:
        print(f"    ⚠ Error: {e}")

    return rows


def fetch_comments(subreddit: str) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/comments.json?limit={POSTS_PER_FETCH}&raw_json=1"
    rows = []

    try:
        resp = SESSION.get(url, timeout=15)
        if resp.status_code != 200:
            return rows

        comments = resp.json().get("data", {}).get("children", [])

        for item in comments:
            c = item.get("data", {})
            body = clean_text(c.get("body", ""))
            if not is_usable(body):
                continue

            link_id = c.get("link_id", "").replace("t3_", "")
            rows.append({
                "id": c.get("id", ""),
                "source": "comment",
                "subreddit": subreddit,
                "sort": "comments",
                "text": body[:1200],
                "score": c.get("score", 0),
                "num_comments": 0,
                "url": f"https://reddit.com/r/{subreddit}/comments/{link_id}",
                "scraped_at": datetime.utcnow().isoformat(),
                "label": "",
                "notes": "",
            })

        time.sleep(2)

    except Exception as e:
        print(f"    ⚠ Comment error: {e}")

    return rows


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("TakeMeter Reddit Scraper (no credentials)")
    print("=" * 55)

    all_rows = []
    seen_ids = set()

    for sub in SUBREDDITS:
        print(f"\n▶ Scraping r/{sub}...")
        sub_count = 0

        for sort in SORT_METHODS:
            print(f"  [{sort}]", end=" ", flush=True)
            rows = fetch_posts(sub, sort)
            for row in rows:
                if row["id"] not in seen_ids:
                    seen_ids.add(row["id"])
                    all_rows.append(row)
                    sub_count += 1
            print(f"{len(rows)} posts")

        print(f"  [comments]", end=" ", flush=True)
        c_rows = fetch_comments(sub)
        for row in c_rows:
            if row["id"] not in seen_ids:
                seen_ids.add(row["id"])
                all_rows.append(row)
                sub_count += 1
        print(f"{len(c_rows)} comments")

        print(f"  ✓ {sub_count} unique from r/{sub}")

    if not all_rows:
        print("\n✗ No data collected.")
        return

    df = pd.DataFrame(all_rows)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    os.makedirs("data", exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print("\n" + "=" * 55)
    print(f"✓ Saved {len(df)} rows → {OUTPUT_PATH}")
    print(f"\nBy subreddit:")
    print(df["subreddit"].value_counts().to_string())
    print(f"\nBy type:")
    print(df["source"].value_counts().to_string())
    print("\nNext: open data/raw_posts.csv and fill in the 'label' column")
    print("Labels: analysis | hot_take | question")
    print("=" * 55)


if __name__ == "__main__":
    main()
