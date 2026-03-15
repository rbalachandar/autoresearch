#!/usr/bin/env python3
"""Evaluation script for prompt optimization."""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from autoresearch.templates.prompt import PromptExperimenter


def main():
    """Run the evaluation and print the metric."""
    work_dir = Path(__file__).parent
    prompt_file = work_dir / "prompt.txt"
    eval_cases_file = work_dir / "eval_cases.json"

    # Load evaluation cases
    eval_cases = json.loads(eval_cases_file.read_text())

    # Create experimenter
    # You can customize the model here
    experimenter = PromptExperimenter(
        eval_cases=eval_cases,
        model="claude-sonnet-4-20250514",
        provider="anthropic",
    )

    # Evaluate
    result = experimenter.evaluate_prompt(prompt_file)

    # Print metric (this is what autoresearch looks for)
    print(f"METRIC: {result['metric']:.4f}")

    # Also print details for debugging
    print(f"Correct: {result['metadata']['correct']}/{result['metadata']['total']}")
    print(f"Accuracy: {result['metadata']['accuracy']:.2%}")


if __name__ == "__main__":
    main()
