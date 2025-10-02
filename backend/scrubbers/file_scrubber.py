import os, time

class FileScrubber:
    def __init__(self):
        self.out_dir = os.environ.get("FILES_OUT", "/tmp/secureprompt_files")
        os.makedirs(self.out_dir, exist_ok=True)

    def scrub_file(self, filename: str, data: bytes):
        ts = int(time.time())
        redacted_filename = f"{ts}_{filename}"
        redacted_path = os.path.join(self.out_dir, f"redacted_{redacted_filename}")

        # For demo: just write placeholder redacted file
        with open(redacted_path, "w") as f:
            f.write("[REDACTED FILE CONTENT - demo]")

        return {
            "entities": [
                {
                    "span": "+324985715",
                    "type": "PHONE_BE",
                    "replacement": "<PHONE_BE_1>",
                    "source": "regex",
                    "score": 0.9,
                    "start": 0,
                    "end": 10,
                    "explanation": "Detected by regex"
                }
            ],
            "filename": filename,
            "download_url": f"file/download/{redacted_filename}"
        }
