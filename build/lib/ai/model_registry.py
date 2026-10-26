"""STARFALL Model Registry and Licensing Metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ModelMetadata:
    identifier: str
    display_name: str
    parameter_size: str
    recommended_ram_gb: int
    license_type: str
    license_notes: str
    description: str


SUPPORTED_MODELS: Dict[str, ModelMetadata] = {
    "gemma4:e2b": ModelMetadata(
        identifier="gemma4:e2b",
        display_name="Gemma 4 (E2B)",
        parameter_size="~2B effective",
        recommended_ram_gb=8,
        license_type="Gemma Open-Weight Terms of Use",
        license_notes="Governed by Google's applicable Gemma Terms of Use. Permitted for local development, research, and non-commercial/commercial usage within terms. Note: Not OSI-approved open source.",
        description="Lightweight local model ideal for fast, responsive tactical JSON generation.",
    ),
    "gemma4:e4b": ModelMetadata(
        identifier="gemma4:e4b",
        display_name="Gemma 4 (E4B)",
        parameter_size="~4B effective",
        recommended_ram_gb=16,
        license_type="Gemma Open-Weight Terms of Use",
        license_notes="Governed by Google's applicable Gemma Terms of Use. Permitted for local development and deployment under Gemma terms.",
        description="Higher-capacity reasoning model providing deeper behavioral pattern correlation.",
    ),
    "llama3.2:latest": ModelMetadata(
        identifier="llama3.2:latest",
        display_name="Llama 3.2 (3B)",
        parameter_size="3B",
        recommended_ram_gb=8,
        license_type="Llama 3.2 Community License",
        license_notes="Alternative local model adapter for machines with standard memory footprints.",
        description="Alternative compatible local model for arcade tactical generation.",
    ),
}


def get_model_info(identifier: str) -> Optional[ModelMetadata]:
    """Retrieve metadata and license info for a model."""
    return SUPPORTED_MODELS.get(identifier)


def list_supported_models() -> List[ModelMetadata]:
    """List all officially documented model adapters."""
    return list(SUPPORTED_MODELS.values())
