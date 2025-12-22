"""Tests for subtitle models."""

import pytest

from src.models.subtitle import (
    SubtitleSegment,
    SubtitleStyle,
    SubtitleTrack,
    SubtitleFormat,
)


class TestSubtitleSegment:
    """Tests for SubtitleSegment model."""

    def test_create_segment(self):
        """Test creating a subtitle segment."""
        segment = SubtitleSegment(
            index=1,
            start_time=0.0,
            end_time=5.0,
            text="Test subtitle",
        )

        assert segment.index == 1
        assert segment.start_time == 0.0
        assert segment.end_time == 5.0
        assert segment.text == "Test subtitle"
        assert segment.duration == 5.0

    def test_end_time_validation(self):
        """Test that end_time must be greater than start_time."""
        with pytest.raises(ValueError, match="end_time must be greater"):
            SubtitleSegment(
                index=1,
                start_time=5.0,
                end_time=3.0,
                text="Invalid",
            )

    def test_confidence_range(self):
        """Test confidence score validation."""
        with pytest.raises(ValueError):
            SubtitleSegment(
                index=1,
                start_time=0.0,
                end_time=5.0,
                text="Test",
                confidence=1.5,  # Invalid: > 1.0
            )


class TestSubtitleStyle:
    """Tests for SubtitleStyle model."""

    def test_create_style(self):
        """Test creating a subtitle style."""
        style = SubtitleStyle(
            name="test",
            font_family="Arial",
            font_size=24,
            font_color="#FFFFFF",
        )

        assert style.name == "test"
        assert style.font_family == "Arial"
        assert style.font_size == 24

    def test_invalid_color(self):
        """Test that invalid hex colors are rejected."""
        with pytest.raises(ValueError, match="hex color"):
            SubtitleStyle(font_color="FFFFFF")  # Missing #

    def test_font_size_validation(self):
        """Test font size bounds."""
        with pytest.raises(ValueError):
            SubtitleStyle(font_size=100)  # Too large


class TestSubtitleTrack:
    """Tests for SubtitleTrack model."""

    def test_create_track(self):
        """Test creating a subtitle track."""
        track = SubtitleTrack(language="en")

        assert track.language == "en"
        assert len(track.segments) == 0
        assert track.total_duration == 0.0

    def test_add_segment(self):
        """Test adding segments to track."""
        track = SubtitleTrack(language="en")
        segment = SubtitleSegment(
            index=1,
            start_time=0.0,
            end_time=5.0,
            text="Test",
        )

        track.add_segment(segment)

        assert len(track.segments) == 1
        assert track.segments[0].index == 1

    def test_get_segment_at_time(self):
        """Test finding active segment at a given time."""
        track = SubtitleTrack(language="en")
        segment = SubtitleSegment(
            index=1,
            start_time=2.0,
            end_time=5.0,
            text="Test",
        )
        track.add_segment(segment)

        # During segment
        assert track.get_segment_at_time(3.0) == segment

        # Before segment
        assert track.get_segment_at_time(1.0) is None

        # After segment
        assert track.get_segment_at_time(6.0) is None

    def test_total_duration(self):
        """Test calculating total duration."""
        track = SubtitleTrack(language="en")

        segment1 = SubtitleSegment(index=1, start_time=0.0, end_time=2.0, text="First")
        segment2 = SubtitleSegment(index=2, start_time=3.0, end_time=10.0, text="Second")

        track.add_segment(segment1)
        track.add_segment(segment2)

        assert track.total_duration == 10.0
