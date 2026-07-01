import bcrypt
import pg8000.dbapi
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR)

class OncologyDatabase:
    """CRUD operations for Oncology Patient Database in PostgreSQL (Pure Python)"""
    
    def __init__(self, user, password, host, port, db):
        self.connection = None
        self.cursor = None
        
        try:
            # This is to connect to the postgres DB using pg8000
            self.connection = pg8000.dbapi.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database=db
            )
            self.cursor = self.connection.cursor()
            print("Connected successfully to PostgreSQL Patient Database")
        except Exception as e:
            logging.error(f"Could not connect to PostgreSQL: {e}")

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def create(self, patient_data):
        """Inserts a new patient record."""
        if not self.connection:
            return False

        try:
            columns = list(patient_data.keys())
            values = [patient_data[column] for column in columns]
            
            # This is to use the pg8000  %s for parameter substitution
            placeholders = ','.join(['%s'] * len(values))
            insert_statement = f"INSERT INTO patients ({','.join(columns)}) VALUES ({placeholders})"
            
            # This is to execute and commit
            self.cursor.execute(insert_statement, tuple(values))
            self.connection.commit()
            return True
        except Exception as e:
            logging.error(f"Error inserting patient data: {e}")
            self.connection.rollback()
            return False

    def read_all(self):
        """Fetches all patients for the dashboard and returns them as dictionaries."""
        if not self.connection:
            return []

        try:
            self.cursor.execute("SELECT * FROM patients;")
            rows = self.cursor.fetchall()
            
            # This is to extract the column names from the cursor description
            columns = [desc[0] for desc in self.cursor.description]
            
            # This converts the tuples back into a list of dictionaries 
            dict_rows = [dict(zip(columns, row)) for row in rows]
            
            return dict_rows
            
        except Exception as e:
            logging.error(f"Error reading patient data: {e}")
            self.connection.rollback()
            return []
        def register_employee(self, username, plain_password, role='viewer'):
        """Hashes a password and creates a new employee record."""
        if not self.connection: return False
        
        # This is to generate secure salt and to hash the password
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
            # this is to set query as to prevent SQL injection
            self.cursor.execute("SELECT password_hash, role FROM employees WHERE username = %s", (username,))
            result = self.cursor.fetchone()

            if result:
                stored_hash, role = result
                # This is to compare the incoming password against the stored hash
                if bcrypt.checkpw(plain_password.encode('utf-8'), stored_hash.encode('utf-8')):
                    return role # Authentication successful
            
            return None # This is to authenticated failed (wrong username or password)
        except Exception as e:
            logging.error(f"Login error: {e}")
            return None