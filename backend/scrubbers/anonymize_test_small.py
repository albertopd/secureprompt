import pandas as pd
from custom_spacy_recognizer import CustomSpacyRecognizer
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
           path_to_model="./nlp/models/model_vers_3_small/model-best", 
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


  test_prompts = [
  "Phone order from Jennifer Maddox. Card CVV is 323. Should I process?",
  "David Coleman's CVV 871 used in suspicious transaction.",
  "Kevin Johnson correctly provided PIN 2034 but CVV 175 doesn't match. Proceed?",
  "James Gonzalez accidentally shared CVV 481 on social media. How should we proceed?",
  "Whose PIN 4821 is this?",
    "Alert: Multiple failed attempts with PIN 5732. Lock account?",
    "Confirm if PIN 1943 belongs to Sarah Lee.",
  ]

  
  for text in test_prompts:
    print("**********************************")
    print("Original Text: ", text)
    print("Anonymized Text level C2: ", test.anonymize_text(text))
    print("**********************************")

