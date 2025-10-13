from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from typing import List
from scrubbers.custom_spacy_recognizer import CustomSpacyRecognizer

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
    CUSTOM_RECOGNIZERS_C3,
    CUSTOM_RECOGNIZERS_C4
    )

# Optional custom model integration
try:
    from scrubbers.model_manager import get_model_manager
    _HAS_CUSTOM_MODELS = True
except ImportError:
    _HAS_CUSTOM_MODELS = False


class TextScrubber:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.classification_entities = self._setup_classification_entities()

        self._register_pattern_recognizers()
        self._register_list_recognizers()
        
        # Initialize custom model manager if available
        self.model_manager = get_model_manager() if _HAS_CUSTOM_MODELS else None
        self._register_list_recognizers() 
        self._register_custom_recognizers()

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
            REGEX_RECOGNIZERS_C4 + REGEX_RECOGNIZERS_C3 + REGEX_RECOGNIZERS_C2
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

    def _register_custom_recognizers(self) -> None:
        recognizers = self._distinct_by_entity(
            CUSTOM_RECOGNIZERS_C3 + CUSTOM_RECOGNIZERS_C4
        )

        for rec in recognizers:
            custom_spacy = CustomSpacyRecognizer(
                path_to_model = rec["model_path"],
                supported_entities = [rec["entity"]]
            )

            self.analyzer.registry.add_recognizer(custom_spacy)

    def _setup_classification_entities(self) -> dict[str, List[str]]:
        classification_entities = {}

        c2_rec_list = (

            DEFAULT_RECOGNIZERS_C2
            + REGEX_RECOGNIZERS_C2
            + DENY_LIST_RECOGNIZERS_C2

        )
        classification_entities["C2"] = [rec["entity"] for rec in c2_rec_list]

        c3_rec_list = (

            DEFAULT_RECOGNIZERS_C2
            + REGEX_RECOGNIZERS_C2
            + DENY_LIST_RECOGNIZERS_C2

            + DEFAULT_RECOGNIZERS_C3
            + REGEX_RECOGNIZERS_C3
            + DENY_LIST_RECOGNIZERS_C3
            + CUSTOM_RECOGNIZERS_C3
        

        )
        classification_entities["C3"] = [rec["entity"] for rec in c3_rec_list]

        c4_rec_list = (
                       
            DEFAULT_RECOGNIZERS_C4
            + REGEX_RECOGNIZERS_C4
            + DENY_LIST_RECOGNIZERS_C4
            + DEFAULT_RECOGNIZERS_C3
            + REGEX_RECOGNIZERS_C3
            + DENY_LIST_RECOGNIZERS_C3
    
            + DEFAULT_RECOGNIZERS_C2
            + REGEX_RECOGNIZERS_C2
            + DENY_LIST_RECOGNIZERS_C2

            +CUSTOM_RECOGNIZERS_C3
            +CUSTOM_RECOGNIZERS_C4

        )
        classification_entities["C4"] = [rec["entity"] for rec in c4_rec_list]

        return classification_entities

    def scrub_text(
        self, 
        text: str, 
        target_risk: str = "C4", 
        language: str = "en"
    ) -> dict:
        """
        Scrubs (anonymizes) the input text based on the target risk level and language.
        Returns a dictionary with the anonymized text and a list of detected entities.
        """
        class_entities = self.classification_entities.get(
            target_risk.strip().upper(), []
        )


        # Analyze text to find entities
        analyzer_results = self.analyzer.analyze(
            text=text, entities=class_entities, language=language
        )

        # Create a map from analyzer_results, entity_type to list of results, where list results are sorted first by their start position (lower to higher) and second by score (from higher to lower)
        entity_map = {}
        for res in analyzer_results:
            if res.entity_type not in entity_map:
                entity_map[res.entity_type] = []
            entity_map[res.entity_type].append(res)

        for entity_type in entity_map:
            entity_map[entity_type].sort(key=lambda r: (r.start, -r.score))

        # Update replacements to have suffixes if there are multiple entities of the same type
        for entity_type, results in entity_map.items():
            if len(results) > 1:
                for i, res in enumerate(results):
                    res.replacement = f"<{entity_type}_{i+1}>"
            else:
                results[0].replacement = f"<{entity_type}>"

        # Anonymize text using the analyzer results
        for r in analyzer_results:
            print(
                f"Entity: {r.entity_type:<20} "
                f"Text: '{text[r.start:r.end]}' "
            )

        # Update replacements to have suffixes if there are multiple entities of the same type
        for entity_type, results in entity_map.items():
            if len(results) > 1:
                for i, res in enumerate(results):
                    res.replacement = f"<{entity_type}_{i+1}>"
            else:
                results[0].replacement = f"<{entity_type}>"

        # Anonymize text using the analyzer results
        anonymized_result = self.anonymizer.anonymize(
            text=text, analyzer_results=analyzer_results  # type: ignore
        )

        # Sort anonymized results by their start position
        anonymized_result.items.sort(key=lambda r: r.start)

        # Build list of detected entities with original text and explanation
        # and update replacements with suffixed versions
        scrubbed_text = anonymized_result.text
        entities = []
        offset = 0
        for res in anonymized_result.items:
            explanation = (
                f"{res.entity_type.lower().replace('_', ' ').capitalize()} detected"
            )

            # Find best matching entity in the map for the current result, first by type, then by nearest start position
            best_match = None
            results_per_type = entity_map.get(res.entity_type, [])

            # Look for exact match on start position
            for candidate in results_per_type:
                if candidate.start == res.start:
                    best_match = candidate
                    break

            if not best_match:
                # Find nearest match on start position
                best_match = min(
                    results_per_type, key=lambda r: abs(r.start - res.start)
                )

            # Remove best match from the list to avoid reusing it
            results_per_type.remove(best_match)

            # Extract original text, replacement, and score from best match
            original = text[best_match.start : best_match.end]
            replacement = best_match.replacement
            score = best_match.score

            # Update the replacement in the scrubbed text
            start = res.start + offset
            end = res.end + offset
            scrubbed_text = scrubbed_text[:start] + replacement + scrubbed_text[end:]

            # Adjust start and end positions based on offset
            new_start = start
            new_end = new_start + len(replacement)
            offset += len(replacement) - len(res.text)

            entities.append(
                {
                    "type": res.entity_type,
                    "start": new_start,
                    "end": new_end,
                    "original": original,
                    "replacement": replacement,
                    "explanation": explanation,
                    "score": score,
                }
            )

        return {"scrubbed_text": scrubbed_text, "entities": entities}

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
