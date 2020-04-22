from flask import Flask
from flask_mail import Mail
import pymysql
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
mydb = pymysql.connect(
  host="localhost",
  user="root",
  password="Aditya@22",
  database="dbms_project",
  cursorclass=pymysql.cursors.DictCursor
)
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'pblvjti@gmail.com'
app.config['MAIL_PASSWORD'] = 'arch1234'
mail = Mail(app)

from ONLINE_SHOP import routes