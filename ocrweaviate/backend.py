"""
PDF Policy Query System - Weaviate v4 Compatible
"""

import os
import re
import tempfile
import logging
from typing import List, Dict, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import weaviate
import weaviate.classes as wvc
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Google Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# Initialize Weaviate client (v4 API)
client = None
try:
    client = weaviate.connect_to_local(
        host="localhost",
        port=8080,
        grpc_port=50051
    )
    logger.info("✅ Connected to Weaviate v4")
    
    # Setup schema immediately
    try:
        # Delete existing collection if it exists
        try:
            client.collections.delete("PolicyDocument")
        except:
            pass
        
        # Create collection with v4 API
        client.collections.create(
            name="PolicyDocument",
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_transformers(),
            properties=[
                wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="source", data_type=wvc.config.DataType.TEXT)
            ]
        )
        logger.info("✅ Schema created with v4 API")
    except Exception as e:
        logger.error(f"Schema error: {e}")

except Exception as e:
    logger.error(f"❌ Weaviate connection failed: {e}")
    # Fallback to REST-only connection
    try:
        client = weaviate.connect_to_local(
            host="localhost", 
            port=8080,
            skip_init_checks=True
        )
        logger.info("✅ Connected to Weaviate (REST-only)")
    except Exception as e2:
        logger.error(f"❌ Fallback connection also failed: {e2}")
        client = None

# FastAPI App
app = FastAPI(title="PDF Policy Query System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    explanation: str
    sources: Optional[List[str]] = None
    cross_document_analysis: Optional[str] = None

class DocumentInfo(BaseModel):
    filename: str
    chunks_created: int
    text_length: int

class MultiUploadResponse(BaseModel):
    message: str
    documents: List[DocumentInfo]
    total_documents: int

@app.get("/")
async def root():
    return {
        "message": "PDF Policy Query System",
        "status": "running",
        "weaviate": "connected" if client else "disconnected"
    }

@app.post("/test-upload")
async def test_upload(files: List[UploadFile] = File(...)):
    """Test endpoint to debug file upload issues"""
    logger.info(f"TEST: Received {len(files)} files")
    result = []
    for i, file in enumerate(files):
        logger.info(f"TEST File {i}: {file.filename}, content_type: {file.content_type}")
        content = await file.read()
        result.append({
            "index": i,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content)
        })
    return {"received_files": result}

async def process_single_pdf(file: UploadFile) -> DocumentInfo:
    """Process a single PDF file"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail=f"Only PDF files supported: {file.filename}")
    
    logger.info(f"📄 Processing {file.filename}")
    
    # Read file
    content = await file.read()
    
    # Extract text from PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name
    
    text = ""
    try:
        pdf = PdfReader(temp_path)
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
    finally:
        os.unlink(temp_path)
    
    if not text.strip():
        raise HTTPException(status_code=400, detail=f"No text found in PDF: {file.filename}")
    
    # Clean text
    text = re.sub(r'\s+', ' ', text.strip())
    text = re.sub(r'\bpage\s*\d+\b', '', text, flags=re.IGNORECASE)
    
    # Create chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len
    )
    chunks = splitter.split_text(text)
    chunks = [chunk.strip() for chunk in chunks if len(chunk.strip()) > 30]
    
    if not chunks:
        raise HTTPException(status_code=400, detail=f"Could not create chunks for: {file.filename}")
    
    # Store in Weaviate using v4 API
    collection = client.collections.get("PolicyDocument")
    stored = 0
    
    for chunk in chunks:
        try:
            collection.data.insert({
                "content": chunk,
                "source": file.filename
            })
            stored += 1
        except Exception as e:
            logger.error(f"Storage error for chunk: {e}")
    
    if stored == 0:
        raise HTTPException(status_code=500, detail=f"Failed to store any chunks for: {file.filename}")
    
    logger.info(f"✅ Stored {stored} chunks from {file.filename}")
    return DocumentInfo(
        filename=file.filename,
        chunks_created=stored,
        text_length=len(text)
    )

@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process up to 3 PDFs"""
    if not client:
        raise HTTPException(status_code=500, detail="Database not available")
    
    logger.info(f"Received {len(files)} files for upload")
    for i, file in enumerate(files):
        logger.info(f"File {i}: {file.filename}, content_type: {file.content_type}")
    
    if len(files) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 PDF files allowed")
    
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="At least 1 PDF file required")
    
    try:
        processed_docs = []
        
        for file in files:
            doc_info = await process_single_pdf(file)
            processed_docs.append(doc_info)
        
        return {
            "message": f"Successfully processed {len(processed_docs)} document(s)",
            "documents": [
                {
                    "filename": doc.filename,
                    "chunks_created": doc.chunks_created,
                    "text_length": doc.text_length
                } for doc in processed_docs
            ],
            "total_documents": len(processed_docs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/upload-single")
async def upload_single_document(file: UploadFile = File(...)):
    """Upload and process a single PDF (for backward compatibility)"""
    if not client:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        doc_info = await process_single_pdf(file)
        return {
            "message": f"Successfully processed {doc_info.filename}",
            "chunks_created": doc_info.chunks_created,
            "text_length": doc_info.text_length
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents with cross-document analysis"""
    if not client:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        logger.info(f"🔍 Query: {request.query}")
        
        # Search Weaviate using v4 API - get more results for cross-document analysis
        try:
            collection = client.collections.get("PolicyDocument")
            response = collection.query.bm25(
                query=request.query,
                limit=5,  # Get more results for cross-document analysis
                return_properties=["content", "source"]
            )
            
            documents = response.objects
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            documents = []
        
        if not documents:
            return QueryResponse(
                answer="No relevant information found",
                explanation="I couldn't find any information in your uploaded documents that relates to your question. Please make sure you've uploaded PDF documents and try again.",
                sources=None
            )
        
        # Group documents by source for cross-document analysis
        source_content = {}
        for doc in documents:
            content = doc.properties.get("content", "")
            source = doc.properties.get("source", "unknown")
            if source not in source_content:
                source_content[source] = []
            source_content[source].append(content)
        
        # Prepare content for analysis
        all_sources = list(source_content.keys())
        combined_content = []
        
        for source, contents in source_content.items():
            # Take the most relevant chunk from each document
            best_content = contents[0] if contents else ""
            combined_content.append(f"From {source}: {best_content}")
        
        # Create cross-document analysis prompt
        if len(all_sources) > 1:
            prompt = f"""Based on content from multiple documents, answer the user's question by analyzing information across all sources.

Documents and Content:
{chr(10).join(combined_content)}

User Question: {request.query}

Please provide:
1. A comprehensive answer that considers information from all relevant documents
2. A clear explanation highlighting any differences, similarities, or complementary information across documents
3. If there are conflicting information, mention it clearly

Format your response exactly like this:
Answer: [your comprehensive answer here]
Explanation: [your detailed explanation here]
Cross-Document Analysis: [analysis of how information relates across documents]
"""
        else:
            # Single document analysis
            prompt = f"""Based on this document content, answer the user's question in simple, clear language.

Document Content: {combined_content[0]}

User Question: {request.query}

Please provide:
1. A direct, simple answer
2. A clear explanation in everyday language

Format your response exactly like this:
Answer: [your direct answer here]
Explanation: [your simple explanation here]
"""

        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse response
            answer = "Unable to generate answer"
            explanation = "There was an issue processing your question."
            cross_analysis = None
            
            if "Answer:" in response_text:
                parts = response_text.split("Answer:", 1)[1]
                
                if "Explanation:" in parts:
                    answer_part, remaining = parts.split("Explanation:", 1)
                    answer = answer_part.strip()
                    
                    if "Cross-Document Analysis:" in remaining:
                        explanation_part, cross_part = remaining.split("Cross-Document Analysis:", 1)
                        explanation = explanation_part.strip()
                        cross_analysis = cross_part.strip()
                    else:
                        explanation = remaining.strip()
                else:
                    answer = parts.strip()
            
            # Fallback parsing
            if answer == "Unable to generate answer":
                lines = response_text.split('\n')
                for line in lines:
                    if line.startswith("Answer:"):
                        answer = line.replace("Answer:", "").strip()
                    elif line.startswith("Explanation:"):
                        explanation = line.replace("Explanation:", "").strip()
                    elif line.startswith("Cross-Document Analysis:"):
                        cross_analysis = line.replace("Cross-Document Analysis:", "").strip()
            
            # Final fallback
            if answer == "Unable to generate answer":
                answer = f"Based on your document(s), here's what I found about your question."
                explanation = f"Found relevant information in {len(all_sources)} document(s) that relates to your question about '{request.query}'."
            
            return QueryResponse(
                answer=answer,
                explanation=explanation,
                sources=all_sources,
                cross_document_analysis=cross_analysis if len(all_sources) > 1 else None
            )
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return QueryResponse(
                answer="Found relevant information",
                explanation=f"I found information in {len(all_sources)} document(s) that relates to your question.",
                sources=all_sources
            )
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    if not client:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        collection = client.collections.get("PolicyDocument")
        response = collection.query.fetch_objects(
            return_properties=["source"],
            limit=1000
        )
        
        # Get unique sources
        sources = set()
        for obj in response.objects:
            source = obj.properties.get("source")
            if source:
                sources.add(source)
        
        return {
            "documents": list(sources),
            "total_count": len(sources)
        }
        
    except Exception as e:
        logger.error(f"Document list error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document list")

@app.delete("/documents")
async def clear_all_documents():
    """Clear all uploaded documents"""
    if not client:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Delete and recreate collection
        client.collections.delete("PolicyDocument")
        
        client.collections.create(
            name="PolicyDocument",
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_transformers(),
            properties=[
                wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="source", data_type=wvc.config.DataType.TEXT)
            ]
        )
        
        logger.info("✅ All documents cleared")
        return {"message": "All documents cleared successfully"}
        
    except Exception as e:
        logger.error(f"Clear documents error: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear documents")

@app.on_event("shutdown")
async def shutdown_event():
    if client:
        client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)