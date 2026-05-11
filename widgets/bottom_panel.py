from pathlib import Path
from textual.widgets import TextArea

SNIPPET_FILE = Path.home() / ".config" / "dashboard" / "snippets.md"


class BottomPanel(TextArea):
    def on_mount(self):
        self.load_text("")
        self.border_title = "Snippet"
        self.tab_behavior = "indent"
        self._load_file()

    def _load_file(self):
        SNIPPET_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not SNIPPET_FILE.exists():
            SNIPPET_FILE.write_text("", encoding="utf-8")
        else:
            content = SNIPPET_FILE.read_text(encoding="utf-8")
            if content:
                self.load_text(content)

    def on_blur(self):
        SNIPPET_FILE.write_text(self.text, encoding="utf-8")
