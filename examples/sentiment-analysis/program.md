# Prompt Engineering Research

## Task
Classify the sentiment of text as positive, negative, or neutral.

The goal is to create a prompt that accurately identifies the emotional tone of the input text.

## Goal
Optimize the system prompt in `prompt.txt` to maximize accuracy on the evaluation cases.

## Current Status
- Target file: `prompt.txt`
- Evaluation model: claude-sonnet-4-20250514
- Number of test cases: 20
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
