import plantuml
import os
import tempfile
import re
from typing import List, Dict, Any, Optional
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from llm_manager import LLMManager, LLMProvider
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DomainClass:
    """Represents a domain class extracted from user story analysis."""
    
    def __init__(self, name: str, purpose: str, fields: List[str], methods: List[str]):
        self.name = name
        self.purpose = purpose
        self.fields = fields
        self.methods = methods
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "fields": self.fields,
            "methods": self.methods
        }

class EnhancedUMLGenerator:
    """Enhanced UML generator with improved workflow and multi-LLM support."""
    
    def __init__(self, plantuml_server="http://www.plantuml.com/plantuml"):
        self.plantuml = plantuml.PlantUML(url=plantuml_server)
        self.llm_manager = LLMManager()
        
        # Domain analysis prompt
        self.domain_analysis_template = PromptTemplate(
            input_variables=["user_story"],
            template="""
            You are an expert software architect specializing in domain-driven design for eCommerce applications.
            
            Analyze the following user story and extract the key domain concepts:
            
            USER STORY:
            {user_story}
            
            Your task:
            A. Parse the story and identify all domain nouns (entities, value objects, services)
            B. Propose up to 6 main classes that would be needed to implement this functionality
            C. For each class, define:
               - Class name (PascalCase)
               - Purpose/responsibility (one sentence)
               - Key fields/attributes (with data types)
               - Essential methods (with brief description)
            
            Focus on core business domain classes, not infrastructure concerns.
            Consider eCommerce patterns like: Product, Customer, Order, Payment, Inventory, etc.
            
            Output format - JSON array:
            [
              {{
                "name": "ClassName",
                "purpose": "Brief description of what this class represents and its responsibility",
                "fields": [
                  "id: Long",
                  "name: String",
                  "createdAt: LocalDateTime"
                ],
                "methods": [
                  "getId(): Long - Returns the unique identifier",
                  "setName(String name): void - Sets the name",
                  "isValid(): boolean - Validates the entity"
                ]
              }}
            ]
            
            Return ONLY the JSON array, no additional text.
            """
        )
        
        # PlantUML generation prompt
        self.plantuml_template = PromptTemplate(
            input_variables=["user_story", "domain_classes"],
            template="""
            You are an expert software architect. Generate a comprehensive PlantUML class diagram 
            for the following user story and domain classes.
            
            USER STORY:
            {user_story}
            
            DOMAIN CLASSES:
            {domain_classes}
            
            Create a PlantUML class diagram that:
            1. Includes all the provided domain classes
            2. Shows proper relationships between classes (association, aggregation, composition, inheritance)
            3. Includes multiplicity notation where appropriate
            4. Uses proper UML syntax and formatting
            5. Groups related classes using packages if beneficial
            6. Includes key methods and attributes for each class
            
            Follow these PlantUML best practices:
            - Use proper access modifiers (+, -, #, ~)
            - Include data types for attributes
            - Show method return types and parameters
            - Use meaningful relationship labels
            - Apply clean formatting and spacing
            
            Output ONLY valid PlantUML code enclosed between @startuml and @enduml tags.
            Do not include any explanation or comments outside the PlantUML code.
            
            Example structure:
            @startuml
            package "Domain Model" {{
                class ClassName {{
                    -id: Long
                    -name: String
                    +getId(): Long
                    +setName(name: String): void
                }}
            }}
            @enduml
            """
        )
    
    def analyze_domain(self, user_story: str, llm_provider: LLMProvider = LLMProvider.GPT_4O) -> List[DomainClass]:
        """
        Analyze user story and extract domain classes.
        
        Args:
            user_story: The user story to analyze
            llm_provider: The LLM provider to use
            
        Returns:
            List of DomainClass objects
        """
        try:
            llm = self.llm_manager.get_llm(llm_provider)
            if not llm:
                raise ValueError(f"LLM provider {llm_provider.value} not available")
            
            # Create chain
            chain = LLMChain(llm=llm, prompt=self.domain_analysis_template)
            
            # Generate domain analysis
            result = chain.run(user_story=user_story)
            logger.info(f"Domain analysis result: {result[:200]}...")
            
            # Parse JSON response
            import json
            try:
                classes_data = json.loads(result.strip())
                domain_classes = []
                
                for class_data in classes_data[:6]:  # Limit to 6 classes
                    domain_class = DomainClass(
                        name=class_data.get("name", "UnknownClass"),
                        purpose=class_data.get("purpose", ""),
                        fields=class_data.get("fields", []),
                        methods=class_data.get("methods", [])
                    )
                    domain_classes.append(domain_class)
                
                logger.info(f"Extracted {len(domain_classes)} domain classes")
                return domain_classes
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {result}")
                # Fallback: create a single generic class
                return [DomainClass(
                    name="GeneratedClass",
                    purpose="Main class for the user story functionality",
                    fields=["id: Long", "name: String"],
                    methods=["getId(): Long", "getName(): String"]
                )]
                
        except Exception as e:
            logger.error(f"Error in domain analysis: {e}")
            raise
    
    def generate_plantuml_diagram(self, user_story: str, domain_classes: List[DomainClass], 
                                 llm_provider: LLMProvider = LLMProvider.GPT_4O) -> str:
        """
        Generate PlantUML class diagram from domain classes.
        
        Args:
            user_story: The original user story
            domain_classes: List of domain classes
            llm_provider: The LLM provider to use
            
        Returns:
            PlantUML diagram code
        """
        try:
            llm = self.llm_manager.get_llm(llm_provider)
            if not llm:
                raise ValueError(f"LLM provider {llm_provider.value} not available")
            
            # Format domain classes for the prompt
            classes_text = ""
            for i, domain_class in enumerate(domain_classes, 1):
                classes_text += f"Class {i}: {domain_class.name}\n"
                classes_text += f"Purpose: {domain_class.purpose}\n"
                classes_text += f"Fields: {', '.join(domain_class.fields)}\n"
                classes_text += f"Methods: {', '.join(domain_class.methods)}\n\n"
            
            # Create chain
            chain = LLMChain(llm=llm, prompt=self.plantuml_template)
            
            # Generate PlantUML
            result = chain.run(user_story=user_story, domain_classes=classes_text)
            
            # Clean up result
            result = result.strip()
            if not result.startswith("@startuml"):
                result = "@startuml\n" + result
            if not result.endswith("@enduml"):
                result = result + "\n@enduml"
            
            logger.info("PlantUML diagram generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error generating PlantUML diagram: {e}")
            raise
    
    def generate_complete_analysis(self, user_story: str, 
                                 llm_provider: LLMProvider = LLMProvider.GPT_4O) -> Dict[str, Any]:
        """
        Complete workflow: analyze domain and generate PlantUML diagram.
        
        Args:
            user_story: The user story to process
            llm_provider: The LLM provider to use
            
        Returns:
            Dictionary containing domain classes and PlantUML diagram
        """
        try:
            # Step 1: Analyze domain and extract classes
            logger.info("Starting domain analysis...")
            domain_classes = self.analyze_domain(user_story, llm_provider)
            
            # Step 2: Generate PlantUML diagram
            logger.info("Generating PlantUML diagram...")
            plantuml_code = self.generate_plantuml_diagram(user_story, domain_classes, llm_provider)
            
            # Step 3: Validate PlantUML
            is_valid, validation_message = self.validate_uml(plantuml_code)
            if not is_valid:
                logger.warning(f"PlantUML validation warning: {validation_message}")
            
            return {
                "domain_classes": [dc.to_dict() for dc in domain_classes],
                "plantuml_code": plantuml_code,
                "is_valid": is_valid,
                "validation_message": validation_message,
                "llm_provider": llm_provider.value
            }
            
        except Exception as e:
            logger.error(f"Error in complete analysis: {e}")
            raise
    
    def render_uml(self, uml_code: str, output_path: Optional[str] = None) -> str:
        """Render PlantUML code to an image file."""
        try:
            if not output_path:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    output_path = tmp.name
            
            self.plantuml.processes(uml_code, outfile=output_path)
            logger.info(f"UML diagram rendered to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error rendering UML: {e}")
            raise
    
    def validate_uml(self, uml_code: str) -> tuple[bool, str]:
        """Validate PlantUML code syntax."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.png') as tmp:
                self.plantuml.processes(uml_code, outfile=tmp.name)
            return True, "UML diagram is valid"
        except Exception as e:
            return False, f"UML validation failed: {str(e)}"
    
    def get_available_llms(self) -> Dict[str, str]:
        """Get available LLM providers."""
        return self.llm_manager.get_available_providers() 