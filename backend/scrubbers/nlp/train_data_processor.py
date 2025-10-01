import re
import pandas as pd
import json
import os


def extract_raw_labels(csv_folder: str, destination_file: str = "backend/scrubbers/nlp/datafiles/raw_labels.json"):
  labels_file = dict()
  for file_name in os.listdir(csv_folder):
      placeholders = set()

      if file_name.endswith(('.csv')):
          csv_path = os.path.join(csv_folder, file_name)
          df = pd.read_csv(csv_path)

      for sanitized_prompt in df["Sanitized Prompt"]:
          matches = re.findall(r"<(.*?)>", sanitized_prompt)
          placeholders.update(matches)

          print(placeholders)

      labels_file[file_name] = list(placeholders)


  with open(destination_file, "w") as f:
      json.dump(labels_file, f, indent=2)

def map_labels(origin_file):
    mapped_labels = dict()
    with open(origin_file, "r") as f:
        raw_labels = json.load(f)

    for label_list in raw_labels.values():
        for label in label_list:
            generalized = generalize_label(label)
            print(f"Label: {label} -> Generalized: {generalized}")
            mapped_labels[label] = generalized

    with open("backend/scrubbers/nlp/datafiles/mapped_labels.json", "w") as f:
        json.dump(mapped_labels, f, indent=2)



def parse_pair_from_file(path):
    # read file and try both formats (tab-separated or two lines)
    txt = open(path, encoding="utf8").read().strip()
    if '\t' in txt:
        raw, template = txt.split('\t', 1)
    else:
        lines = [l for l in txt.splitlines() if l.strip()]
        if len(lines) >= 2:
            raw, template = lines[0], lines[1]
        else:
            raise ValueError(f"Can't parse {path}. Expect raw and template.")
    return raw.strip(), template.strip()


def generalize_label(label):
    label = label.rstrip("_")

    upper = label.upper()
    name_keywords = ["CUSTOMER", "EMP", "LAST", "FIRST", "EXAMPLE", "PAYER"]
    if any(word in upper for word in name_keywords) and "NAME" in upper:
        return "NAME"

    if "EMP" in upper and ("FIRST" in upper or "LAST" in upper):
        return "NAME"
    
    if "ADDRESS" in upper:
        return "ADDRESS"
    
    if "LINK" in upper or "URL" in upper:
        return "LINK"
      
    if "EMAIL" in upper:
        return "EMAIL"
    if "PHONE" in upper:
        return "PHONE"
    
    if "IBAN" in upper:
        return "IBAN"

    if "DATE" in upper:
        return "DATE"

    if "_" in label:
        main, suffix = label.rsplit("_", 1)
        if len(suffix) == 1:
            return main
    return label






if __name__ == "__main__":
    #extract_raw_labels("backend/scrubbers/nlp/datafiles/csv_files")
    #consolidate_labels("backend/scrubbers/nlp/datafiles/raw_labels.json")