import os, time

from core.config import settings
from scrubbers.text_scrubber import TextScrubber


class FileScrubber:
    def __init__(self):
        self.text_scrubber = TextScrubber()
        self.out_dir = settings.TMP_FILES_PATH
        os.makedirs(self.out_dir, exist_ok=True)

    def scrub_file(
        self, 
        filename: str, 
        data: bytes,
        target_risk: str = "C4", 
        language: str = "en"
    ):
        ts = int(time.time())
        output_filename = f"{ts}_scrubbed_{filename}"
        output_path = os.path.join(self.out_dir, f"{output_filename}")
        file_extension = os.path.splitext(filename)[1].lower()

        # TODO: Add support for more file types (e.g., .docx, .pdf, .xlsx)
        match file_extension:
            case ".txt":
                scrub_result = self._scrub_text_file(data, target_risk, language, output_path)
            case _:
                raise ValueError("Unsupported file type")

        return {
            "file_id": str(ts),
            "output_filename": output_filename,
            "entities": scrub_result.get("entities", [])
        }

    def _scrub_text_file(
        self, 
        data, 
        target_risk, 
        language, 
        output_path
    ):
        text = data.decode("utf-8", errors="ignore")
        scrub_result = self.text_scrubber.scrub_text(text, target_risk, language)
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(scrub_result["scrubbed_text"])
        return scrub_result
