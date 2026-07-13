import json
import urllib.request
import urllib.error
import ssl

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
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode()}")
        return None

# Find the category ID for English
english_cat = api("GET", "question_categories", params="?slug=eq.english")
if english_cat:
    english_cat_id = english_cat[0]["id"]
    print(f"Found English category ID: {english_cat_id}")
    
    # Update university_test_configs where category_id is english_cat_id to time_minutes = 30
    res = api("PATCH", "university_test_configs", {"time_minutes": 30}, params=f"?category_id=eq.{english_cat_id}")
    print("Updated English test config time to 30 minutes:", res)

# Verify configs
configs = api("GET", "university_test_configs", params="?select=*,category:question_categories(name,slug)")
if configs:
    print("\nVerified Configs:")
    total_mins = 0
    for c in configs:
        name = c["category"]["name"]
        mins = c["time_minutes"]
        total_mins += mins
        print(f"  - {name}: {c['question_count']} Qs, {mins} mins")
    print(f"Total time config: {total_mins} minutes")
