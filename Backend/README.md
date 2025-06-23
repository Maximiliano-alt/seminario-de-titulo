# Backend API - eCommerce LLM Code Generator

Enhanced FastAPI backend with multi-LLM support for generating UML diagrams and Java code from user stories.

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Docker (optional, for containerized deployment)
- API keys for LLM providers (OpenAI, Anthropic, Google, or OpenRouter)

### 🏃‍♂️ Fastest Setup (Automated)

Run the automated setup script for instant configuration:

```bash
cd Backend
python setup_local.py
```

This script will:

- ✅ Check Python version compatibility
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Create `.env` template file
- ✅ Check Docker availability
- ✅ Provide step-by-step next steps

**Then simply:**

1. Edit `.env` with your API keys
2. Activate virtual environment: `source venv/bin/activate`
3. Start server: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

## 📦 Local Development Setup

### 1. Clone and Navigate

```bash
cd Backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

#### Option A: Automatic (via setup script)

```bash
python setup_local.py  # Creates .env template automatically
```

#### Option B: Manual Setup

```bash
# Create .env file from template (if setup script wasn't used)
touch .env

# Add the following content to .env:
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GOOGLE_API_KEY=your_google_api_key_here
# OPENROUTER_API_KEY=your_openrouter_api_key_here
# ENVIRONMENT=development
# PORT=8000
# FRONTEND_URL=http://localhost:3000
# USE_FAISS=true
# LOG_LEVEL=INFO

# Edit .env file with your actual API keys
nano .env  # or use your preferred editor
```

**Required Environment Variables:**

- `OPENAI_API_KEY`: Your OpenAI API key
- `ANTHROPIC_API_KEY`: Your Anthropic (Claude) API key
- `GOOGLE_API_KEY`: Your Google Gemini API key
- `OPENROUTER_API_KEY`: Your OpenRouter API key

**Note**: At least one API key is required for the application to function.

### 5. Run the Development Server

```bash
# Option 1: Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Using Python directly
python main.py

# Option 3: Using FastAPI CLI (if installed)
fastapi dev main.py
```

The API will be available at:

- **Main API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 🐳 Docker Deployment

### Method 1: Standalone Docker Compose (Recommended)

Use the included `docker-compose.backend.yml` for easy deployment:

```bash
# From the Backend directory
docker-compose -f docker-compose.backend.yml up --build

# Run in background
docker-compose -f docker-compose.backend.yml up --build -d

# Stop the service
docker-compose -f docker-compose.backend.yml down
```

**Features included:**

- ✅ Automatic health checks
- ✅ Volume persistence for data
- ✅ Environment variable management
- ✅ Restart policies
- ✅ Network isolation

### Method 2: Manual Docker Build and Run

#### Step 1: Build the Docker Image

```bash
# From the Backend directory
docker build -t backend-api .
```

#### Step 2: Run with Docker

```bash
# Option A: Run with environment file (.env must exist)
docker run -p 8000:8000 --env-file .env backend-api

# Option B: Run with inline environment variables
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -e ANTHROPIC_API_KEY=your_key_here \
  -e GOOGLE_API_KEY=your_key_here \
  -e FRONTEND_URL=http://localhost:3000 \
  -e ENVIRONMENT=production \
  backend-api

# Option C: Run with volume persistence
docker run -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/vector_store:/app/vector_store \
  -v $(pwd)/static:/app/static \
  backend-api
```

### Method 3: Using Project Root Docker Compose

If you have a `docker-compose.yml` in the project root directory:

```bash
# From the project root
docker-compose up backend
```

### Docker Configuration Files

The backend includes several Docker configuration files:

- **`dockerfile`**: Main Docker image configuration with health checks
- **`docker-compose.backend.yml`**: Standalone service configuration
- **`.env`**: Environment variables (create from template)

## 🛠️ API Endpoints

### Health Check

- `GET /` - API information and status
- `GET /health` - Health check endpoint

### Core API (v2)

- `GET /api/v2/llm-providers` - List available LLM providers
- `POST /api/v2/analyze-domain` - Analyze domain classes from user story
- `POST /api/v2/generate-uml` - Generate UML diagrams
- `POST /api/v2/generate-java-code` - Generate Java code
- `POST /api/v2/complete-workflow` - Complete end-to-end workflow
- `GET /api/v2/render-uml` - Render UML diagram
- `GET /api/v2/download/{filename}` - Download generated files

### Static Files

- `/api/static/uml/*` - UML diagram files
- `/api/static/java/*` - Generated Java code files

## 🔧 Configuration Options

### Environment Variables

| Variable       | Default                 | Description               |
| -------------- | ----------------------- | ------------------------- |
| `ENVIRONMENT`  | `development`           | Application environment   |
| `PORT`         | `8000`                  | Server port               |
| `FRONTEND_URL` | `http://localhost:3000` | Frontend URL for CORS     |
| `USE_FAISS`    | `true`                  | Enable FAISS vector store |
| `LOG_LEVEL`    | `INFO`                  | Logging level             |

### LLM Provider Configuration

The API supports multiple LLM providers. At least one API key is required:

- **OpenAI**: GPT-3.5, GPT-4 models
- **Anthropic**: Claude models
- **Google**: Gemini models
- **OpenRouter**: Access to multiple models

## 📋 Configuration Files Overview

### Setup and Configuration Files

| File                         | Purpose                        | Usage                                             |
| ---------------------------- | ------------------------------ | ------------------------------------------------- |
| `setup_local.py`             | Automated development setup    | `python setup_local.py`                           |
| `.env`                       | Environment variables          | Created by setup script or manually               |
| `env_template.txt`           | Environment variables template | Reference for required variables                  |
| `docker-compose.backend.yml` | Standalone Docker service      | `docker-compose -f docker-compose.backend.yml up` |
| `dockerfile`                 | Docker image configuration     | `docker build -t backend-api .`                   |
| `requirements.txt`           | Python dependencies            | `pip install -r requirements.txt`                 |

### Quick Setup Options

#### 🚀 Fastest: Automated Setup

```bash
python setup_local.py
# Edit .env with your API keys
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 🐳 Docker: One Command Deploy

```bash
docker-compose -f docker-compose.backend.yml up --build
```

#### 🛠️ Manual: Full Control

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Create and edit .env file
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 🐛 Troubleshooting

### Common Issues

1. **Missing API Keys**

   ```
   Error: No valid LLM provider configuration found
   ```

   - Solution: Ensure at least one LLM API key is set in your `.env` file

2. **Port Already in Use**

   ```
   Error: [Errno 48] Address already in use
   ```

   - Solution: Change the port in `.env` or kill the process using port 8000

3. **Import Errors**

   ```
   ImportError: No module named 'some_module'
   ```

   - Solution: Ensure all dependencies are installed: `pip install -r requirements.txt`

4. **CORS Issues**
   - Solution: Update `FRONTEND_URL` in `.env` to match your frontend URL

### Development Tips

- Use `--reload` flag with uvicorn for auto-reloading during development
- Check logs for detailed error information
- Use `/docs` endpoint for interactive API testing
- Ensure your virtual environment is activated

## 📁 Project Structure

```
Backend/
├── main.py                      # FastAPI application entry point
├── api.py                       # Main API routes and logic
├── requirements.txt             # Python dependencies
├── README.md                    # This documentation file
├── setup_local.py              # Automated local development setup script
├── .env                         # Environment variables (create from template)
├── env_template.txt             # Original environment template
├── dockerfile                   # Docker image configuration
├── docker-compose.backend.yml   # Standalone Docker Compose configuration
├── .gitignore                   # Git ignore rules
│
├── # Core Application Files
├── enhanced_java_generator.py   # Advanced Java code generation
├── java_generator.py            # Basic Java code generation
├── uml_generator.py             # UML diagram generation
├── enhanced_uml_generator.py    # Advanced UML generation
├── vector_store.py              # Vector store management
├── create_embeddings.py         # Embedding creation utilities
├── llm_manager.py               # LLM provider management
├── fine_tuning.py              # Model fine-tuning utilities
├── enhanced_api.py             # Enhanced API endpoints
├── simple_enhanced_api.py      # Simplified API version
│
├── # Data and Storage
├── vector_store/               # Vector database storage
│   ├── chroma.sqlite3          # ChromaDB database
│   ├── index.faiss             # FAISS index
│   ├── index.pkl               # Pickled index data
│   └── [collection_dirs]/      # Individual collections
│
├── static/                     # Static files served by API
│   ├── uml/                    # Generated UML diagrams
│   └── java/                   # Generated Java code files
│
├── # Deployment Files
├── Procfile                    # Railway deployment configuration
├── railway.json               # Railway service configuration
│
└── # Development
    ├── venv/                  # Virtual environment (created by setup)
    └── __pycache__/          # Python cache files
```

## 🔄 Development Workflow

1. **Local Development**: Use uvicorn with `--reload` for hot reloading
2. **Testing**: Access `/docs` for interactive API testing
3. **Production**: Use Docker for consistent deployment
4. **Monitoring**: Check `/health` endpoint for service status

### Production Deployment Tips

#### Environment Variables for Production

```bash
ENVIRONMENT=production
PORT=8000
FRONTEND_URL=https://your-frontend-domain.com
LOG_LEVEL=WARNING
```

#### Docker Production Best Practices

```bash
# Build with specific tag
docker build -t backend-api:v1.0.0 .

# Run with resource limits
docker run -p 8000:8000 \
  --memory=512m \
  --cpus=1.0 \
  --restart=unless-stopped \
  --name backend-api \
  --env-file .env \
  backend-api:v1.0.0
```

#### Health Monitoring

```bash
# Check container health
docker ps --filter "name=backend-api"

# View logs
docker logs backend-api

# Monitor health endpoint
curl http://localhost:8000/health
```

## 🔗 Frontend Integration

For frontend integration, ensure the frontend is configured to connect to:

- **Local Development**: `http://localhost:8000`
- **Production**: Your deployed backend URL

### CORS Configuration

The backend automatically allows requests from:

- `http://localhost:3000` (React default)
- `http://localhost:5173` (Vite default)
- Custom URL set in `FRONTEND_URL` environment variable

## 🚀 Performance Tips

1. **Use Docker for production** - More consistent and reliable
2. **Set appropriate `LOG_LEVEL`** - Use `WARNING` or `ERROR` in production
3. **Monitor health endpoint** - Set up automated health checks
4. **Use environment variables** - Never hardcode API keys
5. **Enable vector store persistence** - Mount volumes for data persistence

## 📞 Support

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Verify your **environment variables** are set correctly
3. Ensure **API keys** are valid and have sufficient credits
4. Check the **logs** for detailed error messages
5. Test the **/health** endpoint to verify service status
