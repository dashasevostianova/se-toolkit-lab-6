# Task 2: The Documentation Agent - Implementation Plan

## Overview

This plan describes how to extend the Task 1 agent with tool-calling capabilities to read files and list directories from the project wiki.

## Tool Schema Design

### Approach

I will define tool schemas using the OpenAI function-calling format, which is compatible with Qwen Code API. Each tool will have:
- `name`: The function name (e.g., `read_file`, `list_files`)
- `description`: What the tool does
- `parameters`: JSON Schema defining required arguments

### Tool Definitions

**read_file**
```python
{
    "name": "read_file",
    "description": "Read a file from the project repository",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path from project root"}
        },
        "required": ["path"]
    }
}
```

**list_files**
```python
{
    "name": "list_files",
    "description": "List files and directories at a given path",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative directory path from project root"}
        },
        "required": ["path"]
    }
}
```

## Tool Implementation

### `read_file(path)`
- Resolve the path relative to project root
- Security check: ensure no `../` traversal outside project directory
- Read file contents and return as string
- Return error message if file doesn't exist

### `list_files(path)`
- Resolve the path relative to project root
- Security check: ensure path is within project directory
- List directory entries (files and subdirectories)
- Return newline-separated string of entries

### Path Security Strategy

To prevent directory traversal attacks:
1. Use `os.path.realpath()` to resolve the absolute path
2. Check that the resolved path starts with the project root directory
3. Reject any path that contains `..` or resolves outside the project root

```python
def is_safe_path(path: str) -> bool:
    """Check if path is within project directory."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    resolved = os.path.realpath(os.path.join(project_root, path))
    return resolved.startswith(project_root)
```

## Agentic Loop Implementation

### Loop Structure

```python
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": question}
]
tool_call_count = 0
MAX_TOOL_CALLS = 10

while tool_call_count < MAX_TOOL_CALLS:
    response = call_llm(messages, tools=TOOL_SCHEMAS)
    
    if response has tool_calls:
        for tool_call in tool_calls:
            result = execute_tool(tool_call)
            messages.append({"role": "tool", ...})
        tool_call_count += 1
    else:
        # Final answer - extract and return
        break
```

### Message Format for Tool Calls

When the LLM returns tool calls, I need to:
1. Execute each tool and capture the result
2. Append a message with role `tool` containing the result
3. Send the updated message list back to the LLM

## System Prompt Strategy

The system prompt will instruct the LLM to:
1. Use `list_files` to discover wiki files when needed
2. Use `read_file` to read specific wiki files
3. Always include a `source` field with the file path and section anchor
4. Stop calling tools when it has enough information to answer

Example system prompt:
```
You are a documentation agent that answers questions by reading the project wiki.

Available tools:
- list_files(path): List files in a directory
- read_file(path): Read a file's contents

Instructions:
1. Use list_files to discover relevant wiki files
2. Use read_file to read files and find answers
3. Always cite your source as "wiki/filename.md#section-anchor"
4. When you have enough information, provide the final answer without tool calls
```

## Output Format

The final JSON output must include:
- `answer`: The LLM's final answer text
- `source`: The wiki file and section that contains the answer
- `tool_calls`: Array of all tool calls made, each with `tool`, `args`, and `result`

## Testing Strategy

### Test 1: read_file tool usage
Question: "How do you resolve a merge conflict?"
Expected:
- `tool_calls` contains at least one `read_file` call
- `source` contains `wiki/git-workflow.md`

### Test 2: list_files tool usage
Question: "What files are in the wiki?"
Expected:
- `tool_calls` contains at least one `list_files` call

## Implementation Steps

1. Create `plans/task-2.md` (this file)
2. Add tool functions (`read_file`, `list_files`) with security checks
3. Define tool schemas for LLM function calling
4. Implement the agentic loop in `call_llm` or a new function
5. Update `format_response` to include `source` and populated `tool_calls`
6. Update `AGENT.md` with new architecture documentation
7. Add 2 regression tests to `tests/test_agent.py`
8. Run tests and verify all acceptance criteria

## Dependencies

No new external dependencies needed. Will use:
- `os.path` for path manipulation
- Existing `httpx` for API calls
- Existing `python-dotenv` for environment
