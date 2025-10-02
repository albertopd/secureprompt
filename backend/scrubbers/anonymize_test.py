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
  anonymized = text_scrubber.anonymize_text(text_to_anonymize)
  return anonymized


if __name__ == "__main__":

  file_paths = ["/home/javanegas/estefy/Anonymization/BECODE/PROMPTS/prompts_08_17_18.xlsx", 
                "/home/javanegas/estefy/Anonymization/BECODE/PROMPTS/prompts_13_16_18.xlsx",
                "/home/javanegas/estefy/Anonymization/BECODE/PROMPTS/prompts_09_16_17.xlsx"]

  df_test = pd.read_excel(file_paths[0])
  prompts, responses = get_test_text(df_test)


  test_prompts =["""Provide a compliance sample set: 03488215-4c4a-49aa-ae1c-b7f6ede56a4a (Pending), 
  7f244a6e-6042-4b1f-b1e4-aced4fc1087d (Completed), 5518158a-0d88-48fb-9ed9-db32800c5216 (Failed), 
  2fc89765-a638-4b6a-881a-83b5cfa4b877 (Pending), 36d0b951-2d3d-4161-abff-147784fb9e6d (Completed)."""]


  for text in responses:
    print("**********************************")
    print("Original Text: ", text)
    print("Anonymized Text level C4: ", test_anonymization(text, risk_level="C4"))
    print("**********************************")

