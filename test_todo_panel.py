import unittest
from datetime import date, datetime, timedelta, timezone

from models.types import Todo
from widgets.todo_panel import group_todos


_BJ_TZ = timezone(timedelta(hours=8))


def due(day: date) -> int:
    return int(datetime.combine(day, datetime.min.time(), tzinfo=_BJ_TZ).timestamp() * 1000)


class TodoGroupingTest(unittest.TestCase):
    def test_groups_todos_by_due_date(self):
        today = date(2026, 8, 19)
        todos = [
            Todo("overdue", "过期", due_time=due(today - timedelta(days=1))),
            Todo("today", "今天", due_time=due(today)),
            Todo("tomorrow", "明天", due_time=due(today + timedelta(days=1))),
            Todo("future", "未来", due_time=due(today + timedelta(days=2))),
            Todo("none", "无日期"),
            Todo("invalid", "无效日期", due_time=10**100),
            Todo("text", "文本日期", due_time="invalid"),
        ]

        groups = group_todos(todos, today)

        self.assertEqual(
            [(name, [todo.id for todo in items]) for name, items in groups],
            [
                ("overdue", ["overdue"]),
                ("today", ["today"]),
                ("tomorrow", ["tomorrow"]),
                ("future", ["future"]),
                ("no_due", ["none", "text", "invalid"]),
            ],
        )


if __name__ == "__main__":
    unittest.main()
