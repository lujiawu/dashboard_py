from pathlib import Path
from textual.widgets import TextArea
from config import cfg

SNIPPET_FILE = Path(cfg["snippet_file"]).expanduser()


class BottomPanel(TextArea):
    def on_mount(self):
        self.load_text("")
        self.border_title = "Snippet"
        self.border_subtitle = "Auto-saved"
        self.tab_behavior = "indent"
        self._load_file()

    def _load_file(self):
        SNIPPET_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not SNIPPET_FILE.exists():
            SNIPPET_FILE.write_text("", encoding="utf-8")
            self.load_text("[dim]⌨  粘贴临时片段...[/dim]")
        else:
            content = SNIPPET_FILE.read_text(encoding="utf-8")
            if content:
                self.load_text(content)
            else:
                self.load_text("[dim]⌨  粘贴临时片段...[/dim]")

    def on_blur(self):
        SNIPPET_FILE.write_text(self.text, encoding="utf-8")
