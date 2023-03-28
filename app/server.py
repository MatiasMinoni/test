#from eventlet import monkey_patch
#_ = monkey_patch(all=True)


from app.forms import UserForm
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from flask import jsonify
from flask_jwt_extended import set_access_cookies
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import get_jwt
from app.websocket.chollito_namespace import ChollitoNamespace
from core.webs.web_controller import ChollosWebController
from core.bot_service import BotServiceController
from core.chollito_service import ChollitoService
from app.utils import JWT
from app.database.databases.mongodb import MongoDB
from app.websocket.shortener_namespace import ShortenerNamespace
from datetime import datetime, timedelta
from app.views.user import view as dashboard
from app.views.auth import view as auth
from app.database.models import Account as User
from app.views.shortener import view as shortener
from app.api import v1 as web_api
from flask_socketio import SocketIO
from flask_bcrypt import Bcrypt
from flask import Flask
import os
from flask_talisman import Talisman
from flask_jwt_extended.view_decorators import jwt_required
from dotenv import load_dotenv, find_dotenv



load_dotenv(find_dotenv(), override=True)


def set_up_blueprints():

    auth.set_jwt(jwt)
    shortener.set_jwt(jwt)
    dashboard.set_jwt(jwt)
    web_api.set_services({'bot_service':bot_service, 'chollos_web_controller':web_controller})


db = MongoDB()
web_controller = ChollosWebController()
bot_service = BotServiceController(db)
chollito_service = ChollitoService(db, bot_service)


class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        # Default is '{{', I'm changing this because Vue.js uses '{{' / '}}'
        variable_start_string='%%',
        variable_end_string='%%',
    ))


def create_app():

    app = CustomFlask(__name__)
    Talisman(app, content_security_policy=None)
    app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
    app.config['JWT_SECRET_KEY'] = os.environ['SECRET_KEY']
    app.config["JWT_COOKIE_SECURE"] = False
    app.config['JWT_CSRF_IN_COOKIES'] = True
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.secret_key = os.environ['SECRET_KEY']
    bcrypt = Bcrypt(app)
    auth.bcrypt = bcrypt
    socketio = SocketIO(app, logger=True, always_connect=True,
                        async_mode='eventlet')
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.register_blueprint(auth.app, url_prefix='')
    app.register_blueprint(dashboard.app, url_prefix='')
    app.register_blueprint(shortener.app, url_prefix='')
    app.register_blueprint(web_api.app, url_prefix='')

    return (app, socketio)


def set_up_app(loop):
    bot_service.start_service()
    chollito_service.start_service()
    web_controller.run()
    set_up_blueprints()

user = User(db)
app, socketio = create_app()
jwt = JWT(app, user)
set_up_app(None)

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            uform = UserForm(None, db)
            access_token = uform.get_access_token(email=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original respone
        return response


@app.route('/refresh', methods=['GET', 'POST'])
@jwt_required()
def refresh_token():
    response = jsonify({'status':'ok'})
    return response

shorterner_namespace = ShortenerNamespace('/shortener')
shorterner_namespace.set_up_namespace(database=jwt.get_database())
socketio.on_namespace(shorterner_namespace)

# set up chollito namespace
chollito_namespace = ChollitoNamespace('/app')
chollito_namespace.set_service('web_controller', web_controller)
chollito_namespace.set_service('chollito_service', chollito_service)
chollito_namespace.set_service('bot_service', bot_service)
socketio.on_namespace(chollito_namespace)
