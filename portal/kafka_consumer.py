# ==============================================================================
# KAFKA CONSUMER SCRIPT
# This script runs as a standalone, long-running process in its own Docker container.
# It acts as a "consumer" that listens to a Kafka topic, receives messages,
# and then triggers the appropriate backend process (our Celery task) to handle the job.
# ==============================================================================

import os
import json
import time

# STEP 1: SETUP DJANGO ENVIRONMENT
# ---------------------------------
# This is a standard pattern for standalone scripts that need to interact with a Django project.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_management_system.settings')
import django
django.setup()

# STEP 2: IMPORT NECESSARY LIBRARIES AND TASKS
# ---------------------------------------------
from kafka import KafkaConsumer
from portal.tasks import process_single_cv

# STEP 3: CONFIGURE KAFKA CONNECTION
# ----------------------------------
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_CV_TOPIC = os.getenv('KAFKA_CV_TOPIC')
CONSUMER_GROUP_ID = 'cv_processor_group' # All instances of this consumer will join this group.

def create_consumer():
    """
    Creates and returns a KafkaConsumer instance, retrying connection on failure.
    """
    while True:
        try:
            print("Attempting to connect to Kafka as a consumer...")
            consumer = KafkaConsumer(
                KAFKA_CV_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
                group_id=CONSUMER_GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest'
            )
            print("Kafka Consumer connected successfully!")
            return consumer
        except Exception as e:
            print(f"Could not connect to Kafka Consumer: {e}. Retrying in 5 seconds...")
            time.sleep(5)

# STEP 4: MAIN CONSUMPTION LOOP
# -----------------------------
def consume_messages():
    """
    Listens for messages on the Kafka topic and triggers the Celery task for each one.
    """
    consumer = create_consumer()
    print(f"Consumer is now listening for messages on topic: '{KAFKA_CV_TOPIC}'...")
    
    for message in consumer:
        try:
            job_data = message.value
            print(f"Received new job from Kafka: {job_data.get('original_filename')}")

            task_id_from_message = job_data.get('task_id')

            # =================================================================
            # ===== THE FIX: Call the Celery task with create_candidate=False =====
            # =================================================================
            # The consumer's job is ONLY to get the data ready for the review screen.
            # It should NEVER create a candidate in the database. The final creation
            # is handled by the 'save_candidates_api_view' after the user's approval.
            process_single_cv.delay(
                file_content_b64=job_data['file_content_b64'],
                original_filename=job_data['original_filename'],
                company_id=job_data['company_id'],
                created_by_id=job_data['created_by_id'],
                create_candidate=False, # This is the critical fix.
                task_id=task_id_from_message
            )
            print(f"Job for '{job_data.get('original_filename')}' with task_id {task_id_from_message} has been sent to Celery worker for PARSING ONLY.")

        except Exception as e:
            print(f"Error processing message: {message.value}. Error: {e}")

# This ensures the script starts running when executed from the command line.
if __name__ == '__main__':
    consume_messages()
