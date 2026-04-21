from textual.widgets import Static
from rich.panel import Panel
from models.types import SystemData

class SystemPanel(Static):
    def update_data(self, data: SystemData):
        content = f"""
CPU: {data.cpu:.1f}%
MEM: {data.memory:.1f}%
DISK: {data.disk:.1f}%
"""
        self.update(Panel(content, title="System", border_style="green"))