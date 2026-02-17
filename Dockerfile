# 1. Start with a Linux computer that already has Python 3.11 installed
FROM python:3.11-slim

# 2. Create a folder inside the container to hold our app
WORKDIR /app

# 3. Copy our "Inventory List" into the container
COPY requirements.txt .

# 4. Install the libraries inside the container
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy all our code (main.py, schemas.py, .env) into the container
COPY . .

# 6. Tell the world that this container listens on port 8007
EXPOSE 8007

# 7. The command to run when the container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
