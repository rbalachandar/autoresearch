"""
AutoResearch - General-purpose autonomous research framework for AI agents.

Inspired by Andrej Karpathy's autoresearch: https://github.com/karpathy/autoresearch

The core idea: AI agents autonomously experiment, iterate, and improve systems
while humans only set the research agenda via `program.md`.
"""

__version__ = "0.1.0"

from autoresearch.core.agent import ResearchAgent, AgentConfig
from autoresearch.core.experimenter import Experimenter, Experiment, ExperimentResult
from autoresearch.core.historian import Historian
from autoresearch.core.evaluator import Evaluator
from autoresearch.core.runner import ResearchRunner

__all__ = [
    "ResearchAgent",
    "AgentConfig",
    "Experimenter",
    "Experiment",
    "ExperimentResult",
    "Historian",
    "Evaluator",
    "ResearchRunner",
]
