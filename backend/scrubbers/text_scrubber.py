import re
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities.engine import RecognizerResult as AnonymizerRecognizerResult
from scrubbers.recognizers import (
    DENY_LIST_RECOGNIZERS_CLIENT_C4,
    RECOGNIZERS_CLIENT_C4,
    DEFAULT_RECOGNIZERS_CLIENT_C4,
)


class TextScrubber:
    def __init__(self):
        # Compile patterns
        self.recognizers = []
        for r in RECOGNIZERS_CLIENT_C4:
            pattern = re.compile(r["pattern"], flags=re.IGNORECASE)
            self.recognizers.append({**r, "compiled": pattern})

        self.analyzer = AnalyzerEngine(log_decision_process=True)
        self.anonymizer = AnonymizerEngine()

        self.add_pattern_recognizers()
        self.add_list_recognizers()

    def add_pattern_recognizers(self) -> None:

        for rec in self.recognizers:
            pattern = Pattern(
                name=f"{rec['name']}_pattern",
                regex=rec["pattern"],
                score=rec.get("score", 0.9)
            )

            recognizer = PatternRecognizer(
                supported_entity=rec["entity"],
                patterns=[pattern],
                context=rec.get("context", [])
            )

            self.analyzer.registry.add_recognizer(recognizer)

    def add_list_recognizers(self) -> None:

        for rec in DENY_LIST_RECOGNIZERS_CLIENT_C4:
            recognizer = PatternRecognizer(
                supported_entity=rec["entity"],
                deny_list=rec["deny_list"],
                context=rec.get("context", []),
            )
            self.analyzer.registry.add_recognizer(recognizer)

    def anonymize_text(
        self, text: str, target_risk: str = "C4", language: str = "en"
    ) -> dict:

        classification_entities = []

        if target_risk == "C4":
            for rec in (
                DEFAULT_RECOGNIZERS_CLIENT_C4
                + RECOGNIZERS_CLIENT_C4
                + DENY_LIST_RECOGNIZERS_CLIENT_C4
            ):
                classification_entities.append(rec["entity"])
        else:
            pass  # Todo: Define for other risk levels

        results = self.analyzer.analyze(
            text=text, entities=classification_entities, language=language, return_decision_process=True
        )

        # Convert presidio_analyzer RecognizerResult to presidio_anonymizer RecognizerResult
        converted_results = [
            AnonymizerRecognizerResult(
                entity_type=r.entity_type,
                start=r.start,
                end=r.end,
                score=r.score,
            )
            for r in results
        ]

        anonymized_result = self.anonymizer.anonymize(
            text=text, analyzer_results=converted_results
        )
  
        # Build a quick lookup of scores from analyzer results
        scores_map = {
            (r.entity_type, r.start): getattr(r, "score", 0.5)
            for r in results
        }

        # Sort items left-to-right to assign numbering in reading order
        items_sorted = sorted(anonymized_result.items, key=lambda it: it.start)

        counters = {}               # counts per entity type
        replacement_map = {}        # (start,end) -> replacement token
        entities = []

        # Assign replacement tokens in LEFT->RIGHT order and build entities list
        for item in items_sorted:
            key = (item.entity_type, item.start)
            score = scores_map.get(key, 0.0)

            # Increment counter and create token like <PHONE_BE_1>
            counters[item.entity_type] = counters.get(item.entity_type, 0) + 1
            token = f"<{item.entity_type}_{counters[item.entity_type]}>"

            replacement_map[(item.start, item.end)] = token

            entities.append({
                "span": text[item.start:item.end],      # original span from raw text
                "type": item.entity_type,
                "replacement": token,
                "source": "Presidio Analyzer",
                "score": score,
                "start": item.start,
                "end": item.end,
                "explanation": f"{item.entity_type} detected by Presidio Analyzer",
            })

        # Perform replacements on the original redacted text, going from right->left
        orig_text = anonymized_result.text  # or use your original `text` variable
        redacted_text = orig_text

        # Sort replacement_map by start index descending to avoid shifting positions
        for (start, end), token in sorted(replacement_map.items(), key=lambda kv: kv[0][0], reverse=True):
            redacted_text = redacted_text[:start] + token + redacted_text[end:]

        return {"redacted_text": redacted_text, "entities": entities}

