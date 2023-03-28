from typing import Dict
from os import getenv

class ApiAuth:

    def __init__(self) -> None:
        self.__token = getenv('ACCESS_TOKEN')

    def _check_headers(self):
        return 'x-access-token' in self.headers

    def _verify_token(self):
        return self.user_token == self.__token

    def validate(self, headers: Dict):

        self.headers = headers
        self.user_token = self.headers.get('x-access-token')

        if self._check_headers():
            return self._verify_token()
    