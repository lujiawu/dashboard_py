from textual.widgets import Static
from models.types import SystemData

class SystemPanel(Static):
    def update_data(self, data: SystemData):
        cpu_bar = "█" * int(data.cpu // 10) + "░" * int(10 - data.cpu // 10)
        mem_bar = "█" * int(data.memory // 10) + "░" * int(10 - data.memory // 10)
        
        content = (
            f"CPU: {cpu_bar} {data.cpu:.1f}%\n"
            f"MEM: {mem_bar} {data.memory:.1f}%\n"
            f"DISK: {data.disk:.1f}%"
        )
        self.update(content)
    
    def format_text(self, data: SystemData):
        cpu_bar = "█" * int(data.cpu // 10) + "░" * int(10 - data.cpu // 10)
        mem_bar = "█" * int(data.memory // 10) + "░" * int(10 - data.memory // 10)
        
        return (
            f"CPU: {cpu_bar} {data.cpu:.1f}%\n"
            f"MEM: {mem_bar} {data.memory:.1f}%\n"
            f"DISK: {data.disk:.1f}%"
        )