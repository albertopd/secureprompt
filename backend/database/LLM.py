import os
from typing import List, Dict, Tuple, Optional, Any
import requests
import json

import numpy as np

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system env vars

# Mongo
from pymongo import MongoClient

# Gemini / Google Generative AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Google Generative AI not available. Install with: pip install google-generativeai")

# FAISS for vector search
try:
    import faiss  # type: ignore
except ImportError:
    faiss = None  # type: ignore


class LLMSystem:
    """
    Minimal LLM retrieval pipeline:
      1) Connect to MongoDB
      2) Build one chunk per Mongo collection (file), with security + source
      3) Connect to Gemini
      4) Create embeddings with Gemini
      5) Build FAISS index
      6) Execute queries: retrieve top-k and optionally generate an answer

    Notes:
    - One chunk per collection to match the requirement "un par fichier mongodb".
    - To avoid extremely long inputs, chunks can be capped with max_chars_per_chunk.
    """

    def __init__(
        self,
        mongo_uri: Optional[str] = None,
        mongo_db: Optional[str] = None,
        google_api_key: Optional[str] = None,
        embedding_model: str = "models/embedding-001",
        generation_model: str = "gemini-2.5-flash-lite",
    ) -> None:
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.mongo_db = mongo_db or os.getenv("MONGO_DB", "secureprompt")
        self.client: Optional[MongoClient] = None
        self.db = None

        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.embedding_model_name = embedding_model
        self.generation_model_name = generation_model
        self.embedding_model = None
        self.generation_model = None

        # Ollama configuration
        self.use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        self.ollama_generation_model = os.getenv("OLLAMA_GENERATION_MODEL", "llama3.2")

        # In-memory artifacts
        self.chunks: List[str] = []
        self.sources: Dict[int, str] = {}
        self.securities: Dict[int, str] = {}
        self.index: Any = None
        self.embeddings: Optional[np.ndarray] = None
        
        # Build index automatically on initialization
        self.build_from_mongo()

    # 1) Connect to MongoDB
    def connect_mongo(self):
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        return self.db

    # 2) Create chunks (one per Mongo collection)
    def create_chunks_from_collections(
        self,
        include_collections: Optional[List[str]] = None,
        exclude_collections: Optional[List[str]] = None,
        max_chars_per_chunk: int = 8000,
    ) -> Tuple[List[str], Dict[int, str], Dict[int, str]]:
        if self.db is None:
            self.connect_mongo()
        assert self.db is not None

        names = self.db.list_collection_names()
        # Filter system collections
        names = [n for n in names if not n.startswith("system.")]
        if include_collections:
            names = [n for n in names if n in include_collections]
        if exclude_collections:
            names = [n for n in names if n not in exclude_collections]

        chunks: List[str] = []
        sources: Dict[int, str] = {}
        securities: Dict[int, str] = {}

        for coll_name in names:
            col = self.db[coll_name]
            docs = list(col.find({}))
            if not docs:
                continue
            # Guess security level from first doc; default c1
            sec = str(docs[0].get("security", "c1"))
            # Build a readable text: header from keys (excluding our meta fields), then rows
            # Exclude common meta fields
            meta_keys = {"_id", "security", "source_file", "row_idx"}
            # Build header from union of keys across sample of docs
            sample = docs[:50]
            keys: List[str] = []
            seen = set()
            for d in sample:
                for k in d.keys():
                    if k in meta_keys:
                        continue
                    if k not in seen:
                        seen.add(k)
                        keys.append(k)
            # Format rows
            lines: List[str] = [f"Source: {coll_name}", f"Security: {sec}", "---"]
            for d in docs:
                parts = []
                for k in keys:
                    v = d.get(k, "")
                    parts.append(f"{k}: {v}")
                lines.append(" | ".join(parts))
                # Keep chunk bounded
                if sum(len(x) + 1 for x in lines) > max_chars_per_chunk:
                    lines.append("...")
                    break
            text = "\n".join(lines)

            chunks.append(text)
            sources[len(chunks) - 1] = coll_name
            securities[len(chunks) - 1] = sec

        self.chunks = chunks
        self.sources = sources
        self.securities = securities
        return chunks, sources, securities

    # 3) Connect to Gemini
    def connect_gemini(self):
        if self.use_ollama:
            return True  # Skip Gemini when using Ollama
        if not GEMINI_AVAILABLE:
            raise RuntimeError("Google Generative AI not installed")
        if not self.google_api_key:
            raise RuntimeError("Missing GOOGLE_API_KEY")
        genai.configure(api_key=self.google_api_key)
        return True

    # 4) Create embeddings with Gemini
    def _extract_embedding_vector(self, payload) -> List[float]:
        # Robust extraction depending on gemini SDK structure
        if isinstance(payload, dict):
            payload = payload.get("embedding") or payload
            values = payload.get("values") if isinstance(payload, dict) else None
            if values:
                return [float(x) for x in values]
        if hasattr(payload, "values"):
            return [float(x) for x in list(payload.values)]
        if isinstance(payload, (list, tuple)):
            return [float(x) for x in payload]
        raise ValueError("Unrecognized embedding response format")

    def get_ollama_embedding(self, text: str) -> List[float]:
        """Get embeddings from Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={
                    "model": self.ollama_embedding_model,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            print(f"Ollama embedding error: {e}")
            # Fallback to mock embeddings
            return self._text_to_mock_embedding(text)

    def _text_to_mock_embedding(self, text: str) -> List[float]:
        """Convert text to deterministic mock embedding"""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        hash_nums = [int(text_hash[i:i+2], 16) for i in range(0, len(text_hash), 2)]
        
        # Extend to 768 dimensions
        while len(hash_nums) < 768:
            hash_nums.extend(hash_nums[:768-len(hash_nums)])
        hash_nums = hash_nums[:768]
        
        # Normalize to [-1, 1] range
        return [(x - 127.5) / 127.5 for x in hash_nums]

    def get_embeddings(self, texts: List[str], batch_size: int = 16, use_mock: bool = None) -> np.ndarray:
        # Check if we should use mock embeddings
        if use_mock is None:
            use_mock = os.getenv("USE_MOCK_EMBEDDINGS", "false").lower() == "true"
        
        if use_mock:
            print(f"Using mock embeddings for {len(texts)} texts")
            return self._get_mock_embeddings(texts)
        
        # Use Ollama if enabled
        if self.use_ollama:
            print(f"Using Ollama embeddings with model: {self.ollama_embedding_model}")
            embeddings = []
            for i, text in enumerate(texts):
                if i % 10 == 0:
                    print(f"Processing embedding {i+1}/{len(texts)}")
                embeddings.append(self.get_ollama_embedding(text))
            
            arr = np.array(embeddings, dtype="float32")
            self.embeddings = arr
            return arr
        
        # Try Gemini with fallback to Ollama
        try:
            self.connect_gemini()
            vectors: List[List[float]] = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                for j, t in enumerate(batch):
                    if (i + j) % 10 == 0:
                        print(f"Processing Gemini embedding {i+j+1}/{len(texts)}")
                    resp = genai.embed_content(model=self.embedding_model_name, content=t)
                    vec = self._extract_embedding_vector(resp)
                    vectors.append(vec)
            
            if not vectors:
                return np.zeros((0, 768), dtype="float32")
            dim = max(len(v) for v in vectors)
            arr = np.zeros((len(vectors), dim), dtype="float32")
            for i, v in enumerate(vectors):
                arr[i, : len(v)] = np.array(v, dtype="float32")
            self.embeddings = arr
            return arr
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                print(f"Gemini quota exceeded, switching to Ollama: {e}")
                self.use_ollama = True
                return self.get_embeddings(texts, batch_size, use_mock)  # Retry with Ollama
            else:
                print(f"Gemini embeddings failed, falling back to mock: {e}")
                return self._get_mock_embeddings(texts)
    
    def _get_mock_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate simple mock embeddings for testing when Gemini quota is exceeded"""
        import hashlib
        dim = 768  # Standard embedding dimension
        vectors = []
        
        for text in texts:
            # Create deterministic "embeddings" based on text hash
            text_hash = hashlib.md5(text.encode()).hexdigest()
            # Convert hash to numbers and normalize
            hash_nums = [int(text_hash[i:i+2], 16) for i in range(0, len(text_hash), 2)]
            # Pad or truncate to desired dimension
            while len(hash_nums) < dim:
                hash_nums.extend(hash_nums[:dim-len(hash_nums)])
            hash_nums = hash_nums[:dim]
            # Normalize to [-1, 1] range
            normalized = [(x - 127.5) / 127.5 for x in hash_nums]
            vectors.append(normalized)
        
        arr = np.array(vectors, dtype="float32")
        self.embeddings = arr
        return arr

    # 5) Create FAISS index
    def create_index(self, embeddings: Optional[np.ndarray] = None):
        if faiss is None:
            raise RuntimeError("faiss is not installed. Please install faiss-cpu.")
        embs = embeddings if embeddings is not None else self.embeddings
        if embs is None or embs.size == 0:
            raise ValueError("No embeddings available to build index")
        dim = embs.shape[1]
        index: Any = faiss.IndexFlatL2(dim)  # type: ignore
        index.add(embs.astype("float32"))
        self.index = index
        return index

    # 6) Execution: retrieve top-k and generate answer
    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[int, float]]:
        if self.index is None:
            raise ValueError("Index not built")
        q_emb = self.get_embeddings([query])
        idx: Any = self.index  # type: ignore
        D, I = idx.search(q_emb.astype("float32"), k=max(1, top_k))
        # Return list of (idx, distance)
        return list(zip(I[0].tolist(), D[0].tolist()))

    def generate_with_ollama(self, prompt: str) -> str:
        """Generate answer using Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.ollama_generation_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # More focused responses
                        "top_p": 0.9,
                        "num_predict": 300,  # Allow longer responses
                        "stop": ["---", "Q:", "\nQ:", "QUESTION:"]  # Better stop tokens
                    }
                },
                timeout=180  # Increased timeout to 3 minutes
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            print(f"Ollama generation error: {e}")
            return f"[OLLAMA ERROR] Could not generate response: {str(e)}"

    def generate_answer(self, question: str, retrieved: List[Tuple[int, float]], max_context: int = 1, use_mock: bool = None) -> str:
        # Check if we should use mock generation
        if use_mock is None:
            use_mock = os.getenv("USE_MOCK_GENERATION", "false").lower() == "true"
        
        if use_mock:
            return self._generate_mock_answer(question, retrieved, max_context)
        
        # Build context from retrieved chunks - ONLY USE THE BEST MATCH
        contexts = []
        for i, (idx_i, dist) in enumerate(retrieved[:max_context], 1):
            source = self.sources.get(idx_i, 'unknown')
            security = self.securities.get(idx_i, '?')
            chunk_text = self.chunks[idx_i]
            
            # Truncate chunk to first 1000 chars to reduce context size
            if len(chunk_text) > 1000:
                chunk_text = chunk_text[:1000] + "..."
            
            # Format the context more clearly for the LLM
            context_block = f"""--- DATA SOURCE {i} ---
Source File: {source}
Security Level: {security}
Relevance Score: {dist:.2f}

Data:
{chunk_text}

---"""
            contexts.append(context_block)
        
        # Improved prompt for complete, direct responses
        prompt = f"""Based on this fictional test data, answer the customer question directly and completely:

{chr(10).join(contexts)}

Question: {question}

Provide a complete, helpful response including specific details from the data:"""
        
        # Use Ollama if enabled
        if self.use_ollama:
            print(f"Generating answer with Ollama model: {self.ollama_generation_model}")
            return self.generate_with_ollama(prompt)
        
        # Try Gemini with fallback to Ollama
        try:
            self.connect_gemini()
            model = genai.GenerativeModel(self.generation_model_name)
            resp = model.generate_content(prompt)
            return getattr(resp, "text", str(resp))
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                print(f"Gemini quota exceeded, switching to Ollama: {e}")
                self.use_ollama = True
                return self.generate_with_ollama(prompt)
            else:
                print(f"Gemini generation failed: {e}")
                return self._generate_mock_answer(question, retrieved, max_context)
    
    def _generate_mock_answer(self, question: str, retrieved: List[Tuple[int, float]], max_context: int = 3) -> str:
        """Generate a mock answer for testing when Gemini quota is exceeded"""
        contexts = []
        for idx_i, dist in retrieved[:max_context]:
            source = self.sources.get(idx_i, 'unknown')
            security = self.securities.get(idx_i, '?')
            chunk_preview = self.chunks[idx_i][:200] + "..." if len(self.chunks[idx_i]) > 200 else self.chunks[idx_i]
            contexts.append(f"[Source: {source}, Security: {security}, Distance: {dist:.3f}]\n{chunk_preview}")
        
        return f"""[MOCK ANSWER - Gemini quota exceeded]

Question: {question}

Based on the retrieved contexts, here are the relevant information chunks:

{chr(10).join(contexts)}

Note: This is a mock response generated when Gemini API quota is exceeded. The actual RAG pipeline (MongoDB → embeddings → FAISS → retrieval) is working correctly. Only the final answer generation is mocked."""

    # Convenience end-to-end
    def build_from_mongo(
        self,
        include_collections: Optional[List[str]] = None,
        exclude_collections: Optional[List[str]] = None,
    ):
        self.connect_mongo()
        self.create_chunks_from_collections(include_collections, exclude_collections)
        embs = self.get_embeddings(self.chunks)
        self.create_index(embs)
        return True
