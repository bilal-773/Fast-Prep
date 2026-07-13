"""
batch_extract_all.py

Runs extract_questions.py on every PDF in the fast past papers folder,
saves per-PDF JSON files, then merges all into one master JSON file.
Supports both text-based and image-based (scanned) PDFs automatically.
"""

import os
import sys
import json
import subprocess
import re

# ────────── Config ──────────
PAPERS_DIR = r"C:\Users\M Bilal\Desktop\uni\fast past papers"
OUTPUT_DIR = r"C:\Users\M Bilal\Desktop\uni\extracted"
SCRIPT_PATH = r"C:\Users\M Bilal\Desktop\uni\scripts\extract_questions.py"
MASTER_OUTPUT = r"C:\Users\M Bilal\Desktop\uni\all_questions.json"

PYTHON = sys.executable  # same python that is running this script

# PDF → metadata mapping (university, category override, year)
# category = None → let GPT guess from content
PDF_META = {
    "FAST-ENGLISH-PAST-PAPER-MCQS.pdf":           {"category": "english", "year": None},
    "FAST ENTRY TEST PAST PAPERS.pdf":             {"category": None,      "year": None},
    "FAST ENTRY TEST PAST PAPERS-1.pdf":           {"category": None,      "year": None},
    "FAST ENTRY TEST PAST PAPERS 1 PakLearningSpot.pdf": {"category": None, "year": None},
    "FAST Entry Test Past Papers 2023 PLS.pdf":    {"category": None,      "year": 2023},
    "FAST Entry Test Past Papers PLS 2024.pdf":    {"category": None,      "year": 2024},
    "FAST FLP 3 BY KIPS.pdf":                     {"category": None,      "year": None},
    "FAST PAST PAPER 1 IQ SOLVED.pdf":            {"category": "iq",      "year": None},
    "FAST PAST PAPER 3 IQ SOLVED.pdf":            {"category": "iq",      "year": None},
    "FAST PAST PAPER.pdf":                        {"category": None,      "year": None},
    "FAST PAST PAPERS 01.pdf":                    {"category": None,      "year": None},
    "fast paper 2_PakLearningSpot.pdf":           {"category": None,      "year": None},
}


def normalize_text(text):
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text


def slugify(name):
    """Turn a filename into a safe output slug."""
    name = os.path.splitext(name)[0]
    name = re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_').lower()
    return name


def run_extraction(pdf_path, output_path, category=None, year=None):
    """Call extract_questions.py as a subprocess for one PDF."""
    cmd = [
        PYTHON, SCRIPT_PATH,
        "--pdf", pdf_path,
        "--university", "fast-nuces",
        "--output", output_path,
        "--pages", "all",
    ]
    if category:
        cmd += ["--category", category]
    if year:
        cmd += ["--year", str(year)]

    print(f"\n{'='*60}")
    print(f"Running: {os.path.basename(pdf_path)}")
    print(f"  Output: {output_path}")
    print(f"  Category override: {category or 'auto'}")
    print(f"  Year: {year or 'unknown'}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode == 0


def merge_all(output_dir, master_output):
    """Read all per-PDF JSON files and merge into one deduplicated master list."""
    all_questions = []
    seen = set()
    duplicates = 0

    json_files = [f for f in os.listdir(output_dir) if f.endswith(".json")]
    print(f"\nMerging {len(json_files)} extracted JSON file(s) into master list...")

    for fname in sorted(json_files):
        fpath = os.path.join(output_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                questions = json.load(f)
            source_count = len(questions)
            added = 0
            for q in questions:
                q_text = q.get("question_text", "")
                norm = normalize_text(q_text)
                if norm and norm not in seen:
                    seen.add(norm)
                    all_questions.append(q)
                    added += 1
                else:
                    duplicates += 1
            print(f"  {fname}: {source_count} questions, {added} unique added.")
        except Exception as e:
            print(f"  Warning: could not read {fname}: {e}")

    print(f"\nTotal unique questions: {len(all_questions)}")
    print(f"Total duplicates removed: {duplicates}")

    with open(master_output, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=2, ensure_ascii=False)

    print(f"\nMaster file saved to: {master_output}")
    return all_questions


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pdfs = [f for f in os.listdir(PAPERS_DIR) if f.lower().endswith(".pdf")]
    print(f"Found {len(pdfs)} PDF files in '{PAPERS_DIR}'")

    success_count = 0
    fail_count = 0
    skipped_count = 0

    for pdf_name in sorted(pdfs):
        pdf_path = os.path.join(PAPERS_DIR, pdf_name)
        slug = slugify(pdf_name)
        output_path = os.path.join(OUTPUT_DIR, f"{slug}.json")

        # Skip if already extracted (re-run is expensive with Vision API)
        if os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if len(existing) > 0:
                    print(f"\nSkipping (already extracted {len(existing)} questions): {pdf_name}")
                    skipped_count += 1
                    continue
            except Exception:
                pass  # corrupted output → re-extract

        meta = PDF_META.get(pdf_name, {})
        category = meta.get("category")
        year = meta.get("year")

        ok = run_extraction(pdf_path, output_path, category=category, year=year)
        if ok:
            success_count += 1
        else:
            print(f"  !! Extraction FAILED for: {pdf_name}")
            fail_count += 1

    print(f"\n\n{'='*60}")
    print(f"Batch complete: {success_count} succeeded, {fail_count} failed, {skipped_count} skipped.")
    print(f"{'='*60}")

    # Merge everything
    all_questions = merge_all(OUTPUT_DIR, MASTER_OUTPUT)

    # Print category breakdown
    cat_counts = {}
    for q in all_questions:
        cat = q.get("category_slug", "unknown")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    print("\nQuestions by category:")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
