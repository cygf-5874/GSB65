"""colfmt 的既有用例（起点全绿）。

这些用例只覆盖 ASCII、单行单元格的公开行为；不触碰任何内部结构。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from colfmt import display_width, render_table, wrap_text  # noqa: E402


class WidthTest(unittest.TestCase):
    def test_display_width_ascii(self):
        self.assertEqual(display_width("abc"), 3)
        self.assertEqual(display_width("#-+|"), 4)
        self.assertEqual(display_width("a b"), 3)

    def test_display_width_empty_and_space(self):
        self.assertEqual(display_width(""), 0)
        self.assertEqual(display_width(" "), 1)
        self.assertEqual(display_width("   "), 3)


class RenderTest(unittest.TestCase):
    def test_render_no_header(self):
        self.assertEqual(
            render_table([["a", "bb"]]),
            "+---+----+\n| a | bb |\n+---+----+",
        )

    def test_render_with_header(self):
        self.assertEqual(
            render_table([["a", "bb"]], headers=["h", "i"]),
            "+---+----+\n| h | i  |\n+---+----+\n| a | bb |\n+---+----+",
        )

    def test_align_left_default(self):
        text = render_table([["a", "bb"], ["ccc", "d"]], headers=["h", "i"])
        self.assertEqual(
            text,
            "+-----+----+\n"
            "| h   | i  |\n"
            "+-----+----+\n"
            "| a   | bb |\n"
            "+-----+----+\n"
            "| ccc | d  |\n"
            "+-----+----+",
        )

    def test_align_right(self):
        text = render_table([["a", "bb"], ["ccc", "d"]], headers=["h", "i"], align="right")
        self.assertEqual(
            text,
            "+-----+----+\n"
            "|   h |  i |\n"
            "+-----+----+\n"
            "|   a | bb |\n"
            "+-----+----+\n"
            "| ccc |  d |\n"
            "+-----+----+",
        )

    def test_align_center_residual(self):
        self.assertEqual(
            render_table([["ab"]], widths=[5], align="center"),
            "+-------+\n|  ab   |\n+-------+",
        )

    def test_align_per_column(self):
        self.assertEqual(
            render_table([["a", "b"], ["cc", "dd"]], align=["left", "right"]),
            "+----+----+\n| a  |  b |\n+----+----+\n| cc | dd |\n+----+----+",
        )

    def test_single_column(self):
        self.assertEqual(
            render_table([["x"], ["yy"]], headers=["id"]),
            "+----+\n| id |\n+----+\n| x  |\n+----+\n| yy |\n+----+",
        )

    def test_empty_table(self):
        self.assertEqual(render_table([]), "")
        self.assertEqual(render_table([], headers=[]), "")

    def test_header_only(self):
        self.assertEqual(
            render_table([], headers=["a", "b"]),
            "+---+---+\n| a | b |\n+---+---+",
        )

    def test_empty_string_cells(self):
        self.assertEqual(
            render_table([["", "z"], ["x", ""]]),
            "+---+---+\n|   | z |\n+---+---+\n| x |   |\n+---+---+",
        )

    def test_explicit_widths_pad(self):
        self.assertEqual(
            render_table([["a"]], widths=[4]),
            "+------+\n| a    |\n+------+",
        )


class WrapTest(unittest.TestCase):
    def test_wrap_text_and_no_trailing_space(self):
        self.assertEqual(wrap_text("abc", 5), ["abc"])
        for text in (
            render_table([["a", "bb"], ["ccc", "d"]], headers=["h", "i"]),
            render_table([["only"]]),
            render_table([], headers=["a", "b"]),
        ):
            for line in text.split("\n"):
                self.assertFalse(line.endswith(" "), "行尾出现空格：%r" % (line,))


if __name__ == "__main__":
    unittest.main()
