"""
Handles conversions between images including HEIC, SVG, and WEBP.
"""

from pathlib import Path

from PIL import Image, ImageOps

from converter_app.utils import DEFAULT_IMAGE_QUALITY, output_path

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
SVG_LONG_SIDE = 1024  # SVGs are rasterized so that their longer side is this many pixels


class ImageConverter:
    # Note: 'gif' is intentionally excluded — animated GIFs are handled
    # end-to-end by AnimatedConverter, which owns that extension.
    SUPPORTED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp', 'ico',
                            'heic', 'heif', 'svg'}

    def __init__(self, quality: int = DEFAULT_IMAGE_QUALITY):
        self.quality = quality

    def convert(self, filepath: str, mode: str, new_name: str,
                quality: int = None, resize: tuple = None):
        mode = mode.lower()
        img = self.load(filepath)
        if resize:
            img = img.resize(resize, Image.Resampling.LANCZOS)

        if mode == 'ico':
            self.create_favicon(img, output_path(filepath, new_name, 'ico'))
            return
        self.save(img, output_path(filepath, new_name, mode), mode, quality or self.quality)

    @staticmethod
    def load(filepath) -> Image.Image:
        """Open any supported image upright (EXIF orientation applied)."""
        ext = Path(filepath).suffix.lower()
        if ext == '.svg':
            return ImageConverter._rasterize_svg(filepath)
        if ext in ('.heic', '.heif'):
            from pillow_heif import register_heif_opener
            register_heif_opener()

        with Image.open(filepath) as img:
            img.load()
        img = ImageOps.exif_transpose(img)
        if img.mode == 'CMYK':  # print-oriented files: convert once, here, so a CMYK ICC profile never ends up on RGB pixels
            img = ImageConverter._cmyk_to_rgb(img)
        return img

    @staticmethod
    def _cmyk_to_rgb(img: Image.Image) -> Image.Image:
        icc = img.info.get('icc_profile')
        if icc:
            try:
                import io
                from PIL import ImageCms
                src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
                rgb = ImageCms.profileToProfile(img, src, ImageCms.createProfile('sRGB'), outputMode='RGB')
            except Exception:
                rgb = img.convert('RGB')
        else:
            rgb = img.convert('RGB')
        rgb.info.pop('icc_profile', None)
        return rgb

    @staticmethod
    def _rasterize_svg(filepath) -> Image.Image:
        import pymupdf
        with pymupdf.open(str(filepath)) as doc:
            rect = doc[0].rect
            scale = SVG_LONG_SIDE / max(rect.width, rect.height, 1)
            pix = doc[0].get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=True)
            return Image.frombytes('RGBA', (pix.width, pix.height), pix.samples)

    def save(self, img: Image.Image, out: Path, mode: str, quality: int = None) -> None:
        save_kwargs = {}
        icc = img.info.get('icc_profile')
        if icc:
            save_kwargs['icc_profile'] = icc

        if mode in ('jpg', 'jpeg'):
            img = self._flatten(img)
            save_kwargs.update(quality=quality or self.quality, optimize=True)
        elif mode == 'webp':
            img = img if self._has_alpha(img) else img.convert('RGB')
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA')
            save_kwargs['quality'] = quality or self.quality
        elif mode == 'png':
            if img.mode not in ('1', 'L', 'LA', 'P', 'RGB', 'RGBA', 'I', 'I;16'):
                img = img.convert('RGBA' if self._has_alpha(img) else 'RGB')
            save_kwargs['compress_level'] = 6
        elif img.mode not in ('RGB', 'RGBA', 'L'):
            img = img.convert('RGBA' if self._has_alpha(img) else 'RGB')

        exif = img.getexif()
        if exif and mode in ('jpg', 'jpeg', 'webp', 'png'):
            save_kwargs['exif'] = exif.tobytes()

        try:
            img.save(out, format=Image.registered_extensions().get(f'.{mode}'), **save_kwargs)
        except (ValueError, KeyError) as e:
            out.unlink(missing_ok=True)
            raise ValueError(f"Target format '.{mode}' not supported for images") from e

    @staticmethod
    def _has_alpha(img: Image.Image) -> bool:
        return 'A' in img.getbands() or (img.mode == 'P' and 'transparency' in img.info)

    def _flatten(self, img: Image.Image) -> Image.Image:
        """Composite transparent images onto white — JPEG has no alpha channel."""
        if not self._has_alpha(img):
            return img.convert('RGB')
        rgba = img.convert('RGBA')
        background = Image.new('RGB', rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel('A'))
        return background

    @staticmethod
    def create_favicon(img: Image.Image, out: Path, sizes: list = None) -> None:
        """Multi-resolution .ico; non-square images are centered on a transparent square."""
        sizes = sizes or ICO_SIZES
        img = img.convert('RGBA')
        side = max(img.size)
        if img.width != img.height:
            square = Image.new('RGBA', (side, side), (0, 0, 0, 0))
            square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
            img = square
        if side < max(sizes):  # upscale so every icon size gets generated
            img = img.resize((max(sizes), max(sizes)), Image.Resampling.LANCZOS)
        img.save(out, format='ICO', sizes=[(s, s) for s in sizes])
