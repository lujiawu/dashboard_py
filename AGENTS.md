# Textual Dashboard - Agent Instructions

## Environment Gotchas

- On Windows PowerShell: Use `python app.py`, NOT `python3 app.py` (python3 is not available)

## Textual Version Quirks

- **Major upgrade**: textual `0.58.0` → `8.2.4` (8 major versions ahead)
- **ListView behavior changed**: `clear()`+`append()` causes `DuplicateIds` exception in 8.x
  - Workaround: Use `query("ListItem").remove()` + `mount()` (no explicit IDs)
- **Dataclass hashes**: Models used in ListView must implement `__hash__` to avoid refresh conflicts:
  ```python
  @dataclass
  class Todo:
      # ...
      def __hash__(self):
          return id(self)  # Use object identity
  ```

## Architecture

- **Entry**: `app.py` (state-driven dashboard with polling update loop)
- **State**: `store/store.py` (simple pub/sub pattern)
- **Layout**: Grid in `styles/app.tcss`
- **Components**: All in `widgets/`, each updates state-reactively

## Running & Dev Commands

- `python app.py` - Start the dashboard
- Hotkeys: `t` toggle first todo, `q` quit