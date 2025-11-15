from flask import Flask, render_template, request, redirect, url_for
import matplotlib.pyplot as plt
import os
from config import get_db_connection
from flask import abort
from flask import render_template, request, redirect, url_for, flash


app = Flask(__name__)
app.secret_key = "your-very-secret-key"   # 👈 Add this line

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Show all departments as cards
@app.route('/departments')
def departments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM department")
    departments = cursor.fetchall()
    conn.close()
    return render_template('departments.html', departments=departments)

# Show details of a specific department
@app.route('/departments/<int:id>')
def department_detail(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get department info
    cursor.execute("SELECT * FROM department WHERE id=%s", (id,))
    department = cursor.fetchone()

    # Get students in this department
    cursor.execute("SELECT * FROM student WHERE department_id=%s", (id,))
    students = cursor.fetchall()

    conn.close()
    return render_template('department_detail.html', department=department, students=students)

# show courses for departments
@app.route('/departments/<int:id>/courses')
def department_courses(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM course WHERE department_id=%s", (id,))
    courses = cursor.fetchall()
    conn.close()
    return render_template('courses.html', courses=courses)

# show batches for a course
@app.route('/courses/<int:id>/batches')
def course_batches(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT batch.id, batch.year, course.name AS course_name
        FROM batch
        JOIN course ON batch.course_id = course.id
        WHERE course.id = %s
        ORDER BY batch.year
    """, (id,))
    batches = cursor.fetchall()
    conn.close()
    return render_template('batches.html', batches=batches)

# show students for a batch
@app.route('/batches/<int:id>/students')
def batch_students(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get batch info (year + course name)
    cursor.execute("""
    SELECT b.id, b.year, c.name AS course_name
    FROM batch b
    JOIN course c ON b.course_id = c.id
    WHERE b.id = %s
    """, (id,))
    batch_info = cursor.fetchone()

    if batch_info is None:
      abort(404)

    # Get students
    cursor.execute("SELECT * FROM student WHERE batch_id = %s", (id,))
    students = cursor.fetchall()
    conn.close()

    return render_template(
        'students.html',
        students=students,
        batch=batch_info,
        no_data=(len(students) == 0)
    )

@app.route('/students/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM student WHERE id=%s", (id,))
    student = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        gender = request.form['gender']
        # update other fields...
        cursor.execute("""
            UPDATE student SET name=%s, gender=%s WHERE id=%s
        """, (name, gender, id))
        conn.commit()
        conn.close()
        flash("Student updated successfully!", "success")
        return redirect(url_for('students'))

    conn.close()
    return render_template('edit_student.html', student=student)


@app.route('/students/delete/<int:id>/<int:batch_id>', methods=['POST','GET'])
def delete_student(id, batch_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM student WHERE id=%s", (id,))
    conn.commit()
    conn.close()

    flash("Student deleted successfully!", "danger")
    # Redirect back to the batch students page
    return redirect(url_for('batch_students', id=batch_id))

@app.route('/students/add', methods=['GET', 'POST'])
def add_student():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get courses and batches for dropdowns
    cursor.execute("SELECT id, name, department_id FROM course")
    courses = cursor.fetchall()

    cursor.execute("SELECT id, year, course_id FROM batch")
    batches = cursor.fetchall()

    if request.method == 'POST':
        enrollment_no = request.form['enrollment_no']
        registration_no = request.form['registration_no']
        name = request.form['name']
        parentage = request.form['parentage']
        dob = request.form['dob']
        category = request.form['category']
        gender = request.form['gender']
        course_id = request.form['course_id']
        batch_id = request.form['batch_id']

        cursor.execute("""
            INSERT INTO student (
                enrollment_no, registration_no, name, parentage, dob,
                category, gender, department_id, batch_id
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s,
                (SELECT department_id FROM course WHERE id=%s),
                %s
            )
        """, (enrollment_no, registration_no, name, parentage, dob,
              category, gender, course_id, batch_id))

        conn.commit()
        conn.close()

        flash("Student added successfully!", "success")
        return redirect(url_for('flasmessage.html'))

    conn.close()
    return render_template('add_student.html', courses=courses, batches=batches)

# Reports page with bar chart
@app.route('/reports')
def reports():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.name, COUNT(s.id)
        FROM department d
        LEFT JOIN course c ON c.department_id = d.id
        LEFT JOIN batch b ON b.course_id = c.id
        LEFT JOIN student s ON s.batch_id = b.id
        GROUP BY d.name
    """)
    data = cursor.fetchall()
    conn.close()

    departments = [row[0] for row in data]
    counts = [row[1] for row in data]

    plt.figure(figsize=(8,6))
    plt.bar(departments, counts, color='skyblue')
    plt.title("Student Enrollment per Department")
    plt.xlabel("Departments")
    plt.ylabel("Number of Students")
    plt.xticks(rotation=45)
    plt.tight_layout()

    graph_path = os.path.join("static", "dept_report.png")
    plt.savefig(graph_path)
    plt.close()

    return render_template('reports.html', graph_file="dept_report.png")

if __name__ == "__main__":
    app.run(debug= True)