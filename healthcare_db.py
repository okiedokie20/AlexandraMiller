import sqlite3
from typing import List, Dict, Optional
from datetime import datetime

class HealthcareDatabase:
    def __init__(self, db_name: str = "healthcare.db"):
        """Initialize the database connection and create tables"""
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """Create the necessary tables for healthcare records"""
        # Patients table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth DATE NOT NULL,
            gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
            phone TEXT,
            email TEXT UNIQUE,
            address TEXT,
            blood_type TEXT CHECK(blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'))
        )
        """)

        # Medical records table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS medical_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            visit_date DATE NOT NULL,
            diagnosis TEXT,
            treatment TEXT,
            medications TEXT,
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
        )
        """)

        # Appointments table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            appointment_date DATETIME NOT NULL,
            purpose TEXT,
            status TEXT DEFAULT 'Scheduled' CHECK(status IN ('Scheduled', 'Completed', 'Cancelled')),
            FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
        )
        """)

        self.conn.commit()

    def add_patient(self, first_name: str, last_name: str, date_of_birth: str, 
                   gender: str, phone: str = None, email: str = None, 
                   address: str = None, blood_type: str = None) -> int:
        """Add a new patient to the database"""
        try:
            self.cursor.execute("""
            INSERT INTO patients (first_name, last_name, date_of_birth, gender, 
                                 phone, email, address, blood_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, date_of_birth, gender, 
                  phone, email, address, blood_type))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError as e:
            print(f"Error adding patient: {e}")
            return -1

    def add_medical_record(self, patient_id: int, visit_date: str, diagnosis: str = None, 
                          treatment: str = None, medications: str = None, notes: str = None) -> int:
        """Add a medical record for a patient"""
        try:
            self.cursor.execute("""
            INSERT INTO medical_records (patient_id, visit_date, diagnosis, 
                                      treatment, medications, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (patient_id, visit_date, diagnosis, treatment, medications, notes))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error adding medical record: {e}")
            return -1

    def schedule_appointment(self, patient_id: int, appointment_date: str, 
                           purpose: str, status: str = "Scheduled") -> int:
        """Schedule a new appointment"""
        try:
            self.cursor.execute("""
            INSERT INTO appointments (patient_id, appointment_date, purpose, status)
            VALUES (?, ?, ?, ?)
            """, (patient_id, appointment_date, purpose, status))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error scheduling appointment: {e}")
            return -1

    def get_patient_by_id(self, patient_id: int) -> Optional[Dict]:
        """Retrieve a patient by their ID"""
        self.cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        patient = self.cursor.fetchone()
        if patient:
            return {
                "patient_id": patient[0],
                "first_name": patient[1],
                "last_name": patient[2],
                "date_of_birth": patient[3],
                "gender": patient[4],
                "phone": patient[5],
                "email": patient[6],
                "address": patient[7],
                "blood_type": patient[8]
            }
        return None

    def search_patients(self, name: str = None, gender: str = None) -> List[Dict]:
        """Search for patients by name or gender"""
        query = "SELECT * FROM patients WHERE 1=1"
        params = []
        
        if name:
            query += " AND (first_name LIKE ? OR last_name LIKE ?)"
            params.extend([f"%{name}%", f"%{name}%"])
        
        if gender:
            query += " AND gender = ?"
            params.append(gender)
            
        self.cursor.execute(query, params)
        patients = self.cursor.fetchall()
        return [{
            "patient_id": p[0],
            "first_name": p[1],
            "last_name": p[2],
            "date_of_birth": p[3],
            "gender": p[4],
            "phone": p[5],
            "email": p[6],
            "address": p[7],
            "blood_type": p[8]
        } for p in patients]

    def get_patient_medical_history(self, patient_id: int) -> List[Dict]:
        """Get all medical records for a patient"""
        self.cursor.execute("""
        SELECT * FROM medical_records 
        WHERE patient_id = ?
        ORDER BY visit_date DESC
        """, (patient_id,))
        records = self.cursor.fetchall()
        return [{
            "record_id": r[0],
            "visit_date": r[2],
            "diagnosis": r[3],
            "treatment": r[4],
            "medications": r[5],
            "notes": r[6]
        } for r in records]

    def get_upcoming_appointments(self, days_ahead: int = 7) -> List[Dict]:
        """Get appointments scheduled for the next X days"""
        self.cursor.execute("""
        SELECT a.appointment_id, p.first_name, p.last_name, 
               a.appointment_date, a.purpose, a.status
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        WHERE a.appointment_date BETWEEN datetime('now') AND datetime('now', ?)
        ORDER BY a.appointment_date
        """, (f"+{days_ahead} days",))
        appointments = self.cursor.fetchall()
        return [{
            "appointment_id": a[0],
            "patient_name": f"{a[1]} {a[2]}",
            "appointment_date": a[3],
            "purpose": a[4],
            "status": a[5]
        } for a in appointments]

    def update_appointment_status(self, appointment_id: int, status: str) -> bool:
        """Update the status of an appointment"""
        try:
            self.cursor.execute("""
            UPDATE appointments SET status = ? WHERE appointment_id = ?
            """, (status, appointment_id))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating appointment: {e}")
            return False

    def __del__(self):
        """Close the database connection when the object is destroyed"""
        self.conn.close()

def main():
    # Initialize the healthcare database
    db = HealthcareDatabase()
    
    # Add sample patients
    patient1 = db.add_patient(
        first_name="John",
        last_name="Doe",
        date_of_birth="1985-05-15",
        gender="Male",
        phone="555-0101",
        email="john.doe@example.com",
        blood_type="O+"
    )
    
    patient2 = db.add_patient(
        first_name="Jane",
        last_name="Smith",
        date_of_birth="1990-11-22",
        gender="Female",
        phone="555-0202",
        email="jane.smith@example.com",
        blood_type="A-"
    )
    
    # Add medical records
    db.add_medical_record(
        patient_id=patient1,
        visit_date="2023-01-10",
        diagnosis="Hypertension",
        medications="Lisinopril 10mg daily",
        notes="Patient advised to reduce sodium intake"
    )
    
    db.add_medical_record(
        patient_id=patient1,
        visit_date="2023-04-15",
        diagnosis="Annual checkup",
        notes="Patient in good health, blood pressure controlled"
    )
    
    # Schedule appointments
    db.schedule_appointment(
        patient_id=patient1,
        appointment_date="2023-10-20 09:30:00",
        purpose="Follow-up for hypertension"
    )
    
    db.schedule_appointment(
        patient_id=patient2,
        appointment_date="2023-10-21 14:00:00",
        purpose="Annual physical"
    )
    
    # Display patient information
    print("Patient Search Results:")
    for patient in db.search_patients(name="Doe"):
        print(f"{patient['first_name']} {patient['last_name']} ({patient['gender']}), DOB: {patient['date_of_birth']}")
    
    # Show medical history
    print("\nMedical History for John Doe:")
    for record in db.get_patient_medical_history(patient1):
        print(f"{record['visit_date']}: {record['diagnosis'] or 'No diagnosis'}")
    
    # Show upcoming appointments
    print("\nUpcoming Appointments (next 30 days):")
    for appointment in db.get_upcoming_appointments(days_ahead=30):
        print(f"{appointment['patient_name']}: {appointment['appointment_date']} - {appointment['purpose']}")

if __name__ == "__main__":
    main()
