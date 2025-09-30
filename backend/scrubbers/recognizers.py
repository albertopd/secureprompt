RECOGNIZERS = [
    {"entity": "IBAN", "pattern": r"\bBE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\b"},
    {"entity": "NATIONAL_REG", "pattern": r"\b\d{2}[.\-]?\d{2}[.\-]?\d{2}[.\-]?\d{3}[.\-]?\d{2}\b"},
    {"entity": "VAT_BE", "pattern": r"\bBE0\d{9}\b"},
    {"entity": "PHONE_BE", "pattern": r"(\+32\s?|0)(\d{1,2})(\s?\d{2}\s?\d{2}\s?\d{2}|\s?\d{3}\s?\d{3})"},
    {"entity": "POSTAL_CODE_BE", "pattern": r"\b[1-9][0-9]{3}\b"},
    {"entity": "CREDIT_CARD", "pattern": r"(?:\d[ -]*?){13,19}"},
]
