#!/usr/bin/env python3
"""
Validate tone_of_voice.yaml configuration file.
Usage: python validate_tone.py config/tone_of_voice.yaml
"""

import sys
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError, field_validator


class ToneProfile(BaseModel):
    tone_id: str
    display_name: str
    language: str
    persona: dict
    structure_preferences: dict
    platform_overrides: dict = {}

    @field_validator("tone_id")
    @classmethod
    def validate_tone_id(cls, v: str) -> str:
        if not v or not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("tone_id must be alphanumeric with underscores/hyphens only")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if not v or len(v) < 2:
            raise ValueError("language must be a valid language code (e.g., pt-BR, en-US)")
        return v

    @field_validator("persona")
    @classmethod
    def validate_persona(cls, v: dict) -> dict:
        required = ["archetype", "traits", "forbidden_words", "preferred_phrases"]
        for field in required:
            if field not in v:
                raise ValueError(f"persona missing required field: {field}")
        if not isinstance(v["traits"], list) or len(v["traits"]) < 3:
            raise ValueError("persona.traits must be a list with at least 3 items")
        if not isinstance(v["forbidden_words"], list):
            raise ValueError("persona.forbidden_words must be a list")
        if not isinstance(v["preferred_phrases"], list):
            raise ValueError("persona.preferred_phrases must be a list")
        return v

    @field_validator("structure_preferences")
    @classmethod
    def validate_structure_prefs(cls, v: dict) -> dict:
        required = ["hook_style", "cta_style", "emoji_usage", "line_break_density"]
        for field in required:
            if field not in v:
                raise ValueError(f"structure_preferences missing required field: {field}")

        valid_hook_styles = ["curiosity", "contrarian", "pain_point", "social_proof", "bold_statement", "contrarian_insight", "visual_curiosity"]
        valid_cta_styles = ["question_driven", "direct_command", "resource_link", "challenge"]
        valid_emoji = ["none", "minimal", "moderate", "heavy"]
        valid_line_breaks = ["low", "medium", "high"]

        if v["hook_style"] not in valid_hook_styles:
            raise ValueError(f"hook_style must be one of: {valid_hook_styles}")
        if v["cta_style"] not in valid_cta_styles:
            raise ValueError(f"cta_style must be one of: {valid_cta_styles}")
        if v["emoji_usage"] not in valid_emoji:
            raise ValueError(f"emoji_usage must be one of: {valid_emoji}")
        if v["line_break_density"] not in valid_line_breaks:
            raise ValueError(f"line_break_density must be one of: {valid_line_breaks}")
        return v

    @field_validator("platform_overrides")
    @classmethod
    def validate_platform_overrides(cls, v: dict) -> dict:
        valid_platforms = ["instagram", "tiktok", "linkedin", "twitter", "youtube"]
        valid_override_keys = ["hook_style", "cta_style", "emoji_usage", "line_break_density"]
        for platform, overrides in v.items():
            if platform not in valid_platforms:
                raise ValueError(f"Unknown platform in overrides: {platform}")
            for key in overrides:
                if key not in valid_override_keys:
                    raise ValueError(f"Invalid override key: {key}")
        return v


def validate_tone_file(filepath: Path) -> bool:
    """Validate a tone configuration file."""
    print(f"🔍 Validating: {filepath}")

    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ YAML parse error: {e}")
        return False

    try:
        profile = ToneProfile(**data)
        print(f"✅ Valid tone profile: {profile.tone_id} ({profile.display_name})")
        print(f"   Language: {profile.language}")
        print(f"   Archetype: {profile.persona['archetype']}")
        print(f"   Traits: {', '.join(profile.persona['traits'])}")
        print(f"   Forbidden words: {len(profile.persona['forbidden_words'])}")
        print(f"   Hook style: {profile.structure_preferences['hook_style']}")
        print(f"   CTA style: {profile.structure_preferences['cta_style']}")
        print(f"   Emoji usage: {profile.structure_preferences['emoji_usage']}")
        print(f"   Line breaks: {profile.structure_preferences['line_break_density']}")
        if profile.platform_overrides:
            print(f"   Platform overrides: {', '.join(profile.platform_overrides.keys())}")
        return True
    except ValidationError as e:
        print(f"❌ Validation failed:")
        for error in e.errors():
            loc = " → ".join(str(x) for x in error["loc"])
            print(f"   • {loc}: {error['msg']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_tone.py <tone_config.yaml>")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    success = validate_tone_file(filepath)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()