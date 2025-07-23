# Step 1: Use an official Python runtime as a parent image
FROM python:3.10-slim-bullseye

# Step 2: Set environment variables
# Prevents Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED 1

# Step 3: Set the working directory in the container
WORKDIR /app

# Step 4: Install system dependencies (if any)
# We don't have any for now, but this is where they would go.
# RUN apt-get update && apt-get install -y ...

# Step 5: Install Python dependencies
# Copy the requirements file first to leverage Docker's layer caching.
# If requirements.txt doesn't change, Docker won't re-install dependencies on every build.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 6: Copy the entrypoint script
COPY ./entrypoint.sh /app/entrypoint.sh
# Make the script executable
RUN chmod +x /app/entrypoint.sh

# Step 7: Copy the rest of the application code into the container
COPY . .

# Step 8: Expose the port the app runs on
EXPOSE 8000

# Step 9: Define the entrypoint for the container.
# This will run our setup script before starting the main process.
ENTRYPOINT ["/app/entrypoint.sh"]