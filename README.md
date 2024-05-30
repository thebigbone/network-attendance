<p align="center">
  <img alt="network attendance" src="./assets/image.png" width="150" />
</p>

### Network Based Attendance System

[![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/License-CC_BY--NC--ND_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)

### Requirements

- Python >= 3.8
- Linux or Windows
- MySQL

### Demo Video

![Admin Panel](/assets/Admin_Panel.gif)

![Faculty-Student Panel](/assets/FacultyStudent_Panel.gif)


### Installation

#### Manual Install

First, install the requirements:

```
pip install -r requirements.txt
```

After that, create a `database.py` file. It will be used to enter MySQL credentials.

Sample `database.py`:

```python
from flask_mysqldb import MySQL

mysql = MySQL()

def configure_mysql(app):
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'user'
    app.config['MYSQL_PASSWORD'] = 'pass'

    mysql.init_app(app)
```

For using the email functionality, create `.env` file with following details. We are using gmail's smtp:

```.env
GOOGLE_EMAIL=example@gmail.com
GOOGLE_PASSWORD=password
```

Now, run the queries in the `database.txt` for creating the database.

#### Docker install

- Work in progress.

### Description

Current attendance systems are tedious and prone to error. We wanted to change that therefore we built a network attendance system from ground up using Flask and Python. Some of the features:

1. Dedicated dashboards for **student, faculty and admin**.
2. Admin can do the following things:
   - Upload faculty and student list from a csv file
   - Secure password generation for faculty and student
   - Passwords are emailed to both are successful upload
   - Add subject list
   - Allocate and delete subjects to faculty
3. Faculty can do the following things:
   - Start attendance and generate a secure token
   - Filter the attendance details by percentage
   - Modify the attendance of students

### Tech Stack

![tech](/assets/techstack1.png)

### System architecture

Our **first architecture** was just divided between faculty and student.

However, **we completely rewrote it** and **introduced an admin panel** which **handles all the administration work**. Thereby eliminating the need for faculty(s) or student(s) worrying about proper registration.

Our **current architecture** is described below:

![flow](/assets/flow.png)

### Run the application

To start the application, run:

```sh
flask run
```

If you want to start in debug mode, add `--debug` flag.

<p xmlns:cc="http://creativecommons.org/ns#" >This work is licensed under <a href="http://creativecommons.org/licenses/by-nc-nd/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">CC BY-NC-ND 4.0<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/nc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/nd.svg?ref=chooser-v1"></a></p>
