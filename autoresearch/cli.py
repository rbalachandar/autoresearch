"""
Command-line interface for AutoResearch.
"""

import click
from pathlib import Path
from rich.console import Console

from .core import ResearchRunner, AgentConfig


console = Console()


@click.group()
def main():
    """AutoResearch - General-purpose autonomous research framework for AI agents."""
    pass


@main.command()
@click.argument("work_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--target", "-t", default="prompt.txt", help="Target file to optimize"
)
@click.option(
    "--program", "-p", default="program.md", help="Program/agenda file"
)
@click.option(
    "--model", "-m", default="claude-sonnet-4-20250514", help="LLM model to use"
)
@click.option(
    "--provider", default="anthropic", type=click.Choice(["anthropic", "openai"]),
    help="LLM provider"
)
@click.option(
    "--max-experiments", "-n", type=int, default=10,
    help="Maximum number of experiments to run"
)
@click.option(
    "--higher-is-better", is_flag=True, default=True,
    help="Whether higher metric values are better"
)
def run(
    work_dir: Path,
    target: str,
    program: str,
    model: str,
    provider: str,
    max_experiments: int,
    higher_is_better: bool,
):
    """
    Run autonomous research in the specified directory.

    Example:
        autoresearch run ./my-experiment -n 20
    """
    config = AgentConfig(
        provider=provider,
        model=model,
        max_experiments=max_experiments,
    )

    runner = ResearchRunner(
        work_dir=work_dir,
        target_file=target,
        program_file=program,
        agent_config=config,
        metric_higher_is_better=higher_is_better,
    )

    runner.run(max_experiments=max_experiments)


@main.command()
@click.argument("directory", type=click.Path(path_type=Path))
@click.option(
    "--task", "-t", required=True, help="Description of the task"
)
@click.option(
    "--eval-cases", "-e", required=True, type=click.Path(exists=True, path_type=Path),
    help="JSON file with evaluation cases"
)
@click.option(
    "--initial-prompt", "-p", type=click.Path(exists=True, path_type=Path),
    help="Initial prompt file (optional, will use default if not provided)"
)
@click.option(
    "--model", "-m", default="claude-sonnet-4-20250514",
    help="Model to use for evaluation"
)
def init_prompt(
    directory: Path,
    task: str,
    eval_cases: Path,
    initial_prompt: Path,
    model: str,
):
    """
    Initialize a prompt optimization template.

    Example:
        autoresearch init-prompt ./my-prompt-experiment \\
            --task "Extract sentiment from text" \\
            --eval-cases ./sentiment_cases.json
    """
    import json
    from .templates.prompt import create_prompt_template

    # Load evaluation cases
    cases = json.loads(eval_cases.read_text())

    # Load or create initial prompt
    if initial_prompt and initial_prompt.exists():
        prompt_text = initial_prompt.read_text()
    else:
        prompt_text = """You are a helpful assistant. Please respond to the user's request to the best of your ability."""

    create_prompt_template(
        work_dir=directory,
        task_description=task,
        eval_cases=cases,
        initial_prompt=prompt_text,
        model=model,
    )


@main.command()
@click.argument("target_file", type=click.Path(exists=True, path_type=Path))
def test(target_file: Path):
    """
    Test a target file manually (useful for debugging).

    Example:
        autoresearch test ./prompt.txt
    """
    import subprocess

    # Find the run_eval.py script
    run_eval = target_file.parent / "run_eval.py"

    if not run_eval.exists():
        console.print(f"[red]Error: run_eval.py not found in {target_file.parent}[/red]")
        return

    console.print(f"[dim]Running: python {run_eval}[/dim]")
    result = subprocess.run(["python", str(run_eval)], capture_output=True, text=True)
    console.print(result.stdout)
    if result.stderr:
        console.print(result.stderr)


@main.command()
@click.argument("work_dir", type=click.Path(exists=True, path_type=Path))
def report(work_dir: Path):
    """
    Generate and display a report from previous experiments.

    Example:
        autoresearch report ./my-experiment
    """
    from .core import Historian

    output_dir = work_dir / ".autoresearch"
    historian = Historian(output_dir=output_dir)

    report_text = historian.generate_report()
    console.print(report_text)


if __name__ == "__main__":
    main()
