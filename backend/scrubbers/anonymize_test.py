import pandas as pd
from scrubbers.text_scrubber import TextScrubber

def get_test_text(df: pd.DataFrame):
  prompts=[]
  responses =[]

  if 'Prompt' in df.columns:
    prompts.extend(df['Prompt'].tolist())
  elif 'Original Prompt' in df.columns:
    prompts.extend(df['Original Prompt'].tolist())

  if 'Response' in df.columns:
    responses.extend(df['Response'].tolist())
  elif 'Original Response' in df.columns:
    responses.extend(df['Original Response'].tolist())
    
  return prompts, responses

def test_anonymization(text_to_anonymize: str, risk_level: str = "C4"):
  text_scrubber = TextScrubber(risk_level=risk_level)
  text_scrubber.add_pattern_recognizers()
  text_scrubber.add_list_recognizers()
  text_scrubber.add_spacy_recognizers()
  anonymized = text_scrubber.anonymize_text(text_to_anonymize)
  return anonymized


if __name__ == "__main__":

  file_paths = ["/home/javanegas/estefy/Anonymization/anonymization-presidio/csv_files_PROMPTS/prompts_01_05_15.csv", 
                "/home/javanegas/estefy/Anonymization/anonymization-presidio/csv_files_PROMPTS/prompts_01_06_14.csv",
                "/home/javanegas/estefy/Anonymization/anonymization-presidio/csv_files_PROMPTS/prompts_01_06_18.csv"]

  df_test = pd.read_csv(file_paths[0])
  prompts, responses = get_test_text(df_test)


  test_prompts =["""I have 54.000 euros in my bank account with IBAN BE12 3456 7890 1234.""",

  """Mary Smith is of Asian descent and a votes for the socialist party.
    Confirm if she is heterosexual and has a chronic illness? 
    She has 35000 dollars in her savings account.""",

   """Linda Walker was born on 1996-05-28 with National ID 96.05.28-537.79. Her phone number is +32 68 536 512.
   Her email is laura.walker@proximus.be.  Provide her IBAN.
   Currently she have $5,000 in her account.""",

   """To whom it belongs the IBAN BE64322050574468, biometric data FaceID 
   with credit card number 5390880703591623, CVV 910 and expiry date 02/28 ? 
   Also, this person has 75.000 in savings and 54650 in checking account.""",
]


  for text in test_prompts:
    print("**********************************")
    print("Original Text: ", text)
    print("Anonymized Text level C2: ", test_anonymization(text, risk_level="C2"))
    print("**********************************")

