from flask_jwt_extended.jwt_manager import JWTManager as JWT
from app.utils import JWT, login_required
from flask import Blueprint, render_template

app = Blueprint('dashboard', __name__, template_folder='templates', static_folder='static', static_url_path='')

jwt : JWT = JWT
database = lambda : jwt.database
def set_jwt(value):
    global jwt
    jwt = value

@app.route('/', methods=['GET','POST'])
@login_required()
def index():
    return render_template('index.html')