from flask import Blueprint, render_template, request, redirect, url_for, session, send_file
from database import mysql
from werkzeug.utils import secure_filename
import pandas as pd
import string
import random

from email.mime.text import MIMEText
import json

import os
from dotenv import load_dotenv
import smtplib
import threading

load_dotenv()


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
                "SELECT * FROM wifiattendance.admin_accounts WHERE email = %s AND password = %s", (admin_email, password))
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
        cursor.execute("INSERT INTO wifiattendance.admin_accounts (email, name, password) VALUES (%s, %s, %s)",
                       (admin_email, name, password))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('admin.admin_login'))

    return render_template('admin_register.html')

# admin dashboard


@admin.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin_email' in session:
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT distinct(semester) FROM attendance_details.college_details")
        sem_list = cursor.fetchall()
        cursor.close()
        
        sem = request.form.get('semester')
        
        cursor = mysql.connection.cursor()
        if sem:
            cursor.execute("SELECT subject_name, total_attendance FROM attendance_details.college_details where semester = %s",(sem,))
            data = cursor.fetchall()
        
        else:
            cursor.execute("SELECT subject_name, total_attendance FROM attendance_details.college_details")
            data = cursor.fetchall()
        
        cursor.close()
        
        mylabels=[]
        info=[]
        
        for item in data:
            mylabels.append(item[0])
            info.append(item[1])
        
        
        chart_data = {
            "labels": mylabels,
            "values": info
        }
        
        chart_data = json.dumps(chart_data)

        return render_template('admin_dashboard.html', sem_list= sem_list, chart_data = chart_data, sem = sem)
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
            
            try:
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
                            cursor.execute("INSERT INTO attendance_details.college_details (academic_year, department, semester, subject_name,total_attendance) VALUES (%s, %s, %s, %s, 0)",
                                           (acad_year, dept, sem, lecture_subject_name))

                        if sub_info['lab'] == 'y':
                            lab_subject_name = f"{subject_name_prefix}_lab"

                            for batch_name in ['BatchA', 'BatchB', 'BatchC', 'BatchD']:
                                lab_subject_batch_name = f"{lab_subject_name}_{batch_name}"
                                cursor.execute("INSERT INTO attendance_details.college_details (academic_year, department, semester, subject_name, total_attendance) VALUES (%s, %s, %s, %s, 0)",
                                               (acad_year, dept, sem, lab_subject_batch_name))

                        if sub_info['tutorial'] == 'y':
                            tutorial_subject_name = f"{subject_name_prefix}_tutorial"

                            for batch_name in ['BatchA', 'BatchB', 'BatchC', 'BatchD']:
                                tutorial_subject_batch_name = f"{tutorial_subject_name}_{batch_name}"
                                cursor.execute("INSERT INTO attendance_details.college_details (academic_year, department, semester, subject_name, total_attendance) VALUES (%s, %s, %s, %s, 0)",
                                               (acad_year, dept, sem, tutorial_subject_batch_name))

                        mysql.connection.commit()
                        cursor.close()

                cursor = mysql.connection.cursor()
                cursor.execute("SELECT subject_name FROM attendance_details.college_details")
                all_subjects = cursor.fetchall()

                for classname_tuple in all_subjects:
                    classname = classname_tuple[0]

                    create_table_query = f"CREATE TABLE attendance_details.{classname} (enrollment BIGINT PRIMARY KEY, name VARCHAR(255), faculty_id VARCHAR(255), percentage DECIMAL(5,2))"
                    cursor.execute(create_table_query)
                    mysql.connection.commit()

                cursor.close()

                msg = "Subjects added successfully!"
                
            except Exception as e:
                print(f"Error occurred: {str(e)}")
                msg = "An error occurred while adding subjects. Please try again."

        return render_template('add_subject_list.html', msg=msg)
    else:
        return redirect(url_for('admin.admin_login'))


#Delete subjects
@admin.route('/time_table_manage/delete_subject_list', methods=['GET', 'POST'])
def delete_subject_list():
    if 'admin_email' in session:
        subjects = []
        msg=""
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT subject_name FROM attendance_details.college_details WHERE subject_name LIKE '%\_lecture'")
        all_subjects = cursor.fetchall()
        cursor.close()

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
            
            try:
                cursor.execute("DELETE FROM attendance_details.college_details WHERE academic_year = %s AND department = %s AND semester = %s AND subject_name LIKE %s",
                               (acad_year, dept, sem, f'{selected_sub}%'))
                rows_removed = cursor.rowcount
                mysql.connection.commit()
    
                cursor.execute(
                    "SELECT CONCAT('DROP TABLE IF EXISTS attendance_details.', table_name, ';') FROM information_schema.tables WHERE table_schema = 'attendance_details' AND table_name LIKE %s", (f'{selected_sub}%',))
                drop_queries = cursor.fetchall()
    
                for query in drop_queries:
                    cursor.execute(query[0])
    
                mysql.connection.commit()
                cursor.close()
    
                if rows_removed > 0:
                    msg = "Subjects removed successfully! Add new subjects from the Add Subject menu."
            except Exception as e:
                print(f"Error occurred: {str(e)}")
                msg = "An error occurred while deleting subjects. Please try again."
            

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
        
        
        if request.method == 'POST':
            direct = request.args.get('direct')
            
            if direct == 'allocate' and acad and dept and sem:
                return redirect(url_for('admin.allocate_subjects', acad=acad, dept=dept, sem=sem))
            
            if direct == 'modify' and acad and dept and sem:
                return redirect(url_for('admin.modify_allocated_sub', acad=acad, dept=dept, sem=sem))
           
        
        return render_template('filter_subjects.html',direct=direct)
    else:
        return redirect(url_for('admin.admin_login'))

#Allocate subjects route
@admin.route('/faculty_manage/allocate_subjects', methods=['GET', 'POST'])
def allocate_subjects():
    msg = ""
    if 'admin_email' in session: 
        
        acad = request.args.get('acad')
        dept = request.args.get('dept')
        sem = request.args.get('sem')
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT distinct(subject_name) FROM attendance_details.college_details WHERE academic_year = %s AND department = %s AND semester = %s", (acad, dept, sem))
        subject_list = cursor.fetchall()
        
        cursor.execute("SELECT name, faculty_id FROM wifiattendance.faculty_accounts")
        faculty_list = cursor.fetchall()
        
        
        cursor.close()
        
        if request.method=='POST':
            
            try:
                for subject in subject_list:
                    subject_name = subject[0]
                    faculty_id = request.form.get(subject_name)
                   
                    cursor = mysql.connection.cursor()
                    cursor.execute("UPDATE attendance_details.college_details SET faculty_id = %s WHERE academic_year = %s AND department = %s AND semester = %s AND subject_name = %s", (faculty_id, acad, dept, sem, subject_name))
                    mysql.connection.commit()
                    cursor.close()
                
                msg = "Subjects allocated successfully!"
                
            except Exception:
                msg="Allocation failed! Try again later."

        return render_template('allocate_subjects.html', msg=msg, subject_list=subject_list, faculty_list=faculty_list, acad= acad, dept= dept, sem=sem)
    else:
        return redirect(url_for('admin.admin_login'))


#modify Allocation
@admin.route('/faculty_manage/modify_alloacated_sub', methods=['GET', 'POST'])
def modify_allocated_sub():
    msg = ""
    if 'admin_email' in session: 
        
        acad = request.args.get('acad')
        dept = request.args.get('dept')
        sem = request.args.get('sem')
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT distinct(subject_name) FROM attendance_details.college_details WHERE academic_year = %s AND department = %s AND semester = %s", (acad, dept, sem))
        subject_list = cursor.fetchall()
        
        cursor.execute("SELECT name, faculty_id FROM wifiattendance.faculty_accounts")
        faculty_list = cursor.fetchall()
        
        
        cursor.close()
        
        if request.method=='POST':
           
            subject_name = request.form.get('subject')
            faculty_id = request.form.get('faculty_id')
            
            try:
                cursor = mysql.connection.cursor()
                cursor.execute(f"UPDATE attendance_details.{subject_name} SET faculty_id = %s",(faculty_id,))
                mysql.connection.commit()
                cursor.execute("UPDATE attendance_details.college_details SET faculty_id = %s WHERE academic_year = %s AND department = %s AND semester = %s AND subject_name = %s", (faculty_id, acad, dept, sem, subject_name))
                mysql.connection.commit()
    
                cursor.close()
                msg = "Allocation Modified successfully!"
                
            except Exception:
                msg = "Allocation was not modified!"
                             

        return render_template('modify_allocated_sub.html', msg=msg, subject_list=subject_list, faculty_list=faculty_list, acad= acad, dept= dept, sem=sem)
    else:
        return redirect(url_for('admin.admin_login'))

@admin.route('/sample')
def sample():
    filename = 'student_data_sample.xlsx'
    
    current_directory = os.getcwd()
    
    file_path = os.path.join(current_directory, 'sample_download', filename)
    
    return send_file(file_path, as_attachment=True)

@admin.route('/sample1')
def sample1():
    filename = 'faculty_data_sample.xlsx'
    
    current_directory = os.getcwd()
    
    file_path = os.path.join(current_directory, 'sample_download', filename)
    
    return send_file(file_path, as_attachment=True)

# Add student
@admin.route('/upload', methods=['POST', 'GET'])
def upload():
    if 'file' in request.files:
        file = request.files['file']
        filename = secure_filename(file.filename)
        
        print(filename)
        df = pd.DataFrame(pd.read_excel(file)) 
  
        print(df) 
        
        if (df.columns[0] == 'Enrollment'):
            for index, row in df.iterrows():
                insert_data_students(row)
                
                class_name = row['Class-Sem']
                batch_name = row['Batch']
                
                cursor = mysql.connection.cursor()
                
                sql_batch = f"select TABLE_NAME FROM information_schema.tables WHERE TABLE_NAME LIKE '{class_name}%%{batch_name}' UNION select TABLE_NAME FROM information_schema.tables WHERE TABLE_NAME LIKE '{class_name}%%lecture';"              
                cursor.execute(sql_batch)
                
                table_name = cursor.fetchall()
                
                table_name1 = [item[0][:] for item in table_name]
                
                if table_name:
                    for table_names in table_name1:
                        sql = f"INSERT IGNORE INTO attendance_details.{table_names} (enrollment, name) VALUES (%s, %s)"
                        values = (row['Enrollment'], row['Full Name'])
                    
                        cursor.execute(sql, values)
                        mysql.connection.commit()
                    
                    cursor.close()
            
            # sending emails    
            send_email_from_table('student_accounts')
            
            message = 'Students added and allocated successfully! Sending emails for login credentials now. It will take a few minutes to arrive.'
            
            return render_template('add_student_list.html', message=message)
        else:
            for index, row in df.iterrows():
                insert_data_faculty(row)

            send_email_from_table('faculty_accounts')
            
            message = 'Faculties added successfully! Sending emails for login credentials now. It will take a few minutes to arrive.'

            return render_template('add_faculty_list.html', message=message)
        
    return 'No file uploaded'

@admin.route('/student_manage',methods=['GET','POST'])
def student_manage():
    if 'admin_email' in session:

        return render_template('student_manage.html')
    else:
        return redirect(url_for('admin.admin_login'))
    

@admin.route('/student_manage/add_student_list', methods=['GET', 'POST'])
def add_student_list():
    if 'admin_email' in session:
    
        return render_template('add_student_list.html')
    else:
        return redirect(url_for('admin.admin_login'))

def insert_data_students(row):
    cursor = mysql.connection.cursor()

    sql = "INSERT INTO wifiattendance.student_accounts (enrollment, email, name, student_class, password, batch) VALUES (%s, %s, %s, %s, %s, %s)"
    values = (row['Enrollment'], row['Email-id'], row['Full Name'], row['Class-Sem'], generate_random_string(), row['Batch'])
    cursor.execute(sql, values)
    mysql.connection.commit()
    cursor.close()
    
def insert_data_faculty(row):
    cursor = mysql.connection.cursor()

    sql = "INSERT INTO wifiattendance.faculty_accounts (faculty_id, name, email, password) VALUES (%s, %s, %s, %s)"
    values = (row['Faculty_id'], row['Full name'], row['Email-id'], generate_random_string() )
    cursor.execute(sql, values)
    mysql.connection.commit()
    
    cursor.execute("CREATE TABLE wifiattendance.{}_keys (attendance_id VARCHAR(255), atten_id_date VARCHAR(255), faculty_id VARCHAR(255), FOREIGN KEY (faculty_id) REFERENCES faculty_accounts(faculty_id))".format(row['Faculty_id']))

    cursor.close()    

def generate_random_string(length=8):
    alphanumeric = string.ascii_letters + string.digits
    return ''.join(random.choice(alphanumeric) for _ in range(length))

def send_email(to_email, subject, body, html_body=None):
    gmail_user = os.getenv('GOOGLE_EMAIL') 
    gmail_password = os.getenv('GOOGLE_PASSWORD')
    
    sent_from = gmail_user
    
    if html_body:
        msg = MIMEText(html_body, 'html')
    else:
        msg = MIMEText(body)
    
    msg['Subject'] = subject
    msg['From'] = sent_from
    msg['To'] = to_email

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to_email, msg.as_string())
        server.close()

        print('email sent')
    except Exception as e:
        print(f'an error occurred: {e}')
        
def send_email_from_table(table_name):
    cursor = mysql.connection.cursor()
    
    sql = f'SELECT email, password FROM wifiattendance.{table_name};'
    cursor.execute(sql)
    
    rows = cursor.fetchall()
    print(rows)
    
    for email, password in rows:
        body = f"Email: {email} \n Password: {password}"
        subject = "Login credentials for Attendance."
        background_thread = threading.Thread(target=send_email, args=(email, subject, body))
        background_thread.start()