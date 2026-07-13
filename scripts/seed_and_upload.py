import json
import urllib.request
import urllib.error
import ssl
import time

# ============================================================
# Config
# ============================================================
from db_config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY as SERVICE_KEY

BASE_URL = f"{SUPABASE_URL}/rest/v1"
ctx = ssl.create_default_context()

HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def api(method, endpoint, data=None, params=""):
    url = f"{BASE_URL}/{endpoint}{params}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        # Handle duplicate policy errors gracefully
        if e.code == 409 or "already exists" in body:
            return None  # already exists, ok
        print(f"  HTTP {e.code} on {method} {endpoint}: {body[:200]}")
        return None

# ============================================================
# Step 1: Insert University — FAST-NUCES
# ============================================================
print("=== Seeding University ===")
existing = api("GET", "universities", params="?slug=eq.fast-nuces")
if existing:
    univ = existing[0]
    print(f"  Already exists: {univ['name']} ({univ['id']})")
else:
    result = api("POST", "universities", {
        "name": "FAST-NUCES",
        "slug": "fast-nuces",
        "is_active": True
    })
    univ = result[0] if result else None
    print(f"  Created: {univ['name']} ({univ['id']})")

UNIV_ID = univ["id"]
print(f"  University ID: {UNIV_ID}")

# ============================================================
# Step 2: Insert Question Categories
# ============================================================
print("\n=== Seeding Question Categories ===")
categories_data = [
    {"name": "Advanced Mathematics", "slug": "advanced_math"},
    {"name": "Basic Mathematics",    "slug": "basic_math"},
    {"name": "IQ / Analytical Skills","slug": "iq"},
    {"name": "English",              "slug": "english"},
]

cat_map = {}  # slug -> id
for cat in categories_data:
    existing = api("GET", "question_categories", params=f"?university_id=eq.{UNIV_ID}&slug=eq.{cat['slug']}")
    if existing:
        cat_obj = existing[0]
        print(f"  Already exists: {cat_obj['name']} ({cat_obj['id']})")
    else:
        result = api("POST", "question_categories", {
            "university_id": UNIV_ID,
            "name": cat["name"],
            "slug": cat["slug"]
        })
        cat_obj = result[0] if result else None
        print(f"  Created: {cat_obj['name']} ({cat_obj['id']})")
    cat_map[cat["slug"]] = cat_obj["id"]

print(f"  Category map: {cat_map}")

# ============================================================
# Step 3: Insert University Test Configs
# ============================================================
print("\n=== Seeding University Test Configs ===")
# FAST-NUCES test structure (from AGENTS.md rules)
test_configs = [
    {"slug": "advanced_math", "question_count": 50, "time_minutes": 50},
    {"slug": "basic_math",    "question_count": 20, "time_minutes": 20},
    {"slug": "iq",            "question_count": 20, "time_minutes": 20},
    {"slug": "english",       "question_count": 30, "time_minutes": 10},
]

for cfg in test_configs:
    cat_id = cat_map[cfg["slug"]]
    existing = api("GET", "university_test_configs", params=f"?university_id=eq.{UNIV_ID}&category_id=eq.{cat_id}")
    if existing:
        print(f"  Already exists: {cfg['slug']}")
    else:
        result = api("POST", "university_test_configs", {
            "university_id": UNIV_ID,
            "category_id": cat_id,
            "question_count": cfg["question_count"],
            "time_minutes": cfg["time_minutes"],
            "marks_per_question": 1.0,
            "negative_marks": 0.0
        })
        obj = result[0] if result else None
        print(f"  Created config: {cfg['slug']} — {cfg['question_count']} Qs, {cfg['time_minutes']} mins")

# ============================================================
# Step 4: Upload Questions
# ============================================================
print("\n=== Uploading Questions ===")

with open("all_questions.json", "r", encoding="utf-8") as f:
    all_questions = json.load(f)

print(f"  Total questions in JSON: {len(all_questions)}")

# Check how many already exist
existing_count_resp = api("GET", "questions", params=f"?university_id=eq.{UNIV_ID}&select=id")
existing_count = len(existing_count_resp) if existing_count_resp else 0
print(f"  Already in DB: {existing_count}")

if existing_count >= len(all_questions):
    print("  All questions already uploaded. Skipping.")
else:
    # Map category slugs to IDs
    # JSON uses: english, iq, advanced_math, basic_math
    # Some might use 'math' as slug - let's check
    slugs_in_json = set(q.get("category_slug") for q in all_questions)
    print(f"  Category slugs in JSON: {slugs_in_json}")

    # Build rows to insert
    rows = []
    skipped = 0
    for q in all_questions:
        cat_slug = q.get("category_slug", "").strip()
        
        # Handle any slug variations
        if cat_slug not in cat_map:
            # Try to remap common variants
            remap = {
                "math": "advanced_math",
                "mathematics": "advanced_math",
                "analytical": "iq",
                "iq_analytical": "iq",
            }
            cat_slug = remap.get(cat_slug, cat_slug)
        
        if cat_slug not in cat_map:
            skipped += 1
            continue
        
        # Normalize correct_option
        correct = q.get("correct_option")
        if correct:
            correct = str(correct).strip().upper()
            if correct not in ("A", "B", "C", "D"):
                correct = None

        rows.append({
            "university_id": UNIV_ID,
            "category_id": cat_map[cat_slug],
            "question_text": str(q.get("question_text", "")).strip(),
            "option_a": str(q.get("option_a", "")).strip(),
            "option_b": str(q.get("option_b", "")).strip(),
            "option_c": str(q.get("option_c", "")).strip(),
            "option_d": str(q.get("option_d", "")).strip(),
            "correct_option": correct,
            "explanation": q.get("explanation"),
            "year": q.get("year"),
            "is_published": True,
            "is_verified": False
        })

    print(f"  Rows to insert: {len(rows)}  |  Skipped (unknown category): {skipped}")

    # Batch insert in chunks of 100
    BATCH = 100
    inserted = 0
    errors = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i+BATCH]
        result = api("POST", "questions", batch)
        if result is not None:
            inserted += len(result) if isinstance(result, list) else len(batch)
        else:
            errors += len(batch)
        
        pct = min(100, int((i + BATCH) / len(rows) * 100))
        print(f"  Progress: {pct}% ({min(i+BATCH, len(rows))}/{len(rows)}) | Inserted: {inserted} | Errors: {errors}", end="\r")
        time.sleep(0.05)  # gentle rate limiting

    print(f"\n  Done! Inserted: {inserted} | Errors: {errors}")

# ============================================================
# Final Summary
# ============================================================
print("\n=== Final Verification ===")
for slug, cat_id in cat_map.items():
    count_resp = api("GET", "questions", params=f"?category_id=eq.{cat_id}&select=id")
    count = len(count_resp) if count_resp else 0
    print(f"  {slug}: {count} questions")

total_resp = api("GET", "questions", params=f"?university_id=eq.{UNIV_ID}&select=id")
total = len(total_resp) if total_resp else 0
print(f"\n  TOTAL questions in DB: {total}")
print("\nDONE! Database is ready.")
