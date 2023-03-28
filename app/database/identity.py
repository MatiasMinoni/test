from dataclasses import dataclass
from typing import Dict

ID = 0

@dataclass
class Identity:

    type: str
    id: str
    value: str

    def __init__(self, type, id, value, role='editor') -> None:
        self.type = type
        self.id = id
        self.value = value
        self.role = role

    def _to_dict(self) -> Dict:

        return {self.type:self.value}
    
    def __call__(self) -> Dict:
        return self._to_dict()