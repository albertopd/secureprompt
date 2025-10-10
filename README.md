# SecurePrompt 

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-brightgreen.svg)](https://fastapi.tiangolo.com/) [![Uvicorn](https://img.shields.io/badge/Uvicorn-0.29.0-purple.svg)](https://www.uvicorn.org/) [![PyMongo](https://img.shields.io/badge/PyMongo-4.6.0-orange.svg)](https://pymongo.readthedocs.io/) [![Streamlit](https://img.shields.io/badge/Streamlit-1.33.0-ff4b4b.svg)](https://streamlit.io/)

SecurePrompt is a comprehensive data protection system designed for banking environments, showcasing an end-to-end secure prompt management architecture. Built with FastAPI, Streamlit, and MongoDB, it implements a sophisticated multi-tier architecture with advanced text and file scrubbing capabilities.

The system features specialized AI models for financial data detection, achieving exceptional performance scores of 99.7% for customer data (C3) and 90.7% for sensitive financial data (C4). A comprehensive security-aware testing framework validates the system across 906 test scenarios with an overall security score of 73.2%, prioritizing data protection over traditional accuracy metrics.

Key innovations include Presidio-based entity detection with custom spaCy models, multi-format file processing (PDF, screenshots), and a "better safe than sorry" approach that rewards over-detection to prevent data leaks. The system automatically redacts sensitive financial and personal information before prompts are sent to large language models (LLMs), ensuring compliance with banking data privacy and security standards while enabling secure AI interactions.

## ✨ Features

### 🏗️ Multi-Tier Architecture
- **Data Tier**: MongoDB with UserManager, FileManager, and LogManager interfaces
- **Logic Tier**: SecurePrompt API with organized endpoint groups
- **Presentation Tier**: POC Streamlit application for testing functionality

### 🛡️ Advanced Text Scrubbing
- **Presidio Integration**: Enterprise-grade entity detection and anonymization
- **Security Level Classification**: C1 (Public), C2 (Internal), C3 (Customer Data), C4 (Sensitive Financial Data)
- **Custom NLP Models**: Specialized spaCy models for C3/C4 levels achieving 99.7% performance
- **Regex & Model-Based Entities**: Combined approach for comprehensive detection
- **Over-Detection Strategy**: "Better safe than sorry" approach with 90% score for cautious detection

### 📁 File Processing Capabilities
- **PDF Scrubbing**: Text extraction and anonymization with format preservation
- **Screenshot Analysis**: OCR-based detection using OpenCV and Pytesseract
- **Multi-Format Support**: Various document types commonly used in banking

### 🚀 RESTful API Endpoints
- **Health**: `/health/live`, `/health/ready`
- **Authentication**: `/auth/login`, `/auth/logout`
- **Text Processing**: `/text/scrub`, `/text/descrub`
- **File Processing**: `/file/scrub`, `/file/descrub`, `/file/download`
- **Auditing**: `/audit/logs`, `/audit/search`, `/audit/stats`

### 📊 Security-Aware Testing Framework
- **906 New Test Prompts**: Comprehensive scenarios across all security levels
- **Security Score: 73.2%**: Overall protection effectiveness prioritizing data safety
- **Performance by Level**: C3 (99.7%), C4 (90.7%), C2 (66.0%), C1 (36.3%)
- **Detection Analysis**: 49.2% perfect, 26.7% over-detection (positive), 24.2% under-detection

## 📂 Project Structure

```
secureprompt/
├── backend/                          # Logic Tier - SecurePrompt API
│   ├── api/                         # API Layer
│   │   ├── main.py                  # FastAPI application entry point
│   │   ├── models.py                # Pydantic data models
│   │   ├── rbac.py                  # Role-Based Access Control
│   │   ├── dependencies.py          # Dependency injection
│   │   └── routers/                 # API endpoint routers
│   │       ├── authentication.py   # /auth/* endpoints
│   │       ├── text_scrubbing.py   # /text/* endpoints
│   │       ├── file_scrubbing.py   # /file/* endpoints
│   │       ├── audit.py            # /audit/* endpoints
│   │       └── system.py           # /health/* endpoints
│   ├── scrubbers/                   # Core Scrubbing Engine
│   │   ├── text_scrubber.py        # Main text processing logic
│   │   ├── file_scrubber.py        # PDF processing capabilities
│   │   ├── screenshot_scrub.py     # Image/OCR processing
│   │   ├── recognizers.py          # Custom entity recognizers
│   │   ├── custom_spacy_recognizer.py # Estefania's custom model integration
│   │   └── models/                 # Custom spaCy models (excluded from repo)
│   │       ├── models_c3/          # Customer data models
│   │       └── models_c4/          # Sensitive financial data models
│   ├── database/                   # Data Tier Interfaces
│   │   ├── connection.py           # MongoDB connection management
│   │   ├── user_manager.py         # User operations
│   │   ├── log_manager.py          # Audit logging
│   │   └── log_record.py           # Log data models
│   ├── tests/                      # Testing Framework
│   │   ├── test_text_scrubber.py   # Core functionality tests
│   │   ├── test_text_scrubber_report.py # Performance reporting
│   │   ├── data/prompts/           # 906 test cases across security levels
│   │   └── helpers/excel_loader.py # Test data utilities
│   └── test_security_aware_metrics.py # Security performance analysis (73.2% score)
├── frontend/                       # Presentation Tier - POC Application
│   ├── app.py                      # Main Streamlit interface
│   ├── text_scrubber.py           # Text processing UI
│   ├── file_scrubber.py           # File upload and processing UI
│   ├── utils.py                   # UI utilities
│   └── style.css                  # Custom styling
├── docker-compose.yml             # Container orchestration
├── Dockerfile.backend             # Backend service container
├── Dockerfile.frontend            # Frontend service container
└── requirements_*.txt             # Python dependencies
```

## 📋 Requirements

- Python 3.11 or later
- MongoDB instance (local or in docker)
- Required Python packages listed in:
    - [requirements_backend.txt](requirements_backend.txt)
    - [requirements_frontend.txt](requirements_frontend.txt)

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

### Custom Models Setup

The system uses specialized spaCy models for enhanced financial data detection:

#### 📥 Model Installation
Custom models are hosted externally due to size constraints:

- **C3 Model**: [Download here](https://drive.google.com/file/d/1yFl0jBxb3wynQ851yZGpP3ysjl230Wik/view?usp=drive_link)
- **C4 Model**: [Download here](https://drive.google.com/file/d/1RtNWZmFGTEQhW5__MnkzQ458eJn2wzEE/view?usp=drive_link)

Models should be placed in:
```
backend/scrubbers/nlp/
├── models_c3/    # Customer data model
└── models_c4/    # Sensitive financial data model
```

### Environment Variables
```bash
MONGODB_URI=mongodb://localhost:27017
SECRET_KEY=your-secret-key
API_HOST=0.0.0.0
API_PORT=8000
```

## 🚀 Usage

### Run locally with Docker

- Use the following URLs:
    - Backend API: http://localhost:8000/docs
    - Frontend UI: http://localhost:8501

### Run locally without Docker

#### Backend (API)

- Run API:
```bash
cd backend
uvicorn api.main:app --reload
```

- Browse API documentation: http://localhost:8000/docs

#### Frontend (UI)

- Run Streamlit app:
```bash
cd frontend
streamlit run app.py
```

- Browse application: http://localhost:8501

## 🧪 Testing & Performance

### Security-Aware Metrics

Run the comprehensive testing framework:

```bash
cd backend
python test_security_aware_metrics.py
```

#### Performance Results (Based on 906 Test Cases)
```
SECURITY-AWARE PERFORMANCE ANALYSIS
====================================
Overall Security Score: 73.2%
Structural Accuracy: 35.0%

BY SECURITY LEVEL:
• C1 (Public Data): 36.3%
• C2 (Internal Operations): 66.0%  
• C3 (Customer Data): 99.7% ⭐
• C4 (Sensitive Data): 90.7% ⭐

SECURITY BREAKDOWN:
• Perfect Detection: 49.2% (exact matches)
• Good Over-Detection: 26.7% (better safe than sorry)
• Under-Detection: 24.2% (needs improvement)
```

### Testing Philosophy
- **Security-First Approach**: Over-detection gets 90% score (better to be cautious)
- **Perfect Detection**: 100% score for exact matches
- **Under-Detection**: Penalty score (security risk)

### Test Data Validation
- **906 New Prompts**: Comprehensive scenarios across all security levels
- **Data Normalization**: Achieved 99.7% consistency from original 43.3%
- **Real-World Patterns**: Based on actual banking communication scenarios

## 🛡️ Scrubbing Strategy

### Presidio-Based Detection Engine

The system uses a sophisticated entity detection pipeline:

#### Detection Components
1. **Default Entities**: Standard PII patterns (names, emails, phones)
2. **Regex Entities**: Custom patterns for financial data (cards, PINs, CVVs)
3. **Model-Based Entities**: Estefania's specialized spaCy models
4. **Blacklist Entities**: Context-specific exclusions

#### Processing Pipeline
```
Text Input → Analyzer Engine → Entity Detection → Anonymizer Engine → Scrubbed Output
                    ↓
            [Default, Regex, Model-based, Blacklist entities]
                    ↓
            [entity_type, start, end, score] → [text, anonymization_items]
                    ↓
            Text Post-Processor → Final scrubbed_text + metadata
```

#### Security Level Entity Mapping
- **C1 (Public)**: Minimal redaction needed
- **C2 (Internal)**: Employee IDs, internal references
- **C3 (Customer Data)**: Names, emails, addresses, customer IDs (99.7% accuracy)
- **C4 (Sensitive Financial)**: Credit cards, CVVs, PINs, account numbers (90.7% accuracy)

### NLP Model Training

#### Custom Model Development
- **Data Sources**: CSV data, synthetic data generation, LLM-generated templates
- **Processing**: Data processor converts to DocBin format
- **Training Files**: train.spacy, dev.spacy with config.cfg
- **Architecture**: tok2vec >> ner pipeline
- **Optimization**: Iterative improvement based on banking scenarios

### File Processing Capabilities

#### PDF Scrubbing
- **Core Library**: anonympy.pdf.pdfAnonymizer for text blurring/redacting
- **OCR Integration**: pytesseract + pdf2image for image-based PDFs
- **Pattern Matching**: Regex detection of sensitive entities
- **Audit Logging**: JSON-structured processing logs with timestamps

#### Screenshot Analysis
- **OCR Engine**: OpenCV + Pytesseract for text extraction
- **Presidio Integration**: Entity detection on extracted text
- **Visual Redaction**: Coordinate-based masking of sensitive areas

## 🚨 Debugging

To debug the application in Visual Studio Code, follow these instructions:

**1. Create (or update) a .vscode/launch.json in your project root:**
- Create a `.vscode` folder in the root directory of the project if it doesn't already exist.
- Inside the `.vscode` folder, create a file named `launch.json`.
- Add the following configuration to `launch.json`:

``` json
{
    "configurations": [
        {
            "name": "FastAPI",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "api.main:app",
                "--reload"
            ],
            "cwd": "${workspaceFolder}/backend",
            "console": "integratedTerminal"
        },
        {
            "name": "Streamlit",
            "type": "debugpy",
            "request": "launch",
            "module": "streamlit",
            "args": [
                "run",
                "app.py"
            ],
            "cwd": "${workspaceFolder}/frontend",
            "console": "integratedTerminal"
        }
    ]
}
```
**2. Start Debugging:**
- Go to the `Run and Debug` panel in VS Code (Ctrl+Shift+D).
- Select the desired configuration ("FastAPI" or "Streamlit") from the dropdown at the top.
- Click the green play button or press F5 to start debugging.

## 🧪 Unit Testing

The project includes comprehensive unit tests for the scrubber component to ensure functionality and reliability.
It uses `pytest` for testing and `pandas` for handling test data stored in csv files under `backend/tests/data/prompts`.

### Running Tests

Run tests with security-focused performance reporting:

```bash
cd backend
pytest -vv tests/test_security_aware_metrics.py
```

Test reports are generated automatically and saved in the `backend/tests/data/reports` directory. These reports include detailed information about test failures and successes.

## 🚀 Next Steps

Based on team development roadmap:

### 🔬 Model Improvements
- **Expand NLP Models**: Enhance custom models with additional training data
- **Entity Coverage**: Add support for new financial entities and patterns
- **Model Optimization**: Improve processing speed and accuracy

### 📁 File Processing Enhancement
- **Format Expansion**: Support for more document types (Word, Excel, PowerPoint)
- **Advanced OCR**: Improved screenshot and image processing capabilities
- **File De-scrubbing**: Implement reverse anonymization for authorized users

### 📊 Monitoring & Analytics
- **Metrics Dashboard**: Real-time performance monitoring interface
- **Audit Improvements**: Enhanced logging and compliance reporting
- **Performance Analytics**: Detailed insights into scrubbing effectiveness

### 🔐 Security & Integration
- **LLM Connection**: Direct integration with language models
- **Advanced Authentication**: Enhanced login and security access controls
- **Compliance Features**: Additional regulatory compliance tools

### � Testing & Quality
- **Prompt Testing**: Expanded test scenarios and validation
- **Performance Benchmarking**: Continuous improvement metrics
- **Integration Testing**: End-to-end workflow validation

## 👤 Collaborators

- [Estefania Sosa](https://github.com/hermstefanny)
- [Floriane Haulot](https://github.com/fhaulot)
- [Preeti Duhan](https://github.com/Preeti9392)
- [Alberto Pérez](https://github.com/albertopd)
