#!/usr/bin/env python3
"""
Startup script for production deployment.
Handles memory constraints and graceful service degradation.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_memory_constraints():
    """Check if we're in a memory-constrained environment."""
    memory_limit = os.getenv("MEMORY_LIMIT", "1024")
    
    try:
        memory_limit_mb = int(memory_limit)
        if memory_limit_mb <= 512:
            logger.info(f"Memory-constrained environment detected: {memory_limit_mb}MB")
            return True
    except ValueError:
        pass
    
    return False

def set_production_environment():
    """Set environment variables for production deployment."""
    
    # Check if we're in a memory-constrained environment
    is_memory_constrained = check_memory_constraints()
    
    # Check if we're on Railway (Railway has good memory limits)
    is_railway = os.getenv("RAILWAY_ENVIRONMENT") is not None
    
    if is_railway:
        logger.info("Detected Railway deployment - using FULL functionality")
        # Railway has good memory limits, use full features
        os.environ.setdefault("USE_LIGHTWEIGHT_VECTOR_STORE", "false")
        os.environ.setdefault("USE_EMBEDDINGS", "true")
        os.environ.setdefault("USE_FAISS", "true")
        
    elif is_memory_constrained:
        logger.info("Configuring for memory-constrained deployment")
        
        # Use lightweight configurations
        os.environ.setdefault("USE_LIGHTWEIGHT_VECTOR_STORE", "true")
        os.environ.setdefault("USE_EMBEDDINGS", "false")
        os.environ.setdefault("USE_FAISS", "false")
        
        # Disable heavy features
        os.environ.setdefault("DISABLE_VECTOR_STORE", "false")  # Keep it enabled but lightweight
        
    else:
        logger.info("Configuring for standard deployment")
        
        # Use full features when memory allows
        os.environ.setdefault("USE_LIGHTWEIGHT_VECTOR_STORE", "false")
        os.environ.setdefault("USE_EMBEDDINGS", "true")
        os.environ.setdefault("USE_FAISS", "true")
    
    # Common production settings
    os.environ.setdefault("ENVIRONMENT", "production")
    os.environ.setdefault("PORT", "8000")
    
    logger.info("Environment configured for production")

def start_application():
    """Start the FastAPI application with fallback to minimal version."""
    try:
        # Set environment first
        set_production_environment()
        
        # Import and start the app
        import uvicorn
        
        # Try to import the full main app first
        try:
            from main import app
            logger.info("Starting full-featured application")
        except ImportError as import_error:
            logger.warning(f"Failed to import main app: {import_error}")
            logger.info("Falling back to minimal application")
            
            try:
                from main_minimal import app
                logger.info("Using minimal application")
            except ImportError:
                logger.warning("Minimal app also failed, creating emergency app")
                from fastapi import FastAPI
                
                app = FastAPI(title="Emergency eCommerce API", version="2.0.0")
                
                @app.get("/")
                async def emergency_root():
                    return {
                        "message": "Emergency mode - limited functionality", 
                        "status": "emergency",
                        "available_endpoints": ["/", "/health"]
                    }
                
                @app.get("/health")
                async def emergency_health():
                    return {"status": "healthy", "mode": "emergency"}
        
        port = int(os.getenv("PORT", 8000))
        host = os.getenv("HOST", "0.0.0.0")
        
        logger.info(f"Starting application on {host}:{port}")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_application() 