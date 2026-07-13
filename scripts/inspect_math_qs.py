import json

with open("all_questions.json", "r", encoding="utf-8") as f:
    qs = json.load(f)

int_qs = []
diff_qs = []

for q in qs:
    text = q.get("question_text", "")
    text_lower = text.lower()
    if any(k in text_lower for k in ["integral", "integrate", "integration", "∫"]):
        int_qs.append(q)
    if any(k in text_lower for k in ["derivative", "differentiate", "differentiation", "dy/dx", "d/dx"]):
        diff_qs.append(q)

with open("math_qs_output.txt", "w", encoding="utf-8") as f:
    f.write(f"Found {len(int_qs)} integration questions.\n")
    for idx, q in enumerate(int_qs):
        f.write(f"  {idx+1}. ID: {q.get('id')} | TEXT: {q['question_text']}\n")
        f.write(f"     A: {q['option_a']}, B: {q['option_b']}, C: {q['option_c']}, D: {q['option_d']}\n\n")

    f.write(f"\nFound {len(diff_qs)} differentiation questions.\n")
    for idx, q in enumerate(diff_qs):
        f.write(f"  {idx+1}. ID: {q.get('id')} | TEXT: {q['question_text']}\n")
        f.write(f"     A: {q['option_a']}, B: {q['option_b']}, C: {q['option_c']}, D: {q['option_d']}\n\n")

print("Saved output to math_qs_output.txt")
