"""
Handles conversions between MP4, GIF, PNG formats and audio extraction.
"""

from PIL import Image, ImageSequence
from pathlib import Path
from moviepy import VideoFileClip
from converter_app.utils import check_ffmpeg, show_toast
import subprocess


class AnimatedConverter:
    SUPPORTED_EXTENSIONS = {'mp4', 'gif', 'mp3', 'wav', 'flac', 'aac', 'ogg'}
    AUDIO_CODECS = {'mp3': 'libmp3lame', 'wav': 'pcm_s16le', 'flac': 'flac', 'aac': 'aac', 'ogg': 'libvorbis'}
    
    def __init__(self, audio_bitrate: str = '192k', video_bitrate: str = '2000k'):
        self.audio_bitrate = audio_bitrate
        self.video_bitrate = video_bitrate
    
    @staticmethod
    def _ensure_ffmpeg() -> bool:
        if not check_ffmpeg(): show_toast("FFmpeg Required", "FFmpeg is needed for media conversion. Please install it.")
    
    def convert(self, filepath: str, mode: str, new_name: str,
                audio_bitrate: str = None, video_bitrate: str = None, fps: int = 10) -> None:
        if not self._ensure_ffmpeg():
            return
        ext = Path(filepath).suffix
        mode = mode.lower()
        ab = audio_bitrate or self.audio_bitrate
        vb = video_bitrate or self.video_bitrate
        out_dir = Path(filepath).parent

        if ext == 'mp4':
            self._route_mp4(filepath, mode, out_dir / new_name, ab, vb, fps)
        elif ext == 'gif':
            self._route_gif(filepath, mode, out_dir / new_name, vb, fps)
        elif ext in self.AUDIO_CODECS:
            self._convert_audio(filepath, mode, out_dir / f"{new_name}.{mode}", ab)
        else:
            show_toast("Error", f"Unsupported source format .{ext}")

    def _route_mp4(self, fp: str, mode: str, out_path: Path, ab: str, vb: str, fps: int) -> None:
        if mode == 'gif': self._video_to_gif(fp, out_path, fps)
        elif mode in self.AUDIO_CODECS: self._video_to_audio(fp, out_path, ab, mode)
        else: show_toast("Error", f"Target format '{mode}' not supported for MP4")

    def _route_gif(self, fp: str, mode: str, out_path: Path, vb: str, fps: int) -> None:
        if mode == 'mp4': self._gif_to_video(fp, out_path, vb)
        elif mode in ('png', 'pngs'):
            target = out_path.parent / f"{out_path.stem}_frames" if mode == 'pngs' else out_path.parent / f"{out_path.stem}.png"
            self._gif_to_photos(fp, target, mode == 'pngs')
        else: show_toast("Error", f"Target format '{mode}' not supported for GIF")
    
    def _convert_audio(self, fp: str, mode: str, out_path: Path, ab: str) -> None:
        cmd = ['ffmpeg', '-i', fp, '-acodec', self.AUDIO_CODECS[mode], '-b:a', ab, '-y', str(out_path)]
        
        try: subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            show_toast("Error", f"Audio conversion failed: {e.stderr.decode(errors='ignore')}")
    
    def _video_to_gif(self, fp: str, out_path: Path, fps: int) -> None:
        with VideoFileClip(fp) as clip:
            clip.write_gif(str(out_path), fps=fps, logger=None)

    def _video_to_audio(self, fp: str, out_path: Path, ab: str, fmt: str) -> None:
        with VideoFileClip(fp) as clip:
            clip.audio.write_audiofile(str(out_path), bitrate=ab, logger=None)

    def _gif_to_video(self, fp: str, out_path: Path, vb: str) -> None:
        with VideoFileClip(fp) as clip:
            clip.write_videofile(str(out_path), bitrate=vb, logger=None)
    
    def _gif_to_photos(self, fp: str, out_path: Path, extract_all: bool) -> None:
        out_path.parent.mkdir(exist_ok=True)
        base = out_path.stem
        with Image.open(fp) as img:
            if extract_all:
                for i, frame in enumerate(ImageSequence.Iterator(img)):
                    frame.save(out_path.parent / f"{base}-{i}.png", "PNG")
            else:
                img.save(out_path, "PNG")