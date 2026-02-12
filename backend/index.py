import os
import sys
import logging
from typing import List
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# Add backend directory to path so "from app.*" resolves to backend/app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import AuthRequest, AuthResponse, QueryRequest, QueryResponse, HealthResponse, UploadResponse
from app.database import initialize_database, is_database_empty, get_document_count, clear_all_embeddings
from app.rag_chain import query_rag, get_embedding
from app.auth import verify_password, create_token, get_current_token
from app.vector_store import store_embeddings

# Note: document_processor is lazy-imported in upload_files() to avoid loading
# heavy dependencies (langchain, tiktoken) on Vercel serverless startup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Showcase Agent API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database."""
    try:
        initialize_database()
        logger.info("Database initialized")

        doc_count = get_document_count()
        if doc_count > 0:
            logger.info(f"Database contains {doc_count} document chunks")
        else:
            logger.info("Database is empty - waiting for file uploads")
    except Exception as e:
        logger.error(f"Error during startup: {e}")


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        from app.database import get_db_connection
        conn = get_db_connection()
        conn.close()
        database_connected = True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        database_connected = False

    documents_loaded = not is_database_empty()

    return HealthResponse(
        status="healthy" if database_connected else "unhealthy",
        database_connected=database_connected,
        documents_loaded=documents_loaded
    )


@app.post("/api/auth", response_model=AuthResponse)
@app.post("/auth", response_model=AuthResponse)
async def auth(request: AuthRequest):
    """Verify password and return JWT."""
    if not verify_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    return AuthResponse(token=create_token())


@app.post("/api/upload", response_model=UploadResponse)
@app.post("/upload", response_model=UploadResponse)
async def upload_files(files: List[UploadFile] = File(...), _: str = Depends(get_current_token)):
    """
    Upload files, clear existing embeddings, and process the new files.
    Accepts PDF and Word documents (.pdf, .docx, .doc).
    """
    # Lazy import to avoid loading heavy dependencies on serverless startup
    from app.document_processor import process_uploaded_file
    
    try:
        # Validate file types
        supported_extensions = {'.pdf', '.docx', '.doc'}
        filenames = []
        
        for file in files:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in supported_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file.filename}. Supported types: PDF, DOCX, DOC"
                )
            filenames.append(file.filename)
        
        logger.info(f"Received {len(files)} files for upload: {filenames}")
        
        # Clear existing embeddings
        deleted_count = clear_all_embeddings()
        logger.info(f"Cleared {deleted_count} existing embeddings")
        
        # Process each uploaded file
        all_chunks = []
        files_processed = 0
        
        for file in files:
            file_bytes = await file.read()
            chunks = process_uploaded_file(file_bytes, file.filename)
            all_chunks.extend(chunks)
            files_processed += 1
            logger.info(f"Processed file {file.filename}: {len(chunks)} chunks")
        
        if not all_chunks:
            return UploadResponse(
                message="Files uploaded but no text content found",
                files_processed=files_processed,
                chunks_processed=0,
                filenames=filenames
            )
        
        # Generate embeddings for all chunks
        logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
        embeddings = []
        for i, chunk in enumerate(all_chunks):
            if (i + 1) % 10 == 0:
                logger.info(f"Embedding progress: {i + 1}/{len(all_chunks)}")
            embedding = get_embedding(chunk['text'])
            embeddings.append(embedding)
        
        # Store embeddings in database
        logger.info("Storing embeddings in database...")
        store_embeddings(all_chunks, embeddings)
        
        return UploadResponse(
            message="Files uploaded and processed successfully",
            files_processed=files_processed,
            chunks_processed=len(all_chunks),
            filenames=filenames
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents")
@app.delete("/documents")
async def delete_documents(_: str = Depends(get_current_token)):
    """Delete all documents from the vector database."""
    try:
        deleted_count = clear_all_embeddings()
        return {"message": f"Deleted {deleted_count} document chunks"}
    except Exception as e:
        logger.error(f"Error deleting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _handle_query(request: QueryRequest):
    """Shared query logic for /api/query and /query."""
    prev = None
    if request.previous_messages:
        prev = [{"query": m.query, "answer": m.answer} for m in request.previous_messages]
    result = query_rag(request.query, top_k=request.top_k, previous_messages=prev)
    return QueryResponse(
        answer=result['answer'],
        sources=result['sources']
    )


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest, _: str = Depends(get_current_token)):
    """Query the RAG system (protected)."""
    try:
        return _handle_query(request)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_local(request: QueryRequest, _: str = Depends(get_current_token)):
    """Query endpoint for local dev when proxy strips /api prefix."""
    try:
        return _handle_query(request)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
