

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
    {"name": "pc_be", "entity": "POSTAL_CODE_BE", "pattern": r"\b[1-9][0-9]{3}\b", "score": 0.3, "context":["postal code", "postcode", "zip code", "zip"]},
    {"name": "birth_dt", "entity": "BIRTH_DATE", "pattern": r"\b(19[0-9]{2}|20[0-4][0-9])-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])\b", "context" : ["birth date", "date of birth", "dob", "born on"]},
    {"name": "pin_mask", "entity": "PIN_MASKED", "pattern": r"\*{4}\d{2}"},
   
    {"name": "cred_sc", "entity":"CREDIT_SCORE", "pattern": r"\b(3\d{2}|4\d{2}|5\d{2}|6\d{2}|7\d{2}|8[0-4]\d|850)\b", "score": 0.3, "context":["credit score", "credit"]},
    {"name": "pin", "entity": "PIN", "pattern": r"(?<!\d)\d{4}(?!\d)", "score": 0.3, "context":["PIN", "pin", "pin code", "pin:", "code", "passcode"]},
    {"name": "ccv", "entity": "CCV", "pattern": r"(?<!\d)\d{3}(?!\d)", "score": 0.3, "context":["CCV", "ccv", "ccv:", "cvc", "cvc:", "security code", "security number", "card security", "card code"]},
   
    {"name": "exp_dt", "entity": "EXPIRATION_DATE", "pattern": r"\b(0[1-9]|1[0-2])\s?[\/\-]\s?\d{2}\b", "context":["expiration date", "exp date", "expiry date", "valid thru", "valid through", "expires"]}

]


DENY_LIST_RECOGNIZERS_CLIENT_C4 = [
  
    {"name": "eth_pr", "entity": "ETHNIC_ORIGIN", "deny_list": ["ethnic origin", "black", "arab", "mixed", "asian", "white", "hispanic"]},
    {"name": "pol_op", "entity": "POLITICAL_OPINION", "deny_list": ["political opinion", "liberal", "green", "conservative", "socialist"] , "context":["political" "party", "politics"]},
    {"name": "hlth", "entity": "HEALTH", "deny_list": ["health","client health", "health record","chronic illness", "mental health", "disability"], "context":["health", "medical", "medicine", "doctor"]},
    {"name": "rel_bel", "entity": "RELIGIOUS_BELIEF", "deny_list": ["religious belief", "religion", "religious","christian", "muslim", "jewish", "hindu", "buddhist", "catholic"], "context":["religion", "religious belief"]},
    {"name": "phil_bel", "entity": "PHILOSOPHICAL_BELIEF", "deny_list": ["philosophical belief", "agnostic", "atheist", "humanist", "spiritual"]},
    {"name": "sex_or", "entity": "SEXUAL_ORIENTATION", "deny_list": ["sexual orientation", "asexual", "homosexual", "heterosexual","bisexual"]},
    {"name": "ins_pol", "entity": "INSURANCE_POLICY", "deny_list": ["insurance policy", "health insurance", "home insurance", "car insurance"], "context":["insurance", "policy","coverage"]},
    {"name": "emp_status", "entity": "EMPLOYMENT_STATUS", "deny_list": ["employment status", "employed", "unemployed", "retired"], "context":["employment", "work"]},
    {"name": "bio_data", "entity": "BIOMETRIC_DATA", "deny_list": ["biometric data","voice", "FaceID", "fingerprint", "iris"], "context":["biometric"]}
]

