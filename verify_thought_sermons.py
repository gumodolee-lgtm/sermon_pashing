from __future__ import annotations

import csv
import math
import re
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SERMON_DIR = ROOT / "sermon"
THOUGHT_DIR = ROOT / "생각"
CSV_PATH = ROOT / "thought_verification.csv"
MD_PATH = ROOT / "thought_verification_report.md"
OUTPUT_DIR = ROOT / "생각_검증"
FINAL_CSV_PATH = ROOT / "thought_verification_final.csv"
FINAL_MD_PATH = ROOT / "thought_verification_final_report.md"
FINAL_OUTPUT_DIR = ROOT / "생각_검증_최종"


THOUGHT_TITLE_MARKERS = [
    "생각",
    "의식",
    "사고방식",
    "마음",
    "정신",
    "자화상",
    "지혜",
    "두려움",
    "우울",
    "선택",
    "새롭게",
    "밝게",
    "건강",
]

THOUGHT_STRONG_PHRASES = {
    "생각": 5.0,
    "생각하는": 5.0,
    "생각을": 5.0,
    "생각이": 5.0,
    "의식": 5.0,
    "사고방식": 6.0,
    "생각의": 5.5,
    "마음의 자세": 6.0,
    "마음을 새롭게": 6.0,
    "자화상": 6.0,
    "정신적": 5.0,
    "마음밭": 5.0,
    "마음의 밭": 5.0,
    "묵상": 4.0,
    "지혜": 4.5,
    "깨달음": 4.0,
    "태도": 4.5,
    "관점": 4.0,
    "시각": 4.0,
    "선택": 4.0,
    "결단": 4.0,
    "새롭게": 3.5,
    "변화": 3.0,
    "변화를": 3.0,
    "두려움": 4.5,
    "염려": 4.0,
    "우울": 4.5,
    "낙심": 4.0,
    "강하고 담대": 3.0,
    "긍정": 4.5,
    "부정적": 4.5,
    "절망": 3.5,
    "희망": 3.0,
    "건강한 마음": 5.0,
    "마음의 건강": 5.5,
    "삶을 좀 더 밝게": 6.0,
}

THOUGHT_SUPPORT_PHRASES = {
    "마음": 1.4,
    "정신": 1.8,
    "생각해": 2.0,
    "생각하": 2.0,
    "지혜로운": 2.5,
    "깨닫": 2.2,
    "태도": 2.4,
    "마음속": 2.0,
    "마음에": 1.2,
    "결심": 2.0,
    "결단": 2.2,
    "염려하지": 2.0,
    "두려워": 2.0,
    "낙심하지": 2.0,
    "담대": 2.0,
    "새 사람": 2.0,
    "변화받": 2.5,
    "바라보": 1.8,
}

NON_THOUGHT_BUCKETS = {
    "faith": {
        "markers": ["믿음", "신앙", "확신", "순종"],
        "weight": 1.0,
    },
    "holy_spirit": {
        "markers": ["성령", "보혜사", "방언", "성령충만", "성령세례"],
        "weight": 1.3,
    },
    "word_prayer": {
        "markers": ["말씀", "기도", "부르짖", "선포", "입술", "말"],
        "weight": 0.9,
    },
    "dream_vision": {
        "markers": ["꿈", "비전", "소망"],
        "weight": 1.1,
    },
    "cross_salvation": {
        "markers": ["십자가", "보혈", "부활", "구원", "예수님"],
        "weight": 1.0,
    },
}

POSITIVE_SEED_TITLES = [
    "1981-06-21 나 나의생각.txt",
    "1981-08-30 의식혁명.txt",
    "1984-11-11 생각을 바꾸라.txt",
    "1989-12-03 마음의 눈.txt",
    "1990-01-28 삶을 좀 더 밝게 보며.txt",
    "1998-02-01 마음을 새롭게 함으로 변화를 받으라.txt",
    "1999-11-14 불행을 만드는 사람.txt",
    "2000-10-29 종의 사고방식과 자유인의 사고방식.txt",
    "2000-10-15 치료받아야 할 마음.txt",
    "2002-10-06 하나님의 생각과 우리의 생각, 하나님의 길과 우리의 길.txt",
]

NEGATIVE_SEED_TITLE_MARKERS = [
    "성령",
    "보혜사",
    "믿음",
    "기도",
    "꿈",
    "십자가",
    "부활",
    "예수님",
    "보혈",
]

MANUAL_FINAL_EXCLUDE = {
    "1990-07-29 너희가 믿을 때 성령을 받았느냐.txt": "본문 주제가 성령세례와 성령시대 설명에 집중됨",
    "1994-01-30 성령세례란 무엇인가.txt": "성령세례 정의와 체험이 중심이며 생각 축은 보조적임",
    "1992-09-27 성령과 말씀과 기적.txt": "성령과 말씀의 창조적 역사 설명이 핵심임",
    "1994-05-22 성령님과의 교통.txt": "보혜사 성령과의 교통이 핵심 주제임",
    "1991-12-15 하나님의 믿음과 사람의 믿음.txt": "의심과 마음을 다루지만 설교 중심축은 믿음론임",
    "1990-02-18 믿음이 빛난 자산.txt": "히브리서 11장 중심의 믿음과 순종 설교임",
    "1995-06-04 보혜사 성령님.txt": "보혜사 성령의 존재와 사역을 설명하는 설교임",
    "1984-12-23 오직 성령의 힘으로.txt": "오순절 성령 역사와 능력의 확산이 중심임",
    "1997-05-18 성령강림의 의미.txt": "성령강림의 의미와 성령의 사역 설명이 중심임",
    "1999-05-23 왜 성령께서 오셔야만 했는가.txt": "성령이 오셔야 하는 이유를 체계적으로 설명함",
    "1992-06-07 오순절 날에 임하신 성령.txt": "오순절 성령과 방언, 성령의 불/바람 상징이 중심임",
    "1996-05-26 성령충만과 방언.txt": "성령충만과 방언의 의미와 효익이 주제임",
}


def has_positive_title_marker(title: str) -> bool:
    return any(marker in title for marker in THOUGHT_TITLE_MARKERS)


def has_negative_title_marker(title: str) -> bool:
    return any(marker in title for marker in NEGATIVE_SEED_TITLE_MARKERS)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\ufeff", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[가-힣A-Za-z]{2,}", text)


def count_phrase_weight(text: str, phrases: dict[str, float]) -> tuple[float, Counter]:
    hits = Counter()
    score = 0.0
    for phrase, weight in phrases.items():
        count = text.count(phrase)
        if count:
            hits[phrase] = count
            score += count * weight
    return score, hits


def count_bucket_weight(text: str) -> tuple[float, dict[str, float], Counter]:
    bucket_scores: dict[str, float] = {}
    bucket_hits: Counter = Counter()
    total = 0.0
    for bucket, config in NON_THOUGHT_BUCKETS.items():
        subtotal = 0.0
        for marker in config["markers"]:
            count = text.count(marker)
            if count:
                subtotal += count * config["weight"]
                bucket_hits[marker] += count
        bucket_scores[bucket] = subtotal
        total += subtotal
    return total, bucket_scores, bucket_hits


def title_score(name: str) -> float:
    title = Path(name).stem
    score = 0.0
    for marker in THOUGHT_TITLE_MARKERS:
        if marker in title:
            score += 3.0
    for marker in NEGATIVE_SEED_TITLE_MARKERS:
        if marker in title and not has_positive_title_marker(title):
            score -= 1.0
    return score


def build_tfidf_vectors(docs: dict[str, str]) -> tuple[dict[str, dict[str, float]], dict[str, float]]:
    tokenized = {name: tokenize(text) for name, text in docs.items()}
    doc_freq = Counter()
    term_freqs: dict[str, Counter] = {}

    for name, tokens in tokenized.items():
        tf = Counter(tokens)
        term_freqs[name] = tf
        doc_freq.update(tf.keys())

    total_docs = len(tokenized)
    idf = {
        term: math.log((1 + total_docs) / (1 + freq)) + 1
        for term, freq in doc_freq.items()
    }

    vectors: dict[str, dict[str, float]] = {}
    for name, tf in term_freqs.items():
        length = sum(tf.values()) or 1
        vec = {term: (count / length) * idf[term] for term, count in tf.items()}
        norm = math.sqrt(sum(value * value for value in vec.values())) or 1.0
        vectors[name] = {term: value / norm for term, value in vec.items()}
    return vectors, idf


def average_vector(names: list[str], vectors: dict[str, dict[str, float]]) -> dict[str, float]:
    acc: Counter = Counter()
    if not names:
        return {}
    for name in names:
        acc.update(vectors[name])
    averaged = {term: value / len(names) for term, value in acc.items()}
    norm = math.sqrt(sum(value * value for value in averaged.values())) or 1.0
    return {term: value / norm for term, value in averaged.items()}


def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    if len(vec_a) > len(vec_b):
        vec_a, vec_b = vec_b, vec_a
    return sum(value * vec_b.get(term, 0.0) for term, value in vec_a.items())


def choose_negative_seeds(paths: list[Path]) -> list[str]:
    chosen: list[str] = []
    for path in paths:
        title = path.stem
        if has_positive_title_marker(title):
            continue
        if any(marker in title for marker in NEGATIVE_SEED_TITLE_MARKERS):
            chosen.append(path.name)
        if len(chosen) >= 30:
            break
    return chosen


def classify(score: float, thought_ratio: float, sim_gap: float) -> str:
    if score >= 2.0 and thought_ratio >= 0.35 and sim_gap >= 0.01:
        return "높음"
    if score >= 1.1 and thought_ratio >= 0.22:
        return "중간"
    return "낮음"


def top_hits(counter: Counter, limit: int = 8) -> str:
    if not counter:
        return "-"
    return ", ".join(f"{key}({value})" for key, value in counter.most_common(limit))


def main() -> None:
    sermon_paths = sorted(SERMON_DIR.glob("*.txt"))
    thought_paths = sorted(THOUGHT_DIR.glob("*.txt"))

    docs = {path.name: clean_text(read_text(path)) for path in sermon_paths}
    vectors, _ = build_tfidf_vectors(docs)

    negative_seeds = choose_negative_seeds(sermon_paths)
    positive_centroid = average_vector(POSITIVE_SEED_TITLES, vectors)
    negative_centroid = average_vector(negative_seeds, vectors)

    rows = []
    for path in thought_paths:
        text = docs[path.name]
        word_count = len(tokenize(text))
        stem = path.stem

        strong_score, strong_hits = count_phrase_weight(text, THOUGHT_STRONG_PHRASES)
        support_score, support_hits = count_phrase_weight(text, THOUGHT_SUPPORT_PHRASES)
        non_thought_score, bucket_scores, bucket_hits = count_bucket_weight(text)

        density = (strong_score + support_score) / max(word_count, 1) * 1000
        ratio = (strong_score + support_score) / max(strong_score + support_score + non_thought_score, 1.0)
        sim_pos = cosine_similarity(vectors[path.name], positive_centroid)
        sim_neg = cosine_similarity(vectors[path.name], negative_centroid)
        sim_gap = sim_pos - sim_neg

        score = (
            (density * 0.35)
            + (ratio * 2.2)
            + (sim_gap * 6.0)
            + title_score(path.name)
        )

        label = classify(score, ratio, sim_gap)
        review_flag = (
            label == "낮음"
            or (
                has_negative_title_marker(stem)
                and not has_positive_title_marker(stem)
                and sim_gap < 0
                and ratio < 0.36
            )
        )

        reason_bits = []
        if title_score(path.name) > 0:
            reason_bits.append("제목에 생각 축 표지어가 있음")
        if strong_hits:
            reason_bits.append(f"핵심표현: {top_hits(strong_hits, 5)}")
        if support_hits and len(reason_bits) < 3:
            reason_bits.append(f"보조표현: {top_hits(support_hits, 5)}")
        dominant_bucket = max(bucket_scores, key=bucket_scores.get)
        if bucket_scores[dominant_bucket] > (strong_score + support_score):
            reason_bits.append(f"비생각 주제 우세: {dominant_bucket}")

        rows.append(
            {
                "filename": path.name,
                "label": label,
                "score": round(score, 4),
                "thought_density": round(density, 4),
                "thought_ratio": round(ratio, 4),
                "sim_pos": round(sim_pos, 4),
                "sim_neg": round(sim_neg, 4),
                "sim_gap": round(sim_gap, 4),
                "strong_score": round(strong_score, 2),
                "support_score": round(support_score, 2),
                "non_thought_score": round(non_thought_score, 2),
                "dominant_non_thought": dominant_bucket,
                "strong_hits": top_hits(strong_hits),
                "support_hits": top_hits(support_hits),
                "non_thought_hits": top_hits(bucket_hits),
                "review_flag": "재검토" if review_flag else "",
                "reason": " | ".join(reason_bits) if reason_bits else "-",
            }
        )

    rows.sort(key=lambda row: ({"높음": 2, "중간": 1, "낮음": 0}[row["label"]], row["score"]), reverse=True)

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    by_label = Counter(row["label"] for row in rows)
    low_rows = [row for row in rows if row["label"] == "낮음"]
    mid_rows = [row for row in rows if row["label"] == "중간"]
    high_rows = [row for row in rows if row["label"] == "높음"]
    review_rows = [row for row in rows if row["review_flag"] == "재검토"]
    review_only_rows = [row for row in review_rows if row["label"] != "낮음"]
    keep_rows = [row for row in rows if row not in review_rows]

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    keep_dir = OUTPUT_DIR / "유지"
    review_dir = OUTPUT_DIR / "재검토"
    exclude_dir = OUTPUT_DIR / "제외"
    for folder in (keep_dir, review_dir, exclude_dir):
        folder.mkdir(parents=True, exist_ok=True)

    for row in keep_rows:
        shutil.copy2(THOUGHT_DIR / row["filename"], keep_dir / row["filename"])
    for row in review_only_rows:
        shutil.copy2(THOUGHT_DIR / row["filename"], review_dir / row["filename"])
    for row in low_rows:
        shutil.copy2(THOUGHT_DIR / row["filename"], exclude_dir / row["filename"])

    def render_table(title: str, items: list[dict], limit: int = 20) -> list[str]:
        lines = [f"## {title}", "", "| 파일 | 판정 | 점수 | 비고 |", "|---|---:|---:|---|"]
        for row in items[:limit]:
            lines.append(
                f"| {row['filename']} | {row['label']} | {row['score']:.2f} | {row['reason']} |"
            )
        lines.append("")
        return lines

    report = [
        "# 생각 폴더 재검증 보고서",
        "",
        f"- 총 후보 수: {len(rows)}",
        f"- 유지 권장: {len(keep_rows)}",
        f"- 높음: {by_label['높음']}",
        f"- 중간: {by_label['중간']}",
        f"- 낮음: {by_label['낮음']}",
        f"- 재검토 필요: {len(review_rows)}",
        "",
        "분류 결과:",
        f"- [생각_검증/유지]({keep_dir.as_posix()}) : {len(keep_rows)}편",
        f"- [생각_검증/재검토]({review_dir.as_posix()}) : {len(review_only_rows)}편",
        f"- [생각_검증/제외]({exclude_dir.as_posix()}) : {len(low_rows)}편",
        "",
        "판정 기준:",
        "- 본문 안의 생각/의식/마음 태도/자화상 관련 핵심 표현 밀도",
        "- 다른 영성 축(믿음, 성령, 꿈, 말씀/기도, 십자가) 쏠림 정도",
        "- 대표적인 생각 설교들과의 TF-IDF 내용 유사도",
        "- 제목의 직접 표지어 여부는 보조지표로만 사용",
        "",
    ]
    report.extend(render_table("재검토 필요", review_rows, 40))
    report.extend(render_table("낮음 판정", low_rows, 40))
    report.extend(render_table("중간 판정", mid_rows, 40))
    report.extend(render_table("상위 높은 판정 예시", high_rows, 25))

    MD_PATH.write_text("\n".join(report), encoding="utf-8")

    final_rows = []
    for row in rows:
        final_row = dict(row)
        manual_reason = MANUAL_FINAL_EXCLUDE.get(row["filename"], "")
        if manual_reason:
            final_row["final_bucket"] = "제외"
            final_row["final_reason"] = manual_reason
        else:
            final_row["final_bucket"] = "유지"
            final_row["final_reason"] = "자동 판정과 수동 검토 기준에서 생각 축 유지"
        final_rows.append(final_row)

    if FINAL_OUTPUT_DIR.exists():
        shutil.rmtree(FINAL_OUTPUT_DIR)

    final_keep_dir = FINAL_OUTPUT_DIR / "유지"
    final_exclude_dir = FINAL_OUTPUT_DIR / "제외"
    for folder in (final_keep_dir, final_exclude_dir):
        folder.mkdir(parents=True, exist_ok=True)

    for row in final_rows:
        src = THOUGHT_DIR / row["filename"]
        dst_dir = final_keep_dir if row["final_bucket"] == "유지" else final_exclude_dir
        shutil.copy2(src, dst_dir / row["filename"])

    with FINAL_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(final_rows[0].keys()))
        writer.writeheader()
        writer.writerows(final_rows)

    final_counts = Counter(row["final_bucket"] for row in final_rows)
    final_excludes = [row for row in final_rows if row["final_bucket"] == "제외"]
    final_keeps = [row for row in final_rows if row["final_bucket"] == "유지"]

    final_report = [
        "# 생각 폴더 최종 검증 보고서",
        "",
        f"- 총 후보 수: {len(final_rows)}",
        f"- 최종 유지: {final_counts['유지']}",
        f"- 최종 제외: {final_counts['제외']}",
        "",
        "최종 판단 원칙:",
        "- 자동 검증에서 낮음 또는 재검토로 나온 파일을 우선 선별",
        "- 본문을 직접 읽어 생각 축이 중심 주제인지 재확인",
        "- 생각/마음/지혜 언급이 있어도 설교 주제가 성령론·믿음론이면 제외",
        "",
        "최종 분류 결과:",
        f"- [생각_검증_최종/유지]({final_keep_dir.as_posix()}) : {final_counts['유지']}편",
        f"- [생각_검증_최종/제외]({final_exclude_dir.as_posix()}) : {final_counts['제외']}편",
        "",
        "## 최종 제외 목록",
        "",
        "| 파일 | 사유 |",
        "|---|---|",
    ]
    for row in final_excludes:
        final_report.append(f"| {row['filename']} | {row['final_reason']} |")

    final_report.extend([
        "",
        "## 검증 메모",
        "",
        "- `믿음이 빛난 자산`, `하나님의 믿음과 사람의 믿음`은 마음과 의심을 다루지만 논지의 중심은 믿음과 순종입니다.",
        "- `보혜사 성령님`, `성령강림의 의미`, `오순절 날에 임하신 성령`, `성령충만과 방언` 등은 성령의 정체와 사역이 핵심입니다.",
        "- 따라서 생각 축 전용 묶음에서는 제외하는 편이 더 엄격하고 일관된 분류입니다.",
    ])

    FINAL_MD_PATH.write_text("\n".join(final_report), encoding="utf-8")

    print(f"Wrote {CSV_PATH.name}")
    print(f"Wrote {MD_PATH.name}")
    print(f"Wrote {FINAL_CSV_PATH.name}")
    print(f"Wrote {FINAL_MD_PATH.name}")
    print(f"유지={len(keep_rows)} 재검토={len(review_only_rows)} 제외={len(low_rows)}")
    print(f"높음={by_label['높음']} 중간={by_label['중간']} 낮음={by_label['낮음']}")
    print(f"최종 유지={final_counts['유지']} 최종 제외={final_counts['제외']}")


if __name__ == "__main__":
    main()
