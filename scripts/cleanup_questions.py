import json
import urllib.request
import urllib.error
import ssl
import sys

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
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode('utf-8')[:300]}")
        return None

def main():
    print("Fetching all questions from Supabase...")
    all_qs = []
    offset = 0
    batch = 1000
    while True:
        resp = api("GET", "questions", params=f"?select=id,question_text,category_id&limit={batch}&offset={offset}")
        if not resp:
            break
        all_qs.extend(resp)
        if len(resp) < batch:
            break
        offset += batch

    print(f"Loaded {len(all_qs)} questions from DB.")

    bad_ids = []
    for q in all_qs:
        text = str(q.get("question_text", "")).strip()
        text_lower = text.lower()
        
        # Criteria 1: Too short / junk text
        if len(text) < 8 or text.isdigit():
            bad_ids.append(q["id"])
            continue

        # Criteria 2: Shape / Figure references (since we can't display images)
        shape_keywords = [
            "figure above", "figure below", "figure shown", "shown in the figure",
            "enclosed by the figure", "shaded region", "diagram above", "diagram below",
            "pattern below", "following pattern", "missing shape", "next shape", "the graph below",
            "in the graph", "graph above", "graph shown", "shown in the graph"
        ]
        
        if any(keyword in text_lower for keyword in shape_keywords):
            bad_ids.append(q["id"])
            continue

    print(f"Identified {len(bad_ids)} questions to unpublish/hide.")

    if not bad_ids:
        print("No bad questions found.")
        return

    # Update is_published = false in chunks
    PATCH_HEADERS = dict(HEADERS)
    PATCH_HEADERS["Prefer"] = "return=minimal"
    
    updated = 0
    chunk_size = 50
    for i in range(0, len(bad_ids), chunk_size):
        chunk = bad_ids[i:i+chunk_size]
        id_list = ",".join(chunk)
        url = f"{BASE_URL}/questions?id=in.({id_list})"
        body = json.dumps({"is_published": False}).encode('utf-8')
        req = urllib.request.Request(url, data=body, headers=PATCH_HEADERS, method="PATCH")
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
                updated += len(chunk)
        except Exception as e:
            print(f"Error updating chunk {i}: {e}")
        
        print(f"Progress: {int((i+len(chunk))/len(bad_ids)*100)}% | Hidden: {updated}", end="\r")

    print(f"\nSuccessfully hidden {updated} bad questions from active pool.")

if __name__ == "__main__":
    main()
