# Use a lightweight Python 3.11 image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# 1. Copy just the requirements first (this makes rebuilding faster)
COPY requirements.txt .

# 2. Install all the libraries we've been using (fastapi, litellm, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the rest of your code (app folder, brain.py, etc.)
COPY . .

# 4. Create empty folders so the agent has a place to look for data
RUN mkdir -p data logs docs

# 5. Tell the container to listen on port 8000
EXPOSE 8000

# 6. The command to start your API
CMD ["python3", "-m", "uvicorn", "app.backend.api:app", "--host", "0.0.0.0", "--port", "8000"]