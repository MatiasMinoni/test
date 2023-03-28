from flask import session
from secrets import token_urlsafe
from datetime import datetime
from calendar import month_abbr
from requests import get
from bs4 import BeautifulSoup


class BaseUser:

    def __init__(self, database):
        self.database = database

    def _create_user(self, data):

        self.database._user_model()
        try:
            self.database.new_user_model['email'] = data['email']
            self.database.new_user_model['password'] = data['password']
            self.database.new_user_model['token'] = token_urlsafe(16)
            return (self.database.collection.insert_one(self.database.new_user_model) is not None)
        except KeyError:
            return

    def _login_user(self, email):
        session['token'] = self._get_token(email)

    def _get_password_hash(self, email):

        query = self.database.collection.find_one({'email': email})
        if query is not None:
            return query['password']

    def _is_registered_by_email(self, email):

        return self.database.collection.find_one({'email': email})

    def _get_token(self, email):

        query = self.database.collection.find_one({'email': email})
        if query is not None:
            return query['token']

    def _is_registered_by_token(self, token):

        user_data = self.database.get_data({'token': token})
        return (user_data is not None)

    def _get_sessions(self, token):

        user_data = self.database.get_data({'token': token})

        return user_data['sessions']

    def _get_configs(self, token):

        user_data = self.database.get_data({'token': token})
        try:
            return user_data['configs']
        except TypeError:
            return

    def _get_all_urls(self):

        urls = self.database.urls.find({}, {'_id': False})
        if urls is not None:
            return list(urls)
        return []

    def _get_one_url(self, key):

        data = self.database.urls.find_one({"uuid": key})

        if data is not None:
            return data['data']

    def _add_url(self, data):

        name = data.get('title', 'Url')
        url = data.get('url')
        key = token_urlsafe(6).replace('_', '').replace('-', '')
        exists_in_database = self._get_one_url(key)

        if (temp := self.database.urls.find_one({"data.original_url": url})) is not None:
            return f"https://cholli.to/{temp['uuid']}"

        if not exists_in_database:  # Si nos retorna un None es porque no existe en la database
            assert (self.database.urls.insert_one({"uuid": key, "clicks": 0, "data": {
                    "url": f"https://cholli.to/{key}", "title": name, "created": self.created_date(), "original_url": url, "clicks": 0}}) is not None)

            return f"https://cholli.to/{key}"
        else:
            if exists_in_database['data']['original_url'].lower() == url.lower():
                return f"https://cholli.to/{key}"

        return self._add_url(data)

    def _add_url_with_response(self, data):
        # Refactorizar el codigo de add_url para combinar con el with_response.
        name = data.get('title', 'Url')
        url = data.get('url')
        key = token_urlsafe(6).replace('_', '').replace('-', '')
        exists_in_database = self._get_one_url(key)

        if not self.have_title(name):
            name = self.get_title_from_url(url)

        response = {"uuid": key, "clicks": 0, "data": {"url": f"https://cholli.to/{key}",
                                                       "title": name, "created": self.created_date(), "original_url": url, "clicks": 0}}

        if (temp := self.database.urls.find_one({"data.original_url": url}, {"_id": False})) is not None:
            response.update(temp)
            response['info'] = '¡La URL ya existe!'
            if '_id' in response:
                response.pop('_id')
            return response

        if not exists_in_database:  # Si nos retorna un None es porque no existe en la database
            assert (self.database.urls.insert_one(response) is not None)
            response['info'] = '¡Link creado!'
            if '_id' in response:
                response.pop('_id')
            return response

        return self._add_url_with_response(data)

    def _add_click(self, key):

        try:
            data = self.database.urls.find_one({"uuid": key})
            if data is not None:
                clicks = data['clicks'] if data['clicks'] is not None else 1

                self.database.urls.update_one(
                    data, {'$set': {'clicks': clicks+1}})
        except Exception as error:
            print(error)

    def _delete_url(self, key):

        try:
            self.database.urls.delete_one({'uuid': key})
        except Exception as error:
            print(error)

    def _get_total_urls(self):

        try:
            return self.database.urls.count()
        except:
            return 0

    def _update_user_config(self, **kwargs):

        token = kwargs.pop('token')

        user_data = self.database.get_data({'token': token})
        config = kwargs.pop('configs')
        name = list(config.keys())[0]

        if name == 'shortener':
            user_data['configs'][name] = config[name]
        else:
            user_data['configs'][name].update(config[name])

        return self.database.update({'token': token}, user_data)

    @staticmethod
    def created_date():
        time = datetime.today()
        return {'day': time.day, 'month': month_abbr[time.month], 'year': time.year}

    @staticmethod
    def is_valid_url(url):

        if url.count('http') or url.count('https'):
            return url

        return None

    @staticmethod
    def get_title_from_url(url: str) -> str:

        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 OPR/72.0.3815.487'}

        response = get(url, headers=headers)

        if response.status_code == 200:
            try:
                doc = BeautifulSoup(response.content)
                title = doc.findAll('title')[0].get_text()[0:70]
                return title
            except:
                return 'Sin titulo'
        return 'Sin titulo'

    @staticmethod
    def have_title(title: str) -> bool:

        return len(title) >= 1
