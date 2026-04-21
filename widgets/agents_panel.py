from textual.widgets import Static
from rich.panel import Panel
from rich.table import Table
from models.types import Agent

class AgentsPanel(Static):
    def update_agents(self, agents: list[Agent]):
        table = Table(show_header=True, header_style="bold")
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="magenta")
        
        for agent in agents:
            status_color = "green" if agent.status == "running" else "yellow" if agent.status == "idle" else "red"
            table.add_row(agent.name, f"[{status_color}]{agent.status}[/]")
        
        self.update(Panel(table, title="Agents", border_style="blue"))