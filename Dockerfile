FROM python:3.12-slim

# 1. Install system dependencies for XGBoost and Postgress
RUN apt-get update && apt-get install -y libpq-dev gcc g++ && rm -rf /var/lib/apt/lists/*

WORKDIR /project

# 2. Layer caching for requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy everything (app/, tml-data/, migrations/)
COPY . .

# 4. CRITICAL: Set PYTHONPATH so 'import app' works from /project
ENV PYTHONPATH=/project

# 5. Start Uvicorn with --reload for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
