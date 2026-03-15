# Sentiment Analysis Example

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
