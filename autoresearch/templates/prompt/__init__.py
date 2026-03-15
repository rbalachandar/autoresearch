"""
Prompt Engineering Template - Optimize LLM prompts automatically.

This template provides a framework for automatically optimizing
system prompts for LLM tasks using the autoresearch framework.
"""

from pathlib import Path
from typing import Any, Optional
import json


class PromptExperimenter:
    """
    Experimenter specialized for prompt optimization.

    Runs evaluation of prompts against test cases and reports metrics.
    """

    def __init__(
        self,
        eval_cases: list[dict],
        model: str = "claude-sonnet-4-20250514",
        provider: str = "anthropic",
    ):
        self.eval_cases = eval_cases
        self.model = model
        self.provider = provider

        # Initialize LLM client
        if provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic()
        elif provider == "openai":
            from openai import OpenAI
            self.client = OpenAI()
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def evaluate_prompt(
        self,
        prompt_file: Path,
    ) -> dict[str, Any]:
        """
        Evaluate a prompt against test cases.

        Args:
            prompt_file: Path to the prompt file to evaluate

        Returns:
            Dictionary with metric and metadata
        """
        prompt = prompt_file.read_text()

        correct = 0
        total = len(self.eval_cases)
        outputs = []

        for case in self.eval_cases:
            input_text = case["input"]
            expected = case["expected"]

            try:
                output = self._call_llm(prompt, input_text)
                is_correct = self._check_output(output, expected)

                if is_correct:
                    correct += 1

                outputs.append({
                    "input": input_text,
                    "expected": expected,
                    "output": output,
                    "correct": is_correct,
                })

            except Exception as e:
                outputs.append({
                    "input": input_text,
                    "expected": expected,
                    "error": str(e),
                    "correct": False,
                })

        accuracy = correct / total if total > 0 else 0

        return {
            "metric": accuracy,
            "metadata": {
                "correct": correct,
                "total": total,
                "accuracy": accuracy,
                "outputs": outputs,
            },
        }

    def _call_llm(self, system_prompt: str, user_input: str) -> str:
        """Call the LLM with the given prompt and input"""
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.0,  # Deterministic for evaluation
                system=system_prompt,
                messages=[{"role": "user", "content": user_input}],
            )
            return response.content[0].text
        else:  # openai
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
            )
            return response.choices[0].message.content

    def _check_output(self, output: str, expected: Any) -> bool:
        """Check if the output matches the expected result"""
        # For simple string matching
        if isinstance(expected, str):
            return expected.lower() in output.lower()

        # For JSON/array expected results
        if isinstance(expected, list):
            for item in expected:
                if isinstance(item, str) and item.lower() in output.lower():
                    return True
            return False

        # For boolean expected
        if isinstance(expected, bool):
            # Check for yes/no, true/false
            output_lower = output.lower()
            if expected:
                return any(word in output_lower for word in ["yes", "true", "correct"])
            else:
                return any(word in output_lower for word in ["no", "false", "incorrect"])

        return str(expected).lower() in output.lower()


def create_prompt_template(
    work_dir: Path,
    task_description: str,
    eval_cases: list[dict],
    initial_prompt: str,
    model: str = "claude-sonnet-4-20250514",
    provider: str = "anthropic",
) -> None:
    """
    Create a prompt optimization template in a directory.

    Args:
        work_dir: Directory to create the template in
        task_description: Description of the task for program.md
        eval_cases: List of evaluation cases
        initial_prompt: Initial prompt to start with
        model: Model to use for evaluation
        provider: LLM provider
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    # Create program.md
    program_md = f"""# Prompt Engineering Research

## Task
{task_description}

## Goal
Optimize the system prompt in `prompt.txt` to maximize accuracy on the evaluation cases.

## Current Status
- Target file: `prompt.txt`
- Evaluation model: {model}
- Number of test cases: {len(eval_cases)}
- Metric: Accuracy (higher is better)

## Guidelines for Optimization
1. Make incremental changes to the prompt
2. Focus on clarity and specificity
3. Add examples if they help
4. Consider edge cases
5. Remove unnecessary instructions
6. Test different prompt structures

## What to Modify
Only modify `prompt.txt`. The evaluation script will automatically test your changes.

## Good Strategies to Try
- Adding explicit instructions for the desired output format
- Including few-shot examples
- Breaking down complex instructions into steps
- Adding constraints or guidelines
- Clarifying ambiguous requirements
"""
    (work_dir / "program.md").write_text(program_md)

    # Create prompt.txt
    (work_dir / "prompt.txt").write_text(initial_prompt)

    # Create eval_cases.json
    (work_dir / "eval_cases.json").write_text(json.dumps(eval_cases, indent=2))

    # Create run_eval.py
    run_eval_py = '''#!/usr/bin/env python3
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
'''
    (work_dir / "run_eval.py").write_text(run_eval_py)

    print(f"Prompt optimization template created at: {work_dir}")
    print(f"  - Edit program.md to adjust the research agenda")
    print(f"  - The initial prompt is in prompt.txt")
    print(f"  - Run 'python run_eval.py' to test manually")
    print(f"  - Use autoresearch to start automatic optimization")
