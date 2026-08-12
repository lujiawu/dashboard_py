import unittest

from app import MIN_ROW_HEIGHT, resize_rows


class LayoutResizeTest(unittest.TestCase):
    def test_top_divider_keeps_middle_at_minimum(self):
        self.assertEqual(resize_rows(9, 5, 20, "top-divider", 4), (9, 5))

    def test_middle_divider_keeps_bottom_visible(self):
        self.assertEqual(resize_rows(9, 18, MIN_ROW_HEIGHT, "middle-divider", 4), (18, MIN_ROW_HEIGHT))


if __name__ == "__main__":
    unittest.main()
