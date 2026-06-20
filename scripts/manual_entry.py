"""
TakeMeter — Manual Entry Helper
Use this when you find a great post manually that you want to add to your dataset.
Run it interactively: python scripts/manual_entry.py

It opens a prompt, you paste the post text, assign a label, and it appends
the row to data/raw_posts.csv in the same format as the scraper output.

This keeps your dataset in one file regardless of how the post was collected.
"""

import pandas as pd
import os
from datetime import datetime

OUTPUT_PATH = "data/raw_posts.csv"
VALID_LABELS = {"analysis", "hot_take", "question"}


def load_existing() -> pd.DataFrame:
    if os.path.exists(OUTPUT_PATH):
        return pd.read_csv(OUTPUT_PATH)
    # Return empty DataFrame with correct columns
    return pd.DataFrame(columns=[
        "id", "source", "subreddit", "sort", "text",
        "score", "num_comments", "url", "scraped_at", "label", "notes"
    ])


def main():
    print("=" * 50)
    print("TakeMeter — Manual Post Entry")
    print("Adds posts to data/raw_posts.csv")
    print("Type EXIT at any prompt to stop.")
    print("=" * 50)

    df = load_existing()
    added = 0

    while True:
        print(f"\n── Entry #{len(df) + 1} ──")

        print("Paste post text (press Enter twice when done):")
        lines = []
        while True:
            line = input()
            if line == "EXIT":
                break
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)

        if not lines or (lines and lines[0] == "EXIT"):
            break

        text = " ".join(l for l in lines if l).strip()
        if len(text) < 30:
            print("⚠ Text too short, skipping.")
            continue

        print(f"\nLabel options: analysis | hot_take | question")
        label = input("Label: ").strip().lower()
        if label == "exit":
            break
        if label not in VALID_LABELS:
            print(f"⚠ '{label}' is not a valid label. Skipping.")
            continue

        url = input("URL (optional, press Enter to skip): ").strip()
        subreddit = input("Subreddit (e.g. MachineLearning): ").strip()
        notes = input("Notes on this case (optional): ").strip()

        new_row = {
            "id": f"manual_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            "source": "manual",
            "subreddit": subreddit or "unknown",
            "sort": "manual",
            "text": text,
            "score": None,
            "num_comments": None,
            "url": url or "",
            "scraped_at": datetime.utcnow().isoformat(),
            "label": label,
            "notes": notes,
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(OUTPUT_PATH, index=False)
        added += 1
        print(f"✓ Saved. Total in dataset: {len(df)}")

    print(f"\nDone. Added {added} manual entries.")
    if os.path.exists(OUTPUT_PATH):
        df = pd.read_csv(OUTPUT_PATH)
        print(f"Total dataset size: {len(df)} rows")
        if "label" in df.columns:
            labeled = df[df["label"].notna() & (df["label"] != "")]
            print(f"Labeled so far: {len(labeled)}")
            if len(labeled):
                print(labeled["label"].value_counts().to_string())


if __name__ == "__main__":
    main()
