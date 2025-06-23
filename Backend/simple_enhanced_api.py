from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize router
router = APIRouter()

# Simple LLM Provider Management
class LLMProviderInfo:
    def __init__(self):
        self.providers = self._initialize_providers()
    
    def _initialize_providers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize LLM providers based on available API keys."""
        providers = {}
        
        # Check OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        print(openai_key)
        if openai_key and openai_key.strip() and openai_key != "your_openai_api_key_here":
            providers["gpt-4o"] = {
                "name": "GPT-4o (OpenAI)",
                "available": True,
                "provider": "openai"
            }
            providers["gpt-4o-mini"] = {
                "name": "GPT-4o Mini (OpenAI)",
                "available": True,
                "provider": "openai"
            }
            providers["gpt-3.5-turbo"] = {
                "name": "GPT-3.5 Turbo (OpenAI)",
                "available": True,
                "provider": "openai"
            }
            logger.info("OpenAI providers initialized successfully")
        else:
            providers["gpt-4o"] = {
                "name": "GPT-4o (OpenAI) - API Key Required",
                "available": False,
                "provider": "openai"
            }
            providers["gpt-4o-mini"] = {
                "name": "GPT-4o Mini (OpenAI) - API Key Required",
                "available": False,
                "provider": "openai"
            }
        
        # Check Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key and anthropic_key.strip() and anthropic_key != "your_anthropic_api_key_here":
            providers["claude-3-5-sonnet-20241022"] = {
                "name": "Claude 3.5 Sonnet (Anthropic)",
                "available": True,
                "provider": "anthropic"
            }
            logger.info("Anthropic providers initialized successfully")
        else:
            providers["claude-3-5-sonnet-20241022"] = {
                "name": "Claude 3.5 Sonnet (Anthropic) - API Key Required",
                "available": False,
                "provider": "anthropic"
            }
        
        # Check Google
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key and google_key.strip() and google_key != "your_google_api_key_here":
            providers["gemini-2.0-flash-exp"] = {
                "name": "Gemini 2.0 Flash (Google)",
                "available": True,
                "provider": "google"
            }
            logger.info("Google providers initialized successfully")
        else:
            providers["gemini-2.0-flash-exp"] = {
                "name": "Gemini 2.0 Flash (Google) - API Key Required",
                "available": False,
                "provider": "google"
            }
        
        # Check DeepSeek
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key and deepseek_key.strip() and deepseek_key != "your_deepseek_api_key_here":
            providers["deepseek-r1"] = {
                "name": "DeepSeek R1",
                "available": True,
                "provider": "deepseek"
            }
            logger.info("DeepSeek providers initialized successfully")
        else:
            providers["deepseek-r1"] = {
                "name": "DeepSeek R1 - API Key Required",
                "available": False,
                "provider": "deepseek"
            }
        
        logger.info(f"Initialized {len(providers)} LLM providers")
        return providers
    
    def get_all_providers(self) -> Dict[str, str]:
        """Get all providers (available and unavailable)."""
        return {key: info["name"] for key, info in self.providers.items()}
    
    def get_available_providers(self) -> Dict[str, str]:
        """Get only available providers."""
        return {key: info["name"] for key, info in self.providers.items() if info["available"]}
    
    def is_provider_available(self, provider_id: str) -> bool:
        """Check if a provider is available."""
        return provider_id in self.providers and self.providers[provider_id]["available"]

# Initialize provider manager
llm_provider_manager = LLMProviderInfo()

# Request/Response Models
class UserStoryRequest(BaseModel):
    user_story: str
    llm_provider: Optional[str] = "gpt-4o"

class DomainAnalysisResponse(BaseModel):
    domain_classes: List[Dict[str, Any]]
    llm_provider: str
    analysis_summary: str

# Mock domain analysis function
def mock_analyze_domain(user_story: str, llm_provider: str) -> List[Dict[str, Any]]:
    """Mock domain analysis for demo purposes."""
    # Simple keyword-based analysis for demo
    classes = []
    
    if "customer" in user_story.lower():
        classes.append({
            "name": "Customer",
            "purpose": "Represents a customer in the eCommerce system",
            "fields": ["id: Long", "name: String", "email: String", "createdAt: LocalDateTime"],
            "methods": ["getId(): Long", "getName(): String", "getEmail(): String"]
        })
    
    if "product" in user_story.lower() or "item" in user_story.lower():
        classes.append({
            "name": "Product",
            "purpose": "Represents a product available for purchase",
            "fields": ["id: Long", "name: String", "price: BigDecimal", "description: String"],
            "methods": ["getId(): Long", "getName(): String", "getPrice(): BigDecimal"]
        })
    
    if "cart" in user_story.lower() or "shopping" in user_story.lower():
        classes.append({
            "name": "ShoppingCart",
            "purpose": "Manages customer's selected items before purchase",
            "fields": ["id: Long", "customerId: Long", "items: List<CartItem>", "total: BigDecimal"],
            "methods": ["addItem(Product product): void", "removeItem(Long productId): void", "getTotal(): BigDecimal"]
        })
    
    if "order" in user_story.lower() or "purchase" in user_story.lower():
        classes.append({
            "name": "Order",
            "purpose": "Represents a completed purchase transaction",
            "fields": ["id: Long", "customerId: Long", "orderDate: LocalDateTime", "status: OrderStatus"],
            "methods": ["getId(): Long", "getCustomerId(): Long", "getStatus(): OrderStatus"]
        })
    
    # If no specific keywords found, provide generic classes
    if not classes:
        classes = [
            {
                "name": "User",
                "purpose": "Represents a user in the system",
                "fields": ["id: Long", "username: String", "email: String"],
                "methods": ["getId(): Long", "getUsername(): String"]
            },
            {
                "name": "Service",
                "purpose": "Provides business logic for the application",
                "fields": ["repository: Repository"],
                "methods": ["processRequest(): Response"]
            }
        ]
    
    return classes

# API Endpoints
@router.get("/llm-providers")
async def get_available_llm_providers():
    """Get list of available LLM providers."""
    try:
        all_providers = llm_provider_manager.get_all_providers()
        available_providers = llm_provider_manager.get_available_providers()
        
        return {
            "available_providers": all_providers,
            "available_count": len(available_providers),
            "total_count": len(all_providers),
            "default_provider": "gpt-4o",
            "status": "success"
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
        # Check if provider is available
        if not llm_provider_manager.is_provider_available(request.llm_provider):
            # For demo purposes, we'll still proceed but note the limitation
            logger.warning(f"LLM provider {request.llm_provider} is not available, using mock analysis")
        
        # Use mock analysis for now
        domain_classes = mock_analyze_domain(request.user_story, request.llm_provider)
        
        # Create summary
        class_names = [dc["name"] for dc in domain_classes]
        summary = f"Identified {len(domain_classes)} domain classes: {', '.join(class_names)}"
        
        return DomainAnalysisResponse(
            domain_classes=domain_classes,
            llm_provider=request.llm_provider,
            analysis_summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error in domain analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-uml")
async def generate_uml_diagram(request: UserStoryRequest):
    """
    Step 2: Generate PlantUML class diagram from domain classes.
    """
    try:
        # Mock UML generation for demo
        domain_classes = mock_analyze_domain(request.user_story, request.llm_provider)
        
        # Generate simple PlantUML
        plantuml_code = "@startuml\n"
        for dc in domain_classes:
            plantuml_code += f"class {dc['name']} {{\n"
            for field in dc['fields'][:3]:  # Limit fields for readability
                plantuml_code += f"  {field}\n"
            plantuml_code += "}\n\n"
        plantuml_code += "@enduml"
        
        return {
            "plantuml_code": plantuml_code,
            "domain_classes": domain_classes,
            "is_valid": True,
            "validation_message": "UML diagram generated successfully",
            "llm_provider": request.llm_provider
        }
        
    except Exception as e:
        logger.error(f"Error generating UML diagram: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/complete-workflow")
async def complete_workflow(request: UserStoryRequest):
    """
    Complete workflow: User Stories → LLM processing → UML diagram → Java code.
    """
    import time
    start_time = time.time()
    
    try:
        # Step 1: Domain Analysis
        domain_classes = mock_analyze_domain(request.user_story, request.llm_provider)
        
        # Step 2: UML Generation
        plantuml_code = "@startuml\n"
        for dc in domain_classes:
            plantuml_code += f"class {dc['name']} {{\n"
            for field in dc['fields'][:3]:
                plantuml_code += f"  {field}\n"
            plantuml_code += "}\n\n"
        plantuml_code += "@enduml"
        
        # Step 3: Mock Java Code Generation
        java_classes = {}
        for dc in domain_classes:
            java_code = f"""package com.generated.ecommerce.model;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "{dc['name'].lower()}s")
public class {dc['name']} {{
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    // Add other fields here
    private String name;
    
    // Constructors
    public {dc['name']}() {{}}
    
    // Getters and Setters
    public Long getId() {{
        return id;
    }}
    
    public void setId(Long id) {{
        this.id = id;
    }}
    
    public String getName() {{
        return name;
    }}
    
    public void setName(String name) {{
        this.name = name;
    }}
}}"""
            java_classes[f"com.generated.ecommerce.model.{dc['name']}"] = java_code
        
        processing_time = time.time() - start_time
        
        return {
            "domain_classes": domain_classes,
            "plantuml_code": plantuml_code,
            "uml_is_valid": True,
            "uml_validation_message": "UML diagram generated successfully",
            "java_classes": java_classes,
            "project_structure": {
                "com.generated.ecommerce.model": [dc["name"] for dc in domain_classes]
            },
            "dependencies": ["Spring Boot Web", "Spring Boot Data JPA", "H2 Database"],
            "llm_provider": request.llm_provider,
            "total_classes": len(domain_classes),
            "processing_time": round(processing_time, 2)
        }
        
    except Exception as e:
        logger.error(f"Error in complete workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/render-uml")
async def render_uml_diagram(request: dict):
    """Render PlantUML code to image using PlantUML server."""
    try:
        plantuml_code = request.get("plantuml_code", "")
        if not plantuml_code:
            raise HTTPException(status_code=400, detail="PlantUML code is required")
        
        import base64
        from plantuml import PlantUML
        
        try:
            # Use PlantUML library to render the diagram
            plantuml = PlantUML(url='http://www.plantuml.com/plantuml/img/')
            
            # Generate the image
            image_data = plantuml.processes(plantuml_code)
            
            if image_data:
                # Convert image to base64
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                return {
                    "success": True,
                    "image_base64": image_base64,
                    "message": "Diagram rendered successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate diagram"
                }
        except Exception as plantuml_error:
            # Fallback: try to create a simple text-based representation
            logger.warning(f"PlantUML rendering failed: {plantuml_error}")
            
            # Create a simple SVG as fallback
            svg_content = f"""
            <svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6"/>
                <text x="200" y="100" text-anchor="middle" font-family="monospace" font-size="14" fill="#495057">
                    UML Diagram Preview
                </text>
                <text x="200" y="120" text-anchor="middle" font-family="monospace" font-size="12" fill="#6c757d">
                    PlantUML Code Generated
                </text>
                <text x="200" y="140" text-anchor="middle" font-family="monospace" font-size="10" fill="#6c757d">
                    Switch to "PlantUML Code" tab to view
                </text>
            </svg>
            """
            
            # Convert SVG to base64
            svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
            
            return {
                "success": True,
                "image_base64": svg_base64,
                "message": "Fallback diagram generated (PlantUML service unavailable)",
                "is_fallback": True
            }
            
    except Exception as e:
        logger.error(f"Error rendering UML diagram: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    available_providers = llm_provider_manager.get_available_providers()
    return {
        "status": "healthy",
        "available_llm_providers": list(available_providers.keys()),
        "total_providers": len(available_providers)
    } 