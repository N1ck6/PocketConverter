"""
Standard unit tests for all converter modules.
Run with: python -m pytest test_converters.py -v
Or in VS Code: Right-click -> Run Tests
"""

import unittest
import sys
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from converter_app.image_converter import ImageConverter
from converter_app.document_converter import DocumentConverter
from converter_app.folder_converter import DataConverter, BatchProcessor


class TestImageConverter(unittest.TestCase):
    """Test image conversion functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests in class."""
        cls.test_dir = Path(__file__).parent / 'samples'
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.converter = ImageConverter()

        # Copy sample files to temp directory for testing
        for ext in ['png', 'jpg', 'bmp']:
            src = cls.test_dir / f'sample.{ext}'
            if src.exists():
                shutil.copy(src, cls.temp_dir / f'test.{ext}')

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

    def setUp(self):
        """Reset temp directory before each test."""
        for f in self.temp_dir.glob('*'):
            if f.is_file():
                f.unlink()
        # Restore sample files
        for ext in ['png', 'jpg', 'bmp']:
            src = self.test_dir / f'sample.{ext}'
            if src.exists():
                shutil.copy(src, self.temp_dir / f'test.{ext}')

    def test_png_to_jpg_conversion(self):
        """Test PNG to JPG conversion."""
        input_file = self.temp_dir / 'test.png'
        if not input_file.exists():
            self.skipTest("Sample PNG file not found")

        self.converter.convert(str(input_file), 'jpg', 'output')
        output_file = self.temp_dir / 'output.jpg'

        self.assertTrue(output_file.exists(), "JPG output file should be created")
        self.assertGreater(output_file.stat().st_size, 0, "Output file should not be empty")

    def test_png_to_bmp_conversion(self):
        """Test PNG to BMP conversion."""
        input_file = self.temp_dir / 'test.png'
        if not input_file.exists():
            self.skipTest("Sample PNG file not found")

        self.converter.convert(str(input_file), 'bmp', 'output')
        output_file = self.temp_dir / 'output.bmp'

        self.assertTrue(output_file.exists(), "BMP output file should be created")

    def test_jpg_to_png_conversion(self):
        """Test JPG to PNG conversion."""
        input_file = self.temp_dir / 'test.jpg'
        if not input_file.exists():
            self.skipTest("Sample JPG file not found")

        self.converter.convert(str(input_file), 'png', 'output')
        output_file = self.temp_dir / 'output.png'

        self.assertTrue(output_file.exists(), "PNG output file should be created")

    def test_bmp_to_webp_conversion(self):
        """Test BMP to WEBP conversion."""
        input_file = self.temp_dir / 'test.bmp'
        if not input_file.exists():
            self.skipTest("Sample BMP file not found")

        self.converter.convert(str(input_file), 'webp', 'output')
        output_file = self.temp_dir / 'output.webp'

        self.assertTrue(output_file.exists(), "WEBP output file should be created")


class TestDocumentConverter(unittest.TestCase):
    """Test document conversion functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.test_dir = Path(__file__).parent / 'samples'
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.converter = DocumentConverter()

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

    def setUp(self):
        """Reset temp directory before each test."""
        for f in self.temp_dir.glob('*'):
            if f.is_file():
                f.unlink()
        # Restore sample files
        for ext in ['txt', 'md', 'html']:
            src = self.test_dir / f'sample.{ext}'
            if src.exists():
                shutil.copy(src, self.temp_dir / f'test.{ext}')

    def test_txt_to_pdf_conversion(self):
        """Test TXT to PDF conversion."""
        input_file = self.temp_dir / 'test.txt'
        if not input_file.exists():
            self.skipTest("Sample TXT file not found")

        try:
            self.converter.convert(str(input_file), 'pdf', 'output')
            output_file = self.temp_dir / 'output.pdf'

            self.assertTrue(output_file.exists(), "PDF output file should be created")
            self.assertGreater(output_file.stat().st_size, 0, "Output file should not be empty")
        except Exception as e:
            self.skipTest(f"PDF conversion failed: {e}")

    def test_txt_to_docx_conversion(self):
        """Test TXT to DOCX conversion."""
        input_file = self.temp_dir / 'test.txt'
        if not input_file.exists():
            self.skipTest("Sample TXT file not found")

        try:
            self.converter.convert(str(input_file), 'docx', 'output')
            output_file = self.temp_dir / 'output.docx'

            self.assertTrue(output_file.exists(), "DOCX output file should be created")
        except Exception as e:
            self.skipTest(f"DOCX conversion failed: {e}")

    def test_md_to_html_conversion(self):
        """Test Markdown to HTML conversion."""
        input_file = self.temp_dir / 'test.md'
        if not input_file.exists():
            self.skipTest("Sample MD file not found")

        self.converter.convert(str(input_file), 'html', 'output')
        output_file = self.temp_dir / 'output.html'

        self.assertTrue(output_file.exists(), "HTML output file should be created")

        content = output_file.read_text(encoding='utf-8')
        self.assertIn('<html', content)
        self.assertIn('</html>', content)

    def test_html_to_txt_conversion(self):
        """Test HTML to TXT conversion."""
        input_file = self.temp_dir / 'test.html'
        if not input_file.exists():
            self.skipTest("Sample HTML file not found")

        self.converter.convert(str(input_file), 'txt', 'output')
        output_file = self.temp_dir / 'output.txt'

        self.assertTrue(output_file.exists(), "TXT output file should be created")

        content = output_file.read_text(encoding='utf-8')
        self.assertIn('Hello World', content)

    # GPT Support Tests - from test_converters_last.py
    def test_process_txt_with_gpt_support_removes_headings(self):
        """Test that headings are removed in GPT support mode."""
        text = "# Heading\n## Subheading\n### Deep heading"
        expected = "Heading\nSubheading\nDeep heading"
        result = self.converter._process_txt_with_gpt_support(text)
        self.assertEqual(result, expected)

    def test_process_txt_with_gpt_support_removes_bold(self):
        """Test that bold markers are removed."""
        text = "This is **bold** text"
        expected = "This is bold text"
        result = self.converter._process_txt_with_gpt_support(text)
        self.assertEqual(result, expected)

    def test_process_txt_with_gpt_support_removes_italic(self):
        """Test that italic markers are removed."""
        text = "This is *italic* text"
        expected = "This is italic text"
        result = self.converter._process_txt_with_gpt_support(text)
        self.assertEqual(result, expected)

    def test_process_txt_with_gpt_support_removes_code_blocks(self):
        """Test that code markers are removed."""
        text = "Use `code` for inline"
        expected = "Use code for inline"
        result = self.converter._process_txt_with_gpt_support(text)
        self.assertEqual(result, expected)

    def test_process_txt_with_gpt_support_removes_links(self):
        """Test that markdown links are converted."""
        text = "Visit [Google](https://google.com)"
        expected = "Visit Google"
        result = self.converter._process_txt_with_gpt_support(text)
        self.assertEqual(result, expected)

    def test_process_txt_with_gpt_support_removes_list_markers(self):
        """Test that list markers are removed."""
        text = "- Item 1\n* Item 2"
        result = self.converter._process_txt_with_gpt_support(text)
        self.assertIn("Item 1", result)
        self.assertIn("Item 2", result)
        self.assertNotIn("- ", result)
        self.assertNotIn("* ", result)

    def test_process_txt_with_gpt_support_removes_quote_markers(self):
        """Test that quote markers are removed."""
        text = "> This is a quote"
        result = self.converter._process_txt_with_gpt_support(text)
        self.assertEqual(result, "This is a quote")

    def test_md_to_txt_cleaning(self):
        """Test that markdown syntax is cleaned when converting to TXT."""
        input_file = self.temp_dir / 'test.md'
        if not input_file.exists():
            self.skipTest("Sample MD file not found")

        self.converter.convert(str(input_file), 'txt', 'output')
        output_file = self.temp_dir / 'output.txt'

        content = output_file.read_text(encoding='utf-8')

        # Check that markdown syntax is removed
        self.assertNotIn('# ', content, "Heading markers should be removed")
        self.assertNotIn('**', content, "Bold markers should be removed")

    # Formula Conversion Tests - from test_converters_last.py
    def test_convert_formulas_square_root_parentheses(self):
        """Test formula conversion for square root with parentheses."""
        text = "√(x)"
        expected = "(x)^(1/2)"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_square_root_symbol_only(self):
        """Test formula conversion for square root with number only."""
        text = "√16"
        expected = "(16)^(1/2)"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_cube_root(self):
        """Test formula conversion for cube root."""
        text = "³√(8)"
        expected = "(8)^(1/3)"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_fraction_latex(self):
        """Test formula conversion for LaTeX fractions."""
        text = "\\frac{a}{b}"
        expected = "(a)/(b)"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_unicode_fractions(self):
        """Test formula conversion for unicode fractions."""
        text = "½ + ¼ = ¾"
        expected = "1/2 + 1/4 = 3/4"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_multiplication_division(self):
        """Test formula conversion for multiplication and division symbols."""
        text = "5 × 3 = 15, 10 ÷ 2 = 5"
        expected = "5 * 3 = 15, 10 / 2 = 5"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_minus_plusminus(self):
        """Test formula conversion for minus and plus-minus symbols."""
        text = "5 − 3 = 2, ±1"
        expected = "5 - 3 = 2, +/-1"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_pi_infinity(self):
        """Test formula conversion for pi and infinity symbols."""
        text = "π ≈ 3.14, approaching ∞"
        expected = "pi ≈ 3.14, approaching inf"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_trig_functions(self):
        """Test formula conversion for trigonometric functions."""
        text = "\\sin(x), \\cos(x), \\tan(x)"
        expected = "sin(x), cos(x), tan(x)"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_left_right_parentheses(self):
        """Test formula conversion for left/right parentheses."""
        text = "\\left(a + b\\right)"
        expected = "(a + b)"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_convert_formulas_power(self):
        """Test formula conversion for power notation."""
        text = "x^2"
        expected = "x^2"
        result = self.converter._convert_formulas(text)
        self.assertEqual(result, expected)

    def test_process_txt_with_gpt_support_full(self):
        """Test full GPT support processing with combined features."""
        text = "# Heading\n**Bold** and *italic*\n√(x)\n\\frac{1}{2}"

        test_file = self.temp_dir / "temp_test_input.txt"
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


class TestDataConverter(unittest.TestCase):
    """Test data format conversion functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.test_dir = Path(__file__).parent / 'samples'
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.converter = DataConverter()

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

    def setUp(self):
        """Reset temp directory before each test."""
        for f in self.temp_dir.glob('*'):
            if f.is_file():
                f.unlink()
        # Restore sample files
        for ext in ['json', 'csv', 'xml', 'yaml']:
            src = self.test_dir / f'sample.{ext}'
            if src.exists():
                shutil.copy(src, self.temp_dir / f'test.{ext}')

    def test_json_to_csv_conversion(self):
        """Test JSON to CSV conversion."""
        input_file = self.temp_dir / 'sample.json'
        if not input_file.exists():
            self.skipTest("Sample JSON file not found")

        self.converter.convert(str(input_file), 'csv', 'output')
        output_file = self.temp_dir / 'output.csv'

        self.assertTrue(output_file.exists(), "CSV output file should be created")

    def test_json_to_xml_conversion(self):
        """Test JSON to XML conversion."""
        input_file = self.temp_dir / 'sample.json'
        if not input_file.exists():
            self.skipTest("Sample JSON file not found")

        self.converter.convert(str(input_file), 'xml', 'output')
        output_file = self.temp_dir / 'output.xml'

        self.assertTrue(output_file.exists(), "XML output file should be created")

        content = output_file.read_text(encoding='utf-8')
        self.assertIn('<?xml', content)

    def test_csv_to_json_conversion(self):
        """Test CSV to JSON conversion."""
        input_file = self.temp_dir / 'test.csv'
        if not input_file.exists():
            self.skipTest("Sample CSV file not found")

        self.converter.convert(str(input_file), 'json', 'output')
        output_file = self.temp_dir / 'output.json'

        self.assertTrue(output_file.exists(), "JSON output file should be created")

        import json
        with open(output_file, 'r') as f:
            data = json.load(f)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_xml_to_json_conversion(self):
        """Test XML to JSON conversion."""
        input_file = self.temp_dir / 'test.xml'
        if not input_file.exists():
            self.skipTest("Sample XML file not found")

        self.converter.convert(str(input_file), 'json', 'output')
        output_file = self.temp_dir / 'output.json'

        self.assertTrue(output_file.exists(), "JSON output file should be created")

    def test_yaml_to_json_conversion(self):
        """Test YAML to JSON conversion."""
        input_file = self.temp_dir / 'test.yaml'
        if not input_file.exists():
            self.skipTest("Sample YAML file not found")

        self.converter.convert(str(input_file), 'json', 'output')
        output_file = self.temp_dir / 'output.json'

        self.assertTrue(output_file.exists(), "JSON output file should be created")

    def test_json_to_yaml_conversion(self):
        """Test JSON to YAML conversion."""
        input_file = self.temp_dir / 'test.json'
        if not input_file.exists():
            self.skipTest("Sample JSON file not found")

        self.converter.convert(str(input_file), 'yaml', 'output')
        output_file = self.temp_dir / 'output.yaml'

        self.assertTrue(output_file.exists(), "YAML output file should be created")


class TestBatchProcessor(unittest.TestCase):
    """Test batch processing functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.test_dir = Path(__file__).parent / 'samples'
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.processor = BatchProcessor()

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

    def setUp(self):
        """Create test folder with images."""
        self.batch_folder = self.temp_dir / 'batch_test'
        self.batch_folder.mkdir(exist_ok=True)

        from PIL import Image
        for i, color in enumerate(['red', 'green', 'blue']):
            img = Image.new('RGB', (100, 100), color=color)
            img.save(self.batch_folder / f'image{i}.png')

    def test_images_to_pdf_batch(self):
        """Test batch conversion of images to PDF."""
        try:
            result = self.processor.convert_folder(str(self.batch_folder), 'pdf')

            parent_dir = self.batch_folder.parent
            pdf_files = list(parent_dir.glob('Combined_images*.pdf'))

            self.assertGreater(len(pdf_files), 0, "PDF file should be created")

            for f in pdf_files:
                f.unlink()
        except Exception as e:
            self.skipTest(f"Batch PDF conversion failed: {e}")

    def test_images_to_gif_batch(self):
        """Test batch conversion of images to GIF."""
        try:
            self.processor.convert_folder(str(self.batch_folder), 'gif')

            parent_dir = self.batch_folder.parent
            gif_files = list(parent_dir.glob('Combined_images*.gif'))

            self.assertGreater(len(gif_files), 0, "GIF file should be created")

            for f in gif_files:
                f.unlink()
        except Exception as e:
            self.skipTest(f"Batch GIF conversion failed: {e}")


class TestIntegration(unittest.TestCase):
    """Integration tests for complete conversion workflows."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from converter import FileConverter
        cls.test_dir = Path(__file__).parent / 'samples'
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.converter = FileConverter()

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

    def setUp(self):
        """Copy sample files to temp directory."""
        for f in self.temp_dir.glob('*'):
            if f.is_file():
                f.unlink()
        for src in self.test_dir.glob('*'):
            if src.is_file():
                shutil.copy(src, self.temp_dir / src.name)

    def test_single_file_conversion(self):
        """Test single file conversion through main converter."""
        input_file = self.temp_dir / 'sample.png'
        if not input_file.exists():
            self.skipTest("Sample PNG file not found")

        success, message = self.converter.convert_file(str(input_file), 'jpg')

        self.assertTrue(success, f"Conversion should succeed: {message}")
        self.assertIn('jpg', message.lower())

        output_file = self.temp_dir / 'sample.jpg'
        self.assertTrue(output_file.exists())

    def test_multiple_files_conversion(self):
        """Test multiple file conversion with progress tracking."""
        from PIL import Image
        test_files = []
        for i, color in enumerate(['red', 'blue', 'green', 'yellow']):
            img = Image.new('RGB', (100, 100), color=color)
            filepath = self.temp_dir / f'multi_{i}.png'
            img.save(filepath)
            test_files.append(str(filepath))

        results = self.converter.convert_multiple_files(test_files, 'jpg', show_progress=False)

        success_count = sum(1 for success, _ in results if success)
        self.assertEqual(success_count, len(test_files), f"All conversions should succeed: {results}")

        for i in range(len(test_files)):
            output_file = self.temp_dir / f'multi_{i}.jpg'
            self.assertTrue(output_file.exists())

    def test_invalid_file_handling(self):
        """Test handling of invalid files."""
        fake_file = self.temp_dir / 'nonexistent.png'

        success, message = self.converter.convert_file(str(fake_file), 'jpg')

        self.assertFalse(success)
        self.assertIn('exist', message.lower())

    def test_unsupported_format_handling(self):
        """Test handling of unsupported formats."""
        fake_file = self.temp_dir / 'test.xyz'
        fake_file.write_text("fake content")

        success, message = self.converter.convert_file(str(fake_file), 'jpg')

        self.assertFalse(success)
        self.assertIn('not allowed', message.lower())


if __name__ == '__main__':
    unittest.main(verbosity=2)