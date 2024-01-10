from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_mysqldb import MySQL
from flask_socketio import SocketIO, emit
import pandas as pd
import secrets, io


app = Flask(__name__)
app.secret_key = 'ekdjo39ijdowdpwmdo39dowdmw'  # Set your own secret key

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'wifiattendance'

mysql = MySQL(app)

socketio = SocketIO(app)

timer_value = 0

@socketio.on('start_timer')
def start_timer(duration):
    global timer_value
    timer_value = int(duration)
    while timer_value >= 0:
        socketio.emit('update_timer', timer_value)
        socketio.sleep(1)
        timer_value -= 1

#First page: Choose faculty or student
@app.route('/')
@app.route('/choose', methods=['GET', 'POST'])
def choose():
    if request.method == 'POST':
        role = request.form['role']
        if role == 'faculty':
            return redirect(url_for('faculty_login'))
        elif role == 'student':
            return redirect(url_for('student_login'))
    return render_template('choose.html')

# Faculty registration page
@app.route('/faculty_register', methods=['GET', 'POST'])
def faculty_register():
    if request.method == 'POST' and 'faculty_id' in request.form and 'name' in request.form and 'email' in request.form and 'password' in request.form:
        faculty_id = request.form['faculty_id']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        teaching_class = request.form.getlist('teaching_class')
        
        classes = ','.join(teaching_class)
        
        cursor = mysql.connection.cursor()

        cursor.execute("INSERT INTO faculty_accounts (faculty_id, name, email, password, teaching_class) VALUES (%s, %s, %s, %s, %s)",(faculty_id, name, email, password, classes))
        
        #creating teaching class table
        for classname in teaching_class:
            create_table_query = f"CREATE TABLE {classname} (enrollment INT PRIMARY KEY, name VARCHAR(255), faculty_id VARCHAR(255), FOREIGN KEY (faculty_id) REFERENCES faculty_accounts(faculty_id))"
            cursor.execute(create_table_query)
        
        #creating table to store pass keys
        cursor.execute(f"CREATE TABLE {faculty_id}_keys(attendance_id VARCHAR(255), atten_id_date VARCHAR(255), faculty_id VARCHAR(255), FOREIGN KEY (faculty_id) REFERENCES faculty_accounts(faculty_id))")
        mysql.connection.commit()

        cursor.close()
        return redirect(url_for('faculty_login'))
    return render_template('faculty_register.html')

# Faculty login page
@app.route('/faculty_login', methods=['GET', 'POST'])
def faculty_login():
    if 'faculty_id' in session:
        return redirect(url_for('faculty_dashboard'))
    else:
        msg = ''
        if request.method == 'POST' and 'faculty_id' in request.form and 'password' in request.form:
            faculty_id = request.form['faculty_id']
            password = request.form['password']
            
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM faculty_accounts WHERE faculty_id = %s AND password = %s", (faculty_id, password))
            account = cursor.fetchone()
            cursor.close()
            
            if account:
                session['faculty_id'] = faculty_id
                
                return redirect(url_for('faculty_dashboard'))
            else:
                msg = 'Incorrect faculty ID or password!'
    return render_template('faculty_login.html', msg=msg)

# Faculty dashboard
@app.route('/faculty_dashboard', methods=['GET', 'POST'])
def faculty_dashboard():
    
    if 'faculty_id' in session:
            
        faculty_id = session['faculty_id']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT teaching_class FROM faculty_accounts WHERE faculty_id = %s", (faculty_id,))
        result = cursor.fetchone()
        cursor.close()

        subjects = []
        if result:
            teaching_class = result[0]
            subjects = teaching_class.split(',') if teaching_class else []

        date_error = request.args.get('date_error')

        app.logger.info(date_error)

        return render_template('faculty_dashboard.html', subjects=subjects, date_error=date_error)
    else:
        return redirect('/faculty_login')

# Start attendance from faculty dashboard
@app.route('/start_attendance', methods=['GET', 'POST'])
def start_attendance():

    faculty_id = session.get('faculty_id')
    app.logger.info("Fac id: %s", faculty_id)
    
    selected_subject = request.form.get('subject')
    session['selected_subject'] = selected_subject
    app.logger.info("subject: %s", selected_subject)
   
    date = request.form.get('date')
    app.logger.info("SESSION SET DATE: %s",date)
    session['date'] = date
    
    given_time = request.form.get('time')
    app.logger.info("time: %s", given_time)
   
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME=%s AND COLUMN_NAME=%s", (selected_subject, date))
    result = cursor.fetchone()
    cursor.close()
    if result:
        date_error='Attendance is taken for this date! Change date.'
        #return render_template('faculty_dashboard.html',msg=msg)

        return redirect(url_for('faculty_dashboard', date_error=date_error))
    
    if given_time:
        session['time'] = given_time
        timer_duration = int(given_time)
    
    if faculty_id:
        attendance_id = secrets.token_urlsafe(5).upper()
        
        selected_subject = request.form.get('subject')
        session['selected_subject'] = selected_subject

        cursor = mysql.connection.cursor()
        cursor.execute(f"INSERT INTO {faculty_id}_keys (attendance_id, atten_id_date, faculty_id) VALUES (%s, %s, %s)", (attendance_id, date, faculty_id))
        
        alter_query = f"ALTER TABLE {selected_subject} ADD COLUMN `{date}` CHAR(1)"
        cursor.execute(alter_query)
        mysql.connection.commit()
        cursor.close()

        return render_template('start_attendance.html', faculty_id=faculty_id, attendance_id=attendance_id, selected_subject=selected_subject, timer_duration=timer_duration)
    else:
        return redirect(url_for('faculty_login'))
    

# Stop attendance from faculty dashboard
@app.route('/stop_attendance', methods=['GET', 'POST'])
def stop_attendance():
    if 'faculty_id' in session:
        selected_subject = session.get('selected_subject')
        date = session.get('date')
        faculty_id = session.get("faculty_id")
    
        cursor = mysql.connection.cursor()
        #delete all the keys
        cursor.execute(f"DELETE FROM {faculty_id}_keys where 1")
        mysql.connection.commit()
        
        #student data
        cursor.execute(f"SELECT enrollment, name, `{date}` FROM {selected_subject} WHERE `{date}`='P'")
        students_data = cursor.fetchall()
        
        #student count
        cursor.execute(f"SELECT COUNT(`{date}`) FROM {selected_subject} WHERE `{date}`='P' ")
        students_count = cursor.fetchone()[0]
        
        #mark absent as A
        cursor.execute(f" UPDATE {selected_subject} SET `{date}` = COALESCE(`{date}`, 'A')")
        mysql.connection.commit()
        
        cursor.close()
    
        return render_template('stop_attendance.html', students_data=students_data, students_count=students_count, selected_subject=selected_subject)
    else:
        return redirect(url_for('faculty_login'))

# Download Attendance
@app.route('/download_attendance', methods=['GET', 'POST'])
def download_attendance():
    if 'faculty_id' in session:
        
        selected_subject = session.get('selected_subject')
        
        # database to excel
        atten_sheet = pd.read_sql(f"SELECT * FROM {selected_subject}", mysql.connection)

        # Create a BytesIO buffer to store the Excel file
        excel_buffer = io.BytesIO()
        atten_sheet.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        # Send the Excel file as a response for download
        return send_file(excel_buffer, download_name=f"{selected_subject}_attendance_sheet.xlsx", as_attachment=True)
    else:
        return redirect(url_for('faculty_login'))    

# Student registration page
@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST' and 'enrollment' in request.form and 'name' in request.form and 'student_class' in request.form and 'password' in request.form:
        enrollment = request.form['enrollment']
        name = request.form['name']
        student_class = request.form['student_class']  
        password = request.form['password']
        
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO student_accounts (enrollment, name, student_class, password) VALUES (%s, %s, %s, %s)", (enrollment, name, student_class, password))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('student_login'))
    
    return render_template('student_register.html')

# Student login page
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    msg = ''
    if request.method == 'POST' and 'enrollment' in request.form and 'password' in request.form:
        enrollment = request.form['enrollment']
        password = request.form['password']
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM student_accounts WHERE enrollment = %s AND password = %s", (enrollment, password))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            session['enrollment'] = enrollment
            session['student_class'] = result[3]
            session['name'] = result[2]
            return redirect(url_for('student_dashboard'))
        else:
            msg = 'Incorrect enrollment or password!'
    return render_template('student_login.html', msg=msg)

# Student Dashboard
@app.route('/student_dashboard', methods=['GET', 'POST'])
def student_dashboard():
    
    time_session = session.get('time')
    app.logger.info("Timer: %s" , time_session)
    
    if 'enrollment' in session:
        msg = ''
        student_class = session.get('student_class')
        name = session.get('name')
        enrollment = request.form.get('enrollment')
        student_attendance_id = request.form.get('attendance_id')

        selected_subject = request.form.get('subject')
        session['selected_subject'] = selected_subject
        app.logger.info("Selected subject: %s",selected_subject)
        
        
        
        # Finding the tables to show on the dropdown menu
        if student_class:
            cursor = mysql.connection.cursor()
            cursor.execute("SHOW TABLES LIKE %s", (f"{student_class}_%",))
            subjects = cursor.fetchall()
            cursor.close()
        else:
            subjects = []
        
        
        # Finding all IDs from faculty_id_keys table
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT faculty_id FROM faculty_accounts WHERE TRIM(teaching_class) LIKE %s", (f'%{selected_subject}%',))
        faculty_id_row = cursor.fetchone()

        if faculty_id_row:
            faculty_id = faculty_id_row[0]
            table_name = f"{faculty_id}_keys"
            cursor.execute(f"SELECT attendance_id, atten_id_date FROM {table_name}")
            keys = cursor.fetchall()
            cursor.close()
            
            # Convert the results to a dictionary
            keys_dict = dict(keys)
            app.logger.info("Dictionary of keys: %s", keys_dict)
            
            if session['enrollment'] == enrollment:
                if student_attendance_id in keys_dict.keys():
                    
                    date = keys_dict.get(student_attendance_id)
                    
                    cursor = mysql.connection.cursor()
                    table_name = f"{selected_subject}"

                    # Check if the student already has a row in the table
                    cursor.execute(f"SELECT * FROM {table_name} WHERE enrollment = %s", (enrollment,))
                    studentdatarow = cursor.fetchone()

                    if studentdatarow:
                        # If the student already has a row, update the attendance for the current date as P
                        cursor.execute(f"UPDATE {table_name} SET `{date}` = 'P' WHERE enrollment = %s", (enrollment,))

                    elif not studentdatarow:
                        # If the student doesn't have a row, insert a new row with attendance 'P'
                        cursor.execute(f"INSERT INTO {table_name} (enrollment, name, `{date}`, faculty_id) VALUES (%s, %s, 'P', %s)", (enrollment, name, faculty_id))

                    mysql.connection.commit()
                    cursor.close()
                    return redirect(url_for('attendance_marked'))

                else:
                    if keys:
                        msg = "Wrong Attendance ID for the selected subject."
                    else:
                        msg ="Attendance timed out!!! Contact admin"
            else:
                msg = "Incorrect enrollment"
        else:
            msg = "Enter attendance details"

    else:
        return redirect(url_for('student_login'))

    return render_template('student_dashboard.html', subjects=subjects, msg=msg, timer_duration=time_session)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    faculty_id = session.get('faculty_id')
    if faculty_id:
        session.clear()
        return redirect(url_for('faculty_login'))
    
    else:
        session.clear()
        return redirect(url_for('student_login'))
    

# Page to display that attendance has been marked
@app.route('/attendance_marked')
def attendance_marked():
    enrollment = session.get('enrollment')
    selected_subject = session.get('selected_subject')
   
    return render_template('attendance_marked.html', enrollment=enrollment, selected_subject=selected_subject)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
