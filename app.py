from flask import Flask, render_template, request, redirect, url_for
import matplotlib.pyplot as plt

import os
from config import get_db_connection
from flask import abort
from flask import render_template, request, redirect, url_for, flash
import io
import base64
import csv
import webbrowser
from threading import Timer

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
@app.route('/department/cse/info')
def cse_info():
    return render_template('info/cse_info.html')

@app.route('/department/management/info')
def management_info():
    return render_template('info/management_info.html')

@app.route('/department/english/info')
def english_info():
    return render_template('info/english_info.html')

@app.route('/department/cs/info')
def cs_info():
    return render_template('info/cs_info.html')

@app.route('/department/teacher/info')
def teacher_info():
    return render_template('info/teacher_info.html')

@app.route('/department/botany/info')
def botany_info():
    return render_template('info/botany_info.html')


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

    # Get batch info
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

    # Search logic
    search_query = request.args.get('search', '').lower()
    if search_query:
        students = [s for s in students if
                    search_query in s['name'].lower() or
                    search_query in s['enrollment_no'].lower() or
                    search_query in s['registration_no'].lower()]

    # Pick first match for Edit/Delete beside search box
    selected_student = students[0] if students else None

    return render_template(
        'students.html',
        students=students,
        batch=batch_info,
        no_data=(len(students) == 0),
        selected_student=selected_student,
        search_query=search_query
    )

@app.route('/batches/<int:batch_id>/gender-ratio')
def gender_ratio_chart(batch_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT gender FROM student WHERE batch_id = %s", (batch_id,))
    students = cursor.fetchall()
    conn.close()

    # Count genders
    male_count = sum(1 for s in students if s['gender'].lower() == 'male')
    female_count = sum(1 for s in students if s['gender'].lower() == 'female')

    # Create pie chart
    labels = ['Male', 'Female']
    sizes = [male_count, female_count]
    colors = ['#3498db', '#e74c3c']
    explode = (0.05, 0.05)

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, colors=colors, explode=explode, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    plt.title('Gender Ratio in Batch')

    # Convert plot to base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    chart_data = base64.b64encode(buf.getvalue()).decode()
    buf.close()

    return render_template('gender_chart.html', chart_data=chart_data, batch_id=batch_id)

@app.route('/students/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM student WHERE id=%s", (id,))
    student = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        gender = request.form['gender']
        enrollment_no = request.form['enrollment_no']
        registration_no = request.form['registration_no']
        parentage = request.form['parentage']
        dob = request.form['dob']
        category = request.form['category']

        cursor.execute("""
            UPDATE student 
            SET name=%s, gender=%s, enrollment_no=%s, registration_no=%s,
                parentage=%s, dob=%s, category=%s
            WHERE id=%s
        """, (name, gender, enrollment_no, registration_no,
              parentage, dob, category, id))

        conn.commit()
        conn.close()
        flash("Student updated successfully!", "success")
        return redirect(url_for('batch_students', id=student['batch_id']))

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
    #  Check if teacher is logged in
    if 'teacher_id' not in session:
        flash("Please log in as a teacher to add students.", "warning")
        return redirect(url_for('teacher_login'))

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
        course_id = int(request.form['course_id'])
        batch_id = int(request.form['batch_id'])

        try:
            # ✅ Insert student with both course_id and department_id
            cursor.execute("""
                INSERT INTO student (
                    enrollment_no, registration_no, name, parentage, dob,
                    category, gender, department_id, batch_id, course_id
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s,
                    (SELECT department_id FROM course WHERE id=%s),
                    %s, %s
                )
            """, (
                enrollment_no, registration_no, name, parentage, dob,
                category, gender, course_id, batch_id, course_id
            ))

            conn.commit()
            flash("Student added successfully!", "success")
            return redirect(url_for('add_student'))  # redirect back to form or another route

        except Exception as e:
            conn.rollback()
            flash(f"Error adding student: {e}", "danger")

    conn.close()
    return render_template('add_student.html', courses=courses, batches=batches)

from flask import request, session, redirect, url_for, render_template, flash
from werkzeug.security import check_password_hash

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM teacher WHERE username=%s", (username,))
        teacher = cursor.fetchone()
        conn.close()

        if teacher and password == teacher['password']:  # or use check_password_hash()
            session['teacher_id'] = teacher['id']
            return redirect(url_for('add_student'))
        else:
            flash('Invalid login details', 'danger')

    return render_template('teacher_login.html')
# enrollment summary
@app.route('/batches/<int:batch_id>/enrollment_summary')
def enrollment_summary(batch_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Fetch Batch Info
    cursor.execute("""
        SELECT b.year, c.name as course_name, d.name as dept_name 
        FROM batch b
        JOIN course c ON b.course_id = c.id
        JOIN department d ON c.department_id = d.id
        WHERE b.id = %s
    """, (batch_id,))
    batch_info = cursor.fetchone()

    if not batch_info:
        conn.close()
        return "Batch not found", 404

    # 2. Fetch Aggregated Student Data
    query = """
        SELECT mode, category, gender, COUNT(*) as count 
        FROM student 
        WHERE batch_id = %s 
        GROUP BY mode, category, gender
    """
    cursor.execute(query, (batch_id,))
    results = cursor.fetchall()
    conn.close()

    # 3. Setup Matrix
    categories = ['General', 'EWS', 'SC', 'ST', 'OBC']
    genders = ['Male', 'Female', 'Transgender']
    modes = ['Regular', 'Distance']

    data = {mode: {cat: {gen: 0 for gen in genders} for cat in categories} for mode in modes}

    for mode in modes:
        data[mode]['Total'] = {gen: 0 for gen in genders}

    # 4. Fill Matrix
    cat_map = {'OM': 'General'}

    for row in results:
        raw_mode = row['mode']
        raw_cat = row['category']
        raw_gen = row['gender']
        count = row['count']

        mode_key = raw_mode if raw_mode in modes else 'Regular'
        cat_key = cat_map.get(raw_cat, raw_cat)
        gen_key = raw_gen.capitalize() if raw_gen else None

        if mode_key in data and cat_key in categories and gen_key in genders:
            data[mode_key][cat_key][gen_key] += count
            data[mode_key]['Total'][gen_key] += count

    return render_template('enrollment_summary.html',
                           batch=batch_info,
                           data=data,
                           categories=categories,
                           modes=modes)

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
def read_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

@app.route('/scholarships')
def scholarships():
    rows = read_csv('scholarships.csv')
    # Derive unique schemes for a filter dropdown (optional)
    schemes = sorted(set(r['ScholarshipScheme'] for r in rows))
    rowgroups = ['Total', 'PWD', 'Muslim Minority', 'Other Minority']
    return render_template('scholarships.html', rows=rows, schemes=schemes, rowgroups=rowgroups)




def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run(debug=True,use_reloader=True)
