"""Subtitle formatter for multiple export formats."""

import json
from datetime import timedelta
from pathlib import Path
from typing import Optional

from ..models.subtitle import SubtitleFormat, SubtitleSegment, SubtitleStyle, SubtitleTrack


class SubtitleFormatter:
    """Format subtitle tracks to various export formats."""

    def __init__(self, style: Optional[SubtitleStyle] = None):
        self.style = style or SubtitleStyle()

    def format(
        self,
        track: SubtitleTrack,
        format_type: SubtitleFormat,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Format subtitle track to specified format.

        Args:
            track: Subtitle track to format
            format_type: Output format
            output_path: Optional path to save the file

        Returns:
            Formatted subtitle content as string
        """
        if format_type == SubtitleFormat.SRT:
            content = self._format_srt(track)
        elif format_type == SubtitleFormat.VTT:
            content = self._format_vtt(track)
        elif format_type == SubtitleFormat.ASS:
            content = self._format_ass(track)
        elif format_type == SubtitleFormat.TXT:
            content = self._format_txt(track)
        elif format_type == SubtitleFormat.JSON:
            content = self._format_json(track)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8-sig")

        return content

    @staticmethod
    def _format_timestamp_srt(seconds: float) -> str:
        """Format timestamp for SRT format."""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        millis = td.microseconds // 1000
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _format_timestamp_vtt(seconds: float) -> str:
        """Format timestamp for WebVTT format."""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        millis = td.microseconds // 1000
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    @staticmethod
    def _format_timestamp_ass(seconds: float) -> str:
        """Format timestamp for ASS format."""
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        secs = td.seconds % 60
        centisecs = td.microseconds // 10000
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    def _format_srt(self, track: SubtitleTrack) -> str:
        """Format as SubRip (SRT)."""
        lines = []
        for segment in track.segments:
            start = self._format_timestamp_srt(segment.start_time)
            end = self._format_timestamp_srt(segment.end_time)
            lines.append(f"{segment.index}")
            lines.append(f"{start} --> {end}")
            lines.append(segment.text)
            lines.append("")  # Empty line between segments
        return "\n".join(lines)

    def _format_vtt(self, track: SubtitleTrack) -> str:
        """Format as WebVTT."""
        lines = ["WEBVTT\n"]
        for segment in track.segments:
            start = self._format_timestamp_vtt(segment.start_time)
            end = self._format_timestamp_vtt(segment.end_time)
            lines.append(f"{segment.index}")
            lines.append(f"{start} --> {end}")
            lines.append(segment.text)
            lines.append("")
        return "\n".join(lines)

    def _format_ass(self, track: SubtitleTrack) -> str:
        """Format as Advanced SubStation Alpha (ASS)."""
        style = self.style

        # ASS header
        lines = [
            "[Script Info]",
            "Title: SubtitleMaker Export",
            "ScriptType: v4.00+",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Default,{style.font_family},{style.font_size},&H{self._bgr_to_hex(style.font_color)},&H{self._bgr_to_hex(style.font_color)},&H{self._bgr_to_hex(style.outline_color)},&H{self._bgr_to_hex(style.background_color)},"
            f"{-1 if style.font_style == 'bold' else 0},{-1 if style.font_style == 'italic' else 0},0,0,100,100,0,0,1,{style.outline_width},{style.shadow_depth},"
            f"{self._alignment_to_ass(style.position, style.alignment)},{style.horizontal_margin},{style.horizontal_margin},{style.vertical_margin},1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]

        for segment in track.segments:
            start = self._format_timestamp_ass(segment.start_time)
            end = self._format_timestamp_ass(segment.end_time)
            text = self._escape_ass_text(segment.text)
            lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

        return "\n".join(lines)

    @staticmethod
    def _bgr_to_hex(hex_color: str) -> str:
        """Convert hex color to ASS BGR format."""
        hex_color = hex_color.lstrip("#")
        r = hex_color[0:2]
        g = hex_color[2:4]
        b = hex_color[4:6]
        # ASS uses BGR order
        return f"{b}{g}{r}".upper()

    @staticmethod
    def _alignment_to_ass(position: str, alignment: str) -> int:
        """Convert position/alignment to ASS alignment code."""
        # ASS alignment codes: 1=bottom-left, 2=bottom-center, 3=bottom-right,
        # 4=mid-left, 5=mid-center, 6=mid-right, 9=top-left, 10=top-center, 11=top-right
        pos_map = {"bottom": 1, "center": 4, "top": 7}
        base = pos_map.get(position, 1)

        align_map = {"left": 0, "center": 1, "right": 2}
        offset = align_map.get(alignment, 1)

        return base + offset

    @staticmethod
    def _escape_ass_text(text: str) -> str:
        """Escape special characters for ASS format."""
        # Escape backslashes and special characters
        text = text.replace("\\", "\\\\")
        text = text.replace("{", "\\{")
        text = text.replace("}", "\\}")
        # New line in ASS is \N
        text = text.replace("\n", "\\N")
        return text

    def _format_txt(self, track: SubtitleTrack) -> str:
        """Format as plain text."""
        lines = []
        for segment in track.segments:
            lines.append(segment.text)
        return "\n\n".join(lines)

    def _format_json(self, track: SubtitleTrack) -> str:
        """Format as JSON."""
        data = {
            "language": track.language,
            "segments": [
                {
                    "index": s.index,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "text": s.text,
                    "confidence": s.confidence,
                }
                for s in track.segments
            ],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    @staticmethod
    def parse_srt(content: str) -> SubtitleTrack:
        """Parse SRT format content into SubtitleTrack."""
        track = SubtitleTrack()
        segments = content.strip().split("\n\n")

        for segment_block in segments:
            lines = segment_block.strip().split("\n")
            if len(lines) < 3:
                continue

            try:
                index = int(lines[0])
                time_line = lines[1]
                text = "\n".join(lines[2:])

                # Parse timestamp: 00:00:00,000 --> 00:00:05,000
                if "-->" not in time_line:
                    continue
                start_str, end_str = time_line.split("-->")

                def parse_timestamp(ts: str) -> float:
                    ts = ts.strip()
                    if "," in ts:
                        time_part, ms = ts.split(",")
                    else:
                        time_part, ms = ts.split(".")
                    h, m, s = time_part.split(":")
                    return int(h) * 3600 + int(m) * 60 + float(s) + int(ms) / 1000

                start = parse_timestamp(start_str)
                end = parse_timestamp(end_str)

                segment = SubtitleSegment(
                    index=index, start_time=start, end_time=end, text=text
                )
                track.add_segment(segment)

            except (ValueError, IndexError):
                continue

        return track

    @staticmethod
    def parse_vtt(content: str) -> SubtitleTrack:
        """Parse WebVTT format content into SubtitleTrack."""
        # Remove WEBVTT header
        lines = content.split("\n")
        if lines and lines[0].startswith("WEBVTT"):
            lines = lines[1:]

        # Parse similar to SRT but with . instead of , for milliseconds
        track = SubtitleTrack()
        segments_data = []
        current_segment = []

        for line in lines:
            line = line.strip()
            if not line:
                if current_segment:
                    segments_data.append(current_segment)
                    current_segment = []
                continue

            current_segment.append(line)

        for seg_data in segments_data:
            if len(seg_data) < 2 or "-->" not in seg_data[1]:
                continue

            try:
                time_line = seg_data[1]
                start_str, end_str = time_line.split("-->")

                def parse_timestamp(ts: str) -> float:
                    ts = ts.strip()
                    if "." in ts:
                        time_part, ms = ts.split(".", 1)
                        ms = ms[:3]  # Limit to 3 digits
                    else:
                        time_part = ts
                        ms = "0"
                    parts = time_part.split(":")
                    if len(parts) == 3:
                        h, m, s = parts
                        return int(h) * 3600 + int(m) * 60 + float(s) + float(ms) / 1000
                    return 0.0

                start = parse_timestamp(start_str)
                end = parse_timestamp(end_str)
                text = "\n".join(seg_data[2:])

                segment = SubtitleSegment(
                    index=len(track.segments) + 1,
                    start_time=start,
                    end_time=end,
                    text=text,
                )
                track.add_segment(segment)

            except (ValueError, IndexError):
                continue

        return track
