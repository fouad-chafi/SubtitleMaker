"""Tests for subtitle formatter."""

import pytest

from src.core.subtitle_formatter import SubtitleFormatter
from src.models.subtitle import SubtitleTrack, SubtitleSegment, SubtitleFormat, SubtitleStyle


class TestSubtitleFormatter:
    """Tests for SubtitleFormatter."""

    @pytest.fixture
    def sample_track(self):
        """Create a sample subtitle track."""
        track = SubtitleTrack(language="en")

        segments = [
            SubtitleSegment(index=1, start_time=0.0, end_time=2.5, text="Hello, world!"),
            SubtitleSegment(index=2, start_time=3.0, end_time=5.0, text="This is a test."),
        ]

        for segment in segments:
            track.add_segment(segment)

        return track

    def test_format_srt(self, sample_track):
        """Test SRT formatting."""
        formatter = SubtitleFormatter()
        result = formatter.format(sample_track, SubtitleFormat.SRT)

        assert "1" in result
        assert "00:00:00,000 --> 00:00:02,500" in result
        assert "Hello, world!" in result
        assert "2" in result
        assert "This is a test." in result

    def test_format_vtt(self, sample_track):
        """Test WebVTT formatting."""
        formatter = SubtitleFormatter()
        result = formatter.format(sample_track, SubtitleFormat.VTT)

        assert "WEBVTT" in result
        assert "Hello, world!" in result

    def test_format_txt(self, sample_track):
        """Test plain text formatting."""
        formatter = SubtitleFormatter()
        result = formatter.format(sample_track, SubtitleFormat.TXT)

        assert "Hello, world!" in result
        assert "This is a test." in result
        # No timestamps in plain text
        assert "-->" not in result

    def test_format_json(self, sample_track):
        """Test JSON formatting."""
        import json

        formatter = SubtitleFormatter()
        result = formatter.format(sample_track, SubtitleFormat.JSON)

        data = json.loads(result)
        assert data["language"] == "en"
        assert len(data["segments"]) == 2
        assert data["segments"][0]["text"] == "Hello, world!"

    def test_parse_srt(self):
        """Test parsing SRT format."""
        srt_content = """1
00:00:00,000 --> 00:00:02,500
Hello, world!

2
00:00:03,000 --> 00:00:05,000
This is a test.
"""

        formatter = SubtitleFormatter()
        track = formatter.parse_srt(srt_content)

        assert len(track.segments) == 2
        assert track.segments[0].text == "Hello, world!"
        assert track.segments[0].start_time == 0.0
        assert track.segments[0].end_time == 2.5
