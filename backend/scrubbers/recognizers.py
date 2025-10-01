
DEFAULT_RECOGNIZERS_CLIENT_C4 = [
  
    {"name": "person", "entity": "PERSON"},
    {"name": "email", "entity": "EMAIL_ADDRESS"},
    {"name": "cc", "entity": "CREDIT_CARD"},
    {"name": "iban", "entity": "IBAN_CODE"},
    {"name": "ph","entity": "PHONE_NUMBER"},
  
]

RECOGNIZERS_CLIENT_C4 = [


    {"name" : "ccs", "entity": "CREDIT_CARD_SYNTHETIC", "pattern": r"\b(?:\d[ -]*?){13,19}\b"},
    {"name": "iban_be", "entity": "IBAN_BE", "pattern": r"\bBE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\b"},
    {"name": "nn_reg","entity": "NATIONAL_REG", "pattern": r"\b\d{2}[.\-]?\d{2}[.\-]?\d{2}[.\-]?\d{3}[.\-]?\d{2}\b"},
    {"name": "vat_be","entity": "VAT_BE", "pattern": r"\bBE0\d{9}\b"},
    {"name": "ph_be","entity": "PHONE_BE", "pattern": r"(\+32\s?|0)(\d{1,2})(\s?\d{2}\s?\d{2}\s?\d{2}|\s?\d{3}\s?\d{3})"},
    {"name": "pc_be", "entity": "POSTAL_CODE_BE", "pattern": r"\b[1-9][0-9]{3}\b"},

    {"name": "add_be", "entity": "ADDRESS_BE", "pattern": r"(?i)\b(?:st(?:reet)?|str|dr|rd|road|ave|blvd|boulevard|sq|square|rue|av|avenue|bd|boulevard|straat|laan|plein)\.?$"}
    
]
