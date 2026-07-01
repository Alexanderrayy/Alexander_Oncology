import bcrypt
import logging
import pg8000.dbapi

class OncologyDatabase:
    
    def __init__(self, user, password, host, port, db):
        # This sets connection variables to None 
        self.connection = None
        self.cursor = None
        
       #This checks for tge values using strings
        if port == "" or port == "None" or port == None or port == 0:
            connection_port = 5432
        else:
            connection_port = int(port)
            
        try:
            # This is to establish connection using the library (pg8000 library)
            self.connection = pg8000.dbapi.connect(
                user=str(user),
                password=str(password),
                host=str(host),
                port=connection_port,
                database=str(db)
            )
            self.cursor = self.connection.cursor()
            print("Connected successfully to Supabase Cloud PostgreSQL Database!")
        except Exception as e:
            print("Could not connect to Supabase database! Error was:")
            print(e)

    def close(self):
        # This is to check if they exist before closing them
        if self.cursor is not None:
            self.cursor.close()
        if self.connection is not None:
            self.connection.close()

    def create(self, patient_data):
        #this is to ensure a database connection before doing anything else
        if self.connection is None:
            return False

        try:
            #This is the insert SQL 
            pid = patient_data["patient_id"]
            ctype = patient_data["cancer_type"]
            sev = patient_data["severity"]
            treat = patient_data["treatment"]
            lat = patient_data["location_lat"]
            long = patient_data["location_long"]
            
            # This is the SQL query
            insert_statement = "INSERT INTO patients (patient_id, cancer_type, severity, treatment, location_lat, location_long) VALUES (%s, %s, %s, %s, %s, %s)"
            
            # This combines values into a matching list to pass to the database executor
            all_values = (pid, ctype, sev, treat, lat, long)
            
            self.cursor.execute(insert_statement, all_values)
            self.connection.commit()
            return True
            
        except Exception as e:
            print("Error inserting patient data into the table!")
            print(e)
            self.connection.rollback()
            return False

    def read_all(self):
        if self.connection is None:
            return []

        try:
            # This runs the fetch query
            self.cursor.execute("SELECT * FROM patients;")
            rows = self.cursor.fetchall()
            
           #This a loop through the tuples to construct dictionary keys.
            patient_list = []
            
            for row in rows:
               
                # this has the options for patient including: patient_id, 1: cancer_type, 2: severity, 3: treatment, 4: location_at, 5: location_long
                patient_dict = {
                    "patient_id": row[0],
                    "cancer_type": row[1],
                    "severity": row[2],
                    "treatment": row[3],
                    "location_lat": row[4],
                    "location_long": row[5]
                }
                patient_list.append(patient_dict)
                
            return patient_list
            
        except Exception as e:
            print("Error reading patient data from database!")
            print(e)
            self.connection.rollback()
            return []
    def register_employee(self, username, plain_password, role='viewer'):
        """Hashes a password and creates a new employee record."""
        if not self.connection: return False
        
        # Generate a secure salt and hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')
        
        try:
            insert_query = "INSERT INTO employees (username, password_hash, role) VALUES (%s, %s, %s)"
            self.cursor.execute(insert_query, (username, hashed, role))
            self.connection.commit()
            print(f"Employee {username} registered successfully.")
            return True
        except Exception as e:
            logging.error(f"Error registering employee: {e}")
            self.connection.rollback()
            return False

    def verify_employee(self, username, plain_password):
        """Verifies credentials. Returns the employee's role if successful, None otherwise."""
        if not self.connection: return None

        try:
            # This query helps prevent SQL injection
            self.cursor.execute("SELECT password_hash, role FROM employees WHERE username = %s", (username,))
            result = self.cursor.fetchone()

            if result:
                stored_hash, role = result
                # this compares the incoming password against the stored hash
                if bcrypt.checkpw(plain_password.encode('utf-8'), stored_hash.encode('utf-8')):
                    return role # Authentication successful
            
            return None # This is in case of athentication fail (wrong username or password)
        except Exception as e:
            logging.error(f"Login error: {e}")
            return None    