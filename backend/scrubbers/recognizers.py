




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
    {"name": "birth_dt", "entity": "BIRTH_DATE", "pattern": r"\b\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b"},
    {"name": "pin_mask", "entity": "PIN_MASKED", "pattern": r"\*{4}\d{2}"},

    {"name": "add_be", "entity": "ADDRESS_BE", "pattern": r"(?i)\b(?:st(?:reet)?|str|dr|rd|road|ave|blvd|boulevard|sq|square|rue|av|avenue|bd|boulevard|straat|laan|plein)\.?$"}
    
]


DENY_LIST_RECOGNIZERS_CLIENT_C4 = [
  
    {"name": "eth_pr", "entity": "ETHNIC_ORIGIN", "deny_list": ["ethnic origin", "black", "arab", "mixed", "asian", "white", "hispanic"]},
    {"name": "pol_op", "entity": "POLITICAL_OPINION", "deny_list": ["political opinion", "liberal", "green", "conservative", "socialist"]},
    {"name": "hlth", "entity": "HEALTH", "deny_list": ["client health", "health record","chronic illness", "mental health", "disability"]},
    {"name": "rel_bel", "entity": "RELIGIOUS_BELIEF", "deny_list": ["religious belief", "religion", "religious","christian", "muslim", "jewish", "hindu", "buddhist"]},
    {"name": "phil_bel", "entity": "PHILOSOPHICAL_BELIEF", "deny_list": ["philosophical belief", "agnostic", "atheist", "humanist", "spiritual"]},
    {"name": "sex_or", "entity": "SEXUAL_ORIENTATION", "deny_list": ["sexual orientation", "asexual", "homosexual", "heterosexual","bisexual"]}


]