from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import the enhanced API, but provide fallback if it fails
try:
    from api import router as enhanced_router
    logger.info("Successfully imported enhanced API with real LLM calls")
    use_enhanced_api = True
except ImportError as e:
    logger.warning(f"Failed to import enhanced API: {e}")
    logger.info("Creating minimal API with basic endpoints")
    use_enhanced_api = False
    
    # Create a minimal router as fallback
    from fastapi import APIRouter
    enhanced_router = APIRouter()
    
    @enhanced_router.get("/llm-providers")
    async def get_llm_providers():
        return {"providers": [], "message": "LLM providers not available - missing dependencies"}
    
    @enhanced_router.post("/analyze-domain")
    async def analyze_domain(request: dict):
        return {
            "domain_classes": [
                {"name": "Product", "fields": ["id", "name", "price"], "methods": ["getId", "setPrice"]},
                {"name": "User", "fields": ["id", "email"], "methods": ["login", "logout"]}
            ],
            "message": "Mock response - LLM not available"
        }
    
    @enhanced_router.post("/generate-uml")
    async def generate_uml(request: dict):
        return {
            "uml_code": "@startuml\nclass Product {\n  +id: Long\n  +name: String\n}\n@enduml",
            "message": "Mock UML - LLM not available"
        }
    
    @enhanced_router.post("/generate-java-code")
    async def generate_java_code(request: dict):
        return {
            "java_files": [{"filename": "Product.java", "content": "public class Product { private Long id; }"}],
            "message": "Mock Java code - LLM not available"
        }

# Initialize FastAPI app
app = FastAPI(
    title="eCommerce Code Generator API",
    description="Code generator API - minimal mode" if not use_enhanced_api else "Enhanced API with LLM support",
    version="2.0.0"
)

# Global Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."},
    )

# Configure CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
allowed_origins = [
    "http://localhost:3000", 
    "http://localhost:5173",
    frontend_url
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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

# Include the enhanced API router (v2)
app.include_router(enhanced_router, prefix="/api/v2")

@app.get("/")
async def root():
    api_status = "Enhanced API with real LLM calls" if use_enhanced_api else "Minimal API (mock responses)"
    
    return {
        "message": "eCommerce LLM Code Generator API",
        "version": "2.0.0",
        "api_mode": api_status,
        "using_real_llm": use_enhanced_api,
        "api_versions": {
            "v2": {
                "description": api_status,
                "endpoints": [
                    "/api/v2/llm-providers",
                    "/api/v2/analyze-domain",
                    "/api/v2/generate-uml",
                    "/api/v2/generate-java-code"
                ]
            }
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0", "mode": "minimal" if not use_enhanced_api else "full"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 