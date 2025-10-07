import random
import re
import pandas as pd
import json
import os

import spacy
from spacy.tokens import DocBin


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
    original_text = raw
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
    return (original_text, {"entities": entities})

def shuffle_data(tagged_data, training_split, seed=42):
    random.shuffle(tagged_data)
    split = int(len(tagged_data)*training_split)
    train_data = tagged_data[:split]
    test_data = tagged_data[split:]
    return train_data, test_data

def save_spacy_data(tagged_data, output_path:str):
    nlp = spacy.blank("en")
    db = DocBin()

    for text, annot in tagged_data:
        doc = nlp.make_doc(text)
        ents = [doc.char_span(start, end, label) for start, end, label in annot["entities"] if doc.char_span(start, end, label)]
        doc.ents = ents
        db.add(doc)

    db.to_disk(output_path)




if __name__ == "__main__":
    #extract_raw_labels("backend/scrubbers/nlp/datafiles/csv_files")
    #consolidate_labels("backend/scrubbers/nlp/datafiles/raw_labels.json")

    # folder_path = '/home/javanegas/estefy/Anonymization/anonymization-presidio/synthetic_DATA/'  

    # files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    # print(files)
    # pairs_total=[]
    # for file in files:
    #     pairs = parse_pair_from_file(file)
    #     pairs_total.extend(pairs)
    
    pairs_total =parse_pair_from_file("/home/javanegas/estefy/Anonymization/anonymization-presidio/synthetic_DATA/c4_sensitive_data_prompts_v2.csv")
    tagged_data_file = []
    count = 0

    for raw, template in pairs_total:
        try:
            entities = extract_entities_from_template(raw, template)
            count += 1
            tagged_data_file.append(entities)
        except ValueError as e:
            print(f"Skipping pair due to error: {e}")
            continue
    print(f"Processed {count} pairs successfully.")

    print(f"Total tagged data samples: {len(tagged_data_file)}")

    with open("./datafiles/tagged_data_v3.json", "w") as f:
        json.dump(tagged_data_file, f, indent=2)


    train, test = shuffle_data(tagged_data_file, training_split=0.8)
    save_spacy_data (train, "./datafiles/train_v3.spacy")
    save_spacy_data (test, "./datafiles/dev_v3.spacy")