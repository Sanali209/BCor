import unittest

from src.common.ui.theming.provider import DynamicIconProvider, QSSProcessor


class TestQSSProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = QSSProcessor()

    def test_basic_variable_substitution(self):
        template = "QWidget { color: @text; }"
        colors = {"text": "#ffffff"}
        result = self.processor.process(template, colors)
        self.assertEqual(result, "QWidget { color: #ffffff; }")

    def test_multiple_variables(self):
        template = "QWidget { color: @text; background-color: @bg; }"
        colors = {"text": "#ffffff", "bg": "#000000"}
        result = self.processor.process(template, colors)
        self.assertEqual(result, "QWidget { color: #ffffff; background-color: #000000; }")

    def test_nested_variables(self):
        template = "QWidget { color: @link; }"
        colors = {"primary": "#007bff", "link": "@primary"}
        # QSSProcessor should resolve @link -> @primary -> #007bff
        result = self.processor.process(template, colors)
        self.assertEqual(result, "QWidget { color: #007bff; }")

    def test_lighten_function(self):
        template = "QPushButton { background-color: lighten(#808080, 20%); }"
        result = self.processor.process(template, {})
        # #808080 is (128, 128, 128). Lighten by 20% (of 255) -> +51 -> (179, 179, 179) -> #b3b3b3
        self.assertEqual(result.lower(), "qpushbutton { background-color: #b3b3b3; }")

    def test_darken_function(self):
        template = "QPushButton { background-color: darken(#808080, 20%); }"
        result = self.processor.process(template, {})
        # #808080 - 20% -> 128 - 51 = 77 -> #4d4d4d
        self.assertEqual(result.lower(), "qpushbutton { background-color: #4d4d4d; }")

    def test_alpha_function(self):
        template = "QFrame { background-color: alpha(#ff0000, 0.5); }"
        result = self.processor.process(template, {})
        # #ff0000 with 0.5 alpha -> rgba(255, 0, 0, 0.5) or #80ff0000 (Qt format)
        # 0.5 * 255 = 127.5 -> round to 128 (half to even)
        self.assertEqual(result.lower(), "qframe { background-color: rgba(255, 0, 0, 128); }")

    def test_combined_vars_and_functions(self):
        template = "QPushButton { background-color: darken(@primary, 10%); }"
        colors = {"primary": "#ff0000"}
        result = self.processor.process(template, colors)
        # #ff0000 (255, 0, 0) -> darken 10% (25) -> (230, 0, 0) -> #e60000
        self.assertEqual(result.lower(), "qpushbutton { background-color: #e60000; }")

    def test_overlapping_variable_names(self):
        template = "QPushButton { background-color: @btn; } QPushButton:hover { background-color: @btn-hover; }"
        colors = {"btn": "#111111", "btn-hover": "#222222"}
        result = self.processor.process(template, colors)
        # Should NOT be "QPushButton { background-color: #111111; } QPushButton:hover { background-color: #111111-hover; }"
        self.assertIn("background-color: #111111;", result)
        self.assertIn("background-color: #222222;", result)
        self.assertNotIn("#111111-hover", result)


class TestDynamicIconProvider(unittest.TestCase):
    def setUp(self):
        self.provider = DynamicIconProvider()

    def test_svg_color_substitution(self):
        svg_template = '<svg><path stroke="@primary" fill="@secondary" /></svg>'
        colors = {"primary": "#ff0000", "secondary": "#00ff00"}
        result = self.provider.colorize_svg(svg_template, colors)
        self.assertIn('stroke="#ff0000"', result)
        self.assertIn('fill="#00ff00"', result)

    def test_svg_current_color_replacement(self):
        # Support for standard 'currentColor' pattern
        svg_template = '<svg><path stroke="currentColor" /></svg>'
        colors = {"accent": "#0000ff"}
        # Map currentColor to accent by default
        result = self.provider.colorize_svg(svg_template, colors, color_role="accent")
        self.assertIn('stroke="#0000ff"', result)


if __name__ == "__main__":
    unittest.main()
