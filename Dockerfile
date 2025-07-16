FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only necessary application files
COPY main.py .
COPY db.py .
COPY dependency.py .
COPY oauth2.py .
COPY utils.py .
COPY models/ ./models/
COPY routers/ ./routers/
COPY schemas/ ./schemas/
COPY agent/ ./agent/
COPY .env .

# Create media directory
RUN mkdir -p media

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]