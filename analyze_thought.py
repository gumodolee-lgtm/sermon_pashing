import os
import shutil
import re
from collections import defaultdict

SERMON_DIR = r"d:/Ai_aigent/_sermon_pashing/sermon"
OUTPUT_DIR = r"d:/Ai_aigent/_sermon_pashing/생각"
TOP_N = 300

# Keyword categories with weights
PRIMARY = {  # weight 5
    "생각": 5, "사고": 5, "마음을 새롭게": 5, "의식혁명": 5,
    "생각의 힘": 5, "생각을 바꾸": 5, "긍정적": 5, "부정적 생각": 5,
    "사고방식": 5, "마인드": 5, "생각하는": 5, "생각이": 5, "생각을": 5,
}

SECONDARY = {  # weight 3
    "마음": 3, "의식": 3, "정신": 3, "묵상": 3, "상상": 3,
    "태도": 3, "관점": 3, "시각": 3, "인식": 3, "판단": 3,
    "지혜": 3, "분별": 3, "깨달": 3, "통찰": 3, "심리": 3,
    "사상": 3, "관념": 3, "뜻을 품": 3, "마음의 눈": 3,
    "영적 사고": 3, "내면": 3, "자아": 3, "정체성": 3, "자존감": 3,
    "변화": 3, "혁신": 3, "새롭게": 3, "회개": 3, "회복": 3,
    "치유": 3, "결심": 3, "결단": 3, "작정": 3, "선택": 3,
}

TERTIARY = {  # weight 1
    "영성": 1, "영적": 1, "차원": 1, "능력": 1, "힘": 1,
    "믿음": 1, "기도": 1, "말씀": 1, "성령": 1, "소망": 1,
    "비전": 1, "꿈": 1, "계획": 1, "목표": 1, "성장": 1,
    "성숙": 1, "자유": 1, "해방": 1, "승리": 1,
}

# Combine all keywords
ALL_KEYWORDS = {}
ALL_KEYWORDS.update(TERTIARY)
ALL_KEYWORDS.update(SECONDARY)
ALL_KEYWORDS.update(PRIMARY)  # Primary last so it overwrites overlaps

# Primary keywords for title bonus
PRIMARY_TITLE_KEYWORDS = list(PRIMARY.keys())

def score_file(filepath, filename):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"  Error reading {filename}: {e}")
        return None

    if not content.strip():
        return None

    # Word count (Korean: rough estimate by splitting on whitespace)
    word_count = len(content.split())
    if word_count < 10:
        return None

    # Score content
    raw_score = 0
    keyword_hits = defaultdict(int)

    for keyword, weight in ALL_KEYWORDS.items():
        count = content.count(keyword)
        if count > 0:
            raw_score += weight * count
            keyword_hits[keyword] = count

    # Title bonus: check filename for primary keywords (weight 10)
    title_bonus = 0
    title = os.path.splitext(filename)[0]
    for keyword in PRIMARY_TITLE_KEYWORDS:
        if keyword in title:
            title_bonus += 10
            keyword_hits[f"[TITLE]{keyword}"] = 1

    raw_score += title_bonus

    # Normalize by length (per 1000 words)
    normalized_score = raw_score / (word_count / 1000) if word_count > 0 else 0

    # Final score: normalized + small bonus for raw (to prefer substantial content)
    # raw_bonus = log-scaled to dampen effect of very long files
    import math
    raw_bonus = math.log1p(raw_score) * 2
    final_score = normalized_score + raw_bonus

    return {
        "filename": filename,
        "final_score": final_score,
        "normalized_score": normalized_score,
        "raw_score": raw_score,
        "title_bonus": title_bonus,
        "word_count": word_count,
        "keyword_hits": dict(keyword_hits),
    }


def main():
    # Gather all txt files
    files = [f for f in os.listdir(SERMON_DIR) if f.endswith(".txt")]
    print(f"Found {len(files)} sermon files.\n")

    results = []
    for f in files:
        filepath = os.path.join(SERMON_DIR, f)
        result = score_file(filepath, f)
        if result:
            results.append(result)

    print(f"Successfully scored {len(results)} files.\n")

    # Sort by final_score descending
    results.sort(key=lambda x: x["final_score"], reverse=True)

    # Take top 300
    top = results[:TOP_N]

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Copy files
    copied = 0
    for r in top:
        src = os.path.join(SERMON_DIR, r["filename"])
        dst = os.path.join(OUTPUT_DIR, r["filename"])
        shutil.copy2(src, dst)
        copied += 1

    print(f"Copied {copied} files to {OUTPUT_DIR}\n")

    # Print top 300
    print("=" * 120)
    print(f"{'Rank':<6} {'Score':>8} {'Norm':>8} {'Raw':>7} {'Words':>7} {'TitleB':>7}  {'Filename'}")
    print("=" * 120)
    for i, r in enumerate(top, 1):
        print(f"{i:<6} {r['final_score']:>8.1f} {r['normalized_score']:>8.1f} {r['raw_score']:>7} {r['word_count']:>7} {r['title_bonus']:>7}  {r['filename']}")

    # Top 20 with keyword details
    print("\n" + "=" * 120)
    print("TOP 20 - Keyword Detail")
    print("=" * 120)
    for i, r in enumerate(top[:20], 1):
        print(f"\n#{i} [{r['final_score']:.1f}] {r['filename']}")
        # Sort hits by contribution (weight * count)
        hits = r["keyword_hits"]
        sorted_hits = sorted(hits.items(), key=lambda x: ALL_KEYWORDS.get(x[0].replace("[TITLE]", ""), 10) * x[1], reverse=True)
        top_keywords = sorted_hits[:15]
        kw_str = ", ".join([f"{k}({v})" for k, v in top_keywords])
        print(f"   Keywords: {kw_str}")

    # Summary statistics
    print("\n" + "=" * 120)
    print("SUMMARY STATISTICS")
    print("=" * 120)
    all_scores = [r["final_score"] for r in results]
    top_scores = [r["final_score"] for r in top]
    print(f"Total files scored: {len(results)}")
    print(f"Top {TOP_N} selected")
    print(f"Score range (all):    {min(all_scores):.1f} - {max(all_scores):.1f}")
    print(f"Score range (top300): {min(top_scores):.1f} - {max(top_scores):.1f}")
    print(f"Mean score (all):     {sum(all_scores)/len(all_scores):.1f}")
    print(f"Mean score (top300):  {sum(top_scores)/len(top_scores):.1f}")

    # Score distribution
    print(f"\nScore distribution (top 300):")
    brackets = [(200, float('inf')), (150, 200), (100, 150), (80, 100), (60, 80), (0, 60)]
    for lo, hi in brackets:
        count = sum(1 for s in top_scores if lo <= s < hi)
        label = f"{lo}-{hi}" if hi != float('inf') else f"{lo}+"
        print(f"  {label:>10}: {count} files")

    # Word count stats for top 300
    wc = [r["word_count"] for r in top]
    print(f"\nWord count (top 300): min={min(wc)}, max={max(wc)}, avg={sum(wc)//len(wc)}")


if __name__ == "__main__":
    main()
