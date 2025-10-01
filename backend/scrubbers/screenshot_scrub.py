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

        for item in ocr_results:
            text, box = item["text"], item["box"]

            results = analyze_text(text)
            if results:  # PII detected
                pii_boxes.append(box)

                # anonymize detected text
                anonymized = anonymizer.anonymize(text=text, analyzer_results=results)

                for r in results:
                    audit_logs.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "entity_type": r.entity_type,
                        "original_text": text,
                        "anonymized_text": anonymized.text,
                        "box": box
                    })

        # redact detected PII from image
        image = redact_boxes(image, pii_boxes, mode="black")

        # save outputs
        cv2.imwrite(output_image, image)
        save_audit_log(audit_logs, log_file)

        print(f"✅ Anonymized screenshot saved to {output_image}")
        print(f"✅ Audit logs saved to {log_file}")

    except Exception as e:
        print(f"❌ Unexpected error during anonymization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        anonymize_screenshot(r"backend\scrubbers\Screenshot.png", "backend/screenshot_anonymized.png", "backend/audit.jsonl")
    except KeyboardInterrupt:
        print("\n❌ Process interrupted by user.")
        sys.exit(0)
