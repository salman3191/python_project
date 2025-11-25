from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'student'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    gender = db.Column(db.Enum('Male', 'Female', 'Transgender'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    enrollment_no = db.Column(db.String(20),nullable=True, unique=True)
    registration_no = db.Column(db.String(30), nullable=True)
    parentage = db.Column(db.String(100), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(20), nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), nullable=True)
    mode = db.Column(db.Enum('Regular', 'Di stance'), default='Regular')

    # Relationships
    department = db.relationship('Department', backref='students', lazy=True)
    batch = db.relationship('Batch', backref='students', lazy=True)

    def __repr__(self):
        return f"<Student {self.name} - {self.enrollment_no}>"