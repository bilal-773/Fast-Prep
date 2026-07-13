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

missing_ans = api("GET", "questions", "?correct_option=is.null&select=id")
if missing_ans is not None:
    print(f"Current questions with missing correct_option in DB: {len(missing_ans)}")
else:
    print("Failed to fetch.")
