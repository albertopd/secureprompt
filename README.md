# SecurePrompt 

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-brightgreen.svg)](https://fastapi.tiangolo.com/) [![Uvicorn](https://img.shields.io/badge/Uvicorn-0.29.0-purple.svg)](https://www.uvicorn.org/) [![PyMongo](https://img.shields.io/badge/PyMongo-4.6.0-orange.svg)](https://pymongo.readthedocs.io/) [![Streamlit](https://img.shields.io/badge/Streamlit-1.33.0-ff4b4b.svg)](https://streamlit.io/)

SecurePrompt is a demonstration application designed for banking environments, showcasing how to build a secure prompt management system using FastAPI, Streamlit and MongoDB. It features advanced text and file scrubbers to automatically redact sensitive financial and personal information before prompts are sent to large language models (LLMs), helping ensure compliance with banking data privacy and security standards.

## ✨ Features

## 📂 Project Structure

## 📋 Requirements

- Python 3.11 or later
- MongoDB instance (local or cloud)
- Required Python packages listed in:
    - [requirements_backend.txt](requirements_backend.txt)
    - [requirements_frontend.txt](requirements_fronten.txt)

## 📦 Installation

### With Docker

```bash
docker-compose up --build
```
### Without Docker

#### MongoDB

- Install MongoDB and ensure it's running locally at: `mongodb://localhost:27017`

#### Backend (API)

- Install backend requirements:
```bash
pip install -r requirements_backend.txt
```

#### Frontend

- Install frontend requirements:
```bash
pip install -r requirements_frontend.txt
```

## ⚙️ Configuration

## 🚀 Usage

### Run locally with Docker

- Use the following URLs:
    - Backend: http://localhost:8000/docs
    - UI: http://localhost:8501

### Run locally without Docker

#### Backend (API)

- Run API:
```bash
cd backend
uvicorn api.main:app --reload
```

- Browse: http://localhost:8000/docs

#### Frontend (UI)

- Run Streamlit app:
```bash
cd frontend
streamlit run scrubber_app.py
```

- Browse: http://localhost:8501

## 📝 Example Output

## 📜 License

## 👤 Collaborators

- [Estefania Sosa](https://github.com/hermstefanny)
- [Floriane Haulot](https://github.com/fhaulot)
- [Preeti Duhan](https://github.com/Preeti9392)
- [Alberto Pérez](https://github.com/albertopd)