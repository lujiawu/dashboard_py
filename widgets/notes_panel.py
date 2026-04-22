from textual.widgets import Static
from models.types import Note

class NotesPanel(Static):
    def update_notes(self, notes: list[Note]):
        if not notes:
            content = "No notes yet"
        else:
            content = "\n".join([f"• {note.content}" for note in notes])
        
        self.update(content)
    
    def format_text(self, notes: list[Note]):
        if not notes:
            return "No notes yet"
        else:
            return "\n".join([f"• {note.content}" for note in notes])