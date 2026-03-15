"""
Templates for different research domains.

Each template provides a specialized implementation of the
autoresearch framework for a specific domain.
"""

from autoresearch.templates.prompt import PromptExperimenter, create_prompt_template

__all__ = [
    "PromptExperimenter",
    "create_prompt_template",
]
