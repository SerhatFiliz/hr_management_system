# Step 1: Use an official Python runtime as a parent image
FROM python:3.10-slim-bullseye

# Step 2: Set environment variables
# Prevents Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED 1

# ==============================================================================
# ===== THE FIX: Set the PYTHONPATH environment variable =====
# ==============================================================================
# This is a critical step. It tells Python to include the project's root directory (/app)
# when it looks for modules to import. This allows standalone scripts like 'celery'
# and 'kafka_consumer.py' to find and import your project's modules, such as
# 'hr_management_system.settings'.
ENV PYTHONPATH /app

# Step 3: Set the working directory in the container
WORKDIR /app

# Step 4: Install Python dependencies
# Copy the requirements file first to leverage Docker's layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the entrypoint script
COPY ./entrypoint.sh /app/entrypoint.sh
# Make the script executable
RUN chmod +x /app/entrypoint.sh

# Step 6: Copy the rest of the application code into the container
COPY . .

# Step 7: Expose the port the app runs on
EXPOSE 8000

# Step 8: Define the entrypoint for the contai  ner.
# This will run our setup script before starting the main process.
ENTRYPOINT ["/app/entrypoint.sh"]
