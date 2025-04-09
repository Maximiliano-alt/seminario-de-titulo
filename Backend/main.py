from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from api import router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="eCommerce LLM Code Generator",
    description="Generate UML diagrams and Java code from user stories using LangChain and RAG",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories for static files
os.makedirs("static/uml", exist_ok=True)
os.makedirs("static/java", exist_ok=True)

# Mount static file directories
app.mount("/api/static/uml", StaticFiles(directory="static/uml"), name="uml_static")
app.mount("/api/static/java", StaticFiles(directory="static/java"), name="java_static")

# Include the API router
app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "eCommerce LLM Code Generator API",
        "version": "1.0.0",
        "endpoints": [
            "/api/user-story/uml",
            "/api/user-story/java",
            "/api/search-similar",
            "/api/generate",
            "/api/fine-tune"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 