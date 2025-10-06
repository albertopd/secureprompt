import pandas as pd
from scrubbers.custom_spacy_recognizer import CustomSpacyRecognizer
from scrubbers.text_scrubber import TextScrubber
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine

from presidio_analyzer.predefined_recognizers import SpacyRecognizer

from presidio_analyzer.nlp_engine import NlpEngineProvider


class AnonymizationTest:
  def __init__(self):
    nlp_configuration = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "en", "model_name": "en_core_web_lg"},
    ],
}

    nlp_engine = NlpEngineProvider(nlp_configuration=nlp_configuration).create_engine()
    self.analyzer =AnalyzerEngine(nlp_engine=nlp_engine)
    self.anonymizer = AnonymizerEngine()

  def add_custom_recognizers(self) -> None:
        custom_spacy = CustomSpacyRecognizer(
           path_to_model="./scrubbers/nlp/models/pin_ccv_model", 
           supported_entities=["PIN", "CVV"])
        self.analyzer.registry.add_recognizer(custom_spacy)

  def add_spacy_recognizers(self) -> None:

      spacy_money = SpacyRecognizer(
          supported_entities=["MONEY"])
      self.analyzer.registry.add_recognizer(spacy_money)

  def anonymize_text(self,text: str):
      # Call analyzer with entity names only
      results = self.analyzer.analyze(
          text=text,
          entities=["MONEY", "PIN", "CVV"],
          language="en"
      )
      anonymized_text = self.anonymizer.anonymize(
          text=text, 
          analyzer_results=results
      )
      return anonymized_text



if __name__ == "__main__":
  test = AnonymizationTest()
  test.add_spacy_recognizers()
  test.add_custom_recognizers()


  test_prompts =["""I have 54.000 euros in my bank account.""", """The PIN number of my card is 4355""",

  """She has 35000 dollars in her savings account.""", """Her card's PIN is 8586.""",

   """Currently she has $5,000 in her account.""", """Her PIN is 2389 """,

   """Follow-up on ticket #54321 for Kendra Clayton. They confirmed their PIN is 7968 and the issue is resolved. Their CVV is 123."""
]

  
  for text in test_prompts:
    print("**********************************")
    print("Original Text: ", text)
    print("Anonymized Text level C2: ", test.anonymize_text(text))
    print("**********************************")

