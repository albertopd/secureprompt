import pandas as pd
from scrubbers.text_scrubber import TextScrubber

def get_test_text(excel_files: list[str]):
  prompts=[]
  responses =[]
  for file in excel_files:
    df = pd.read_excel(file)
    prompts.extend(df['Original Prompt'].tolist())
    if 'Response' in df.columns:
      responses.extend(df['Response'].tolist())
    elif 'Original Response' in df.columns:
        responses.extend(df['Original Response'].tolist())
    else:
      responses.extend([])  
    
    return prompts, responses

def test_anonymization(text_to_anonymize: str):
  text_scrubber = TextScrubber()
  text_scrubber.add_recognizers()

  anonymized = text_scrubber.anonymize_text(text_to_anonymize)
  print("Anonymized text:", anonymized)


if __name__ == "__main__":
  prompts, responses = get_test_text(["/home/javanegas/estefy/Anonymization/BECODE/PROMPTS/prompts_08_17_18.xlsx", 
                 "/home/javanegas/estefy/Anonymization/BECODE/PROMPTS/prompts_13_16_18.xlsx",
                 "/home/javanegas/estefy/Anonymization/BECODE/PROMPTS/prompts_09_16_17.xlsx"])
  
  #print(prompts)
  #print(responses)

  for text in prompts:
    test_anonymization(text)