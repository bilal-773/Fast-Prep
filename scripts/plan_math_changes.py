import json
import re

with open("all_questions.json", "r", encoding="utf-8") as f:
    qs = json.load(f)

proposed_changes = []

def clean_integration_text(text):
    original = text
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
    
    # Replace "integral from a to b of X dx" -> "∫[a to b] X dx"
    # Or "Integral from a to b of X = ?" -> "∫[a to b] X dx = ?"
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
            r"(?i)\bintegrate\s+(.+?)",
            r"∫ \1 dx",
            text
        )
    
    return text

def clean_differentiation_text(text):
    original = text
    # Replace "derivative of X w.r.t 'x'" / "derivative of X w.r.t x"
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
    # Replace "Find the second derivative of X"
    text = re.sub(
        r"(?i)find\s+the\s+second\s+derivative\s+of\s+(.+?)",
        r"Find d²/dx² of \1",
        text
    )
    # Replace "Find the derivative of X"
    text = re.sub(
        r"(?i)find\s+the\s+derivative\s+of\s+(.+?)",
        r"Find dy/dx of \1",
        text
    )
    # Replace "differentiate X w.r.t. x" / "differentiate X"
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
    # Replace "differentiation of X"
    text = re.sub(
        r"(?i)differentiation\s+of\s+(.+?)",
        r"dy/dx of \1",
        text
    )
    
    return text

for q in qs:
    text = q.get("question_text", "")
    cat = q.get("category_slug", "")
    
    # Check if math related
    if cat not in ["math", "mathematics", "advanced_math", "basic_math"]:
        continue
    
    text_lower = text.lower()
    is_int = any(k in text_lower for k in ["integral", "integrate", "integration"])
    is_diff = any(k in text_lower for k in ["derivative", "differentiate", "differentiation"])
    
    new_text = text
    if is_int:
        new_text = clean_integration_text(text)
    elif is_diff:
        new_text = clean_differentiation_text(text)
        
    if new_text != text:
        proposed_changes.append({
            "original": text,
            "proposed": new_text,
            "category": cat
        })

print(f"Total proposed updates: {len(proposed_changes)}")
with open("proposed_math_changes.txt", "w", encoding="utf-8") as f:
    for idx, pc in enumerate(proposed_changes):
        f.write(f"Change #{idx+1} ({pc['category']}):\n")
        f.write(f"  FROM: {pc['original']}\n")
        f.write(f"  TO:   {pc['proposed']}\n\n")

print("Proposed changes saved to proposed_math_changes.txt")
