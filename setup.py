#!/usr/bin/env python3
"""
Setup script for creating Claude Code compatible autoresearch projects.

This creates a simple directory with a program.md that can be used
directly in Claude Code for autonomous research.
"""

import json
import shutil
import sys
from pathlib import Path
from typing import Optional


def create_prompt_research(
    output_dir: Path,
    task_description: str,
    eval_cases_file: Path,
    initial_prompt: Optional[str] = None,
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
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read evaluation cases
    try:
        eval_cases = json.loads(eval_cases_file.read_text())
    except FileNotFoundError:
        print(f"Error: Evaluation cases file not found: {eval_cases_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in evaluation cases file: {e}")
        sys.exit(1)

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
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed. Run: pip install openai")
    sys.exit(1)

def save_result(metric, work_dir):
    """Save evaluation result to .autoresearch/results.json"""
    results_dir = work_dir / ".autoresearch"
    results_dir.mkdir(exist_ok=True)

    results_file = results_dir / "results.json"

    # Load existing results or create new
    if results_file.exists():
        data = json.loads(results_file.read_text())
    else:
        data = {{
            "experiments": [],
            "best_metric": 0.0,
            "best_experiment": 0
        }}

    # Determine if this is an improvement
    is_improvement = metric > data["best_metric"]

    # Create experiment record
    experiment = {{
        "number": len(data["experiments"]) + 1,
        "metric": metric,
        "timestamp": datetime.now().isoformat(),
        "is_improvement": is_improvement
    }}

    data["experiments"].append(experiment)

    if is_improvement:
        data["best_metric"] = metric
        data["best_experiment"] = experiment["number"]

    # Save results
    results_file.write_text(json.dumps(data, indent=2))

    return experiment["number"], is_improvement

def main():
    """Run the evaluation."""
    work_dir = Path(__file__).parent

    # Load the prompt
    prompt = (work_dir / "prompt.txt").read_text()

    # Load evaluation cases
    eval_cases = json.loads((work_dir / "eval_cases.json").read_text())

    # Initialize client (supports OpenAI-compatible APIs)
    client = OpenAI()

    # Get model from env or use default
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Run evaluation
    correct = 0
    total = len(eval_cases)

    for case in eval_cases:
        input_text = case["input"]
        expected = case["expected"]

        response = client.chat.completions.create(
            model=model,
            messages=[
                {{"role": "system", "content": prompt}},
                {{"role": "user", "content": input_text}}
            ],
            max_tokens=1024,
            temperature=0.0,
        )

        output = response.choices[0].message.content

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

    # Save result to .autoresearch/results.json
    exp_num, is_improvement = save_result(accuracy, work_dir)

    # Print result (this is what autoresearch looks for)
    print(f"METRIC: {{accuracy:.4f}}")
    print(f"Correct: {{correct}}/{{total}}")
    print(f"Accuracy: {{accuracy:.2%}}")
    print(f"Experiment: #{{exp_num}} {{'(✨ New Best!)' if is_improvement else ''}}")

if __name__ == "__main__":
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


def create_rag_research(
    output_dir: Path,
    task_description: str,
    documents_path: Path,
    eval_cases_file: Path = None,
    max_experiments: int = 20,
    time_minutes: int = 30,
):
    """
    Create a RAG optimization research setup for Claude Code.

    This creates a RAG pipeline with configurable chunking, retrieval, and prompt parameters.
    """
    import json

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Default RAG config
    rag_config = f"""# RAG Configuration

# Chunking
chunk_size: 512
chunk_overlap: 50

# Retrieval
top_k: 5
retriever_type: "similarity"

# Reranking
enable_rerank: false
rerank_top_k: 3

# Generation
model: "gpt-4o-mini"  # Can be overridden in eval script
max_tokens: 1024
temperature: 0.0
"""

    # Create config file
    (output_dir / "rag_config.yaml").write_text(rag_config)

    # Create RAG evaluation script
    rag_eval_script = f'''#!/usr/bin/env python3
"""Evaluate RAG configuration."""

import json
import time
import yaml
from pathlib import Path

# Load config
config = yaml.safe_load((Path(__file__).parent / "rag_config.yaml").read_text())

# Simulated RAG pipeline (replace with actual implementation)
def retrieve_chunks(query, config):
    """Simulate retrieving relevant chunks."""
    # In real implementation, this would use embeddings + vector DB
    # For now, return dummy chunks
    return [
        {{"content": "Sample chunk 1", "score": 0.9}},
        {{"content": "Sample chunk 2", "score": 0.8}},
    ]

def generate_answer(query, chunks, config):
    """Generate answer using retrieved chunks."""
    # In real implementation, this would call Claude API
    context = "\\n".join([c["content"] for c in chunks])
    return f"Based on the context: {{context[:100]}}..."

def evaluate_rag(eval_cases, config):
    """Evaluate RAG on test cases."""
    correct = 0
    total = len(eval_cases)

    for case in eval_cases:
        query = case["query"]
        expected_answer = case["expected_answer"]

        # Retrieve and generate
        chunks = retrieve_chunks(query, config)
        answer = generate_answer(query, chunks, config)

        # Check if expected answer is in response
        if expected_answer.lower() in answer.lower():
            correct += 1

    return correct / total if total > 0 else 0

def save_result(metric, work_dir):
    """Save evaluation result to .autoresearch/results.json"""
    from datetime import datetime

    results_dir = work_dir / ".autoresearch"
    results_dir.mkdir(exist_ok=True)

    results_file = results_dir / "results.json"

    # Load existing results or create new
    if results_file.exists():
        data = json.loads(results_file.read_text())
    else:
        data = {{
            "experiments": [],
            "best_metric": 0.0,
            "best_experiment": 0
        }}

    # Determine if this is an improvement
    is_improvement = metric > data["best_metric"]

    # Create experiment record
    experiment = {{
        "number": len(data["experiments"]) + 1,
        "metric": metric,
        "timestamp": datetime.now().isoformat(),
        "is_improvement": is_improvement
    }}

    data["experiments"].append(experiment)

    if is_improvement:
        data["best_metric"] = metric
        data["best_experiment"] = experiment["number"]

    # Save results
    results_file.write_text(json.dumps(data, indent=2))

    return experiment["number"], is_improvement

def main():
    """Run RAG evaluation."""
    work_dir = Path(__file__).parent

    # Load evaluation cases
    eval_cases_path = work_dir / "eval_cases.json"
    if eval_cases_path.exists():
        eval_cases = json.loads(eval_cases_path.read_text())
    else:
        # Default test cases if none provided
        eval_cases = [
            {{"query": "What is RAG?", "expected_answer": "Retrieval Augmented Generation"}},
            {{"query": "How does chunk size affect retrieval?", "expected_answer": "chunk"}},
        ]

    # Run evaluation
    accuracy = evaluate_rag(eval_cases, config)

    # Print metric
    print(f"METRIC: {{accuracy:.4f}}")
    print(f"Correct: {{int(accuracy * len(eval_cases))}}/{{len(eval_cases)}}")
    print(f"Accuracy: {{accuracy:.2%}}")
    print(f"Config: top_k={{config.get('top_k')}}, chunk_size={{config.get('chunk_size')}}")

    # Save result to .autoresearch/results.json
    exp_num, is_improvement = save_result(accuracy, work_dir)
    print(f"Experiment: #{{exp_num}} {{'(✨ New Best!)' if is_improvement else ''}}")

if __name__ == "__main__":
    start = time.time()
    main()
    elapsed = time.time() - start
    print(f"Evaluation time: {{elapsed:.1f}}s")
'''
    (output_dir / "eval_rag.py").write_text(rag_eval_script)
    (output_dir / "eval_rag.py").chmod(0o755)

    # Copy or create evaluation cases
    if eval_cases_file and eval_cases_file.exists():
        import shutil
        shutil.copy(eval_cases_file, output_dir / "eval_cases.json")
    else:
        # Create default RAG evaluation cases
        default_cases = [
            {
                "query": "What is Retrieval Augmented Generation?",
                "expected_answer": "RAG"
            },
            {
                "query": "How do I optimize chunk size for my documents?",
                "expected_answer": "chunk"
            },
            {
                "query": "What's the difference between similarity and semantic search?",
                "expected_answer": "search"
            },
        ]
        (output_dir / "eval_cases.json").write_text(json.dumps(default_cases, indent=2))

    # Create program.md
    program_template = (Path(__file__).parent / "program.md").read_text()

    program_md = program_template.replace("{{TASK_DESCRIPTION}}", task_description)
    program_md = program_md.replace("{{TARGET_FILE}}", "rag_config.yaml")
    program_md = program_md.replace("{{EVAL_COMMAND}}", "uv run python eval_rag.py")
    program_md = program_md.replace("{{MAX_EXPERIMENTS}}", str(max_experiments))
    program_md = program_md.replace("{{TOTAL_TIME_MINUTES}}", str(time_minutes))
    program_md = program_md.replace("{{TARGET_METRIC}}", "best retrieval accuracy")

    (output_dir / "program.md").write_text(program_md)

    # Create README
    readme = f"""# RAG Optimization - {task_description}

## How to Use (Claude Code)

1. **Open this directory in Claude Code:**
   ```bash
   cd {output_dir}
   claude-code .
   ```

2. **Tell Claude what to do:**
   ```
   Hi! Please read program.md and let's start the RAG optimization research.
   ```

3. **Claude will:**
   - Read the current rag_config.yaml
   - Run a baseline evaluation
   - Experiment with chunk sizes, top_k values, and reranking
   - Report progress after each experiment
   - Stop when it reaches the goal or budget

## Files

- **program.md** - Instructions for Claude (what to read first!)
- **rag_config.yaml** - The RAG configuration to optimize
- **eval_rag.py** - RAG evaluation script
- **eval_cases.json** - Test queries and expected answers

## Configuration Parameters

Claude can optimize these parameters in `rag_config.yaml`:

- **chunk_size**: Size of document chunks (default: 512)
- **chunk_overlap**: Overlap between chunks (default: 50)
- **top_k**: Number of chunks to retrieve (default: 5)
- **enable_rerank**: Whether to rerank results (default: false)
- **rerank_top_k**: Number of chunks after reranking (default: 3)

## Manual Testing

```bash
python eval_rag.py
```

## Current Status

- Initial config: rag_config.yaml
- Evaluation cases: {len(json.loads((output_dir / "eval_cases.json").read_text()) if (output_dir / "eval_cases.json").exists() else [])}
- Max experiments: {max_experiments}
- Time budget: {time_minutes} minutes
"""
    (output_dir / "README.md").write_text(readme)

    print(f"✅ Created RAG optimization project at: {output_dir}")
    print(f"\nNext steps:")
    print(f"  1. cd {output_dir}")
    print(f"  2. Add your documents to the documents/ folder")
    print(f"  3. Update eval_cases.json with your test queries")
    print(f"  4. claude-code .")
    print(f"  5. Tell Claude: 'Please read program.md and let's start RAG optimization'")


def create_tools_research(
    output_dir: Path,
    task_description: str,
    tools_config: str = None,
    eval_cases_file: Path = None,
    max_experiments: int = 20,
    time_minutes: int = 30,
):
    """
    Create a Tool/Function calling optimization research setup for Claude Code.

    This creates a tool calling setup with optimized tool descriptions and prompts.
    """
    import json

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Default tools configuration
    if tools_config is None:
        tools_config = """# Tools Configuration

# Tool Descriptions (these will be optimized)
tools:
  - name: web_search
    description: "Search the web for current information"
    parameters:
      query:
        type: string
        description: "The search query"
        required: true

  - name: calculator
    description: "Perform mathematical calculations"
    parameters:
      expression:
        type: string
        description: "The mathematical expression to evaluate"
        required: true

  - name: file_reader
    description: "Read and analyze file contents"
    parameters:
      filepath:
        type: string
        description: "Path to the file to read"
        required: true

# System prompt for tool use
system_prompt: |
  You are a helpful assistant with access to tools.
  Use the appropriate tool when needed to help the user.
  Think step by step about which tool to use.
"""

    # Create tools config file
    (output_dir / "tools_config.yaml").write_text(tools_config)

    # Create tool evaluation script with real LLM-based selection
    tools_eval_script = f'''#!/usr/bin/env python3
"""Evaluate tool calling configuration using real LLM for selection."""

import json
import time
import os
import yaml
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed. Run: pip install openai")
    import sys
    sys.exit(1)

# Load config
config = yaml.safe_load((Path(__file__).parent / "tools_config.yaml").read_text())

def get_llm_client():
    """Get OpenAI client (works with OpenAI-compatible APIs)."""
    # Uses OPENAI_API_KEY, OPENAI_BASE_URL environment variables
    # Supports: OpenAI, Anthropic, Together, Azure, local models, etc.
    return OpenAI()

def select_tool_with_llm(query, config):
    """Use LLM to select the appropriate tool based on descriptions."""
    tools = config.get("tools", [])
    system_prompt = config.get("system_prompt", "You are a helpful assistant.")

    # Build tool descriptions for the prompt
    tools_desc = "\\n".join([
        f"- {{tool['name']}}: {{tool.get('description', 'No description')}}"
        for tool in tools
    ])

    prompt = f"""You have access to the following tools:

{{tools_desc}}

Given the user request: "{{query}}"

Select the most appropriate tool to use. Respond with ONLY the tool name (e.g., "web_search", "calculator", "file_reader"). If no tool is appropriate, respond with "no_tool"."""

    try:
        client = get_llm_client()

        # Get model from env or use default
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {{"role": "system", "content": system_prompt}},
                {{"role": "user", "content": prompt}}
            ],
            max_tokens=100,
            temperature=0.0,
        )

        selected_tool = response.choices[0].message.content.strip().lower()

        # Extract just the tool name if LLM adds extra text
        for tool in tools:
            if tool["name"] in selected_tool:
                return tool["name"]

        return selected_tool if selected_tool in [t["name"] for t in tools] else "no_tool"

    except Exception as e:
        print(f"Error calling LLM: {{e}}")
        return "no_tool"

def evaluate_tools(eval_cases, config):
    """Evaluate tool selection on test cases using real LLM."""
    correct = 0
    total = len(eval_cases)

    for case in eval_cases:
        query = case["query"]
        expected_tool = case["expected_tool"]

        # Use LLM for tool selection
        selected_tool = select_tool_with_llm(query, config)

        # Case-insensitive comparison
        if selected_tool.lower() == expected_tool.lower():
            correct += 1
        else:
            print(f"  Query: {{query}}")
            print(f"  Expected: {{expected_tool}}, Got: {{selected_tool}}")

    return correct / total if total > 0 else 0

def save_result(metric, work_dir):
    """Save evaluation result to .autoresearch/results.json"""
    from datetime import datetime

    results_dir = work_dir / ".autoresearch"
    results_dir.mkdir(exist_ok=True)

    results_file = results_dir / "results.json"

    # Load existing results or create new
    if results_file.exists():
        data = json.loads(results_file.read_text())
    else:
        data = {{
            "experiments": [],
            "best_metric": 0.0,
            "best_experiment": 0
        }}

    # Determine if this is an improvement
    is_improvement = metric > data["best_metric"]

    # Create experiment record
    experiment = {{
        "number": len(data["experiments"]) + 1,
        "metric": metric,
        "timestamp": datetime.now().isoformat(),
        "is_improvement": is_improvement
    }}

    data["experiments"].append(experiment)

    if is_improvement:
        data["best_metric"] = metric
        data["best_experiment"] = experiment["number"]

    # Save results
    results_file.write_text(json.dumps(data, indent=2))

    return experiment["number"], is_improvement

def main():
    """Run tool evaluation."""
    work_dir = Path(__file__).parent

    # Load evaluation cases
    eval_cases_path = work_dir / "eval_cases.json"
    if eval_cases_path.exists():
        eval_cases = json.loads(eval_cases_path.read_text())
    else:
        # Default test cases
        eval_cases = [
            {{"query": "What's the weather like today?", "expected_tool": "web_search"}},
            {{"query": "Calculate 15% of 250", "expected_tool": "calculator"}},
            {{"query": "Show me the contents of data.json", "expected_tool": "file_reader"}},
            {{"query": "Who won the world series last year?", "expected_tool": "web_search"}},
            {{"query": "What is 2^10?", "expected_tool": "calculator"}},
        ]

    print(f"Evaluating {{len(eval_cases)}} test cases with LLM-based tool selection...")
    print()

    # Run evaluation
    accuracy = evaluate_tools(eval_cases, config)

    # Print metric
    print()
    print(f"METRIC: {{accuracy:.4f}}")
    print(f"Correct: {{int(accuracy * len(eval_cases))}}/{{len(eval_cases)}}")
    print(f"Accuracy: {{accuracy:.2%}}")

    # Save result to .autoresearch/results.json
    exp_num, is_improvement = save_result(accuracy, work_dir)
    print(f"Experiment: #{{exp_num}} {{'(✨ New Best!)' if is_improvement else ''}}")

    # Count tools
    num_tools = len(config.get("tools", []))
    print(f"Available tools: {{num_tools}}")

if __name__ == "__main__":
    start = time.time()
    main()
    elapsed = time.time() - start
    print(f"Evaluation time: {{elapsed:.1f}}s")
'''
    (output_dir / "eval_tools.py").write_text(tools_eval_script)
    (output_dir / "eval_tools.py").chmod(0o755)

    # Copy or create evaluation cases
    if eval_cases_file and eval_cases_file.exists():
        import shutil
        shutil.copy(eval_cases_file, output_dir / "eval_cases.json")
    else:
        # Create default tool evaluation cases
        default_cases = [
            {
                "query": "What's the weather like today?",
                "expected_tool": "web_search"
            },
            {
                "query": "Calculate 15% of 250",
                "expected_tool": "calculator"
            },
            {
                "query": "Show me the contents of data.json",
                "expected_tool": "file_reader"
            },
            {
                "query": "Who won the world series last year?",
                "expected_tool": "web_search"
            },
            {
                "query": "What is 2^10?",
                "expected_tool": "calculator"
            },
        ]
        (output_dir / "eval_cases.json").write_text(json.dumps(default_cases, indent=2))

    # Create program.md
    program_template = (Path(__file__).parent / "program.md").read_text()

    program_md = program_template.replace("{{TASK_DESCRIPTION}}", task_description)
    program_md = program_md.replace("{{TARGET_FILE}}", "tools_config.yaml")
    program_md = program_md.replace("{{EVAL_COMMAND}}", "uv run python eval_tools.py")
    program_md = program_md.replace("{{MAX_EXPERIMENTS}}", str(max_experiments))
    program_md = program_md.replace("{{TOTAL_TIME_MINUTES}}", str(time_minutes))
    program_md = program_md.replace("{{TARGET_METRIC}}", "best tool selection accuracy")

    (output_dir / "program.md").write_text(program_md)

    # Create README
    readme = f"""# Tool/Function Calling Optimization - {task_description}

## How to Use (Claude Code)

1. **Open this directory in Claude Code:**
   ```bash
   cd {output_dir}
   claude-code .
   ```

2. **Tell Claude what to do:**
   ```
   Hi! Please read program.md and let's start the tool optimization research.
   ```

3. **Claude will:**
   - Read the current tools_config.yaml
   - Run a baseline evaluation
   - Optimize tool descriptions and system prompt
   - Report progress after each experiment
   - Stop when it reaches the goal or budget

## Files

- **program.md** - Instructions for Claude (what to read first!)
- **tools_config.yaml** - The tools configuration to optimize
- **eval_tools.py** - Tool evaluation script
- **eval_cases.json** - Test queries and expected tool selections

## What Gets Optimized

Claude can optimize in `tools_config.yaml`:

- **Tool descriptions**: More precise descriptions improve LLM tool selection
- **Parameter descriptions**: Better parameter docs improve usage
- **System prompt**: Instructions for when and how to use tools
- **Tool order**: The sequence tools are presented

## How Evaluation Works

This evaluation uses **real LLM-based tool selection** (not simulation):
- Sends each query to Claude with your tool descriptions
- Claude selects the appropriate tool based on descriptions
- Compares selection against expected tool
- Better descriptions = better tool selection accuracy

## Manual Testing

```bash
python eval_tools.py
```

## Current Status

- Initial config: tools_config.yaml
- Evaluation cases: {len(json.loads((output_dir / "eval_cases.json").read_text()) if (output_dir / "eval_cases.json").exists() else [])}
- Max experiments: {max_experiments}
- Time budget: {time_minutes} minutes
"""
    (output_dir / "README.md").write_text(readme)

    print(f"✅ Created tool calling optimization project at: {output_dir}")
    print(f"\nNext steps:")
    print(f"  1. cd {output_dir}")
    print(f"  2. Update tools_config.yaml with your actual tools")
    print(f"  3. Update eval_cases.json with test queries")
    print(f"  4. claude-code .")
    print(f"  5. Tell Claude: 'Please read program.md and let's start tool optimization'")


def main():
    """CLI for setting up autoresearch projects."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Create a Claude Code compatible autoresearch project"
    )
    parser.add_argument("type", choices=["prompt", "ml", "rag", "tools"], help="Type of research")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("--task", "-t", required=True, help="Task description")
    parser.add_argument("--eval-cases", "-e", help="Evaluation cases JSON (for prompt, rag, tools types)")
    parser.add_argument("--dataset", "-d", help="Dataset URL (for ML type)")
    parser.add_argument("--documents", "--docs", help="Documents path (for RAG type)")
    parser.add_argument("--tools-config", help="Tools config YAML (for tools type)")
    parser.add_argument("--max-experiments", "-n", type=int, default=20, help="Max experiments")
    parser.add_argument("--time-budget", type=int, default=30, help="Total time budget in minutes")

    args = parser.parse_args()

    # Validate parameters
    if args.max_experiments <= 0:
        print("Error: --max-experiments must be a positive integer")
        sys.exit(1)

    if args.time_budget <= 0:
        print("Error: --time-budget must be a positive integer")
        sys.exit(1)

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
            time_minutes=args.time_budget,
        )

    elif args.type == "ml":
        create_ml_research(
            output_dir=args.output_dir,
            task_description=args.task,
            dataset_url=args.dataset or "",
            max_experiments=args.max_experiments,
            time_minutes=args.time_budget,
        )

    elif args.type == "rag":
        # RAG optimization
        eval_cases_path = Path(args.eval_cases) if args.eval_cases else None
        if eval_cases_path and not eval_cases_path.exists():
            print(f"Error: Evaluation cases file not found: {eval_cases_path}")
            sys.exit(1)

        create_rag_research(
            output_dir=args.output_dir,
            task_description=args.task,
            documents_path=Path(args.documents) if args.documents else None,
            eval_cases_file=eval_cases_path,
            max_experiments=args.max_experiments,
            time_minutes=args.time_budget,
        )

    elif args.type == "tools":
        # Tool/Function calling optimization
        eval_cases_path = Path(args.eval_cases) if args.eval_cases else None
        if eval_cases_path and not eval_cases_path.exists():
            print(f"Error: Evaluation cases file not found: {eval_cases_path}")
            sys.exit(1)

        create_tools_research(
            output_dir=args.output_dir,
            task_description=args.task,
            tools_config=args.tools_config,
            eval_cases_file=eval_cases_path,
            max_experiments=args.max_experiments,
            time_minutes=args.time_budget,
        )


if __name__ == "__main__":
    main()
