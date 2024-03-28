from flask import Blueprint, render_template, request, redirect, url_for, session, send_file
import pandas as pd
import secrets, io
from database import mysql


faculty = Blueprint("faculty", __name__ , static_folder="static", template_folder="templates")



'''
# Faculty registration page
@faculty.route('/faculty_register', methods=['GET', 'POST'])
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
            create_table_query = f"CREATE TABLE {classname} (enrollment BIGINT PRIMARY KEY, name VARCHAR(255), faculty_id VARCHAR(255), percentage DECIMAL(5,2), FOREIGN KEY (faculty_id) REFERENCES faculty_accounts(faculty_id))"
            cursor.execute(create_table_query)
        
        #creating table to store pass keys
        cursor.execute(f"CREATE TABLE {faculty_id}_keys(attendance_id VARCHAR(255), atten_id_date VARCHAR(255), faculty_id VARCHAR(255), FOREIGN KEY (faculty_id) REFERENCES faculty_accounts(faculty_id))")
        mysql.connection.commit()

        cursor.close()
        return redirect(url_for('faculty.faculty_login'))
    return render_template('faculty_register.html')
'''

# Faculty login page
@faculty.route('/faculty_login', methods=['GET', 'POST'])
def faculty_login():
    if 'faculty_id' in session:
        return redirect(url_for('faculty.faculty_dashboard'))
    else:
        msg = ''
        if request.method == 'POST' and 'faculty_id' in request.form and 'password' in request.form:
            faculty_id = request.form['faculty_id']
            password = request.form['password']
            
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM wifiattendance.faculty_accounts WHERE faculty_id = %s AND password = %s", (faculty_id, password))
            account = cursor.fetchone()
            cursor.close()
            
            if account:
                session['faculty_id'] = faculty_id
                
                return redirect(url_for('faculty.faculty_dashboard'))
            else:
                msg = 'Incorrect faculty ID or password!'
    return render_template('faculty_login.html', msg=msg)

# Faculty dashboard
@faculty.route('/faculty_dashboard', methods=['GET', 'POST'])
def faculty_dashboard():
    
    if 'faculty_id' in session:
            
        faculty_id = session['faculty_id']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT subject_name FROM attendance_details.college_details WHERE faculty_id = %s", (faculty_id,))
        subjects = cursor.fetchall()
        cursor.close()
        
        
        date_error = session.get('date_error')
        session.pop('date_error', None)
        

        return render_template('faculty_dashboard.html', subjects=subjects, date_error=date_error)
    else:
        return redirect(url_for('faculty.faculty_login'))

# Start attendance from faculty dashboard
@faculty.route('/start_attendance', methods=['GET', 'POST'])
def start_attendance():

    faculty_id = session.get('faculty_id')
    
    selected_subject = request.form.get('subject')
    session['selected_subject'] = selected_subject
    

    date = request.form.get('date')
    session['date'] = date

    if faculty_id:
        attendance_id = secrets.token_urlsafe(5).upper()
        
        selected_subject = request.form.get('subject')
        session['selected_subject'] = selected_subject
        
        try:
            cursor = mysql.connection.cursor()
            cursor.execute(f"INSERT INTO wifiattendance.{faculty_id}_keys (attendance_id, atten_id_date, faculty_id) VALUES (%s, %s, %s)", (attendance_id, date, faculty_id))
            mysql.connection.commit()
           
            
            cursor.execute(f"ALTER TABLE attendance_details.{selected_subject} ADD COLUMN `{date}` CHAR(1)")
            mysql.connection.commit()
            
        
            cursor.close()
            
        except Exception:
            msg='Attendance is taken for this date! Change date.'
            session['date_error'] = msg
            return redirect(url_for('faculty.faculty_dashboard'))
        
        return render_template('start_attendance.html', faculty_id=faculty_id, attendance_id=attendance_id, selected_subject=selected_subject)
    else:
        return redirect(url_for('faculty.faculty_login'))
    

# Stop attendance from faculty dashboard
@faculty.route('/stop_attendance', methods=['GET', 'POST'])
def stop_attendance():
    if 'faculty_id' in session:
        selected_subject = session.get('selected_subject')
        date = session.get('date')
        faculty_id = session.get("faculty_id")
    
        cursor = mysql.connection.cursor()

        # Delete all the keys
        cursor.execute(f"DELETE FROM wifiattendance.{faculty_id}_keys")
        mysql.connection.commit()
        
        # Get student data
        cursor.execute(f"SELECT enrollment, name, percentage FROM attendance_details.{selected_subject} WHERE `{date}` = 'P'")
        students_data = cursor.fetchall()
        
        # Get student count
        cursor.execute(f"SELECT COUNT(`{date}`) FROM attendance_details.{selected_subject} WHERE `{date}` = 'P'")
        students_count = cursor.fetchone()[0]
        
        # Mark absent as 'A'
        cursor.execute(f"UPDATE attendance_details.{selected_subject} SET `{date}` = COALESCE(`{date}`, 'A') , faculty_id= COALESCE( faculty_id, %s )",(faculty_id,))
        mysql.connection.commit()
        
        #Increment counter of attendance taken in college_details
        cursor.execute("UPDATE attendance_details.college_details SET total_attendance = total_attendance + 1 where subject_name = %s",(selected_subject,))
        mysql.connection.commit()
        
        cursor.close()
        
        # Logic for attendance percentage calculation
        cursor = mysql.connection.cursor()
        table_name = selected_subject
        
        # Fetch all distinct enrollments from the table
        cursor.execute(f"SELECT DISTINCT enrollment FROM attendance_details.{table_name}")
        all_enrollments = [enrollment[0] for enrollment in cursor.fetchall()]
        
        # Fetch all columns from the table
        cursor.execute(f"SHOW COLUMNS FROM attendance_details.{table_name}")
        all_columns = [column[0] for column in cursor.fetchall()]
        
        # Start from the 5th column (index 4) for the number of presents
        columns_to_check = all_columns[4:]
        
        for enrollment in all_enrollments:        
            # Constructing the SQL query dynamically 
            sql_query = (
                f"SELECT SUM("
                f"{' + '.join([f'(`{column}` = %s)' for column in columns_to_check])}"
                f") AS total_p_count "
                f"FROM attendance_details.{table_name} WHERE enrollment = %s"
                )

            # Execute the query
            cursor.execute(sql_query, ['P'] * len(columns_to_check) + [enrollment])
            
            total_presents = cursor.fetchone()[0]  
            
            percentage = (total_presents / (len(all_columns) - 4)) * 100
            
            # Add percentage in the column
            update_query = f"UPDATE attendance_details.{table_name} SET percentage = {percentage} WHERE enrollment = {enrollment}"
            cursor.execute(update_query)
        
        mysql.connection.commit()
        cursor.close()
        
        return render_template('stop_attendance.html', students_data=students_data, students_count=students_count, selected_subject=selected_subject)
    else:
        return redirect(url_for('faculty.faculty_login'))


# Download Attendance
@faculty.route('/download_attendance', methods=['GET', 'POST'])
def download_attendance():
    if 'faculty_id' in session:
        
        selected_subject = session.get('selected_subject')
        
        # database to excel
        atten_sheet = pd.read_sql(f"SELECT * FROM attendance_details.{selected_subject}", mysql.connection)

        # Create a BytesIO buffer to store the Excel file
        excel_buffer = io.BytesIO()
        atten_sheet.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        # Send the Excel file as a response for download
        return send_file(excel_buffer, download_name=f"{selected_subject}_attendance_sheet.xlsx", as_attachment=True)
    else:
        return redirect(url_for('faculty.faculty_login')) 

# Modify Attendance
@faculty.route('/modify_attendance', methods=['GET','POST'])
def modify_attendance():
    msg=''
    if 'faculty_id' in session:
        
        # Show subjects
        faculty_id = session['faculty_id']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT subject_name FROM attendance_details.college_details WHERE faculty_id = %s", (faculty_id,))
        subjects = cursor.fetchall()
        cursor.close()

        
            
        if request.method == 'POST':
            modify_subject = request.form['subject']
            date = request.form['date']
            enrollment = request.form['enrollment']
            new_attendance = request.form['new_attendance']
            
            try:
                cursor = mysql.connection.cursor()
                cursor.execute(f"UPDATE attendance_details.{modify_subject} SET `{date}` = %s WHERE enrollment = %s;", (new_attendance, enrollment))
                mysql.connection.commit()
                
                if cursor.rowcount > 0:
                    msg='Record Updated successfully!!!'
                else:
                    msg='No records updated. Please try again.'
                
                
                # Fetch all columns from the table
                cursor.execute(f"SHOW COLUMNS FROM attendance_details.{modify_subject}")
                all_columns = [column[0] for column in cursor.fetchall()]
                
                # Start from the 5th column (index 4) for the number of presents
                columns_to_check = all_columns[4:]
                
                sql_query = (
                    f"SELECT SUM("
                    f"{' + '.join([f'(`{column}` = %s)' for column in columns_to_check])}"
                    f") AS total_p_count "
                    f"FROM attendance_details.{modify_subject} WHERE enrollment = %s"
                    )
                # Execute the query
                cursor.execute(sql_query, ['P'] * len(columns_to_check) + [enrollment])
                    
                total_presents = cursor.fetchone()[0]  
                    
                percentage = (total_presents / (len(all_columns) - 4)) * 100
                    
                # Add percentage in the column
                update_query = f"UPDATE attedance_details.{modify_subject} SET percentage = {percentage} WHERE enrollment = {enrollment}"
                cursor.execute(update_query)
                
                mysql.connection.commit()
                cursor.close()
                    
            except Exception:
                msg = 'Error updating records: Date or Enrollment does not exist.'
            
        
        return render_template('modify_attendance.html',subjects=subjects,msg=msg)
    else:
        return redirect(url_for('faculty.faculty_login'))

# Apply Filter 
@faculty.route('/apply_filter', methods=['GET','POST'])
def apply_filter():
    if 'faculty_id' in session:
        # Show subjects
        faculty_id = session['faculty_id']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT subject_name FROM attendance_details.college_details WHERE faculty_id = %s", (faculty_id,))
        subjects = cursor.fetchall()
        cursor.close()


        if request.method == 'POST':
            filtered_subject = request.form['subject']
            given_filter = request.form['filter']
            percentage = request.form['percentage']

            # Redirect to filtered_data with URL parameters
            return redirect(url_for('faculty.filtered_data', filtered_subject=filtered_subject, given_filter=given_filter,percentage=percentage))

        return render_template('apply_filter.html', subjects=subjects)
    else:
        return redirect(url_for('faculty.faculty_login'))

# Filtered data show
@faculty.route('/apply_filter/filtered_data', methods=['GET','POST'])
def filtered_data():
    if 'faculty_id' in session:
        filtered_subject = request.args.get('filtered_subject')
        session['filtered_subject'] = filtered_subject
        
        given_filter = request.args.get('given_filter')
        session['given_filter'] = given_filter
       
        filter_percentage = request.args.get('percentage')
        session['filter_percentage'] = filter_percentage

        cursor = mysql.connection.cursor()
        
        if given_filter == 'greater_than':
            cursor.execute(f"SELECT enrollment, name, percentage FROM attendance_details.{filtered_subject} WHERE percentage >= %s",(filter_percentage,))
            filtered_attendance = cursor.fetchall()
            #app.logger.info(filtered_attendance)
            cursor.execute(f"SELECT COUNT(*) FROM attendance_details.{filtered_subject} WHERE percentage >= %s",(filter_percentage,))
            students_count = cursor.fetchone()[0]
            

        elif given_filter == 'less_than':
            cursor.execute(f"SELECT enrollment, name, percentage FROM attendance_details.{filtered_subject} WHERE percentage <= %s",(filter_percentage,))
            filtered_attendance = cursor.fetchall()
            #app.logger.info(filtered_attendance)
            cursor.execute(f"SELECT COUNT(*) FROM attendance_details.{filtered_subject} WHERE percentage <= %s",(filter_percentage,))
            students_count = cursor.fetchone()[0]
            
        cursor.close()
        
        return render_template('filtered_data.html', filtered_subject=filtered_subject, filtered_attendance=filtered_attendance, students_count=students_count)

    else:
        return redirect(url_for('faculty.faculty_login'))
    
# filter download
@faculty.route('/filter_download', methods=['GET', 'POST'])
def filter_download():
    if 'faculty_id' in session:
        
        filtered_subject = session.get('filtered_subject')
        
        given_filter = session.get('given_filter')
       
        filter_percentage = session.get('filter_percentage')
        
        if given_filter == 'greater_than':
            atten_sheet = pd.read_sql(f"SELECT * FROM attendance_details.{filtered_subject} WHERE percentage >= {filter_percentage}", mysql.connection)

        elif given_filter == 'less_than':
            atten_sheet = pd.read_sql(f"SELECT * FROM attendance_details.{filtered_subject} WHERE percentage <= {filter_percentage}", mysql.connection)
        
        session.pop('filtered_subject')
        session.pop('given_filter')
        session.pop('filter_percentage')
       

        # Create a BytesIO buffer to store the Excel file
        excel_buffer = io.BytesIO()
        atten_sheet.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        # Send the Excel file as a response for download
        return send_file(excel_buffer, download_name=f"Filtered_{filtered_subject}.xlsx", as_attachment=True)
    else:
        return redirect(url_for('faculty.faculty_login'))


#LOG OUT
@faculty.route('/logout', methods=['GET', 'POST'])
def logout():
    faculty_id = session.get('faculty_id')
    if faculty_id:
        session.clear()
        return redirect(url_for('faculty.faculty_login'))


    