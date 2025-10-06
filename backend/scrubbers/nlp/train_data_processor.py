import re
import pandas as pd
import json
import os


def extract_raw_labels(csv_folder: str,  column_with_labels = "Sanitized Prompt", destination_file: str = "backend/scrubbers/nlp/datafiles/raw_labels.json"):
  labels_file = dict()
  for file_name in os.listdir(csv_folder):
      placeholders = set()

      if file_name.endswith(('.csv')):
          csv_path = os.path.join(csv_folder, file_name)
          df = pd.read_csv(csv_path)

      for sanitized_prompt in df[column_with_labels]:
          matches = re.findall(r"<(.*?)>", sanitized_prompt)
          placeholders.update(matches)

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



def parse_pair_from_file(csv_path):
    df = pd.read_csv(csv_path)
    original_text_col = "Original Prompt" if "Original Prompt" in df.columns else "Prompt"
    labeled_text_col = "Sanitized Prompt"
    pairs = list(zip(df[original_text_col], df[labeled_text_col]))
    return pairs

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


def extract_entities_from_template(raw, label):
 
    tokens = re.split(r'(<[A-Z_]+>)', label)
    pointer = 0
    entities = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.startswith('<') and token.endswith('>'):
            label = token[1:-1]
            next_static = tokens[i+1] if i+1 < len(tokens) else ''
            if next_static:
                idx = raw.find(next_static, pointer)
                if idx == -1:
                    idx = raw.find(next_static)
                    if idx == -1:
                        raise ValueError(f"Could not locate static segment '{next_static}' in raw:\n{raw}\nTEMPLATE:\n{template}")
                        
                start = pointer
                end = idx
            else:
                start = pointer
                end = len(raw)
            while start < end and raw[start].isspace():
                start += 1
            while end > start and raw[end-1].isspace():
                end -= 1
            if end > start:

                entities.append((start, end, label))
            pointer = idx if next_static else end
            i += 1
        else:
            static = token
            if static == '':
                i += 1
                continue
            idx = raw.find(static, pointer)
            if idx == -1:
                idx = raw.find(static)
                if idx == -1:
                    raise ValueError(f"Static token not found: '{static}'\nRaw: {raw}\nTemplate: {template}")
            pointer = idx + len(static)
            i += 1
    return entities




if __name__ == "__main__":
    #extract_raw_labels("backend/scrubbers/nlp/datafiles/csv_files")
    #consolidate_labels("backend/scrubbers/nlp/datafiles/raw_labels.json")

    pairs = parse_pair_from_file("backend/scrubbers/nlp/datafiles/csv_files/prompts_13_16_18.csv")

    count = 0
    for raw, template in pairs:
        try:
            entities = extract_entities_from_template(raw, template)
            count += 1
        except ValueError as e:
            print(f"Skipping pair due to error: {e}")
            continue
    print(f"Processed {count} pairs successfully.")