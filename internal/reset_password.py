from database import mysql
from admin.admin import send_email, generate_random_string

def get_user_id(email, table_name, identifier):
    cursor = mysql.connection.cursor()
    sql = f"SELECT {identifier} FROM wifiattendance.{table_name} where email = '{email}';"
    cursor.execute(sql)
    user_id = cursor.fetchone()
    cursor.close()
    return user_id[0] if user_id else None

def save_reset_token(user_id, secret_token):
    cursor = mysql.connection.cursor()
    sql = "INSERT INTO wifiattendance.reset_password (id, password_token) values (%s, %s)"
    values = (user_id, secret_token)
    cursor.execute(sql, values)
    mysql.connection.commit()
    cursor.close()

def send_reset_email(email, secret_token):
    subject = "Reset Password"
    body = f"Enter the following token to reset your password: \n {secret_token}"
    send_email(email, subject, body)
    
def check_reset_token(token):
    cursor = mysql.connection.cursor()
    sql = f"SELECT id FROM wifiattendance.reset_password where password_token = '{token}';"
    cursor.execute(sql)
    result = cursor.fetchone()
    cursor.close()
    return result is not None

def update_password(user_id, new_password, table_name):
    cursor = mysql.connection.cursor()
    if table_name == "student_accounts":
        sql = f"UPDATE wifiattendance.{table_name} SET password = '{new_password}' where enrollment = '{user_id}';"
    else:
        sql = f"UPDATE wifiattendance.{table_name} SET password = '{new_password}' where id = '{user_id}';"
        
    cursor.execute(sql)
    mysql.connection.commit()
    cursor.close()

def delete_reset_token(user_id):
    cursor = mysql.connection.cursor()
    sql = f"DELETE FROM wifiattendance.reset_password where id = '{user_id}';"
    cursor.execute(sql)
    mysql.connection.commit()
    cursor.close()
