from app.database.models.admin import Admin
from app.database.models.editor import Editor
from app.database.identity import Identity

class AccountManager:

    def get_user(self, identity: Identity):

        if identity.role == 'admin':
            return Admin
        elif identity.role == 'editor':
            return Editor