import os

import os

# Recognizers configuration for C4 risk level
DEFAULT_RECOGNIZERS_C4 = [
    {"name": "person", "entity": "PERSON"},
    {"name": "email", "entity": "EMAIL_ADDRESS"},
    {"name": "cc", "entity": "CREDIT_CARD"},
    {"name": "iban", "entity": "IBAN_CODE"},
    {"name": "ph","entity": "PHONE_NUMBER"},
]

REGEX_RECOGNIZERS_C4 = [
    {"name" : "ccs", "entity": "CREDIT_CARD_SYNTHETIC", "pattern": r"\b(?:\d[ -]*?){13,19}\b"},
    {"name": "iban_be", "entity": "IBAN_BE", "pattern": r"\bBE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\b"},
    {"name": "nn_reg","entity": "NATIONAL_REG", "pattern": r"\b\d{2}[.\-]?\d{2}[.\-]?\d{2}[.\-]?\d{3}[.\-]?\d{2}\b"},
    {"name": "vat_be","entity": "VAT_BE", "pattern": r"\bBE0\d{9}\b"},
    #{"name": "ph_be","entity": "PHONE_BE", "pattern": r"(\+32\s?|0)(\d{1,2})(\s?\d{2}\s?\d{2}\s?\d{2}|\s?\d{3}\s?\d{3})"},
    {"name": "date", "entity": "DATE", "pattern": r"\b(19[0-9]{2}|20[0-4][0-9])-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])\b", "score": 0.5, "context" : ["date"]},
    {"name": "money", "entity": "FINANCIAL_AMOUNT", "pattern": r"€\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?"},
    {"name": "pin_mask", "entity": "PIN_MASKED", "pattern": r"\*{4}\d{2}"},
   
    #{"name": "cred_sc", "entity":"CREDIT_SCORE", "pattern": r"\b(3\d{2}|4\d{2}|5\d{2}|6\d{2}|7\d{2}|8[0-4]\d|850)\b", "score": 0.3, "context":["credit score", "credit"]},
    #{"name": "pin", "entity": "PIN", "pattern": r"(?<!\d)\d{4}(?!\d)", "score": 0.3, "context":["PIN", "pin", "pin code", "pin:", "code", "passcode"]},
    #{"name": "cvc", "entity": "CVC", "pattern": r"(?<!\d)\d{3}(?!\d)", "score": 0.3, "context":["CCV", "ccv", "ccv:", "cvc", "cvc:", "security code", "security number", "card security", "card code"]},
   
    {"name": "exp_dt", "entity": "EXPIRATION_DATE", "pattern": r"\b(0[1-9]|1[0-2])\s?[\/\-]\s?\d{2}\b", "context":["expiration date", "exp date", "expiry date", "valid thru", "valid through", "expires"]}
]

DENY_LIST_RECOGNIZERS_C4 = [ 
    {"name": "eth_pr", "entity": "ETHNIC_ORIGIN", "deny_list": ["ethnic origin", "black", "arab", "mixed", "asian", "white", "hispanic"]},
    {"name": "pol_op", "entity": "POLITICAL_OPINION", "deny_list": ["political opinion", "liberal", "green", "conservative", "socialist"] , "context":["political" "party", "politics"]},
    {"name": "hlth", "entity": "HEALTH", "deny_list": ["health","client health", "health record","chronic illness", "mental health", "disability"], "context":["health", "medical", "medicine", "doctor"]},
    {"name": "rel_bel", "entity": "RELIGIOUS_BELIEF", "deny_list": ["religious belief", "religion", "religious","christian", "muslim", "jewish", "hindu", "buddhist", "catholic"], "context":["religion", "religious belief"]},
    {"name": "phil_bel", "entity": "PHILOSOPHICAL_BELIEF", "deny_list": ["philosophical belief", "agnostic", "atheist", "humanist", "spiritual"]},
    {"name": "sex_or", "entity": "SEXUAL_ORIENTATION", "deny_list": ["sexual orientation", "asexual", "homosexual", "heterosexual","bisexual"]},
    {"name": "ins_pol", "entity": "INSURANCE_POLICY", "deny_list": ["insurance policy", "health insurance", "home insurance", "car insurance"], "context":["insurance", "policy","coverage"]},
    {"name": "emp_status", "entity": "EMPLOYMENT_STATUS", "deny_list": ["employment status", "employed", "unemployed", "retired"], "deny_list_score": 0.3, "context":["employment", "work"]},
    {"name": "bio_data", "entity": "BIOMETRIC_DATA", "deny_list": ["biometric data","voice", "FaceID", "fingerprint", "iris"], "context":["biometric"]}
]

BASE_MODEL_C4 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "nlp", "models_c4", "model_vers_3_small", "model-best"
)

CUSTOM_RECOGNIZERS_C4 =[{"name": "pin", 
                         "entity": "PIN",         
                         "model_path": BASE_MODEL_C4},

                        {"name": "cvv", 
                         "entity": "CVV", 
                         "model_path": BASE_MODEL_C4} ]

BASE_MODEL_C4 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "nlp", "models_c4", "model_vers_3_small", "model-best"
)

CUSTOM_RECOGNIZERS_C4 =[{"name": "pin", 
                         "entity": "PIN",         
                         "model_path": BASE_MODEL_C4},

                        {"name": "cvv", 
                         "entity": "CVV", 
                         "model_path": BASE_MODEL_C4} ]


# Recognizers configuration for C3 risk level

DEFAULT_RECOGNIZERS_C3 = [
    {"name": "person", "entity": "PERSON"},
    {"name": "email", "entity": "EMAIL_ADDRESS"},
    {"name": "ph","entity": "PHONE_NUMBER"},
]

REGEX_RECOGNIZERS_C3 = [
    {"name": "nn_reg","entity": "NATIONAL_REG", "pattern": r"\b\d{2}[.\-]?\d{2}[.\-]?\d{2}[.\-]?\d{3}[.\-]?\d{2}\b"},
    {"name" :"ag_id", "entity": "AGREEMENT_ID", "pattern": r"CUST-\d{1,4}"},
    {"name": "date", "entity": "DATE", "pattern": r"\b(19[0-9]{2}|20[0-4][0-9])-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])\b", "context" : ["date"]},
    #{"name": "ph_be","entity": "PHONE_BE", "pattern": r"(\+32\s?|0)(\d{1,2})(\s?\d{2}\s?\d{2}\s?\d{2}|\s?\d{3}\s?\d{3})"},
    {"name": "ip_addr", "entity":"IP_ADDRESS", "pattern": r"\b((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\b"},
    {"name": "pay_id", "entity": "PAYMENT_ID", "pattern": r"PO-\d{4}"},
    {"name": "pay_id", "entity": "PAYMENT_ID", "pattern": r"PO-\d{4}"},
    {"name":"ref_num", "entity": "REFERENCE_NUMBER", "pattern": r"(?i)^invoice \d{5}$"}
]

DENY_LIST_RECOGNIZERS_C3 = [
    {"name":"ag_type", "entity": "AGREEMENT_TYPE", "deny_list": ["Credit Card Agreement","Letter of Credit","Trust Agreement","Insurance Distribution Agreement","Personal Loan Agreement","Overdraft Agreement","Bank Guarantee","Safe Deposit Box Agreement","Guaranty Agreement", "Merchant Services Agreement","Auto Loan Agreement"],
    "context":["agreement", "contract"]},   
    {"name":"gn", "entity":"GENDER", "deny_list":["male", "female"], "context":["gender", "sex"]},
    {"name":"supp_rel", "entity":"SUPPLIER_RELATIONSHIP", "deny_list": ["Loan Recipient", "Insurance Subscriber", "Account Holder", "Investor"]},
    {"name":"reg_tag", "entity":"REGULATORY_TAG", "deny_list": ["KYC", "GDPR", "FATCA", "AML"], "context":["regulatory", "compliance"]},
    {"name":"pay_type", "entity":"PAYMENT_TYPE", "deny_list":["Wire Transfer", "Cheque", "SEPA Credit", "Direct Debit", "Standing Order"]},
    {"name":"prod_type", "entity":"PRODUCT_TYPE", "deny_list": ["Mobile Banking", "Life Insurance", "Investment Portfolio", "Savings Account", "Travel Insurance", "Mortgage", "Current Account", "Credit Card" ]}
]

BASE_MODEL_C3 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "nlp", "models_c3", "model_c3_v3_3_small", "model-best"
)

CUSTOM_RECOGNIZERS_C3 =[{"name": "pay_nam", "entity": "PAYMENT_NAME", "model_path": BASE_MODEL_C3 },
                        {"name": "pay_stat", "entity": "PAYMENT_STATUS", "model_path": BASE_MODEL_C3 } ]

BASE_MODEL_C3 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "nlp", "models_c3", "model_c3_v3_3_small", "model-best"
)

CUSTOM_RECOGNIZERS_C3 =[{"name": "pay_nam", "entity": "PAYMENT_NAME", "model_path": BASE_MODEL_C3 },
                        {"name": "pay_stat", "entity": "PAYMENT_STATUS", "model_path": BASE_MODEL_C3 } ]


# Recognizers configuration for C2 risk level

DEFAULT_RECOGNIZERS_C2= [
    {"name": "person", "entity": "PERSON"},
    {"name": "email", "entity": "EMAIL_ADDRESS"},
    {"name": "ph","entity": "PHONE_NUMBER"},
    {"name": "iban", "entity": "IBAN_CODE"},
]

REGEX_RECOGNIZERS_C2 = [
  {"name": "iban_be", "entity": "IBAN_BE", "pattern": r"\bBE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\b"},
  #{"name": "ph_be","entity": "PHONE_BE", "pattern": r"(\+32\s?|0)(\d{1,2})(\s?\d{2}\s?\d{2}\s?\d{2}|\s?\d{3}\s?\d{3})"},
  {"name": "date", "entity": "DATE", "pattern": r"\b(19[0-9]{2}|20[0-4][0-9])-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])\b", "score": 0.5, "context" : ["date"]},
  {"name": "app_name", "entity": "APPLICATION_NAME", "pattern": r"^app_\d{1,3}$"},
  {"name":"config_group", "entity": "CONFIG_GROUP", "pattern": r"^T\d{5}$"},
  {"name":"corp_key", "entity":"CORP_KEY", "pattern": r"^[A-Z]{2}\d{2}[A-Z]{2}\d{2}$"},

  {"name":"iass_app", "entity":"IASS_APPLICATION", "pattern": r"IaaSApp_\d{1,2}"},
  {"name":"vm_iass", "entity":"VM_IASS", "pattern": r"VM-IAAS-\d{1,2}"},
  {"name":"ntw_iass", "entity":"NETWORK_IASS", "pattern": r"NIC-IAAS-\d{1,2}"},
  {"name":"sys_iass", "entity":"VM_IASS", "pattern": r"VM-IAAS-\d{1,2}"},

  {"name":"ph_app", "entity":"PHYSICAL_APPLICATION", "pattern": r"PhysicalApp_\d{1,2}"},
  {"name":"vm_ph", "entity":"VM_PH", "pattern": r"VM-PH-\d{1,2}"},
  {"name":"ntw_ph", "entity":"NETWORK_PH", "pattern": r"NIC-PH-\d{1,2}"},
  {"name":"sys_ph", "entity":"SYS_PH", "pattern": r"SYS-PH-\d{1,2}"},

  {"name": "sys-conf", "entity": "SYSTEM_CONFIG", "pattern": r"^\d+\s+vCPU,\s+\d+\s+GB$"},

  {"name": "doc_id", "entity": "DESIGN_DOC_ID", "pattern": r"DOC[A-Z0-9]{7}"},
  {"name":"trans_id", "entity":"TRANSACTION_ID", "pattern": r"(?i)[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"},

  {"name": "prod_code", "entity": "PRODUCT_CODE", "pattern": r"BP[A-Z0-9]{6}"}
]

DENY_LIST_RECOGNIZERS_C2=[
    {"name": "guid", "entity":"GUIDELINE", "deny_list": ["Risk Governance Framework","AML Screening Guidelines","Digital Onboarding Standards","Sustainability Reporting Protocol","Cybersecurity Controls","Customer Complaint Handling","Third-Party Risk Management","Data Privacy Guidelines","Mobile Banking Security","Board Oversight Principles"], "context":["governance", "guideline", "compliance"]},
    {"name": "cl_prov", "entity": "PROVIDER", "deny_list": ["AWS", "Azure", "Google Cloud", "Internal IT"], "context":["cloud", "provider"]},
    {"name":"currency", "entity":"CURRENCY", "deny_list":["USD", "EUR", "GBP", "AUD", "JPY"], "context":["currency"]},
    {"name": "pol_name", "entity": "POLICY_NAME", "deny_list": ["Credit Risk Policy","AML Compliance Policy","Data Security Policy","Customer Service Policy","Operational Risk Policy","Loan Approval Policy","KYC Policy","IT Governance Policy","Fraud Detection Policy","Privacy Protection Policy"], "context":["policy"]},
    {"name": "process", "entity": "PROCESS", "deny_list": ["Customer Onboarding","Loan Origination","KYC Verification","AML Screening","Credit Scoring","Account Closure", "Transaction Monitoring","Fraud Detection","Mobile App Update","ATM Reconciliation", "Statement Generation","Customer Complaint Handling","Password Reset","Data Backup","Regulatory Reporting","Internal Audit","Risk Assessment","Employee Onboarding","Vendor Management"], "context":["process"]},
]