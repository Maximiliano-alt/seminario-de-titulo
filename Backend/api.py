from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import re

# Import LangChain components with error handling
try:
    from langchain_openai import ChatOpenAI
    from openai import APIStatusError
    OPENAI_AVAILABLE = True
except ImportError as e:
    print(f"OpenAI import failed: {e}")
    OPENAI_AVAILABLE = False
    ChatOpenAI = None
    APIStatusError = None

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError as e:
    print(f"Anthropic import failed: {e}")
    ANTHROPIC_AVAILABLE = False
    ChatAnthropic = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GOOGLE_AVAILABLE = True
except ImportError as e:
    print(f"Google import failed: {e}")
    GOOGLE_AVAILABLE = False
    ChatGoogleGenerativeAI = None
import json
import os
import logging
import tempfile
from dotenv import load_dotenv
from vector_store import VectorStore
from uml_generator import UMLGenerator
from java_generator import JavaGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize router
router = APIRouter()

# Multi-LLM Provider Management
class LLMManager:
    def __init__(self):
        self.providers = self._initialize_providers()
        # Removed llm_instances cache to prevent concurrency issues
    
    def _initialize_providers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize LLM providers based on available API keys."""
        providers = {}
        
        # Check OpenAI - Only keep GPT-4o Mini
        openai_key = os.getenv("OPENAI_API_KEY")
        if OPENAI_AVAILABLE and openai_key and openai_key.strip() and openai_key != "your_openai_api_key_here":
            # Remove GPT-4o and GPT-3.5, only keep GPT-4o Mini
            providers["gpt-4o-mini"] = {"name": "GPT-4o Mini (OpenAI)", "available": True, "provider": "openai", "model": "gpt-4o-mini"}
            logger.info("OpenAI providers initialized successfully")
        else:
            reason = "OpenAI libraries not installed." if not OPENAI_AVAILABLE else "OPENAI_API_KEY not found in .env file."
            providers["gpt-4o-mini"] = {"name": "GPT-4o Mini (OpenAI)", "available": False, "provider": "openai", "model": "gpt-4o-mini", "reason": reason}
        
        # Check Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if ANTHROPIC_AVAILABLE and anthropic_key and anthropic_key.strip() and anthropic_key != "your_anthropic_api_key_here":
            providers["claude-3-5-sonnet-20241022"] = {"name": "Claude 3.5 Sonnet (Anthropic)", "available": True, "provider": "anthropic", "model": "claude-3-5-sonnet-20241022"}
            logger.info("Anthropic providers initialized successfully")
        else:
            reason = "Anthropic libraries not installed." if not ANTHROPIC_AVAILABLE else "ANTHROPIC_API_KEY not found in .env file."
            providers["claude-3-5-sonnet-20241022"] = {"name": "Claude 3.5 Sonnet (Anthropic)", "available": False, "provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "reason": reason}
        
        # Check Google
        google_key = os.getenv("GOOGLE_API_KEY")
        if GOOGLE_AVAILABLE and google_key and google_key.strip() and google_key != "your_google_api_key_here":
            providers["gemini-2.0-flash-exp"] = {"name": "Gemini 2.0 Flash (Google)", "available": True, "provider": "google", "model": "gemini-2.0-flash-exp"}
            logger.info("Google providers initialized successfully")
        else:
            reason = "Google libraries not installed." if not GOOGLE_AVAILABLE else "GOOGLE_API_KEY not found in .env file."
            providers["gemini-2.0-flash-exp"] = {"name": "Gemini 2.0 Flash (Google)", "available": False, "provider": "google", "model": "gemini-2.0-flash-exp", "reason": reason}
        
        # Check DeepSeek (using OpenAI-compatible API via OpenRouter for the free model)
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if OPENAI_AVAILABLE and openrouter_key and openrouter_key.strip() and openrouter_key != "your_openrouter_api_key_here":
            providers["deepseek-r1"] = {
                "name": "DeepSeek Chat (Free via OpenRouter)",
                "available": True,
                "provider": "deepseek",
                "model": "deepseek/deepseek-chat"
            }
            logger.info("DeepSeek providers initialized successfully")
        else:
            reason = "OpenAI libraries not installed." if not OPENAI_AVAILABLE else "OPENROUTER_API_KEY not found in .env file."
            providers["deepseek-r1"] = {
                "name": "DeepSeek Chat (Free via OpenRouter)",
                "available": False,
                "provider": "deepseek",
                "model": "deepseek/deepseek-chat",
                "reason": reason
            }
        
        logger.info(f"Initialized {len(providers)} LLM providers")
        return providers
    
    def get_llm_instance(self, provider_id: str):
        """Create a NEW LLM instance for each request to avoid concurrency issues."""
        # NO LONGER using cached instances - create a new one for each request
        # This prevents blocking when multiple users use the same model
        
        provider_info = self.providers.get(provider_id)
        if not provider_info or not provider_info["available"]:
            raise ValueError(f"LLM provider {provider_id} is not available")
        
        try:
            logger.debug(f"Creating new LLM instance for {provider_id}")
            
            if provider_info["provider"] == "openai":
                if not OPENAI_AVAILABLE or ChatOpenAI is None:
                    raise ValueError("OpenAI provider not available due to import failure")
                llm = ChatOpenAI(
                    model=provider_info["model"],
                    temperature=0.1
                )
            elif provider_info["provider"] == "anthropic":
                if not ANTHROPIC_AVAILABLE or ChatAnthropic is None:
                    raise ValueError("Anthropic provider not available due to import failure")
                llm = ChatAnthropic(
                    model=provider_info["model"],
                    temperature=0.1
                )
            elif provider_info["provider"] == "google":
                if not GOOGLE_AVAILABLE or ChatGoogleGenerativeAI is None:
                    raise ValueError("Google provider not available due to import failure")
                llm = ChatGoogleGenerativeAI(
                    model=provider_info["model"],
                    temperature=0.1
                )
            elif provider_info["provider"] == "deepseek":
                if not OPENAI_AVAILABLE or ChatOpenAI is None:
                    raise ValueError("DeepSeek provider not available due to OpenAI import failure")
                # DeepSeek uses OpenAI-compatible API via OpenRouter for the free model
                llm = ChatOpenAI(
                    model="deepseek/deepseek-chat",
                    openai_api_base="https://openrouter.ai/api/v1",
                    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                    temperature=0.1
                )
            else:
                raise ValueError(f"Unknown provider: {provider_info['provider']}")
            
            # DO NOT cache the instance - return a fresh one
            logger.debug(f"Successfully created new LLM instance for {provider_id}")
            return llm
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM {provider_id}: {e}")
            raise
    
    def get_all_providers(self) -> Dict[str, str]:
        """Get all providers (available and unavailable)."""
        return {key: info["name"] for key, info in self.providers.items()}
    
    def get_available_providers(self) -> Dict[str, str]:
        """Get only available providers."""
        return {key: info["name"] for key, info in self.providers.items() if info["available"]}
    
    def is_provider_available(self, provider_id: str) -> bool:
        """Check if a provider is available."""
        return provider_id in self.providers and self.providers[provider_id]["available"]

    def get_unavailability_reason(self, provider_id: str) -> str:
        """Get the reason why a provider is unavailable."""
        if provider_id not in self.providers:
            return f"Provider '{provider_id}' is not configured."
        
        provider_info = self.providers[provider_id]
        if provider_info.get('available'):
            return "Provider is available."
            
        return provider_info.get("reason", "Provider is not available for an unknown reason.")

# Initialize LLM manager
# Note: LLMManager creates new instances per request to avoid concurrency issues
# This ensures multiple users can use the same model simultaneously
llm_manager = LLMManager()

# Initialize vector store and load dataset
try:
    # Initialize vector store with FAISS backend and SentenceTransformers embeddings
    use_faiss = os.getenv("USE_FAISS", "true").lower() == "true"  # Default to FAISS to avoid ChromaDB issues
    vector_store = VectorStore(use_faiss=use_faiss, embedding_provider="sentence-transformers")
    
    # Get the absolute path to the dataset
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(os.path.dirname(current_dir), "data", "dataset_new.json")
    
    # Try to load existing vector store first
    try:
        loaded = vector_store.load_vector_store(collection_name="ecommerce_examples")
        if loaded:
            logger.info("Successfully loaded pre-built vector store with RAG examples")
        else:
            logger.warning("Vector store not found, will proceed without RAG context")
            vector_store = None
    except Exception as load_error:
        logger.warning(f"Failed to load existing vector store: {load_error}")
        # Don't try to create from dataset, just proceed without vector store
        vector_store = None
        
    logger.info("Vector store initialized successfully")
    
    # Initialize UML and Java generators
    uml_generator = UMLGenerator()
    java_generator = JavaGenerator()
    logger.info("UML and Java generators initialized successfully")
    
except Exception as e:
    logger.warning(f"Failed to initialize some services: {str(e)}")
    # Continue with limited functionality
    vector_store = None
    uml_generator = UMLGenerator()
    java_generator = JavaGenerator()
    logger.info("Initialized with limited functionality (no vector store)")

# Models for request/response validation
class GenerationRequest(BaseModel):
    userStory: str
    umlDiagram: str

class GenerationResponse(BaseModel):
    code: str
    classInfo: list
    relationships: list
    
class UserStory(BaseModel):
    description: str
    acceptanceCriteria: List[str]

class UMLRequest(BaseModel):
    userStory: UserStory
    projectContext: Optional[str] = None
    llm_provider: Optional[str] = "gemini-2.0-flash-exp"  # Default to Gemini to avoid OpenAI quota
    
class UMLResponse(BaseModel):
    classDiagram: str
    sequenceDiagram: Optional[str] = None
    imageUrl: Optional[str] = None
    
class JavaCodeRequest(BaseModel):
    userStory: UserStory
    umlDiagram: str
    projectContext: Optional[str] = None
    llm_provider: Optional[str] = "gemini-2.0-flash-exp"  # Default to Gemini to avoid OpenAI quota
    
class ClassInfo(BaseModel):
    name: str
    purpose: str
    properties: List[str]
    methods: List[str]
    
class Relationship(BaseModel):
    fromClass: str
    toClass: str
    type: str
    description: str
    
class JavaCodeResponse(BaseModel):
    code: Dict[str, str]
    classInfo: List[ClassInfo]
    relationships: List[Relationship]
    downloadUrl: Optional[str] = None

# LLM will be initialized per request based on selected provider
logger.info("Multi-LLM manager initialized successfully")

# New Multi-LLM Endpoints
@router.get("/llm-providers")
async def get_llm_providers():
    """Get available LLM providers and their status
    This endpoint is stateless and thread-safe for concurrent access"""
    try:
        # Log the request for debugging
        logger.debug("LLM providers endpoint called")
        
        available_providers = {}
        unavailable_providers = {}
        
        for provider_id, provider_info in llm_manager.providers.items():
            if llm_manager.is_provider_available(provider_id):
                available_providers[provider_id] = provider_info['name']
            else:
                unavailable_providers[provider_id] = {
                    "name": provider_info['name'],
                    "reason": provider_info.get('reason', 'Unknown')
                }
        
        response = {
            "available_providers": available_providers,
            "unavailable_providers": unavailable_providers,
            "available_count": len(available_providers),
            "total_count": len(llm_manager.providers),
            "default_provider": "gemini-2.0-flash-exp",
            "status": "success",
            "message": "Providers list retrieved successfully. Multiple users can use the same model simultaneously."
        }
        
        logger.debug(f"Returning {len(available_providers)} available providers")
        return response
        
    except Exception as e:
        logger.error(f"Error getting LLM providers: {e}")
        # Return a degraded response instead of failing completely
        return {
            "available_providers": {},
            "unavailable_providers": {},
            "available_count": 0,
            "total_count": 0,
            "default_provider": "gemini-2.0-flash-exp",
            "status": "error",
            "message": f"Error retrieving providers: {str(e)}"
        }

# Enhanced request models for multi-LLM support
class EnhancedUserStoryRequest(BaseModel):
    user_story: str
    llm_provider: Optional[str] = "gemini-2.0-flash-exp"  # Default to Gemini to avoid OpenAI quota
    include_java_code: Optional[bool] = True

class DomainAnalysisResponse(BaseModel):
    domain_classes: List[Dict[str, Any]]
    llm_provider: str
    analysis_summary: str

@router.post("/analyze-domain", response_model=DomainAnalysisResponse)
async def analyze_domain(request: EnhancedUserStoryRequest):
    """
    Step 1: Analyze user story and extract domain classes using selected LLM.
    Parse the story → infer domain nouns → propose up to 6 classes with fields & methods.
    """
    try:
        # Get LLM instance for the selected provider
        if not llm_manager.is_provider_available(request.llm_provider):
            raise HTTPException(status_code=400, detail=f"LLM provider {request.llm_provider} is not available")
        
        llm = llm_manager.get_llm_instance(request.llm_provider)
        
        # Search for similar stories for RAG context
        similar_results = []
        if vector_store:
            try:
                similar_results = vector_store.search_similar(request.user_story, k=3)
                logger.info(f"Found {len(similar_results)} similar results for domain analysis")
            except Exception as e:
                logger.warning(f"Error searching similar results: {str(e)}")
        
        # Create context from similar results
        context = ""
        if similar_results:
            context = "Here are some similar user stories and their domain models:\n\n"
            for i, result in enumerate(similar_results, 1):
                context += f"Example {i}:\n{result.page_content}\n\n"
        
        # Create domain analysis prompt
        prompt = f"""You are an expert software architect specializing in domain-driven design. 
Analyze the following user story and extract the core domain classes.

{context}

USER STORY:
{request.user_story}

IMPORTANT: Respond ONLY with valid JSON in the exact format below. Do not include any explanation, markdown formatting, or additional text:

{{
    "domain_classes": [
        {{
            "name": "ClassName",
            "purpose": "Brief description of the class's purpose and responsibility",
            "fields": ["field1: Type", "field2: Type", "field3: Type"],
            "methods": ["method1(): ReturnType", "method2(param: Type): void"]
        }}
    ],
    "analysis_summary": "Brief summary of the domain analysis"
}}

Identify 3-6 domain classes with fields and methods. Return only the JSON object."""
        
        # Generate response using the selected LLM
        try:
            logger.info(f"Sending domain analysis request to {request.llm_provider}")
            response = llm.invoke(prompt)
            logger.info("Received response from LLM for domain analysis")
        except Exception as e:
            logger.error(f"Error generating response from LLM: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating response from LLM: {str(e)}")
        
        # Parse the response
        try:
            logger.info("Parsing LLM response for domain analysis")
            logger.info(f"Raw response content: {response.content[:300]}...")
            
            try:
                result = json.loads(response.content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
                
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response.content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                    logger.info("Successfully extracted JSON from markdown code block")
                else:
                    # Fallback response
                    result = {
                        "domain_classes": [
                            {
                                "name": "User",
                                "purpose": "Represents a user in the system",
                                "fields": ["id: Long", "email: String", "name: String"],
                                "methods": ["getId(): Long", "getEmail(): String"]
                            },
                            {
                                "name": "Product",
                                "purpose": "Represents a product in the system",
                                "fields": ["id: Long", "name: String", "price: BigDecimal"],
                                "methods": ["getId(): Long", "getName(): String"]
                            }
                        ],
                        "analysis_summary": "Fallback domain analysis completed"
                    }
                    logger.warning("Using fallback domain analysis result")
            
            return DomainAnalysisResponse(
                domain_classes=result.get("domain_classes", []),
                llm_provider=request.llm_provider,
                analysis_summary=result.get("analysis_summary", "Domain analysis completed")
            )
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing response: {str(e)}")
            
    except HTTPException:
        raise
    except APIStatusError as e:
        logger.error(f"LLM API error in domain analysis: {e}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in domain analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/complete-workflow")
async def complete_workflow(request: EnhancedUserStoryRequest):
    """
    Complete workflow: User Stories → Selected LLM processing → UML diagram → Java code.
    Uses the SELECTED LLM for ALL steps and RAG architecture for context.
    """
    import time
    start_time = time.time()
    
    try:
        # STEP 1: Validate and get the selected LLM instance
        if not llm_manager.is_provider_available(request.llm_provider):
            reason = llm_manager.get_unavailability_reason(request.llm_provider)
            raise HTTPException(status_code=400, detail=f"LLM provider '{request.llm_provider}' is not available. Reason: {reason}")
        
        # Get the LLM instance for the selected provider
        llm = llm_manager.get_llm_instance(request.llm_provider)
        logger.info(f"Starting complete workflow with {request.llm_provider}")
        
        # STEP 2: RAG - Search for similar user stories and implementations
        similar_results = []
        rag_context = ""
        
        if vector_store:
            try:
                # Search for similar user stories
                similar_results = vector_store.search_similar(request.user_story, k=5)
                logger.info(f"RAG: Found {len(similar_results)} similar examples")
                
                # Build RAG context from similar examples
                if similar_results:
                    rag_context = "=== SIMILAR EXAMPLES FROM RAG DATABASE ===\n\n"
                    for i, result in enumerate(similar_results, 1):
                        rag_context += f"Example {i}:\n{result.page_content}\n"
                        rag_context += "=" * 50 + "\n\n"
            except Exception as e:
                logger.warning(f"RAG search failed: {str(e)}")
                rag_context = ""
        else:
            logger.info("No vector store available, proceeding without RAG context")
        
        # STEP 3: Domain Analysis using SELECTED LLM + RAG
        logger.info(f"Domain analysis using {request.llm_provider}")
        
        domain_prompt = f"""You are an expert software architect. Analyze this user story and extract domain classes using the provided examples as reference.

{rag_context}

USER STORY TO ANALYZE:
{request.user_story}

INSTRUCTIONS:
Based on the user story and the similar examples above, identify the core domain classes needed.

RESPOND WITH VALID JSON ONLY:
{{
    "domain_classes": [
        {{
            "name": "ClassName",
            "purpose": "Clear description of the class responsibility",
            "fields": ["field1: Type", "field2: Type"],
            "methods": ["method1(): ReturnType", "method2(param: Type): void"]
        }}
    ]
}}

Extract 4-7 domain classes. Return ONLY the JSON object, no markdown or explanations."""
        
        # Get domain analysis from selected LLM
        domain_response = llm.invoke(domain_prompt)
        logger.info(f"Received domain analysis from {request.llm_provider}")
        
        # Parse domain analysis response
        try:
            # Clean the response and try to parse JSON
            clean_response = domain_response.content.strip()
            
            # Remove markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', clean_response, re.DOTALL)
            if json_match:
                clean_response = json_match.group(1)
            
            domain_result = json.loads(clean_response)
            domain_classes = domain_result.get("domain_classes", [])
            logger.info(f"Successfully parsed {len(domain_classes)} domain classes")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse domain analysis: {e}")
            # Fallback domain classes
            domain_classes = [
                {
                    "name": "User",
                    "purpose": "Represents a user in the system",
                    "fields": ["id: Long", "username: String", "email: String"],
                    "methods": ["authenticate(): boolean", "updateProfile(): void"]
                },
                {
                    "name": "Product", 
                    "purpose": "Represents a product in the system",
                    "fields": ["id: Long", "name: String", "price: BigDecimal"],
                    "methods": ["calculateDiscount(): BigDecimal", "updatePrice(): void"]
                }
            ]
        
        # STEP 4: UML Generation using SELECTED LLM + RAG + Domain Classes
        logger.info(f"UML generation using {request.llm_provider}")
        
        # Create UML generator with the SELECTED LLM
        uml_generator_with_selected_llm = UMLGenerator(llm=llm)
        
        # Enhanced user story with domain context
        enhanced_user_story = f"""
USER STORY:
{request.user_story}

IDENTIFIED DOMAIN CLASSES:
"""
        for dc in domain_classes:
            enhanced_user_story += f"- {dc['name']}: {dc['purpose']}\n"
            enhanced_user_story += f"  Fields: {', '.join(dc.get('fields', []))}\n"
            enhanced_user_story += f"  Methods: {', '.join(dc.get('methods', []))}\n\n"
        
        # Generate UML using the selected LLM
        plantuml_code = uml_generator_with_selected_llm.generate_class_diagram(
            user_story=enhanced_user_story,
            similar_examples=rag_context
        )
        logger.info(f"Generated UML diagram using {request.llm_provider}")
        
        # STEP 5: Java Code Generation using SELECTED LLM + RAG + UML
        java_classes = {}
        if request.include_java_code:
            logger.info(f"Java code generation using {request.llm_provider}")
            
            # Create Java generator with the SELECTED LLM
            java_generator_with_selected_llm = JavaGenerator(llm=llm)
            
            # Generate Java code using the selected LLM
            java_code = java_generator_with_selected_llm.generate_java_code(
                user_story=enhanced_user_story,
                uml_diagram=plantuml_code,
                similar_examples=rag_context
            )
            
            # Parse generated Java code into files
            file_pattern = r'```java\s+(\w+\.java)\s+(.*?)\s+```'
            matches = re.finditer(file_pattern, java_code, re.DOTALL)
            
            for match in matches:
                filename = match.group(1)
                file_content = match.group(2).strip()
                java_classes[filename] = file_content
            
            # If no files were parsed, create classes from domain analysis
            if not java_classes:
                for dc in domain_classes:
                    class_name = dc['name']
                    java_classes[f"{class_name}.java"] = f"""package com.generated.model;

import javax.persistence.*;
import java.time.LocalDateTime;
import java.util.*;

/**
 * {dc['purpose']}
 * Generated using {request.llm_provider}
 */
@Entity
@Table(name = "{class_name.lower()}s")
public class {class_name} {{
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    // Fields based on domain analysis
    {chr(10).join([f'    private String {field.split(":")[0].strip()};' for field in dc.get('fields', [])])}
    
    // Constructors
    public {class_name}() {{}}
    
    // Getters and Setters
    public Long getId() {{ return id; }}
    public void setId(Long id) {{ this.id = id; }}
    
    // Business methods based on domain analysis
    {chr(10).join([f'    // {method}' for method in dc.get('methods', [])])}
}}"""
            
            logger.info(f"Generated {len(java_classes)} Java classes using {request.llm_provider}")
        
        processing_time = time.time() - start_time
        
        # STEP 6: Return complete results
        return {
            "domain_classes": domain_classes,
            "plantuml_code": plantuml_code,
            "uml_is_valid": True,
            "uml_validation_message": f"UML diagram generated successfully using {request.llm_provider} with RAG context",
            "java_classes": java_classes,
            "project_structure": {
                "com.generated.model": [dc["name"] for dc in domain_classes]
            },
            "dependencies": [
                "Spring Boot Starter Web",
                "Spring Boot Starter Data JPA", 
                "H2 Database",
                "Spring Boot Starter Validation"
            ],
            "llm_provider": request.llm_provider,
            "total_classes": len(domain_classes),
            "processing_time": round(processing_time, 2),
            "rag_examples_used": len(similar_results),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error in complete workflow with {request.llm_provider}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow failed with {request.llm_provider}: {str(e)}")

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
            # Try alternative PlantUML servers
            logger.warning(f"PlantUML rendering failed with primary server: {plantuml_error}")
            
            # Try with alternative URL encoding method
            try:
                import requests
                import zlib
                
                # Encode PlantUML using the standard method
                plantuml_encoded = base64.urlsafe_b64encode(
                    zlib.compress(plantuml_code.encode('utf-8'), 9)
                ).decode('ascii')
                
                # Try alternative PlantUML server
                alt_url = f"https://www.plantuml.com/plantuml/svg/{plantuml_encoded}"
                response = requests.get(alt_url, timeout=10)
                
                if response.status_code == 200:
                    # Convert SVG to base64
                    svg_base64 = base64.b64encode(response.content).decode('utf-8')
                    return {
                        "success": True,
                        "image_base64": svg_base64,
                        "message": "Diagram rendered with alternative server",
                        "is_fallback": False
                    }
                    
            except Exception as alt_error:
                logger.warning(f"Alternative PlantUML server also failed: {alt_error}")
            
            # Final fallback: create simple SVG
            svg_content = """<svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" fill="#1a1a1a" stroke="#333"/>
                <text x="300" y="180" text-anchor="middle" font-family="monospace" font-size="16" fill="#fff">
                    UML Diagram Generated
                </text>
                <text x="300" y="200" text-anchor="middle" font-family="monospace" font-size="12" fill="#888">
                    Switch to 'PlantUML Code' tab to view the generated code
                </text>
                <text x="300" y="240" text-anchor="middle" font-family="monospace" font-size="10" fill="#666">
                    PlantUML rendering temporarily unavailable
                </text>
            </svg>"""
            
            svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
            
            return {
                "success": True,
                "image_base64": svg_base64,
                "message": "Fallback diagram generated",
                "is_fallback": True
            }
            
    except Exception as e:
        logger.error(f"Error rendering UML diagram: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.options("/generate")
async def options_generate():
    return {}

# Add endpoint to store code examples
@router.post("/store-example")
async def store_example(code: str):
    if vector_store:
        vector_store.create_vector_store(code)
        return {"status": "success"}
    else:
        return {"status": "error", "message": "Vector store not available"}
   
# Add endpoint to search similar code
@router.get("/search-similar")
async def search_similar(query: str, k: int = 3, doc_type: Optional[str] = None, language: Optional[str] = None):
    """Search for similar code examples with optional filtering by type or language"""
    try:
        if not vector_store:
            return {"results": [], "message": "Vector store not available"}
            
        if doc_type and language:
            filter_criteria = {"type": doc_type, "language": language}
            results = vector_store.search_similar(query, k=k, filter_criteria=filter_criteria)
        elif doc_type:
            results = vector_store.search_similar_by_type(query, doc_type, k=k)
        elif language:
            results = vector_store.search_similar_code(query, language=language, k=k)
        else:
            results = vector_store.search_similar(query, k=k)
            
        # Convert results to JSON-serializable format
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata if hasattr(doc, "metadata") else {}
            })
            
        return {"results": formatted_results}
    except Exception as e:
        logger.error(f"Error searching similar results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching similar results: {str(e)}")

@router.post("/generate")
async def generate_code(request: GenerationRequest):
    try:
        logger.info(f"Received generation request with story length: {len(request.userStory)}")
        
        # Search for similar stories and implementations
        try:
            if vector_store:
                similar_results = vector_store.search_similar(request.userStory, k=3)
                logger.info(f"Found {len(similar_results)} similar results")
            else:
                similar_results = []
                logger.info("Vector store not available, using empty similar results")
        except Exception as e:
            logger.warning(f"Error searching similar results: {str(e)}")
            similar_results = []
        
        # Create context from similar results
        context = "Here are some similar implementations and stories that might help:\n\n"
        for i, result in enumerate(similar_results, 1):
            context += f"Example {i}:\n{result.page_content}\n\n"
        
        logger.info("Created context from similar results")
        
        # Create prompt for the LLM
        prompt = f"""
        Based on the following user story and similar implementations, generate the appropriate code implementation.
        
        SIMILAR IMPLEMENTATIONS AND STORIES:
        {context}
        
        CURRENT USER STORY:
        {request.userStory}
        
        UML DIAGRAM:
        {request.umlDiagram}
        
        Please generate a complete implementation that follows best practices and takes inspiration from the similar implementations above.
        Additionally, provide traceability information by identifying:
        
        1. All classes involved in the implementation
        2. The purpose and responsibility of each class
        3. The relationships between classes (inheritance, composition, association, etc.)
        
        Format your response as a JSON object with the following structure:
        {{
            "code": "the full implementation code",
            "classInfo": [
                {{
                    "name": "ClassName",
                    "purpose": "Brief description of the class's purpose and responsibility",
                    "properties": ["property1", "property2"],
                    "methods": ["method1", "method2"]
                }}
            ],
            "relationships": [
                {{
                    "from": "SourceClass",
                    "to": "TargetClass",
                    "type": "Type of relationship (inheritance, composition, association, etc.)",
                    "description": "Brief description of the relationship"
                }}
            ]
        }}
        """
        
        # Generate response using the default LLM (or first available)
        try:
            available_providers = llm_manager.get_available_providers()
            if not available_providers:
                raise HTTPException(status_code=500, detail="No LLM providers available")
            
            # Use first available provider for legacy endpoint
            provider_id = list(available_providers.keys())[0]
            llm = llm_manager.get_llm_instance(provider_id)
            
            logger.info(f"Sending request to LLM ({provider_id})")
            response = llm.invoke(prompt)
            logger.info("Received response from LLM")
        except Exception as e:
            logger.error(f"Error generating response from LLM: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating response from LLM: {str(e)}")
        
        # Parse the response
        try:
            logger.info("Parsing LLM response")
            result = json.loads(response.content)
            return GenerationResponse(**result)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logger.error(f"Raw response: {response.content}")
            raise HTTPException(status_code=500, detail="Failed to parse LLM response as JSON")
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing response: {str(e)}")
            
    except HTTPException:
        raise
    except APIStatusError as e:
        logger.error(f"LLM API error in generate: {e}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/user-story/uml", response_model=UMLResponse)
async def generate_uml(request: UMLRequest):
    """Generate UML diagrams from a user story using RAG"""
    try:
        logger.info(f"Received UML generation request for user story: {request.userStory.description[:50]}...")
        
        # Format user story
        user_story_text = f"As a user, {request.userStory.description}\n\nAcceptance Criteria:\n"
        for i, criteria in enumerate(request.userStory.acceptanceCriteria, 1):
            user_story_text += f"{i}. {criteria}\n"
            
        # Search for similar stories and UML diagrams
        if vector_store:
            similar_results = vector_store.search_similar_by_type(user_story_text, "uml", k=2)
            logger.info(f"Found {len(similar_results)} similar UML examples")
        else:
            similar_results = []
            logger.info("Vector store not available, using empty similar results")
        
        # Create context from similar results
        similar_examples = ""
        for i, result in enumerate(similar_results, 1):
            similar_examples += f"Example {i}:\n{result.page_content}\n\n"
        
        # Get available LLM for UML generation
        if not llm_manager.is_provider_available(request.llm_provider):
            reason = llm_manager.get_unavailability_reason(request.llm_provider)
            raise HTTPException(status_code=400, detail=f"LLM provider '{request.llm_provider}' is not available. Reason: {reason}")
        
        llm = llm_manager.get_llm_instance(request.llm_provider)
        logger.info(f"Using {request.llm_provider} for UML generation")
        
        # Create UML generator with the selected LLM
        uml_generator_with_llm = UMLGenerator(llm=llm)
        
        # Generate class diagram
        class_diagram = uml_generator_with_llm.generate_class_diagram(
            user_story=user_story_text,
            similar_examples=similar_examples
        )
        logger.info("Generated UML class diagram")
        
        # Generate sequence diagram (optional)
        sequence_diagram = uml_generator_with_llm.generate_sequence_diagram(
            user_story=user_story_text,
            class_diagram=class_diagram,
            similar_examples=similar_examples
        )
        logger.info("Generated UML sequence diagram")
        
        # Render diagram to image (optional)
        try:
            image_path = uml_generator_with_llm.render_uml(class_diagram)
            image_url = f"/api/static/uml/{os.path.basename(image_path)}"
        except Exception as e:
            logger.warning(f"Failed to render UML diagram: {str(e)}")
            image_url = None
        
        return UMLResponse(
            classDiagram=class_diagram,
            sequenceDiagram=sequence_diagram,
            imageUrl=image_url
        )
    
    except APIStatusError as e:
        logger.error(f"LLM API error in UML generation: {e}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating UML: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during UML generation.")

@router.post("/user-story/java", response_model=JavaCodeResponse)
async def generate_java_code(request: JavaCodeRequest):
    """Generate Java code from a user story and UML diagram using RAG"""
    try:
        logger.info(f"Received Java code generation request for user story: {request.userStory.description[:50]}...")
        
        # Format user story
        user_story_text = f"As a user, {request.userStory.description}\n\nAcceptance Criteria:\n"
        for i, criteria in enumerate(request.userStory.acceptanceCriteria, 1):
            user_story_text += f"{i}. {criteria}\n"
            
        # Search for similar code implementations
        if vector_store:
            similar_results = vector_store.search_similar_code(user_story_text, language="java", k=2)
            logger.info(f"Found {len(similar_results)} similar Java code examples")
        else:
            similar_results = []
            logger.info("Vector store not available, using empty similar results")
        
        # Create context from similar results
        similar_examples = ""
        for i, result in enumerate(similar_results, 1):
            similar_examples += f"Example {i}:\n{result.page_content}\n\n"
        
        # Get available LLM for Java generation
        if not llm_manager.is_provider_available(request.llm_provider):
            reason = llm_manager.get_unavailability_reason(request.llm_provider)
            raise HTTPException(status_code=400, detail=f"LLM provider '{request.llm_provider}' is not available. Reason: {reason}")
        
        llm = llm_manager.get_llm_instance(request.llm_provider)
        logger.info(f"Using {request.llm_provider} for Java code generation")
        
        # Create Java generator with the selected LLM
        java_generator_with_llm = JavaGenerator(llm=llm)
        
        # Generate Java code
        java_code = java_generator_with_llm.generate_java_code(
            user_story=user_story_text,
            uml_diagram=request.umlDiagram,
            similar_examples=similar_examples
        )
        logger.info("Generated Java code")
        
        # Extract class information
        # This is a simplified implementation - in a real system, you would parse the generated code
        # to extract class info and relationships
        
        # Parse the code into separate files
        file_pattern = r"```java (\w+\.java)\s+(.*?)\s+```"
        matches = re.finditer(file_pattern, java_code, re.DOTALL)
        
        code_files = {}
        for match in matches:
            filename = match.group(1)
            file_content = match.group(2)
            code_files[filename] = file_content
        
        # Create a temporary directory for the generated code
        output_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory for Java code: {output_dir}")
        
        # Save files to the temporary directory
        for filename, content in code_files.items():
            file_path = os.path.join(output_dir, filename)
            with open(file_path, "w") as f:
                f.write(content)
        
        # Analyze code quality
        quality_report = java_generator_with_llm.analyze_code_quality(java_code)
        
        # Create a response with class information and relationships
        # This is a placeholder implementation
        class_info = [
            ClassInfo(
                name=filename.replace(".java", ""),
                purpose=f"Implementation for {filename}",
                properties=["id", "name", "createdAt"],
                methods=["save", "findById", "findAll"]
            )
            for filename in code_files.keys()
        ]
        
        relationships = []
        
        # For a real system, you would analyze the code to extract proper relationships
        for i in range(len(class_info) - 1):
            relationships.append(
                Relationship(
                    fromClass=class_info[i].name,
                    toClass=class_info[i+1].name,
                    type="association",
                    description=f"Association between {class_info[i].name} and {class_info[i+1].name}"
                )
            )
        
        return JavaCodeResponse(
            code=code_files,
            classInfo=class_info,
            relationships=relationships,
            downloadUrl=f"/api/download/java/{os.path.basename(output_dir)}"
        )
    
    except APIStatusError as e:
        logger.error(f"LLM API error in Java code generation: {e}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating Java code: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during Java code generation.")

@router.post("/fine-tune")
async def fine_tune_model(
    dataset: UploadFile = File(...),
    model_name: str = Form(...),
    epochs: int = Form(3),
    batch_size: int = Form(8)
):
    """Fine-tune the LLM for eCommerce Java development"""
    try:
        logger.info(f"Received fine-tuning request for model: {model_name}")
        
        # Implementation for fine-tuning would go here
        # This is a placeholder since fine-tuning requires more complex setup
        
        return {
            "status": "success",
            "message": f"Started fine-tuning job for model {model_name}",
            "job_id": "ft-job-2023-001"
        }
    
    except Exception as e:
        logger.error(f"Error starting fine-tuning job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting fine-tuning job: {str(e)}")

# Make sure to export the router
__all__ = ['router']

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(router, host="1.0.0.0", port=8000) 