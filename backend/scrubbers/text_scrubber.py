import re
import spacy
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.predefined_recognizers import SpacyRecognizer

from presidio_analyzer.nlp_engine import NlpEngineProvider

from audit.auditor import Auditor
from scrubbers.recognizers import DENY_LIST_RECOGNIZERS_C4, REGEX_RECOGNIZERS_C4, DEFAULT_RECOGNIZERS_C4, DENY_LIST_RECOGNIZERS_C3, DEFAULT_RECOGNIZERS_C3, REGEX_RECOGNIZERS_C3, DENY_LIST_RECOGNIZERS_C2, DEFAULT_RECOGNIZERS_C2, REGEX_RECOGNIZERS_C2


class TextScrubber:
    def __init__(self, secret: str | bytes = b'dev_secret', risk_level:str="C4"):

        nlp_configuration = {
        "nlp_engine_name": "spacy",
        "models": [
            {"lang_code": "en", "model_name": "en_core_web_lg"},
        ],

         }

        nlp_engine = NlpEngineProvider(nlp_configuration=nlp_configuration).create_engine()
        if isinstance(secret, str):
            secret = secret.encode('utf-8')
        self.auditor = Auditor()
        self.risk_level = risk_level
        # compile patterns
        self.recognizers = []
        self.classification_entities =[]

        if risk_level == "C4":
            recognizers_list = REGEX_RECOGNIZERS_C4 
        elif risk_level == "C3":
            recognizers_list = REGEX_RECOGNIZERS_C3 + REGEX_RECOGNIZERS_C4
        elif risk_level == "C2":
            recognizers_list = REGEX_RECOGNIZERS_C2 +REGEX_RECOGNIZERS_C3 + REGEX_RECOGNIZERS_C4

        for r in recognizers_list:
            pattern = re.compile(r['pattern'], flags=re.IGNORECASE)
            self.recognizers.append({**r, "compiled": pattern})


        if self.risk_level == "C4":
            full_rec_list = DEFAULT_RECOGNIZERS_C4 + REGEX_RECOGNIZERS_C4 + DENY_LIST_RECOGNIZERS_C4 

        elif self.risk_level == "C3":
            full_rec_list = DEFAULT_RECOGNIZERS_C3 + REGEX_RECOGNIZERS_C3 + DENY_LIST_RECOGNIZERS_C3 + DEFAULT_RECOGNIZERS_C4 + REGEX_RECOGNIZERS_C4 + DENY_LIST_RECOGNIZERS_C4
        
        elif self.risk_level == "C2":
            full_rec_list = DEFAULT_RECOGNIZERS_C2 + REGEX_RECOGNIZERS_C2 + DENY_LIST_RECOGNIZERS_C2 + DEFAULT_RECOGNIZERS_C3 + REGEX_RECOGNIZERS_C3 + DENY_LIST_RECOGNIZERS_C3 + DEFAULT_RECOGNIZERS_C4 + REGEX_RECOGNIZERS_C4 + DENY_LIST_RECOGNIZERS_C4 + [{"name": "money", "entity": "MONEY"}]

        for rec in full_rec_list:
            self.classification_entities.append(rec["entity"])
        
        self.analyzer =AnalyzerEngine(nlp_engine=nlp_engine)
        self.anonymizer = AnonymizerEngine()


    def add_pattern_recognizers(self) -> None:

        for rec in self.recognizers:
            pattern=Pattern(
                name= f"{rec['name']}_pattern", 
                regex= rec['pattern'], 
                score= rec.get("score", 0.8)   
            )

            recognizer = PatternRecognizer(
                supported_entity=rec["entity"],
                patterns=[pattern],
                context=rec.get("context", []) 
            )

            self.analyzer.registry.add_recognizer(recognizer)

    def add_list_recognizers(self) -> None:

        if self.risk_level == "C4":
            recognizers_list = DENY_LIST_RECOGNIZERS_C4 
        elif self.risk_level == "C3":
            recognizers_list = DENY_LIST_RECOGNIZERS_C3 + DENY_LIST_RECOGNIZERS_C4
        elif self.risk_level == "C2":
            recognizers_list = DENY_LIST_RECOGNIZERS_C2 + DENY_LIST_RECOGNIZERS_C3 + DENY_LIST_RECOGNIZERS_C4

        for rec in recognizers_list:
            recognizer = PatternRecognizer(
                supported_entity=rec["entity"],
                deny_list=rec["deny_list"],
                context=rec.get("context", []),
                deny_list_score=rec.get("deny_list_score", 0.7)
        )
            self.analyzer.registry.add_recognizer(recognizer)


    def add_spacy_recognizers(self) -> None:
        spacy_money = SpacyRecognizer(
        supported_entities=["MONEY"])
        self.analyzer.registry.add_recognizer(spacy_money)


    def anonymize_text(self, text:str, language: str ="en") -> str:


        results = self.analyzer.analyze(text=text, entities=self.classification_entities, language='en')

        anonymized_text = self.anonymizer.anonymize(text=text, analyzer_results=results)

        return anonymized_text.text


    def scrub(self, text: str, target_risk: str = "C3", language: str = "en") -> dict:
        """Detect spans, replace them with stable tokens, and append to ledger."""
        entities = []
        redacted = text
        # To avoid shifting indices during replacement, collect matches first
        matches = []
        for rec in self.recognizers:
            for m in rec['compiled'].finditer(text):
                matches.append({
                    "start": m.start(),
                    "end": m.end(),
                    "span": m.group(0),
                    "type": rec['entity'],
                    "source": "regex",
                    "score": rec.get('score', 0.9)
                })
        # sort by start descending so replacements don't break indices
        matches = sorted(matches, key=lambda x: x['start'], reverse=True)
        replacements = {}
        counts = {}
        for m in matches:
            etype = m['type']
            counts.setdefault(etype, 0)
            counts[etype] += 1
            token = f"[[{etype}_{counts[etype]}]]"
            # perform redaction
            redacted = redacted[:m['start']] + token + redacted[m['end']:]
            entities.append({
                "span": m['span'],
                "type": etype,
                "replacement": token,
                "source": m['source'],
                "score": m['score'],
                "start": m['start'],
                "end": m['end'],
                "explanation": f"{etype} detected by {m['source']}"
            })
            replacements[token] = m['span']
        return {
            "label": "LOW" if not entities else "MEDIUM",
            "entities": entities,
            "redacted_text": redacted
        }

