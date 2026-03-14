# Agent Architecture

## Overview

`agent.py` is a Python CLI that connects to an LLM via an OpenAI-compatible API and returns structured JSON responses.

## LLM Provider

- **Provider**: Qwen Code API
- **Model**: `qwen3-coder-plus`
- **Deployment**: Self-hosted on VM via `qwen-code-oai-proxy`
- **API Base**: `http://10.93.25.94:42005/v1`

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌─────────────┐
│   User      │────▶│   agent.py   │────▶│  Qwen Code API  │────▶│   LLM       │
│  (CLI arg)  │     │  (CLI Tool)  │     │   (VM Proxy)    │     │  (Cloud)    │
└─────────────┘     └──────────────┘     └─────────────────┘     └─────────────┘
                           │
                           ▼
                    JSON Output
                  {answer, tool_calls}
```

## Components

### `agent.py`

**Functions:**

| Function | Purpose |
|----------|---------|
| `load_env()` | Loads `.env.agent.secret` configuration |
| `call_llm(question)` | Sends HTTP POST to LLM API, returns answer text |
| `format_response(answer)` | Builds output JSON with `answer` and `tool_calls` |
| `main()` | Entry point: parses args, orchestrates flow |

**Flow:**

1. Parse command-line argument (question)
2. Load LLM config from `.env.agent.secret`
3. POST to `/v1/chat/completions` endpoint
4. Parse response, extract answer from `choices[0].message.content`
5. Output JSON to stdout, debug logs to stderr

## Configuration

`.env.agent.secret` contains:

| Variable | Description |
|----------|-------------|
| `LLM_API_KEY` | API key for Qwen Code authentication |
| `LLM_API_BASE` | Base URL of the LLM API endpoint |
| `LLM_MODEL` | Model name (e.g., `qwen3-coder-plus`) |

## Usage

```bash
# Run with a question
uv run agent.py "What does REST stand for?"

# Output (stdout)
{"answer": "Representational State Transfer.", "tool_calls": []}
```

## Output Format

```json
{
  "answer": "<LLM response text>",
  "tool_calls": []
}
```

- `answer`: The LLM's response text
- `tool_calls`: Empty array (populated in Task 2 when tools are added)

## Error Handling

- **Missing CLI argument**: Prints usage to stderr, exits with code 1
- **LLM API error**: Returns error message in JSON `answer` field, exits with code 0
- **Timeout**: 60-second timeout on HTTP requests

## Dependencies

- `httpx` - HTTP client for API requests
- `python-dotenv` - Environment variable loading
- `json`, `os`, `sys` - Standard library

## Testing

Run the regression test:

```bash
uv run pytest tests/test_agent.py -v
```

The test verifies:
- `agent.py` runs successfully
- Output is valid JSON
- `answer` field exists
- `tool_calls` field exists and is empty
