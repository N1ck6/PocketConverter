"""
Image file conversion module.
Handles conversions between various image formats including HEIC, SVG, and WEBP.
"""

from PIL import Image
from pathlib import Path
import io


class ImageConverter:
    """Converter for image file formats."""
    
    SUPPORTED_EXTENSIONS = {
        'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp', 'ico', 
        'heic', 'svg', 'gif'
    }
    
    def __init__(self, quality: int = 95):
        """
        Initialize image converter.
        
        Args:
            quality: Default quality for lossy formats (1-100)
        """
        self.quality = quality
    
    def convert(self, filepath: str, mode: str, new_name: str, 
                quality: int = None, resize: tuple = None):
        """
        Convert image between supported formats.
        
        Args:
            filepath: Path to source image
            mode: Target format
            new_name: Output filename without extension
            quality: Quality setting (overrides default)
            resize: Tuple of (width, height) for resizing
        """
        # Handle HEIC format
        ext = Path(filepath).suffix.lower()
        if ext in ['.heic', '.heif']:
            self._convert_heic(filepath, mode, new_name, quality)
            return
        
        # Handle SVG format
        if ext == '.svg':
            self._convert_svg(filepath, mode, new_name, resize)
            return
        
        img = Image.open(filepath)
        
        # Apply resize if specified
        if resize:
            img = img.resize(resize, Image.Resampling.LANCZOS)
        
        # Convert to RGB if saving as JPG or image has no alpha channel
        if mode in ['jpg', 'jpeg'] or 'A' not in img.getbands():
            img = img.convert("RGB")
        
        output_path = Path(filepath).parent / f"{new_name}.{mode}"
        
        # Save with appropriate options
        save_kwargs = {}
        if mode in ['jpg', 'jpeg', 'webp']:
            save_kwargs['quality'] = quality or self.quality
            save_kwargs['optimize'] = True
        elif mode == 'png':
            save_kwargs['optimize'] = True
            save_kwargs['compress_level'] = 6
        
        img.save(output_path, **save_kwargs)
    
    def _convert_heic(self, filepath: str, mode: str, new_name: str, quality: int = None):
        """
        Convert HEIC/HEIF format to other formats.
        
        Args:
            filepath: Path to HEIC file
            mode: Target format
            new_name: Output filename
            quality: Quality setting
        """
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
            
            img = Image.open(filepath)
            output_path = Path(filepath).parent / f"{new_name}.{mode}"
            
            if mode in ['jpg', 'jpeg']:
                img = img.convert("RGB")
                img.save(output_path, quality=quality or self.quality, optimize=True)
            else:
                img.save(output_path)
                
        except ImportError:
            raise ImportError(
                "pillow-heif package required for HEIC conversion. "
                "Install with: pip install pillow-heif"
            )
    
    def _convert_svg(self, filepath: str, mode: str, new_name: str, resize: tuple = None):
        """
        Convert SVG to raster formats.
        
        Args:
            filepath: Path to SVG file
            mode: Target format (png, jpg, etc.)
            new_name: Output filename
            resize: Optional size tuple
        """
        try:
            import cairosvg
            
            # Default size if not specified
            if not resize:
                resize = (1024, 1024)
            
            output_path = Path(filepath).parent / f"{new_name}.{mode}"
            
            if mode == 'png':
                cairosvg.svg2png(
                    url=filepath,
                    write_to=str(output_path),
                    output_width=resize[0],
                    output_height=resize[1]
                )
            else:
                # Convert to PNG first, then to target format
                temp_png = Path(filepath).parent / f"{new_name}_temp.png"
                cairosvg.svg2png(
                    url=filepath,
                    write_to=str(temp_png),
                    output_width=resize[0],
                    output_height=resize[1]
                )
                # Then convert PNG to target format
                self.convert(str(temp_png), mode, new_name)
                temp_png.unlink()  # Remove temp file
                
        except ImportError:
            raise ImportError(
                "cairosvg package required for SVG conversion. "
                "Install with: pip install cairosvg"
            )
    
    def create_favicon(self, filepath: str, sizes: list = None):
        """
        Create ICO favicon from image with multiple sizes.
        
        Args:
            filepath: Path to source image
            sizes: List of sizes to include (default: [16, 32, 48, 64])
        """
        if sizes is None:
            sizes = [16, 32, 48, 64]
        
        img = Image.open(filepath)
        output_path = Path(filepath).parent / f"{Path(filepath).stem}.ico"
        
        # Create resized versions
        icons = []
        for size in sizes:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            icons.append(resized)
        
        # Save as ICO with multiple sizes
        icons[0].save(
            output_path,
            format='ICO',
            sizes=[(s, s) for s in sizes],
            append_icons=icons[1:]
        )
