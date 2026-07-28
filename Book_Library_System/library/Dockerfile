# Dockerfile
FROM python:3.11-slim

WORKDIR /Book_Library_System/library

# Install dependencies
COPY Book_Library_System/library/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Run migrations and start server
ENTRYPOINT ["sh", "Book_Library_System/library/commands.sh"]