#!/usr/bin/env python3
"""
Setup script for creating a complete example prompt optimization project.

Usage:
    python examples/setup_example.py
"""

from pathlib import Path
import json

# Paths
project_root = Path(__file__).parent.parent
examples_dir = project_root / "examples"
example_project_dir = examples_dir / "sentiment-analysis"
sentiment_json = examples_dir / "sentiment.json"


def main():
    """Create a complete example project."""
    example_project_dir.mkdir(exist_ok=True)

    # Import the template creator
    import sys
    sys.path.insert(0, str(project_root))

    from autoresearch.templates.prompt import create_prompt_template

    # Load sentiment cases
    sentiment_cases = json.loads(sentiment_json.read_text())

    # Create the template
    create_prompt_template(
        work_dir=example_project_dir,
        task_description="""Classify the sentiment of text as positive, negative, or neutral.

The goal is to create a prompt that accurately identifies the emotional tone of the input text.""",
        eval_cases=sentiment_cases,
        initial_prompt="""You are a sentiment classifier. Analyze the given text and classify its sentiment as either "positive", "negative", or "neutral".

Respond with only the sentiment classification.""",
        model="claude-sonnet-4-20250514",
    )

    # Create a README for the example
    readme = """# Sentiment Analysis Example

This is a complete example of using AutoResearch to optimize a sentiment classification prompt.

## What This Does

The AI agent will automatically experiment with different prompts to improve accuracy on classifying text sentiment.

## Try It

1. First, test the initial prompt:
   ```bash
   cd sentiment-analysis
   python run_eval.py
   ```

2. Then run autonomous research:
   ```bash
   autoresearch run . -n 10
   ```

3. View the results:
   ```bash
   autoresearch report .
   ```

## What to Expect

- The agent will try different prompt strategies
- Each experiment is evaluated against 20 test cases
- Best prompt is automatically saved
- You can view the full history in `.autoresearch/history.json`

## Experiment Ideas

Edit `program.md` to guide the research:

- Try adding few-shot examples
- Experiment with different output formats
- Add specific instructions for edge cases
- Try Chain-of-Thought prompting

## Customization

Replace `eval_cases.json` with your own test cases to optimize for different tasks.
"""
    (example_project_dir / "README.md").write_text(readme)

    print(f"✅ Example project created at: {example_project_dir}")
    print("")
    print("To try it out:")
    print(f"  cd {example_project_dir.relative_to(project_root)}")
    print("  python run_eval.py")
    print("  autoresearch run . -n 10")


if __name__ == "__main__":
    main()
