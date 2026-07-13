import json

for fname in ["english_questions.json", "general_questions.json"]:
    try:
        with open(fname, "r", encoding="utf-8") as f:
            qs = json.load(f)
        print(f"\nFile: {fname}, total: {len(qs)}")
        if qs:
            print("Keys in first item:", list(qs[0].keys()))
            null_count = len([q for q in qs if not q.get("correct_option")])
            print(f"Null correct_option count: {null_count}")
            # Search for Miss Watson
            watson = [q for q in qs if "Miss Watson" in q.get("question_text", "")]
            if watson:
                print("Found Miss Watson:", watson[0])
    except Exception as e:
        print(f"Error reading {fname}: {e}")
