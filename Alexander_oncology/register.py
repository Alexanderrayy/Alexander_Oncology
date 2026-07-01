from patient_database import OncologyDatabase

# Connect using your existing credentials
db = OncologyDatabase(
    user="postgres",
    password="MrMsAdmin26!", 
    host="db.kpjbkugqexfngdpenybn.supabase.co",
    port=5432,
    db="postgres"
)

#this is to register the sample user
db.register_employee("admin", "securepassword123", "admin")
db.close()