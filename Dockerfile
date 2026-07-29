# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

RUN chmod +x /app/commands.sh
# Run migrations and start server
ENTRYPOINT ["/app/commands.sh"]