from flask.helpers import url_for
from flask_jwt_extended.utils import unset_jwt_cookies
from werkzeug.utils import redirect
from app.database.models.account import Account
from app.database.identity import ID, Identity
from flask_jwt_extended import create_access_token
from flask_jwt_extended import set_access_cookies
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import get_jwt
from flask_jwt_extended import JWTManager, verify_jwt_in_request
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from functools import wraps


def login_required(by_socket=False):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                if claims.get('role') == 'editor':
                    return fn(*args, **kwargs)
                elif claims.get('role') == 'admin':
                    return fn(*args, **kwargs)  # change this
                else:
                    return redirect(url_for('auth.sign_in'))
            except:
                if not by_socket:
                    return redirect(url_for('auth.sign_in'))
                return fn(*args, disconnect=True)
        return decorator
    return wrapper


def is_logged():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                if claims.get('role') == 'editor':
                    return redirect(url_for('dashboard.index'))
                elif claims.get('role') == 'admin':
                    return redirect(url_for('dashboard.index'))  # change this
                else:
                    response = redirect(url_for('auth.sign_in'))
                    unset_jwt_cookies(response)
                    return response
            except:
                return fn(*args, **kwargs)
        return decorator
    return wrapper


class JWT(JWTManager):

    def __init__(self, app, user: Account) -> None:
        super().__init__(app=app)
        self.app = app
        self.user = user
        self.set_dispatchers()

    def get_database(self):
        return self.user.database

    def refresh_expiring_jwts(self, response):
        try:
            exp_timestamp = get_jwt()["exp"]
            now = datetime.now(timezone.utc)
            target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
            if target_timestamp > exp_timestamp:
                access_token = create_access_token(identity=get_jwt_identity())
                set_access_cookies(response, access_token)
            return response
        except (RuntimeError, KeyError):
            return response

    def set_dispatchers(self):
        self.user_identity_loader(self.user_identity_callback)
        self.user_lookup_loader(self.user_lookup_callback)

    def user_identity_callback(self, user):
        return user

    def user_lookup_callback(self, _jwt_header, jwt_data):
        identity = jwt_data['sub']
        return self.user.is_registered(Identity('email', ID, identity))
