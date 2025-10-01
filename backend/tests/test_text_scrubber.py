import pytest
from scrubbers.text_scrubber import TextScrubber
from tests.helpers.excel_loader import load_test_cases_from_excels


@pytest.mark.parametrize("file,input_prompt,sanitized_prompt", load_test_cases_from_excels())
def test_text_scrubber(file: str, input_prompt: str, sanitized_prompt: str):
    """
    Tests the TextScrubber's ability to sanitize input prompts.
    Args:
        file (str): The name or path of the file being tested.
        input_prompt (str): The original prompt text to be scrubbed.
        sanitized_prompt (str): The expected sanitized (redacted) output.
    Asserts:
        The redacted text produced by TextScrubber matches the expected sanitized prompt.
    """
    scrubber = TextScrubber()
    result = scrubber.scrub(input_prompt)
    redacted_text = result["redacted_text"]

    assert redacted_text == sanitized_prompt