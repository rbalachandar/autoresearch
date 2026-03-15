# Prompt Research - Classify text sentiment as positive, negative, or neutral

## How to Use (Claude Code)

1. **Open this directory in Claude Code:**
   ```bash
   claude-code claude-code-mode/sentiment-research
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
- Evaluation cases: 20
- Max experiments: 15
- Time budget: 20 minutes

## Tips

- Give Claude time to think between experiments
- If it gets stuck, remind it of the constraints
- The metric is accuracy (higher is better)
