
FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY k-jarvis-opensource/mock-agents/personal-agent/requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy SDK from parent context (kt-opensource-project-jarvis)
COPY k-jarvis-sdk /tmp/k-jarvis-sdk
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org /tmp/k-jarvis-sdk


# Copy Agent Code
COPY k-jarvis-opensource/mock-agents/personal-agent /app

# Expose Port
EXPOSE 8081

# Run Agent
CMD ["python", "main.py"]
