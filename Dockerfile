FROM python:3.12-slim
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev curl jq && rm -rf /var/lib/apt/lists/*
WORKDIR /project
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# We'll use this to keep the container alive while we run migrations
CMD ["tail", "-f", "/dev/null"]
