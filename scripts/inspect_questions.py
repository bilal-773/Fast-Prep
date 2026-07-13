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
    "Content-Type": "application/json"
}

def api(method, endpoint, params=""):
    url = f"{BASE_URL}/{endpoint}{params}"
    req = urllib.request.Request(url, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode()[:300]}")
        return None

print("Fetching questions with missing correct_option...")
missing_ans = api("GET", "questions", "?correct_option=is.null&select=id,question_text,option_a,option_b,option_c,option_d,category_id")
if missing_ans is not None:
    print(f"Found {len(missing_ans)} questions with missing correct_option.")
    for idx, q in enumerate(missing_ans[:10]):
        print(f"{idx+1}. ID: {q['id']}")
        print(f"   Text: {q['question_text']}")
        print(f"   Options: A: {q['option_a']}, B: {q['option_b']}, C: {q['option_c']}, D: {q['option_d']}")
else:
    print("Failed to fetch.")

print("\nFetching some integration/differentiation questions to inspect their formatting...")
# We will search for questions containing "integral", "derivative", "integrate", "differentiate" or math symbols
all_qs = api("GET", "questions", "?select=id,question_text,correct_option&limit=100")
int_diff_qs = []
if all_qs:
    for q in all_qs:
        text = q['question_text'].lower()
        if "integr" in text or "deriv" in text or "diff" in text or "dy/dx" in text or "d/dx" in text:
            int_diff_qs.append(q)
    print(f"Found {len(int_diff_qs)} match(es) in the first 100 questions:")
    for idx, q in enumerate(int_diff_qs[:10]):
        print(f"{idx+1}. Text: {q['question_text']}")
