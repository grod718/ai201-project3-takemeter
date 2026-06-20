"""
TakeMeter — Dataset Health Check
Run this any time during annotation to see where you stand.

  python scripts/check_dataset.py

Tells you:
- How many rows are labeled vs unlabeled
- Label distribution (flags imbalance)
- Text length stats (flags very short posts)
- Whether you're ready for fine-tuning (200+ labeled, no label > 70%)
"""

import pandas as pd
import os
import sys

OUTPUT_PATH = "data/raw_posts.csv"
LABELED_PATH = "data/labeled_posts.csv"


def check(path: str):
    if not os.path.exists(path):
        print(f"✗ File not found: {path}")
        return

    df = pd.read_csv(path)
    print(f"\n{'='*50}")
    print(f"File: {path}")
    print(f"{'='*50}")
    print(f"Total rows:     {len(df)}")

    # Labeled vs unlabeled
    labeled_mask = df["label"].notna() & (df["label"].astype(str).str.strip() != "")
    labeled = df[labeled_mask]
    unlabeled = df[~labeled_mask]
    print(f"Labeled:        {len(labeled)}")
    print(f"Unlabeled:      {len(unlabeled)}")

    if len(labeled) == 0:
        print("\n⚠ No labeled rows yet — open data/raw_posts.csv and start annotating.")
        return

    # Label distribution
    print(f"\nLabel distribution:")
    counts = labeled["label"].value_counts()
    total = len(labeled)
    for label, count in counts.items():
        pct = count / total * 100
        bar = "█" * int(pct / 3)
        flag = " ⚠ IMBALANCED" if pct > 70 else ""
        print(f"  {label:<18} {count:>4}  ({pct:.1f}%)  {bar}{flag}")

    # Readiness check
    print(f"\nReadiness check:")
    if total >= 200:
        print(f"  ✓ {total} labeled rows (minimum 200 met)")
    else:
        print(f"  ✗ Only {total} labeled rows (need {200 - total} more)")

    max_pct = counts.max() / total * 100
    if max_pct <= 70:
        print(f"  ✓ No label above 70% ({max_pct:.1f}% max)")
    else:
        dominant = counts.idxmax()
        print(f"  ✗ '{dominant}' is {max_pct:.1f}% of labels — collect more minority examples")

    # Text length stats
    df["text_len"] = df["text"].astype(str).str.len()
    print(f"\nText length stats (all rows):")
    print(f"  Min:    {df['text_len'].min()} chars")
    print(f"  Median: {df['text_len'].median():.0f} chars")
    print(f"  Max:    {df['text_len'].max()} chars")

    short = df[df["text_len"] < 60]
    if len(short):
        print(f"  ⚠ {len(short)} rows under 60 chars — review before training")

    # Subreddit breakdown
    if "subreddit" in df.columns:
        print(f"\nBy subreddit:")
        print(df["subreddit"].value_counts().to_string())

    # Hard cases notes
    if "notes" in df.columns:
        noted = df[df["notes"].astype(str).str.strip() != ""]
        if len(noted):
            print(f"\nFlagged hard cases: {len(noted)}")
            for _, row in noted.head(5).iterrows():
                print(f"  [{row.get('label','?')}] {str(row['text'])[:80]}...")
                print(f"       Note: {row['notes']}")

    print()


if __name__ == "__main__":
    # Check raw file if it exists, also labeled if it exists
    check(OUTPUT_PATH)
    if os.path.exists(LABELED_PATH) and LABELED_PATH != OUTPUT_PATH:
        check(LABELED_PATH)
