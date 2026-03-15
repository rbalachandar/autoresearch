"""
Experimenter - Runs experiments and captures metrics.

The experimenter is responsible for:
1. Running the target file (training script, evaluation script, etc.)
2. Capturing the output metrics
3. Returning results in a structured format
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional
import subprocess
import sys


@dataclass
class ExperimentResult:
    """Result of a single experiment run"""

    experiment_number: int
    metric: float  # The primary metric (higher is better by default)
    metadata: dict[str, Any] = field(default_factory=dict)
    output: str = ""
    error: Optional[str] = None
    duration_seconds: float = 0.0
    timestamp: str = ""

    # For comparison
    is_better: bool = False
    is_best: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "experiment_number": self.experiment_number,
            "metric": self.metric,
            "metadata": self.metadata,
            "output": self.output,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp,
            "is_better": self.is_better,
            "is_best": self.is_best,
        }


@dataclass
class Experiment:
    """A single experiment configuration"""

    number: int
    description: str


class Experimenter:
    """
    Runs experiments and captures results.

    The experimenter handles the actual execution of experiments,
    whether that's running a Python script, evaluating a prompt,
    or any other domain-specific task.
    """

    def __init__(
        self,
        target_file: Path,
        run_command: Optional[list[str]] = None,
        metric_parser: Optional[Callable[[str], float]] = None,
        metric_higher_is_better: bool = True,
    ):
        self.target_file = target_file
        self.run_command = run_command or [sys.executable, str(target_file)]
        self.metric_parser = metric_parser or self._default_metric_parser
        self.metric_higher_is_better = metric_higher_is_better

    def run(self, experiment: Experiment) -> ExperimentResult:
        """
        Run a single experiment.

        Args:
            experiment: The experiment configuration

        Returns:
            ExperimentResult with metric and metadata
        """
        import time

        start_time = time.time()
        from datetime import datetime

        try:
            # Run the experiment
            result = subprocess.run(
                self.run_command,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                cwd=self.target_file.parent,
            )

            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr

            # Parse the metric from output
            metric = self.metric_parser(output)

            duration = time.time() - start_time

            return ExperimentResult(
                experiment_number=experiment.number,
                metric=metric,
                output=output,
                duration_seconds=duration,
                timestamp=datetime.now().isoformat(),
                metadata={"description": experiment.description},
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ExperimentResult(
                experiment_number=experiment.number,
                metric=float("-inf") if self.metric_higher_is_better else float("inf"),
                output="",
                error="Experiment timed out after 10 minutes",
                duration_seconds=duration,
                timestamp=datetime.now().isoformat(),
                metadata={"description": experiment.description},
            )

        except Exception as e:
            duration = time.time() - start_time
            return ExperimentResult(
                experiment_number=experiment.number,
                metric=float("-inf") if self.metric_higher_is_better else float("inf"),
                output="",
                error=str(e),
                duration_seconds=duration,
                timestamp=datetime.now().isoformat(),
                metadata={"description": experiment.description},
            )

    def _default_metric_parser(self, output: str) -> float:
        """
        Default metric parser - looks for lines like:
        METRIC: 0.123
        or
        metric: 0.123
        """
        import re

        # Look for METRIC: <value> pattern
        patterns = [
            r"^METRIC:\s*([-\d.]+)",
            r"^metric:\s*([-\d.]+)",
            r"^RESULT:\s*([-\d.]+)",
            r"^result:\s*([-\d.]+)",
        ]

        for line in output.split("\n"):
            for pattern in patterns:
                match = re.match(pattern, line.strip())
                if match:
                    try:
                        return float(match.group(1))
                    except ValueError:
                        continue

        # If no metric found, raise an error
        raise ValueError(
            f"Could not find metric in output. Expected pattern like 'METRIC: 0.123'. "
            f"Output:\n{output[:500]}"
        )


class PythonExperimenter(Experimenter):
    """
    Experimenter for Python-based experiments.

    Provides additional utilities like importing and running functions directly.
    """

    def __init__(
        self,
        target_file: Path,
        function_name: str = "run_experiment",
        metric_higher_is_better: bool = True,
    ):
        super().__init__(target_file, metric_higher_is_better=metric_higher_is_better)
        self.function_name = function_name
        self.module = None

    def load_module(self):
        """Load the target file as a Python module"""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "target_module", self.target_file
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def run_function(self, experiment_number: int = 0, **kwargs) -> ExperimentResult:
        """
        Run the experiment by calling a function directly.

        This is faster than subprocess and allows for better error handling.
        """
        import time
        from datetime import datetime

        if self.module is None:
            self.load_module()

        start_time = time.time()

        try:
            func = getattr(self.module, self.function_name)
            result = func(**kwargs)

            # Result can be a float (metric) or a dict
            if isinstance(result, dict):
                metric = result.get("metric", result.get("value", 0))
                metadata = {k: v for k, v in result.items() if k not in ["metric", "value"]}
            else:
                metric = float(result)
                metadata = {}

            duration = time.time() - start_time

            return ExperimentResult(
                experiment_number=experiment_number,
                metric=metric,
                metadata=metadata,
                duration_seconds=duration,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            duration = time.time() - start_time
            return ExperimentResult(
                experiment_number=experiment_number,
                metric=float("-inf") if self.metric_higher_is_better else float("inf"),
                error=str(e),
                duration_seconds=duration,
                timestamp=datetime.now().isoformat(),
            )
