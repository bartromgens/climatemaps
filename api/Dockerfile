FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY setup.py .
COPY README.md .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install climatemaps package
COPY climatemaps ./climatemaps
RUN pip install --no-cache-dir .

# Copy the rest of your FastAPI app
COPY api/ .

# 5. Run Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
