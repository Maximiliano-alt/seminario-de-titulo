# Enhanced eCommerce LLM Code Generator

This project is a web application that leverages Large Language Models (LLMs) to generate UML diagrams and Java code from user stories. It features a React-based frontend and a Python FastAPI backend.

## User Manual

This guide will help you set up and run the project on your local machine using Docker.

### Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Docker**: [Get Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: Included with Docker Desktop. If you are on Linux, you might need to install it separately. [Install Docker Compose](https://docs.docker.com/compose/install/)

### Configuration

The application requires API keys for Large Language Model (LLM) providers to function correctly. You need to provide at least one of the following API keys.

1.  **Create a `.env` file** in the root directory of the project.
2.  **Add your API keys** to the `.env` file. For example:

    ```
    # At least one of these is required
    OPENAI_API_KEY="your-openai-api-key"
    ANTHROPIC_API_KEY="your-anthropic-api-key"
    GOOGLE_API_KEY="your-google-api-key"
    DEEPSEEK_API_KEY="your-deepseek-api-key"
    ```

    _Note: The `OPENAI_API_KEY` is also used for creating text embeddings, so it is highly recommended to provide it._

### Running the Application

Once you have configured your API keys, you can start the application using Docker Compose.

1.  Open your terminal.
2.  Navigate to the root directory of the project.
3.  Run the following command:

    ```bash
    docker-compose up --build -d
    ```

    This command will build the Docker images for the frontend and backend services and start the containers in detached mode.

### Accessing the Application

- **Frontend**: Open your web browser and navigate to [http://localhost:5173](http://localhost:5173)
- **Backend API**: The backend API is running at [http://localhost:8000](http://localhost:8000). You can access the API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

### Stopping the Application

To stop the running application, execute the following command in the project's root directory:

```bash
docker-compose down
```

This will stop and remove the containers.

### Local Development (Optional)

If you prefer to run the services without Docker for development purposes, you can follow these steps.

#### Backend

1.  Navigate to the `Backend` directory:
    ```bash
    cd Backend
    ```
2.  Create a Python virtual environment:
    ```bash
    python -m venv venv
    ```
3.  Activate the virtual environment:
    - **macOS/Linux**: `source venv/bin/activate`
    - **Windows**: `.\venv\Scripts\activate`
4.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
5.  Run the backend server:
    `bash
    uvicorn main:app --reload
    `
    The backend will be available at `http://localhost:8000`.

#### Frontend

1.  Navigate to the `Frontend` directory:
    ```bash
    cd Frontend
    ```
2.  Install the dependencies:
    ```bash
    npm install
    ```
3.  Run the frontend development server:
    `bash
    npm run dev
    `
    The frontend will be available at `http://localhost:5173`.

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
