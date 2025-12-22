"""Video processing utilities for extracting audio and burning subtitles."""

import subprocess
from enum import Enum
from pathlib import Path
from typing import Optional

from .subtitle_formatter import SubtitleFormatter
from ..models.subtitle import SubtitleFormat, SubtitleStyle, SubtitleTrack


class VideoCodec(str, Enum):
    """Supported video codecs for export."""

    H264 = "libx264"
    H265 = "libx265"
    VP9 = "libvpx-vp9"
    AV1 = "libaom-av1"


class VideoProcessor:
    """Process video files: extract audio, burn subtitles, convert formats."""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def get_video_duration(self, video_path: str | Path) -> float:
        """
        Get video duration in seconds.

        Args:
            video_path: Path to video file

        Returns:
            Duration in seconds
        """
        cmd = [
            self.ffmpeg_path,
            "-i", str(video_path),
            "-f", "null",
            "-",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            # Parse duration from stderr
            for line in result.stderr.split("\n"):
                if "Duration:" in line:
                    duration_str = line.split("Duration:")[1].split(",")[0].strip()
                    # Parse HH:MM:SS.mm
                    h, m, s = duration_str.split(":")
                    s_float = float(s)
                    return int(h) * 3600 + int(m) * 60 + s_float
        except (subprocess.TimeoutExpired, ValueError, IndexError):
            pass

        return 0.0

    def get_video_info(self, video_path: str | Path) -> dict:
        """
        Get detailed video information.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with video metadata
        """
        cmd = [
            self.ffmpeg_path,
            "-i", str(video_path),
            "-f", "null",
            "-",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        info = {
            "duration": 0.0,
            "width": 0,
            "height": 0,
            "fps": 0.0,
            "codec": "unknown",
            "audio_codec": "unknown",
        }

        for line in result.stderr.split("\n"):
            if "Duration:" in line:
                duration_str = line.split("Duration:")[1].split(",")[0].strip()
                try:
                    h, m, s = duration_str.split(":")
                    info["duration"] = int(h) * 3600 + int(m) * 60 + float(s)
                except ValueError:
                    pass

            if "Video:" in line:
                parts = line.split(",")
                for part in parts:
                    part = part.strip()
                    if "x" in part and "fps" not in part:
                        try:
                            res = part.strip().split()[0]
                            info["width"], info["height"] = map(int, res.split("x"))
                        except (ValueError, AttributeError):
                            pass
                    if "fps" in part:
                        try:
                            info["fps"] = float(part.split("fps")[0].strip().split()[-1])
                        except (ValueError, AttributeError):
                            pass
                    if part.startswith("Video:") or "codec" in part.lower():
                        for codec_part in part.split():
                            if not any(c in codec_part for c in ["[", "]", "(", ")"]):
                                info["codec"] = codec_part
                                break

            if "Audio:" in line:
                for codec in line.split(","):
                    if "aac" in codec.lower() or "mp3" in codec.lower() or "opus" in codec.lower():
                        info["audio_codec"] = codec.strip().split()[0]
                        break

        return info

    def extract_audio(
        self,
        video_path: str | Path,
        output_path: str | Path,
        sample_rate: int = 16000,
        channels: int = 1,
    ) -> Path:
        """
        Extract audio from video file.

        Args:
            video_path: Path to video file
            output_path: Output audio path
            sample_rate: Audio sample rate (default 16kHz for Whisper)
            channels: Number of audio channels (1 = mono)

        Returns:
            Path to extracted audio file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_path,
            "-i", str(video_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # PCM 16-bit
            "-ar", str(sample_rate),
            "-ac", str(channels),
            "-y",  # Overwrite
            str(output_path),
        ]

        try:
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=600,  # 10 minute timeout
            )
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to extract audio: {e.stderr}") from e
        except subprocess.TimeoutExpired:
            raise RuntimeError("Audio extraction timed out") from None

    def burn_subtitles(
        self,
        video_path: str | Path,
        subtitle_path: str | Path,
        output_path: str | Path,
        style: Optional[SubtitleStyle] = None,
        codec: VideoCodec = VideoCodec.H264,
    ) -> Path:
        """
        Burn subtitles into video (hard-subs).

        Args:
            video_path: Path to input video
            subtitle_path: Path to subtitle file (SRT/VTT/ASS)
            output_path: Output video path
            style: Optional subtitle style
            codec: Video codec to use

        Returns:
            Path to output video with burned subtitles
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        subtitle_path = Path(subtitle_path)

        # Build subtitle filter based on file type
        if subtitle_path.suffix.lower() == ".ass":
            # ASS files have built-in styling
            filter_spec = f"ass='{subtitle_path}'"
        else:
            # For SRT/VTT, apply basic styling
            style = style or SubtitleStyle()
            filter_spec = (
                f"subtitles='{subtitle_path}':"
                f"force_style='FontSize={style.font_size},"
                f"PrimaryColour=&H{SubtitleFormatter._bgr_to_hex(style.font_color)},"
                f"OutlineColour=&H{SubtitleFormatter._bgr_to_hex(style.outline_color)},"
                f"Outline={style.outline_width},"
                f"Alignment={SubtitleFormatter._alignment_to_ass(style.position, style.alignment)}'"
            )

        cmd = [
            self.ffmpeg_path,
            "-i", str(video_path),
            "-vf", f'"{filter_spec}"',
            "-c:v", str(codec.value),
            "-c:a", "copy",  # Copy audio without re-encoding
            "-y",
            str(output_path),
        ]

        try:
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=3600,  # 1 hour timeout for large videos
            )
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to burn subtitles: {e.stderr}") from e
        except subprocess.TimeoutExpired:
            raise RuntimeError("Subtitle burning timed out") from None

    def embed_subtitles(
        self,
        video_path: str | Path,
        subtitle_path: str | Path,
        output_path: str | Path,
        language: str = "en",
    ) -> Path:
        """
        Embed subtitles as soft-subs (separate stream).

        Args:
            video_path: Path to input video
            subtitle_path: Path to subtitle file
            output_path: Output video path
            language: ISO 639-1 language code

        Returns:
            Path to output video with embedded subtitles
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_path,
            "-i", str(video_path),
            "-i", str(subtitle_path),
            "-c", "copy",
            "-c:s", "mov_text",  # Subtitle codec
            "-metadata:s:s:0", f"language={language}",
            "-y",
            str(output_path),
        ]

        try:
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=1800,  # 30 minute timeout
            )
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to embed subtitles: {e.stderr}") from e
        except subprocess.TimeoutExpired:
            raise RuntimeError("Subtitle embedding timed out") from None

    def create_thumbnail(
        self,
        video_path: str | Path,
        output_path: str | Path,
        timestamp: float = 1.0,
        width: int = 320,
    ) -> Path:
        """
        Create a thumbnail image from video.

        Args:
            video_path: Path to video file
            output_path: Output image path
            timestamp: Timestamp to capture (seconds)
            width: Thumbnail width

        Returns:
            Path to thumbnail image
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_path,
            "-ss", str(timestamp),
            "-i", str(video_path),
            "-vframes", "1",
            "-vf", f"scale={width}:-1",
            "-y",
            str(output_path),
        ]

        try:
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create thumbnail: {e.stderr}") from e
