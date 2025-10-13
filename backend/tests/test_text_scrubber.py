import pytest
from backend.scrubbers.text_scrubber import TextScrubber
from backend.tests.helpers.excel_loader import load_test_cases_from_csv, load_test_cases_from_excels
from backend.tests.structural_comparison import compare_structure, structural_comparison_summary


@pytest.mark.parametrize("file,input_prompt,sanitized_prompt", load_test_cases_from_csv())
def test_text_scrubber(file: str, input_prompt: str, sanitized_prompt: str):
    """
    Tests the TextScrubber's ability to sanitize input prompts using structural comparison.
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