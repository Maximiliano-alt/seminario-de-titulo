from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import the enhanced API with real LLM calls
try:
    from api import router as enhanced_router
    logger.info("Successfully imported enhanced API with real LLM calls")
    use_enhanced_api = True
except ImportError as e:
    logger.error(f"Failed to import enhanced API due to a missing dependency: {e}")
    logger.error("The application will not start. Please install the missing package and try again.")
    raise e

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced eCommerce LLM Code Generator",
    description="Enhanced API with multi-LLM support for generating UML diagrams and Java code from user stories",
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
    frontend_url,
    "https://story-umlify.netlify.app"  # Explicitly add your Netlify URL
]

# Log CORS configuration for debugging
logger.info(f"FRONTEND_URL from environment: {frontend_url}")
logger.info(f"Allowed CORS origins: {allowed_origins}")

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
    api_status = "Enhanced API with real LLM calls" if use_enhanced_api else "Simple Enhanced API (mock responses)"
    
    return {
        "message": "Enhanced eCommerce LLM Code Generator API",
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
                    "/api/v2/generate-java-code",
                    "/api/v2/complete-workflow",
                    "/api/v2/render-uml",
                    "/api/v2/download/{filename}"
                ]
            }
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 