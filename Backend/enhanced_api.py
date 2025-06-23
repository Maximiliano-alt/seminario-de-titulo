from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import logging
import tempfile
from dotenv import load_dotenv
from enhanced_uml_generator import EnhancedUMLGenerator, DomainClass
from enhanced_java_generator import EnhancedJavaGenerator, JavaCodeStructure
from llm_manager import LLMManager, LLMProvider
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize router
router = APIRouter()

# Initialize services
try:
    llm_manager = LLMManager()
    uml_generator = EnhancedUMLGenerator()
    java_generator = EnhancedJavaGenerator()
    logger.info("Enhanced services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize enhanced services: {str(e)}")
    raise

# Request/Response Models
class UserStoryRequest(BaseModel):
    user_story: str
    llm_provider: Optional[str] = "gpt-4o"

class DomainAnalysisResponse(BaseModel):
    domain_classes: List[Dict[str, Any]]
    llm_provider: str
    analysis_summary: str

class UMLGenerationRequest(BaseModel):
    user_story: str
    domain_classes: Optional[List[Dict[str, Any]]] = None
    llm_provider: Optional[str] = "gpt-4o"

class UMLGenerationResponse(BaseModel):
    plantuml_code: str
    domain_classes: List[Dict[str, Any]]
    image_base64: Optional[str] = None
    is_valid: bool
    validation_message: str
    llm_provider: str

class JavaCodeRequest(BaseModel):
    user_story: str
    domain_classes: List[Dict[str, Any]]
    plantuml_code: str
    llm_provider: Optional[str] = "gpt-4o"

class JavaCodeResponse(BaseModel):
    java_classes: Dict[str, str]
    project_structure: Dict[str, List[str]]
    dependencies: List[str]
    download_url: Optional[str] = None
    class_count: int

class CompleteWorkflowRequest(BaseModel):
    user_story: str
    llm_provider: Optional[str] = "gpt-4o"
    include_java_code: Optional[bool] = True

class CompleteWorkflowResponse(BaseModel):
    # Domain Analysis
    domain_classes: List[Dict[str, Any]]
    
    # UML Generation
    plantuml_code: str
    uml_image_base64: Optional[str] = None
    uml_is_valid: bool
    uml_validation_message: str
    
    # Java Code Generation (optional)
    java_classes: Optional[Dict[str, str]] = None
    project_structure: Optional[Dict[str, List[str]]] = None
    dependencies: Optional[List[str]] = None
    download_url: Optional[str] = None
    
    # Metadata
    llm_provider: str
    total_classes: int
    processing_time: float

# Utility functions
def _convert_domain_classes_from_dict(domain_classes_dict: List[Dict[str, Any]]) -> List[DomainClass]:
    """Convert dictionary representation to DomainClass objects."""
    domain_classes = []
    for dc_dict in domain_classes_dict:
        domain_class = DomainClass(
            name=dc_dict.get("name", "UnknownClass"),
            purpose=dc_dict.get("purpose", ""),
            fields=dc_dict.get("fields", []),
            methods=dc_dict.get("methods", [])
        )
        domain_classes.append(domain_class)
    return domain_classes

def _get_llm_provider(provider_name: str) -> LLMProvider:
    """Get LLMProvider enum from string name."""
    try:
        return LLMProvider(provider_name)
    except ValueError:
        logger.warning(f"Unknown LLM provider: {provider_name}, defaulting to GPT-4o")
        return LLMProvider.GPT_4O

def _render_uml_to_base64(plantuml_code: str) -> Optional[str]:
    """Render PlantUML code to base64 encoded image."""
    try:
        image_path = uml_generator.render_uml(plantuml_code)
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
            
            # Cleanup temporary file
            os.unlink(image_path)
            return base64_data
    except Exception as e:
        logger.error(f"Error rendering UML to base64: {e}")
    return None

# API Endpoints

@router.get("/llm-providers")
async def get_available_llm_providers():
    """Get list of available LLM providers."""
    try:
        providers = llm_manager.get_available_providers()
        return {
            "available_providers": providers,
            "default_provider": "gpt-4o"
        }
    except Exception as e:
        logger.error(f"Error getting LLM providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-domain", response_model=DomainAnalysisResponse)
async def analyze_domain(request: UserStoryRequest):
    """
    Step 1: Analyze user story and extract domain classes.
    Parse the story → infer domain nouns → propose up to 6 classes with fields & methods.
    """
    try:
        llm_provider = _get_llm_provider(request.llm_provider)
        
        # Check if provider is available
        if not llm_manager.is_provider_available(llm_provider):
            raise HTTPException(
                status_code=400, 
                detail=f"LLM provider {request.llm_provider} is not available. Please check your API keys."
            )
        
        # Analyze domain
        domain_classes = uml_generator.analyze_domain(request.user_story, llm_provider)
        
        # Create summary
        class_names = [dc.name for dc in domain_classes]
        summary = f"Identified {len(domain_classes)} domain classes: {', '.join(class_names)}"
        
        return DomainAnalysisResponse(
            domain_classes=[dc.to_dict() for dc in domain_classes],
            llm_provider=request.llm_provider,
            analysis_summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error in domain analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-uml", response_model=UMLGenerationResponse)
async def generate_uml_diagram(request: UMLGenerationRequest):
    """
    Step 2: Generate PlantUML class diagram from domain classes.
    Output a complete PlantUML class diagram inside ```@startuml```…```@enduml```.
    """
    try:
        llm_provider = _get_llm_provider(request.llm_provider)
        
        # Check if provider is available
        if not llm_manager.is_provider_available(llm_provider):
            raise HTTPException(
                status_code=400, 
                detail=f"LLM provider {request.llm_provider} is not available"
            )
        
        # If domain classes not provided, analyze first
        if not request.domain_classes:
            domain_classes = uml_generator.analyze_domain(request.user_story, llm_provider)
        else:
            domain_classes = _convert_domain_classes_from_dict(request.domain_classes)
        
        # Generate PlantUML diagram
        plantuml_code = uml_generator.generate_plantuml_diagram(
            request.user_story, domain_classes, llm_provider
        )
        
        # Validate UML
        is_valid, validation_message = uml_generator.validate_uml(plantuml_code)
        
        # Render to image
        image_base64 = _render_uml_to_base64(plantuml_code)
        
        return UMLGenerationResponse(
            plantuml_code=plantuml_code,
            domain_classes=[dc.to_dict() for dc in domain_classes],
            image_base64=image_base64,
            is_valid=is_valid,
            validation_message=validation_message,
            llm_provider=request.llm_provider
        )
        
    except Exception as e:
        logger.error(f"Error generating UML diagram: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-java-code", response_model=JavaCodeResponse)
async def generate_java_code(request: JavaCodeRequest):
    """
    Step 3: Generate compilable Java code from domain classes and UML diagram.
    Generate compilable starter code for those classes in Java.
    """
    try:
        llm_provider = _get_llm_provider(request.llm_provider)
        
        # Check if provider is available
        if not llm_manager.is_provider_available(llm_provider):
            raise HTTPException(
                status_code=400, 
                detail=f"LLM provider {request.llm_provider} is not available"
            )
        
        # Convert domain classes
        domain_classes = _convert_domain_classes_from_dict(request.domain_classes)
        
        # Generate Java code
        code_structure = java_generator.generate_complete_project(
            request.user_story, domain_classes, request.plantuml_code, llm_provider
        )
        
        # Create download package
        output_dir = tempfile.mkdtemp()
        download_path = java_generator.create_download_package(code_structure, output_dir)
        
        return JavaCodeResponse(
            java_classes=code_structure.classes,
            project_structure=code_structure.packages,
            dependencies=code_structure.dependencies,
            download_url=f"/download/{os.path.basename(download_path)}",
            class_count=code_structure.get_class_count()
        )
        
    except Exception as e:
        logger.error(f"Error generating Java code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/complete-workflow", response_model=CompleteWorkflowResponse)
async def complete_workflow(request: CompleteWorkflowRequest):
    """
    Complete workflow: User Stories → LLM processing → UML diagram → Java code.
    Implements the full pipeline in a single endpoint.
    """
    import time
    start_time = time.time()
    
    try:
        llm_provider = _get_llm_provider(request.llm_provider)
        
        # Check if provider is available
        if not llm_manager.is_provider_available(llm_provider):
            raise HTTPException(
                status_code=400, 
                detail=f"LLM provider {request.llm_provider} is not available"
            )
        
        # Step 1: Domain Analysis
        logger.info("Step 1: Analyzing domain...")
        domain_classes = uml_generator.analyze_domain(request.user_story, llm_provider)
        
        # Step 2: UML Generation
        logger.info("Step 2: Generating UML diagram...")
        plantuml_code = uml_generator.generate_plantuml_diagram(
            request.user_story, domain_classes, llm_provider
        )
        
        # Validate and render UML
        is_valid, validation_message = uml_generator.validate_uml(plantuml_code)
        image_base64 = _render_uml_to_base64(plantuml_code)
        
        # Step 3: Java Code Generation (optional)
        java_classes = None
        project_structure = None
        dependencies = None
        download_url = None
        
        if request.include_java_code:
            logger.info("Step 3: Generating Java code...")
            code_structure = java_generator.generate_complete_project(
                request.user_story, domain_classes, plantuml_code, llm_provider
            )
            
            java_classes = code_structure.classes
            project_structure = code_structure.packages
            dependencies = code_structure.dependencies
            
            # Create download package
            output_dir = tempfile.mkdtemp()
            download_path = java_generator.create_download_package(code_structure, output_dir)
            download_url = f"/download/{os.path.basename(download_path)}"
        
        processing_time = time.time() - start_time
        
        return CompleteWorkflowResponse(
            # Domain Analysis
            domain_classes=[dc.to_dict() for dc in domain_classes],
            
            # UML Generation
            plantuml_code=plantuml_code,
            uml_image_base64=image_base64,
            uml_is_valid=is_valid,
            uml_validation_message=validation_message,
            
            # Java Code Generation
            java_classes=java_classes,
            project_structure=project_structure,
            dependencies=dependencies,
            download_url=download_url,
            
            # Metadata
            llm_provider=request.llm_provider,
            total_classes=len(domain_classes),
            processing_time=round(processing_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Error in complete workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
async def download_generated_code(filename: str):
    """Download generated Java project as ZIP file."""
    try:
        # Security check - ensure filename is safe
        if not filename.endswith('.zip') or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        file_path = os.path.join(tempfile.gettempdir(), filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/zip'
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/render-uml")
async def render_uml_image(plantuml_code: str):
    """Render PlantUML code to base64 image for preview."""
    try:
        image_base64 = _render_uml_to_base64(plantuml_code)
        if image_base64:
            return {"image_base64": image_base64}
        else:
            raise HTTPException(status_code=400, detail="Failed to render UML diagram")
    except Exception as e:
        logger.error(f"Error rendering UML: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    available_providers = llm_manager.get_available_providers()
    return {
        "status": "healthy",
        "available_llm_providers": list(available_providers.keys()),
        "total_providers": len(available_providers)
    } 