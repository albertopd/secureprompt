import sys
import uuid
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, Depends, HTTPException, Header
from api.models import LoginRequest, LLMIngestRequest, LLMQueryRequest
from scrubbers.text_scrubber import TextScrubber
from scrubbers.file_scrubber import FileScrubber
from audit.auditor import Auditor
from database.mongo import get_collection
from database.LLM import LLMSystem
from datetime import datetime
from fastapi.logger import logger

app = FastAPI(title="SecurePrompt API")

SESSIONS = {}
text_scrubber = TextScrubber()
file_scrubber = FileScrubber()
auditor = Auditor()
llm_system = LLMSystem()  # Index automatically built on initialization

# Use the get_collection function to connect to MongoDB
users_col = get_collection("employees")
logs_col = get_collection("logs")

def require_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    if token not in SESSIONS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return SESSIONS[token]

# Update login route to handle MongoDB field names
@app.post("/api/v1/login")
def login(req: LoginRequest):
    logger.info("Received login request for email: %s", req.email)
    # Log the incoming request data
    print(f"Login attempt: email={req.email}, CorpKey={req.CorpKey}")

    # Check user credentials in MongoDB
    user = users_col.find_one({"email": req.email, "CorpKey": req.CorpKey})
    logger.debug("MongoDB query result: %s", user)

    if not user:
        logger.warning("Invalid login attempt for email: %s", req.email)
        # Log failed login attempt
        print(f"Login failed for email={req.email}")
        logs_col.insert_one({
            "email": req.email,
            "action": "login",
            "status": "failure",
            "timestamp": datetime.utcnow()
        })
        raise HTTPException(status_code=401, detail="Invalid credentials")

    print(f"Received email: {req.email}, CorpKey: {req.CorpKey}")
    print(f"Query result: {user}")
    # Generate session token
    token = str(uuid.uuid4())
    SESSIONS[token] = {"email": req.email, "role": user["role"]}

    # Log successful login
    logs_col.insert_one({
        "email": req.email,
        "action": "login",
        "status": "success",
        "timestamp": datetime.utcnow()
    })

    return {
        "token": token,
        "first_name": user["First Name"],
        "last_name": user["Last Name"],
        "role": user["role"]
    }

@app.post("/api/v1/logout")
def logout(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.split(" ", 1)[1]
    if token not in SESSIONS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Log the logout action
    user = SESSIONS.pop(token)
    logs_col.insert_one({
        "e-mail": user.get("email"),
        "action": "logout",
        "status": "success",
        "timestamp": datetime.utcnow()
    })

    return {"message": "Successfully logged out"}

@app.post("/api/v1/llm/test")
def llm_test(req: LLMQueryRequest):
    """
    Simple RAG test endpoint - NO AUTH REQUIRED.
    Just tests: MongoDB → chunks → embeddings → FAISS → retrieval → Gemini answer
    """
    try:
        # Retrieval
        retrieved = llm_system.retrieve(req.question, top_k=max(1, req.top_k or 3))
        
        # Answer generation  
        answer = llm_system.generate_answer(req.question, retrieved)
        
        # Return results with transparency
        retrieved_info = [
            {
                "chunk_index": int(idx),
                "distance": float(dist),
                "source": llm_system.sources.get(int(idx)),
                "security": llm_system.securities.get(int(idx)),
            }
            for idx, dist in retrieved
        ]
        
        return {
            "question": req.question,
            "top_k": req.top_k,
            "retrieved": retrieved_info,
            "answer": answer,
        }
    except Exception as e:
        print(f"LLM test error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM test failed: {str(e)}")
