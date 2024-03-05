# database.py
from flask_mysqldb import MySQL

mysql = MySQL()

# MySQL configuration


def configure_mysql(app):
    app.config['MYSQL_HOST'] = '127.0.0.1'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'root'
    app.config['MYSQL_DB'] = 'wifiattendance'

    mysql.init_app(app)
