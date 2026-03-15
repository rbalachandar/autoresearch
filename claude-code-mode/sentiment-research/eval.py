#!/usr/bin/env python3
"""Evaluate a prompt against test cases."""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from anthropic import Anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)

def main():
    """Run the evaluation."""
    # Load the prompt
    prompt = (Path(__file__).parent / "prompt.txt").read_text()

    # Load evaluation cases
    eval_cases = json.loads((Path(__file__).parent / "eval_cases.json").read_text())

    # Initialize client
    client = Anthropic()

    # Run evaluation
    correct = 0
    total = len(eval_cases)

    for case in eval_cases:
        input_text = case["input"]
        expected = case["expected"]

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            temperature=0.0,
            system=prompt,
            messages=[{"role": "user", "content": input_text}],
        )

        output = response.content[0].text

        # Check if expected value is in output
        if isinstance(expected, str):
            is_correct = expected.lower() in output.lower()
        elif isinstance(expected, list):
            is_correct = any(e.lower() in output.lower() for e in expected)
        elif isinstance(expected, bool):
            output_lower = output.lower()
            if expected:
                is_correct = any(w in output_lower for w in ["yes", "true", "correct"])
            else:
                is_correct = any(w in output_lower for w in ["no", "false", "incorrect"])
        else:
            is_correct = str(expected).lower() in output.lower()

        if is_correct:
            correct += 1

    accuracy = correct / total if total > 0 else 0

    # Print result (this is what autoresearch looks for)
    print(f"METRIC: {accuracy:.4f}")
    print(f"Correct: {correct}/{total}")
    print(f"Accuracy: {accuracy:.2%}")

if __name__ == "__main__":
    import time
    start = time.time()

    main()

    elapsed = time.time() - start
    print(f"Evaluation time: {elapsed:.1f}s")
