import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
import re
from backend.scrubbers.text_scrubber import TextScrubber
from backend.tests.helpers.excel_loader import load_test_cases_from_csv
from backend.tests.structural_comparison import compare_structure, structural_comparison_summary


_DEFAULT_REPORTS_DIR = "backend/tests/reports"


def count_entities_only(expected, actual):
    """
    Compare only the number of entities detected, ignoring positions and labels.
    
    Returns:
        dict: {
            "passed": bool,
            "score": float (0.0 to 1.0),
            "expected_count": int,
            "actual_count": int,
            "summary": str
        }
    """
    # Count entities using regex pattern <...>
    expected_entities = re.findall(r'<[^>]+>', expected)
    actual_entities = re.findall(r'<[^>]+>', actual)
    
    expected_count = len(expected_entities)
    actual_count = len(actual_entities)
    
    # Perfect score if same count, partial score based on difference
    if expected_count == 0 and actual_count == 0:
        score = 1.0
    elif expected_count == 0:
        score = 0.0  # Should not detect anything but did
    else:
        # Score based on how close the counts are
        diff = abs(expected_count - actual_count)
        score = max(0.0, 1.0 - (diff / max(expected_count, actual_count)))
    
    passed = score >= 0.7  # 70% threshold
    
    summary = f"Expected: {expected_count}, Got: {actual_count}"
    if expected_count == actual_count:
        summary += " (MATCH)"
    elif actual_count > expected_count:
        summary += " (OVER-DETECTION)"
    else:
        summary += " (UNDER-DETECTION)"
    
    return {
        "passed": passed,
        "score": score,
        "expected_count": expected_count,
        "actual_count": actual_count,
        "summary": summary
    }


def test_text_scrubber_report():
    """
    Runs text scrubbing tests using entity count comparison only.
    """
    scrubber = TextScrubber()
    cases = load_test_cases_from_csv()

    results = []
    for file, prompt, expected in cases:
        result = scrubber.scrub_text(prompt)
        actual = result["scrubbed_text"]
        
        # Use entity count comparison only
        count_result = count_entities_only(expected, actual)
        
        results.append({
            "file": file,
            "prompt": prompt,
            "expected": expected,
            "got": actual,
            "passed": count_result["passed"],
            "score": count_result["score"],
            "expected_count": count_result["expected_count"],
            "actual_count": count_result["actual_count"],
            "summary": count_result["summary"]
        })

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    accuracy = passed_count / total * 100 if total else 0

    report_dir = Path(_DEFAULT_REPORTS_DIR)
    report_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = report_dir / f"entity_count_report_{timestamp}.csv"

    pd.DataFrame(results).to_csv(csv_path, index=False, encoding="utf-8")

    # Calculate average score
    avg_score = sum(r["score"] for r in results) / total if total > 0 else 0
    
    print(f"\nEntity Count Report saved to {csv_path}")
    print(f"Entity Count Accuracy: {accuracy:.2f}% ({passed_count}/{total})")
    print(f"Average Score: {avg_score:.2%}")

    # Show breakdown by detection type
    over_detection = sum(1 for r in results if r["actual_count"] > r["expected_count"])
    under_detection = sum(1 for r in results if r["actual_count"] < r["expected_count"])
    perfect_detection = sum(1 for r in results if r["actual_count"] == r["expected_count"])
    
    print(f"\nDetection Breakdown:")
    print(f"Perfect Detection: {perfect_detection} ({perfect_detection/total*100:.1f}%)")
    print(f"Over-Detection: {over_detection} ({over_detection/total*100:.1f}%)")
    print(f"Under-Detection: {under_detection} ({under_detection/total*100:.1f}%)")

    if accuracy < 70:
        pytest.fail(f"Entity count accuracy below 70%: {accuracy:.2f}%")