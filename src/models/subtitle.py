"""Subtitle data models using Pydantic."""

from datetime import timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SubtitleFormat(str, Enum):
    """Supported subtitle export formats."""

    SRT = "srt"
    VTT = "vtt"
    ASS = "ass"
    TXT = "txt"
    JSON = "json"


class SubtitleSegment(BaseModel):
    """A single subtitle segment with timing and text."""

    index: int = Field(..., description="Segment index (1-based)")
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., ge=0, description="End time in seconds")
    text: str = Field(..., min_length=1, description="Subtitle text content")
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Transcription confidence score"
    )

    @field_validator("end_time")
    @classmethod
    def end_time_after_start(cls, v: float, info) -> float:
        """Ensure end time is after start time."""
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be greater than start_time")
        return v

    @property
    def duration(self) -> float:
        """Get segment duration in seconds."""
        return self.end_time - self.start_time

    def format_timestamp(self, format_type: SubtitleFormat = SubtitleFormat.SRT) -> str:
        """Format timestamp for specific subtitle format."""
        hours = int(self.start_time // 3600)
        minutes = int((self.start_time % 3600) // 60)
        seconds = self.start_time % 60

        if format_type == SubtitleFormat.SRT:
            return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        elif format_type == SubtitleFormat.VTT:
            return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        elif format_type == SubtitleFormat.ASS:
            centiseconds = int((self.start_time % 60) * 100)
            return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"
        return str(self.start_time)


class SubtitleStyle(BaseModel):
    """Subtitle styling configuration."""

    name: str = "default"
    font_family: str = "Arial"
    font_size: int = Field(default=24, ge=10, le=72)
    font_color: str = "#FFFFFF"
    font_style: str = "normal"  # normal, italic, bold
    background_color: str = "#000000"
    background_opacity: float = Field(default=0.0, ge=0.0, le=1.0)
    outline_color: str = "#000000"
    outline_width: int = Field(default=2, ge=0, le=5)
    shadow_color: str = "#000000"
    shadow_depth: int = Field(default=2, ge=0, le=10)
    position: str = "bottom"  # top, center, bottom
    vertical_margin: int = Field(default=50, ge=0, le=200)
    horizontal_margin: int = Field(default=50, ge=0, le=200)
    alignment: str = "center"  # left, center, right
    max_lines: int = Field(default=2, ge=1, le=4)
    max_width: int = Field(default=80, ge=20, le=100)  # percentage

    @field_validator("font_color", "background_color", "outline_color", "shadow_color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """Validate hex color format."""
        if not v.startswith("#") or len(v) != 7:
            raise ValueError('Color must be a valid hex color (e.g., "#FFFFFF")')
        return v


class SubtitleTrack(BaseModel):
    """Complete subtitle track with all segments."""

    language: str = Field(default="en", description="ISO 639-1 language code")
    segments: list[SubtitleSegment] = Field(default_factory=list)
    style: Optional[SubtitleStyle] = None

    def add_segment(self, segment: SubtitleSegment) -> None:
        """Add a segment to the track."""
        segment.index = len(self.segments) + 1
        self.segments.append(segment)

    def get_segment_at_time(self, time: float) -> Optional[SubtitleSegment]:
        """Get the active subtitle segment at a given time."""
        for segment in self.segments:
            if segment.start_time <= time <= segment.end_time:
                return segment
        return None

    @property
    def total_duration(self) -> float:
        """Get total duration of the subtitle track."""
        if not self.segments:
            return 0.0
        return self.segments[-1].end_time

    @property
    def segment_count(self) -> int:
        """Get number of segments in the track."""
        return len(self.segments)
