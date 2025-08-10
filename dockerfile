# Use official lightweight Python image
FROM python:3.9-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies for mysqlclient and build tools
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files into container
COPY app/ .

# Create static folder if your app uses it
RUN mkdir -p static

# Command to run your app
CMD ["python", "app.py"]
