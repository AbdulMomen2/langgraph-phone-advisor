from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from config import Config
from database import DatabaseManager
from langgraph_agent import PhoneRAGGraph


app = FastAPI(
    title="Phone Advisor API",
    description="RAG-based phone specification advisor",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
config = Config()
db_manager = None
rag_agent = None


class QuestionRequest(BaseModel):
    question: str = Field(..., description="Natural language question about phones")
    thread_id: Optional[str] = Field(None, description="Conversation thread ID")

class QuestionResponse(BaseModel):
    answer: str
    sql_query: str
    results: List[Dict[str, Any]]
    thread_id: str
    timestamp: str

class ThreadResponse(BaseModel):
    thread_id: str
    messages: List[Dict[str, str]]

class HealthResponse(BaseModel):
    status: str
    database: str
    agent: str

class PhoneSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(10, ge=1, le=50)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database and RAG agent on startup"""
    global db_manager, rag_agent
    
    try:
        # Initialize database
        db_manager = DatabaseManager(config)
        db_manager.connect()
        
        # Initialize RAG agent with LangGraph
        rag_agent = PhoneRAGGraph(db_manager, config, use_groq=True)
        
    except Exception as e:
        print(f"✗ Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    if db_manager:
        db_manager.close()

# API endpoints
@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if db_manager and db_manager.conn else "disconnected",
        "agent": "ready" if rag_agent else "not initialized"
    }

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question about phones"""
    if not rag_agent:
        raise HTTPException(status_code=503, detail="RAG agent not initialized")
    
    try:
        # Generate or use provided thread_id
        thread_id = request.thread_id or str(uuid.uuid4())
        
        # Get answer from RAG agent
        result = rag_agent.ask(request.question, thread_id)
        
        return QuestionResponse(
            answer=result["answer"],
            sql_query=result["sql_query"],
            results=result["results"],
            thread_id=thread_id,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/thread/{thread_id}", response_model=ThreadResponse)
async def get_thread_history(thread_id: str):
    """Get conversation history for a thread"""
    if not rag_agent:
        raise HTTPException(status_code=503, detail="RAG agent not initialized")
    
    try:
        messages = rag_agent.get_conversation_history(thread_id)
        
        formatted_messages = []
        for msg in messages:
            if hasattr(msg, 'type'):
                role = 'user' if msg.type == 'human' else 'assistant'
            else:
                role = 'system'
            
            formatted_messages.append({
                "role": role,
                "content": msg.content if hasattr(msg, 'content') else str(msg)
            })
        
        return ThreadResponse(
            thread_id=thread_id,
            messages=formatted_messages
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching thread: {str(e)}")

@app.post("/search")
async def search_phones(request: PhoneSearchRequest):
    """Search phones by name"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        query = f"""
        SELECT name, image_url, platform_os, main_camera, battery_type, misc_price
        FROM samsung_phones
        WHERE name ILIKE '%{request.query}%'
        LIMIT {request.limit}
        """
        
        results = db_manager.execute_query(query)
        return {"results": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/phones/popular")
async def get_popular_phones():
    """Get popular/recent phones"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        query = """
        SELECT name, image_url, launch_announced, platform_os, main_camera
        FROM samsung_phones
        WHERE launch_announced != ''
        ORDER BY id DESC
        LIMIT 10
        """
        
        results = db_manager.execute_query(query)
        return {"results": results}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/phones/{phone_id}")
async def get_phone_details(phone_id: int):
    """Get detailed specs for a specific phone"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        query = f"SELECT * FROM samsung_phones WHERE id = {phone_id}"
        results = db_manager.execute_query(query)
        
        if not results:
            raise HTTPException(status_code=404, detail="Phone not found")
        
        return results[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/stats")
async def get_statistics():
    """Get database statistics"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        stats_query = """
        SELECT 
            COUNT(*) as total_phones,
            COUNT(DISTINCT platform_chipset) as unique_chipsets,
            COUNT(*) FILTER (WHERE network_5g_bands != '') as phones_with_5g
        FROM samsung_phones
        """
        
        results = db_manager.execute_query(stats_query)
        return results[0] if results else {}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Run with: uvicorn api:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)