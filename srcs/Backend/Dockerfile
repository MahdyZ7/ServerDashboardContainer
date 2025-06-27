FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN apt-get update && apt-get install -y gcc libpq-dev
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the API runs on
EXPOSE 5000

# Set environment variable for Flask
ENV FLASK_APP=api.py

# Run the API
CMD ["python", "api.py"]
