"""
Research Runner - Orchestrates the autonomous research process.

The runner coordinates the agent, experimenter, historian, and evaluator
to conduct autonomous research experiments.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from .agent import ResearchAgent, AgentConfig
from .experimenter import Experimenter, Experiment, ExperimentResult
from .historian import Historian
from .evaluator import Evaluator, Decision


class ResearchRunner:
    """
    Orchestrates autonomous research experiments.

    The runner:
    1. Sets up the research environment
    2. Runs experiments in a loop
    3. Coordinates between agent, experimenter, historian, and evaluator
    4. Reports progress and final results
    """

    def __init__(
        self,
        work_dir: Path,
        target_file: str,
        program_file: str = "program.md",
        agent_config: Optional[AgentConfig] = None,
        metric_higher_is_better: bool = True,
    ):
        self.work_dir = Path(work_dir)
        self.target_file = self.work_dir / target_file
        self.program_file = self.work_dir / program_file
        self.output_dir = self.work_dir / ".autoresearch"
        self.metric_higher_is_better = metric_higher_is_better

        # Validate files exist
        if not self.target_file.exists():
            raise FileNotFoundError(f"Target file not found: {self.target_file}")
        if not self.program_file.exists():
            raise FileNotFoundError(f"Program file not found: {self.program_file}")

        # Initialize components
        base_config = agent_config or AgentConfig()
        self.agent_config = AgentConfig(
            **base_config.model_dump(),
            metric_higher_is_better=metric_higher_is_better,
        )
        self.agent = ResearchAgent(
            config=self.agent_config,
            target_file=self.target_file,
            program_file=self.program_file,
            output_dir=self.output_dir,
        )

        self.experimenter = Experimenter(
            target_file=self.target_file,
            metric_higher_is_better=metric_higher_is_better,
        )

        self.historian = Historian(
            output_dir=self.output_dir,
            metric_higher_is_better=metric_higher_is_better,
        )

        self.evaluator = Evaluator(higher_is_better=metric_higher_is_better)

    def run(self, max_experiments: Optional[int] = None) -> Historian:
        """
        Run the autonomous research loop.

        Args:
            max_experiments: Maximum number of experiments to run (overrides agent config)

        Returns:
            The historian with all experiment records
        """
        from rich.console import Console
        from rich.panel import Panel

        console = Console()
        started_at = datetime.now()

        console.print(f"[bold cyan]Starting AutoResearch[/bold cyan]")
        console.print(f"  Work directory: {self.work_dir}")
        console.print(f"  Target file: {self.target_file}")
        console.print(f"  Program file: {self.program_file}")
        console.print(f"  Agent: {self.agent_config.provider}/{self.agent_config.model}")
        console.print(f"  Metric direction: {'higher is better' if self.metric_higher_is_better else 'lower is better'}")
        console.print("")

        experiment_number = 0
        last_file_content = self.agent.read_target()
        last_result = None

        while self.agent.should_continue():
            # Check max_experiments override
            if max_experiments and experiment_number >= max_experiments:
                console.print(f"\n[dim]Reached maximum experiments override ({max_experiments})[/dim]")
                break

            experiment_number += 1

            # Propose changes
            console.print(
                f"[dim]Experiment #{experiment_number}:[/dim] Proposing changes..."
            )

            context = {
                "previous_results": [
                    {"metric": r.metric, "description": r.description}
                    for r in self.historian.get_recent_results(5)
                ],
                "last_change": self.historian.records[-1].change_summary
                if self.historian.records
                else "Initial state",
                "last_result": last_result,
                "best_metric": self.historian.best_metric,
            }

            try:
                new_content = self.agent.propose_changes(context)
            except Exception as e:
                console.print(f"[red]Error proposing changes: {e}[/red]")
                break

            # Write the changes
            self.agent.write_target(new_content)

            # Summarize changes once (reuse for both experiment and record)
            change_summary = self._summarize_changes(last_file_content, new_content)

            # Create experiment
            experiment = Experiment(
                number=experiment_number,
                description=change_summary,
            )

            # Run experiment
            console.print(
                f"[dim]Experiment #{experiment_number}:[/dim] Running experiment..."
            )

            result = self.experimenter.run(experiment)

            # Evaluate
            evaluation = self.evaluator.evaluate(
                result=result,
                best_metric=self.historian.best_metric,
                previous_metric=last_result.metric if last_result else None,
            )

            # Update result with evaluation
            result.is_better = evaluation.is_better
            result.is_best = evaluation.is_best

            # Record in historian
            self.historian.record_experiment(
                experiment=experiment,
                result=result,
                file_content=new_content,
                change_summary=change_summary,
            )

            # Display result
            icon = "🟢" if evaluation.is_better else "🔴"
            console.print(
                f"{icon} [bold]Experiment #{experiment_number}[/bold]: "
                f"Metric = {result.metric:.4f} "
                f"(Best: {self.historian.best_metric:.4f}) "
                f"({result.duration_seconds:.1f}s)"
            )

            if evaluation.feedback:
                console.print(f"    [dim]{evaluation.feedback}[/dim]")

            # Decide whether to keep or discard
            if evaluation.decision == Decision.DISCARD:
                # Revert to previous best
                best_record = self.historian.get_best()
                if best_record:
                    console.print(f"    [dim]Reverting to experiment #{best_record.number}[/dim]")
                    self.agent.write_target(best_record.file_snapshot)
                    last_file_content = best_record.file_snapshot
                else:
                    self.agent.write_target(last_file_content)
            elif evaluation.decision == Decision.UNCERTAIN:
                # For uncertain results, keep but note it
                console.print(f"    [dim]⚠️  Result uncertain, keeping changes[/dim]")
                last_file_content = new_content
            else:
                # KEEP decision - keep the changes
                last_file_content = new_content

            last_result = result

        # Check for stop reason and display
        stop_reason = self.agent.get_stop_reason()
        if stop_reason:
            console.print(f"\n[dim]Stopping: {stop_reason}[/dim]")

        # Final report
        elapsed = (datetime.now() - started_at).total_seconds()

        # Handle case where best_metric is still infinity (no successful experiments)
        best_display = self.historian.best_metric
        if abs(best_display) == float("inf"):
            best_display_str = "N/A (no successful experiments)"
        else:
            best_display_str = f"{best_display:.4f}"

        console.print("")
        console.print(
            Panel(
                f"[bold]Research Complete[/bold]\n\n"
                f"Total experiments: {experiment_number}\n"
                f"Best metric: {best_display_str}\n"
                f"Duration: {elapsed:.1f}s\n"
                f"Results saved to: {self.output_dir}",
                title="Summary",
            )
        )

        # Generate and save report
        report = self.historian.generate_report()
        report_file = self.output_dir / "report.txt"
        report_file.write_text(report)
        console.print(f"\nReport saved to: {report_file}")

        return self.historian

    def _summarize_changes(self, old: str, new: str) -> str:
        """
        Generate a brief summary of changes between two file contents.

        Args:
            old: The old file content
            new: The new file content

        Returns:
            A summary string describing the changes
        """
        import difflib

        diff = list(difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            lineterm="",
        ))

        if not diff:
            return "No changes"

        # Count added and removed lines
        added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        # Extract a sample of changed content
        changes = []
        for line in diff:
            if line.startswith("+") and not line.startswith("+++"):
                changes.append(line[1:].strip())
            if len(changes) >= 3:
                break

        summary = f"{added} additions, {removed} deletions"
        if changes:
            sample = " ".join(changes[:50])  # First 50 chars
            summary += f": {sample}..."

        return summary
