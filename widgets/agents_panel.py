from textual.widgets import Static
from models.types import Agent

class AgentsPanel(Static):
    def update_agents(self, agents: list[Agent]):
        agent_lines = []
        for agent in agents:
            status_map = {
                "running": "[RUNNING]",
                "idle": "[IDLE]",
                "stopped": "[STOPPED]"
            }
            status_text = status_map.get(agent.status, "[UNKNOWN]")
            agent_lines.append(f"{agent.name:<15} {status_text}")
        
        content = "\n".join(agent_lines) if agent_lines else "No agents running"
        self.update(content)
    
    def format_text(self, agents: list[Agent]):
        agent_lines = []
        for agent in agents:
            status_map = {
                "running": "[RUNNING]",
                "idle": "[IDLE]", 
                "stopped": "[STOPPED]"
            }
            status_text = status_map.get(agent.status, "[UNKNOWN]")
            agent_lines.append(f"{agent.name:<15} {status_text}")
        
        return "\n".join(agent_lines) if agent_lines else "No agents running"