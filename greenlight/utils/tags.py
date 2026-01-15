"""
Simple tag extraction utility.

No consensus voting, no multi-agent validation - just regex extraction.
"""

import re
from typing import Optional


def extract_tags(text: str) -> dict[str, list[str]]:
    """
    Extract tags from text.

    Tags are in format: [PREFIX_NAME] or PREFIX_NAME
    Prefixes: CHAR_, LOC_, PROP_, CONCEPT_, EVENT_

    Returns:
        Dict with keys: characters, locations, props, concepts, events
    """
    tags = {
        "characters": [],
        "locations": [],
        "props": [],
        "concepts": [],
        "events": [],
    }

    # Pattern matches both [TAG] and bare TAG formats
    pattern = r'\[?(CHAR_[A-Z0-9_]+|LOC_[A-Z0-9_]+|PROP_[A-Z0-9_]+|CONCEPT_[A-Z0-9_]+|EVENT_[A-Z0-9_]+)\]?'

    matches = re.findall(pattern, text, re.IGNORECASE)

    for match in matches:
        tag = match.upper()
        if tag.startswith("CHAR_"):
            if tag not in tags["characters"]:
                tags["characters"].append(tag)
        elif tag.startswith("LOC_"):
            if tag not in tags["locations"]:
                tags["locations"].append(tag)
        elif tag.startswith("PROP_"):
            if tag not in tags["props"]:
                tags["props"].append(tag)
        elif tag.startswith("CONCEPT_"):
            if tag not in tags["concepts"]:
                tags["concepts"].append(tag)
        elif tag.startswith("EVENT_"):
            if tag not in tags["events"]:
                tags["events"].append(tag)

    return tags


def create_tag(prefix: str, name: str) -> str:
    """
    Create a properly formatted tag.

    Args:
        prefix: Tag prefix (CHAR, LOC, PROP, CONCEPT, EVENT)
        name: The name to convert to tag format

    Returns:
        Formatted tag string (e.g., "CHAR_JOHN_DOE")
    """
    # Clean the name
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    clean_name = clean_name.upper().replace(' ', '_')

    # Add prefix if not present
    prefix = prefix.upper()
    if not prefix.endswith('_'):
        prefix += '_'

    return f"{prefix}{clean_name}"


def get_tag_display_name(tag: str) -> str:
    """
    Convert a tag to a display-friendly name.

    Args:
        tag: Tag string (e.g., "CHAR_JOHN_DOE")

    Returns:
        Display name (e.g., "John Doe")
    """
    # Remove prefix
    for prefix in ["CHAR_", "LOC_", "PROP_", "CONCEPT_", "EVENT_"]:
        if tag.startswith(prefix):
            tag = tag[len(prefix):]
            break

    # Convert underscores to spaces and title case
    return tag.replace('_', ' ').title()
