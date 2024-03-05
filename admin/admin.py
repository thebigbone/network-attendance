from flask import Blueprint, render_template, request, redirect, url_for, session
from database import mysql
from werkzeug.utils import secure_filename
import pandas as pd
import string
import random

admin = Blueprint("admin", __name__, static_folder="static",
                  template_folder="templates")


# admin login
@admin.route('/')
@admin.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if 'email' in session:
        return redirect(url_for('admin.admin_dashboard'))
    else:
        msg = ''
        if request.method == 'POST' and 'admin_email' in request.form and 'password' in request.form:
            admin_email = request.form['admin_email']
            password = request.form['password']

            cursor = mysql.connection.cursor()
            cursor.execute(
                "SELECT * FROM admin_accounts WHERE email = %s AND password = %s", (admin_email, password))
            account = cursor.fetchone()
            cursor.close()

            if account:
                session['admin_email'] = admin_email

                return redirect(url_for('admin.admin_dashboard'))
            else:
                msg = 'Incorrect email or password!'
    return render_template('admin_login.html', msg=msg)

# admin Register


@admin.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST' and 'admin_email' in request.form and 'name' in request.form and 'password' in request.form:
        admin_email = request.form['admin_email']
        name = request.form['name']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO admin_accounts (email, name, password) VALUES (%s, %s, %s)",
                       (admin_email, name, password))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('admin.admin_login'))

    return render_template('admin_register.html')

# admin dashboard


@admin.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin_email' in session:

        return render_template('admin_dashboard.html')
    else:
        return redirect(url_for('admin.admin_login'))

# time table management


@admin.route('/time_table_manage', methods=['GET', 'POST'])
def time_table():
    if 'admin_email' in session:

        return render_template('time_table_manage.html')
    else:
        return redirect(url_for('admin.admin_login'))

# Add new subjects


@admin.route('/time_table_manage/add_subject_list', methods=['GET', 'POST'])
def add_subject_list():
    if 'admin_email' in session:
        msg = ""
        if request.method == 'POST' and 'academic_year' in request.form and 'department' in request.form and 'sem' in request.form:

            acad_year = request.form['academic_year']
            dept = request.form['department']
            sem = request.form['sem']
            section = int(request.form['section'])
            total_sub = int(request.form['num_subjects'])

            sub_details = {}

            for i in range(total_sub):
                key = str(i + 1)
                sub_details[key] = {
                    'name': request.form[f"subject_name_{key}"],
                    'code': request.form[f"subject_code_{key}"],
                    'lecture': 'y' if 'lecture_' + key in request.form else 'n',
                    'lab': 'y' if 'lab_' + key in request.form else 'n',
                    'tutorial': 'y' if 'tutorial_' + key in request.form else 'n'
                }

            for i in range(section):

                for j in range(total_sub):
                    cursor = mysql.connection.cursor()
                    key = str(j + 1)
                    sub_info = sub_details[key]
                    subject_name_prefix = f"{sem}{i+1}_{sub_info['name']}_{sub_info['code']}"

                    if sub_info['lecture'] == 'y':
                        lecture_subject_name = f"{subject_name_prefix}_lecture"
                        cursor.execute("INSERT INTO attendance_details.college_details (academic_year, department, semester, subject_name) VALUES (%s, %s, %s, %s)",
                                       (acad_year, dept, sem, lecture_subject_name))

                    if sub_info['lab'] == 'y':
                        lab_subject_name = f"{subject_name_prefix}_lab"

                        for batch_name in ['BatchA', 'BatchB', 'BatchC', 'BatchD']:
                            lab_subject_batch_name = f"{lab_subject_name}_{batch_name}"
                            cursor.execute("INSERT INTO attendance_details.college_details (academic_year, department, semester, subject_name) VALUES (%s, %s, %s, %s)",
                                           (acad_year, dept, sem, lab_subject_batch_name))

                    if sub_info['tutorial'] == 'y':
                        tutorial_subject_name = f"{subject_name_prefix}_tutorial"

                        for batch_name in ['BatchA', 'BatchB', 'BatchC', 'BatchD']:
                            tutorial_subject_batch_name = f"{tutorial_subject_name}_{batch_name}"
                            cursor.execute("INSERT INTO attendance_details.college_details (academic_year, department, semester, subject_name) VALUES (%s, %s, %s, %s)",
                                           (acad_year, dept, sem, tutorial_subject_batch_name))

                    mysql.connection.commit()
                    cursor.close()

            cursor = mysql.connection.cursor()
            cursor.execute(
                "SELECT subject_name FROM attendance_details.college_details")
            all_subjects = cursor.fetchall()

            for classname_tuple in all_subjects:
                classname = classname_tuple[0]
                create_table_query = f"CREATE TABLE attendance_details.{classname} (enrollment BIGINT PRIMARY KEY, name VARCHAR(255), faculty_id VARCHAR(255), percentage DECIMAL(5,2), FOREIGN KEY (faculty_id) REFERENCES college_details(faculty_id))"
                cursor.execute(create_table_query)
                mysql.connection.commit()

            cursor.close()

            msg = "Subjects added successfully!"

        return render_template('add_subject_list.html', msg=msg)
    else:
        return redirect(url_for('admin.admin_login'))

# Add new subjects


@admin.route('/time_table_manage/delete_subject_list', methods=['GET', 'POST'])
def delete_subject_list():
    msg = ""
    if 'admin_email' in session:

        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT subject_name FROM attendance_details.college_details WHERE subject_name LIKE '%\_lecture'")
        all_subjects = cursor.fetchall()
        cursor.close()

        subjects = []

        if all_subjects:
            for classname_tuple in all_subjects:
                classname = classname_tuple[0]
                parts = classname.split('_')
                classname = '_'.join(parts[:2])

                subjects.append(classname)

        if request.method == 'POST':

            acad_year = request.form.get('academic_year')
            dept = request.form.get('department')
            sem = request.form.get('semester')
            selected_sub = request.form.get('subject')

            cursor = mysql.connection.cursor()

            cursor.execute("DELETE FROM attendance_details.college_details WHERE academic_year = %s AND department = %s AND semester = %s AND subject_name LIKE %s",
                           (acad_year, dept, sem, f'{selected_sub}%'))
            rows_removed = cursor.rowcount
            mysql.connection.commit()

            cursor.execute(
                "SELECT CONCAT('DROP TABLE IF EXISTS attendance_details.', table_name, ';') FROM information_schema.tables WHERE table_schema = 'attendance_details' AND table_name LIKE %s", (f'{selected_sub}%',))
            drop_queries = cursor.fetchall()

            for i in drop_queries:
                cursor.execute(i[0])

            mysql.connection.commit()
            cursor.close()

            if rows_removed > 0:
                msg = "Subjects removed successfully! Add new subjects from Add Subject Menu."

        return render_template('delete_subject_list.html', msg=msg, subjects=subjects)
    else:
        return redirect(url_for('admin.admin_login'))

#Faculty Management
@admin.route('/faculty_manage',methods=['GET','POST'])
def faculty():
    if 'admin_email' in session: 
       

        
    
        return render_template('faculty_manage.html')
    else:
        return redirect(url_for('admin.admin_login'))

#add_faculty_list
@admin.route('/faculty_manage/add_faculty_list',methods=['GET','POST'])
def add_faculty_list():
    if 'admin_email' in session: 
       

        
    
        return render_template('add_faculty_list.html')
    else:
        return redirect(url_for('admin.admin_login'))

#filter subjects    
@admin.route('/faculty_manage/filter_subjects', methods=['GET', 'POST'])
def filter_subjects():
    if 'admin_email' in session: 
        acad = request.form.get('academic_year')
        dept = request.form.get('department')
        sem = request.form.get('semester')
        
        if acad and dept and sem:
           
            return redirect(url_for('admin.allocate_subjects', acad=acad, dept=dept, sem=sem))
        
        return render_template('filter_subjects.html')
    else:
        return redirect(url_for('admin.admin_login'))

#Allocate subjects
@admin.route('/faculty_manage/allocate_subjects', methods=['GET', 'POST'])
def allocate_subjects():
    msg = ""
    if 'admin_email' in session: 
        
        acad = request.args.get('acad')
        dept = request.args.get('dept')
        sem = request.args.get('sem')
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT distinct(subject_name) FROM ATTENDANCE_DETAILS.COLLEGE_DETAILS WHERE academic_year = %s AND department = %s AND semester = %s", (acad, dept, sem))
        subject_list = cursor.fetchall()
        
        cursor.execute("SELECT DISTINCT ATTENDANCE_DETAILS.COLLEGE_DETAILS.faculty_id, WIFIATTENDANCE.FACULTY_ACCOUNTS.name FROM ATTENDANCE_DETAILS.COLLEGE_DETAILS INNER JOIN WIFIATTENDANCE.FACULTY_ACCOUNTS ON ATTENDANCE_DETAILS.COLLEGE_DETAILS.faculty_id = WIFIATTENDANCE.FACULTY_ACCOUNTS.faculty_id WHERE academic_year = %s AND department = %s AND semester = %s", (acad, dept, sem))
        faculty_list = cursor.fetchall()
        
        cursor.close()
        

        return render_template('allocate_subjects.html', msg=msg, subject_list=subject_list, faculty_list=faculty_list)
    else:
        return redirect(url_for('admin.admin_login'))

# Add student

@admin.route('/upload', methods=['POST', 'GET'])
def upload():
    message = ''
    if 'file' in request.files:
        file = request.files['file']
        filename = secure_filename(file.filename)
        
        print(filename)
        df = pd.DataFrame(pd.read_excel(file)) 
  
        print(df) 
        print(df.columns[0])
        
        if (df.columns[0] == 'Enrollment'):
            for index, row in df.iterrows():
                insert_data_students(row)

            message = 'Students added successfully!'
            
            return render_template('add_student_list.html', message=message)
        else:
            for index, row in df.iterrows():
                insert_data_faculty(row)

            message = 'Faculties added successfully!'

            return render_template('add_faculty_list.html', message=message)
        
    return 'No file uploaded'

@admin.route('/student_manage/add_student_list', methods=['GET', 'POST'])
def add_student_list():
    if 'admin_email' in session:

        return render_template('add_student_list.html')
    else:
        return redirect(url_for('admin.admin_login'))

def insert_data_students(row):
    cursor = mysql.connection.cursor()

    sql = "INSERT INTO student_accounts (enrollment, email, name, student_class, password, batch) VALUES (%s, %s, %s, %s, %s, %s)"
    values = (row['Enrollment'], row['Email-id'], row['Full Name'], row['Class-Sem'], generate_random_string(), row['Batch'])
    cursor.execute(sql, values)
    mysql.connection.commit()
    cursor.close()
    
def insert_data_faculty(row):
    cursor = mysql.connection.cursor()

    sql = "INSERT INTO faculty_accounts (faculty_id, name, email, password, teaching_class) VALUES (%s, %s, %s, %s, %s)"
    values = (row['Faculty_id'], row['Full name'], row['Email-id'], generate_random_string() , row['Class-name'])
    cursor.execute(sql, values)
    mysql.connection.commit()
    cursor.close()    

def generate_random_string(length=8):
    alphanumeric = string.ascii_letters + string.digits
    return ''.join(random.choice(alphanumeric) for _ in range(length))