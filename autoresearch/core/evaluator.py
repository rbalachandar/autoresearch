"""
Evaluator - Compares experiments and provides feedback.

The evaluator is responsible for:
1. Comparing experiment results
2. Providing feedback to the agent
3. Making decisions about which changes to keep
"""

from dataclasses import dataclass
from typing import Optional, Any
from enum import Enum

from .experimenter import ExperimentResult
from .historian import ExperimentRecord


class Decision(Enum):
    """Decision on whether to keep or discard a change"""

    KEEP = "keep"
    DISCARD = "discard"
    UNCERTAIN = "uncertain"


@dataclass
class Evaluation:
    """Result of evaluating an experiment"""

    decision: Decision
    metric: float
    is_better: bool
    is_best: bool
    improvement: float
    feedback: str
    confidence: float  # 0-1


class Evaluator:
    """
    Evaluates experiments and provides feedback to the agent.

    The evaluator compares new results against previous results
    and provides actionable feedback.
    """

    def __init__(self, higher_is_better: bool = True):
        self.higher_is_better = higher_is_better

    def evaluate(
        self,
        result: ExperimentResult,
        best_metric: float,
        previous_metric: Optional[float] = None,
    ) -> Evaluation:
        """
        Evaluate a single experiment result.

        Args:
            result: The experiment result to evaluate
            best_metric: The best metric seen so far
            previous_metric: The metric from the previous experiment

        Returns:
            An Evaluation with decision and feedback
        """
        metric = result.metric

        # Calculate improvements
        improvement = metric - best_metric
        if previous_metric is not None:
            prev_improvement = metric - previous_metric
        else:
            prev_improvement = improvement

        # Determine if this is better
        is_better = self._is_better(metric, best_metric)
        is_best = is_better

        # Make decision
        if result.error:
            decision = Decision.DISCARD
            feedback = f"Experiment failed with error: {result.error}"
            confidence = 1.0
        elif is_better:
            decision = Decision.KEEP
            feedback = self._generate_positive_feedback(improvement, prev_improvement)
            confidence = self._calculate_confidence(result)
        else:
            # Check if it's close enough to keep
            relative_diff = abs(improvement / best_metric) if best_metric != 0 else abs(improvement)
            if relative_diff < 0.01:  # Within 1%
                decision = Decision.UNCERTAIN
                feedback = f"Metric {metric:.4f} is very close to best {best_metric:.4f}. Consider running again."
                confidence = 0.5
            else:
                decision = Decision.DISCARD
                feedback = self._generate_negative_feedback(improvement, prev_improvement)
                confidence = self._calculate_confidence(result)

        return Evaluation(
            decision=decision,
            metric=metric,
            is_better=is_better,
            is_best=is_best,
            improvement=improvement,
            feedback=feedback,
            confidence=confidence,
        )

    def _is_better(self, new: float, old: float) -> bool:
        """Check if new metric is better than old"""
        if self.higher_is_better:
            return new > old
        return new < old

    def _generate_positive_feedback(self, improvement: float, prev_improvement: float) -> str:
        """Generate feedback for a successful experiment"""
        abs_improvement = abs(improvement)
        abs_prev = abs(prev_improvement)

        if abs_improvement > 0.1:
            return f"Excellent! Metric improved by {abs_improvement:.4f}. This change should be kept."
        elif abs_improvement > 0.01:
            return f"Good improvement of {abs_improvement:.4f}. Keep this change and build on it."
        else:
            direction = "increased" if self.higher_is_better else "decreased"
            return f"Metric {direction} by {abs_improvement:.6f}. Small but positive - keep exploring."

    def _generate_negative_feedback(self, improvement: float, prev_improvement: float) -> str:
        """Generate feedback for an unsuccessful experiment"""
        abs_improvement = abs(improvement)
        abs_prev = abs(prev_improvement)

        direction = "worse" if improvement < 0 else "not better"
        return (
            f"Metric is {direction} than best by {abs_improvement:.4f}. "
            f"Discard this change and try a different approach. "
            f"Consider what made the best experiment successful."
        )

    def _calculate_confidence(self, result: ExperimentResult) -> float:
        """Calculate confidence in the evaluation based on result quality"""
        confidence = 1.0

        # Lower confidence if there was an error
        if result.error:
            confidence = 0.9

        # Lower confidence if duration was very short (might be incomplete)
        if result.duration_seconds < 1:
            confidence *= 0.8

        # Lower confidence if output is empty
        if not result.output:
            confidence *= 0.9

        return max(0.0, min(1.0, confidence))


class MultiMetricEvaluator(Evaluator):
    """
    Evaluator that considers multiple metrics.

    Useful when experiments have multiple dimensions of success.
    """

    def __init__(
        self,
        metrics: dict[str, bool],  # metric_name: higher_is_better
        primary_metric: str,
        weights: Optional[dict[str, float]] = None,
    ):
        super().__init__(higher_is_better=metrics[primary_metric])
        self.metrics = metrics
        self.primary_metric = primary_metric
        self.weights = weights or {k: 1.0 for k in metrics}

    def evaluate_multi(
        self,
        result: ExperimentResult,
        best_metrics: dict[str, float],
    ) -> Evaluation:
        """
        Evaluate an experiment with multiple metrics.

        Args:
            result: The experiment result (metadata should contain all metrics)
            best_metrics: Dictionary of best metrics for each metric name

        Returns:
            An Evaluation with decision and feedback
        """
        # Extract metrics from result metadata
        metrics = result.metadata.get("metrics", {})
        if not metrics:
            # Fallback to single metric
            return self.evaluate(result, best_metrics.get(self.primary_metric, 0))

        # Calculate weighted score
        score = 0.0
        feedback_parts = []

        for metric_name, higher_is_better in self.metrics.items():
            if metric_name not in metrics:
                continue

            value = metrics[metric_name]
            best = best_metrics.get(metric_name, value)

            if higher_is_better:
                improvement = value - best
            else:
                improvement = best - value

            weight = self.weights.get(metric_name, 1.0)
            score += improvement * weight

            if metric_name == self.primary_metric:
                feedback_parts.append(f"{metric_name}: {value:.4f} (improvement: {improvement:.4f})")

        # Primary metric determines the main decision
        primary_value = metrics.get(self.primary_metric, result.metric)
        primary_best = best_metrics.get(self.primary_metric, result.metric)

        is_better = self._is_better(primary_value, primary_best)

        if is_better:
            decision = Decision.KEEP
            feedback = f"Improvement in primary metric. " + ", ".join(feedback_parts)
        else:
            decision = Decision.DISCARD
            feedback = f"Primary metric did not improve. " + ", ".join(feedback_parts)

        return Evaluation(
            decision=decision,
            metric=primary_value,
            is_better=is_better,
            is_best=is_better,
            improvement=score,
            feedback=feedback,
            confidence=0.8,
        )
