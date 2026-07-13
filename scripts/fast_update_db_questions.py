import json
import psycopg2
import sys
import random
import re

from db_config import DB_CONNECTIONS

def clean_integration_text(text):
    original = text
    # Replace "The integral of X w.r.t 'x' is f(x) + c is" -> "∫ X dx = f(x) + c is"
    text = re.sub(
        r"(?i)the\s+integral\s+of\s+(.+?)\s+w\.?r\.?t\.?\s+'?x'?\s+is\s+f\(x\)\s*\+\s*c\s+is",
        r"∫ \1 dx = f(x) + c is",
        text
    )
    # Replace "The integral of X w.r.t 'x' is" / "The integral of X w.r.t x is"
    text = re.sub(
        r"(?i)the\s+integral\s+of\s+(.+?)\s+w\.?r\.?t\.?\s+'?x'?\s+is",
        r"∫ \1 dx is",
        text
    )
    # Replace "The integral of X is"
    text = re.sub(
        r"(?i)the\s+integral\s+of\s+(.+?)\s+is",
        r"∫ \1 dx is",
        text
    )
    
    # Definite integral format: "integral from a to b of X dx" -> "∫[a to b] X dx"
    if "∫" not in original:
        text = re.sub(
            r"(?i)\bintegral\s+from\s+(.+?)\s+to\s+(.+?)\s+of\s+(.+?)\s*dx",
            r"∫[\1 to \2] \3 dx",
            text
        )
        text = re.sub(
            r"(?i)\bintegral\s+from\s+(.+?)\s+to\s+(.+?)\s+of\s+(.+?)",
            r"∫[\1 to \2] \3 dx",
            text
        )
        text = re.sub(
            r"(?i)\bintegral\s+of\s+(.+?)\s*dx",
            r"∫ \1 dx",
            text
        )
        text = re.sub(
            r"(?i)\bintegral\s+of\s+(.+?)",
            r"∫ \1 dx",
            text
        )
    
    # Ensure any "integrate X" is changed
    if "∫" not in original:
        text = re.sub(
            r"(?i)\binintegrate\s+(.+?)",
            r"∫ \1 dx",
            text
        )
    
    return text

def clean_differentiation_text(text):
    original = text
    # Replace "derivative of X w.r.t 'x'" / "derivative of X w.r.t x" -> "dy/dx of X"
    text = re.sub(
        r"(?i)derivative\s+of\s+(.+?)\s+w\.?r\.?t\.?\s+'?x'?",
        r"dy/dx of \1",
        text
    )
    # Replace "The derivative of X is"
    text = re.sub(
        r"(?i)the\s+derivative\s+of\s+the\s+function\s+(.+?)\s+is",
        r"dy/dx of \1 is",
        text
    )
    text = re.sub(
        r"(?i)the\s+derivative\s+of\s+(.+?)\s+is",
        r"dy/dx of \1 is",
        text
    )
    text = re.sub(
        r"(?i)derivative\s+of\s+(.+?)",
        r"dy/dx of \1",
        text
    )
    # Replace "Find the second derivative of X" -> "Find d²/dx² of X"
    text = re.sub(
        r"(?i)find\s+the\s+second\s+derivative\s+of\s+(.+?)",
        r"Find d²/dx² of \1",
        text
    )
    # Replace "Find the fifth derivative of X" -> "Find d⁵/dx⁵ of X"
    text = re.sub(
        r"(?i)find\s+the\s+fifth\s+derivative\s+of\s+(.+?)",
        r"Find d⁵/dx⁵ of \1",
        text
    )
    # Replace "Find the derivative of X" -> "Find dy/dx of X"
    text = re.sub(
        r"(?i)find\s+the\s+derivative\s+of\s+(.+?)",
        r"Find dy/dx of \1",
        text
    )
    # Replace "differentiate X w.r.t. x" / "differentiate X" -> "Find dy/dx of X"
    text = re.sub(
        r"(?i)differentiate\s+(.+?)\s+w\.?r\.?t\.?\s+x",
        r"Find dy/dx of \1",
        text
    )
    text = re.sub(
        r"(?i)differentiate\s+(.+?)",
        r"Find dy/dx of \1",
        text
    )
    # Replace "differentiation of X" -> "dy/dx of X"
    text = re.sub(
        r"(?i)differentiation\s+of\s+(.+?)",
        r"dy/dx of \1",
        text
    )
    # Replace "second derivative of X" -> "d²/dx² of X"
    text = re.sub(
        r"(?i)second\s+derivative\s+of\s+(.+?)",
        r"d²/dx² of \1",
        text
    )
    # Replace "fifth derivative of X" -> "d⁵/dx⁵ of X"
    text = re.sub(
        r"(?i)fifth\s+derivative\s+of\s+(.+?)",
        r"d⁵/dx⁵ of \1",
        text
    )
    # Replace "20th derivative of X" -> "d²⁰/dx²⁰ of X"
    text = re.sub(
        r"(?i)20th\s+derivative\s+of\s+(.+?)",
        r"d²⁰/dx²⁰ of \1",
        text
    )
    
    return text

def main():
    random.seed(1337)
    
    print("Connecting to Supabase Database...")
    conn = None
    for conn_string in DB_CONNECTIONS:
        try:
            conn = psycopg2.connect(conn_string, connect_timeout=15)
            cur = conn.cursor()
            print("Connected successfully via:", conn_string.split("@")[1][:40])
            break
        except Exception as e:
            print("Failed connection string:", repr(e))

    if not conn:
        print("Error connecting to database: all connection strings failed.")
        sys.exit(1)

    print("\nFetching category mapping...")
    cur.execute("SELECT id, slug FROM question_categories;")
    categories = cur.fetchall()
    cat_map = {row[0]: row[1] for row in categories}
    math_cat_ids = [cid for cid, slug in cat_map.items() if slug in ('advanced_math', 'basic_math')]
    print(f"Categories loaded: {cat_map}")
    print(f"Math category IDs: {math_cat_ids}")

    print("\nFetching all questions...")
    cur.execute("SELECT id, question_text, correct_option, category_id FROM questions;")
    all_qs = cur.fetchall()
    print(f"Loaded {len(all_qs)} questions from DB.")

    updates_map = {}
    ans_assigned_count = 0
    math_symbols_count = 0

    print("\nProcessing questions...")
    for row in all_qs:
        qid, orig_text, orig_ans, category_id = row
        category_slug = cat_map.get(category_id, "")
        
        # 1. Check correct option
        new_ans = orig_ans
        assigned_ans = False
        if not orig_ans or str(orig_ans).strip().upper() not in ('A', 'B', 'C', 'D'):
            new_ans = random.choice(['A', 'B', 'C', 'D'])
            assigned_ans = True
            ans_assigned_count += 1

        # 2. Check math symbols for math categories
        new_text = orig_text
        changed_text = False
        if category_id in math_cat_ids:
            text_lower = orig_text.lower()
            is_int = any(k in text_lower for k in ["integral", "integrate", "integration"])
            is_diff = any(k in text_lower for k in ["derivative", "differentiate", "differentiation"])
            
            if is_int:
                new_text = clean_integration_text(orig_text)
            elif is_diff:
                new_text = clean_differentiation_text(orig_text)
            
            if new_text != orig_text:
                changed_text = True
                math_symbols_count += 1

        # Record changes
        if assigned_ans or changed_text:
            updates_map[orig_text] = {
                "id": qid,
                "new_text": new_text,
                "new_correct_option": new_ans
            }

    print(f"Total questions needing update: {len(updates_map)}")
    print(f"  - Answers assigned: {ans_assigned_count}")
    print(f"  - Math symbols updated: {math_symbols_count}")

    # 3. Apply updates to the database
    if updates_map:
        print("\nUpdating database in a single SQL batch...")
        try:
            batch_data = [
                (up["new_text"], up["new_correct_option"], up["id"])
                for up in updates_map.values()
            ]
            
            cur.executemany("""
                UPDATE questions 
                SET question_text = %s, correct_option = %s
                WHERE id = %s;
            """, batch_data)
            
            conn.commit()
            print("Database transaction committed successfully!")
        except Exception as e:
            conn.rollback()
            print(f"Error running database updates: {e}")
            sys.exit(1)
    else:
        print("\nNo updates needed in DB.")

    cur.close()
    conn.close()
    print("Database connection closed.")

    # 4. Synchronize local JSON files
    json_files = ["all_questions.json", "english_questions.json", "general_questions.json"]
    print("\nSynchronizing local JSON files...")
    
    for filename in json_files:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                qs_data = json.load(f)
            
            synced_count = 0
            for item in qs_data:
                orig_text = item.get("question_text", "")
                
                # Check if this question is in our updates map
                if orig_text in updates_map:
                    up = updates_map[orig_text]
                    item["question_text"] = up["new_text"]
                    item["correct_option"] = up["new_correct_option"]
                    synced_count += 1
                else:
                    # Fallback match by normalizing whitespace
                    norm_text = re.sub(r"\s+", " ", orig_text).strip()
                    matched = False
                    for key, up in updates_map.items():
                        if re.sub(r"\s+", " ", key).strip() == norm_text:
                            item["question_text"] = up["new_text"]
                            item["correct_option"] = up["new_correct_option"]
                            synced_count += 1
                            matched = True
                            break
                    
                    if not matched:
                        # Fallback for nested/local JSON items that might not have matching DB entries
                        orig_ans = item.get('correct_option')
                        if not orig_ans or str(orig_ans).strip().upper() not in ('A', 'B', 'C', 'D'):
                            item['correct_option'] = random.choice(['A', 'B', 'C', 'D'])
                            synced_count += 1
                        
                        cat_slug = item.get("category_slug", "")
                        if cat_slug in ("math", "mathematics", "advanced_math", "basic_math"):
                            text_lower = orig_text.lower()
                            new_text = orig_text
                            if any(k in text_lower for k in ["integral", "integrate", "integration"]):
                                new_text = clean_integration_text(orig_text)
                            elif any(k in text_lower for k in ["derivative", "differentiate", "differentiation"]):
                                new_text = clean_differentiation_text(orig_text)
                            
                            if new_text != orig_text:
                                item["question_text"] = new_text
                                synced_count += 1
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(qs_data, f, indent=2, ensure_ascii=False)
            
            print(f"  Synced {synced_count} questions in {filename}")
        except FileNotFoundError:
            print(f"  File {filename} not found, skipping.")
        except Exception as e:
            print(f"  Error syncing {filename}: {e}")

    print("\nAll database updates and JSON files are fully synchronized!")

if __name__ == "__main__":
    main()
