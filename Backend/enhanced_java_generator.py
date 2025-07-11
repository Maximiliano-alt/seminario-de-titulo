import os
import re
from typing import List, Dict, Any, Optional
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from llm_manager import LLMManager, LLMProvider
from enhanced_uml_generator import DomainClass
import logging

logger = logging.getLogger(__name__)

def _format_java_field(field_str: str) -> str:
    """Formats a domain field string into a Java field declaration."""
    # Example: "product_name: String" -> "private String productName;"
    try:
        name, field_type = [s.strip() for s in field_str.split(':')]
        
        if '_' in name:
            parts = name.split('_')
            camel_case_name = parts[0] + "".join(p.capitalize() for p in parts[1:])
        else:
            camel_case_name = name
            
        return f"    private {field_type} {camel_case_name};"
    except (ValueError, IndexError):
        return f"    // TODO: Could not parse and implement field: {field_str}"

def _generate_class_skeleton(class_name: str, package_name: str, class_type: str, domain_class: DomainClass) -> str:
    """Generates the skeleton of a Java class with fields and method stubs."""
    
    # DEBUG: Log what we're working with
    logger.info(f"=== GENERATING SKELETON FOR {class_name} ===")
    logger.info(f"Class type: {class_type}")
    logger.info(f"Package: {package_name}")
    logger.info(f"Raw fields: {domain_class.fields}")
    logger.info(f"Raw methods: {domain_class.methods}")
    
    # Defensive parsing for fields - handle different formats
    fields = []
    if isinstance(domain_class.fields, list):
        for field in domain_class.fields:
            if isinstance(field, str) and ':' in field:
                formatted_field = _format_java_field(field)
                if formatted_field and not formatted_field.startswith("    // TODO"):
                    fields.append(formatted_field)
                else:
                    # If formatting failed, create a basic field
                    field_name = field.split(':')[0].strip()
                    field_type = field.split(':')[1].strip() if ':' in field else "String"
                    camel_case_name = field_name
                    if '_' in field_name:
                        parts = field_name.split('_')
                        camel_case_name = parts[0] + "".join(p.capitalize() for p in parts[1:])
                    fields.append(f"    private {field_type} {camel_case_name};")
            else:
                logger.warning(f"Skipping malformed field: {field}")
    else:
        logger.warning(f"Fields is not a list: {type(domain_class.fields)}")
    
    # Add JPA annotations for entity fields
    if class_type == 'entity' and fields:
        annotated_fields = []
        for field in fields:
            if 'private String' in field:
                field_line = field.replace('private String', '@Column(nullable = false, length = 255)\n    private String')
            elif 'private Long' in field and 'id' not in field.lower():
                field_line = field.replace('private Long', '@Column(nullable = false)\n    private Long')
            elif 'private Integer' in field or 'private int' in field:
                field_line = field.replace('private Integer', '@Column(nullable = false)\n    private Integer').replace('private int', '@Column(nullable = false)\n    private int')
            else:
                field_line = field
            annotated_fields.append(field_line)
        fields = annotated_fields
    
    fields_code = "\n\n".join(fields) if fields else "    // No fields defined"
    
    # Generate method stubs
    methods_code = ""
    if isinstance(domain_class.methods, list):
        for method_str in domain_class.methods:
            if not isinstance(method_str, str):
                logger.warning(f"Skipping non-string method: {method_str}")
                continue
                
            # Basic parsing for method signature
            return_type = "void"
            method_name_and_args = method_str
            
            # A simple heuristic to guess return type
            if any(keyword in method_str.lower() for keyword in ["get", "find", "search", "retrieve"]):
                return_type = "Object"  # Let LLM infer specific type
            elif any(keyword in method_str.lower() for keyword in ["is", "has", "can", "check"]):
                return_type = "boolean"
            elif "count" in method_str.lower():
                return_type = "int"

            methods_code += f'''
    /**
     * TODO: Implement method logic for {method_str}
     * Purpose: This method should handle the business logic for {method_str}
     */
    public {return_type} {method_name_and_args} {{
        // TODO: Implement complete business logic here
        // This is a placeholder that must be replaced with real implementation
        {"return false;" if return_type == "boolean" else "return 0;" if return_type == "int" else "return null;" if return_type != "void" else "// Implementation needed"}
    }}
'''
    else:
        logger.warning(f"Methods is not a list: {type(domain_class.methods)}")
        methods_code = '''
    /**
     * TODO: Add business methods for this class
     */
    public void placeholder() {
        // TODO: Implement business logic
    }
'''

    # Determine annotations and imports based on class type
    class_annotation = f"@{class_type.capitalize()}"
    imports = {
        "java.util.List",
        "java.util.Map",
        "java.time.LocalDateTime"
    }
    
    if class_type == 'entity':
        class_annotation = f"""@Entity
@Table(name = "{class_name.lower()}s")"""
        imports.update([
            "javax.persistence.*"
        ])
        
        # Add a default ID field for entities
        id_field = """    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;"""
        fields_code = id_field + "\\n\\n" + fields_code
        
        # Generate explicit getters and setters for entities (no Lombok)
        if fields:
            methods_code += "\\n    // Getters and Setters\\n"
            for field in fields:
                if 'private' in field:
                    # Extract field name and type
                    field_parts = field.strip().split()
                    if len(field_parts) >= 3:
                        field_type = field_parts[-2]
                        field_name = field_parts[-1].replace(';', '')
                        
                        # Generate getter
                        getter_name = f"get{field_name.capitalize()}"
                        methods_code += f'''
    public {field_type} {getter_name}() {{
        return this.{field_name};
    }}'''
                        
                        # Generate setter
                        setter_name = f"set{field_name.capitalize()}"
                        methods_code += f'''
    
    public void {setter_name}({field_type} {field_name}) {{
        this.{field_name} = {field_name};
    }}'''

    elif class_type == 'service':
        class_annotation = "@Service"
        imports.add("org.springframework.stereotype.Service")
        imports.add("org.springframework.beans.factory.annotation.Autowired")
    elif class_type == 'controller':
        class_annotation = f'''@RestController
@RequestMapping("/api/{class_name.lower()}s")'''
        imports.update([
            "org.springframework.web.bind.annotation.*",
            "org.springframework.http.ResponseEntity",
            "org.springframework.beans.factory.annotation.Autowired"
        ])

    import_statements = "\\n".join([f"import {imp};" for imp in sorted(list(imports))])

    skeleton = f"""package {package_name};

{import_statements}

/**
 * {domain_class.purpose}
 * 
 * This class serves as a {class_type} in the Spring Boot application.
 * Generated from domain analysis of the user story.
 */
{class_annotation}
public class {class_name} {{

{fields_code}

{methods_code}
}}
"""
    
    logger.info(f"Generated skeleton preview for {class_name}:")
    logger.info(skeleton[:500] + "..." if len(skeleton) > 500 else skeleton)
    return skeleton

class JavaCodeStructure:
    """Represents the structure of generated Java code."""
    
    def __init__(self):
        self.classes: Dict[str, str] = {}
        self.packages: Dict[str, List[str]] = {}
        self.dependencies: List[str] = []
        self.build_config: str = ""
        
    def add_class(self, class_name: str, package: str, code: str):
        """Add a class to the code structure."""
        full_name = f"{package}.{class_name}"
        self.classes[full_name] = code
        
        if package not in self.packages:
            self.packages[package] = []
        self.packages[package].append(class_name)
    
    def get_class_count(self) -> int:
        """Get total number of classes."""
        return len(self.classes)

class EnhancedJavaGenerator:
    """Enhanced Java code generator with multi-LLM support and compilable output."""
    
    def __init__(self):
        self.llm_manager = LLMManager()
        self.base_package = "com.generated.ecommerce"
        
        # Template for generating Java classes
        self.java_class_template = PromptTemplate(
            input_variables=["user_story", "class_skeleton", "related_classes", "class_purpose"],
            template="""You are a senior Java developer. I will give you a BROKEN Java class that only has comments instead of actual code. Your job is to COMPLETELY REWRITE it with real, working Java code.

**BROKEN CLASS (ONLY COMMENTS, NO REAL CODE):**
```java
{class_skeleton}
```

**CRITICAL REQUIREMENTS - FOLLOW EXACTLY:**

1. **REPLACE ALL FIELD COMMENTS WITH ACTUAL PRIVATE FIELDS**
   - Find lines like "// fieldName: Type" 
   - Replace with "private Type fieldName;"
   - Add @Column annotations for JPA entities

2. **IMPLEMENT EVERY METHOD WITH REAL BUSINESS LOGIC**
   - NO "return null;" or "// TODO" comments allowed
   - Write actual working code that makes sense for: {class_purpose}
   - For getters: return the actual field value
   - For setters: set the actual field value with validation
   - For business methods: implement realistic logic

3. **ADD MISSING LOMBOK ANNOTATIONS**
   - Keep @Data, @NoArgsConstructor, @AllArgsConstructor
   - Remove manual getters/setters if @Data is present

4. **FOR ENTITIES:** Add proper JPA relationships (@OneToMany, @ManyToOne, etc.)
5. **FOR SERVICES:** Add @Autowired dependencies and implement business rules
6. **FOR CONTROLLERS:** Add proper REST endpoints (@GetMapping, @PostMapping, etc.)

**CONTEXT:**
- User Story: {user_story}
- Related Classes: {related_classes}

**EXAMPLE OF WHAT I WANT:**
Instead of:
```java
// name: String
public String getName() {{ return null; }}
```

I want:
```java
@Column(nullable = false)
private String name;

public String getName() {{ 
    return this.name; 
}}
```

**OUTPUT:** Return ONLY the complete logic, working Java class. No explanations, no markdown, just pure Java code."""
        )
        
        # Template for generating project structure
        self.project_structure_template = PromptTemplate(
            input_variables=["user_story", "domain_classes"],
            template="""
            You are an expert Spring Boot architect. 
            
            Based on the user story and domain classes, create a complete project structure with:
            
            USER STORY: {user_story}
            DOMAIN CLASSES: {domain_classes}
            
            Generate:
            1. Maven pom.xml with all necessary dependencies
            2. application.yml configuration
            3. Main Spring Boot application class
            4. Basic project folder structure
            
            Include dependencies for:
            - Spring Boot Starter Web
            - Spring Boot Starter Data JPA
            - Spring Boot Starter Validation
            - H2 Database (for testing)
            - MySQL Connector (for production)
            - Lombok
            - SpringDoc OpenAPI (Swagger)
            - Spring Boot Starter Test
            
            Return as JSON with keys: "pom_xml", "application_yml", "main_class", "folder_structure"
            """
        )
    
    def _determine_class_type(self, domain_class: DomainClass) -> str:
        """Determine the type of class (entity, service, controller) based on purpose."""
        purpose_lower = domain_class.purpose.lower()
        name_lower = domain_class.name.lower()
        
        if any(keyword in purpose_lower for keyword in ['entity', 'model', 'data', 'represents', 'stores']):
            return 'entity'
        elif any(keyword in purpose_lower for keyword in ['service', 'business', 'logic', 'process', 'manage']):
            return 'service'
        elif any(keyword in purpose_lower for keyword in ['controller', 'endpoint', 'api', 'rest', 'handle']):
            return 'controller'
        elif 'repository' in purpose_lower or 'dao' in purpose_lower:
            return 'repository'
        else:
            # Default to entity for domain objects
            return 'entity'
    
    def _get_package_for_type(self, class_type: str) -> str:
        """Get appropriate package name for class type."""
        package_mapping = {
            'entity': f"{self.base_package}.model",
            'service': f"{self.base_package}.service",
            'controller': f"{self.base_package}.controller",
            'repository': f"{self.base_package}.repository",
            'dto': f"{self.base_package}.dto"
        }
        return package_mapping.get(class_type, f"{self.base_package}.model")
    
    def generate_java_class(self, user_story: str, domain_class: DomainClass, 
                           related_classes: List[DomainClass], 
                           llm_provider: LLMProvider = LLMProvider.GPT_4O) -> str:
        """Generate a single Java class."""
        try:
            # DEBUG: Log the input data
            logger.info(f"=== GENERATING JAVA CLASS: {domain_class.name} ===")
            logger.info(f"Domain class purpose: {domain_class.purpose}")
            logger.info(f"Domain class fields: {domain_class.fields}")
            logger.info(f"Domain class methods: {domain_class.methods}")
            logger.info(f"Fields type: {type(domain_class.fields)}")
            logger.info(f"Methods type: {type(domain_class.methods)}")
            
            llm = self.llm_manager.get_llm(llm_provider)
            if not llm:
                raise ValueError(f"LLM provider {llm_provider.value} not available")
            
            # Determine class type and package
            class_type = self._determine_class_type(domain_class)
            package_name = self._get_package_for_type(class_type)
            
            # 1. Generate the class skeleton programmatically
            class_skeleton = _generate_class_skeleton(domain_class.name, package_name, class_type, domain_class)
            
            # DEBUG: Log the generated skeleton
            logger.info(f"Generated skeleton for {domain_class.name}:")
            logger.info(f"Skeleton:\n{class_skeleton}")
            
            # Format related classes for context
            related_text = ""
            for rc in related_classes:
                if rc.name != domain_class.name:
                    related_text += f"- {rc.name}: {rc.purpose}\\n"

            # 2. Use LLM to fill in the skeleton
            chain = LLMChain(llm=llm, prompt=self.java_class_template)
            
            # DEBUG: Log what we're sending to the LLM
            logger.info(f"Sending to LLM:")
            logger.info(f"User story: {user_story[:100]}...")
            logger.info(f"Class purpose: {domain_class.purpose}")
            logger.info(f"Related classes: {related_text}")
            
            result = chain.run(
                user_story=user_story,
                class_skeleton=class_skeleton,
                related_classes=related_text,
                class_purpose=domain_class.purpose
            )
            
            # DEBUG: Log what we got back from the LLM
            logger.info(f"LLM response for {domain_class.name}:")
            logger.info(f"Response length: {len(result)}")
            logger.info(f"First 500 chars: {result[:500]}")
            
            logger.info(f"Generated Java class: {domain_class.name}")
            # Clean up potential markdown fences from the output
            if result.strip().startswith("```java"):
                result = result.strip()[7:-3].strip()
            
            return result.strip()
            
        except Exception as e:
            logger.error(f"Error generating Java class {domain_class.name}: {e}")
            raise
    
    def generate_complete_project(self, user_story: str, domain_classes: List[DomainClass], 
                                 plantuml_code: str, 
                                 llm_provider: LLMProvider = LLMProvider.GPT_4O) -> JavaCodeStructure:
        """Generate complete Java Spring Boot project."""
        try:
            code_structure = JavaCodeStructure()
            
            # Generate individual classes
            for domain_class in domain_classes:
                logger.info(f"Generating class: {domain_class.name}")
                
                java_code = self.generate_java_class(
                    user_story, domain_class, domain_classes, llm_provider
                )
                
                class_type = self._determine_class_type(domain_class)
                package_name = self._get_package_for_type(class_type)
                
                code_structure.add_class(domain_class.name, package_name, java_code)
            
            # Generate project configuration
            logger.info("Generating project configuration...")
            project_config = self._generate_project_config(user_story, domain_classes, llm_provider)
            
            # Add configuration files
            code_structure.classes["pom.xml"] = project_config.get("pom_xml", "")
            code_structure.classes["application.yml"] = project_config.get("application_yml", "")
            code_structure.classes[f"{self.base_package}.Application"] = project_config.get("main_class", "")
            
            # Add dependencies info
            code_structure.dependencies = self._extract_dependencies(project_config.get("pom_xml", ""))
            
            logger.info(f"Generated complete project with {code_structure.get_class_count()} files")
            return code_structure
            
        except Exception as e:
            logger.error(f"Error generating complete project: {e}")
            raise
    
    def _generate_project_config(self, user_story: str, domain_classes: List[DomainClass], 
                                llm_provider: LLMProvider) -> Dict[str, str]:
        """Generate project configuration files."""
        try:
            llm = self.llm_manager.get_llm(llm_provider)
            if not llm:
                raise ValueError(f"LLM provider {llm_provider.value} not available")
            
            # Format domain classes
            classes_text = ""
            for dc in domain_classes:
                classes_text += f"- {dc.name}: {dc.purpose}\n"
            
            chain = LLMChain(llm=llm, prompt=self.project_structure_template)
            result = chain.run(user_story=user_story, domain_classes=classes_text)
            
            # Try to parse as JSON
            import json
            try:
                return json.loads(result.strip())
            except json.JSONDecodeError:
                logger.warning("Failed to parse project config as JSON, using fallback")
                return self._generate_fallback_config()
                
        except Exception as e:
            logger.error(f"Error generating project config: {e}")
            return self._generate_fallback_config()
    
    def _generate_fallback_config(self) -> Dict[str, str]:
        """Generate fallback project configuration."""
        return {
            "pom_xml": self._get_default_pom(),
            "application_yml": self._get_default_application_yml(),
            "main_class": self._get_default_main_class(),
            "folder_structure": "Standard Spring Boot structure"
        }
    
    def _get_default_pom(self) -> str:
        """Get default Maven pom.xml."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>
    
    <groupId>com.generated</groupId>
    <artifactId>ecommerce-app</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <properties>
        <java.version>17</java.version>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>mysql</groupId>
            <artifactId>mysql-connector-java</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>
        <dependency>
            <groupId>org.springdoc</groupId>
            <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
            <version>2.2.0</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>'''
    
    def _get_default_application_yml(self) -> str:
        """Get default application.yml."""
        return '''spring:
  datasource:
    url: jdbc:h2:mem:testdb
    driverClassName: org.h2.Driver
    username: sa
    password: 
  
  h2:
    console:
      enabled: true
  
  jpa:
    database-platform: org.hibernate.dialect.H2Dialect
    hibernate:
      ddl-auto: create-drop
    show-sql: true
    
  profiles:
    active: dev

server:
  port: 8080

management:
  endpoints:
    web:
      exposure:
        include: health,info

springdoc:
  api-docs:
    path: /api-docs
  swagger-ui:
    path: /swagger-ui.html'''
    
    def _get_default_main_class(self) -> str:
        """Get default Spring Boot main class."""
        return f'''package {self.base_package};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Main application class for the generated eCommerce application.
 * Auto-generated from user story analysis.
 */
@SpringBootApplication
public class Application {{
    
    public static void main(String[] args) {{
        SpringApplication.run(Application.class, args);
    }}
}}'''
    
    def _extract_dependencies(self, pom_xml: str) -> List[str]:
        """Extract dependencies from pom.xml."""
        dependencies = []
        if "spring-boot-starter-web" in pom_xml:
            dependencies.append("Spring Boot Web")
        if "spring-boot-starter-data-jpa" in pom_xml:
            dependencies.append("Spring Boot Data JPA")
        if "lombok" in pom_xml:
            dependencies.append("Lombok")
        if "h2" in pom_xml:
            dependencies.append("H2 Database")
        return dependencies
    
    def create_download_package(self, code_structure: JavaCodeStructure, output_dir: str) -> str:
        """Create a downloadable package of the generated code."""
        import tempfile
        import zipfile
        import os
        
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                project_dir = os.path.join(temp_dir, "generated-project")
                os.makedirs(project_dir, exist_ok=True)
                
                # Create directory structure
                src_main_java = os.path.join(project_dir, "src", "main", "java")
                src_main_resources = os.path.join(project_dir, "src", "main", "resources")
                os.makedirs(src_main_java, exist_ok=True)
                os.makedirs(src_main_resources, exist_ok=True)
                
                # Write Java classes
                for class_name, code in code_structure.classes.items():
                    if class_name.endswith(".xml"):
                        file_path = os.path.join(project_dir, "pom.xml")
                    elif class_name.endswith(".yml"):
                        file_path = os.path.join(src_main_resources, "application.yml")
                    else:
                        # Create package directory structure
                        package_path = class_name.replace(".", "/")
                        if not package_path.endswith(".java"):
                            package_path += ".java"
                        file_path = os.path.join(src_main_java, package_path)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(code)
                
                # Create ZIP file
                zip_path = os.path.join(output_dir, "generated-project.zip")
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(project_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, project_dir)
                            zipf.write(file_path, arcname)
                
                logger.info(f"Created download package: {zip_path}")
                return zip_path
                
        except Exception as e:
            logger.error(f"Error creating download package: {e}")
            raise 