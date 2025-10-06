import os, time

from scrubbers.text_scrubber import TextScrubber

class FileScrubber:
    def __init__(self):
        self.text_scrubber = TextScrubber()
        self.out_dir = os.environ.get("FILES_OUT", "/tmp/secureprompt_files")
        os.makedirs(self.out_dir, exist_ok=True)

    def scrub_file(self, filename: str, data: bytes):
        ts = int(time.time())
        redacted_filename = f"{ts}_{filename}"
        redacted_path = os.path.join(self.out_dir, f"redacted_{redacted_filename}")

        # make case depending on file type - for demo, just txt files
        if filename.lower().endswith(".txt"):
            text = data.decode("utf-8", errors="ignore")
            # Here you would call your TextScrubber to process the text
            scrub_result = self.text_scrubber.anonymize_text(text)
            with open(redacted_path, "w", encoding="utf-8") as f:
                f.write(scrub_result["redacted_text"])

        return {
            "entities": scrub_result.get("entities", []),
            "filename": filename,
            "download_url": f"/file/download/{redacted_filename}"
        }
