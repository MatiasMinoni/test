from abc import ABC, abstractmethod
from app.database.identity import Identity
from typing import Dict

class Database(ABC):

    @abstractmethod
    def create(self, *args) -> bool:
        pass

    @abstractmethod
    def update(self, *args) -> bool:
        pass
    
    @abstractmethod
    def delete(self, *args) -> bool:
        pass
    
    @abstractmethod
    def get_data(self, *args) -> Dict:
        pass