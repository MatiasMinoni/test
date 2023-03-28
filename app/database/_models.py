#Deprecated!

from app.database.base import BaseUser
from flask import redirect, url_for, session
from functools import wraps
import pymongo
import json
import os

UUID_LENGTH_MAX_SIZE = 9

class MongoServer:

    def __init__(self, model='users'):
        
        self.client = pymongo.MongoClient(self.auth)
        self.db = self.client[os.environ['DB_NAME']]
        self.collection = self.db[model]
        self.urls = self.db['urls']
        self.t_users = self.db['t_users']

    def _user_model(self):
        with open('./app/database/system_model.json', 'r') as user_model:
            self.new_user_model = json.load(user_model)
            user_model.close()

    def get_data(self, data):
        """make a query for the user and if the user exist return the user_data"""

        if self.collection.find_one({'token': data['token']}) is not None:
            return self.collection.find_one({'token': data['token']})

    def add(self, data):

        query = self.collection.find_one({'user_id': data['user_id']})
        return (self.collection.update_one(query, data) is not None)
    
    def add_session(self, user_query, data):

        query = self.collection.find_one({'token': user_query['token']})
        return(self.collection.update_one(query, {'$set':data}) is not None)

    def update(self, user, data):

        query = self.collection.find_one({'token': user['token']})
        return (self.collection.update_one(query, {'$set': data}) is not None)
    
    def get_collection(self):

        return self.collection.find()

    @property
    def auth(self):
        return "mongodb+srv://{}:{}@{}{}?retryWrites=true&w=majority".format(os.environ['DB_USER'], os.environ['DB_PASSWORD'], os.environ['DB_URI'], os.environ['DB_NAME'])

class TelegramVotes:
    """
    
        Modelo: 
        {user_id:int, 'messages_id':<list<int>>}
    """
    def __init__(self, db):
        self.db = db

    def user_exists(self, user_id):

        response = self.db.t_users.find_one({'user_id':user_id})
        if response is not None:
            return response

    def vote(self, user_id, message_id):

        response = self.user_exists(user_id)

        if response is not None:
            if not self.user_voted(response, user_id, message_id):
                return self._vote(user_id, message_id, response)
        else:
            return self._new_user_vote(user_id, message_id)

    def user_voted(self, response, user_id, message_id):
        return message_id in response['messages_id']

    def _vote(self, user_id, message_id, response):

        query = self.db.t_users.find_one({'user_id':user_id})
        messages_id = query['messages_id'] + [message_id]
        response = (self.db.t_users.update_one(query, {'$set':{'messages_id':messages_id}}) is not None)
        return response

    def _new_user_vote(self, user_id, message_id):

        return (self.db.t_users.insert_one({'user_id':user_id, 'messages_id':[message_id]}) is not None)


class User(BaseUser):
    
    def __init__(self, db):
        BaseUser.__init__(self, db)
   
    def create_user(self, **kwargs):
        """
        ----------------------------------------------
         CREATE NEW USER IN THE DATABASE 
        ----------------------------------------------

        """
        return self._create_user(kwargs)
    
    def login_user(self, **kwargs):
        """
        ----------------------------------------------
         GET TOKEN FROM THE DATABASE SET TO SESSION COOKIE
        ----------------------------------------------

        """
        return self._login_user(kwargs.get('email'))

    def is_registered(self, **kwargs):
        """
        ----------------------------------------------------------
         CHECK IF THE USER OR COMPANY EXISTS IN THE DATABASE
        ----------------------------------------------------------
        ____________________________
        kwargs:
            - email -> str
            - token -> str
        return:
            -> bool
        ____________________________
        """

        if kwargs.get('email') is not None:
            return self._is_registered_by_email(kwargs.get('email'))

        if kwargs.get('token') is not None:
            return self._is_registered_by_token(kwargs.get('token'))
    
    def get_token(self, **kwargs):
        return self._get_token(kwargs.get('email'))
    
    def get_password_hash(self, **kwargs):
        return self._get_password_hash(kwargs.get('email'))

    def get_configs(self, **kwargs):

        name = kwargs.get('name')
        token = kwargs.get('token')

        if name is not None:

            return self._get_configs(token)[name]
        return self._get_configs(token)

    def get_url(self, **kwargs):
        """
        Con este metodo obtenemos una url especifica.

        kwargs:
            key: str - llave de la url
        """

        key = kwargs.get('key')

        if key is not None and len(key) <= UUID_LENGTH_MAX_SIZE:
            url = self._get_one_url(key)
            if url is not None:
                return url['original_url']

    def get_all_urls(self, **kwargs):
        """
        Con este metodo obtenemos todas las urls con sus informaciones.

        kwagrs:
            token: str - token de la sesion actual
        """
        index = kwargs.get('index')

        return self._get_all_urls()

    def add_url(self, data, **kwargs):
        """
        Con este metodo añadimos una url acortada a la base de datos.

        params:
            data: dict - datos a almacenar

        """
        if kwargs.get('with_response'):
            return self._add_url_with_response(data)

        return self._add_url(data)

    def add_click(self, key):
        
        self._add_click(key)

    def delete_url(self, key):

        self._delete_url(key)

    def get_total_urls(self):

        return self._get_total_urls()

    def update_user_config(self, **kwargs):

        return self._update_user_config(**kwargs)

class UserConfig(User):

    def __init__(self, db):
        super().__init__(db)

        self._current_user = ''

    @property
    def current_user(self):
        return self._current_user

    @current_user.setter
    def current_user(self, token : str):
        self._current_user = token

    @property
    def shortener(self):
        try:
            response = self.get_configs(token=self.current_user)['shortener']
            return response if response != None else 'chollito' 
        except:
            return 'chollito'

    @property
    def telegram_chat_id(self):
        try:
            return self.get_configs(token=self.current_user)['telegram']['telegram_chat_id']
        except TypeError:
            return
    @property
    def telegram_bot_token(self):
        try:
            return self.get_configs(token=self.current_user)['telegram']['telegram_bot_token']
        except TypeError:
            return
    @property
    def tw_consumer_key(self):
        try:
            return self.get_configs(token=self.current_user)['twitter']['tw_consumer_key']
        except TypeError:
            return
    @property
    def tw_consumer_secret(self):
        try:
            return self.get_configs(token=self.current_user)['twitter']['tw_consumer_secret']
        except TypeError:
            return

    @property
    def tw_access_token(self):
        try:
            return self.get_configs(token=self.current_user)['twitter']['tw_access_token']
        except TypeError:
            return

    @property
    def tw_access_secret(self):
        try:
            return self.get_configs(token=self.current_user)['twitter']['tw_access_secret']
        except TypeError:
            return

    @property
    def fb_session(self):
        try:
            return self.get_configs(token=self.current_user)['facebook']['fb_session']
        except TypeError:
            return

    @property
    def fb_access_token(self):
        try:
            return self.get_configs(token=self.current_user)['facebook']['fb_access_token']
        except TypeError:
            return

    @property
    def fb_password(self):
        try:
            return self.get_configs(token=self.current_user)['facebook']['fb_password']
        except TypeError:
            return

    @shortener.setter
    def shortener(self, value):
        config = {'shortener':value}
        return self.update_user_config(token=self.current_user, configs=config)

    @telegram_chat_id.setter
    def telegram_chat_id(self, value):
        config = {'telegram':{'telegram_chat_id':value}}
        return self.update_user_config(token=self.current_user, configs=config)
    
    @telegram_bot_token.setter
    def telegram_bot_token(self, value):
        config = {'telegram':{'telegram_bot_token':value}}
        return self.update_user_config(token=self.current_user, configs=config)

    @tw_access_token.setter
    def tw_access_token(self, value):
        config = {'twitter':{'tw_access_token':value}}
        return self.update_user_config(token=self.current_user, configs=config)
    
    @tw_access_secret.setter
    def tw_access_secret(self, value):
        config = {'twitter':{'tw_access_secret':value}}
        return self.update_user_config(token=self.current_user, configs=config)
    
    @tw_consumer_key.setter
    def tw_consumer_key(self, value):
        config = {'twitter':{'tw_consumer_key':value}}
        return self.update_user_config(token=self.current_user, configs=config)

    @tw_consumer_secret.setter
    def tw_consumer_secret(self, value):
        config = {'twitter':{'tw_consumer_secret':value}}
        return self.update_user_config(token=self.current_user, configs=config)
    
    @fb_access_token.setter
    def fb_access_token(self, value):
        config = {'facebook':{'fb_access_token':value}}
        return self.update_user_config(token=self.current_user, configs=config)
    
    @fb_password.setter
    def fb_password(self, value):
        config = {'facebook':{'fb_password':value}}
        return self.update_user_config(token=self.current_user, configs=config)

    @fb_session.setter
    def fb_session(self, value):
        config = {'facebook':{'fb_session':value}}
        return self.update_user_config(token=self.current_user, configs=config)

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        user = User(kwargs.get('db'))
        if 'token' in session:
            if user.is_registered(token=session['token']):
                return f(*args, **kwargs)
            else:
                session.pop('token')
        return redirect(url_for('auth.sign_in'))
    return wrap 

def is_logged(f, db):
    @wraps(f)
    def wrap(*args, **kwargs):
        user = User(kwargs.get('db'))
        if 'token' in session:
            if user.is_registered(token=session['token']):
                return redirect(url_for('dashboard.index'))
        else:
            return f(*args, **kwargs)
    return wrap