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
from converter_app.utils import _sha256_text, _image_pixel_hash, _pdf_text_hash, _docx_text_hash

# Expected SHA256 hashes
HASH = {
    # ── DocumentConverter ──
    "txt_to_pdf":   "bdd62d24400bda5f949feef040ee81d12d99cf59544b86aad63b46f8566017a8",
    "txt_to_docx":  "c6e20ac29adf95481d582a1624fece6f13858fea1e27b4445c2e51d3ff8a49fe",
    "md_to_html":   "274f4499c45db64414d1ef4c5513b819c72b216e7f72b37a0d6aa9e12f3c9d24",
    "html_to_txt":  "fcb0cc3c62ff84a0a1fc3de9242514434b5d4cd82e97611168c81508e7dd3c71",
    "md_to_txt":    "e983b42b4cfa06ec78bfb801ed9b26adf713412d97337c59339f4d3ab503147c",

    # ── ImageConverter (pixel hashes) ──
    "png_to_jpg":   "71769ca2e8ab0c6913868951cd3f3dedd2a91e1b84f8f06007b981e3742aa257",
    "png_to_bmp":   "d02a8da86fec6ef80c209c8437c76cf8fbecb6528cd7ba95ef93eecc52a171c7",
    "jpg_to_png":   "cccb95455522c0eea4edaddef2921f9cc0eae3e4120c5691ab878c4558ced55d",
    "bmp_to_webp":  "0dbb746cbe56dd10d7bb319e8ad0ba1d3f736d709a90fbcdea3f63e2d1a4f1b4",

    # ── DataConverter ──
    "json_to_csv":  "bfb7e00208ff62a2ed59f9890f2fd2b4dcdb533ee043b252d75ec68f96293559",
    "json_to_xml":  "03421661858c3bd94a622429f1e8a4b19b9aa0179ee399b755a8dfcfcb159b18",
    "csv_to_json":  "c0840f5777f389f21611705ddbb36f19661bb2da5f1e42abc6465b9a7a550fc1",
    "xml_to_json":  "f1a728a1b83af48f23102b50fc9b3ace1065652a5a98e3f2a7b28b64f3d9e26d",
    "yaml_to_json": "5e0533807b3d372823bec729e74a5bdacdc07a6bafe38bf726b3ce78ba5bb751",
    "json_to_yaml": "6f27adab722bfb2b9d1238a0123323a1dfccfab74de9e2165cc18796ffe1187b",

    # ── Integration ──
    "integration_single": "cccb95455522c0eea4edaddef2921f9cc0eae3e4120c5691ab878c4558ced55d",
}

class TestImageConverter(unittest.TestCase):
    """Test image conversion functionality."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path(__file__).parent
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.converter = ImageConverter()

    @classmethod
    def tearDownClass(cls):
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

    def setUp(self):
        for f in self.temp_dir.glob("*"):
            if f.is_file():
                f.unlink()
        for ext in ["png", "jpg", "bmp"]:
            src = self.test_dir / f"sample.{ext}"
            if src.exists():
                shutil.copy(src, self.temp_dir / f"sample.{ext}")

    def test_png_to_jpg_conversion(self):
        input_file = self.temp_dir / "sample.png"
        self.assertTrue(input_file.exists(), "Sample PNG file must exist")

        self.converter.convert(str(input_file), "jpg", "output")
        output_file = self.temp_dir / "output.jpg"

        self.assertTrue(output_file.exists(), "JPG output file should be created")
        self.assertGreater(output_file.stat().st_size, 0, "Output file should not be empty")
        actual = _image_pixel_hash(output_file)
        self.assertEqual(actual, HASH["png_to_jpg"],
                         f"PNG->JPG hash mismatch. ACTUAL: {actual}")

    def test_png_to_bmp_conversion(self):
        input_file = self.temp_dir / "sample.png"
        self.assertTrue(input_file.exists(), "Sample PNG file must exist")

        self.converter.convert(str(input_file), "bmp", "output")
        output_file = self.temp_dir / "output.bmp"

        self.assertTrue(output_file.exists(), "BMP output file should be created")
        actual = _image_pixel_hash(output_file)
        self.assertEqual(actual, HASH["png_to_bmp"],
                         f"PNG->BMP hash mismatch. ACTUAL: {actual}")

    def test_jpg_to_png_conversion(self):
        input_file = self.temp_dir / "sample.jpg"
        self.assertTrue(input_file.exists(), "Sample JPG file must exist")

        self.converter.convert(str(input_file), "png", "output")
        output_file = self.temp_dir / "output.png"

        self.assertTrue(output_file.exists(), "PNG output file should be created")
        actual = _image_pixel_hash(output_file)
        self.assertEqual(actual, HASH["jpg_to_png"],
                         f"JPG->PNG hash mismatch. ACTUAL: {actual}")

    def test_bmp_to_webp_conversion(self):
        input_file = self.temp_dir / "sample.bmp"
        self.assertTrue(input_file.exists(), "Sample BMP file must exist")

        self.converter.convert(str(input_file), "webp", "output")
        output_file = self.temp_dir / "output.webp"

        self.assertTrue(output_file.exists(), "WEBP output file should be created")
        actual = _image_pixel_hash(output_file)
        self.assertEqual(actual, HASH["bmp_to_webp"],
                         f"BMP->WEBP hash mismatch. ACTUAL: {actual}")

class TestDocumentConverter(unittest.TestCase):
    """Test document conversion functionality."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path(__file__).parent
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.converter = DocumentConverter()

    @classmethod
    def tearDownClass(cls):
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

    def setUp(self):
        for f in self.temp_dir.glob("*"):
            if f.is_file():
                f.unlink()
        for ext in ["txt", "md", "html"]:
            src = self.test_dir / f"sample.{ext}"
            if src.exists():
                shutil.copy(src, self.temp_dir / f"sample.{ext}")

    def test_txt_to_pdf_conversion(self):
        input_file = self.temp_dir / "sample.txt"
        self.assertTrue(input_file.exists(), "Sample TXT file must exist")

        self.converter.convert(str(input_file), "pdf", "output")
        output_file = self.temp_dir / "output.pdf"

        self.assertTrue(output_file.exists(), "PDF output file should be created")
        self.assertGreater(output_file.stat().st_size, 0, "Output file should not be empty")
        actual = _pdf_text_hash(output_file)
        self.assertEqual(actual, HASH["txt_to_pdf"],
                         f"TXT->PDF hash mismatch. ACTUAL: {actual}")

    def test_txt_to_docx_conversion(self):
        input_file = self.temp_dir / "sample.txt"
        self.assertTrue(input_file.exists(), "Sample TXT file must exist")

        self.converter.convert(str(input_file), "docx", "output")
        output_file = self.temp_dir / "output.docx"

        self.assertTrue(output_file.exists(), "DOCX output file should be created")
        actual = _docx_text_hash(output_file)
        self.assertEqual(actual, HASH["txt_to_docx"],
                         f"TXT->DOCX hash mismatch. ACTUAL: {actual}")

    def test_md_to_html_conversion(self):
        input_file = self.temp_dir / "sample.md"
        self.assertTrue(input_file.exists(), "Sample MD file must exist")

        self.converter.convert(str(input_file), "html", "output")
        output_file = self.temp_dir / "output.html"

        self.assertTrue(output_file.exists(), "HTML output file should be created")
        content = output_file.read_text(encoding="utf-8")
        self.assertIn("<html", content)
        self.assertIn("</html>", content)
        actual = _sha256_text(content)
        self.assertEqual(actual, HASH["md_to_html"],
                         f"MD->HTML hash mismatch. ACTUAL: {actual}")

    def test_html_to_txt_conversion(self):
        input_file = self.temp_dir / "sample.html"
        self.assertTrue(input_file.exists(), "Sample HTML file must exist")

        self.converter.convert(str(input_file), "txt", "output")
        output_file = self.temp_dir / "output.txt"

        self.assertTrue(output_file.exists(), "TXT output file should be created")
        content = output_file.read_text(encoding="utf-8")
        self.assertIn("Hello World", content)
        actual = _sha256_text(content)
        self.assertEqual(actual, HASH["html_to_txt"],
                         f"HTML->TXT hash mismatch. ACTUAL: {actual}")

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
        input_file = self.temp_dir / 'sample.md'
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
        cls.test_dir = Path(__file__).parent
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.converter = DataConverter()

    @classmethod
    def tearDownClass(cls):
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

    def setUp(self):
        for f in self.temp_dir.glob("*"):
            if f.is_file():
                f.unlink()
        for ext in ["json", "csv", "xml", "yaml"]:
            src = self.test_dir / f"sample.{ext}"
            if src.exists():
                shutil.copy(src, self.temp_dir / f"sample.{ext}")

    def test_json_to_csv_conversion(self):
        input_file = self.temp_dir / "sample.json"
        self.assertTrue(input_file.exists(), "Sample JSON file must exist")

        self.converter.convert(str(input_file), "csv", "output")
        output_file = self.temp_dir / "output.csv"

        self.assertTrue(output_file.exists(), "CSV output file should be created")
        actual = _sha256_text(output_file.read_text(encoding="utf-8"))
        self.assertEqual(actual, HASH["json_to_csv"],
                         f"JSON->CSV hash mismatch. ACTUAL: {actual}")

    def test_json_to_xml_conversion(self):
        input_file = self.temp_dir / "sample.json"
        self.assertTrue(input_file.exists(), "Sample JSON file must exist")

        self.converter.convert(input_file, "xml", "output")
        output_file = self.temp_dir / "output.xml"

        self.assertTrue(output_file.exists(), "XML output file should be created")
        content = output_file.read_text(encoding="utf-8")
        self.assertIn("<?xml", content)
        actual = _sha256_text(content)
        self.assertEqual(actual, HASH["json_to_xml"],
                         f"JSON->XML hash mismatch. ACTUAL: {actual}")

    def test_csv_to_json_conversion(self):
        input_file = self.temp_dir / "sample.csv"
        self.assertTrue(input_file.exists(), "Sample CSV file must exist")

        self.converter.convert(str(input_file), "json", "output")
        output_file = self.temp_dir / "output.json"

        self.assertTrue(output_file.exists(), "JSON output file should be created")
        import json as _json
        with open(output_file, "r") as f:
            data = _json.load(f)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        actual = _sha256_text(output_file.read_text(encoding="utf-8"))
        self.assertEqual(actual, HASH["csv_to_json"],
                         f"CSV->JSON hash mismatch. ACTUAL: {actual}")

    def test_xml_to_json_conversion(self):
        input_file = self.temp_dir / "sample.xml"
        self.assertTrue(input_file.exists(), "Sample XML file must exist")

        self.converter.convert(str(input_file), "json", "output")
        output_file = self.temp_dir / "output.json"

        self.assertTrue(output_file.exists(), "JSON output file should be created")
        actual = _sha256_text(output_file.read_text(encoding="utf-8"))
        self.assertEqual(actual, HASH["xml_to_json"],
                         f"XML->JSON hash mismatch. ACTUAL: {actual}")

    def test_yaml_to_json_conversion(self):
        input_file = self.temp_dir / "sample.yaml"
        self.assertTrue(input_file.exists(), "Sample YAML file must exist")

        self.converter.convert(str(input_file), "json", "output")
        output_file = self.temp_dir / "output.json"

        self.assertTrue(output_file.exists(), "JSON output file should be created")
        actual = _sha256_text(output_file.read_text(encoding="utf-8"))
        self.assertEqual(actual, HASH["yaml_to_json"],
                         f"YAML->JSON hash mismatch. ACTUAL: {actual}")

    def test_json_to_yaml_conversion(self):
        input_file = self.temp_dir / "sample.json"
        self.assertTrue(input_file.exists(), "Sample JSON file must exist")

        self.converter.convert(str(input_file), "yaml", "output")
        output_file = self.temp_dir / "output.yaml"

        self.assertTrue(output_file.exists(), "YAML output file should be created")
        actual = _sha256_text(output_file.read_text(encoding="utf-8"))
        self.assertEqual(actual, HASH["json_to_yaml"],
                         f"JSON->YAML hash mismatch. ACTUAL: {actual}")

class TestBatchProcessor(unittest.TestCase):
    """Test batch processing functionality."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path(__file__).parent
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.processor = BatchProcessor()

    @classmethod
    def tearDownClass(cls):
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

    def setUp(self):
        self.batch_folder = self.temp_dir / "batch_test"
        self.batch_folder.mkdir(exist_ok=True)

        from PIL import Image
        for i, color in enumerate(["red", "green", "blue"]):
            img = Image.new("RGB", (100, 100), color=color)
            img.save(self.batch_folder / f"image{i}.png")

    def test_images_to_pdf_batch(self):
        self.processor.convert_folder(str(self.batch_folder), "pdf")

        parent_dir = self.batch_folder.parent
        pdf_files = list(parent_dir.glob("Combined_images*.pdf"))

        self.assertGreater(len(pdf_files), 0, "PDF file should be created")
        for f in pdf_files:
            self.assertGreater(f.stat().st_size, 0, "PDF should not be empty")
            f.unlink()

    def test_images_to_gif_batch(self):
        self.processor.convert_folder(str(self.batch_folder), "gif")

        parent_dir = self.batch_folder.parent
        gif_files = list(parent_dir.glob("Combined_images*.gif"))

        self.assertGreater(len(gif_files), 0, "GIF file should be created")
        for f in gif_files:
            self.assertGreater(f.stat().st_size, 0, "GIF should not be empty")
            f.unlink()

class TestIntegration(unittest.TestCase):
    """Integration tests for complete conversion workflows."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from converter import FileConverter
        cls.test_dir = Path(__file__).parent
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.converter = FileConverter()

    @classmethod
    def tearDownClass(cls):
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

    def setUp(self):
        for f in self.temp_dir.glob("*"):
            if f.is_file():
                f.unlink()
        for src in self.test_dir.glob("*"):
            if src.is_file():
                shutil.copy(src, self.temp_dir / src.name)

    def test_single_file_conversion(self):
        input_file = self.temp_dir / "sample.png"
        self.assertTrue(input_file.exists(), "Sample PNG file must exist")

        success, message = self.converter.convert_file(str(input_file), "jpg")

        self.assertTrue(success, f"Conversion should succeed: {message}")
        self.assertIn("jpg", message.lower())

        output_file = self.temp_dir / "sample.jpg"
        self.assertTrue(output_file.exists())
        actual = _image_pixel_hash(output_file)
        self.assertEqual(actual, HASH["integration_single"],
                         f"Integration hash mismatch. ACTUAL: {actual}")

    def test_multiple_files_conversion(self):
        from PIL import Image
        test_files = []
        for i, color in enumerate(["red", "blue", "green", "yellow"]):
            img = Image.new("RGB", (100, 100), color=color)
            filepath = self.temp_dir / f"multi_{i}.png"
            img.save(filepath)
            test_files.append(str(filepath))

        results = self.converter.convert_multiple_files(test_files, "jpg", show_progress=False)

        success_count = sum(1 for success, _ in results if success)
        self.assertEqual(success_count, len(test_files),
                         f"All conversions should succeed: {results}")

        for i in range(len(test_files)):
            output_file = self.temp_dir / f"multi_{i}.jpg"
            self.assertTrue(output_file.exists())
            self.assertGreater(output_file.stat().st_size, 0)

    def test_invalid_file_handling(self):
        fake_file = self.temp_dir / "nonexistent.png"

        success, message = self.converter.convert_file(str(fake_file), "jpg")

        self.assertFalse(success)
        self.assertIn("exist", message.lower())

    def test_unsupported_format_handling(self):
        fake_file = self.temp_dir / "sample.xyz"
        fake_file.write_text("fake content")

        success, message = self.converter.convert_file(str(fake_file), "jpg")

        self.assertFalse(success)
        self.assertIn("not allowed", message.lower())

if __name__ == '__main__':
    unittest.main(verbosity=2)