# database.py
from flask_mysqldb import MySQL

mysql = MySQL()

# MySQL configuration
def configure_mysql(app):
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'akshar'
    app.config['MYSQL_DB'] = 'wifiattendance'

    mysql.init_app(app)


