import unittest

from app import MIN_ROW_HEIGHT, resize_columns, resize_rows


class LayoutResizeTest(unittest.TestCase):
    def test_keeps_bottom_at_minimum(self):
        self.assertEqual(resize_rows(9, MIN_ROW_HEIGHT, 4), (9, MIN_ROW_HEIGHT))

    def test_moves_height_between_rows(self):
        self.assertEqual(resize_rows(18, 20, 4), (22, 16))

    def test_clamps_column_widths(self):
        self.assertEqual(resize_columns(40, 50, 20, 30, 40), (50, 40))
        self.assertEqual(resize_columns(40, 50, -20, 30, 40), (30, 60))

    def test_preserves_total_width_when_resizing(self):
        left, right = resize_columns(40, 110, 10, 20, 101)
        self.assertEqual((left, right), (49, 101))
        self.assertEqual(left + right, 150)

    def test_dashboard_resize_rows_accepts_single_delta(self):
        import inspect

        from app import DashboardApp

        self.assertEqual(list(inspect.signature(DashboardApp.resize_rows).parameters), ["self", "delta"])


if __name__ == "__main__":
    unittest.main()
