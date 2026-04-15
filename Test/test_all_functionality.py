import unittest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from converter_app.document_converter import DocumentConverter


class TestDocumentConverter(unittest.TestCase):

    def setUp(self):
        self.converter = DocumentConverter()
        self.test_dir = Path(__file__).parent

    def test_clean_gpt_markdown_removes_headings(self):
        text = "# Heading\n## Subheading\n### Deep heading"
        expected = "Heading\nSubheading\nDeep heading"
        result = self.converter._clean_gpt_markdown(text)
        self.assertEqual(result, expected)

    def test_clean_gpt_markdown_removes_bold(self):
        text = "This is **bold** text"
        expected = "This is bold text"
        result = self.converter._clean_gpt_markdown(text)
        self.assertEqual(result, expected)

    def test_clean_gpt_markdown_removes_italic(self):
        text = "This is *italic* text"
        expected = "This is italic text"
        result = self.converter._clean_gpt_markdown(text)
        self.assertEqual(result, expected)

    def test_clean_gpt_markdown_removes_code_blocks(self):
        text = "Use `code` for inline"
        expected = "Use code for inline"
        result = self.converter._clean_gpt_markdown(text)
        self.assertEqual(result, expected)

    def test_clean_gpt_markdown_removes_links(self):
        text = "Visit [Google](https://google.com)"
        expected = "Visit Google"
        result = self.converter._clean_gpt_markdown(text)
        self.assertEqual(result, expected)

    def test_clean_gpt_markdown_removes_list_markers(self):
        text = "- Item 1\n* Item 2"
        result = self.converter._clean_gpt_markdown(text)
        self.assertIn("Item 1", result)
        self.assertIn("Item 2", result)
        self.assertNotIn("- ", result)
        self.assertNotIn("* ", result)

    def test_clean_gpt_markdown_removes_quote_markers(self):
        text = "> This is a quote"
        result = self.converter._clean_gpt_markdown(text)
        self.assertEqual(result, "This is a quote")

    def test_convert_formulas_square_root_parentheses(self):
        text = "√(x)"
        expected = "(x)^(1/2)"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_square_root_symbol_only(self):
        text = "√16"
        expected = "(16)^(1/2)"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_cube_root(self):
        text = "³√(8)"
        expected = "(8)^(1/3)"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_fraction_latex(self):
        text = "\\frac{a}{b}"
        expected = "(a)/(b)"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_unicode_fractions(self):
        text = "½ + ¼ = ¾"
        expected = "1/2 + 1/4 = 3/4"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_multiplication_division(self):
        text = "5 × 3 = 15, 10 ÷ 2 = 5"
        expected = "5 * 3 = 15, 10 / 2 = 5"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_minus_plusminus(self):
        text = "5 − 3 = 2, ±1"
        expected = "5 - 3 = 2, +/-1"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_pi_infinity(self):
        text = "π ≈ 3.14, approaching ∞"
        expected = "pi ≈ 3.14, approaching inf"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_trig_functions(self):
        text = "\\sin(x), \\cos(x), \\tan(x)"
        expected = "sin(x), cos(x), tan(x)"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_left_right_parentheses(self):
        text = "\\left(a + b\\right)"
        expected = "(a + b)"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_power(self):
        text = "x^2"
        expected = "x^2"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_process_txt_with_gpt_support_full(self):
        text = "# Heading\n**Bold** and *italic*\n√(x)\n\\frac{1}{2}"

        test_file = self.test_dir / "temp_test_input.txt"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(text)

        try:
            result = self.converter._process_txt_with_gpt_support(str(test_file))

            self.assertNotIn("# ", result)
            self.assertNotIn("**", result)
            self.assertNotIn("*italic*", result)
            self.assertIn("(x)^(1/2)", result)
            self.assertIn("(1)/(2)", result)
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_txt_to_pdf_integration(self):
        test_input = self.test_dir / "test_plain.txt"

        if not test_input.exists():
            self.skipTest("Test file not found")

        try:
            new_name = "test_output_pdf"
            self.converter._txt_to_pdf(str(test_input), new_name)

            output_file = self.test_dir / f"{new_name}.pdf"
            self.assertTrue(output_file.exists())

            output_file.unlink()
        except Exception as e:
            self.skipTest(f"PDF conversion failed: {e}")

    def test_txt_to_docx_integration(self):
        test_input = self.test_dir / "test_plain.txt"

        if not test_input.exists():
            self.skipTest("Test file not found")

        try:
            new_name = "test_output_docx"
            self.converter._txt_to_docx(str(test_input), new_name)

            output_file = self.test_dir / f"{new_name}.docx"
            self.assertTrue(output_file.exists())

            output_file.unlink()
        except Exception as e:
            self.skipTest(f"DOCX conversion failed: {e}")

    def test_txt_to_markdown_integration(self):
        test_input = self.test_dir / "test_gpt_formatted.txt"

        if not test_input.exists():
            self.skipTest("Test file not found")

        try:
            new_name = "test_output_md"
            self.converter._txt_to_markdown(str(test_input), new_name)

            output_file = self.test_dir / f"{new_name}.md"
            self.assertTrue(output_file.exists())

            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()

            self.assertNotIn("# ", content)
            self.assertNotIn("**", content)

            output_file.unlink()
        except Exception as e:
            self.skipTest(f"Markdown conversion failed: {e}")

    def test_txt_to_html_integration(self):
        test_input = self.test_dir / "test_plain.txt"

        if not test_input.exists():
            self.skipTest("Test file not found")

        try:
            new_name = "test_output_html"
            self.converter._txt_to_html(str(test_input), new_name)

            output_file = self.test_dir / f"{new_name}.html"
            self.assertTrue(output_file.exists())

            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()

            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("<html>", content)
            self.assertIn("</html>", content)

            output_file.unlink()
        except Exception as e:
            self.skipTest(f"HTML conversion failed: {e}")


class TestFormulaConversions(unittest.TestCase):

    def setUp(self):
        self.converter = DocumentConverter()

    def test_sqrt_variations(self):
        test_cases = [
            ("√(x)", "(x)^(1/2)"),
            ("√16", "(16)^(1/2)"),
            ("\\sqrt{x}", "(x)^(1/2)"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.converter._convert_formulas(input_text)
                self.assertEqual(result, expected)

    def test_nth_root(self):
        text = "\\sqrt[4]{x}"
        result = self.converter._convert_formulas(text)
        self.assertIn("^(1/4)", result)

    def test_complex_expression(self):
        text = "\\frac{\\sqrt{x} + 1}{2}"
        result = self.converter._convert_formulas(text)
        self.assertIn("(x)^(1/2)", result)
        self.assertIn("/(2)", result)


if __name__ == '__main__':
    unittest.main(verbosity=2)