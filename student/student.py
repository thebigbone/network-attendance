from flask import Blueprint, render_template, request, redirect, url_for, session
from database import mysql
from admin.admin import send_email, generate_random_string
import secrets

student = Blueprint("student", __name__,
                    static_folder="static", template_folder="templates")
'''
# Student registration page
@student.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST' and 'enrollment' in request.form and 'name' in request.form and 'student_class' in request.form and 'password' in request.form:
        enrollment = request.form['enrollment']
        name = request.form['name']
        student_class = request.form['student_class']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO student_accounts (enrollment, name, student_class, password) VALUES (%s, %s, %s, %s)",
                       (enrollment, name, student_class, password))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('student.student_login'))

    return render_template('student_register.html')
'''

# Student login page
@student.route('/student_login', methods=['GET', 'POST'])
def student_login():
    msg = ''
    if request.method == 'POST' and 'enrollment' in request.form and 'password' in request.form:
        enrollment = request.form['enrollment']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM wifiattendance.student_accounts WHERE enrollment = %s AND password = %s", (enrollment, password))
        result = cursor.fetchone()
        cursor.close()

        if result:
            session['enrollment'] = enrollment
            session['name'] = result[2]
            session['student_class'] = result[4]
            session['batch']= result[6]

            return redirect(url_for('student.student_dashboard'))
        else:
            msg = 'Incorrect enrollment or password!'
    return render_template('student_login.html', msg=msg)

# Student Dashboard


@student.route('/student_dashboard', methods=['GET', 'POST'])
def student_dashboard():

    time_session = session.get('time')
    # app.logger.info("Timer: %s" , time_session)

    if 'enrollment' in session:
        msg = ''
        student_class = session.get('student_class')
        batch = session.get('batch')
        name = session.get('name')
        enrollment = request.form.get('enrollment')
        student_attendance_id = request.form.get('attendance_id')
        

        selected_subject = request.form.get('subject')
        session['selected_subject'] = selected_subject
       

        # Finding the tables to show on the dropdown menu
        if student_class:
            cursor = mysql.connection.cursor()
            cursor.execute(f"SELECT TABLE_NAME FROM information_schema.tables WHERE TABLE_NAME LIKE '{student_class}%%{batch}' UNION select TABLE_NAME FROM information_schema.tables WHERE TABLE_NAME LIKE '{student_class}%%lecture'")
            subjects = cursor.fetchall()
            cursor.close()
        else:
            subjects = []

        # Finding all IDs from faculty_id_keys table
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT faculty_id FROM attendance_details.college_details WHERE subject_name = %s",(selected_subject,))
        faculty_id = cursor.fetchall()

        if faculty_id:
            table_name = f"{faculty_id[0][0]}_keys"
            cursor.execute(f"SELECT attendance_id, atten_id_date FROM wifiattendance.{table_name}")
            keys = cursor.fetchone()
            cursor.close()


            if session['enrollment'] == enrollment:
                if student_attendance_id == keys[0]:

                    date = keys[1]


                    cursor = mysql.connection.cursor()

                    # Check if the student already has a row in the table
                    cursor.execute(
                        f"SELECT * FROM attendance_details.{selected_subject} WHERE enrollment = %s", (enrollment,))
                    studentdatarow = cursor.fetchone()

                    if studentdatarow:

                        # If the student already has a row, update the attendance for the current date as P
                        cursor.execute(
                            f"UPDATE attendance_details.{selected_subject} SET `{date}` = 'P' WHERE enrollment = %s", (enrollment,))

                    elif not studentdatarow:
                            msg = "Record Not found..."
                        
                    mysql.connection.commit()
                    cursor.close()

                    return redirect(url_for('student.attendance_marked'))

                else:
                    if keys:
                        msg = "Wrong Attendance ID for the selected subject."
                    else:
                        msg = "Attendance timed out!!! Contact Faculty."
            else:
                msg = "Incorrect enrollment."
        else:
            msg = f"Hello {name}, enter attendance details."

    else:
        return redirect(url_for('student.student_login'))

    return render_template('student_dashboard.html', subjects=subjects, msg=msg, timer_duration=time_session)


# Page to display that attendance has been marked
@student.route('/attendance_marked')
def attendance_marked():
    enrollment = session.get('enrollment')
    selected_subject = session.get('selected_subject')

    return render_template('attendance_marked.html', enrollment=enrollment, selected_subject=selected_subject)

@student.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST' and 'email' in request.form:
        email = request.form["email"]
        
        cursor = mysql.connection.cursor()
        
        sql = f"SELECT id FROM wifiattendance.student_accounts where email = '{email}';"
        cursor.execute(sql)
        user_id = cursor.fetchone()
        
        session['user_id'] = user_id
        print("user session: ", session.get('user_id'))
        
        if user_id:
            secret_token = generate_random_string(8)
            sql = "INSERT INTO wifiattendance.reset_password (id, password_token) values (%s, %s)"
            values = (user_id, secret_token)
            
            cursor.execute(sql, values)
            mysql.connection.commit()
            cursor.close()
            
            subject = "Reset Password"
            body = f"Enter the following token to reset your password: \n {secret_token}"
            
            send_email(email, subject, body)
            return redirect(url_for('student.reset_password'))
        else:
            msg = 'User not found.'
            return render_template('forgot_password.html', msg=msg)
        
    return render_template('forgot_password.html')

@student.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST' and 'token' in request.form:
        token = request.form["token"]
        
        user_id = session.get('user_id')
        print(user_id)
        cursor = mysql.connection.cursor()
        sql = f"SELECT id FROM wifiattendance.reset_password where password_token = '{token}';"
        cursor.execute(sql)
        
        result = cursor.fetchone()
        print(result)
        
        if result:
            return redirect(url_for('student.change_password'))
        else:
            msg = 'Invalid token.'
            return render_template('reset_password.html', msg=msg)
            
    return render_template('reset_password.html')
        
@student.route('/change_password', methods=['GET', 'POST'])
def change_password():
    msg = ''
    if request.method == 'POST' and 'password' in request.form:
        new_password = request.form["password"]
        
        user_id = session.get('user_id')
        
        cursor = mysql.connection.cursor()
        sql = f"UPDATE wifiattendance.student_accounts SET password = '{new_password}' where id = '{user_id}';"
        cursor.execute(sql)
        
        sql1 = f"DELETE FROM wifiattendance.reset_password where id = '{user_id}';"
        cursor.execute(sql1)
        mysql.connection.commit()
        
        msg = 'Password updated successfully!'
        return render_template('change_password.html', msg=msg)
    
    return render_template('change_password.html')
        

# LOG OUT
@student.route('/logout', methods=['GET', 'POST'])
def logout():
    enrollment = session.get('enrollment')
    if enrollment:
        session.clear()
        return redirect(url_for('student.student_login'))
