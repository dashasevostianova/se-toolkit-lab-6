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


def test_documentation_agent_read_file():
    """
    Test that the documentation agent uses read_file tool for wiki questions.
    
    Question: "How do you resolve a merge conflict?"
    Expected:
    - tool_calls contains at least one read_file call
    - source contains a wiki file path
    """
    result = subprocess.run(
        ["uv", "run", "agent.py", "How do you resolve a merge conflict?"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    # Check exit code
    assert result.returncode == 0, f"Agent exited with code {result.returncode}: {result.stderr}"

    # Parse stdout as JSON
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Failed to parse stdout as JSON: {result.stdout}") from e

    # Verify required fields exist
    assert "answer" in output, "Missing 'answer' field in output"
    assert "source" in output, "Missing 'source' field in output"
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"

    # Verify read_file was called
    tool_calls = output["tool_calls"]
    assert len(tool_calls) > 0, "Expected at least one tool call"
    
    read_file_calls = [tc for tc in tool_calls if tc.get("tool") == "read_file"]
    assert len(read_file_calls) > 0, "Expected at least one read_file tool call"

    # Verify source contains a wiki file path
    source = output["source"]
    assert "wiki/" in source, f"Expected 'wiki/' in source, got: {source}"

    print("✓ Documentation agent read_file test passed!")


def test_documentation_agent_list_files():
    """
    Test that the documentation agent uses list_files tool for directory questions.
    
    Question: "What files are in the wiki?"
    Expected:
    - tool_calls contains at least one list_files call
    """
    result = subprocess.run(
        ["uv", "run", "agent.py", "What files are in the wiki?"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    # Check exit code
    assert result.returncode == 0, f"Agent exited with code {result.returncode}: {result.stderr}"

    # Parse stdout as JSON
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Failed to parse stdout as JSON: {result.stdout}") from e

    # Verify required fields exist
    assert "answer" in output, "Missing 'answer' field in output"
    assert "source" in output, "Missing 'source' field in output"
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"

    # Verify list_files was called
    tool_calls = output["tool_calls"]
    assert len(tool_calls) > 0, "Expected at least one tool call"
    
    list_files_calls = [tc for tc in tool_calls if tc.get("tool") == "list_files"]
    assert len(list_files_calls) > 0, "Expected at least one list_files tool call"

    print("✓ Documentation agent list_files test passed!")


if __name__ == "__main__":
    test_agent_output_format()
