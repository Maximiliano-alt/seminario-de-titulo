import os
import re
import tempfile
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from jinja2 import Template
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class JavaGenerator:
    def __init__(self):
        """Initialize the Java code generator."""
        # Check for API key
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is not set. Please add it to your .env file.")
        
        # Initialize LLM
        self.llm = ChatOpenAI(temperature=0.2, model="gpt-4")
        
        # Define prompt templates
        self.java_code_template = PromptTemplate(
            input_variables=["user_story", "uml_diagram", "similar_examples"],
            template="""
            You are an expert Java developer specializing in eCommerce applications.
            Based on the following user story and UML diagram, generate Java code that 
            implements the required functionality following industry best practices.
            
            USER STORY:
            {user_story}
            
            UML DIAGRAM:
            {uml_diagram}
            
            SIMILAR EXAMPLES:
            {similar_examples}
            
            Generate complete, well-structured Java code for all classes in the UML diagram:
            1. Include proper package structure (use com.ecommerce as the base package)
            2. Follow proper naming conventions and Java best practices
            3. Implement all attributes and methods shown in the UML
            4. Add appropriate annotations for Spring Boot if applicable
            5. Include proper imports
            6. Add comprehensive documentation with JavaDoc
            7. Implement appropriate design patterns where relevant
            
            Organize the code using a typical eCommerce layered architecture:
            - Domain/entity classes
            - Repository interfaces
            - Service interfaces and implementations
            - Controller classes (if applicable)
            
            For each class, wrap the code in ```java [className].java and ``` tags.
            """
        )
        
        # Java class templates
        self.entity_template = Template("""package com.ecommerce.domain;

import java.util.*;
import jakarta.persistence.*;
import lombok.Data;

/**
 * {{ class_doc }}
 */
@Entity
@Data
public class {{ class_name }} {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private {{ id_type }} id;
    
    {% for attribute in attributes %}
    {% if attribute.annotation %}{{ attribute.annotation }}{% endif %}
    private {{ attribute.type }} {{ attribute.name }};
    {% endfor %}
    
    {% for relationship in relationships %}
    {% if relationship.annotation %}{{ relationship.annotation }}{% endif %}
    private {{ relationship.type }} {{ relationship.name }};
    {% endfor %}
    
    {% for method in methods %}
    /**
     * {{ method.doc }}
     */
    public {{ method.return_type }} {{ method.name }}({% for param in method.params %}{{ param.type }} {{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %}) {
        {{ method.body }}
    }
    {% endfor %}
}
""")
        
        self.repository_template = Template("""package com.ecommerce.repository;

import com.ecommerce.domain.{{ domain_class }};
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.*;

/**
 * Repository interface for {{ domain_class }} entities
 */
@Repository
public interface {{ class_name }} extends JpaRepository<{{ domain_class }}, {{ id_type }}> {
    {% for method in methods %}
    /**
     * {{ method.doc }}
     */
    {{ method.return_type }} {{ method.name }}({% for param in method.params %}{{ param.type }} {{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %});
    {% endfor %}
}
""")
        
        self.service_interface_template = Template("""package com.ecommerce.service;

import com.ecommerce.domain.{{ domain_class }};
import java.util.*;

/**
 * Service interface for {{ domain_class }} operations
 */
public interface {{ class_name }} {
    {% for method in methods %}
    /**
     * {{ method.doc }}
     */
    {{ method.return_type }} {{ method.name }}({% for param in method.params %}{{ param.type }} {{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %});
    {% endfor %}
}
""")
        
        self.service_impl_template = Template("""package com.ecommerce.service.impl;

import com.ecommerce.domain.{{ domain_class }};
import com.ecommerce.repository.{{ repository_name }};
import com.ecommerce.service.{{ service_interface }};
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.*;

/**
 * Implementation of the {{ service_interface }} interface
 */
@Service
@Transactional
public class {{ class_name }} implements {{ service_interface }} {

    private final {{ repository_name }} repository;
    
    @Autowired
    public {{ class_name }}({{ repository_name }} repository) {
        this.repository = repository;
    }
    
    {% for method in methods %}
    /**
     * {{ method.doc }}
     */
    @Override
    public {{ method.return_type }} {{ method.name }}({% for param in method.params %}{{ param.type }} {{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %}) {
        {{ method.body }}
    }
    {% endfor %}
}
""")
        
        self.controller_template = Template("""package com.ecommerce.controller;

import com.ecommerce.domain.{{ domain_class }};
import com.ecommerce.service.{{ service_interface }};
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.util.*;

/**
 * REST controller for {{ domain_class }} operations
 */
@RestController
@RequestMapping("/api/{{ api_path }}")
public class {{ class_name }} {

    private final {{ service_interface }} service;
    
    @Autowired
    public {{ class_name }}({{ service_interface }} service) {
        this.service = service;
    }
    
    {% for endpoint in endpoints %}
    /**
     * {{ endpoint.doc }}
     */
    @{{ endpoint.method }}("{{ endpoint.path }}")
    public {{ endpoint.return_type }} {{ endpoint.name }}(
        {% for param in endpoint.params %}@{{ param.annotation }} {{ param.type }} {{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %}
    ) {
        {{ endpoint.body }}
    }
    {% endfor %}
}
""")

    def _extract_class_info_from_uml(self, uml_diagram):
        """Extract class names, attributes, and relationships from UML diagram."""
        class_info = {}
        
        # Extract class definitions
        class_matches = re.finditer(r'class\s+(\w+)(\s+.*?)?\s*\{([^}]*)\}', uml_diagram, re.DOTALL)
        
        for match in class_matches:
            class_name = match.group(1)
            attributes_section = match.group(3)
            
            # Process attributes
            attributes = []
            for line in attributes_section.split('\n'):
                line = line.strip()
                if line and ':' in line:
                    # Handle attributes like "+ title: String"
                    visibility, attr_info = line[0], line[1:].strip()
                    attr_parts = attr_info.split(':', 1)
                    attr_name = attr_parts[0].strip()
                    attr_type = attr_parts[1].strip() if len(attr_parts) > 1 else "String"
                    
                    attributes.append({
                        "name": attr_name,
                        "type": attr_type,
                        "visibility": visibility
                    })
            
            class_info[class_name] = {
                "name": class_name,
                "attributes": attributes,
                "relationships": []
            }
        
        # Extract relationships
        relationship_matches = re.finditer(r'(\w+)\s+"(\w+)"\s+--\s+"(\w+)"\s+(\w+)', uml_diagram)
        
        for match in relationship_matches:
            source_class = match.group(1)
            multiplicity_source = match.group(2)
            multiplicity_target = match.group(3)
            target_class = match.group(4)
            
            if source_class in class_info:
                class_info[source_class]["relationships"].append({
                    "target": target_class,
                    "multiplicity": multiplicity_target,
                    "type": self._determine_relationship_type(multiplicity_source, multiplicity_target)
                })
        
        return class_info
    
    def _determine_relationship_type(self, source_mult, target_mult):
        """Determine the type of relationship based on multiplicities."""
        if target_mult == "1" and source_mult == "1":
            return "OneToOne"
        elif target_mult == "*" and source_mult == "1":
            return "OneToMany"
        elif target_mult == "*" and source_mult == "*":
            return "ManyToMany"
        elif target_mult == "1" and source_mult == "*":
            return "ManyToOne"
        else:
            return "Association"

    def generate_java_code(self, user_story, uml_diagram, similar_examples=""):
        """Generate Java code from a user story and UML diagram."""
        # Create chain
        chain = LLMChain(llm=self.llm, prompt=self.java_code_template)
        
        # Generate Java code
        result = chain.run(
            user_story=user_story,
            uml_diagram=uml_diagram,
            similar_examples=similar_examples
        )
        
        return result
    
    def generate_structured_java_code(self, user_story, uml_diagram, output_dir=None):
        """Generate structured Java code files from a user story and UML diagram."""
        # Extract class information from UML
        class_info = self._extract_class_info_from_uml(uml_diagram)
        
        # Create output directory if specified
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        else:
            output_dir = tempfile.mkdtemp()
        
        # Create directory structure
        for package in ["domain", "repository", "service", "service/impl", "controller"]:
            os.makedirs(os.path.join(output_dir, "com/ecommerce", package), exist_ok=True)
        
        # Generate code for each class
        generated_files = []
        
        for class_name, info in class_info.items():
            # Generate entity class
            entity_code = self.entity_template.render(
                class_name=class_name,
                class_doc=f"Entity class for {class_name}",
                id_type="Long",
                attributes=info["attributes"],
                relationships=info["relationships"],
                methods=[]  # Simplified for this example
            )
            
            entity_path = os.path.join(output_dir, f"com/ecommerce/domain/{class_name}.java")
            with open(entity_path, "w") as f:
                f.write(entity_code)
            generated_files.append(entity_path)
            
            # Generate repository interface
            repo_name = f"{class_name}Repository"
            repo_code = self.repository_template.render(
                class_name=repo_name,
                domain_class=class_name,
                id_type="Long",
                methods=[
                    {
                        "doc": f"Find {class_name} by a specific attribute",
                        "return_type": f"Optional<{class_name}>",
                        "name": f"findBy{class_name}Name",
                        "params": [{"type": "String", "name": "name"}]
                    }
                ]
            )
            
            repo_path = os.path.join(output_dir, f"com/ecommerce/repository/{repo_name}.java")
            with open(repo_path, "w") as f:
                f.write(repo_code)
            generated_files.append(repo_path)
            
            # Generate service interface
            service_name = f"{class_name}Service"
            service_code = self.service_interface_template.render(
                class_name=service_name,
                domain_class=class_name,
                methods=[
                    {
                        "doc": f"Get all {class_name}s",
                        "return_type": f"List<{class_name}>",
                        "name": f"getAll{class_name}s",
                        "params": []
                    },
                    {
                        "doc": f"Get {class_name} by id",
                        "return_type": f"Optional<{class_name}>",
                        "name": f"get{class_name}ById",
                        "params": [{"type": "Long", "name": "id"}]
                    },
                    {
                        "doc": f"Save {class_name}",
                        "return_type": f"{class_name}",
                        "name": f"save{class_name}",
                        "params": [{"type": f"{class_name}", "name": f"{class_name.lower()}"}]
                    }
                ]
            )
            
            service_path = os.path.join(output_dir, f"com/ecommerce/service/{service_name}.java")
            with open(service_path, "w") as f:
                f.write(service_code)
            generated_files.append(service_path)
            
            # Generate service implementation
            impl_name = f"{class_name}ServiceImpl"
            impl_code = self.service_impl_template.render(
                class_name=impl_name,
                domain_class=class_name,
                repository_name=repo_name,
                service_interface=service_name,
                methods=[
                    {
                        "doc": f"Get all {class_name}s",
                        "return_type": f"List<{class_name}>",
                        "name": f"getAll{class_name}s",
                        "params": [],
                        "body": f"return repository.findAll();"
                    },
                    {
                        "doc": f"Get {class_name} by id",
                        "return_type": f"Optional<{class_name}>",
                        "name": f"get{class_name}ById",
                        "params": [{"type": "Long", "name": "id"}],
                        "body": f"return repository.findById(id);"
                    },
                    {
                        "doc": f"Save {class_name}",
                        "return_type": f"{class_name}",
                        "name": f"save{class_name}",
                        "params": [{"type": f"{class_name}", "name": f"{class_name.lower()}"}],
                        "body": f"return repository.save({class_name.lower()});"
                    }
                ]
            )
            
            impl_path = os.path.join(output_dir, f"com/ecommerce/service/impl/{impl_name}.java")
            with open(impl_path, "w") as f:
                f.write(impl_code)
            generated_files.append(impl_path)
            
            # Generate controller
            controller_name = f"{class_name}Controller"
            snake_case = ''.join(['_' + i.lower() if i.isupper() else i.lower() for i in class_name]).lstrip('_')
            
            controller_code = self.controller_template.render(
                class_name=controller_name,
                domain_class=class_name,
                service_interface=service_name,
                api_path=snake_case.replace('_', '-'),
                endpoints=[
                    {
                        "doc": f"Get all {class_name}s",
                        "method": "GetMapping",
                        "path": "/",
                        "return_type": f"ResponseEntity<List<{class_name}>>",
                        "name": f"getAll{class_name}s",
                        "params": [],
                        "body": f"return ResponseEntity.ok(service.getAll{class_name}s());"
                    },
                    {
                        "doc": f"Get a {class_name} by id",
                        "method": "GetMapping",
                        "path": "/{id}",
                        "return_type": f"ResponseEntity<{class_name}>",
                        "name": f"get{class_name}ById",
                        "params": [{"annotation": "PathVariable", "type": "Long", "name": "id"}],
                        "body": f"return service.get{class_name}ById(id)\n                .map(ResponseEntity::ok)\n                .orElse(ResponseEntity.notFound().build());"
                    },
                    {
                        "doc": f"Create a new {class_name}",
                        "method": "PostMapping",
                        "path": "/",
                        "return_type": f"ResponseEntity<{class_name}>",
                        "name": f"create{class_name}",
                        "params": [{"annotation": "RequestBody", "type": f"{class_name}", "name": f"{class_name.lower()}"}],
                        "body": f"return ResponseEntity.ok(service.save{class_name}({class_name.lower()}));"
                    }
                ]
            )
            
            controller_path = os.path.join(output_dir, f"com/ecommerce/controller/{controller_name}.java")
            with open(controller_path, "w") as f:
                f.write(controller_code)
            generated_files.append(controller_path)
        
        return generated_files
    
    def analyze_code_quality(self, java_code):
        """Analyze Java code for quality metrics."""
        quality_prompt = PromptTemplate(
            input_variables=["java_code"],
            template="""
            You are a senior Java code reviewer specializing in eCommerce applications.
            Review the following Java code and provide quality metrics and suggestions for improvement.
            
            JAVA CODE:
            {java_code}
            
            Please analyze the code for:
            1. Code structure and organization
            2. Design patterns usage
            3. Adherence to Java best practices
            4. Potential bugs or code smells
            5. Performance considerations
            
            Provide a quality score from 1-10 for each category and specific recommendations for improvement.
            Format your response as valid JSON with the following structure:
            {{
                "overall_score": 0,
                "categories": [
                    {{
                        "name": "Code structure",
                        "score": 0,
                        "comments": ""
                    }},
                    // other categories
                ],
                "recommendations": [
                    "Recommendation 1",
                    "Recommendation 2"
                ]
            }}
            """
        )
        
        # Create chain and run
        chain = LLMChain(llm=self.llm, prompt=quality_prompt)
        result = chain.run(java_code=java_code)
        
        return result 