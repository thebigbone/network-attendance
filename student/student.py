from flask import Blueprint, render_template, request, redirect, url_for, session
from database import mysql



student = Blueprint("student", __name__ , static_folder="static", template_folder="templates")




# Student registration page
@student.route('/student_register', methods=['GET', 'POST'])
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

        return redirect(url_for('student.student_login'))
    
    return render_template('student_register.html')

# Student login page
@student.route('/student_login', methods=['GET', 'POST'])
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
            
            return redirect(url_for('student.student_dashboard'))
        else:
            msg = 'Incorrect enrollment or password!'
    return render_template('student_login.html', msg=msg)

# Student Dashboard
@student.route('/student_dashboard', methods=['GET', 'POST'])
def student_dashboard():
    
    time_session = session.get('time')
    #app.logger.info("Timer: %s" , time_session)
    
    if 'enrollment' in session:
        msg = ''
        student_class = session.get('student_class')
        name = session.get('name')
        enrollment = request.form.get('enrollment')
        student_attendance_id = request.form.get('attendance_id')

        selected_subject = request.form.get('subject')
        session['selected_subject'] = selected_subject
        #app.logger.info("Selected subject: %s",selected_subject)
        
        
        
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
            
            if session['enrollment'] == enrollment:
                if student_attendance_id in keys_dict.keys():
                    
                    date = keys_dict.get(student_attendance_id)
                    
                    table_name = selected_subject
                    
                    cursor = mysql.connection.cursor()
                    
                    # Check if the student already has a row in the table
                    cursor.execute(f"SELECT * FROM {table_name} WHERE enrollment = %s", (enrollment,))
                    studentdatarow = cursor.fetchone()

                    if studentdatarow:
                        
                        # If the student already has a row, update the attendance for the current date as P
                        cursor.execute(f"UPDATE {table_name} SET `{date}` = 'P' WHERE enrollment = %s", (enrollment,))

                    elif not studentdatarow:
                        
                        # If the student doesn't have a row, insert a new row with attendance 'P'
                        cursor.execute(f"INSERT INTO {table_name} (enrollment, name, faculty_id,`{date}`) VALUES (%s, %s, %s,'P')", (enrollment, name, faculty_id,))

                    mysql.connection.commit()
                    cursor.close()
                   
                    
                    return redirect(url_for('student.attendance_marked'))

                else:
                    if keys:
                        msg = "Wrong Attendance ID for the selected subject."
                    else:
                        msg ="Attendance timed out!!! Contact Faculty."
            else:
                msg = "Incorrect enrollment."
        else:
            msg = "Enter attendance details."

    else:
        return redirect(url_for('student.student_login'))

    return render_template('student_dashboard.html', subjects=subjects, msg=msg, timer_duration=time_session)


    
# Page to display that attendance has been marked
@student.route('/attendance_marked')
def attendance_marked():
    enrollment = session.get('enrollment')
    selected_subject = session.get('selected_subject')
   
    return render_template('attendance_marked.html', enrollment=enrollment, selected_subject=selected_subject)

    
#LOG OUT
@student.route('/logout', methods=['GET', 'POST'])
def logout():
    enrollment = session.get('enrollment')
    if enrollment:
        session.clear()
        return redirect(url_for('student.student_login'))
  

