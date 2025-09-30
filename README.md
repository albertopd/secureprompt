# SecurePrompt (Restructured)

Project structure:
- api: FastAPI endpoints and models
- app: Streamlit UI
- audit: Audit logging
- scrubbers: Text and file scrubbers
- database: Mongo integration

## Run locally with Docker
```bash
docker-compose up --build
```
- Backend: http://localhost:8000
- UI: http://localhost:8501
- MongoDB: http://localhost:27017
