# HR Core - HR Management System

HR Core is a web application designed for Human Resources (HR) employees to manage job postings and candidate profiles on behalf of their respective companies. The system provides a secure authentication mechanism, role-based authorization, and an optional AI-powered feature for generating job titles.

---

## Features

- **User Management:** Secure registration and login functionality for HR employees.
- **Company Association:** Each user is associated with a company. New companies are created automatically during registration if they don't already exist.
- **Authorization:** Users can only view and manage job postings and candidates belonging to their own company.
- **Job Posting Management (CRUD):**
    - Create, list, update, and delete job postings.
    - View a detail page for each job posting.
- **Candidate Management (CRUD):**
    - Create and update candidate profiles.
    - Upload and view candidate resumes (PDF format only).
- **Application System:**
    - Link existing candidates to specific job postings to create an application record.
    - Update the status of each application (e.g., Pending, Reviewed, Hired).
- **AI-Powered Title Generation (Optional):** An "Suggest Title with AI" button on the job posting form sends the description to an external API (Hugging Face) to generate a concise title.

---

## Technology Stack

- **Backend:** Python 3.x, Django 5.x
- **Database:** PostgreSQL
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
- **API Integration:** Python `requests` library for communicating with the Hugging Face Inference API.
- **Environment Management:** `python-dotenv` for managing environment variables.

---

## Setup and Installation

Follow these steps to set up and run the project locally.

### 1. Prerequisites

- Python 3.10 or higher
- PostgreSQL installed and running
- Git

### 2. Clone the Repository

```bash
git clone [https://github.com/SerhatFiliz/hr_management_system.git](https://github.com/SerhatFiliz/hr_management_system.git)
cd hr_management_system
```

### 3. Set Up the Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies

Install all the required packages from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 5. Configure the Database

- Create a new database in PostgreSQL. For example, you can name it `hrcore_db`.
- Make sure the PostgreSQL server is running.

### 6. Set Up Environment Variables

The project uses a `.env` file to manage sensitive information like database credentials and API keys.

- In the root directory of the project, create a new file named `.env`.
- Copy the contents of `.env.example` (if provided) or add the following variables to your `.env` file and replace them with your actual credentials.

```bash
# .env file

# --- DATABASE CONFIGURATION ---
DB_NAME="hrcore_db"
DB_USER="your_postgres_username"
DB_PASSWORD="your_postgres_password"
DB_HOST="localhost"
DB_PORT="5432"

# --- DJANGO SECRET KEY ---
# Generate a new secret key. You can use an online generator.
SECRET_KEY="your_django_secret_key"

# --- HUGGING FACE API SETTINGS ---
HUGGING_FACE_API_URL="[https://api-inference.huggingface.co/models/facebook/bart-large-cnn](https://api-inference.huggingface.co/models/facebook/bart-large-cnn)"
HUGGING_FACE_API_KEY="your_hugging_face_api_key"
```

### 7. Run Database Migrations

Apply the database schema to your newly created database.

```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. Create a Superuser

Create an admin account to access the Django admin panel.

```bash
python manage.py createsuperuser
```
Follow the prompts to create your superuser account. After creating it, you will need to log into the admin panel (`/admin/`) to create an `Employee` profile for this user and associate it with a company.

### 9. Run the Development Server

You are now ready to run the project!

```bash
python manage.py runserver
```
The application will be available at `http://127.0.0.1:8000/`.

---

## Usage

1.  **Register:** Navigate to the registration page to create a new HR employee account and associate it with a company.
2.  **Login:** Use your credentials to log in.
3.  **Dashboard:** After logging in, you will be redirected to the main dashboard where you can see lists of job postings and candidates for your company.
4.  **Manage Jobs:** Use the "Create Job Posting" button to add new jobs. Use the "Edit" and "Delete" buttons in the list to manage existing ones.
5.  **Manage Candidates:** Use the "Add Candidate" button to add new candidates and upload their resumes.
6.  **Manage Applications:** Click on a job posting title to go to its detail page. From there, you can add existing candidates to the job to create an application and update the status of existing applications.
