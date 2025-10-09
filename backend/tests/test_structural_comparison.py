import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
from backend.scrubbers.text_scrubber import TextScrubber
from backend.tests.helpers.excel_loader import load_test_cases_from_csv
from backend.tests.structural_comparison import compare_structure, structural_comparison_summary


_DEFAULT_REPORTS_DIR = "tests/data/reports"


@pytest.mark.parametrize("file,input_prompt,sanitized_prompt", load_test_cases_from_csv())
def test_text_scrubber_structural(file: str, input_prompt: str, sanitized_prompt: str):
    """
    Tests the TextScrubber's ability to sanitize input prompts using structural comparison.
    
    This test compares the STRUCTURE of masking rather than exact label matches:
    - Same number of entities detected
    - Same positions of masked content
    - Same overall text structure
    
    Args:
        file (str): The name or path of the file being tested.
        input_prompt (str): The original prompt text to be scrubbed.
        sanitized_prompt (str): The expected sanitized (redacted) output.
    Asserts:
        The structure of redacted text matches the expected structure (70% threshold).
    """
    scrubber = TextScrubber()
    result = scrubber.scrub_text(input_prompt)
    scrubbed_text = result["scrubbed_text"]

    # Use structural comparison instead of exact match
    structural_result = compare_structure(sanitized_prompt, scrubbed_text)
    
    if not structural_result["passed"]:
        summary = structural_comparison_summary(sanitized_prompt, scrubbed_text)
        pytest.fail(f"Structural mismatch ({structural_result['score']:.1%}): {summary}")
    
    assert structural_result["passed"], f"Score: {structural_result['score']:.1%}"


def test_text_scrubber_structural_report():
    """
    Runs structural text scrubbing tests and generates a comprehensive report.

    This test:
    - Loads test cases using `load_test_cases_from_csv()`
    - For each case, scrubs the prompt and compares structure to expected output
    - Uses structural comparison (positions, entity counts) rather than exact matches
    - Collects results including scores, summaries, and pass/fail status
    - Calculates overall accuracy and average scores
    - Saves a detailed CSV report to `tests/reports` with timestamp
    - Uses 70% threshold for acceptance (instead of 100%)

    The report CSV columns are: file, prompt, expected, got, passed, score, summary.
    """
    scrubber = TextScrubber()
    cases = load_test_cases_from_csv()

    results = []
    for file, prompt, expected in cases:
        result = scrubber.scrub_text(prompt)
        actual = result["scrubbed_text"]
        
        # Use structural comparison instead of exact match
        structural_result = compare_structure(expected, actual)
        passed = structural_result["passed"]
        
        results.append({
            "file": file,
            "prompt": prompt,
            "expected": expected,
            "got": actual,
            "passed": passed,
            "score": structural_result["score"],
            "summary": structural_comparison_summary(expected, actual)
        })

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    accuracy = passed_count / total * 100 if total else 0
    
    # Calculate average score
    avg_score = sum(r["score"] for r in results) / total if total > 0 else 0

    report_dir = Path(_DEFAULT_REPORTS_DIR)
    report_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = report_dir / f"structural_comparison_report_{timestamp}.csv"

    pd.DataFrame(results).to_csv(csv_path, index=False, encoding="utf-8")

    print(f"\nStructural Report saved to {csv_path}")
    print(f"Structural Accuracy: {accuracy:.2f}% ({passed_count}/{total})")
    print(f"Average Score: {avg_score:.2%}")

    # Use 70% as acceptable threshold (instead of 100%)
    if accuracy < 70:
        pytest.fail(f"Structural accuracy below 70%: {accuracy:.2f}%")


def test_text_scrubber_structural_sample():
    """
    Quick structural test with a small sample for debugging and validation.
    
    Tests the first 10 cases from each CSV file to quickly validate
    the structural comparison is working as expected.
    """
    scrubber = TextScrubber()
    cases = load_test_cases_from_csv()
    
    # Test first 10 cases for quick feedback
    sample_cases = cases[:10] if len(cases) > 10 else cases
    
    results = []
    for file, prompt, expected in sample_cases:
        result = scrubber.scrub_text(prompt)
        actual = result["scrubbed_text"]
        
        structural_result = compare_structure(expected, actual)
        summary = structural_comparison_summary(expected, actual)
        
        results.append({
            "file": file,
            "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
            "expected": expected,
            "actual": actual,
            "score": structural_result["score"],
            "passed": structural_result["passed"],
            "summary": summary
        })
        
        print(f"{file}")
        print(f"{prompt[:70]}...")
        print(f"Expected: {expected}")
        print(f"Actual:   {actual}")
        print(f"{summary}")
        print("-" * 80)
    
    passed_count = sum(1 for r in results if r["passed"])
    accuracy = passed_count / len(results) * 100 if results else 0
    
    print(f"\n🎯 Sample Results: {accuracy:.1f}% ({passed_count}/{len(results)})")
    
    # Lower threshold for sample test
    assert accuracy >= 50, f"Sample accuracy too low: {accuracy:.1f}%"