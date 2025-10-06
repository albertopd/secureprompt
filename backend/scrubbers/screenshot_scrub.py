import cv2
import pytesseract
from PIL import Image
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
import json
from datetime import datetime
import sys

# ---------------- Tesseract setup ----------------
try:
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    # Quick test to see if tesseract is callable
    pytesseract.get_tesseract_version()
except FileNotFoundError:
    print("❌ Tesseract executable not found. Please check the path and installation.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error initializing Tesseract: {e}")
    sys.exit(1)

# ---------------- Presidio setup ----------------
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Custom recognizers
account_num_pattern = Pattern(name="account_number", regex=r"\b\d{10,16}\b", score=0.9)
account_num_recognizer = PatternRecognizer(supported_entity="ACCOUNT_NUMBER", patterns=[account_num_pattern])

national_id_pattern = Pattern(name="national_id", regex=r"\b\d{9,12}\b", score=0.85)
national_id_recognizer = PatternRecognizer(supported_entity="NATIONAL_ID", patterns=[national_id_pattern])

# Register custom recognizers
analyzer.registry.add_recognizer(account_num_recognizer)
analyzer.registry.add_recognizer(national_id_recognizer)

# ---------------- OCR ----------------
def extract_text_with_boxes(image_path):
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"❌ Could not open image: {image_path}")

        pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
        results = []
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            if text:
                box = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                results.append({"text": text, "box": box})
        return results, image
    except FileNotFoundError as fnf_err:
        print(fnf_err)
        sys.exit(1)
    except pytesseract.TesseractNotFoundError:
        print("❌ Tesseract not found. Please check the installation.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during OCR: {e}")
        sys.exit(1)

# ---------------- Presidio Analysis ----------------
def analyze_text(text):
    return analyzer.analyze(
        text=text,
        language="en",
        entities=[
            "PERSON",
            "LOCATION",       # or ADDRESS if enabled
            "DATE_TIME",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "ACCOUNT_NUMBER",
            "NATIONAL_ID"
        ]
    )

# ---------------- Redaction ----------------
def redact_boxes(image, boxes, mode="black"):
    for (x, y, w, h) in boxes:
        roi = image[y:y+h, x:x+w]
        if roi.size == 0:
            continue
        if mode == "black":
            image[y:y+h, x:x+w] = (0, 0, 0)
        elif mode == "blur":
            image[y:y+h, x:x+w] = cv2.GaussianBlur(roi, (51, 51), 0)
        elif mode == "pixelate":
            small = cv2.resize(roi, (10, 10), interpolation=cv2.INTER_LINEAR)
            image[y:y+h, x:x+w] = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    return image

# ---------------- Audit Logging ----------------
def save_audit_log(logs, output_file="backend/audit_logs.jsonl"):
    try:
        with open(output_file, "a") as f:
            for entry in logs:
                f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"❌ Failed to save audit log: {e}")
        sys.exit(1)

# ---------------- Main Pipeline ----------------
def anonymize_screenshot(input_image, output_image, log_file="backend/audit_logs.jsonl"):
    try:
        ocr_results, image = extract_text_with_boxes(input_image)
        pii_boxes = []
        audit_logs = []

        # 1. Prepare for full text analysis and mapping
        full_text = ""
        box_map = [] # To map character index back to the OCR box
        current_offset = 0

        # Build the full text string and the box map
        for item in ocr_results:
            text, box = item["text"], item["box"]
            
            # The space is crucial for separating words for Presidio analysis
            padded_text = text + " "
            full_text += padded_text
            
            box_map.append({
                "box": box,
                "start": current_offset,
                "end": current_offset + len(text)
            })
            current_offset += len(padded_text)

        # 2. Analyze the full text for PII
        all_results = analyze_text(full_text)
        
        # 3. Process the results and map PII spans back to boxes
        for r in all_results:
            # Find the OCR boxes that fall within the detected PII span (r.start, r.end)
            
            # Extract the original text for the log (based on the full span)
            original_pii_text = full_text[r.start:r.end].strip()

            # The anonymizer needs a slightly different structure than the log
            anonymized_result = anonymizer.anonymize(
                text=full_text, 
                analyzer_results=[r]
            )
            anonymized_pii_text = anonymized_result.text[r.start:r.end].strip()

            # Find all boxes that overlap with the PII span
            boxes_to_redact = []
            for item in box_map:
                # Check for overlap: [item.start, item.end] inside [r.start, r.end]
                # A box is included if its start or end falls within the PII span
                if max(item["start"], r.start) < min(item["end"], r.end):
                    pii_boxes.append(item["box"])
                    boxes_to_redact.append(item["box"])
            
            # Deduplicate the boxes for redaction (important if one box is part of multiple PII)
            # The pii_boxes list at the function level is used for redaction and should be unique.
            # Using a set to ensure unique boxes before the redaction step is a good practice.
            # For logging, we log the *full* PII entity only once.
            
            if boxes_to_redact:
                audit_logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "entity_type": r.entity_type,
                    "original_text": original_pii_text,
                    "anonymized_text": anonymized_pii_text,
                    # Log the full span in the text, not just one word's box
                    "start": r.start,
                    "end": r.end,
                    "confidence_score": r.score
                })

        # Remove duplicate boxes (e.g., if a box contains a name AND part of a phone number)
        unique_pii_boxes = list(set(pii_boxes)) 
        
        # 4. Redact detected PII from image
        image = redact_boxes(image, unique_pii_boxes, mode="black")

        # 5. Save outputs
        cv2.imwrite(output_image, image)
        save_audit_log(audit_logs, log_file)

        print(f"✅ Anonymized screenshot saved to {output_image}")
        print(f"✅ Audit logs saved to {log_file}")

    except Exception as e:
        print(f"❌ Unexpected error during anonymization: {e}")
        # Only exit on critical error, not on a simple exception
        # sys.exit(1) # Consider removing this to allow partial success


if __name__ == "__main__":
    try:
        anonymize_screenshot(r"backend\scrubbers\Screenshot.png", "backend/screenshot_anonymized.png", "backend/audit.jsonl")
    except KeyboardInterrupt:
        print("\n❌ Process interrupted by user.")
        sys.exit(0)
