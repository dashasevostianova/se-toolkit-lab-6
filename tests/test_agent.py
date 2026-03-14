"""
Regression tests for agent.py

Tests verify that the agent outputs valid JSON with required fields.
"""

import json
import subprocess
import sys


def test_agent_output_format():
    """
    Test that agent.py outputs valid JSON with 'answer' and 'tool_calls' fields.
    """
    # Run agent.py with a test question
    result = subprocess.run(
        ["uv", "run", "agent.py", "What is 2+2?"],
        capture_output=True,
        text=True,
    )

    # Check exit code
    assert result.returncode == 0, f"Agent exited with code {result.returncode}: {result.stderr}"

    # Parse stdout as JSON
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Failed to parse stdout as JSON: {result.stdout}") from e

    # Verify 'answer' field exists and is non-empty
    assert "answer" in output, "Missing 'answer' field in output"
    assert output["answer"], "'answer' field is empty"
    assert isinstance(output["answer"], str), "'answer' must be a string"

    # Verify 'tool_calls' field exists and is empty array
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"
    assert output["tool_calls"] == [], f"'tool_calls' should be empty array, got {output['tool_calls']}"

    print("✓ All checks passed!")


if __name__ == "__main__":
    test_agent_output_format()
