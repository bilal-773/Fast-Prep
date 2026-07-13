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

# Fetch category mapping
categories = api("GET", "question_categories")
cat_map = {c['slug']: c['id'] for c in categories}
print("Categories:", cat_map)

# Get all questions
all_qs = []
offset = 0
while True:
    qs = api("GET", "questions", f"?select=id,question_text,correct_option,category_id&limit=1000&offset={offset}")
    if not qs:
        break
    all_qs.extend(qs)
    if len(qs) < 1000:
        break
    offset += 1000

print(f"Total questions in database: {len(all_qs)}")

# Filter math categories
math_cat_ids = [cat_map['advanced_math'], cat_map['basic_math']]
math_qs = [q for q in all_qs if q['category_id'] in math_cat_ids]
print(f"Total math questions in DB: {len(math_qs)}")

# Categorize integration / differentiation
int_qs = []
diff_qs = []
other_math_qs = []

for q in math_qs:
    text = q['question_text'].lower()
    is_int = any(k in text for k in ["integral", "integrate", "integration", "∫"])
    is_diff = any(k in text for k in ["derivative", "differentiate", "differentiation", "dy/dx", "d/dx"])
    
    if is_int:
        int_qs.append(q)
    elif is_diff:
        diff_qs.append(q)
    else:
        other_math_qs.append(q)

print(f"Integration questions: {len(int_qs)}")
print(f"Differentiation questions: {len(diff_qs)}")

with open("db_math_qs.txt", "w", encoding="utf-8") as f:
    f.write("=== INTEGRATION QUESTIONS ===\n")
    for idx, q in enumerate(int_qs):
        f.write(f"{idx+1}. ID: {q['id']} | TEXT: {q['question_text']} | ANS: {q['correct_option']}\n")
    
    f.write("\n=== DIFFERENTIATION QUESTIONS ===\n")
    for idx, q in enumerate(diff_qs):
        f.write(f"{idx+1}. ID: {q['id']} | TEXT: {q['question_text']} | ANS: {q['correct_option']}\n")

print("Saved report to db_math_qs.txt")
