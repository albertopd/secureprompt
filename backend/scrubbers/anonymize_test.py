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
  text_scrubber.add_pattern_recognizers()
  text_scrubber.add_list_recognizers()
  anonymized = text_scrubber.anonymize_text(text_to_anonymize)
  print("Anonymized text:", anonymized)


if __name__ == "__main__":
  prompts, responses = get_test_text(["/home/javanegas/estefy/Anonymization/BECODE/PROMPTS/prompts_08_17_18.xlsx", 
                 "/home/javanegas/estefy/Anonymization/BECODE/PROMPTS/prompts_13_16_18.xlsx",
                 "/home/javanegas/estefy/Anonymization/BECODE/PROMPTS/prompts_09_16_17.xlsx"])

artificial_prompts =[ "I live in 1234 Maple ST and my PIN is 1234.",
                      "My credit score is 750 and my birth date is 1990-05-15",
                      "4321 is a random number, but 5678 is my PIN code.",
                      "my pin is 9876 and my CCV is 123",
                      "234 keilagh",
                      "My ccv is 457",
                      "My credit score is 820 and my expiration date is 12/25",
                      "My card expires on 11-24 and my credit score is 680",
                      "My ccv is 321 and my pin is 4567"

]

for text in artificial_prompts:
  test_anonymization(text)

