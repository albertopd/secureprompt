import os
import requests
import zipfile


MODEL_INFO = {
    "C4": {
        "url": "https://drive.google.com/file/d/1RtNWZmFGTEQhW5__MnkzQ458eJn2wzEE/view?usp=drive_link",
        "target_path": os.path.join("backend", "scrubbers", "nlp"),
    },
    "C3": {
        "url": "https://drive.google.com/file/d/1yFl0jBxb3wynQ851yZGpP3ysjl230Wik/view?usp=drive_link",
        "target_path": os.path.join("backend", "scrubbers", "nlp"),
    },
}

def download_and_extract(url, target_path):
    os.makedirs(target_path, exist_ok=True)
    zip_path = os.path.join(target_path, "temp.zip")

    print(f"Downloading {url} ...")
    r = requests.get(url, stream=True)
    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print(f"Extracting to {target_path} ...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(target_path)
    os.remove(zip_path)
    print("Done.")

if __name__ == "__main__":
    for level, info in MODEL_INFO.items():
        download_and_extract(info["url"], info["target_path"])