from flask_sqlalchemy import SQLAlchemy

# Initialize the database instance
db = SQLAlchemy()


class Student(db.Model):
    # This must match the table name in your university_db.sql file
    __tablename__ = 'student'

    # These columns must match the columns in your SQL file
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # The fields we need for the Enrollment Summary
    department = db.Column(db.String(50), nullable=False)  # e.g., 'Computer Science'
    batch = db.Column(db.String(20), nullable=False)  # e.g., '2024-2025'
    category = db.Column(db.String(20), nullable=False)  # e.g., 'General', 'SC', 'ST'
    mode = db.Column(db.String(20), nullable=False)  # e.g., 'Regular', 'Distance'
    gender = db.Column(db.String(20), nullable=False)  # e.g., 'Male', 'Female'

    def __repr__(self):
        return f'<Student {self.name} - {self.department}>'
