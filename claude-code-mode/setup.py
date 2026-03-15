#!/usr/bin/env python3
"""
Setup script for creating Claude Code compatible autoresearch projects.

This creates a simple directory with a program.md that can be used
directly in Claude Code for autonomous research.
"""

import os
import sys
from pathlib import Path


def create_prompt_research(
    output_dir: Path,
    task_description: str,
    eval_cases_file: Path,
    initial_prompt: str = None,
    max_experiments: int = 20,
    time_minutes: int = 30,
):
    """
    Create a prompt optimization research setup for Claude Code.

    Args:
        output_dir: Directory to create the research project
        task_description: Description of the task
        eval_cases_file: Path to JSON file with evaluation cases
        initial_prompt: Initial prompt to start with (optional)
        max_experiments: Maximum number of experiments
        time_minutes: Total time budget in minutes
    """
    import json

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read evaluation cases
    eval_cases = json.loads(eval_cases_file.read_text())

    # Default initial prompt
    if initial_prompt is None:
        initial_prompt = """You are a helpful assistant. Please respond to the user's request to the best of your ability."""

    # Create target file (prompt.txt)
    (output_dir / "prompt.txt").write_text(initial_prompt)

    # Copy evaluation cases
    import shutil
    shutil.copy(eval_cases_file, output_dir / "eval_cases.json")

    # Create evaluation script
    eval_script = f'''#!/usr/bin/env python3
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
            messages=[{{"role": "user", "content": input_text}}],
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
    print(f"METRIC: {{accuracy:.4f}}")
    print(f"Correct: {{correct}}/{{total}}")
    print(f"Accuracy: {{accuracy:.2%}}")

if __name__ == "__main__":
    import time
    start = time.time()

    main()

    elapsed = time.time() - start
    print(f"Evaluation time: {{elapsed:.1f}}s")
'''
    (output_dir / "eval.py").write_text(eval_script)
    (output_dir / "eval.py").chmod(0o755)

    # Create program.md with the specific values
    program_template = (Path(__file__).parent / "program.md").read_text()

    program_md = program_template.replace("{{TASK_DESCRIPTION}}", task_description)
    program_md = program_md.replace("{{TARGET_FILE}}", "prompt.txt")
    program_md = program_md.replace("{{EVAL_COMMAND}}", "uv run python eval.py")
    program_md = program_md.replace("{{MAX_EXPERIMENTS}}", str(max_experiments))
    program_md = program_md.replace("{{TOTAL_TIME_MINUTES}}", str(time_minutes))

    target_metric = "100% accuracy" if "classification" in task_description.lower() else "best possible"
    program_md = program_md.replace("{{TARGET_METRIC}}", target_metric)

    (output_dir / "program.md").write_text(program_md)

    # Create README
    readme = f"""# Prompt Research - {task_description}

## How to Use (Claude Code)

1. **Open this directory in Claude Code:**
   ```bash
   claude-code {output_dir}
   ```

2. **Tell Claude what to do:**
   ```
   Hi! Please read program.md and let's start the autonomous research.
   ```

3. **Claude will:**
   - Read the current prompt.txt
   - Run a baseline evaluation
   - Start iterating on the prompt
   - Report progress after each experiment
   - Stop when it reaches the goal or budget

## Files

- **program.md** - Instructions for Claude (what to read first!)
- **prompt.txt** - The prompt Claude will optimize
- **eval.py** - Script to evaluate the prompt
- **eval_cases.json** - Test cases for evaluation

## Manual Testing

You can also test manually:
```bash
python eval.py
```

## Current Status

- Initial prompt: prompt.txt
- Evaluation cases: {len(eval_cases)}
- Max experiments: {max_experiments}
- Time budget: {time_minutes} minutes

## Tips

- Give Claude time to think between experiments
- If it gets stuck, remind it of the constraints
- The metric is accuracy (higher is better)
"""
    (output_dir / "README.md").write_text(readme)

    print(f"✅ Created Claude Code autoresearch project at: {output_dir}")
    print(f"\nNext steps:")
    print(f"  1. cd {output_dir}")
    print(f"  2. claude-code .")
    print(f"  3. Tell Claude: 'Please read program.md and let's start research'")


def create_ml_research(
    output_dir: Path,
    task_description: str,
    dataset_url: str,
    initial_config: str = None,
    max_experiments: int = 20,
    time_minutes: int = 30,
):
    """
    Create an ML training research setup for Claude Code.

    This creates a simple training script that Claude can optimize.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Default config
    if initial_config is None:
        initial_config = """# Model Configuration
model_type: "simple"
hidden_size: 128
num_layers: 2
learning_rate: 0.001
batch_size: 32
epochs: 5

# Training
optimizer: "adam"
dropout: 0.1
"""

    # Create config file
    (output_dir / "config.yaml").write_text(initial_config)

    # Create training script
    train_script = f'''#!/usr/bin/env python3
"""Training script with 5-minute time budget."""

import time
import yaml
from pathlib import Path

# Load config
config = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text())

# Start 5-minute timer
START_TIME = time.time()
TIME_BUDGET = 5 * 60  # 5 minutes

def check_time():
    """Check if we've exceeded time budget."""
    elapsed = time.time() - START_TIME
    if elapsed >= TIME_BUDGET:
        return True
    return False

def train_one_epoch(model, data, config):
    """Simulate training one epoch."""
    # Simulated training - replace with actual training
    import random
    time.sleep(2)  # Simulate work
    loss = random.uniform(0.1, 1.0) - (config.get("hidden_size", 128) / 1000)
    return loss

def main():
    """Train the model."""
    print(f"Starting training with config: {{config}}")
    print(f"Time budget: {{TIME_BUDGET}}s")

    # Simulate model
    model = type("Model", (), {{}})()

    # Simulate data
    data = [1, 2, 3, 4, 5]

    best_loss = float("inf")
    for epoch in range(config.get("epochs", 5)):
        if check_time():
            print("Time budget reached!")
            break

        loss = train_one_epoch(model, data, config)
        print(f"Epoch {{epoch+1}}: loss = {{loss:.4f}}")

        if loss < best_loss:
            best_loss = loss

    # Print final metric
    # Note: lower loss is better, so we negate for "higher is better"
    metric = -best_loss
    print(f"METRIC: {{metric:.4f}}")
    print(f"Best loss: {{best_loss:.4f}}")

if __name__ == "__main__":
    main()
'''
    (output_dir / "train.py").write_text(train_script)
    (output_dir / "train.py").chmod(0o755)

    # Create program.md
    program_template = (Path(__file__).parent / "program.md").read_text()

    program_md = program_template.replace("{{TASK_DESCRIPTION}}", task_description)
    program_md = program_md.replace("{{TARGET_FILE}}", "config.yaml")
    program_md = program_md.replace("{{EVAL_COMMAND}}", "uv run python train.py")
    program_md = program_md.replace("{{MAX_EXPERIMENTS}}", str(max_experiments))
    program_md = program_md.replace("{{TOTAL_TIME_MINUTES}}", str(time_minutes))
    program_md = program_md.replace("{{TARGET_METRIC}}", "lowest loss")

    (output_dir / "program.md").write_text(program_md)

    # Create README
    readme = f"""# ML Research - {task_description}

## How to Use (Claude Code)

1. **Open this directory in Claude Code:**
   ```bash
   claude-code {output_dir}
   ```

2. **Tell Claude what to do:**
   ```
   Hi! Please read program.md and let's start the autonomous research.
   ```

3. **Claude will:**
   - Read the current config.yaml
   - Run a baseline training
   - Start iterating on hyperparameters
   - Report progress after each experiment
   - Stop when it reaches the goal or budget

## Files

- **program.md** - Instructions for Claude (what to read first!)
- **config.yaml** - The configuration Claude will optimize
- **train.py** - Training script with 5-minute time budget

## Current Status

- Initial config: config.yaml
- Max experiments: {max_experiments}
- Time budget: {time_minutes} minutes
- Per-experiment budget: 5 minutes

## Tips

- Claude can modify any parameter in config.yaml
- Each training run is limited to 5 minutes
- Lower loss is better (we negate it for the metric)
"""
    (output_dir / "README.md").write_text(readme)

    print(f"✅ Created ML autoresearch project at: {output_dir}")
    print(f"\nNext steps:")
    print(f"  1. cd {output_dir}")
    print(f"  2. claude-code .")
    print(f"  3. Tell Claude: 'Please read program.md and let's start research'")


def main():
    """CLI for setting up autoresearch projects."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Create a Claude Code compatible autoresearch project"
    )
    parser.add_argument("type", choices=["prompt", "ml"], help="Type of research")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("--task", "-t", required=True, help="Task description")
    parser.add_argument("--eval-cases", "-e", help="Evaluation cases JSON (for prompt type)")
    parser.add_argument("--dataset", "-d", help="Dataset URL (for ML type)")
    parser.add_argument("--max-experiments", "-n", type=int, default=20, help="Max experiments")
    parser.add_argument("--time", type=int, default=30, help="Time budget in minutes")

    args = parser.parse_args()

    if args.type == "prompt":
        if not args.eval_cases:
            print("Error: --eval-cases required for prompt type")
            sys.exit(1)

        # Check if eval_cases file exists
        eval_cases_path = Path(args.eval_cases)
        if not eval_cases_path.exists():
            print(f"Error: Evaluation cases file not found: {eval_cases_path}")
            sys.exit(1)

        create_prompt_research(
            output_dir=args.output_dir,
            task_description=args.task,
            eval_cases_file=eval_cases_path,
            max_experiments=args.max_experiments,
            time_minutes=args.time,
        )

    elif args.type == "ml":
        create_ml_research(
            output_dir=args.output_dir,
            task_description=args.task,
            dataset_url=args.dataset or "",
            max_experiments=args.max_experiments,
            time_minutes=args.time,
        )


if __name__ == "__main__":
    main()
