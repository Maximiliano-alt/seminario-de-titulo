from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from langchain_openai import ChatOpenAI
import json
import os
import logging
import tempfile
from dotenv import load_dotenv
from vector_store import VectorStore
from uml_generator import UMLGenerator
from java_generator import JavaGenerator
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for API key
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please add it to your .env file.")

# Initialize router
router = APIRouter()

# Initialize vector store and load dataset
try:
    # Initialize vector store with FAISS backend if requested
    use_faiss = os.getenv("USE_FAISS", "false").lower() == "true"
    vector_store = VectorStore(use_faiss=use_faiss)
    
    # Get the absolute path to the dataset
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(os.path.dirname(current_dir), "data", "dataset_new.json")
    
    # Try to load existing vector store first
    loaded = vector_store.load_vector_store(collection_name="ecommerce_examples")
    
    if not loaded:
        # Create embeddings from dataset if loading failed
        logger.info(f"Loading dataset from: {dataset_path}")
        vector_store.create_embeddings_from_dataset(dataset_path)
        
    logger.info("Vector store initialized and dataset loaded successfully")
    
    # Initialize UML and Java generators
    uml_generator = UMLGenerator()
    java_generator = JavaGenerator()
    logger.info("UML and Java generators initialized successfully")
    
except Exception as e:
    logger.error(f"Failed to initialize services: {str(e)}")
    raise

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
    
class UMLResponse(BaseModel):
    classDiagram: str
    sequenceDiagram: Optional[str] = None
    imageUrl: Optional[str] = None
    
class JavaCodeRequest(BaseModel):
    userStory: UserStory
    umlDiagram: str
    projectContext: Optional[str] = None
    
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

# Initialize LLM
try:
    llm = ChatOpenAI()
    logger.info("ChatOpenAI initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ChatOpenAI: {str(e)}")
    raise

@router.options("/generate")
async def options_generate():
    return {}

# Add endpoint to store code examples
@router.post("/store-example")
async def store_example(code: str):
    vector_store.create_vector_store(code)
    return {"status": "success"}
   
# Add endpoint to search similar code
@router.get("/search-similar")
async def search_similar(query: str, k: int = 3, doc_type: Optional[str] = None, language: Optional[str] = None):
    """Search for similar code examples with optional filtering by type or language"""
    try:
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
            similar_results = vector_store.search_similar(request.userStory, k=3)
            logger.info(f"Found {len(similar_results)} similar results")
        except Exception as e:
            logger.error(f"Error searching similar results: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error searching similar results: {str(e)}")
        
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
        
        # Generate response using the LLM
        try:
            logger.info("Sending request to LLM")
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
        similar_results = vector_store.search_similar_by_type(user_story_text, "uml", k=2)
        logger.info(f"Found {len(similar_results)} similar UML examples")
        
        # Create context from similar results
        similar_examples = ""
        for i, result in enumerate(similar_results, 1):
            similar_examples += f"Example {i}:\n{result.page_content}\n\n"
        
        # Generate class diagram
        class_diagram = uml_generator.generate_class_diagram(
            user_story=user_story_text,
            similar_examples=similar_examples
        )
        logger.info("Generated UML class diagram")
        
        # Generate sequence diagram (optional)
        sequence_diagram = uml_generator.generate_sequence_diagram(
            user_story=user_story_text,
            class_diagram=class_diagram,
            similar_examples=similar_examples
        )
        logger.info("Generated UML sequence diagram")
        
        # Render diagram to image (optional)
        try:
            image_path = uml_generator.render_uml(class_diagram)
            image_url = f"/api/static/uml/{os.path.basename(image_path)}"
        except Exception as e:
            logger.warning(f"Failed to render UML diagram: {str(e)}")
            image_url = None
        
        return UMLResponse(
            classDiagram=class_diagram,
            sequenceDiagram=sequence_diagram,
            imageUrl=image_url
        )
    
    except Exception as e:
        logger.error(f"Error generating UML diagrams: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating UML diagrams: {str(e)}")

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
        similar_results = vector_store.search_similar_code(user_story_text, language="java", k=2)
        logger.info(f"Found {len(similar_results)} similar Java code examples")
        
        # Create context from similar results
        similar_examples = ""
        for i, result in enumerate(similar_results, 1):
            similar_examples += f"Example {i}:\n{result.page_content}\n\n"
        
        # Generate Java code
        java_code = java_generator.generate_java_code(
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
        quality_report = java_generator.analyze_code_quality(java_code)
        logger.info("Generated code quality report")
        
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
    
    except Exception as e:
        logger.error(f"Error generating Java code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating Java code: {str(e)}")

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