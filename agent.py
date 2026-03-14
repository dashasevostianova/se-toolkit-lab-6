#!/usr/bin/env python3
"""
Agent CLI - Connects to an LLM and answers questions.

Usage:
    uv run agent.py "Your question here"

Output:
    JSON with 'answer' and 'tool_calls' fields to stdout.
"""

import json
import os
import sys

import httpx
from dotenv import load_dotenv


def load_env() -> None:
    """Load environment variables from .env.agent.secret."""
    env_path = os.path.join(os.path.dirname(__file__), ".env.agent.secret")
    load_dotenv(env_path)


def call_llm(question: str) -> str:
    """
    Send a question to the LLM and return the answer.

    Args:
        question: The user's question.

    Returns:
        The LLM's answer as a string.
    """
    api_key = os.getenv("LLM_API_KEY")
    api_base = os.getenv("LLM_API_BASE")
    model = os.getenv("LLM_MODEL")

    if not api_key or not api_base or not model:
        raise ValueError("Missing LLM configuration in .env.agent.secret")

    url = f"{api_base}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question},
        ],
    }

    print(f"Calling LLM at {url}...", file=sys.stderr)

    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    answer = data["choices"][0]["message"]["content"]
    return answer


def format_response(answer: str) -> dict:
    """
    Format the LLM response as the required JSON structure.

    Args:
        answer: The LLM's answer text.

    Returns:
        Dictionary with 'answer' and 'tool_calls' fields.
    """
    return {
        "answer": answer,
        "tool_calls": [],
    }


def main() -> int:
    """
    Main entry point for the agent CLI.

    Returns:
        Exit code (0 for success).
    """
    if len(sys.argv) < 2:
        print("Usage: uv run agent.py \"<question>\"", file=sys.stderr)
        return 1

    question = sys.argv[1]
    print(f"Question: {question}", file=sys.stderr)

    try:
        load_env()
        answer = call_llm(question)
        output = format_response(answer)
        print(json.dumps(output))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        error_output = format_response(f"Error: {e}")
        print(json.dumps(error_output))
        return 0


if __name__ == "__main__":
    sys.exit(main())
