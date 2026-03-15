# Claude Code AutoResearch

A **Claude Code native** implementation of autonomous research, inspired by [Andrej Karpathy's autoresearch](https://github.com/karpathy/autoresearch).

## The Key Difference

| API Framework (Previous) | Claude Code Mode (This) |
|--------------------------|-------------------------|
| Agent calls via API | Agent has full access |
| Framework extracts code | Agent edits files directly |
| Framework runs commands | Agent runs commands |
| Framework orchestrates | Agent is autonomous |

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE SESSION                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  User: "Please read program.md and let's start research."          │
│                                                                     │
│  Claude:                                                            │
│  1. Reads program.md (instructions)                                │
│  2. Reads prompt.txt (target file)                                 │
│  3. Runs: python eval.py                                           │
│  4. Sees: METRIC: 0.7500                                           │
│  5. Decides: "I'll add few-shot examples"                          │
│  6. Edits prompt.txt (directly, in the editor)                     │
│  7. Runs: python eval.py                                           │
│  8. Sees: METRIC: 0.8500 ✅                                        │
│  9. Reports: "Experiment #2: Added examples, 0.75→0.85, improved"   │
│  10. Repeats...                                                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Create a Research Project

```bash
# For prompt optimization
python claude-code-mode/setup.py prompt my-research \\
  --task "Classify sentiment of text" \\
  --eval-cases examples/sentiment.json \\
  -n 20 --time 30

# For ML training
python claude-code-mode/setup.py ml ml-research \\
  --task "Train a simple classifier" \\
  -n 20 --time 30
```

### 2. Open in Claude Code

```bash
cd my-research
claude-code .
```

### 3. Start Research

Tell Claude:
```
Please read program.md and let's start the autonomous research.
```

That's it! Claude will:
- Read the instructions
- Run experiments
- Report progress
- Iterate autonomously

## Example Projects

### Sentiment Analysis (Included)

```bash
cd claude-code-mode/sentiment-research
claude-code .
```

Then tell Claude:
```
Please read program.md and run a baseline experiment first.
```

### Custom Prompt Research

```bash
python claude-code-mode/setup.py prompt ./my-prompt-research \\
  --task "Extract key information from emails" \\
  --eval-cases ./my_cases.json
```

Create `my_cases.json`:
```json
[
  {
    "input": "Meeting at 3pm tomorrow",
    "expected": ["3pm", "tomorrow"]
  },
  {
    "input": "Call John about the project",
    "expected": ["John", "project"]
  }
]
```

## What the Agent Can Do

With Claude Code, the agent has **actual capabilities**:

| ✅ Claude Code Can Do | ❌ API Cannot Do |
|----------------------|-----------------|
| Edit files directly | Only generate text |
| Run shell commands | No execution |
| Read multiple files | Single context only |
| Use terminal tools | No tools |
| See real output | Simulated output |
| Multi-file changes | Single file only |
| Debug errors | Can't debug |

## Why This Is Better

1. **True Autonomy** - Claude controls everything
2. **Real Feedback** - Claude sees actual command output
3. **Flexible** - Can do more than just edit one file
4. **Debugging** - Claude can fix errors when they occur
5. **Natural** - Works like a real researcher would

## Comparison with Karpathy's AutoResearch

| Aspect | Karpathy's | This Implementation |
|--------|------------|---------------------|
| **Agent** | Claude via Cursor | Claude via Claude Code |
| **Task** | ML training (nanogpt) | Any task (prompts, ML, etc.) |
| **Files** | `prepare.py`, `train.py`, `program.md` | `program.md`, target, eval script |
| **Time Budget** | 5 minutes per experiment | Configurable |
| **Metric** | Validation bpb | Any metric |
| **Language** | Python | Python, or anything |

## File Structure

```
claude-code-mode/
├── program.md          # Template for agent instructions
├── setup.py            # Create new research projects
└── sentiment-research/ # Example project
    ├── program.md      # Filled-in instructions
    ├── prompt.txt      # Target file to optimize
    ├── eval.py         # Evaluation script
    ├── eval_cases.json # Test cases
    └── README.md       # Project info
```

## Creating Custom Research Projects

You can create a custom project by just creating three files:

### 1. program.md (Instructions)

```markdown
You are an autonomous research agent.

## Task
Optimize the config file for better performance.

## Target File
`config.json` - This is the ONLY file you should modify.

## How to Run
1. Make a change to config.json
2. Run: python benchmark.py
3. Check METRIC in output
4. Keep or revert

## Constraints
- Small changes only
- Explain why
- Build on what works
```

### 2. Target File (What to Optimize)

```json
{
  "learning_rate": 0.001,
  "batch_size": 32
}
```

### 3. Eval Script (How to Measure)

```python
import json

config = json.loads(open("config.json"))
result = run_benchmark(config)
print(f"METRIC: {result['score']}")
```

Then open in Claude Code and say "Read program.md and let's start research!"

## Tips for Best Results

1. **Start simple** - Let Claude establish a baseline first
2. **Be patient** - Each experiment takes time to run
3. **Check in** - You can pause and ask Claude what it's trying
4. **Adjust** - Edit program.md if Claude is going in wrong direction
5. **Stop anytime** - Just tell Claude to stop

## Limitations

- Requires Claude Code (or similar coding agent)
- Not as structured as API framework
- Less control over exact behavior
- Requires human supervision

## When to Use Each

| Use Claude Code Mode when... | Use API Framework when... |
|------------------------------|---------------------------|
| You have Claude Code | You only have API access |
| Want maximum flexibility | Want structured control |
| Task involves debugging | Task is well-defined |
| Can supervise | Want to run unattended |
| Research/exploration | Production automation |

## License

MIT License - feel free to use this for your own autonomous research projects!

---

**Wake up to better systems, autonomously, with Claude Code.**
