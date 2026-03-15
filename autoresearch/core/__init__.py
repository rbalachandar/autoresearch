"""
Core components of the AutoResearch framework.
"""

from .agent import ResearchAgent, AgentConfig
from .experimenter import Experimenter, Experiment, ExperimentResult, PythonExperimenter
from .historian import Historian, ExperimentRecord
from .evaluator import Evaluator, Evaluation, Decision, MultiMetricEvaluator
from .runner import ResearchRunner

__all__ = [
    "ResearchAgent",
    "AgentConfig",
    "Experimenter",
    "Experiment",
    "ExperimentResult",
    "PythonExperimenter",
    "Historian",
    "ExperimentRecord",
    "Evaluator",
    "Evaluation",
    "Decision",
    "MultiMetricEvaluator",
    "ResearchRunner",
]
