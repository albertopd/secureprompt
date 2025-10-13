#!pip install git+https://github.com/ArtLabss/open-data-anonymizer.git
from anonympy.pdf import pdfAnonymizer
import pytesseract
from pdf2image import convert_from_path
import re
import json
import datetime
from pathlib import Path
import importlib.util

# === CONFIG ===
input_pdf = r"scrubbers\resume-sample.pdf"
output_pdf = r"scrubbers\output.pdf"
audit_log = r"scrubbers\auditlogs.jsonl"
recognizers_py = r"scrubbers\recognizers.py"  # your uploaded recognizers
risk_level = "C4"

# === helper: load recognizers module ===
def load_recognizers_module(path):
    spec = importlib.util.spec_from_file_location("recog_conf", path)
    mod = importlib.util.module_from_spec(spec) # type: ignore
    spec.loader.exec_module(mod) # type: ignore
    return mod

# === helper: extract text via OCR ===
def extract_text_ocr(pdf_path, dpi=300):
    text = ""
    images = convert_from_path(pdf_path, dpi=dpi)
    for img in images:
        text_piece = pytesseract.image_to_string(img)
        if text_piece:
            text += text_piece + "\n"
    return text

# === build patterns ===
def build_patterns_from_module(mod, risk_level="C4"):
    if risk_level == "C4":
        regex_list = getattr(mod, "REGEX_RECOGNIZERS_C4", [])
    elif risk_level == "C3":
        regex_list = getattr(mod, "REGEX_RECOGNIZERS_C3", [])
    elif risk_level == "C2":
        regex_list = getattr(mod, "REGEX_RECOGNIZERS_C2", [])
    else:
        regex_list = []

    patterns = []
    for r in regex_list:
        patt = r.get("pattern")
        if patt:
            patterns.append({
                "entity": r.get("entity", r.get("name")),
                "pattern": patt,
                "score": float(r.get("score", 0.4))
            })
    return patterns

# === main function ===
def detect_and_anonymize(pdf_path, recognizers_py, audit_log_jsonl, output_pdf, risk_level="C4"):
    mod = load_recognizers_module(recognizers_py)
    patterns = build_patterns_from_module(mod, risk_level)

    text = extract_text_ocr(pdf_path)
    if not text.strip():
        print("⚠️ No text extracted from PDF.")
        return

    logs = []
    seen = set()

    for patt in patterns:
        entity_type = patt["entity"]
        regex = patt["pattern"]
        score = patt["score"]
        for m in re.finditer(regex, text, flags=re.IGNORECASE):
            original = m.group().strip()
            start, end = m.span()
            key = (entity_type, start, end, original)
            if key in seen:
                continue
            seen.add(key)

            anonymized_text = f"<{entity_type}>"
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "entity_type": entity_type,
                "original_text": original,
                "anonymized_text": anonymized_text,
                "start": start,
                "end": end,
                "confidence_score": score
            }
            logs.append(log_entry)

    # Save audit logs
    Path(audit_log_jsonl).parent.mkdir(parents=True, exist_ok=True)
    with open(audit_log_jsonl, "a", encoding="utf-8") as f:
        for entry in logs:
            f.write(json.dumps(entry) + "\n")

    # --- Run anonymization ---
    anonym = pdfAnonymizer(
        path_to_pdf=pdf_path,
        pytesseract_path=r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    )

    anonym.anonymize(
        output_path=output_pdf,
        remove_metadata=True,
        fill="black",
        outline="black"
    )

    print(f"✅ Done. {len(logs)} entities logged and PDF anonymized to:\n{output_pdf}")

# === Run it ===
detect_and_anonymize(input_pdf, recognizers_py, audit_log, output_pdf, risk_level)
