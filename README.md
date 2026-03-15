# AutoResearch

> General-purpose autonomous research framework for AI agents

Inspired by [Andrej Karpathy's autoresearch](https://github.com/karpathy/autoresearch), this framework enables AI agents to autonomously experiment, iterate, and improve systems while humans only set the research agenda.

## The Core Idea

You don't touch the code directly. Instead, you edit `program.md` which defines:
- **What** to optimize
- **How** to measure success
- **Constraints and guidelines**

The AI agent then autonomously:
1. Reads the current state
2. Proposes changes
3. Runs experiments
4. Evaluates results
5. Keeps or discards changes
6. Repeats

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/autoresearch-framework.git
cd autoresearch-framework

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

## Quick Start

### 1. Initialize a Prompt Optimization Experiment

```bash
autoresearch init-prompt ./my-first-experiment \
  --task "Extract the main sentiment from text (positive, negative, or neutral)" \
  --eval-cases ./examples/sentiment.json
```

This creates:
```
my-first-experiment/
├── program.md          # Edit this to define your research agenda
├── prompt.txt          # The file that gets optimized
├── eval_cases.json     # Test cases for evaluation
└── run_eval.py         # Evaluation script
```

### 2. Test Manually (Optional)

```bash
autoresearch test ./my-first-experiment/prompt.txt
```

### 3. Run Autonomous Research

```bash
autoresearch run ./my-first-experiment -n 10
```

The agent will run 10 experiments and output:
```
🟢 Experiment #1: Metric = 0.7500 (Best: 0.7500) (12.3s)
    Excellent! Metric improved by 0.7500. This change should be kept.

🔴 Experiment #2: Metric = 0.7000 (Best: 0.7500) (11.8s)
    Metric is worse than best by 0.0500. Discard this change...

🟢 Experiment #3: Metric = 0.8000 (Best: 0.8000) (13.1s)
    Excellent! Metric improved by 0.0500. This change should be kept.
```

### 4. View Results

```bash
autoresearch report ./my-first-experiment
```

## Architecture

```
autoresearch/
├── core/               # Core framework components
│   ├── agent.py        # AI agent that proposes changes
│   ├── experimenter.py # Runs experiments and captures metrics
│   ├── historian.py    # Tracks all experiments and results
│   ├── evaluator.py    # Evaluates and compares results
│   └── runner.py       # Orchestrates the research loop
├── templates/          # Domain-specific templates
│   └── prompt/         # Prompt engineering template
└── cli.py              # Command-line interface
```

## Templates

### Prompt Engineering (Included)

Optimize LLM system prompts for specific tasks:

```bash
autoresearch init-prompt ./sentiment-analysis \\
  --task "Classify text sentiment" \\
  --eval-cases ./sentiment_cases.json
```

### Coming Soon

- **ML Training** - Hyperparameter optimization and architecture search
- **Web Performance** - Optimize for Lighthouse scores, bundle size
- **SQL Optimization** - Automatic query tuning
- **Docker Optimization** - Minimize image size and build time

## How It Works

### The Research Loop

```
┌─────────────────────────────────────────────────────────────┐
│  1. Agent reads program.md and current target file          │
│  2. Agent proposes changes to target file                   │
│  3. Experimenter runs the experiment                        │
│  4. Evaluator compares result against best                  │
│  5. If better: keep changes                                 │
│     If worse: revert to best                                │
│  6. Historian records everything                           │
│  7. Repeat until max_experiments or time budget            │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

| Principle | Description |
|-----------|-------------|
| **Single file to modify** | The agent only touches one file, keeping diffs reviewable |
| **Fixed time budget** | Each experiment runs for the same duration, enabling fair comparison |
| **Self-contained** | Minimal dependencies, easy to run anywhere |
| **Observable** | Full history of all experiments with rollback capability |

## Configuration

### Agent Config

```python
from autoresearch.core import AgentConfig

config = AgentConfig(
    provider="anthropic",  # or "openai"
    model="claude-sonnet-4-20250514",
    max_experiments=100,
    time_budget_seconds=300,  # 5 minutes per experiment
)
```

### Custom Experimenter

```python
from autoresearch.core import Experimenter, ResearchRunner

class MyExperimenter(Experimenter):
    def run(self, experiment):
        # Your custom experiment logic
        result = my_custom_function()
        return ExperimentResult(
            metric=result["score"],
            metadata=result,
        )

runner = ResearchRunner(
    work_dir="./my-experiment",
    target_file="my_file.py",
)
runner.experimenter = MyExperimenter(...)
runner.run()
```

## Output

After running experiments, you'll find:

```
.autoresearch/
├── history.json     # Complete experiment history
└── report.txt       # Human-readable summary
```

Example report:

```
# AutoResearch Summary

Total Experiments: 10
Best Metric: 0.8500 (Experiment #7)
Total Duration: 123.4s

┌──────┬───────────┬──────────┬──────────────────────────────┐
│  #   │  Metric   │ Duration │         Description          │
├──────┼───────────┼──────────┼──────────────────────────────┤
│  7   │  0.8500   │  12.3s   │ Added few-shot examples...   │
│  3   │  0.8000   │  11.8s   │ Clarified output format...   │
│  1   │  0.7500   │  13.1s   │ Initial prompt structure...  │
└──────┴───────────┴──────────┴──────────────────────────────┘
```

## Contributing

Contributions are welcome! Areas to contribute:

1. **New templates** - Add support for new domains
2. **Better agents** - Implement advanced strategies
3. **Evaluation metrics** - Add more sophisticated evaluation
4. **Visualizations** - Build dashboards and charts

## License

MIT License - feel free to use this for your own projects.

## Acknowledgments

- Inspired by [Andrej Karpathy's autoresearch](https://github.com/karpathy/autoresearch)
- Built with [Anthropic](https://www.anthropic.com) and [OpenAI](https://www.openai.com) APIs

---

**Wake up to better systems, automatically.**
