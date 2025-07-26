FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      git \
    && rm -rf /var/lib/apt/lists/*

# 1. Set workdir
WORKDIR /app

# 2. Copy only what we need for install
COPY setup.py .
COPY README.md .
COPY climatemaps ./climatemaps
COPY requirements.txt .

# 3. Install dependencies & your package
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir .

# 4. Copy the rest of your FastAPI app
COPY api/ .

# 5. Run Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
