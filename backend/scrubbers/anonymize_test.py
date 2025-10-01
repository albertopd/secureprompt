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

artificial_prompts =[ "John Smith, living at 45 Green Street, Brussels 1000, phone +32 475 123 456 "
"is of Arab ethnic origin and a practicing muslim."
"His IBAN is BE78676613260743 and his credit card 5851 9202 8729 1507. He voted for the socialist party.",

"Maria Gonzalez, 12 Rue de la Loi, 1040 Etterbeek, phone 0478 555 222,"
"is Hispanic and identifies as Christian. "
"She has a chronic illness that requires ongoing treatment. "
"Her card number is 4532 6987 2209 8871 and her IBAN is BE24699985452067.",

"David Cohen, address 89 Avenue Louise, 1050 Brussels, phone +32 488 444 321,"
"is Jewish and politically liberal. "
"His health record mentions a disability. "
"His MasterCard is 5100 4321 8765 1234 and IBAN BE75573778827078.",

"Anika Sharma, 5 Drève des Chênes, 1410 Waterloo, phone 0472 333 999,"
"is of Asian ethnic origin and follows Hindu religious beliefs. "
"She supports the Green party. "
"Her credit card is 3714 496353 98431 and IBAN BE67999912345678."

]

for text in artificial_prompts:
  test_anonymization(text)

