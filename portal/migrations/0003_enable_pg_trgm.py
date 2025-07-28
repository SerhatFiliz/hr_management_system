# This is a custom database migration created to enable the 'pg_trgm' PostgreSQL extension.

# STEP 1: Import the necessary modules from Django.
from django.db import migrations
# This specific import provides access to PostgreSQL-specific operations, like enabling extensions.
from django.contrib.postgres.operations import TrigramExtension

class Migration(migrations.Migration):
    """
    What is pg_trgm?
    -----------------
    'pg_trgm' (PostgreSQL Trigram) is an official extension that provides functions
    and operators for determining the similarity of alphanumeric text based on trigram matching.
    A trigram is a group of three consecutive characters taken from a string. For example,
    the string "hello" is composed of the trigrams: " h", "he ", "hel", "ell", "llo", "lo ".
    
    Why do we need it?
    -------------------
    By enabling this extension, we gain access to advanced text-search capabilities that go
    beyond simple 'exact' or 'contains' matches. We can query the database for records that are
    "similar" to a search term, which is the foundation for our vector-based (or more accurately,
    similarity-based) search feature. This allows the system to handle typos and find closely
    related terms (e.g., a search for "selcuk" can return results like "semih").

    Why is this done in a migration file?
    ---------------------------------
    Placing this database-level setup in a migration file ensures that the extension is
    enabled in every environment where this project is deployed (development, testing, production).
    When 'python manage.py migrate' is run, Django will execute this operation, making the
    setup process automated, version-controlled, and reliable.
    """

    # STEP 2: Define Dependencies.
    # The 'dependencies' list tells Django which migrations must be run before this one.
    # This is crucial to ensure that the tables we might want to use this extension on already exist.
    dependencies = [
        # IMPORTANT: Replace '0001_initial' with the name of your LAST migration file in the 'portal' app.
        # You can find this by looking at the other files in the 'portal/migrations/' directory.
        ('portal', '0001_initial'), 
    ]

    # STEP 3: Define the Database Operations.
    # The 'operations' list contains the database actions to be performed when this migration is run.
    operations = [
        # This is the specific operation that tells Django to execute the
        # 'CREATE EXTENSION IF NOT EXISTS pg_trgm;' SQL command in the PostgreSQL database.
        # It's idempotent, meaning running it multiple times will not cause an error.
        TrigramExtension(),
    ]
