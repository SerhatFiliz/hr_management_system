HR Management System This project is a web application that enables HR employees to create job postings on behalf of their affiliated companies, manage candidate profiles who apply for these positions, and automate business processes through AI integration. The system is built on a secure authentication infrastructure and an authorization mechanism that ensures each user can only access their own company's data.

✨ Key Features

    User Management: Secure registration and login system for HR employees.
    
    Dynamic Company Management: During registration, if the mentioned company does not exist in the database, it is created automatically; if it exists, it is associated with the existing one.
    
    Authorization: Each user can only view and manage the job postings and candidate profiles belonging to their own company.
    
    Job Posting Management: Create, Read, Update, and Delete (CRUD) operations for job postings on behalf of the company.
    
    Candidate Profile Management: Creation and listing of profiles for job applicants, including name, surname, email, and resume (PDF).
    
    Secure File Management: Resumes are accepted only in PDF format and stored securely on the server.
    
    AI Integration (Optional): After entering a job description, an AI API like Gemini can be called with a single click to automatically generate the most suitable job title.
🛠️ Technologies Used

    The following technologies and libraries were used in the development of this project:
    
    Backend: Python 3.x, Django 5.x
    
    Database: PostgreSQL
    
    Artificial Intelligence API: Integration with modern LLM APIs such as Hugging Face, Groq, or Gemini.
    
    API Requests: requests library
    
    Frontend (Optional): Basic HTML, CSS, and JavaScript (AJAX)
🚀 Setup and Installation

    You can follow the steps below to run the project on your local machine.
    
    1. Clone the Repository:
    
    git clone https://github.com/your-username/hr_management_system.git
    cd hr_management_system
    
    2. Create and Activate a Virtual Environment:
    
    # Create the virtual environment
    python -m venv venv
    
    # Activate on Windows
    venv\Scripts\activate
    
    # Activate on macOS/Linux
    source venv/bin/activate
    
    3. Install Required Packages:
    All necessary libraries for the project are listed in the requirements.txt file.
    
    pip install -r requirements.txt
    
    4. Configure Database Settings:
    
    Create a database for your project in PostgreSQL.
    
    Copy the .env.example file in the project's root directory to .env.
    
    Fill in the fields in the .env file, such as the database name (DB_NAME), user (DB_USER), and password (DB_PASSWORD), with your own information.
    
    5. Create Database Tables:
    The following command will create the database schema.
    
    python manage.py migrate
    
    6. Start the Development Server:
    
    python manage.py runserver
    
    Your project will now be running at http://127.0.0.1:8000/!
