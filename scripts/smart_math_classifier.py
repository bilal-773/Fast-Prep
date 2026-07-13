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

# Topic keywords for Advanced Math (from the list of 21 topics)
ADV_KEYWORDS = [
    # 01 Complex numbers
    "complex number", "imaginary", " argand", "conjugate",
    # 02 Sets, functions, groups
    "venn diagram", "binary operation", "group properties", " bijection", " surjection", " injection",
    # 03 Matrices
    "matrix", "matrices", "determinant", "transpose", "cramer", "inverse of the",
    # 04 Quadratic
    "quadratic", " roots ", "discriminant",
    # 05 Partial fractions
    "partial fraction",
    # 06 Sequences
    "progression", "arithmetic mean", "geometric mean", "harmonic mean", "nth term",
    " A.P.", " G.P.", " H.P.", "geometric series",
    # 07 Permutations
    "permutation", "combination", "factorial", "npr", "ncr",
    # 08 Induction / Binomial
    "binomial", "induction", "coefficient of x", "expansion of",
    # 09-14 Trigonometry
    "trigonometr", " sin ", " cos ", " tan ", "theta", "θ", "cosec", " sec ", " cot ",
    "radian", "quadrant", "law of sines", "law of cosines", "arcsin", "arccos", "arctan",
    "sin^-1", "cos^-1", "tan^-1", "trigonometric",
    # 15-17 Limits & Calculus
    " limit", "continuity", "continuous", "l'hopital", "differentiat", "derivativ",
    "dy/dx", "implicit function", "parametric equation", "tangent to the", "normal to the",
    "integrat", "integral", "definite", "indefinite", "calculus",
    # 18-20 Analytical Geometry & Conics
    "straight line", " tangent", "normal", "slope of the line", "perpendicular",
    "parallel line", "equation of the circle", "parabola", "ellipse", "hyperbola",
    " eccentricity", "directrix", "conic",
    # 21 Vectors
    "vector", "dot product", "cross product", "scalar product", "vector product",
    "unit vector", "magnitude of", "collinear", "coplanar", "projection of"
]

def main():
    # Category IDs
    ADV_MATH_ID    = "a0ef72d3-8f2e-45cb-8126-f3a2b113413c"
    BASIC_MATH_ID  = "6818bcea-0528-4e03-8594-2f2664a9e9db"

    print("Fetching all math questions...")
    math_qs = []
    offset = 0
    batch = 1000
    while True:
        # Fetch both categories
        resp = api("GET", "questions", 
                   params=f"?category_id=in.({ADV_MATH_ID},{BASIC_MATH_ID})&select=id,question_text,category_id&limit={batch}&offset={offset}")
        if not resp:
            break
        math_qs.extend(resp)
        if len(resp) < batch:
            break
        offset += batch

    print(f"Found {len(math_qs)} total math questions in DB.")

    adv_pool = []
    basic_pool = []

    for q in math_qs:
        text = str(q.get("question_text", "")).strip()
        text_lower = text.lower()
        
        # Smart matching
        is_advanced = False
        for kw in ADV_KEYWORDS:
            if kw.lower() in text_lower:
                is_advanced = True
                break
        
        # Override for specific edge cases (e.g. nPr, nCr, AP, GP as standalone uppercase words)
        words = text_lower.split()
        if "ap" in words or "gp" in words or "hp" in words or "npr" in words or "ncr" in words:
            is_advanced = True

        if is_advanced:
            adv_pool.append(q)
        else:
            basic_pool.append(q)

    print("\n--- Classification Summary ---")
    print(f"Advanced Math Pool size: {len(adv_pool)}")
    print(f"Basic Math Pool size:    {len(basic_pool)}")
    
    # Check if pool sizes are too small
    if len(adv_pool) < 50 or len(basic_pool) < 20:
        print("Error: Pool size is too small to fulfill test requirements.")
        return

    # Print samples safely avoiding unicode errors
    print("\n--- Basic Math Samples ---")
    for q in basic_pool[:5]:
        txt = q["question_text"].encode('ascii', 'ignore').decode('ascii')
        print(f"  - {txt[:90]}...")

    print("\n--- Advanced Math Samples ---")
    for q in adv_pool[:5]:
        txt = q["question_text"].encode('ascii', 'ignore').decode('ascii')
        print(f"  - {txt[:90]}...")

    # Confirm and update in DB
    print("\nApplying updates to Supabase...")
    
    # 1. Update Advanced Math questions
    PATCH_HEADERS = dict(HEADERS)
    PATCH_HEADERS["Prefer"] = "return=minimal"
    
    adv_ids = [q["id"] for q in adv_pool]
    updated_adv = 0
    for i in range(0, len(adv_ids), 50):
        chunk = adv_ids[i:i+50]
        id_list = ",".join(chunk)
        url = f"{BASE_URL}/questions?id=in.({id_list})"
        body = json.dumps({"category_id": ADV_MATH_ID}).encode('utf-8')
        req = urllib.request.Request(url, data=body, headers=PATCH_HEADERS, method="PATCH")
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
                updated_adv += len(chunk)
        except Exception as e:
            print(f"Error on adv chunk {i}: {e}")
            
    # 2. Update Basic Math questions
    basic_ids = [q["id"] for q in basic_pool]
    updated_basic = 0
    for i in range(0, len(basic_ids), 50):
        chunk = basic_ids[i:i+50]
        id_list = ",".join(chunk)
        url = f"{BASE_URL}/questions?id=in.({id_list})"
        body = json.dumps({"category_id": BASIC_MATH_ID}).encode('utf-8')
        req = urllib.request.Request(url, data=body, headers=PATCH_HEADERS, method="PATCH")
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
                updated_basic += len(chunk)
        except Exception as e:
            print(f"Error on basic chunk {i}: {e}")

    print(f"\nDB update finished successfully!")
    print(f"  Advanced Math records updated: {updated_adv}")
    print(f"  Basic Math records updated:    {updated_basic}")

if __name__ == "__main__":
    main()
