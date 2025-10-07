from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.predefined_recognizers import SpacyRecognizer
import spacy


nlp_model = spacy.load("models/model_vers_4/model-best")
text = "Customer's password is r#45231, the PIN is 9343 and CVV 123"
doc = nlp_model(text)

entities = [(ent.text, ent.label_) for ent in doc.ents]
print(entities)
