"""
Handles video, GIF and audio conversions.

All heavy lifting is done by the FFmpeg binary bundled with imageio-ffmpeg,
so users don't need FFmpeg installed and no console window pops up.
"""

from pathlib import Path
from typing import Optional

from PIL import Image, ImageSequence

from converter_app.utils import (DEFAULT_AUDIO_BITRATE, DEFAULT_VIDEO_BITRATE,
                                 get_unique_dirname, output_path, run_ffmpeg)

GIF_FPS = 10
GIF_MAX_WIDTH = 720  # full-HD GIFs are enormous; this keeps them shareable

EVEN_DIMENSIONS = 'scale=trunc(iw/2)*2:trunc(ih/2)*2'  # H.264 4:2:0 requires even width/height


class AnimatedConverter:
    VIDEO_EXTENSIONS = {'mp4', 'mov', 'mkv', 'avi', 'webm'}
    AUDIO_CODECS = {'mp3': 'libmp3lame', 'wav': 'pcm_s16le', 'flac': 'flac', 'aac': 'aac', 'ogg': 'libvorbis'}
    LOSSLESS = {'wav', 'flac'}
    SUPPORTED_EXTENSIONS = VIDEO_EXTENSIONS | {'gif', 'm4a'} | set(AUDIO_CODECS)

    def __init__(self, audio_bitrate: str = DEFAULT_AUDIO_BITRATE, video_bitrate: str = DEFAULT_VIDEO_BITRATE):
        self.audio_bitrate = audio_bitrate
        self.video_bitrate = video_bitrate

    def convert(self, filepath: str, mode: str, new_name: str) -> Optional[Path]:
        ext = Path(filepath).suffix.lower().lstrip('.')
        mode = mode.lower()

        if mode in self.AUDIO_CODECS and ext != 'gif':
            self._to_audio(filepath, output_path(filepath, new_name, mode), mode)
        elif ext in self.VIDEO_EXTENSIONS and mode == 'gif':
            self._video_to_gif(filepath, output_path(filepath, new_name, 'gif'))
        elif mode == 'mp4' and (ext in self.VIDEO_EXTENSIONS or ext == 'gif'):
            self._to_mp4(filepath, output_path(filepath, new_name, 'mp4'))
        elif ext == 'gif' and mode == 'png':
            with Image.open(filepath) as img:
                img.convert('RGBA').save(output_path(filepath, new_name, 'png'), 'PNG')
        elif ext == 'gif' and mode == 'pngs':
            return self._gif_to_frames(filepath, new_name)
        else:
            raise ValueError(f"Can't convert .{ext} to .{mode}")

    def _to_audio(self, fp: str, out: Path, mode: str) -> None:
        args = ['-i', fp, '-map', '0:a:0', '-vn', '-c:a', self.AUDIO_CODECS[mode]]
        if mode not in self.LOSSLESS:
            args += ['-b:a', self.audio_bitrate]
        self._run(args, out)

    def _video_to_gif(self, fp: str, out: Path) -> None:
        # Two-pass palette gives far better colors than the default 256-color web palette
        vf = (f"fps={GIF_FPS},scale='min({GIF_MAX_WIDTH},iw)':-1:flags=lanczos,"
              "split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5")
        self._run(['-i', fp, '-vf', vf, '-loop', '0'], out)

    def _to_mp4(self, fp: str, out: Path) -> None:
        # yuv420p + even size: plays in Windows Media Player, browsers and phones
        self._run(['-i', fp, '-vf', EVEN_DIMENSIONS, '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                   '-b:v', self.video_bitrate, '-c:a', 'aac', '-b:a', self.audio_bitrate,
                   '-movflags', '+faststart'], out)

    @staticmethod
    def _run(args: list, out: Path) -> None:
        try:
            run_ffmpeg([*args, str(out)])
        except Exception:
            out.unlink(missing_ok=True)  # don't leave a truncated file behind
            raise

    @staticmethod
    def _gif_to_frames(fp: str, new_name: str) -> Path:
        """Extract every frame into a new "<name>_frames" folder next to the GIF."""
        folder = get_unique_dirname(Path(fp).parent, f"{new_name}_frames")
        folder.mkdir()
        with Image.open(fp) as img:
            digits = len(str(getattr(img, 'n_frames', 1)))
            for i, frame in enumerate(ImageSequence.Iterator(img)):
                frame.convert('RGBA').save(folder / f"frame_{i:0{digits}d}.png", 'PNG')
        return folder
