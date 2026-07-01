import random
import time
from faker import Faker
from patient_database import OncologyDatabase 

print("Starting the data generator script...")

#This is to bring in Faker 
fake = Faker()

#This is to connect to the database
db = OncologyDatabase(
    user="postgres",
    password="MrMsAdmin26!", 
    host="db.kpjbkugqexfngdpenybn.supabase.co",
    port=5432, 
    db="postgres"
)

# this is the list of choices for randomized program to select from
CANCER_TYPES = ["Breast", "Lung", "Prostate", "Colorectal", "Melanoma", "Leukemia", "Lymphoma", "Pancreatic"]
SEVERITIES = ["Stage I", "Stage II", "Stage III", "Stage IV", "Remission"]
TREATMENTS = ["Chemotherapy", "Radiation therapy", "Surgery", "Immunotherapy", "Targeted therapy", "Hormone therapy", "Observation"]

# This is to track how many successfully save to the database
success_count = 0
total_to_generate = 500

print("Connected! Starting the loop to make 500 patients...")

# this is a list to keep track of IDs we already used so we don't end up with duplicates
used_ids = []

for i in range(total_to_generate):
    
   #this is to generate a number and check if we used it
    while True:
        num = random.randint(100000, 999999)
        patient_id = "PAT-" + str(num)
        if patient_id not in used_ids:
            used_ids.append(patient_id)
            break
    # this picks random items from lists using random.choice
    chosen_type = random.choice(CANCER_TYPES)
    chosen_severity = random.choice(SEVERITIES)
    chosen_treatment = random.choice(TREATMENTS)

    # This generates latitude and longitude decimals
    lat = round(random.uniform(25.0, 49.0), 6)
    long = round(random.uniform(-125.0, -70.0), 6)

    # This builds the dictionary row to exactly match the database table columns
    patient = {
        "patient_id": patient_id,
        "cancer_type": chosen_type,
        "severity": chosen_severity,
        "treatment": chosen_treatment,
        "location_lat": lat,
        "location_long": long
    }
    
    # This sends it to the database
    result = db.create(patient)
    if result == True:
        success_count = success_count + 1 # Basic manual counter instead of +=
        
    # This prints out progress every 100 times
    if i == 99 or i == 199 or i == 299 or i == 399 or i == 499:
        print("Processed " + str(i + 1) + " records so far...")

# This prints the final summary results
print("\n--- ALL DONE ---")
print("Successfully inserted " + str(success_count) + " new patient records!")

# THis safely closes the database connection 
db.close()