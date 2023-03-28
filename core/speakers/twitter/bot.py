from core.speakers.utils import download_image
import tweepy
from typing import NoReturn

SUCCESS = True
ERROR = False

class TWBot:

    TWITTER_CHARACTERS_LIMIT = 280
    DOTS = 3

    def __init__(self):
        self.consumer_key = ''
        self.consumer_secret = ''
        self.access_token = ''
        self.access_secret = ''

    def update_config(self, **kwargs):
        if (consumer_key:=kwargs.get('consumer_key')):
            self.consumer_key = consumer_key

        if (consumer_secret:=kwargs.get('consumer_secret')):
            self.consumer_secret = consumer_secret

        if (access_token:=kwargs.get('access_token')):
            self.access_token = access_token

        if (access_secret:=kwargs.get('secret_token')):
            self.access_secret = access_secret

    def _auth(self):

        try:
            auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
            auth.set_access_token(self.access_token, self.access_secret)
            self.api = tweepy.API(auth)
            return SUCCESS
        except:
            return ERROR

    def auth(self, **kwargs):
        return self._auth()

    def send_message(self, message, image_url, token=None, **kwargs) -> NoReturn:
        
        try:
            self.api.verify_credentials()
            image_path = download_image(image_url)

            if isinstance(image_path, str):
                self.api.update_with_media(image_path, message)
            else:
                self.api.update_status(status=message)
        except tweepy.TweepError:
            return
        except:
            self._auth()
            return self.send_message(message, image_url, token=token)

    def start_bot(self):
        self.auth()

    def stop_bot(self):
        del self.api