HR Core - AI-Powered HR Management System
HR Core is an intelligent web application designed for Human Resources (HR) employees to streamline their recruitment workflow. The system provides secure authentication, role-based authorization, and leverages asynchronous task processing and artificial intelligence to automate time-consuming tasks.

Features
User Management: Secure registration and login functionality for HR employees.

Company Association: Each user is associated with a company. New companies are created automatically during registration if they don't already exist.

Authorization: Users can only view and manage job postings and candidates belonging to their own company.

Job Posting Management (CRUD):

Create, list, update, and delete job postings.

View a detail page for each job posting.

Candidate Management (CRUD):

Create and update candidate profiles.

Upload and view candidate resumes (PDF format only).

Application System:

Link existing candidates to specific job postings to create an application record.

Update the status of each application (e.g., Pending, Reviewed, Hired).

AI-Powered Title Generation (Optional): An "Suggest Title with AI" button on the job posting form sends the description to an external API to generate a concise title.

Automatic Job Posting Deactivation:

Utilizes Celery Beat to run a scheduled task every morning.

This task automatically finds job postings whose closing_date has passed and sets their status to "Inactive", ensuring the job board is always up-to-date without manual intervention.

AI-Powered Bulk CV Upload & Parsing:

Allows HR employees to upload multiple candidate CVs (PDFs) at once.

Each uploaded CV is processed in the background by a Celery worker to prevent UI freezing.

The system uses the Google Gemini API to read the text from each CV and intelligently extract key information like first_name, last_name, and email.

A new Candidate profile is automatically created in the database using the information extracted by the AI, enabling rapid candidate registration.

Technology Stack
Backend: Python 3.x, Django 5.x

Database: PostgreSQL

Asynchronous Tasks: Celery

Message Broker: Redis

AI Integration: Google Gemini API (google-generativeai), PyPDF2

Frontend: HTML5, CSS3, JavaScript, Bootstrap 5, django-crispy-forms

Environment Management: python-dotenv

Setup and Installation
Follow these steps to set up and run the project locally.

1. Prerequisites
Python 3.10 or higher

PostgreSQL installed and running

Redis installed and running

Git

2. Clone the Repository
git clone https://github.com/SerhatFiliz/hr_management_system.git
cd hr_management_system

3. Set Up the Virtual Environment
It is highly recommended to use a virtual environment to manage project dependencies.

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

4. Install Dependencies
Install all the required packages from the requirements.txt file.

pip install -r requirements.txt

5. Configure the Database
Create a new database in PostgreSQL. For example, you can name it hrcore_db.

Make sure the PostgreSQL server is running.

6. Set Up Environment Variables
The project uses a .env file to manage sensitive information like database credentials and API keys.

In the root directory of the project, create a new file named .env.

Add the following variables to your .env file and replace the placeholder values with your actual credentials.

# .env file

# --- DATABASE CONFIGURATION ---
DB_NAME="hrcore_db"
DB_USER="your_postgres_username"
DB_PASSWORD="your_postgres_password"
DB_HOST="localhost"
DB_PORT="5432"

# --- DJANGO SECRET KEY ---
# Generate a new secret key for your project.
SECRET_KEY="your_django_secret_key"

# --- GOOGLE GEMINI API KEY ---
# Get your free API key from Google AI Studio.
GOOGLE_API_KEY="your_google_gemini_api_key"

7. Run Database Migrations
Apply the database schema to your newly created database.

python manage.py makemigrations
python manage.py migrate

8. Create a Superuser
Create an admin account to access the Django admin panel.

python manage.py createsuperuser

After creating the superuser, you must log into the admin panel (/admin/) to create an Employee profile for this user and associate it with a company.

9. Running the Project
To run the full application with all its features, you will need to run three separate services in three separate terminals.

Terminal 1: Run the Django Development Server

python manage.py runserver

Terminal 2: Run the Celery Worker
This service listens for and executes background tasks (like processing CVs).

celery -b redis://localhost:679/0 -A hr_management_system worker -l info -P solo

Terminal 3: Run the Celery Beat Scheduler
This service triggers scheduled tasks (like deactivating old job postings).

celery -A hr_management_system beat -l info

The application will be available at http://127.0.0.1:8000/.

Usage
Register: Navigate to the registration page to create a new HR employee account and associate it with a company.

Login: Use your credentials to log in.

Dashboard: After logging in, you will be redirected to the main dashboard where you can see lists of job postings and candidates for your company.

Manage Jobs & Candidates: Use the buttons to create, edit, and delete jobs and candidates.

Bulk Upload CVs: Use the "Bulk Upload CVs" button to upload multiple PDF resumes. The system will process them in the background and automatically create new candidate profiles.

Manage Applications: Click on a job posting title to go to its detail page. From there, you can add existing candidates to the job to create an application and update the status of existing applications.