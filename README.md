# Proyecto de Título: DESARROLLO DE UN LLM PARA LA GENERACIÓN DE CÓDIGO DESDE HISTORIAS DE USUARIO Y DIAGRAMAS DE CLASE.

A Large Language Model (LLM) powered system using LangChain, Retrieval-Augmented Generation (RAG), and fine-tuning for eCommerce projects in Java. This project is an MVP that:

Este proyecto tiene como objetivo principal la automatización de la generación de artefactos (historias de usuario, modelos UML y código asociado) para sistemas basados en microservicios en el dominio del comercio electrónico. Utilizando un enfoque orientado a datos y herramientas modernas, el sistema automatiza tareas críticas del desarrollo, desde la generación de requisitos hasta la implementación de prototipos funcionales.

1. Captures user stories related to an eCommerce application
2. Transforms these user stories into UML models (using PlantUML)
3. Generates Java code automatically from those UML diagrams

## System Architecture

### Objetivo General

Automatizar la generación de artefactos de software para microservicios, integrando modelos UML, historias de usuario y código en un sistema unificado que acelere el desarrollo y reduzca errores.

### LangChain Integration

- Chains various LLM prompts and tools together
- Modular architecture for different steps (user story analysis, UML generation, Java code creation)
- Uses prompt templates and agents for efficient processing

### Objetivos Específicos

## Retrieval-Augmented Generation (RAG)

- Knowledge base of eCommerce patterns, Java code, and architectural components
- Vector database with either ChromaDB or FAISS for efficient similarity search
- Enhanced with metadata for context-aware retrieval

1. **Integrar herramientas modernas de desarrollo**: Utilizar Python, Java con Spring Boot, Docker y Kubernetes para construir un ecosistema de desarrollo robusto.
2. **Generar un dataset estructurado**: Crear un conjunto de datos que combine historias de usuario, diagramas UML y código asociado para entrenar modelos de lenguaje.
3. **Automatizar la extracción y modelado**: Diseñar un pipeline que procese repositorios de código y genere artefactos consistentes y reutilizables.
4. **Validar la trazabilidad de artefactos**: Asegurar que los diagramas, historias y código generados estén alineados con los requisitos del sistema.

- Fine-tune existing large language models on eCommerce and Java development data
- Includes domain-specific terminology, patterns, and best practices
- Optimized for Java code generation from user stories

1. **Análisis de repositorios**: Identificación y selección de repositorios de código relevantes, con énfasis en microservicios escritos en Java utilizando Spring Boot.
2. **Desarrollo de scripts en Python**: Implementación de herramientas para la extracción de clases, generación de UML en PlantUML y creación de historias de usuario con el soporte de OpenAI API.
3. **Contenerización de servicios**: Uso de Docker para encapsular microservicios y Kubernetes para la orquestación de los mismos.
4. **Diseño de un pipeline automatizado**: Creación de un flujo de trabajo iterativo que conecta las historias de usuario con diagramas UML y código fuente funcional.
5. **Pruebas y validación**: Validación del sistema mediante pruebas unitarias y de integración, utilizando bases de datos H2 y MySQL.

## key characteristics

- **User Story Processing**: Parse and understand eCommerce user stories
- **UML Diagram Generation**: Create PlantUML diagrams (Class and Sequence diagrams)
- **Java Code Generation**: Generate Spring Boot based Java code with proper architecture
- **Vector-based Retrieval**: Search for similar examples in the knowledge base
- **Metadata Filtering**: Filter search results by type (code, UML, requirements)
- **Fine-tuning Support**: Improve model performance on domain-specific tasks

## Getting Started

### Prerequisites

- **Dataset estructurado**: Un JSON que combina historias de usuario, diagramas UML y código funcional.
- **Pipeline automatizado**: Sistema que genera artefactos reutilizables a partir de entradas textuales y código fuente.
- **Validación de microservicios**: Diagramas y prototipos alineados con los requisitos iniciales.
- **Prototipo funcional**: Sistema navegable basado en los microservicios generados y modelados automáticamente.

### Installation

1. Clone the repository

   ```bash
   git clone [repository-url]
   cd [repository-directory]
   ```

2. Set up a virtual environment

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies

   ```bash
   pip install -r Backend/requirements.txt
   ```

## Contacto

**Nombre del Autor**: Max Espindola\
**Correo**: [maxespindola@example.com](mailto:maxespindola@example.com)\
**Repositorio del Proyecto**: [URL del Repositorio]

## Getting started

To make it easy for you to get started with GitLab, here's a list of recommended next steps.

Already a pro? Just edit this README.md and make it your own. Want to make it easy? [Use the template at the bottom](#editing-this-readme)!

## Add your files

- [ ] [Create](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#create-a-file) or [upload](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#upload-a-file) files
- [ ] [Add files using the command line](https://docs.gitlab.com/ee/gitlab-basics/add-file.html#add-a-file-using-the-command-line) or push an existing Git repository with the following command:

```
cd existing_repo
git remote add origin https://gitlab.com/max0101/seminario-de-titulo.git
git branch -M main
git push -uf origin main
```

4. Create a `.env` file in the Backend directory with your OpenAI API key
   ```
   OPENAI_API_KEY=your-api-key-here
   USE_FAISS=false  # Set to true to use FAISS instead of ChromaDB
   ```

- [ ] [Set up project integrations](https://gitlab.com/max0101/seminario-de-
      titulo/-/settings/integrations)

### Running the Application

1. Start the backend server

   ```bash
   cd Backend
   uvicorn main:app --reload
   ```

2. Start the frontend (if applicable)

   ```bash
   cd Frontend
   npm install
   npm run dev
   ```

3. Access the application at http://localhost:3000 (frontend) or http://localhost:8000 (API)

## API Endpoints

- `POST /api/user-story/uml` - Generate UML diagrams from a user story
- `POST /api/user-story/java` - Generate Java code from UML diagrams
- `GET /api/search-similar` - Search for similar code examples, UML, or user stories
- `POST /api/fine-tune` - Fine-tune the model on custom data
- `POST /api/generate` - Legacy endpoint for combined generation

## Dataset

The system includes a dataset of eCommerce projects with:

- User stories and acceptance criteria
- UML class and sequence diagrams
- Java code implementations
- Metadata for enhanced retrieval

## Vector Storage

The system supports two vector database backends:

### ChromaDB (Default)

- Persistent local storage
- Simple setup and usage
- Good for medium-sized datasets

### FAISS (Optional)

- High-performance vector search
- Better for large-scale deployments
- Optimized for similarity search at scale

To switch between them, set the `USE_FAISS` environment variable in your `.env` file.

## Fine-Tuning

You can fine-tune the base LLM using:

```bash
python fine_tuning.py --dataset path/to/dataset.json --model gpt2 --output ./fine_tuned_model
```

## Project Structure

```
├── Backend/
│   ├── api.py                 # FastAPI endpoints
│   ├── main.py                # Application entry point
│   ├── vector_store.py        # Vector database management
│   ├── uml_generator.py       # UML generation from user stories
│   ├── java_generator.py      # Java code generation from UML
│   ├── fine_tuning.py         # LLM fine-tuning utilities
│   ├── requirements.txt       # Python dependencies
│   └── vector_store/          # Persistent vector database
├── Frontend/
│   ├── src/                   # Frontend source code
│   └── ...
├── data/
│   └── dataset_new.json       # Dataset for training and RAG
└── README.md                  # This file
```

## Future Enhancements

- Integration with version control systems
- Testing code generation for the generated Java code
- Support for additional programming languages
- Multi-language support (Spanish, etc.)
- Advanced fine-tuning with more domain-specific data

## License

[Specify the license]

## Acknowledgments

- LangChain for the foundation of the RAG system
- OpenAI for the base LLM capabilities
- FAISS and ChromaDB for vector storage
