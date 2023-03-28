"""
Author: Scr44gr

"""
from core.speakers.facebook.sfybook.auth import Auth
from core.speakers.facebook.sfybook.poster import Poster
from core.speakers.facebook.sfybook.comments import Comments
from core.speakers.facebook.sfybook import urls


class Client(Poster, Comments):

    def __init__(self, **kwargs):

        self.auth = Auth()
        if kwargs.get('session'):
            self.auth.session = kwargs.get('session')
        Poster.__init__(self, self.auth.session)
        Comments.__init__(self, self.auth.session)

class SfyNode(Client):
    """
        Client Node.
    """
    def __init__(self, session, **kwargs):
        super().__init__(session=session)
        self.url_id = kwargs.get('url_id')
        self.name = kwargs.get('name')