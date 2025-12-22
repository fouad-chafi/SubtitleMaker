"""Subtitle style endpoints."""

import yaml
from pathlib import Path
from fastapi import APIRouter

from ..schemas import SubtitleStyleResponse

router = APIRouter()


@router.get("/styles", response_model=SubtitleStyleResponse)
async def get_styles() -> SubtitleStyleResponse:
    """
    Get available subtitle style presets.
    """
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "styles.yaml"

    if not config_path.exists():
        return SubtitleStyleResponse(styles=[])

    with config_path.open("r") as f:
        config = yaml.safe_load(f)

    styles = []
    for style_name, style_data in config.get("styles", {}).items():
        styles.append({
            "id": style_name,
            "name": style_data.get("name", style_name),
            **{k: v for k, v in style_data.items() if k != "name"},
        })

    return SubtitleStyleResponse(styles=styles)


@router.get("/languages")
async def get_languages():
    """
    Get supported languages for transcription.
    """
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "languages.yaml"

    if not config_path.exists():
        return {"languages": {}}

    with config_path.open("r") as f:
        config = yaml.safe_load(f)

    languages = {}
    for lang_code, lang_data in config.get("languages", {}).items():
        if isinstance(lang_data, dict):
            languages[lang_code] = lang_data.get("name", lang_code)
        else:
            languages[lang_code] = lang_code

    return {"languages": languages}
