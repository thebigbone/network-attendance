from flask import Blueprint, render_template, request, redirect, url_for, session
from database import mysql



admin = Blueprint("admin", __name__ , static_folder="static", template_folder="templates")




#admin login
@admin.route('/')
@admin.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if 'email' in session:
        return redirect(url_for('admin.admin_dashboard'))
    else:
        msg = ''
        if request.method == 'POST' and 'admin_email' in request.form and 'password' in request.form:
            admin_email = request.form['admin_email']
            password = request.form['password']
            
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM admin_accounts WHERE email = %s AND password = %s", (admin_email, password))
            account = cursor.fetchone()
            cursor.close()
            
            if account:
                session['admin_email'] = admin_email
                
                return redirect(url_for('admin.admin_dashboard'))
            else:
                msg = 'Incorrect email or password!'
    return render_template('admin_login.html', msg=msg)

#admin Register
@admin.route('/admin_register',methods=['GET','POST'])
def admin_register():
    if request.method == 'POST' and 'admin_email' in request.form and 'name' in request.form and 'password' in request.form:
        admin_email = request.form['admin_email']
        name = request.form['name']  
        password = request.form['password']
        
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO admin_accounts (email, name, password) VALUES (%s, %s, %s)", (admin_email, name, password))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('admin.admin_login'))
    
    return render_template('admin_register.html')

#admin dashboard
@admin.route('/admin_dashboard',methods=['GET','POST'])
def admin_dashboard():
    if 'admin_email' in session:
       

        
    
        return render_template('admin_dashboard.html')
    else:
        return redirect(url_for('admin.admin_login'))
    
#time table management
@admin.route('/time_table_manage',methods=['GET','POST'])
def time_table():
    if 'admin_email' in session: 
       

        
    
        return render_template('time_table_manage.html')
    else:
        return redirect(url_for('admin.admin_login'))
    
#Add new subjects
@admin.route('/time_table_manage/add_subject_list',methods=['GET','POST'])
def add_subject_list():
    if 'admin_email' in session: 
       

        
    
        return render_template('add_subject_list.html')
    else:
        return redirect(url_for('admin.admin_login'))
    
#Add new subjects
@admin.route('/time_table_manage/modify_subject_list',methods=['GET','POST'])
def modify_subject_list():
    if 'admin_email' in session: 
       

        
    
        return render_template('modify_subject_list.html')
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

#allocate subjects
@admin.route('/faculty_manage/allocate_subjects',methods=['GET','POST'])
def allocate_subjects():
    if 'admin_email' in session: 
       

        
    
        return render_template('allocate_subjects.html')
    else:
        return redirect(url_for('admin.admin_login'))


#Student Management
@admin.route('/student_manage',methods=['GET','POST'])
def student():
    if 'admin_email' in session: 
       

        
    
        return render_template('student_manage.html')
    else:
        return redirect(url_for('admin.admin_login'))

#Add student
@admin.route('/student_manage/add_student_list',methods=['GET','POST'])
def add_student_list():
    if 'admin_email' in session: 
       

        
    
        return render_template('add_student_list.html')
    else:
        return redirect(url_for('admin.admin_login'))
