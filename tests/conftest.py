"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest


@pytest.fixture
def sample_subtitle_track():
    """Create a sample subtitle track for testing."""
    from src.models.subtitle import SubtitleTrack, SubtitleSegment

    track = SubtitleTrack(language="en")

    segments = [
        SubtitleSegment(index=1, start_time=0.0, end_time=2.5, text="Hello, world!"),
        SubtitleSegment(index=2, start_time=3.0, end_time=5.0, text="This is a test."),
        SubtitleSegment(index=3, start_time=5.5, end_time=8.0, text="Subtitle generation."),
    ]

    for segment in segments:
        track.add_segment(segment)

    return track
