import spacy
from spacy.pipeline import EntityRuler

# Load your trained model
nlp = spacy.load("./models/model_vers_3_small/model-best")

# Add the EntityRuler AFTER 'ner'
ruler = nlp.add_pipe("entity_ruler", after="ner")

# Add your patterns
patterns = patterns = [
    {"label": "PIN", "pattern": [{"TEXT": {"REGEX": r"[^\d]+\d{4}[^\d|^\-]+"}}]},
    {"label": "CVV", "pattern": [{"TEXT": {"REGEX": r"[^\d]+\d{3}[^\d|^\-]+"}}]},
]
ruler.add_patterns(patterns)

# Save updated pipeline
nlp.to_disk("./models/model_vers3.2_with_ruler")
print("Model saved to models/model_vers3.2_with_ruler")
