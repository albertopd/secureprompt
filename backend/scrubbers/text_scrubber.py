import re
from scrubbers.recognizers import RECOGNIZERS


class TextScrubber:
    def __init__(self):
        # compile patterns
        self.recognizers = []
        for r in RECOGNIZERS:
            pattern = re.compile(r['pattern'], flags=re.IGNORECASE)
            self.recognizers.append({**r, "compiled": pattern})

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
