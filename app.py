from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
from database import configure_mysql

from werkzeug.routing import BuildError
from jinja2.exceptions import TemplateNotFound


from admin.admin import admin
from faculty.faculty import faculty
from student.student import student


app = Flask(__name__)
configure_mysql(app)

app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(faculty, url_prefix='/faculty')
app.register_blueprint(student, url_prefix='/student')

app.secret_key = 'ekdjo39ijdowdpwmdo39dowdmw'  



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
            return redirect(url_for('faculty.faculty_login'))
        elif role == 'student':
            return redirect(url_for('student.student_login'))
    return render_template('choose.html')


@app.errorhandler(404)
@app.errorhandler(500)
@app.errorhandler(505)
def handle_errors(error):
    return render_template('error.html'), error.code

@app.errorhandler(BuildError)
def handle_build_error(error):
    return render_template('error.html'), 500  

@app.errorhandler(TemplateNotFound)
def template_not_found(error):
    return render_template('error.html'), 404


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
