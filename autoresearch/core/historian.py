"""
Historian - Tracks all experiments and their results.

The historian maintains a complete history of all experiments run,
including the changes made, results, and a leaderboard of best experiments.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import json
from datetime import datetime


@dataclass
class ExperimentRecord:
    """A complete record of a single experiment"""

    number: int
    timestamp: str
    description: str
    metric: float
    file_snapshot: str  # The content of the target file
    output: str = ""
    error: Optional[str] = None
    duration_seconds: float = 0.0
    is_better: bool = False
    is_best: bool = False
    change_summary: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "number": self.number,
            "timestamp": self.timestamp,
            "description": self.description,
            "metric": self.metric,
            "file_snapshot": self.file_snapshot,
            "output": self.output,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "is_better": self.is_better,
            "is_best": self.is_best,
            "change_summary": self.change_summary,
        }


class Historian:
    """
    Tracks and manages the complete history of all experiments.

    The historian:
    1. Records every experiment with full details
    2. Maintains a leaderboard of best experiments
    3. Provides analysis and insights
    4. Enables rollback to any previous state
    """

    def __init__(self, output_dir: Path, metric_higher_is_better: bool = True):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = output_dir / "history.json"
        self.best_metric = float("-inf") if metric_higher_is_better else float("inf")
        self.metric_higher_is_better = metric_higher_is_better

        self.records: list[ExperimentRecord] = []
        self.leaderboard: list[ExperimentRecord] = []

        self._load_history()

    def record_experiment(
        self,
        experiment: Any,
        result: Any,
        file_content: str,
        change_summary: str = "",
    ) -> ExperimentRecord:
        """
        Record a new experiment.

        Args:
            experiment: The experiment configuration
            result: The experiment result
            file_content: The content of the target file
            change_summary: Summary of what was changed

        Returns:
            The created ExperimentRecord
        """
        is_better = self._is_better(result.metric)
        is_best = is_better and self._is_best(result.metric)

        record = ExperimentRecord(
            number=experiment.number,
            timestamp=datetime.now().isoformat(),
            description=experiment.description,
            metric=result.metric,
            file_snapshot=file_content,
            output=result.output,
            error=result.error,
            duration_seconds=result.duration_seconds,
            is_better=is_better,
            is_best=is_best,
            change_summary=change_summary,
        )

        self.records.append(record)

        if is_best:
            self.best_metric = result.metric
            self.leaderboard.insert(0, record)
        else:
            # Add to leaderboard in sorted position
            inserted = False
            for i, existing in enumerate(self.leaderboard):
                if self._is_better(result.metric, existing.metric):
                    self.leaderboard.insert(i, record)
                    inserted = True
                    break
            if not inserted and len(self.leaderboard) < 10:
                self.leaderboard.append(record)

        self._save_history()
        return record

    def get_best(self) -> Optional[ExperimentRecord]:
        """Get the best experiment so far"""
        if self.leaderboard:
            return self.leaderboard[0]
        return None

    def get_file_at(self, experiment_number: int) -> Optional[str]:
        """Get the file content at a specific experiment"""
        for record in self.records:
            if record.number == experiment_number:
                return record.file_snapshot
        return None

    def get_recent_results(self, n: int = 5) -> list[ExperimentRecord]:
        """Get the most recent n results"""
        return self.records[-n:]

    def get_leaderboard(self, n: int = 10) -> list[ExperimentRecord]:
        """Get the top n experiments"""
        return self.leaderboard[:n]

    def generate_report(self) -> str:
        """Generate a human-readable report of all experiments"""
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel

        console = Console(record=True)
        output = []

        # Summary
        best = self.get_best()
        if best:
            summary = f"""
# AutoResearch Summary

Total Experiments: {len(self.records)}
Best Metric: {best.metric:.4f} (Experiment #{best.number})
Total Duration: {sum(r.duration_seconds for r in self.records):.1f}s
"""
        else:
            summary = f"""
# AutoResearch Summary

Total Experiments: {len(self.records)}
No successful experiments yet.
"""

        output.append(summary)

        # Leaderboard table
        table = Table(title="Leaderboard (Top 10)")
        table.add_column("#", style="dim")
        table.add_column("Metric", style="bold cyan")
        table.add_column("Duration", style="dim")
        table.add_column("Description")

        for i, record in enumerate(self.get_leaderboard(10), 1):
            table.add_row(
                str(record.number),
                f"{record.metric:.4f}",
                f"{record.duration_seconds:.1f}s",
                record.description[:50] + "..." if len(record.description) > 50 else record.description,
            )

        console.print(table)
        output.append(console.export_text())

        # Recent results
        if len(self.records) > 0:
            recent_table = Table(title="Recent Experiments")
            recent_table.add_column("#", style="dim")
            recent_table.add_column("Metric")
            recent_table.add_column("Change")

            for record in self.get_recent_results(5):
                icon = "🟢" if record.is_better else "🔴"
                recent_table.add_row(
                    f"{icon} {record.number}",
                    f"{record.metric:.4f}",
                    record.change_summary[:40] + "..."
                    if len(record.change_summary) > 40
                    else record.change_summary,
                )

            console.print(recent_table)
            output.append(console.export_text())

        return "\n\n".join(output)

    def _is_better(self, new_metric: float, old_metric: Optional[float] = None) -> bool:
        """Check if a new metric is better than the old one"""
        if old_metric is None:
            old_metric = self.best_metric

        if self.metric_higher_is_better:
            return new_metric > old_metric
        return new_metric < old_metric

    def _is_best(self, metric: float) -> bool:
        """Check if this is the best metric so far"""
        return self._is_better(metric)

    def _load_history(self):
        """Load history from disk"""
        if self.history_file.exists():
            try:
                data = json.loads(self.history_file.read_text())
                self.records = [ExperimentRecord(**r) for r in data.get("records", [])]
                self.leaderboard = [
                    ExperimentRecord(**r) for r in data.get("leaderboard", [])
                ]
                if self.leaderboard:
                    self.best_metric = self.leaderboard[0].metric
            except Exception as e:
                print(f"Warning: Could not load history: {e}")

    def _save_history(self):
        """Save history to disk"""
        data = {
            "records": [r.to_dict() for r in self.records],
            "leaderboard": [r.to_dict() for r in self.leaderboard],
            "best_metric": self.best_metric,
        }
        self.history_file.write_text(json.dumps(data, indent=2))
