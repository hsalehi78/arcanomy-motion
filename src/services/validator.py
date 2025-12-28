"""Validation service for reel seed files.

Implements the validation checklist from docs/arcanomy-studio-integration/06-validation-checklist.md
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.utils.paths import inputs_dir, seed_path, claim_json_path, chart_json_path
from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class ValidationResult:
    """Result of validating a reel's seed files."""

    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.passed = False

    def add_warning(self, msg: str):
        self.warnings.append(msg)


# Valid chart types from docs/arcanomy-studio-integration/02-chart-schema.md
VALID_CHART_TYPES = [
    "bar",
    "horizontalBar",
    "stackedBar",
    "pie",
    "line",
    "scatter",
    "progress",
    "number",
]

# Required seed.md sections
REQUIRED_SEED_SECTIONS = [
    "# Hook",
    "# Core Insight",
    "# Visual Vibe",
    "# Script Structure",
    "# Key Data",
]

# Vague words to flag
VAGUE_WORDS = ["should", "might", "could", "maybe", "possibly"]


def validate_claim(claim_path: Path) -> ValidationResult:
    """Validate claim.json against schema.

    Checks:
    - Valid JSON syntax
    - Required fields present
    - claim_text under 25 words
    - audit_level is valid
    """
    result = ValidationResult(passed=True)

    if not claim_path.exists():
        result.add_error(f"claim.json not found at {claim_path}")
        return result

    try:
        with open(claim_path, "r", encoding="utf-8") as f:
            claim = json.load(f)
    except json.JSONDecodeError as e:
        result.add_error(f"claim.json: Invalid JSON syntax: {e}")
        return result

    # Required fields
    required_fields = ["claim_id", "claim_text", "supporting_data_ref", "audit_level"]
    for field_name in required_fields:
        if field_name not in claim:
            result.add_error(f"claim.json: Missing required field '{field_name}'")

    # claim_text word count
    claim_text = claim.get("claim_text", "")
    word_count = len(claim_text.split())
    if word_count > 25:
        result.add_error(
            f"claim.json: claim_text exceeds 25 words (has {word_count})"
        )

    # audit_level validation
    audit_level = claim.get("audit_level", "")
    if audit_level and audit_level not in ("basic", "strict"):
        result.add_error(
            f"claim.json: audit_level must be 'basic' or 'strict', got '{audit_level}'"
        )

    return result


def validate_seed(seed_file: Path) -> ValidationResult:
    """Validate seed.md structure and content.

    Checks:
    - All 5 required sections present
    - Hook under 15 words
    - Core Insight under 50 words
    - Script Structure has TRUTH, MISTAKE, FIX
    - No vague language
    - No em-dashes
    """
    result = ValidationResult(passed=True)

    if not seed_file.exists():
        result.add_error(f"seed.md not found at {seed_file}")
        return result

    content = seed_file.read_text(encoding="utf-8")

    # Check required sections
    for section in REQUIRED_SEED_SECTIONS:
        if section not in content:
            result.add_error(f"seed.md: Missing required section '{section}'")

    # Extract and validate Hook
    hook_match = re.search(r"# Hook\n(.+?)(?=\n#|\Z)", content, re.DOTALL)
    if hook_match:
        hook = hook_match.group(1).strip()
        word_count = len(hook.split())
        if word_count > 15:
            result.add_error(f"seed.md: Hook exceeds 15 words (has {word_count})")
    else:
        result.add_error("seed.md: Could not extract Hook section")

    # Extract and validate Core Insight
    insight_match = re.search(r"# Core Insight\n(.+?)(?=\n#|\Z)", content, re.DOTALL)
    if insight_match:
        insight = insight_match.group(1).strip()
        word_count = len(insight.split())
        if word_count > 50:
            result.add_error(
                f"seed.md: Core Insight exceeds 50 words (has {word_count})"
            )

    # Check Script Structure for TRUTH, MISTAKE, FIX
    script_match = re.search(r"# Script Structure\n(.+?)(?=\n#|\Z)", content, re.DOTALL)
    if script_match:
        script = script_match.group(1).upper()
        if "TRUTH" not in script:
            result.add_error("seed.md: Script Structure missing TRUTH")
        if "MISTAKE" not in script:
            result.add_error("seed.md: Script Structure missing MISTAKE")
        if "FIX" not in script:
            result.add_error("seed.md: Script Structure missing FIX")

    # Check for vague language
    content_lower = content.lower()
    for word in VAGUE_WORDS:
        if word in content_lower:
            result.add_warning(f"seed.md: Contains vague language: '{word}'")

    # Check for em-dashes
    if "—" in content:
        result.add_warning("seed.md: Contains em-dashes (—), use commas or periods")

    return result


def validate_chart(chart_path: Path) -> ValidationResult:
    """Validate chart.json against schema.

    Checks:
    - Valid JSON syntax
    - chartType is valid
    - data array has 2-6 items (for non-number charts)
    - Labels under 10 characters
    - Background is #00FF00 for green screen
    - Animation duration is reasonable
    """
    result = ValidationResult(passed=True)

    if not chart_path.exists():
        # chart.json is optional
        return result

    try:
        with open(chart_path, "r", encoding="utf-8") as f:
            chart = json.load(f)
    except json.JSONDecodeError as e:
        result.add_error(f"chart.json: Invalid JSON syntax: {e}")
        return result

    # chartType validation
    chart_type = chart.get("chartType")
    if chart_type not in VALID_CHART_TYPES:
        result.add_error(
            f"chart.json: Invalid chartType '{chart_type}'. "
            f"Must be one of: {', '.join(VALID_CHART_TYPES)}"
        )

    # Data array validation (not for number counter)
    if chart_type != "number":
        data = chart.get("data", [])
        if len(data) < 2:
            result.add_error("chart.json: data array must have at least 2 items")
        if len(data) > 6:
            result.add_warning(
                f"chart.json: data array has {len(data)} items "
                "(recommended max 6 for readability)"
            )

        # Label length validation
        for i, item in enumerate(data):
            label = item.get("label", "")
            if len(label) > 10:
                result.add_error(
                    f"chart.json: data[{i}].label '{label}' exceeds 10 characters"
                )

    # Background color validation
    bg_color = chart.get("background", {}).get("color", "")
    if bg_color and bg_color != "#00FF00":
        result.add_warning(
            f"chart.json: background.color is '{bg_color}', "
            "should be '#00FF00' for green screen"
        )

    # Animation duration validation
    anim_duration = chart.get("animation", {}).get("duration", 30)
    if anim_duration < 15 or anim_duration > 60:
        result.add_warning(
            f"chart.json: animation.duration {anim_duration} is unusual "
            "(expected 15-60 frames)"
        )

    return result


def validate_reel(reel_path: Path) -> ValidationResult:
    """Validate all seed files for a reel.

    Args:
        reel_path: Path to the reel folder

    Returns:
        Combined ValidationResult from all file validations
    """
    result = ValidationResult(passed=True)

    # Validate claim.json
    claim_result = validate_claim(claim_json_path(reel_path))
    result.errors.extend(claim_result.errors)
    result.warnings.extend(claim_result.warnings)
    if not claim_result.passed:
        result.passed = False

    # Validate seed.md
    seed_result = validate_seed(seed_path(reel_path))
    result.errors.extend(seed_result.errors)
    result.warnings.extend(seed_result.warnings)
    if not seed_result.passed:
        result.passed = False

    # Validate chart.json (if present)
    chart_file = chart_json_path(reel_path)
    if chart_file.exists():
        chart_result = validate_chart(chart_file)
        result.errors.extend(chart_result.errors)
        result.warnings.extend(chart_result.warnings)
        if not chart_result.passed:
            result.passed = False

    return result
