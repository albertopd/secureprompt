import re
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from scrubbers.recognizers import (
    DENY_LIST_RECOGNIZERS_C4,
    REGEX_RECOGNIZERS_C4,
    DEFAULT_RECOGNIZERS_C4,
    DENY_LIST_RECOGNIZERS_C3,
    DEFAULT_RECOGNIZERS_C3,
    REGEX_RECOGNIZERS_C3,
    DENY_LIST_RECOGNIZERS_C2,
    DEFAULT_RECOGNIZERS_C2,
    REGEX_RECOGNIZERS_C2,
)


class TextScrubber:
    def __init__(self, secret: str | bytes = b"dev_secret", risk_level: str = "C4"):
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        self.risk_level = risk_level
        # compile patterns
        self.recognizers = []

        if risk_level == "C4":
            recognizers_list = (
                REGEX_RECOGNIZERS_C4 + REGEX_RECOGNIZERS_C3 + REGEX_RECOGNIZERS_C2
            )
        elif risk_level == "C3":
            recognizers_list = REGEX_RECOGNIZERS_C3 + REGEX_RECOGNIZERS_C2
        elif risk_level == "C2":
            recognizers_list = REGEX_RECOGNIZERS_C2

        for r in recognizers_list:
            pattern = re.compile(r["pattern"], flags=re.IGNORECASE)
            self.recognizers.append({**r, "compiled": pattern})

        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

    def add_pattern_recognizers(self) -> None:

        for rec in self.recognizers:
            pattern = Pattern(
                name=f"{rec['name']}_pattern",
                regex=rec["pattern"],
                score=rec.get("score", 0.8),
            )

            recognizer = PatternRecognizer(
                supported_entity=rec["entity"],
                patterns=[pattern],
                context=rec.get("context", []),
            )

            self.analyzer.registry.add_recognizer(recognizer)

    def add_list_recognizers(self) -> None:

        if self.risk_level == "C4":
            recognizers_list = (
                DENY_LIST_RECOGNIZERS_C4
                + DENY_LIST_RECOGNIZERS_C3
                + DENY_LIST_RECOGNIZERS_C2
            )
        elif self.risk_level == "C3":
            recognizers_list = DENY_LIST_RECOGNIZERS_C3 + DENY_LIST_RECOGNIZERS_C2
        elif self.risk_level == "C2":
            recognizers_list = DENY_LIST_RECOGNIZERS_C2

        for rec in recognizers_list:
            recognizer = PatternRecognizer(
                supported_entity=rec["entity"],
                deny_list=rec["deny_list"],
                context=rec.get("context", []),
                deny_list_score=rec.get("deny_list_score", 0.7),
            )
            self.analyzer.registry.add_recognizer(recognizer)

    def anonymize_text(
        self, text: str, target_risk: str = "C4", language: str = "en"
    ) -> dict:

        classification_entities = []

        if target_risk == "C2":
            full_rec_list = (
                DEFAULT_RECOGNIZERS_C2 + REGEX_RECOGNIZERS_C2 + DENY_LIST_RECOGNIZERS_C2
            )
        elif target_risk == "C3":
            full_rec_list = (
                DEFAULT_RECOGNIZERS_C3
                + REGEX_RECOGNIZERS_C3
                + DENY_LIST_RECOGNIZERS_C3
                + DEFAULT_RECOGNIZERS_C2
                + REGEX_RECOGNIZERS_C2
                + DENY_LIST_RECOGNIZERS_C2
            )
        else:
            full_rec_list = (
                DEFAULT_RECOGNIZERS_C4
                + REGEX_RECOGNIZERS_C4
                + DENY_LIST_RECOGNIZERS_C4
                + DEFAULT_RECOGNIZERS_C3
                + REGEX_RECOGNIZERS_C3
                + DENY_LIST_RECOGNIZERS_C3
                + DEFAULT_RECOGNIZERS_C2
                + REGEX_RECOGNIZERS_C2
                + DENY_LIST_RECOGNIZERS_C2
            )

        for rec in full_rec_list:
            classification_entities.append(rec["entity"])

        analyzer_results = self.analyzer.analyze(
            text=text,
            entities=classification_entities,
            language=language,
            return_decision_process=True,
        )

        anonymized_result = self.anonymizer.anonymize(
            text=text, analyzer_results=analyzer_results  # type: ignore
        )

        # Build a quick lookup of scores from analyzer results
        scores_map = {
            (r.entity_type, r.start): getattr(r, "score", 0.5) for r in analyzer_results
        }

        # Sort items left-to-right to assign numbering in reading order
        items_sorted = sorted(anonymized_result.items, key=lambda it: it.start)

        counters = {}  # counts per entity type
        replacement_map = {}  # (start,end) -> replacement token
        entities = []

        # Assign replacement tokens in LEFT->RIGHT order and build entities list
        for item in items_sorted:
            key = (item.entity_type, item.start)
            score = scores_map.get(key, 0.5)

            # Increment counter and create token like <PHONE_BE_1>
            counters[item.entity_type] = counters.get(item.entity_type, 0) + 1
            entity = f"<{item.entity_type}_{counters[item.entity_type]}>"

            replacement_map[(item.start, item.end)] = entity

            entities.append(
                {
                    "type": item.entity_type,
                    "start": item.start,
                    "end": item.end,
                    "original": text[item.start : item.end],
                    "replacement": entity,
                    "explanation": f"{item.entity_type} detected",
                    "score": score,
                }
            )

        return {"anonymized_text": anonymized_result.text, "entities": entities}
