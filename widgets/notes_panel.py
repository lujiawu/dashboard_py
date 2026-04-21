from textual.widgets import Static
from rich.panel import Panel
from rich.text import Text
from models.types import Note

class NotesPanel(Static):
    def update_notes(self, notes: list[Note]):
        if not notes:
            content = "No notes yet"
        else:
            content_parts = []
            for note in notes[:5]:  # 只显示最近5条
                content_parts.append(f"• {note.content}")
            content = "\n".join(content_parts)
        
        self.update(Panel(content, title="Notes", border_style="yellow"))