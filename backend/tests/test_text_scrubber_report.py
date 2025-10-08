import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
from scrubbers.text_scrubber import TextScrubber
from tests.helpers.excel_loader import load_test_cases_from_excels


_DEFAULT_REPORTS_DIR = "tests/data/reports"


def test_text_scrubber_report():
    """
    Runs text scrubbing tests using cases loaded from Excel files and generates a report.

    - Loads test cases using `load_test_cases_from_excels()`.
    - For each case, scrubs the prompt and compares the result to the expected output.
    - Collects results including file name, prompt, expected output, actual output and pass/fail status.
    - Calculates overall accuracy.
    - Saves a CSV report with all results to `tests/reports` with a timestamped filename.
    - Prints the report location and accuracy summary.
    - Fails the test if accuracy is below 100%.

    The report CSV columns are: file, prompt, expected, got, passed.
    """
    scrubber = TextScrubber()
    cases = load_test_cases_from_excels()

    results = []
    for file, prompt, expected in cases:
        result = scrubber.scrub_text(prompt)
        passed = result == expected
        results.append({
            "file": file,
            "prompt": prompt,
            "expected": expected,
            "got": result["scrubbed_text"],
            "passed": passed
        })

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    accuracy = passed_count / total * 100 if total else 0

    report_dir = Path(_DEFAULT_REPORTS_DIR)
    report_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = report_dir / f"text_scrubber_report_{timestamp}.csv"

    pd.DataFrame(results).to_csv(csv_path, index=False, encoding="utf-8")

    print(f"\nReport saved to {csv_path}")
    print(f"Accuracy: {accuracy:.2f}% ({passed_count}/{total})")

    if accuracy < 100:
        pytest.fail(f"Accuracy below 100%: {accuracy:.2f}%")
