from dataclasses import dataclass, field
from typing import List

@dataclass
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float

    def __hash__(self):
        return id(self)


@dataclass
class SystemData:
    cpu: float = 0.0
    cpu_count: int = 0
    memory: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    disk: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    network_upload_kb: float = 0.0
    network_download_kb: float = 0.0
    process_count: int = 0
    boot_time: float = 0.0
    top_processes: list = field(default_factory=list)  # top N 进程信息

@dataclass
class Agent:
    name: str
    status: str

@dataclass
class Todo:
    id: str
    content: str
    completed: bool = False
    
    def __hash__(self):
        return id(self)

@dataclass
class Note:
    id: str
    content: str

    def __hash__(self):
        return id(self)

@dataclass
class AppState:
    system: SystemData = field(default_factory=SystemData)
    agents: List[Agent] = field(default_factory=list)
    todos: List[Todo] = field(default_factory=list)
    notes: List[Note] = field(default_factory=list)