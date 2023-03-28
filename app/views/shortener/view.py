from app.utils import JWT, login_required
from flask import Blueprint, redirect, render_template, abort, request
from app.database.models import Shortener

app = Blueprint('shortener', __name__, template_folder='templates', static_folder='static', static_url_path='/shortener/static/')

jwt : JWT = JWT
database = lambda : jwt.database
def set_jwt(value):
    global jwt
    jwt = value

@app.route('/shortener/dashboard', methods=['GET', 'POST'])
@login_required()
def dashboard():
    return render_template('shortener.html')

@app.route('/<url_uuid>', methods=['GET'])
def index(url_uuid):
    
    temp = Shortener(jwt.get_database())
    telegram_user_id = request.args.get('telegram_user_id')
    try:
        url = temp.get_one_url(url_uuid)['data']['original_url']
        if url is not None:
            temp.add_click(url_uuid, telegram_user_id=telegram_user_id)
            return redirect(url)
    except TypeError:
        return abort(404)
    return abort(404)

@app.errorhandler(404)
def error(error):
    return redirect("https://soydechollos.com")