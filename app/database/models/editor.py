from app.database.databases.mongodb import MongoDB
from app.database.identity import Identity
from app.database.models.account import Account


class Editor(Account):
    def __init__(self, database: MongoDB) -> None:
        super().__init__(database)

    def get_bots(self, identity: Identity):
         
        data = self.get_data(identity)
        bots = data['bots']
        return bots
