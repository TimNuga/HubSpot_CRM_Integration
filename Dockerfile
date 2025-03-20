FROM python:3.9-slim

WORKDIR /app

# Install netcat for the wait-for.sh script
RUN apt-get update && apt-get install -y netcat-openbsd gcc build-essential && \
    apt-get install -y netcat-openbsd libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Make scripts executable
RUN chmod +x /app/scripts/entrypoint.sh && chmod +x /app/scripts/wait-for.sh

# Expose port
EXPOSE 5001

ENV FLASK_ENV=production
ENV RUN_TESTS=0

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
