"""
Handles conversions between images including HEIC, SVG, and WEBP.
"""

from PIL import Image
from pathlib import Path


class ImageConverter:
    # Note: 'gif' is intentionally excluded — animated GIFs are handled
    # end-to-end by AnimatedConverter, which owns that extension.
    SUPPORTED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp', 'ico',
        'heic', 'heif', 'svg'}
    
    def __init__(self, quality: int = 95):
        self.quality = quality
    
    def convert(self, filepath: str, mode: str, new_name: str, 
                quality: int = None, resize: tuple = None):

        ext = Path(filepath).suffix.lower()
        mode = mode.lower()

        if ext == '.svg':
            self._convert_svg(filepath, mode, new_name, resize)
            return

        if ext in ('.heic', '.heif'):
            from pillow_heif import register_heif_opener
            register_heif_opener()

        if mode == 'ico':
            self.create_favicon(filepath, new_name=new_name)
            return

        img = Image.open(filepath)
        if resize: img = img.resize(resize, Image.Resampling.LANCZOS)
        if mode in ('jpg', 'jpeg') or 'A' not in img.getbands(): img = img.convert("RGB")

        output_path = Path(filepath).parent / f"{new_name}.{mode}"
        save_kwargs = {}
        if mode in ('jpg', 'jpeg', 'webp'):
            save_kwargs['quality'] = quality or self.quality
            save_kwargs['optimize'] = True
        elif mode == 'png':
            save_kwargs['optimize'] = True
            save_kwargs['compress_level'] = 6

        try:
            img.save(output_path, **save_kwargs)
        except (ValueError, KeyError):
            raise ValueError(f"Target format '.{mode}' not supported for images")
    
    def _convert_svg(self, filepath: str, mode: str, new_name: str, resize: tuple = None):
        import cairosvg
        if not resize: resize = (1024, 1024)

        if mode == 'png':
            output_path = Path(filepath).parent / f"{new_name}.png"
            cairosvg.svg2png(
                url=filepath,
                write_to=str(output_path),
                output_width=resize[0],
                output_height=resize[1]
            )
        else:
            temp_png = Path(filepath).parent / f"{new_name}_temp.png"
            cairosvg.svg2png(
                url=filepath,
                write_to=str(temp_png),
                output_width=resize[0],
                output_height=resize[1]
            )
            try:
                self.convert(str(temp_png), mode, new_name)
            finally:
                temp_png.unlink(missing_ok=True)

    def create_favicon(self, filepath: str, new_name: str = None, sizes: list = None):
        if sizes is None:
            sizes = [16, 32, 48, 64]

        img = Image.open(filepath)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        base_name = new_name or Path(filepath).stem
        output_path = Path(filepath).parent / f"{base_name}.ico"

        icons = [img.resize((s, s), Image.Resampling.LANCZOS) for s in sizes]
        icons[0].save(
            output_path,
            format='ICO',
            sizes=[(s, s) for s in sizes],
            append_icons=icons[1:]
        )
