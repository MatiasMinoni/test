from flask import Blueprint, url_for, redirect, session, request, flash, render_template
from flask_bcrypt import Bcrypt
from flask_jwt_extended.utils import set_access_cookies, unset_jwt_cookies
from flask_jwt_extended.view_decorators import jwt_required
from app.forms import Validators, UserForm
from app.utils import JWT, is_logged


app = Blueprint('auth', __name__, template_folder='templates', static_folder='static', static_url_path='/user/static/')
bcrypt = Bcrypt()
jwt : JWT = JWT


def set_jwt(value):
    global jwt
    jwt = value

@app.route('/user/sign_in', methods=['GET','POST'])
@is_logged()
def sign_in():

    validator = Validators(jwt.get_database())
    user = UserForm(bcrypt, jwt.get_database())

    response = validator.validate_form(request.form, bcrypt)
    if request.method == 'POST':
        if isinstance(response, bool):
            token = user.get_access_token(email=request.form['email'])
            response = redirect(url_for('dashboard.index'))
            set_access_cookies(response, token)
            return response
        else:
            flash(response)
        return render_template('sign_in.html')

    elif request.method == 'GET':
        return render_template('sign_in.html')

@app.route('/user/sign_up', methods=['GET','POST'])
@is_logged()
def sign_up():

    validator = Validators(jwt.get_database())
    user = UserForm(bcrypt, jwt.get_database())
    response = validator.validate_form(request.form, bcrypt, type='sign_up')
    if request.method == 'POST':
        if isinstance(response, bool):
            response = user.create_account(email=request.form['email'], password=request.form['password'])
            flash(response)
            return render_template('sign_up.html')
        else:
            flash(response) 
        return render_template('sign_up.html')

    elif request.method == 'GET':
        return render_template('sign_up.html')

@app.route('/logout', methods=['GET','POST'])
def logout():
    response = redirect(url_for('auth.sign_in'))
    unset_jwt_cookies(response)
    return response