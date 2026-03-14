#!/usr/bin/env python3
"""
Agent CLI - Connects to an LLM and answers questions using tools.

Usage:
    uv run agent.py "Your question here"

Output:
    JSON with 'answer', 'source', and 'tool_calls' fields to stdout.
"""

import json
import os
import sys

import httpx
from dotenv import load_dotenv


# Maximum number of tool calls per question
MAX_TOOL_CALLS = 10


def load_env() -> None:
    """Load environment variables from .env.agent.secret."""
    env_path = os.path.join(os.path.dirname(__file__), ".env.agent.secret")
    load_dotenv(env_path)


def get_project_root() -> str:
    """Get the project root directory (parent of agent.py)."""
    return os.path.dirname(os.path.abspath(__file__))


def is_safe_path(path: str) -> bool:
    """
    Check if a path is within the project directory.
    
    Prevents directory traversal attacks by ensuring the resolved
    path starts with the project root.
    
    Args:
        path: Relative path from project root.
    
    Returns:
        True if path is safe, False otherwise.
    """
    project_root = get_project_root()
    # Resolve the absolute path
    resolved = os.path.realpath(os.path.join(project_root, path))
    # Ensure it's within project root
    return resolved.startswith(project_root + os.sep) or resolved == project_root


def read_file(path: str) -> str:
    """
    Read a file from the project repository.
    
    Args:
        path: Relative path from project root.
    
    Returns:
        File contents as a string, or an error message.
    """
    if not is_safe_path(path):
        return f"Error: Access denied - path '{path}' is outside project directory"
    
    project_root = get_project_root()
    full_path = os.path.join(project_root, path)
    
    if not os.path.isfile(full_path):
        return f"Error: File not found - '{path}'"
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


def list_files(path: str) -> str:
    """
    List files and directories at a given path.
    
    Args:
        path: Relative directory path from project root.
    
    Returns:
        Newline-separated listing of entries, or an error message.
    """
    if not is_safe_path(path):
        return f"Error: Access denied - path '{path}' is outside project directory"
    
    project_root = get_project_root()
    full_path = os.path.join(project_root, path)
    
    if not os.path.isdir(full_path):
        return f"Error: Directory not found - '{path}'"
    
    try:
        entries = os.listdir(full_path)
        # Sort entries: directories first, then files
        dirs = sorted([e for e in entries if os.path.isdir(os.path.join(full_path, e))])
        files = sorted([e for e in entries if os.path.isfile(os.path.join(full_path, e))])
        return "\n".join(dirs + files)
    except Exception as e:
        return f"Error listing directory: {e}"


# Tool schemas for LLM function calling
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the project repository. Use this to read the contents of a specific file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root (e.g., 'wiki/git-workflow.md')"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path. Use this to discover what files exist in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root (e.g., 'wiki')"
                    }
                },
                "required": ["path"]
            }
        }
    }
]

# Map of tool names to functions
TOOL_FUNCTIONS = {
    "read_file": read_file,
    "list_files": list_files,
}

SYSTEM_PROMPT = """You are a documentation agent that answers questions by reading the project wiki.

Available tools:
- list_files(path): List files and directories in a directory. Use this to discover what files exist.
- read_file(path): Read the contents of a specific file. Use this to find answers in wiki files.

Instructions:
1. Use list_files to discover relevant wiki files when you don't know which file contains the answer.
2. Use read_file to read specific wiki files and find the answer.
3. When you find the answer, provide it along with the source reference.
4. The source should be in the format: wiki/filename.md#section-anchor
   - Use the filename where you found the answer
   - Use a section anchor based on the heading (lowercase, hyphens instead of spaces)
5. When you have enough information to answer, respond with a text message (no tool calls).

Always be concise and cite your sources."""


def call_llm(messages: list, tools: list = None) -> dict:
    """
    Send messages to the LLM and return the response.
    
    Args:
        messages: List of message dictionaries (role, content).
        tools: Optional list of tool schemas for function calling.
    
    Returns:
        The LLM's response as a dictionary.
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
        "messages": messages,
    }
    
    if tools:
        payload["tools"] = tools

    print(f"Calling LLM at {url}...", file=sys.stderr)

    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    return data["choices"][0]["message"]


def execute_tool(tool_call: dict) -> dict:
    """
    Execute a tool call and return the result.
    
    Args:
        tool_call: Tool call dictionary from LLM response.
    
    Returns:
        Dictionary with tool, args, and result.
    """
    function = tool_call.get("function", {})
    tool_name = function.get("name")
    args_str = function.get("arguments", "{}")
    
    try:
        args = json.loads(args_str)
    except json.JSONDecodeError:
        args = {}
    
    print(f"Executing tool: {tool_name} with args: {args}", file=sys.stderr)
    
    if tool_name not in TOOL_FUNCTIONS:
        result = f"Error: Unknown tool '{tool_name}'"
    else:
        func = TOOL_FUNCTIONS[tool_name]
        result = func(**args)
    
    return {
        "tool": tool_name,
        "args": args,
        "result": result,
    }


def run_agentic_loop(question: str) -> tuple:
    """
    Run the agentic loop to answer a question using tools.

    Args:
        question: The user's question.

    Returns:
        Tuple of (answer, source, tool_calls_list).
    """
    # Initialize messages with system prompt and user question
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    
    tool_calls_list = []
    tool_call_count = 0
    
    while tool_call_count < MAX_TOOL_CALLS:
        try:
            # Call LLM with current messages and tool schemas
            response = call_llm(messages, tools=TOOL_SCHEMAS)
        except Exception as e:
            # If LLM call fails but we have tool results, return what we have
            print(f"LLM call failed: {e}", file=sys.stderr)
            if tool_calls_list:
                return "Error during processing, but here's what I found:", "", tool_calls_list
            return f"Error: {e}", "", []
        
        # Check if LLM wants to call tools
        tool_calls = response.get("tool_calls")
        
        if tool_calls:
            # Execute each tool call
            for tool_call in tool_calls:
                result_dict = execute_tool(tool_call)
                tool_calls_list.append(result_dict)
                
                # Append tool result as an assistant message describing the output
                # This format works better with some LLM providers
                messages.append({
                    "role": "assistant",
                    "content": f"[Tool output from {result_dict['tool']}]: {result_dict['result'][:4000]}",
                })
            
            tool_call_count += 1
            print(f"Tool call count: {tool_call_count}", file=sys.stderr)
        else:
            # LLM provided a final answer (no tool calls)
            answer = response.get("content", "")
            # Extract source from answer if present, otherwise use empty string
            source = ""
            return answer, source, tool_calls_list
    
    # Hit max tool calls - use whatever answer we have
    print(f"Hit maximum tool calls ({MAX_TOOL_CALLS})", file=sys.stderr)
    return "I reached the maximum number of tool calls.", "", tool_calls_list


def extract_source_from_answer(answer: str, tool_calls_list: list) -> str:
    """
    Extract or generate a source reference from the answer and tool calls.
    
    Args:
        answer: The LLM's answer text.
        tool_calls_list: List of tool calls made.
    
    Returns:
        Source reference string.
    """
    # Look for the last read_file call to determine source
    for call in reversed(tool_calls_list):
        if call["tool"] == "read_file":
            path = call["args"].get("path", "")
            if path.startswith("wiki/"):
                # Try to extract section from answer
                # For now, just return the file path
                return path
    
    return ""


def format_response(answer: str, source: str, tool_calls_list: list) -> dict:
    """
    Format the response as the required JSON structure.
    
    Args:
        answer: The LLM's answer text.
        source: The source reference.
        tool_calls_list: List of tool calls made.
    
    Returns:
        Dictionary with 'answer', 'source', and 'tool_calls' fields.
    """
    return {
        "answer": answer,
        "source": source,
        "tool_calls": tool_calls_list,
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
        answer, source, tool_calls_list = run_agentic_loop(question)
        
        # Extract source if not provided
        if not source:
            source = extract_source_from_answer(answer, tool_calls_list)
        
        output = format_response(answer, source, tool_calls_list)
        print(json.dumps(output))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        error_output = format_response(f"Error: {e}", "", [])
        print(json.dumps(error_output))
        return 0


if __name__ == "__main__":
    sys.exit(main())
