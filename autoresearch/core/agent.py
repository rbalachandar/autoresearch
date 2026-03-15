"""
Research Agent - The AI agent that conducts autonomous experiments.

The agent reads program.md for context and iteratively modifies the target file
to improve metrics.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

from anthropic import Anthropic
from openai import OpenAI
from pydantic import BaseModel


class AgentConfig(BaseModel):
    """Configuration for a research agent."""

    name: str = "researcher"
    provider: str = "anthropic"  # anthropic, openai
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192
    temperature: float = 0.7

    # Experiment constraints
    max_experiments: int = 100
    time_budget_seconds: Optional[int] = None  # None = unlimited
    metric_higher_is_better: bool = True  # Whether higher metrics are better


@dataclass
class AgentState:
    """The current state of the agent."""

    experiment_number: int = 0
    best_metric: Optional[float] = None  # Will be set based on first result
    current_file_content: str = ""
    history: list[dict] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    metric_higher_is_better: bool = True


def _create_llm_client(provider: str):
    """
    Create an LLM client for the specified provider.

    Args:
        provider: Either 'anthropic' or 'openai'

    Returns:
        An initialized client instance

    Raises:
        ValueError: If provider is unsupported or API key is missing
    """
    if provider == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Please set it in your environment "
                "or .env file."
            )
        return Anthropic()
    elif provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "OPENAI_API_KEY not set. Please set it in your environment "
                "or .env file."
            )
        return OpenAI()
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. "
            "Supported providers are: 'anthropic', 'openai'"
        )


def _is_better_metric(
    new: float, old: float, higher_is_better: bool
) -> bool:
    """
    Check if a new metric is better than an old one.

    Args:
        new: The new metric value
        old: The old metric value
        higher_is_better: Whether higher values are better

    Returns:
        True if new is better than old
    """
    if higher_is_better:
        return new > old
    return new < old


class ResearchAgent:
    """
    An AI agent that autonomously conducts research experiments.

    The agent:
    1. Reads the target file (e.g., train.py, prompt.txt)
    2. Modifies it based on research agenda
    3. Runs the experiment
    4. Evaluates results
    5. Keeps or discards changes
    6. Repeats
    """

    def __init__(
        self,
        config: AgentConfig,
        target_file: Path,
        program_file: Path,
        output_dir: Path,
    ):
        self.config = config
        self.target_file = target_file
        self.program_file = program_file
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize LLM client with validation
        self.client = _create_llm_client(config.provider)

        # Initialize state with metric direction
        self.state = AgentState(
            metric_higher_is_better=config.metric_higher_is_better
        )

    def read_program(self) -> str:
        """Read the research agenda from program.md"""
        return self.program_file.read_text()

    def read_target(self) -> str:
        """Read the current target file content"""
        return self.target_file.read_text()

    def write_target(self, content: str) -> None:
        """Write new content to target file"""
        self.target_file.write_text(content)
        self.state.current_file_content = content

    def propose_changes(self, context: dict[str, Any]) -> str:
        """
        Ask the agent to propose changes to the target file.

        Args:
            context: Additional context including previous results, current best, etc.

        Returns:
            The proposed new content for the target file

        Raises:
            RuntimeError: If API call fails or returns unexpected response
        """
        program = self.read_program()
        current = self.read_target()

        system_prompt = self._build_system_prompt()
        user_message = self._build_user_message(program, current, context)

        try:
            if self.config.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": user_message,
                        }
                    ],
                )
                # Extract content with type checking
                if not response.content:
                    raise RuntimeError("API returned empty response")
                return self._extract_code(response.content[0].text)

            else:  # openai
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                )
                # Extract content with type checking
                if not response.choices:
                    raise RuntimeError("API returned no choices")
                content = response.choices[0].message.content
                if content is None:
                    raise RuntimeError("API returned empty content")
                return self._extract_code(content)

        except Exception as e:
            raise RuntimeError(f"Failed to get response from {self.config.provider}: {e}")

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the agent"""
        direction = "higher" if self.config.metric_higher_is_better else "lower"
        return f"""You are an autonomous research agent. Your job is to iteratively improve a system by making small, focused changes and evaluating the results.

## Your Goal
Maximize the metric ({direction} is better).

## Your Process
1. Analyze the current state and previous results
2. Propose a specific, testable change
3. Explain your reasoning
4. Provide the complete updated file

## Your Constraints
- Make ONE change at a time
- Changes should be small and focused
- Always explain WHY you're making the change
- Build on what works, discard what doesn't
- Stay within the problem domain defined in program.md

## Output Format
Your response must contain the complete updated file in a code block:
```
<file content here>
```

The code block will be automatically extracted and saved as the new target file."""

    def _build_user_message(
        self, program: str, current: str, context: dict[str, Any]
    ) -> str:
        """Build the user message with all context"""
        # Format best metric appropriately
        if self.state.best_metric is None:
            best_metric_str = "No experiments yet"
        else:
            best_metric_str = f"{self.state.best_metric:.4f}"

        msg = f"""# Research Agenda (program.md)
{program}

---

# Current Target File Content
```file
{current}
```

---

# Experiment Context
Experiment Number: {self.state.experiment_number}
Best Metric So Far: {best_metric_str}
"""

        if context.get("previous_results"):
            msg += "\n## Previous Results\n"
            for i, result in enumerate(context["previous_results"][-5:], 1):
                msg += f"{i}. Metric: {result['metric']:.4f} - {result.get('description', 'N/A')}\n"

        if context.get("last_change"):
            msg += f"\n## Last Change\n{context['last_change']}\n"

        if context.get("last_result"):
            msg += f"\n## Last Result\nMetric: {context['last_result']['metric']:.4f}\n"
            if "feedback" in context["last_result"]:
                msg += f"Feedback: {context['last_result']['feedback']}\n"

        msg += "\n---\n\nPropose your next change. Provide the complete updated file in a code block."

        return msg

    def _extract_code(self, response: str) -> str:
        """
        Extract code from a markdown code block.

        Args:
            response: The response text from the LLM

        Returns:
            The extracted code, or the whole response if no code block found
        """
        # Look for code blocks with or without language specifiers
        import re

        # Try to find a code block
        pattern = r"```(?:\w+)?\n([\s\S]*?)```"
        matches = re.findall(pattern, response)

        if matches:
            # Return the first code block found
            return matches[0].strip()

        # If no code block found, return the whole response
        return response.strip()

    def should_continue(self) -> bool:
        """
        Check if the agent should continue experimenting.

        Returns:
            False if max_experiments or time_budget_seconds has been reached
        """
        if self.config.max_experiments:
            if self.state.experiment_number >= self.config.max_experiments:
                return False

        if self.config.time_budget_seconds:
            elapsed = (datetime.now() - self.state.started_at).total_seconds()
            if elapsed >= self.config.time_budget_seconds:
                return False

        return True

    def record_experiment(
        self, result: dict[str, Any]
    ) -> None:
        """
        Record an experiment in the agent's history.

        Args:
            result: Dictionary containing at least 'metric' key
        """
        self.state.experiment_number += 1
        self.state.history.append(result)

        metric = result.get("metric")
        if metric is None:
            return

        # Update best metric considering direction
        if self.state.best_metric is None:
            self.state.best_metric = metric
        elif _is_better_metric(
            metric, self.state.best_metric, self.state.metric_higher_is_better
        ):
            self.state.best_metric = metric

    def get_stop_reason(self) -> Optional[str]:
        """
        Get a human-readable reason for why the agent should stop.

        Returns:
            A string explaining why to stop, or None if should continue
        """
        if self.config.max_experiments:
            if self.state.experiment_number >= self.config.max_experiments:
                return f"Reached maximum number of experiments ({self.config.max_experiments})"

        if self.config.time_budget_seconds:
            elapsed = (datetime.now() - self.state.started_at).total_seconds()
            if elapsed >= self.config.time_budget_seconds:
                return f"Reached time budget ({self.config.time_budget_seconds}s)"

        return None
