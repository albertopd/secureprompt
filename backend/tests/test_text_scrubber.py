from scrubbers.text_scrubber import TextScrubber


def test_iban_detection():
    scrubber = TextScrubber()
    text = "Please transfer to BE71 0961 2345 6769 for the invoice."
    res = scrubber.scrub(text)
    assert res["entities"], "No entities detected"
    assert any(e["type"] == "IBAN" for e in res["entities"])
    assert "[[IBAN_1]]" in res["redacted_text"]


def test_vat_detection():
    scrubber = TextScrubber()
    text = "Our supplier VAT number is BE0123456789."
    res = scrubber.scrub(text)
    assert any(e["type"] == "VAT_BE" for e in res["entities"])


def test_national_register_detection():
    scrubber = TextScrubber()
    text = "ID: 79.01.23-123.45 belonged to the customer."
    res = scrubber.scrub(text)
    assert any(e["type"] == "NATIONAL_REG" for e in res["entities"])


def test_phone_and_postal():
    scrubber = TextScrubber()
    text = "Call +32 2 502123456 or send to 1000 Brussels."
    res = scrubber.scrub(text)
    types = [e["type"] for e in res["entities"]]
    assert "PHONE_BE" in types
    assert "POSTAL_CODE_BE" in types
