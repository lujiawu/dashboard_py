from dataclasses import dataclass, field
from typing import List

@dataclass
class SystemData:
    cpu: float = 0.0
    memory: float = 0.0
    disk: float = 0.0

@dataclass
class Agent:
    name: str
    status: str

@dataclass
class Todo:
    id: str
    content: str
    completed: bool = False

@dataclass
class Note:
    id: str
    content: str

@dataclass
class AppState:
    system: SystemData = field(default_factory=SystemData)
    agents: List[Agent] = field(default_factory=list)
    todos: List[Todo] = field(default_factory=list)
    notes: List[Note] = field(default_factory=list)