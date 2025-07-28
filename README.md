# AI-Powered, Event-Driven Applicant Tracking System (ATS)

<p align="center">
  <img src="https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django" alt="Django"/>
  <img src="https://img.shields.io/badge/Celery-5.5-37814A?style=for-the-badge&logo=celery" alt="Celery"/>
  <img src="https://img.shields.io/badge/Kafka-3.7-231F20?style=for-the-badge&logo=apachekafka" alt="Kafka"/>
  <img src="https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Docker-20.10-2496ED?style=for-the-badge&logo=docker" alt="Docker"/>
</p>

## 1. Project Overview

This project is an advanced, enterprise-grade Applicant Tracking System (ATS) designed to streamline and automate modern recruitment workflows. It is architected as a robust, scalable, and event-driven system, leveraging **Artificial Intelligence**, **asynchronous task processing**, and a **message-driven pipeline** to handle high-volume CV processing with exceptional efficiency and reliability.

The entire application is **fully containerized with Docker**, allowing for a seamless, one-command setup and deployment in any environment, completely abstracting away the complexities of the underlying services.

---

## 2. Core Features

This platform is more than a simple CRUD application; it's a demonstration of modern backend architecture and intelligent data processing.

### Architectural & Backend Features

* **Fully Dockerized Environment:** The entire stack—including the web application, database, and all background services—is orchestrated with Docker Compose for one-command setup and guaranteed consistency across all development and production environments.
* **Asynchronous Task Processing with Celery:** Long-running, computationally expensive tasks, such as AI-powered CV analysis, are handled by Celery workers in the background. This ensures the web application remains fast and responsive at all times, never blocking the user's workflow.
* **Event-Driven Architecture with Apache Kafka:** A highly scalable and fault-tolerant CV processing pipeline has been implemented. Instead of direct communication, CV upload requests are published as events to a Kafka topic. This decouples the web application from the processing workers, providing a resilient buffer that ensures no data is lost even under extreme load.
* **Production-Ready Web Server:** The Django application is served via Gunicorn, a robust WSGI HTTP server suitable for production deployments, managed within its own Docker container.

### AI & Data Processing Features

* **AI-Powered CV Parsing:** Utilizes Google's Gemini API (`gemini-1.5-flash`) to intelligently extract key candidate details (first name, last name, email) from unstructured PDF resumes. Includes a RegEx-based fallback mechanism to ensure functionality even if the AI service fails.
* **Vector-Based (Semantic) Search:** Implements a sophisticated search functionality using PostgreSQL's `pg_trgm` extension. This allows for similarity-based searches that are tolerant of typos and can find closely related names and emails (e.g., searching for "selcuk" can match "semih"). The system ranks results by relevance, providing a superior search experience.

### User-Facing Features

* **Interactive Bulk CV Upload:** A user-friendly interface for uploading multiple CVs simultaneously. The system processes each CV in the background and provides real-time feedback to the user as results become available.
* **Real-time UI Updates with Polling:** The bulk upload interface uses a client-side polling mechanism. After submitting CVs, the frontend periodically queries a status-check API to fetch results for completed tasks, dynamically updating the UI without requiring a page reload.
* **AI-Powered Form Auto-filling:** A smart "Auto-fill from CV" feature on the candidate creation form that parses a selected CV and populates the form fields instantly, demonstrating a synchronous use case of the AI task.
* **Advanced Candidate Filtering:** A comprehensive filtering system on the main dashboard, allowing users to search and filter candidates by name/email (with vector search), the user who added them, and a specific date range.
* **Modern AJAX-Based UI:** All deletion operations are handled via asynchronous JavaScript (AJAX) calls, using Bootstrap modals for confirmation to provide a smooth, single-page application feel.

---

## 3. System Architecture Explained

The application is designed with a decoupled, service-oriented architecture. This design ensures that each component is independent, scalable, and resilient. The data flow for a typical asynchronous CV upload is as follows:

1.  **Request (Django `web` service):** The user uploads a CV via the Django web application.
2.  **Produce (Django `web` service):** The Django view acts as a **Kafka Producer**. It generates a unique Task ID, packages the CV data (file content, user info, etc.) into a JSON message, and publishes it to the `cv_processing_jobs` topic in **Kafka**. It then immediately returns this Task ID to the user's browser.
3.  **Consume (`kafka_consumer` service):** A dedicated **Kafka Consumer** service, running independently, is subscribed to the `cv_processing_jobs` topic. It receives the message from Kafka as soon as it's available.
4.  **Delegate (`kafka_consumer` service):** The Kafka Consumer's job is to delegate the heavy lifting. It creates a new task for **Celery**, passing along the CV data and the Task ID, and places it in the **Redis** message broker queue.
5.  **Process (`celery_worker` service):** A **Celery Worker** picks up the task from the Redis queue, performs the AI-powered parsing, and saves the final result (the extracted candidate data or an error message) back to **Redis**, using the unique Task ID as the key.
6.  **Poll & Update (User's Browser):** Meanwhile, the user's browser, which received the Task ID in step 2, **polls** a status-check API endpoint every few seconds. This API checks Redis for the Task ID. Once the result is found, the API returns the data, and the JavaScript in the browser updates the UI in real-time.

This event-driven flow ensures that the user gets an immediate response, and the system can handle a massive influx of CVs without slowing down or losing requests.

---

## 4. Technology Stack

| Category              | Technology                                                                                                  |
| --------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Backend** | Django, Django REST Framework, Gunicorn                                                                     |
| **Database** | PostgreSQL                                                                                                  |
| **Task Queue** | Celery                                                                                                      |
| **Message Broker** | Redis (for Celery), Apache Kafka (for event streaming)                                                      |
| **AI & Machine Learning** | Google Gemini API (`gemini-1.5-flash`)                                                                    |
| **Frontend** | HTML5, Bootstrap 5, JavaScript (AJAX, Polling)                                                              |
| **DevOps** | Docker, Docker Compose                                                                                      |

---

## 5. Getting Started: A Step-by-Step Guide

This project is fully containerized. The only prerequisite is to have **Docker** and **Docker Compose** installed on your system. No local installation of Python, PostgreSQL, or Kafka is required.

### Step 1: Clone the Repository

First, clone the project from GitHub to your local machine.

```bash
git clone [https://github.com/SerhatFiliz/hr_management_system.git](https://github.com/SerhatFiliz/hr_management_system.git)
cd hr_management_system
```

### Step 2: Configure Environment Variables

The project uses an `.env` file to manage all environment variables and secrets. This file is not committed to Git for security reasons. A template is provided.

Create your personal `.env` file by copying the example file:

```bash
# For macOS/Linux
cp env.example .env

# For Windows Command Prompt
copy env.example .env
```

Now, open the newly created `.env` file with a text editor and fill in your specific values. **At a minimum, you must provide a `SECRET_KEY` and your `GOOGLE_API_KEY`**.

```env
# .env

# Django Settings
SECRET_KEY=your-unique-and-random-secret-key
DEBUG=1

# PostgreSQL Settings for Docker
SQL_DATABASE=hr_management_db
SQL_USER=postgres
SQL_PASSWORD=admin123
SQL_HOST=db
SQL_PORT=5432

# Redis Settings for Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Kafka Settings
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_CV_TOPIC=cv_processing_jobs

# Google API Key for Gemini
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

### Step 3: Build and Run the Application

With the `.env` file configured, you can build the Docker images and launch all services with a single command.

```bash
docker compose up --build -d
```
* `--build`: This flag tells Docker Compose to build the application image from the `Dockerfile`. You only need to use this the first time or after changing `Dockerfile` or `requirements.txt`.
* `-d`: This flag runs the containers in "detached" mode, meaning they will run in the background and your terminal will be freed up.

The first time you run this command, it may take several minutes to download the base images (PostgreSQL, Kafka, etc.) and build the application image.

### Step 4: Create a Superuser

The database inside the Docker container is initially empty. To access the Django admin panel and use the application, you need to create a superuser.

Open a **new terminal window** (while the application is running) and execute the following command:

```bash
docker compose exec web python manage.py createsuperuser
```

Follow the prompts to create your admin username, email, and password.

### Step 5: Access the Application

Congratulations! The entire application stack is now running.

* **Web Application:** `http://localhost:8000`
* **Django Admin:** `http://localhost:8000/admin`

You can now log in with the superuser credentials you just created and start using the application.

---

## 6. Managing the Application

### Viewing Logs

To view the real-time logs of all running services, you can use:
```bash
docker compose logs -f
```
To view the logs of a specific service (e.g., the `kafka_consumer`), use:
```bash
docker compose logs -f kafka_consumer
```

### Stopping the Application

To stop all running services, navigate to the project directory in your terminal and run:
```bash
docker compose down
```
To stop the services and also remove the persistent database volume (deleting all data), use:
```bash
docker compose down -v
