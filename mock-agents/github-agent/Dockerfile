
FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY k-jarvis-opensource/mock-agents/github-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy SDK from parent context
COPY k-jarvis-sdk /tmp/k-jarvis-sdk
RUN pip install /tmp/k-jarvis-sdk

# Copy Agent Code
COPY k-jarvis-opensource/mock-agents/github-agent /app

# Expose Port
EXPOSE 8082

# Run Agent
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]
