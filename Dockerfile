FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create the files directory
RUN mkdir -p files

# Set environment variables
ENV PORT=8080
# Note: GEMINI_API should be passed at runtime or via Secret Manager

# Expose the application port
EXPOSE 8080

# Command to run the application with Gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app