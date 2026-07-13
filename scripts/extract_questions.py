import os
import sys
import re
import json
import base64
import argparse
import tempfile
import pdfplumber
import fitz  # PyMuPDF — used for rendering image-based (scanned) PDF pages
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

SYSTEM_PROMPT = """You are an expert at parsing Pakistani university entry test papers. 
Extract ALL multiple choice questions from the following text. 
Return ONLY a valid JSON array. Each object must have:
{
  "question_text": string,
  "option_a": string,
  "option_b": string,
  "option_c": string,
  "option_d": string,
  "correct_option": "A" | "B" | "C" | "D" | null,
  "category_hint": string (your best guess at category: math/english/iq/physics/chemistry/biology)
}
If correct answer is not shown in the paper, set correct_option to null.
Do NOT include any other text, markdown, or explanation — only the JSON array."""

VISION_SYSTEM_PROMPT = """You are an expert at reading Pakistani university entry test past papers from images.
Look at the image carefully and extract ALL multiple choice questions visible in it.
Return ONLY a valid JSON array. Each object must have:
{
  "question_text": string,
  "option_a": string,
  "option_b": string,
  "option_c": string,
  "option_d": string,
  "correct_option": "A" | "B" | "C" | "D" | null,
  "category_hint": string (your best guess at category: math/english/iq/physics/chemistry/biology)
}
If correct answer is not shown in the paper, set correct_option to null.
Extract every question visible on the page, including partial ones.
Do NOT include any other text, markdown, or explanation — only the JSON array."""


def normalize_text(text):
    """Normalize text for deduplication checks."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text


def parse_gpt_response(content):
    """Parse JSON array from GPT-4o response, stripping code blocks if present."""
    content = content.strip()

    # Strip markdown code blocks if GPT returned them
    if content.startswith("```"):
        lines = content.splitlines()
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "questions" in data:
            return data["questions"]
        else:
            print(f"  Warning: Response was JSON but not a list: {type(data)}")
            return []
    except json.JSONDecodeError as e:
        print(f"  Error decoding JSON response: {e}")
        debug_file = "failed_gpt_response.txt"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Saved failed response to {debug_file} for inspection.")
        return []


def render_page_to_base64(pdf_path, page_index, dpi=200):
    """Render a PDF page to a base64-encoded PNG using PyMuPDF."""
    doc = fitz.open(pdf_path)
    page = doc[page_index]
    # Scale matrix: dpi/72 gives the zoom factor
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img_bytes = pix.tobytes("png")
    doc.close()
    return base64.b64encode(img_bytes).decode("utf-8")


def extract_from_image_page(client, pdf_path, page_index):
    """Send a single PDF page image to GPT-4o Vision and extract questions."""
    page_num = page_index + 1
    print(f"    Rendering page {page_num} as image...")
    try:
        b64_image = render_page_to_base64(pdf_path, page_index, dpi=200)
    except Exception as e:
        print(f"    Error rendering page {page_num} to image: {e}")
        return []

    print(f"    Sending page {page_num} image to GPT-4o Vision...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": VISION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_image}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": "Extract all multiple choice questions from this page as a JSON array."
                        }
                    ]
                }
            ],
            temperature=0.0,
            max_tokens=4096
        )
        raw_response = response.choices[0].message.content
        questions = parse_gpt_response(raw_response)
        print(f"    Extracted {len(questions)} questions from page {page_num} (vision).")
        return questions
    except Exception as e:
        print(f"    Error calling GPT-4o Vision for page {page_num}: {e}")
        return []


def process_text_based_pdf(client, pdf_path, pages_to_extract):
    """Extract questions from a text-based PDF using pdfplumber + GPT-4o text."""
    extracted_pages = []
    total_text_length = 0

    with pdfplumber.open(pdf_path) as pdf:
        for idx in pages_to_extract:
            page = pdf.pages[idx]
            text = page.extract_text() or ""
            extracted_pages.append((idx + 1, text))
            total_text_length += len(text)

    print(f"  Extracted {len(extracted_pages)} pages. Total text: {total_text_length} chars.")

    # Group pages into chunks (~30,000 chars max per chunk)
    chunks = []
    current_chunk = []
    current_length = 0

    for page_num, text in extracted_pages:
        if not text.strip():
            continue
        if current_length + len(text) > 30000 and current_chunk:
            chunks.append("\n\n--- Page Break ---\n\n".join(current_chunk))
            current_chunk = [f"--- Page {page_num} ---\n{text}"]
            current_length = len(text)
        else:
            current_chunk.append(f"--- Page {page_num} ---\n{text}")
            current_length += len(text)

    if current_chunk:
        chunks.append("\n\n--- Page Break ---\n\n".join(current_chunk))

    print(f"  Split into {len(chunks)} chunk(s) for GPT-4o text processing.")

    all_questions = []
    for i, chunk in enumerate(chunks):
        print(f"  Processing chunk {i+1}/{len(chunks)} with GPT-4o...")
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Extract questions from the following text chunk:\n\n{chunk}"}
                ],
                temperature=0.0
            )
            raw_response = response.choices[0].message.content
            chunk_questions = parse_gpt_response(raw_response)
            print(f"  Extracted {len(chunk_questions)} questions from chunk {i+1}.")
            all_questions.extend(chunk_questions)
        except Exception as e:
            print(f"  Error processing chunk {i+1}: {e}")

    return all_questions


def process_image_based_pdf(client, pdf_path, pages_to_extract):
    """Extract questions from a scanned/image-based PDF using GPT-4o Vision page by page."""
    print(f"  Using GPT-4o Vision for image-based PDF ({len(pages_to_extract)} pages)...")
    all_questions = []
    for idx in pages_to_extract:
        questions = extract_from_image_page(client, pdf_path, idx)
        all_questions.extend(questions)
    return all_questions


def is_image_based_pdf(pdf_path, pages_to_check=5):
    """
    Heuristic: detect image-based (scanned) PDFs.
    
    A PDF is considered image-based if:
    - Average chars per page < 100, OR
    - All checked pages have the exact same text (watermark-only PDF where 
      real content is embedded as images behind a repeated text layer)
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            check_count = min(pages_to_check, total_pages)
            
            page_texts = []
            for i in range(check_count):
                text = (pdf.pages[i].extract_text() or "").strip()
                page_texts.append(text)
            
            total_chars = sum(len(t) for t in page_texts)
            avg_chars = total_chars / check_count if check_count > 0 else 0
            
            # Case 1: Very little text overall
            if avg_chars < 100:
                return True
            
            # Case 2: All pages have identical text — repeated watermark/header,
            # actual questions are rendered as images
            non_empty = [t for t in page_texts if t]
            if len(non_empty) >= 2 and len(set(non_empty)) == 1:
                print(f"  [Detection] All {len(non_empty)} checked pages have identical text — treating as image-based.")
                return True
            
            # Case 3: Text has very low unique word density (same words cycling)
            all_text = " ".join(page_texts)
            words = all_text.lower().split()
            if len(words) > 10:
                unique_ratio = len(set(words)) / len(words)
                if unique_ratio < 0.15:  # less than 15% unique words → repetitive watermark
                    print(f"  [Detection] Low word uniqueness ratio ({unique_ratio:.2f}) — treating as image-based.")
                    return True
            
            # Case 4: Very few/no option patterns (e.g., (a), b., etc.) in text.
            # Real text-based MCQ papers must have option indicators. If they don't, it is a watermark/garbage text layer.
            option_pattern = re.compile(r'\b[a-d]\s*[\.\)]|\([a-d]\)', re.IGNORECASE)
            total_option_matches = sum(len(option_pattern.findall(t)) for t in page_texts)
            if total_option_matches < 2:
                print(f"  [Detection] Only {total_option_matches} option indicators found — treating as image-based scanned PDF.")
                return True
            
            return False
    except Exception:
        return True  # assume image-based if we can't read it


def main():
    parser = argparse.ArgumentParser(description="Extract MCQ questions from past paper PDFs using GPT-4o.")
    parser.add_argument("--pdf", required=True, help="Path to the PDF file")
    parser.add_argument("--university", default="fast-nuces", help="University slug (default: fast-nuces)")
    parser.add_argument("--category", default=None, help="Category slug override (optional)")
    parser.add_argument("--year", type=int, default=None, help="Exam year (optional)")
    parser.add_argument("--output", required=True, help="Path to write the output JSON file")
    parser.add_argument("--pages", default="all", help="Pages to extract (e.g. 'all', '1-5', '1,2,5')")
    parser.add_argument("--force-vision", action="store_true", help="Force GPT-4o Vision even for text-based PDFs")

    args = parser.parse_args()

    # Validate PDF path
    if not os.path.exists(args.pdf):
        print(f"Error: PDF file not found at '{args.pdf}'")
        sys.exit(1)

    # Check OpenAI API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please check your .env file or environment setup.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    print(f"\nOpening PDF: {args.pdf}")

    pages_to_extract = []

    with pdfplumber.open(args.pdf) as pdf:
        total_pdf_pages = len(pdf.pages)

    print(f"Total pages in PDF: {total_pdf_pages}")

    # Parse pages argument
    if args.pages == "all":
        pages_to_extract = list(range(total_pdf_pages))
    else:
        try:
            if "-" in args.pages:
                start, end = map(int, args.pages.split("-"))
                pages_to_extract = list(range(max(0, start - 1), min(total_pdf_pages, end)))
            else:
                pages_to_extract = [int(p.strip()) - 1 for p in args.pages.split(",") if p.strip()]
                pages_to_extract = [p for p in pages_to_extract if 0 <= p < total_pdf_pages]
        except Exception as e:
            print(f"Error parsing --pages argument '{args.pages}': {e}")
            print("Fallback: extracting all pages.")
            pages_to_extract = list(range(total_pdf_pages))

    if not pages_to_extract:
        print("Error: No valid pages selected for extraction.")
        sys.exit(1)

    print(f"Selected pages: {[p + 1 for p in pages_to_extract]}")

    # Determine PDF type
    if args.force_vision:
        print("\nForce-vision mode: using GPT-4o Vision for all pages.")
        pdf_is_image_based = True
    else:
        pdf_is_image_based = is_image_based_pdf(args.pdf)
        if pdf_is_image_based:
            print("\nDetected: Image-based (scanned) PDF — will use GPT-4o Vision.")
        else:
            print("\nDetected: Text-based PDF — will use pdfplumber + GPT-4o text.")

    # Extract questions
    if pdf_is_image_based:
        all_extracted_questions = process_image_based_pdf(client, args.pdf, pages_to_extract)
    else:
        all_extracted_questions = process_text_based_pdf(client, args.pdf, pages_to_extract)

    # Deduplicate
    unique_questions = []
    seen_normalized_texts = set()
    duplicate_count = 0

    for q in all_extracted_questions:
        q_text = q.get("question_text")
        if not q_text:
            continue

        norm_text = normalize_text(q_text)
        if norm_text in seen_normalized_texts:
            duplicate_count += 1
            continue

        seen_normalized_texts.add(norm_text)

        category_hint = q.get("category_hint") or "general"
        formatted_question = {
            "university_slug": args.university,
            "category_slug": args.category if args.category else category_hint.lower(),
            "year": args.year,
            "question_text": q_text.strip(),
            "option_a": (q.get("option_a") or "").strip(),
            "option_b": (q.get("option_b") or "").strip(),
            "option_c": (q.get("option_c") or "").strip(),
            "option_d": (q.get("option_d") or "").strip(),
            "correct_option": q.get("correct_option"),
            "explanation": q.get("explanation")
        }
        unique_questions.append(formatted_question)

    print(f"\n--- Extraction Summary ---")
    print(f"Total raw questions extracted: {len(all_extracted_questions)}")
    print(f"Duplicates removed: {duplicate_count}")
    print(f"Final unique questions: {len(unique_questions)}")

    with_correct = sum(1 for q in unique_questions if q["correct_option"] in ["A", "B", "C", "D"])
    needs_review = len(unique_questions) - with_correct
    print(f"Questions with correct option: {with_correct}")
    print(f"Questions needing review (no answer): {needs_review}")

    # Write output
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(unique_questions, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(unique_questions)} questions to '{args.output}'")


if __name__ == "__main__":
    main()
