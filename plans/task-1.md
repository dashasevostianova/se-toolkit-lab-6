# Task 1: Call an LLM from Code

## LLM Provider and Model

- **Provider**: Qwen Code API (deployed on VM)
- **Model**: `qwen3-coder-plus`
- **API Base**: `http://10.93.25.94:42005/v1`
- **Authentication**: API key stored in `.env.agent.secret`

## Agent Structure

### Input/Output Flow

1. **Input**: Question passed as the first command-line argument
2. **Processing**:
   - Parse CLI argument
   - Load LLM configuration from `.env.agent.secret`
   - Build HTTP request to LLM API (OpenAI-compatible `/v1/chat/completions` endpoint)
   - Send request with timeout (60 seconds)
   - Parse JSON response
3. **Output**: Single JSON line to stdout with `answer` and `tool_calls` fields

### Code Organization

```
agent.py
├── load_env() - Load configuration from .env.agent.secret
├── call_llm(question) - Send request to LLM API, return response
├── format_response(llm_response) - Extract answer, build output JSON
├── main() - Entry point: parse args, call LLM, output JSON
└── Error handling - Catch exceptions, exit with code 0 on success
```

### Libraries

- `sys` / `argparse` - Command-line argument parsing
- `os` - Environment variable access
- `httpx` - HTTP client (already in project dependencies)
- `json` - JSON parsing and serialization
- `python-dotenv` - Load `.env.agent.secret` file

### Error Handling

- **No argument provided**: Print usage to stderr, exit with error
- **LLM API error**: Catch HTTP errors, print to stderr, return error message in JSON
- **Timeout**: Set 60-second timeout on HTTP request
- **Invalid response**: Handle gracefully, return error in JSON

### Output Format

```json
{"answer": "<LLM response text>", "tool_calls": []}
```

- Only valid JSON to stdout
- All debug/logging output to stderr using `print(..., file=sys.stderr)`

### Testing Strategy

- Run `agent.py` as subprocess with a test question
- Parse stdout as JSON
- Verify `answer` field exists and is non-empty
- Verify `tool_calls` field exists and is empty array
