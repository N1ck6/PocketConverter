"""
Handles conversions between MP4, GIF, PNG formats and audio extraction.
"""

from PIL import Image
from pathlib import Path
from moviepy import VideoFileClip
from converter_app.utils import check_ffmpeg, get_ffmpeg_help, show_toast, ICON_PATH
import sys


class AnimatedConverter:
    
    SUPPORTED_EXTENSIONS = {'mp4', 'gif', 'mp3', 'wav', 'flac', 'aac', 'ogg'}
    
    def __init__(self, audio_bitrate: str = '192k', video_bitrate: str = '2000k'):
        self.audio_bitrate = audio_bitrate
        self.video_bitrate = video_bitrate
    
    def _check_ffmpeg(self, operation: str = "video/audio conversion"):
        if not check_ffmpeg():
            show_toast(
                "FFmpeg Required",
                f"FFmpeg is needed for {operation}. Please install it.",
                icon=ICON_PATH
            )
            print(get_ffmpeg_help(), file=sys.stderr)
            raise RuntimeError("FFmpeg not found")
    
    def convert(self, filepath: str, mode: str, new_name: str,
                audio_bitrate: str = None, video_bitrate: str = None,
                fps: int = 10):
        ext = Path(filepath).suffix
        
        if ext == ".mp4":
            self._convert_from_mp4(filepath, mode, new_name, audio_bitrate, video_bitrate, fps)
        elif ext == ".gif":
            self._convert_from_gif(filepath, mode, new_name, video_bitrate, fps)
        elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
            self._convert_audio(filepath, mode, new_name, audio_bitrate)
    
    def _convert_from_mp4(self, filepath: str, mode: str, new_name: str,
                          audio_bitrate: str = None, video_bitrate: str = None, fps: int = 10):
        if mode == "gif":
            self._video_to_gif(filepath, new_name, fps)
        elif mode == "mp3":
            self._video_to_audio(filepath, new_name, audio_bitrate)
        elif mode in ['wav', 'flac', 'aac', 'ogg']:
            self._video_to_audio(filepath, new_name, audio_bitrate, output_format=mode)
    
    def _convert_from_gif(self, filepath: str, mode: str, new_name: str,
                          video_bitrate: str = None, fps: int = 10):
        if mode == "pngs":
            self._gif_to_photos(filepath, new_name)
        elif mode == "png":
            self._gif_to_photo(filepath, new_name)
        elif mode == "mp4":
            self._gif_to_video(filepath, new_name, video_bitrate)
    
    def _convert_audio(self, filepath: str, mode: str, new_name: str, audio_bitrate: str = None):
        self._check_ffmpeg("audio format conversion")
        
        import subprocess
        
        output_path = Path(filepath).parent / f"{new_name}.{mode}"
        
        codec_map = {
            'mp3': 'libmp3lame',
            'wav': 'pcm_s16le',
            'flac': 'flac',
            'aac': 'aac',
            'ogg': 'libvorbis'
        }
        
        cmd = [
            'ffmpeg', '-i', filepath,
            '-acodec', codec_map.get(mode, mode),
            '-b:a', audio_bitrate or self.audio_bitrate,
            '-y',
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Audio conversion failed: {e.stderr.decode()}")
    
    def _video_to_gif(self, filepath: str, new_name: str, fps: int = 10):
        self._check_ffmpeg("GIF conversion")
        
        output_path = Path(filepath).parent / f"{new_name}.gif"
        clip = VideoFileClip(filepath)
        clip.write_gif(output_path, fps=fps, logger=None)
        clip.close()
    
    def _video_to_audio(self, filepath: str, new_name: str, 
                        audio_bitrate: str = None, output_format: str = 'mp3'):
        self._check_ffmpeg("audio extraction")
        
        output_path = Path(filepath).parent / f"{new_name}.{output_format}"
        video = VideoFileClip(filepath)
        video.audio.write_audiofile(
            output_path, 
            bitrate=audio_bitrate or self.audio_bitrate,
            logger=None
        )
        video.close()
    
    def _gif_to_video(self, filepath: str, new_name: str, video_bitrate: str = None):
        self._check_ffmpeg("GIF to video conversion")
        
        output_path = Path(filepath).parent / f"{new_name}.mp4"
        video = VideoFileClip(filepath)
        video.write_videofile(
            output_path, 
            bitrate=video_bitrate or self.video_bitrate,
            logger=None
        )
        video.close()
    
    def _gif_to_photo(self, filepath: str, new_name: str):
        frame = Image.open(filepath)
        output_path = Path(filepath).parent / f"{new_name}.png"
        frame.save(output_path, 'PNG')
    
    def _gif_to_photos(self, filepath: str, new_name: str):
        output_folder = Path(filepath).parent / "extracted gif"
        output_folder.mkdir(exist_ok=True)
        
        frame = Image.open(filepath)
        nframes = 0
        
        while frame:
            frame.save(output_folder / f"{new_name}-{nframes}.png", 'PNG')
            nframes += 1
            try:
                frame.seek(nframes)
            except EOFError:
                break
