from app.utils import login_required
from flask_socketio import Namespace, emit
from app.database.models import Shortener
from typing import List


class ShortenerNamespace(Namespace):

    def set_up_namespace(self, **kwargs):
        self.database = kwargs.get('database')

    @login_required()
    def on_connected(self, urls: List):
        if len(urls) == 0:
            shortener = Shortener(self.database)
            urls = shortener.get_all_urls()
            emit('add_urls', urls)
    
    @login_required()
    def on_add_url(self, data):
        shortener = Shortener(self.database)
        payload = shortener.add_url(data, from_web_app=True)
        emit('created_item_response', payload)
        urls = shortener.get_all_urls()
        emit('add_urls', urls)
        emit('add_total_urls', {'total': shortener.get_total_urls()})
    
    @login_required()
    def on_get_urls(self):

        shortener = Shortener(self.database)    
        urls = shortener.get_all_urls()
        emit('add_urls', urls)
        emit('add_total_urls', {'total': shortener.get_total_urls()})
    
    @login_required()
    def on_get_total_urls(self):

        shortener = Shortener(self.database)
        emit('add_total_urls', {'total': shortener.get_total_urls()})

    @login_required()
    def on_delete_url(self, uuid: str):
        shortener = Shortener(self.database)
        shortener.delete_url(uuid)
        urls = shortener.get_all_urls()
        emit('add_urls', urls)
        emit('add_total_urls', {'total': shortener.get_total_urls()})
