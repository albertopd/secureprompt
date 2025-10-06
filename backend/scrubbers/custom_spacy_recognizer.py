from typing import Tuple, Set

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.predefined_recognizers import SpacyRecognizer

import spacy

class CustomSpacyRecognizer(SpacyRecognizer):
    
    def __init__(self, path_to_model:str, supported_entities: list ):
        """
        SpacyRecognizer with a new/custom model, 
        to run in parallel with the model in NlpEngine.
        :param path_to_model: Path to the custom model's location
        """
        
        self.path_to_model = path_to_model
        self.model = None # Model will be loaded on .load()

        entities = supported_entities # TODO: Add more entities as needed
        spacy_label_groups = [({ent}, {ent}) for ent in entities]
        
        super().__init__(
                supported_language='en',
                supported_entities=entities,
                ner_strength=0.85,
                check_label_groups=spacy_label_groups
        )
    
    def load(self):
        self.model = spacy.load(self.path_to_model)
    
    def analyze(self, text, entities, nlp_artifacts=None):
        """
        Analyze using a spaCy model. Similar to SpacyRecognizer.analyze, 
        except it has an actual call to a spaCy model loaded as part of this recognizer.
        """
        results = []

        doc = self.model(text)
        
        ner_entities = doc.ents

        for entity in entities:
            if entity not in self.supported_entities:
                continue
  

            for ent in ner_entities:
                if ent.label_ not in self.supported_entities:
                    continue
                textual_explanation = f"Identified as {ent.label_} by the spaCy model: {self.path_to_model}"
                explanation = self.build_explanation(
                    self.ner_strength, textual_explanation
                )
                spacy_result = RecognizerResult(
                    entity_type=entity,
                    start=ent.start_char,
                    end=ent.end_char,
                    score=self.ner_strength,
                    analysis_explanation=explanation,
                    recognition_metadata={
                        RecognizerResult.RECOGNIZER_NAME_KEY: self.name
                    },
                )
                results.append(spacy_result)

        return results
    
    @staticmethod
    def __check_label(
        entity: str, label: str, check_label_groups: Tuple[Set, Set]
    ) -> bool:
        return any(
            [entity in egrp and label in lgrp for egrp, lgrp in check_label_groups]
        )



    ...
