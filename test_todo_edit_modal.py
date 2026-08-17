import unittest
from datetime import datetime, timezone, timedelta

from widgets.todo_edit_modal import TodoEditModal, _PRIORITY_OPTIONS
from textual.widgets import Select

_BJ = timezone(timedelta(hours=8))


class TodoEditModalTest(unittest.TestCase):
    def test_parse_due_empty(self):
        self.assertIsNone(TodoEditModal._parse_due(""))

    def test_parse_due_offsets(self):
        d0 = TodoEditModal._parse_due("+0")
        d1 = TodoEditModal._parse_due("+1")
        d2 = TodoEditModal._parse_due("+2")
        end_of_today = datetime.now(tz=_BJ).replace(hour=23, minute=59, second=59, microsecond=0)
        self.assertEqual(d0, int(end_of_today.timestamp() * 1000))
        self.assertEqual(d1 - d0, 86_400_000)
        self.assertEqual(d2 - d0, 86_400_000 * 2)

    def test_parse_due_invalid(self):
        with self.assertRaises(ValueError):
            TodoEditModal._parse_due("2026-03-10")

    def test_priority_options_are_value_second(self):
        select = Select(_PRIORITY_OPTIONS, value=20)
        self.assertTrue({10, 20, 30, 40} <= select._legal_values)


if __name__ == "__main__":
    unittest.main()