import re
import time
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from audit.auditor import Auditor
from scrubbers.recognizers import RECOGNIZERS_CLIENT_C4, DEFAULT_RECOGNIZERS_CLIENT_C4


class TextScrubber:
    def __init__(self, secret: str | bytes = b'dev_secret'):
        if isinstance(secret, str):
            secret = secret.encode('utf-8')
        self.auditor = Auditor()
        # compile patterns
        self.recognizers = []
        for r in RECOGNIZERS_CLIENT_C4:
            pattern = re.compile(r['pattern'], flags=re.IGNORECASE)
            self.recognizers.append({**r, "compiled": pattern})
        
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        


    def add_recognizers(self):

        for rec in self.recognizers:
            pattern=Pattern(
                name= f"{rec['name']}_pattern", 
                regex= rec['pattern'], 
                score= 0.8    
            )

            recognizer = PatternRecognizer(
                supported_entity=rec["entity"],
                patterns=[pattern]
            )

            self.analyzer.registry.add_recognizer(recognizer)


    def anonymize_text(self, text:str, target_risk: str = "C4", language: str ="en") -> str:

        classification_entities = [] 

        if target_risk == "C4":
            for rec in DEFAULT_RECOGNIZERS_CLIENT_C4 + RECOGNIZERS_CLIENT_C4:
                classification_entities.append(rec["entity"])
        else:
            pass # Todo: Define for other risk levels

        results = self.analyzer.analyze(text=text , entities = classification_entities,language='en')
        print(results)

        anonymized_text = self.anonymizer.anonymize(text=text, analyzer_results=results)

        return anonymized_text


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

