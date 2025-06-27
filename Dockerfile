# FastAPI python application Dockerfile
# The python package is located in src/microblog and has the fastapi app in app.py

FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# The pyproject.toml file is copied from root directory to the working directory
COPY pyproject.toml .

# Copy the application code
COPY src /app/src

# Install dependencies
RUN pip install .

# Expose the port the app runs on
EXPOSE 8000

WORKDIR /app/src

# Upgrade database and start the app with uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn microblog.app:app --host 0.0.0.0 --port 8000"]