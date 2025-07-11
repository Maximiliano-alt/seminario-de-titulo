FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY Backend/requirements-railway.txt .
RUN pip install --no-cache-dir -r requirements-railway.txt

# Copy Backend application code
COPY Backend/ .

# Create static directories
RUN mkdir -p static/uml static/java

# Start the application
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"] 