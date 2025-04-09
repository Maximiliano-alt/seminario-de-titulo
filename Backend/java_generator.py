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
            
            Generate complete, production-ready Java code for all classes in the UML diagram following these requirements:
            
            1. PACKAGE STRUCTURE:
               - Use com.ecommerce as the base package
               - Organize in domain, dto, repository, service, service.impl, controller packages
            
            2. PROPER ANNOTATIONS:
               - Use @Entity, @Table for domain classes
               - Include @Id, @GeneratedValue for primary keys
               - Add appropriate relationship annotations (@OneToMany, @ManyToOne, etc.)
               - Use @Repository, @Service, @RestController for respective components
               - Include validation annotations (@NotNull, @Size, etc.) where appropriate
            
            3. COMPLETE IMPLEMENTATIONS:
               - Provide full method bodies, not just comments
               - Properly initialize relationships between objects
               - Include business logic in service implementations
            
            4. ACCESS MODIFIERS AND ENCAPSULATION:
               - All class attributes must be private
               - Provide proper getters and setters
               - Use Lombok annotations where appropriate (@Data, @AllArgsConstructor, etc.)
            
            5. BEST PRACTICES:
               - Include default and parameterized constructors
               - Implement equals, hashCode, and toString methods
               - Follow SOLID principles
               - Use proper exception handling
               - Include data validation logic
               - Implement DTO pattern for controller layer
            
            6. COMPREHENSIVE DOCUMENTATION:
               - Add JavaDoc for all classes and methods
               - Include meaningful comments for complex logic
            
            For each class, wrap the code in ```java [className].java and ``` tags.
            """
        )
        
        # Java class templates
        self.entity_template = Template("""package com.ecommerce.domain;

import java.util.*;
import java.time.LocalDateTime;
import java.math.BigDecimal;
import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.EqualsAndHashCode;

/**
 * {{ class_doc }}
 */
@Entity
@Table(name = "{{ table_name }}")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@EqualsAndHashCode(of = {"id"})
public class {{ class_name }} {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private {{ id_type }} id;
    
    {% for attribute in attributes %}
    {% if attribute.validation %}{{ attribute.validation }}{% endif %}
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
     {% for param in method.params %}
     * @param {{ param.name }} {{ param.description }}
     {% endfor %}
     {% if method.return_type != "void" %}
     * @return {{ method.return_description }}
     {% endif %}
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
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.*;

/**
 * Repository interface for {{ domain_class }} entities.
 * Provides database operations for the {{ domain_class }} domain object.
 */
@Repository
public interface {{ class_name }} extends JpaRepository<{{ domain_class }}, {{ id_type }}> {
    {% for method in methods %}
    /**
     * {{ method.doc }}
     {% for param in method.params %}
     * @param {{ param.name }} {{ param.description|default(param.name) }}
     {% endfor %}
     * @return {{ method.return_description|default("the result of the query") }}
     */
    {{ method.return_type }} {{ method.name }}({% for param in method.params %}{{ param.type }} {{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %});
    {% endfor %}
}
""")
        
        self.service_interface_template = Template("""package com.ecommerce.service;

import com.ecommerce.domain.{{ domain_class }};
import com.ecommerce.dto.{{ domain_class }}DTO;
import java.util.*;

/**
 * Service interface for {{ domain_class }} operations.
 * Defines the business operations available for {{ domain_class }} entities.
 */
public interface {{ class_name }} {
    {% for method in methods %}
    /**
     * {{ method.doc }}
     {% for param in method.params %}
     * @param {{ param.name }} {{ param.description|default(param.name) }}
     {% endfor %}
     {% if method.return_type != "void" %}
     * @return {{ method.return_description|default("the result of the operation") }}
     {% endif %}
     {% if method.exceptions %}
     {% for exception in method.exceptions %}
     * @throws {{ exception.type }} {{ exception.description }}
     {% endfor %}
     {% endif %}
     */
    {{ method.return_type }} {{ method.name }}({% for param in method.params %}{{ param.type }} {{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %});
    {% endfor %}
}
""")
        
        self.service_impl_template = Template("""package com.ecommerce.service.impl;

import com.ecommerce.domain.{{ domain_class }};
import com.ecommerce.dto.{{ domain_class }}DTO;
import com.ecommerce.repository.{{ repository_name }};
import com.ecommerce.service.{{ service_interface }};
import com.ecommerce.exception.ResourceNotFoundException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.*;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;

/**
 * Implementation of the {{ service_interface }} interface.
 * Provides the business logic for {{ domain_class }} operations.
 */
@Service
@Transactional
@Slf4j
public class {{ class_name }} implements {{ service_interface }} {

    private final {{ repository_name }} repository;
    
    /**
     * Constructs a new {{ class_name }} with the required dependencies.
     * 
     * @param repository the {{ repository_name }} used for data access
     */
    @Autowired
    public {{ class_name }}({{ repository_name }} repository) {
        this.repository = repository;
    }
    
    {% for method in methods %}
    /**
     * {{ method.doc }}
     {% for param in method.params %}
     * @param {{ param.name }} {{ param.description|default(param.name) }}
     {% endfor %}
     {% if method.return_type != "void" %}
     * @return {{ method.return_description|default("the result of the operation") }}
     {% endif %}
     {% if method.exceptions %}
     {% for exception in method.exceptions %}
     * @throws {{ exception.type }} {{ exception.description }}
     {% endfor %}
     {% endif %}
     */
    @Override
    {% if method.transactional %}
    @Transactional({% if method.transactional_args %}{{ method.transactional_args }}{% endif %})
    {% endif %}
    public {{ method.return_type }} {{ method.name }}({% for param in method.params %}{{ param.type }} {{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %}) {
        {% if method.logging %}
        log.debug("{{ method.logging }}", {% for param in method.log_params %}{{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %});
        {% endif %}
        {{ method.body }}
    }
    {% endfor %}
}
""")
        
        # Update controller template with better practices
        self.controller_template = Template("""package com.ecommerce.controller;

import com.ecommerce.domain.{{ domain_class }};
import com.ecommerce.dto.{{ domain_class }}DTO;
import com.ecommerce.service.{{ service_interface }};
import com.ecommerce.exception.ResourceNotFoundException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import jakarta.validation.Valid;
import java.util.*;
import lombok.extern.slf4j.Slf4j;

/**
 * REST controller for {{ domain_class }} operations.
 * Provides API endpoints for managing {{ domain_class }} resources.
 */
@RestController
@RequestMapping("/api/{{ api_path }}")
@Slf4j
@Validated
public class {{ class_name }} {

    private final {{ service_interface }} service;
    
    /**
     * Constructs a new {{ class_name }} with the required dependencies.
     * 
     * @param service the {{ service_interface }} used for business operations
     */
    @Autowired
    public {{ class_name }}({{ service_interface }} service) {
        this.service = service;
    }
    
    {% for endpoint in endpoints %}
    /**
     * {{ endpoint.doc }}
     {% for param in endpoint.params %}
     * @param {{ param.name }} {{ param.description|default(param.name) }}
     {% endfor %}
     * @return {{ endpoint.return_description|default("the appropriate response entity") }}
     */
    @{{ endpoint.method }}("{{ endpoint.path }}")
    {% if endpoint.status %}
    @ResponseStatus(HttpStatus.{{ endpoint.status }})
    {% endif %}
    public {{ endpoint.return_type }} {{ endpoint.name }}(
        {% for param in endpoint.params %}@{{ param.annotation }} {% if param.validation %}@Valid {% endif %}{{ param.type }} {{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %}
    ) {
        {% if endpoint.logging %}
        log.info("{{ endpoint.logging }}", {% for param in endpoint.log_params %}{{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %});
        {% endif %}
        {{ endpoint.body }}
    }
    {% endfor %}
}
""")

        # Add a DTO template
        self.dto_template = Template("""package com.ecommerce.dto;

import java.util.*;
import java.time.LocalDateTime;
import java.math.BigDecimal;
import jakarta.validation.constraints.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

/**
 * Data Transfer Object for {{ domain_class }}.
 * Used for data validation and transferring {{ domain_class }} data between processes.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class {{ class_name }}DTO {
    
    {% if has_id %}
    private {{ id_type }} id;
    {% endif %}
    
    {% for field in fields %}
    {% if field.validation %}{{ field.validation }}{% endif %}
    private {{ field.type }} {{ field.name }};
    {% endfor %}
    
    /**
     * Converts this DTO to a domain entity.
     * 
     * @return a new {{ domain_class }} instance with values from this DTO
     */
    public {{ domain_class }} toEntity() {
        return {{ domain_class }}.builder()
            {% if has_id %}
            .id(this.id)
            {% endif %}
            {% for field in fields %}
            .{{ field.name }}(this.{{ field.name }})
            {% endfor %}
            .build();
    }
    
    /**
     * Creates a DTO from a domain entity.
     * 
     * @param entity the {{ domain_class }} entity
     * @return a new DTO with values from the entity
     */
    public static {{ class_name }}DTO fromEntity({{ domain_class }} entity) {
        if (entity == null) {
            return null;
        }
        
        return {{ class_name }}DTO.builder()
            {% if has_id %}
            .id(entity.getId())
            {% endif %}
            {% for field in fields %}
            .{{ field.name }}(entity.get{{ field.name|capitalize }}())
            {% endfor %}
            .build();
    }
    
    /**
     * Creates a list of DTOs from a list of domain entities.
     * 
     * @param entities the list of {{ domain_class }} entities
     * @return a list of DTOs
     */
    public static List<{{ class_name }}DTO> fromEntities(List<{{ domain_class }}> entities) {
        if (entities == null) {
            return Collections.emptyList();
        }
        
        return entities.stream()
            .map({{ class_name }}DTO::fromEntity)
            .collect(Collectors.toList());
    }
}
""")

        # Add an exception class template
        self.exception_template = Template("""package com.ecommerce.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

/**
 * Exception thrown when a requested resource is not found.
 */
@ResponseStatus(HttpStatus.NOT_FOUND)
public class ResourceNotFoundException extends RuntimeException {
    
    /**
     * Constructs a new exception with the specified detail message.
     * 
     * @param message the detail message
     */
    public ResourceNotFoundException(String message) {
        super(message);
    }
    
    /**
     * Constructs a new exception for a specific resource.
     * 
     * @param resourceName the name of the resource
     * @param fieldName the name of the field
     * @param fieldValue the value of the field
     * @return a formatted exception
     */
    public static ResourceNotFoundException create(String resourceName, String fieldName, Object fieldValue) {
        return new ResourceNotFoundException(String.format(
            "%s not found with %s: '%s'", resourceName, fieldName, fieldValue));
    }
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
        for package in ["domain", "dto", "repository", "service", "service/impl", "controller", "exception"]:
            os.makedirs(os.path.join(output_dir, "com/ecommerce", package), exist_ok=True)
        
        # Generate exception handling class first
        exception_path = os.path.join(output_dir, "com/ecommerce/exception/ResourceNotFoundException.java")
        with open(exception_path, "w") as f:
            f.write(self.exception_template.render())
        
        generated_files = [exception_path]
        
        # Generate code for each class
        for class_name, info in class_info.items():
            # Convert attributes to a more comprehensive format
            enhanced_attributes = []
            for attr in info["attributes"]:
                attr_type = attr["type"]
                # Add validation annotations based on type
                validation = None
                if attr_type == "String":
                    validation = '@NotBlank(message = "' + attr["name"] + ' cannot be blank")\n    @Size(max = 255, message = "' + attr["name"] + ' cannot exceed 255 characters")'
                elif attr_type in ["int", "Integer", "Long", "Double", "Float", "BigDecimal"]:
                    validation = '@NotNull(message = "' + attr["name"] + ' cannot be null")'
                
                enhanced_attributes.append({
                    "name": attr["name"],
                    "type": attr_type,
                    "visibility": attr["visibility"],
                    "validation": validation,
                    "annotation": None
                })
            
            # Enhanced relationships with JPA annotations
            enhanced_relationships = []
            for rel in info["relationships"]:
                annotation = None
                rel_type = rel["type"]
                
                if rel_type == "OneToOne":
                    annotation = '@OneToOne(fetch = FetchType.LAZY)\n    @JoinColumn(name = "' + rel["target"].lower() + '_id")'
                    rel_type = rel["target"]
                elif rel_type == "OneToMany":
                    annotation = '@OneToMany(mappedBy = "' + class_name.lower() + '", cascade = CascadeType.ALL, orphanRemoval = true)'
                    rel_type = f"List<{rel['target']}>"
                elif rel_type == "ManyToOne":
                    annotation = '@ManyToOne(fetch = FetchType.LAZY)\n    @JoinColumn(name = "' + rel["target"].lower() + '_id")'
                    rel_type = rel["target"]
                elif rel_type == "ManyToMany":
                    annotation = '@ManyToMany(cascade = {CascadeType.PERSIST, CascadeType.MERGE})\n    @JoinTable(name = "' + class_name.lower() + '_' + rel["target"].lower() + '",\n        joinColumns = @JoinColumn(name = "' + class_name.lower() + '_id"),\n        inverseJoinColumns = @JoinColumn(name = "' + rel["target"].lower() + '_id"))'
                    rel_type = f"Set<{rel['target']}>"
                else:
                    rel_type = rel["target"]
                
                enhanced_relationships.append({
                    "target": rel["target"],
                    "type": rel_type,
                    "multiplicity": rel["multiplicity"],
                    "annotation": annotation
                })
            
            # Extract methods from the UML if available
            methods = []
            # Here you would parse method information from the UML if available
            
            # Generate entity class
            table_name = ''.join(['_' + i.lower() if i.isupper() else i.lower() for i in class_name]).lstrip('_')
            entity_code = self.entity_template.render(
                class_name=class_name,
                class_doc=f"Entity class for {class_name} in the eCommerce domain",
                table_name=table_name,
                id_type="Long",
                attributes=enhanced_attributes,
                relationships=enhanced_relationships,
                methods=methods
            )
            
            entity_path = os.path.join(output_dir, f"com/ecommerce/domain/{class_name}.java")
            with open(entity_path, "w") as f:
                f.write(entity_code)
            generated_files.append(entity_path)
            
            # Generate DTO class
            dto_name = f"{class_name}DTO"
            dto_fields = []
            
            for attr in enhanced_attributes:
                dto_fields.append({
                    "name": attr["name"],
                    "type": attr["type"],
                    "validation": attr["validation"]
                })
                
            dto_code = self.dto_template.render(
                class_name=dto_name,
                domain_class=class_name,
                has_id=True,
                id_type="Long",
                fields=dto_fields
            )
            
            dto_path = os.path.join(output_dir, f"com/ecommerce/dto/{dto_name}.java")
            with open(dto_path, "w") as f:
                f.write(dto_code)
            generated_files.append(dto_path)
            
            # Generate repository interface
            repo_name = f"{class_name}Repository"
            repo_methods = [
                {
                    "doc": f"Find {class_name} by name",
                    "return_type": f"Optional<{class_name}>",
                    "name": f"findBy{class_name}Name",
                    "params": [{
                        "type": "String", 
                        "name": "name",
                        "description": f"the name of the {class_name} to find"
                    }],
                    "return_description": f"an Optional containing the found {class_name} or empty if not found"
                },
                {
                    "doc": f"Find all {class_name}s by a certain attribute",
                    "return_type": f"List<{class_name}>",
                    "name": f"findAllBy{class_name}Active",
                    "params": [{
                        "type": "boolean", 
                        "name": "active",
                        "description": "whether to find active or inactive entities"
                    }],
                    "return_description": f"a list of {class_name}s matching the criteria"
                }
            ]
            
            repo_code = self.repository_template.render(
                class_name=repo_name,
                domain_class=class_name,
                id_type="Long",
                methods=repo_methods
            )
            
            repo_path = os.path.join(output_dir, f"com/ecommerce/repository/{repo_name}.java")
            with open(repo_path, "w") as f:
                f.write(repo_code)
            generated_files.append(repo_path)
            
            # Generate service interface
            service_name = f"{class_name}Service"
            service_methods = [
                {
                    "doc": f"Get all {class_name}s",
                    "return_type": f"List<{class_name}DTO>",
                    "name": f"getAll{class_name}s",
                    "params": [],
                    "return_description": f"a list of all {class_name} entities converted to DTOs"
                },
                {
                    "doc": f"Get {class_name} by id",
                    "return_type": f"{class_name}DTO",
                    "name": f"get{class_name}ById",
                    "params": [{
                        "type": "Long", 
                        "name": "id",
                        "description": f"the id of the {class_name} to retrieve"
                    }],
                    "return_description": f"the {class_name} converted to a DTO",
                    "exceptions": [{
                        "type": "ResourceNotFoundException",
                        "description": f"if the {class_name} is not found"
                    }]
                },
                {
                    "doc": f"Create a new {class_name}",
                    "return_type": f"{class_name}DTO",
                    "name": f"create{class_name}",
                    "params": [{
                        "type": f"{class_name}DTO", 
                        "name": f"{class_name.lower()}DTO",
                        "description": f"the {class_name} data to create"
                    }],
                    "return_description": f"the created {class_name} converted to a DTO"
                },
                {
                    "doc": f"Update an existing {class_name}",
                    "return_type": f"{class_name}DTO",
                    "name": f"update{class_name}",
                    "params": [
                        {
                            "type": "Long", 
                            "name": "id",
                            "description": f"the id of the {class_name} to update"
                        },
                        {
                            "type": f"{class_name}DTO", 
                            "name": f"{class_name.lower()}DTO",
                            "description": f"the updated {class_name} data"
                        }
                    ],
                    "return_description": f"the updated {class_name} converted to a DTO",
                    "exceptions": [{
                        "type": "ResourceNotFoundException",
                        "description": f"if the {class_name} is not found"
                    }]
                },
                {
                    "doc": f"Delete a {class_name} by id",
                    "return_type": "void",
                    "name": f"delete{class_name}",
                    "params": [{
                        "type": "Long", 
                        "name": "id",
                        "description": f"the id of the {class_name} to delete"
                    }],
                    "exceptions": [{
                        "type": "ResourceNotFoundException",
                        "description": f"if the {class_name} is not found"
                    }]
                }
            ]
            
            service_code = self.service_interface_template.render(
                class_name=service_name,
                domain_class=class_name,
                methods=service_methods
            )
            
            service_path = os.path.join(output_dir, f"com/ecommerce/service/{service_name}.java")
            with open(service_path, "w") as f:
                f.write(service_code)
            generated_files.append(service_path)
            
            # Generate service implementation
            impl_name = f"{class_name}ServiceImpl"
            impl_methods = [
                {
                    "doc": f"Get all {class_name}s",
                    "return_type": f"List<{class_name}DTO>",
                    "name": f"getAll{class_name}s",
                    "params": [],
                    "transactional": True,
                    "transactional_args": 'readOnly = true',
                    "logging": f"Retrieving all {class_name}s",
                    "log_params": [],
                    "body": f"List<{class_name}> {class_name.lower()}s = repository.findAll();\nreturn {class_name}DTO.fromEntities({class_name.lower()}s);"
                },
                {
                    "doc": f"Get {class_name} by id",
                    "return_type": f"{class_name}DTO",
                    "name": f"get{class_name}ById",
                    "params": [{
                        "type": "Long", 
                        "name": "id",
                        "description": f"the id of the {class_name} to retrieve"
                    }],
                    "transactional": True,
                    "transactional_args": 'readOnly = true',
                    "logging": f"Retrieving {class_name} with id: {{}}", 
                    "log_params": [{"name": "id"}],
                    "body": f"return repository.findById(id)\n            .map({class_name}DTO::fromEntity)\n            .orElseThrow(() -> ResourceNotFoundException.create(\"{class_name}\", \"id\", id));"
                },
                {
                    "doc": f"Create a new {class_name}",
                    "return_type": f"{class_name}DTO",
                    "name": f"create{class_name}",
                    "params": [{
                        "type": f"{class_name}DTO", 
                        "name": f"{class_name.lower()}DTO",
                        "description": f"the {class_name} data to create"
                    }],
                    "transactional": True,
                    "logging": f"Creating new {class_name}",
                    "log_params": [],
                    "body": f"{class_name} {class_name.lower()} = {class_name.lower()}DTO.toEntity();\n{class_name} saved{class_name} = repository.save({class_name.lower()});\nlog.info(\"{class_name} created with id: {{}}\", saved{class_name}.getId());\nreturn {class_name}DTO.fromEntity(saved{class_name});"
                },
                {
                    "doc": f"Update an existing {class_name}",
                    "return_type": f"{class_name}DTO",
                    "name": f"update{class_name}",
                    "params": [
                        {
                            "type": "Long", 
                            "name": "id",
                            "description": f"the id of the {class_name} to update"
                        },
                        {
                            "type": f"{class_name}DTO", 
                            "name": f"{class_name.lower()}DTO",
                            "description": f"the updated {class_name} data"
                        }
                    ],
                    "transactional": True,
                    "logging": f"Updating {class_name} with id: {{}}", 
                    "log_params": [{"name": "id"}],
                    "body": f"return repository.findById(id)\n            .map(existing{class_name} -> {{\n                // Update the existing entity with DTO values\n                {class_name} updated = {class_name.lower()}DTO.toEntity();\n                updated.setId(id);\n                // Keep any values not in the DTO\n                // ...\n                \n                {class_name} saved = repository.save(updated);\n                log.info(\"{class_name} updated: {{}}\", saved.getId());\n                return {class_name}DTO.fromEntity(saved);\n            }})\n            .orElseThrow(() -> ResourceNotFoundException.create(\"{class_name}\", \"id\", id));"
                },
                {
                    "doc": f"Delete a {class_name} by id",
                    "return_type": "void",
                    "name": f"delete{class_name}",
                    "params": [{
                        "type": "Long", 
                        "name": "id",
                        "description": f"the id of the {class_name} to delete"
                    }],
                    "transactional": True,
                    "logging": f"Deleting {class_name} with id: {{}}", 
                    "log_params": [{"name": "id"}],
                    "body": f"{class_name} {class_name.lower()} = repository.findById(id)\n            .orElseThrow(() -> ResourceNotFoundException.create(\"{class_name}\", \"id\", id));\n\nrepository.delete({class_name.lower()});\nlog.info(\"{class_name} deleted: {{}}\", id);"
                }
            ]
            
            impl_code = self.service_impl_template.render(
                class_name=impl_name,
                domain_class=class_name,
                repository_name=repo_name,
                service_interface=service_name,
                methods=impl_methods
            )
            
            impl_path = os.path.join(output_dir, f"com/ecommerce/service/impl/{impl_name}.java")
            with open(impl_path, "w") as f:
                f.write(impl_code)
            generated_files.append(impl_path)
            
            # Generate controller
            controller_name = f"{class_name}Controller"
            snake_case = ''.join(['_' + i.lower() if i.isupper() else i.lower() for i in class_name]).lstrip('_')
            
            controller_endpoints = [
                {
                    "doc": f"Get all {class_name}s",
                    "method": "GetMapping",
                    "path": "/",
                    "return_type": f"ResponseEntity<List<{class_name}DTO>>",
                    "name": f"getAll{class_name}s",
                    "params": [],
                    "logging": f"REST request to get all {class_name}s",
                    "log_params": [],
                    "return_description": f"ResponseEntity containing the list of {class_name}s",
                    "body": f"List<{class_name}DTO> result = service.getAll{class_name}s();\nreturn ResponseEntity.ok(result);"
                },
                {
                    "doc": f"Get a {class_name} by id",
                    "method": "GetMapping",
                    "path": "/{id}",
                    "return_type": f"ResponseEntity<{class_name}DTO>",
                    "name": f"get{class_name}ById",
                    "params": [{
                        "annotation": "PathVariable", 
                        "type": "Long", 
                        "name": "id",
                        "description": f"the id of the {class_name} to retrieve"
                    }],
                    "logging": f"REST request to get {class_name} : {{}}", 
                    "log_params": [{"name": "id"}],
                    "return_description": f"ResponseEntity containing the {class_name}",
                    "body": f"try {{\n    {class_name}DTO result = service.get{class_name}ById(id);\n    return ResponseEntity.ok(result);\n}} catch (ResourceNotFoundException e) {{\n    log.warn(e.getMessage());\n    return ResponseEntity.notFound().build();\n}}"
                },
                {
                    "doc": f"Create a new {class_name}",
                    "method": "PostMapping",
                    "path": "/",
                    "status": "CREATED",
                    "return_type": f"ResponseEntity<{class_name}DTO>",
                    "name": f"create{class_name}",
                    "params": [{
                        "annotation": "RequestBody", 
                        "validation": True,
                        "type": f"{class_name}DTO", 
                        "name": f"{class_name.lower()}DTO",
                        "description": f"the {class_name}DTO to create"
                    }],
                    "logging": f"REST request to create {class_name}", 
                    "log_params": [],
                    "return_description": f"ResponseEntity containing the created {class_name}",
                    "body": f"{class_name}DTO result = service.create{class_name}({class_name.lower()}DTO);\nreturn ResponseEntity.status(HttpStatus.CREATED).body(result);"
                },
                {
                    "doc": f"Update an existing {class_name}",
                    "method": "PutMapping",
                    "path": "/{id}",
                    "return_type": f"ResponseEntity<{class_name}DTO>",
                    "name": f"update{class_name}",
                    "params": [
                        {
                            "annotation": "PathVariable", 
                            "type": "Long", 
                            "name": "id",
                            "description": f"the id of the {class_name} to update"
                        },
                        {
                            "annotation": "RequestBody", 
                            "validation": True,
                            "type": f"{class_name}DTO", 
                            "name": f"{class_name.lower()}DTO",
                            "description": f"the {class_name}DTO to update"
                        }
                    ],
                    "logging": f"REST request to update {class_name} : {{}}", 
                    "log_params": [{"name": "id"}],
                    "return_description": f"ResponseEntity containing the updated {class_name}",
                    "body": f"try {{\n    {class_name}DTO result = service.update{class_name}(id, {class_name.lower()}DTO);\n    return ResponseEntity.ok(result);\n}} catch (ResourceNotFoundException e) {{\n    log.warn(e.getMessage());\n    return ResponseEntity.notFound().build();\n}}"
                },
                {
                    "doc": f"Delete a {class_name} by id",
                    "method": "DeleteMapping",
                    "path": "/{id}",
                    "status": "NO_CONTENT",
                    "return_type": "ResponseEntity<Void>",
                    "name": f"delete{class_name}",
                    "params": [{
                        "annotation": "PathVariable", 
                        "type": "Long", 
                        "name": "id",
                        "description": f"the id of the {class_name} to delete"
                    }],
                    "logging": f"REST request to delete {class_name} : {{}}", 
                    "log_params": [{"name": "id"}],
                    "return_description": "ResponseEntity with status 204 (NO_CONTENT)",
                    "body": f"try {{\n    service.delete{class_name}(id);\n    return ResponseEntity.noContent().build();\n}} catch (ResourceNotFoundException e) {{\n    log.warn(e.getMessage());\n    return ResponseEntity.notFound().build();\n}}"
                }
            ]
            
            controller_code = self.controller_template.render(
                class_name=controller_name,
                domain_class=class_name,
                service_interface=service_name,
                api_path=snake_case.replace('_', '-'),
                endpoints=controller_endpoints
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