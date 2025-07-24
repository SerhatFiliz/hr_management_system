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

# --- DÜZELTME BURADA ---
# Step 6: Copy the entrypoint script AND make it executable
# entrypoint.sh dosyasını kopyalayın ve çalıştırılabilir hale getirin
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Step 7: Copy the rest of the application code into the container
# entrypoint.sh'den SONRA kopyalanmalı
COPY . .

# Step 8: Expose the port the app runs on
EXPOSE 8000

# Step 9: Define the entrypoint for the container.
# This will run our setup script before starting the main process.
ENTRYPOINT ["/app/entrypoint.sh"]

# Step 10: Define the default command that will be passed as arguments to ENTRYPOINT.
# docker-compose.yml'deki command bu CMD'yi geçersiz kılar, bu normaldir.
# Önemli olan, entrypoint.sh'nin kendisinin bulunması ve doğru argümanları almasıdır.
# entrypoint.sh'deki "exec "$@"" komutu bu CMD'yi veya docker-compose'daki command'i çalıştırır.
CMD ["gunicorn", "hr_management_system.wsgi:application", "--bind", "0.0.0.0:8000"]