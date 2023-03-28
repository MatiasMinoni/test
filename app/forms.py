"""
Author: Scr44gr
"""
from app.database.models import Account as User
from app.database.identity import Identity, ID
from os import getenv
from flask_jwt_extended import create_access_token, set_access_cookies
from uuid import uuid4

class Validators:
    
    def __init__(self, db):
        self.user = User(db)
        self.code = getenv('INVITATION_CODE')

    def validate_form(self, form, bcrypt, type='login'):
        
        self.form = form
        self.bcrypt = bcrypt
        if type == 'login':
            return self.__validate_login()
        elif type == 'sign_up':
            return self.__validate_sign_up()
        return 'error'
    
    def __validate_login(self):
        
        email = self.form.get('email')
        password = self.form.get('password')
        identity = Identity('email', ID, email) 
        if self.user.is_registered(identity):
            if self.bcrypt.check_password_hash(self.user.get_password_hash(identity).get('password'), password):
                return True
            else:
                return 'Contraseña inválida!'
        else:
            return 'Correo electronico inválido!'

    def __validate_sign_up(self):

        email = self.form.get('email')
        password = self.form.get('password')
        confirm_password = self.form.get('confirm-password')
        code = self.form.get('code')

        try:
            if not self.user.is_registered(Identity('email', ID, email)):
                if password == confirm_password and code == self.code:
                    return True
                elif code != self.code:
                    return 'Lo sentimos, el código que has usado es invalido!'
                return 'Las contraseñas no coinciden!'
            else:
                return 'Correo electrónico ya existe en la base de datos!'
        except:
            return 'Error, por favor inténtalo mas tarde!'

class UserForm:
    
    def __init__(self, bcrypt, db):
        self.user = User(db)
        self.bcrypt = bcrypt

    def create_account(self, **kwargs):
        
        data = kwargs
        data['password'] = self.bcrypt.generate_password_hash(kwargs['password'])
        data['token'] = f'token__{uuid4()}'
        data['role'] = 'editor'

        if self.user.create_account(data):
            return 'El usuario ha sido creado exitosamente!'
        else:
            return 'Error, por favor inténtalo otra vez!'

    def get_access_token(self, **kwargs):
        identity = Identity('email', ID, kwargs.get('email'))
        aditional_claims = self.user.get_user_info(identity)
        token = create_access_token(identity=identity.value, additional_claims=aditional_claims)
        return token

    def edit_user(self, **kwargs): ...

    def delete_user(self, **kwargs): ...
