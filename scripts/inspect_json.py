import json

with open("all_questions.json", "r", encoding="utf-8") as f:
    qs = json.load(f)

print(f"Total questions in JSON: {len(qs)}")
# Let's search for "Miss Watson" in JSON
found = [q for q in qs if "Miss Watson" in q.get("question_text", "")]
if found:
    print("Found 'Miss Watson' question:")
    print(json.dumps(found[0], indent=2))
else:
    print("'Miss Watson' not found in JSON.")

# Let's search for "TELLER : BANK"
found2 = [q for q in qs if "TELLER" in q.get("question_text", "")]
if found2:
    print("Found 'TELLER' question:")
    print(json.dumps(found2[0], indent=2))

# Let's count how many questions in the JSON file have a null, empty, or missing correct_option
null_in_json = [q for q in qs if not q.get("correct_option")]
print(f"Questions with null/missing correct_option in JSON: {len(null_in_json)}")
if null_in_json:
    print("Sample missing in JSON:")
    print(json.dumps(null_in_json[0], indent=2))
