from logging import getLogger
from sys import stdout
from core.speakers.utils import download_image
from pyfacebook import GraphAPI

NOT_DEFINED = None

class FBot:

    def __init__(self, bot_id: str):
        self.__logger = getLogger(f'<FacebookSpeaker> bot_id -> {bot_id}')
        self.api = NOT_DEFINED
        self.access_token = ''

    def auth(self, **kwargs):

        try:
            if len(self.access_token) >= 1:
                self.api = GraphAPI(access_token=self.access_token)
        except:
            self.__logger.error('an error ocurred on [auth]\ndetails:\n', exc_info=1)

    def update_config(self, **kwargs):

        if kwargs.get('access_token') is not None:
            self.stop_bot()
            self.access_token = kwargs.get('access_token')
            self.start_bot()

    def send_message(self, message, image_url, **kwargs):
        try:
            if self.api is NOT_DEFINED and self.access_token:
                self.api = GraphAPI(access_token=self.access_token)

            #post_id = self.api.post_object(object_id='685791634883049', connection='feed', data=dict(message=message, image=image_url))
            # send a post with a photo.
            # get he page id
            page_id = self.api.get_object(object_id='me')['id']
            post_id = self.api.post_object(object_id=page_id, connection='photos', data=dict(message=message, url=image_url))
            return 'id' in post_id
        except:
            self.__logger.error('an error ocurred on [send_message]\ndetails:\n', exc_info=1)

    def start_bot(self):
        self.auth()
    
    def stop_bot(self):
        self.api = NOT_DEFINED