from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RankedItem:
    rank: int
    label: str
    count: int
    max_count: int = 0

    @property
    def percentage(self) -> float:
        if self.max_count == 0:
            return 0.0
        return (self.count / self.max_count) * 100

    def __hash__(self):
        return id(self)


@dataclass
class LogPattern:
    pattern: str
    percentage: float
    count: int
    color: str = "white"

    def __hash__(self):
        return id(self)


@dataclass
class LogLevelStats:
    fatal: int = 0
    error: int = 0
    warn: int = 0
    info: int = 0
    debug: int = 0
    trace: int = 0
    total: int = 0


@dataclass
class LogEntry:
    time: str
    level: str
    host: str
    service: str
    message: str

    def __hash__(self):
        return id(self)


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
class AgentSession:
    id: str
    title: str
    directory: str
    status: str
    start_time: str = ""
    update_time: str = ""
    error: Optional[str] = None
    agent: str = ""
    model_id: str = ""
    host: str = "local"

    def __hash__(self):
        return id(self)


@dataclass
class Agent:
    name: str
    status: str

@dataclass
class Todo:
    id: str
    subject: str
    completed: bool = False
    priority: int = 0
    due_time: int = 0
    created_time: int = 0

    def __hash__(self):
        return id(self)

@dataclass
class ChatConversation:
    conversation_id: str
    title: str
    unread_count: int
    is_single_chat: bool = False

    def __hash__(self):
        return id(self)


@dataclass
class CalendarEvent:
    event_id: str
    title: str
    start_time: int
    end_time: int

    def __hash__(self):
        return id(self)


@dataclass
class GoalProgress:
    name: str
    used: float
    goal: float
    unit: str = ""
    disabled: bool = False
    icon: str = "◆"

    @property
    def percentage(self) -> float:
        if self.goal == 0:
            return 0.0
        return min(100.0, (self.used / self.goal) * 100)

    @property
    def is_warning(self) -> bool:
        return self.disabled or self.percentage >= 90

    def __hash__(self):
        return id(self)


@dataclass
class AppState:
    system: SystemData = field(default_factory=SystemData)
    sessions: List[AgentSession] = field(default_factory=list)
    todos: List[Todo] = field(default_factory=list)
