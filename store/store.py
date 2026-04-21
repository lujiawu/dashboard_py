from typing import Callable, List
from models.types import AppState

class Store:
    def __init__(self):
        self.state = AppState()
        self.subscribers: List[Callable] = []

    def subscribe(self, callback: Callable):
        self.subscribers.append(callback)

    def set_state(self, new_state: AppState):
        self.state = new_state
        for cb in self.subscribers:
            cb(self.state)