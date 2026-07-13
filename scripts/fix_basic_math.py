"""
Fix: Reassign a portion of advanced_math questions to basic_math.
FAST-NUCES test has both sections. Since the source PDFs didn't distinguish them,
we'll split: first ~300 math Qs → basic_math, rest stay as advanced_math.
This gives both sections a large enough random pool to draw from.
"""
import json, urllib.request, urllib.error, ssl, random

from db_config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY as SERVICE_KEY

BASE_URL = f"{SUPABASE_URL}/rest/v1"
ctx = ssl.create_default_context()
HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

UNIV_ID        = "1ab2082b-b156-4191-82dd-6873f6946614"
ADV_MATH_ID    = "a0ef72d3-8f2e-45cb-8126-f3a2b113413c"
BASIC_MATH_ID  = "6818bcea-0528-4e03-8594-2f2664a9e9db"

def api(method, endpoint, data=None, params=""):
    url = f"{BASE_URL}/{endpoint}{params}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()[:200]}")
        return None

# Step 1: Get all advanced_math question IDs (paginate to get all 883)
print("Fetching all advanced_math question IDs...")
all_adv_ids = []
offset = 0
batch = 500
while True:
    resp = api("GET", "questions",
               params=f"?category_id=eq.{ADV_MATH_ID}&select=id&limit={batch}&offset={offset}")
    if not resp:
        break
    all_adv_ids.extend([r["id"] for r in resp])
    if len(resp) < batch:
        break
    offset += batch

print(f"  Found {len(all_adv_ids)} advanced_math questions")

# Step 2: Randomly pick 300 to become basic_math
# We want: advanced_math pool >= 50*3 = 150 (plenty)
#          basic_math pool >= 20*3 = 60 (plenty)
# 300 → basic_math, 583 → keep advanced_math
random.seed(42)  # reproducible
random.shuffle(all_adv_ids)
basic_math_ids = all_adv_ids[:300]
print(f"  Reassigning {len(basic_math_ids)} questions to basic_math...")

# Step 3: Update in batches of 50 using PATCH with id filter
updated = 0
PATCH_HEADERS = dict(HEADERS)
PATCH_HEADERS["Prefer"] = "return=minimal"

for i in range(0, len(basic_math_ids), 50):
    chunk = basic_math_ids[i:i+50]
    id_list = ",".join(chunk)
    url = f"{BASE_URL}/questions?id=in.({id_list})"
    body = json.dumps({"category_id": BASIC_MATH_ID}).encode()
    req = urllib.request.Request(url, data=body, headers=PATCH_HEADERS, method="PATCH")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            updated += len(chunk)
    except urllib.error.HTTPError as e:
        print(f"  Error on chunk {i}: {e.read().decode()[:100]}")
    
    pct = min(100, int((i + 50) / len(basic_math_ids) * 100))
    print(f"  Progress: {pct}% | Updated: {updated}", end="\r")

print(f"\n  Done! Updated {updated} questions to basic_math")

# Step 4: Verify final counts
print("\n=== Final Verification ===")
cats = {
    "advanced_math": ADV_MATH_ID,
    "basic_math":    BASIC_MATH_ID,
    "iq":            "36c36d9c-1ea5-4d77-80ec-bb7edc1de655",
    "english":       "6dfdbcbc-8941-4010-a89b-49e0ef1cab43"
}

total = 0
for slug, cat_id in cats.items():
    # Use count header
    url = f"{BASE_URL}/questions?category_id=eq.{cat_id}&select=id"
    all_ids = []
    offset = 0
    while True:
        resp = api("GET", "questions",
                   params=f"?category_id=eq.{cat_id}&select=id&limit=1000&offset={offset}")
        if not resp:
            break
        all_ids.extend(resp)
        if len(resp) < 1000:
            break
        offset += 1000
    count = len(all_ids)
    total += count
    print(f"  {slug}: {count} questions")

print(f"\n  TOTAL in DB: {total}")
print("\nDatabase is fully ready!")
