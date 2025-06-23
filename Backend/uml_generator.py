import plantuml
import os
import tempfile
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class UMLGenerator:
    def __init__(self, plantuml_server="http://www.plantuml.com/plantuml", llm=None):
        """Initialize the UML generator with a PlantUML server URL and optional LLM instance."""
        self.plantuml = plantuml.PlantUML(url=plantuml_server)
        
        # Use provided LLM or fallback to OpenAI
        if llm is not None:
            self.llm = llm
        else:
            # Check for API key
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY environment variable is not set. Please add it to your .env file.")
            
            # Initialize LLM
            self.llm = ChatOpenAI(temperature=0.2, model="gpt-4")
        
        # Define prompt templates
        self.uml_class_diagram_template = PromptTemplate(
            input_variables=["user_story", "similar_examples"],
            template="""
            You are an expert software architect specializing in eCommerce applications using Java.
            Based on the following user story, generate a PlantUML class diagram that follows
            best practices for Java eCommerce applications.
            
            USER STORY:
            {user_story}
            
            SIMILAR EXAMPLES:
            {similar_examples}
            
            Create a comprehensive PlantUML class diagram with:
            1. All necessary classes to implement this user story
            2. Appropriate attributes for each class (include data types)
            3. Methods that would be required
            4. Proper relationships between classes (association, aggregation, composition, inheritance)
            5. Proper multiplicity notation (1, *, 1..*, etc.)
            
            Each class should follow Java best practices. Include:
            - Data encapsulation
            - Proper layering (model, repository, service, controller)
            - Clear separation of concerns
            
            ONLY output valid PlantUML code enclosed between @startuml and @enduml tags.
            Do not include any explanation or comments outside the PlantUML code.
            """
        )
        
        self.uml_sequence_diagram_template = PromptTemplate(
            input_variables=["user_story", "class_diagram", "similar_examples"],
            template="""
            You are an expert software architect specializing in eCommerce applications using Java.
            Based on the following user story and class diagram, generate a PlantUML sequence diagram
            that illustrates the interaction flow between components.
            
            USER STORY:
            {user_story}
            
            CLASS DIAGRAM:
            {class_diagram}
            
            SIMILAR EXAMPLES:
            {similar_examples}
            
            Create a detailed PlantUML sequence diagram that:
            1. Shows the interaction between all relevant objects/components
            2. Follows the logical flow of operations needed to fulfill the user story
            3. Includes all method calls, returns, and data exchanges
            4. Demonstrates typical eCommerce patterns for this scenario
            
            ONLY output valid PlantUML code enclosed between @startuml and @enduml tags.
            Do not include any explanation or comments outside the PlantUML code.
            """
        )
    
    def generate_class_diagram(self, user_story, similar_examples=""):
        """Generate a PlantUML class diagram from a user story."""
        # Create chain
        chain = LLMChain(llm=self.llm, prompt=self.uml_class_diagram_template)
        
        # Generate UML
        result = chain.run(user_story=user_story, similar_examples=similar_examples)
        
        # Clean up result and remove any existing PlantUML tags to avoid duplicates
        result = result.strip()
        
        # Remove existing @startuml and @enduml tags if present
        if result.startswith("@startuml"):
            result = result[9:].strip()
        if result.endswith("@enduml"):
            result = result[:-7].strip()
        
        # Remove any markdown code blocks
        import re
        result = re.sub(r'```plantuml\s*', '', result)
        result = re.sub(r'```\s*', '', result)
        
        # Add clean PlantUML tags
        result = "@startuml\n" + result + "\n@enduml"
            
        return result
    
    def generate_sequence_diagram(self, user_story, class_diagram, similar_examples=""):
        """Generate a PlantUML sequence diagram from a user story and class diagram."""
        # Create chain
        chain = LLMChain(llm=self.llm, prompt=self.uml_sequence_diagram_template)
        
        # Generate UML
        result = chain.run(
            user_story=user_story,
            class_diagram=class_diagram,
            similar_examples=similar_examples
        )
        
        # Clean up result and remove any existing PlantUML tags to avoid duplicates
        result = result.strip()
        
        # Remove existing @startuml and @enduml tags if present
        if result.startswith("@startuml"):
            result = result[9:].strip()
        if result.endswith("@enduml"):
            result = result[:-7].strip()
        
        # Remove any markdown code blocks
        import re
        result = re.sub(r'```plantuml\s*', '', result)
        result = re.sub(r'```\s*', '', result)
        
        # Add clean PlantUML tags
        result = "@startuml\n" + result + "\n@enduml"
            
        return result
    
    def render_uml(self, uml_code, output_path=None):
        """Render PlantUML code to an image file or return the image data."""
        # Create temp file if no output path specified
        if not output_path:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                output_path = tmp.name
        
        # Generate the UML diagram
        self.plantuml.processes(uml_code, outfile=output_path)
        
        return output_path
    
    def validate_uml(self, uml_code):
        """Validate if the PlantUML code is syntactically correct."""
        try:
            # Try to process the UML to check for syntax errors
            with tempfile.NamedTemporaryFile(suffix='.png') as tmp:
                self.plantuml.processes(uml_code, outfile=tmp.name)
            return True, "UML diagram is valid"
        except Exception as e:
            return False, f"UML diagram validation failed: {str(e)}" 