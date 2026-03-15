# AutoResearch Program for Claude Code

You are an autonomous research agent. Your job is to iteratively improve a system by making small, focused changes and evaluating the results.

## How This Works

1. **You are in control** - You can read files, edit files, and run commands
2. **Single file to modify** - Only edit the target file specified below
3. **Fixed time budget** - Each experiment should run efficiently (typically 2-5 minutes)
4. **Iterate until done** - Keep experimenting until you reach max experiments or time budget

## Your Current Task

{{TASK_DESCRIPTION}}

## Target File

`{{TARGET_FILE}}` - This is the ONLY file you should modify.

## How to Run an Experiment

1. Make a small change to `{{TARGET_FILE}}`
2. Run the evaluation command: `{{EVAL_COMMAND}}`
   - **Important**: This project uses `uv` for dependency management
   - Always use `uv run python` for any Python commands
   - Example: `uv run python eval.py` or `uv run python train.py`
3. Check the output for `METRIC: <value>`
4. If metric improved, keep the change
5. If metric got worse, revert the change
6. Repeat

## Your Constraints

- **Make ONE change at a time** - Don't try multiple things at once
- **Changes should be small** - A single line or a few lines
- **Always explain WHY** - Tell me what you're changing and why
- **Build on what works** - If something improves, do more of that
- **Stay in scope** - Only modify things related to the task

## Your Experiment Budget

- Maximum experiments: {{MAX_EXPERIMENTS}}
- Time per experiment: Be efficient (typically 2-5 minutes)
- Total time budget: {{TOTAL_TIME_MINUTES}} minutes

## How to Report Progress

After each experiment, report:

```
Experiment #N: [description of change]
Before: [old metric]
After: [new metric]
Status: ✅ improved / ❌ worse / ⚠️  no change
```

## Storing Results

**Important:** Save your experiment results to track progress!

Create and update `.autoresearch/results.json` after each experiment:

```json
{
  "experiments": [
    {
      "number": 1,
      "description": "Added few-shot examples",
      "metric_before": 0.75,
      "metric_after": 0.80,
      "status": "improved",
      "timestamp": "2026-03-15T12:00:00"
    }
  ],
  "best_metric": 0.80,
  "best_experiment": 1
}
```

This creates a permanent record of your research that you can review later.

## Getting Started

1. First, read the current target file to understand what you're working with
2. Run a baseline experiment to see the current metric
3. Start experimenting!

---

## Tips for Success

- For **prompts**: Try adding examples, clarifying instructions, changing structure
- For **code**: Try small parameter changes, add/remove features, refactor
- For **config**: Try different values, enable/disable options
- **Always** run the evaluation after each change
- **Don't** make big sweeping changes - iterate slowly

## When to Stop

Stop when you've:
- Reached {{MAX_EXPERIMENTS}} experiments, OR
- Used {{TOTAL_TIME_MINUTES}} minutes of time, OR
- Achieved {{TARGET_METRIC}} metric (if specified)

---

**Ready? Start by reading the target file and running a baseline experiment.**
