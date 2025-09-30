from scrubbers.text_scrubber import TextScrubber


def test_iban_detection():
    scrubber = TextScrubber()
    text = "Please transfer to BE71 0961 2345 6769 for the invoice."
    res = scrubber.scrub(text)
    redacted_text = res["redacted_text"]

    assert res["entities"], f"Expected at least one entity to be detected for IBAN, but got none.\nSource text: '{text}'"

    assert any(e["type"] == "IBAN" for e in res["entities"]), "IBAN entity type not found in detected entities."

    assert "[[IBAN_1]]" in redacted_text, f"Redacted text does not contain expected [[IBAN_1]] placeholder.\nRedacted text: '{redacted_text}'"


def test_vat_detection():
    scrubber = TextScrubber()
    text = "Our supplier VAT number is BE0123456789."
    res = scrubber.scrub(text)
    redacted_text = res["redacted_text"]

    assert res["entities"], f"Expected at least one entity to be detected for VAT_BE, but got none.\nSource text: '{text}'"

    assert any(e["type"] == "VAT_BE" for e in res["entities"]), "VAT_BE entity type not found in detected entities."

    assert "[[VAT_BE_1]]" in redacted_text, f"Redacted text does not contain expected [[VAT_BE_1]] placeholder.\nRedacted text: '{redacted_text}'"


def test_national_register_detection():
    scrubber = TextScrubber()
    text = "ID: 79.01.23-123.45 belonged to the customer."
    res = scrubber.scrub(text)
    redacted_text = res["redacted_text"]

    assert res["entities"], f"Expected at least one entity to be detected for NATIONAL_REG, but got none.\nSource text: '{text}'"
    
    assert any(e["type"] == "NATIONAL_REG" for e in res["entities"]), "NATIONAL_REG entity type not found in detected entities."
    
    assert "[[NATIONAL_REG_1]]" in redacted_text, f"Redacted text does not contain expected [[NATIONAL_REG_1]] placeholder.\nRedacted text: '{redacted_text}'"


def test_phone_and_postal():
    scrubber = TextScrubber()
    text = "Call +32 2 502123456 or send to 1000 Brussels."
    res = scrubber.scrub(text)
    types = [e["type"] for e in res["entities"]]
    redacted_text = res["redacted_text"]

    assert res["entities"], f"Expected at least one entity to be detected for PHONE_BE and POSTAL_CODE_BE, but got none.\nSource text: '{text}'"
    
    assert "PHONE_BE" in types, "PHONE_BE entity type not found in detected entities."

    assert "POSTAL_CODE_BE" in types, "POSTAL_CODE_BE entity type not found in detected entities."
    
    assert "[[PHONE_BE_1]]" in redacted_text, f"Redacted text does not contain expected [[PHONE_BE_1]] placeholder.\nRedacted text: '{redacted_text}'"
    
    assert "[[POSTAL_CODE_BE_1]]" in redacted_text, f"Redacted text does not contain expected [[POSTAL_CODE_BE_1]] placeholder.\nRedacted text: '{redacted_text}'"
