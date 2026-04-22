from textual.widgets import Static
from models.types import Agent, AgentSession
from datetime import datetime, timezone
import time


class AgentsPanel(Static):
    def update_sessions(self, sessions: list[AgentSession]):
        """Update panel with session info"""
        content = self.format_text(sessions)
        self.update(content)

    def update_agents(self, agents: list[Agent]):
        """Original method for updating demo agents"""
        agent_lines = []
        for agent in agents:
            status_text = agent.status
            agent_lines.append(f"{agent.name:<15} {status_text}")
        
        content = "\n".join(agent_lines) if agent_lines else "No agents running"
        self.update(content)
    
    def format_text(self, sessions: list[AgentSession]):
        """Format session data for display with filtering and sorting"""
        if not sessions:
            return "No active sessions"
            
        current_time = datetime.now(timezone.utc)
        filtered_sessions = []
        
        for session in sessions:
            try:
                # Parse update time from ISO format string like "2026-04-22T09:35:53.040Z"
                # If updateTime ends with 'Z', replace with '+00:00' for parsing
                update_time_str = session.update_time
                if update_time_str and update_time_str.endswith('Z'):
                    update_time_str = update_time_str[:-1] + '+00:00'
                elif not update_time_str:  # Handle empty updateTime
                    continue  # Skip sessions without update time
                
                update_time = datetime.fromisoformat(update_time_str)
                
                # Calculate difference in hours
                time_diff = abs((current_time - update_time).total_seconds()) / 3600
                
                # Only include sessions updated within the last 24 hours
                # Changed from 1 hour to 24 hours to show more sessions
                if time_diff <= 1:
                    filtered_sessions.append((session, update_time))
                    
            except ValueError:
                # Skip sessions with invalid timestamp format
                continue
        
        # Sort by update time (descending - most recent first)
        filtered_sessions.sort(key=lambda x: x[1], reverse=True)
        
        # Format the session lines
        session_lines = []
        for session, _ in filtered_sessions:
            # Defense: handle empty status
            status_val = session.status.strip().lower() if session.status else "unknown"
            if not status_val:  # If stripped status is empty
                status_val = "unknown"
            
            # Format status with mapping
           
            status_text = status_val
            
            # Format directory (truncate if too long)
            directory = session.directory if session.directory else "Unknown"
            if len(directory) > 15:
                directory = directory[:12] + "..."
                
            # Format title (use the entire remaining space)
            title = session.title 
            if len(title) > 50:  # Reasonable default for remaining space
                title = title[:47] + "..."
                
            # Format as: [STATUS] directory | title
            formatted_line = f"{status_text:<10} {directory:<15} | {title}"
            session_lines.append(formatted_line)
        
        return "\n".join(session_lines) if session_lines else "No sessions updated in the past 24 hours"
    
    def format_demo_text(self, agents: list[Agent]):
        """Original method for demo agents formatting"""
        agent_lines = []
        for agent in agents:
            status_text = agent.status
            agent_lines.append(f"{agent.name:<15} {status_text}")
        
        return "\n".join(agent_lines) if agent_lines else "No agents running"