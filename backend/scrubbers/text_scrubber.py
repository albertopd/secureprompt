from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from typing import List

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
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.classification_entities = self._setup_classification_entities()

        self._register_pattern_recognizers()
        self._register_list_recognizers()

    def _distinct_by_entity(self, items: List[dict]) -> List[dict]:
        seen = set()
        result = []
        for item in items:
            if (e := item["entity"]) not in seen:
                seen.add(e)
                result.append(item)
        return result

    def _register_pattern_recognizers(self) -> None:
        recognizers = self._distinct_by_entity(
            REGEX_RECOGNIZERS_C4 
            + REGEX_RECOGNIZERS_C3 
            + REGEX_RECOGNIZERS_C2
        )

        for rec in recognizers:
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

    def _register_list_recognizers(self) -> None:
        recognizers = self._distinct_by_entity(
            DENY_LIST_RECOGNIZERS_C4
            + DENY_LIST_RECOGNIZERS_C3
            + DENY_LIST_RECOGNIZERS_C2
        )

        for rec in recognizers:
            recognizer = PatternRecognizer(
                supported_entity=rec["entity"],
                deny_list=rec["deny_list"],
                context=rec.get("context", []),
                deny_list_score=rec.get("deny_list_score", 0.7),
            )
            self.analyzer.registry.add_recognizer(recognizer)

    def _setup_classification_entities(self) -> dict[str, List[str]]:
        classification_entities = {}

        c2_rec_list = (
            DEFAULT_RECOGNIZERS_C2
            + REGEX_RECOGNIZERS_C2
            + DENY_LIST_RECOGNIZERS_C2
        )
        classification_entities["C2"] = [rec["entity"] for rec in c2_rec_list]

        c3_rec_list = (
            DEFAULT_RECOGNIZERS_C3
            + REGEX_RECOGNIZERS_C3
            + DENY_LIST_RECOGNIZERS_C3
            + DEFAULT_RECOGNIZERS_C2
            + REGEX_RECOGNIZERS_C2
            + DENY_LIST_RECOGNIZERS_C2
        )
        classification_entities["C3"] = [rec["entity"] for rec in c3_rec_list]

        c4_rec_list =(
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
        classification_entities["C4"] = [rec["entity"] for rec in c4_rec_list]

        return classification_entities

    def scrub_text(
        self, text: str, target_risk: str = "C4", language: str = "en"
    ) -> dict:
        """
        Scrubs (anonymizes) the input text based on the target risk level and language.
        Returns a dictionary with the anonymized text and a list of detected entities.
        """
        class_entities = self.classification_entities.get(target_risk.strip().upper(), [])

        analyzer_results = self.analyzer.analyze(
            text=text,
            entities=class_entities,
            language=language
        )

        # Sort analyzer results by their start position first and second by score
        analyzer_results.sort(key=lambda r: (r.start, r.score))

        anonymized_result = self.anonymizer.anonymize(
            text=text, 
            analyzer_results=analyzer_results  # type: ignore
        )

        # Sort anonymized results by their start position
        anonymized_result.items.sort(key=lambda r: r.start)

        entities = []
        for res in anonymized_result.items:
            explanation = f"{res.entity_type.lower().replace('_', ' ').capitalize()} detected"

            # Find matching result from analyzer
            original = ""
            score = 0.5
            while analyzer_results:
                candidate = analyzer_results.pop(0)
                if candidate.entity_type == res.entity_type:
                    original = text[candidate.start : candidate.end]
                    score = candidate.score
                    break

            entities.append(
                {
                    "type": res.entity_type,
                    "start": res.start,
                    "end": res.end,
                    "original": original,
                    "replacement": f"<{res.entity_type}>",
                    "explanation": explanation,
                    "score": score
                }
            )

        return {"scrubbed_text": anonymized_result.text, "entities": entities}

    def descrub_text(self, scrubbed_text: str, entities: list[dict]) -> str:
        """
        Reverses the scrubbing by replacing tokens with their original values.
        """
        descrubbed_text = scrubbed_text

        # Sort entities by start position in reverse order to avoid messing up indices
        entities_sorted = sorted(entities, key=lambda e: e["start"], reverse=True)

        for entity in entities_sorted:
            descrubbed_text = (
                descrubbed_text[: entity["start"]]
                + entity["original"]
                + descrubbed_text[entity["end"] :]
            )

        return descrubbed_text
