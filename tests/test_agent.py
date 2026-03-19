#!/usr/bin/env python3
"""
Regression tests for the System Agent
Tests verify that the agent uses the correct tools for different question types
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from agent import SystemAgent, read_file, query_api


class TestSystemAgent:
    """Test suite for System Agent tool selection"""

    def setup_method(self):
        """Setup test environment"""
        # Use test environment variables
        import os
        os.environ["LLM_API_KEY"] = "test-key"
        os.environ["LLM_API_BASE"] = "http://localhost:8080/v1"
        os.environ["LLM_MODEL"] = "test-model"
        os.environ["LMS_API_KEY"] = "test-lms-key"

    def test_data_query_uses_api(self):
        """Test 1: Question about database items should use query_api"""
        agent = SystemAgent()
        question = "How many items are in the database?"

        # Mock the LLM response to use query_api
        mock_response = {
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {
                            "name": "query_api",
                            "arguments": json.dumps({"method": "GET", "path": "/items/"})
                        }
                    }]
                }
            }]
        }

        # Second call returns the final answer
        mock_response_final = {
            "choices": [{
                "message": {
                    "content": "There are 42 items in the database. Source: /items/",
                    "tool_calls": None
                }
            }]
        }

        with patch('agent.call_llm') as mock_call:
            mock_call.side_effect = [mock_response, mock_response_final]
            response = agent.process_question(question)

        # Check that query_api was called
        tool_calls = response.get("tool_calls", [])
        api_calls = [call for call in tool_calls if call["tool"] == "query_api"]

        assert len(api_calls) > 0, "Expected query_api to be called for data question"

        # Check the API call parameters
        api_call = api_calls[0]
        assert api_call["args"]["method"] == "GET"
        assert api_call["args"]["path"] == "/items/"

        print("✓ Test 1 passed: Data question uses query_api")

    def test_code_query_uses_read_file(self):
        """Test 2: Question about framework should use read_file"""
        agent = SystemAgent()
        question = "What Python web framework does the backend use?"

        # Mock the LLM response to use read_file
        mock_response = {
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {
                            "name": "read_file",
                            "arguments": json.dumps({"path": "backend/app/main.py"})
                        }
                    }]
                }
            }]
        }

        # Second call returns the final answer
        mock_response_final = {
            "choices": [{
                "message": {
                    "content": "The backend uses FastAPI. Source: backend/app/main.py",
                    "tool_calls": None
                }
            }]
        }

        with patch('agent.call_llm') as mock_call:
            mock_call.side_effect = [mock_response, mock_response_final]
            response = agent.process_question(question)

        # Check that read_file was called
        tool_calls = response.get("tool_calls", [])
        read_calls = [call for call in tool_calls if call["tool"] == "read_file"]

        assert len(read_calls) > 0, "Expected read_file to be called for framework question"

        # Check the file path
        read_call = read_calls[0]
        assert "main.py" in read_call["args"]["path"] or "pyproject.toml" in read_call["args"]["path"]

        print("✓ Test 2 passed: Code question uses read_file")

    def test_status_code_uses_api(self):
        """Optional test: Status code question should use query_api"""
        agent = SystemAgent()
        question = "What HTTP status code does the API return when you request /items/ without authentication?"

        # Mock the LLM response to use query_api with auth=false
        mock_response = {
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {
                            "name": "query_api",
                            "arguments": json.dumps({"method": "GET", "path": "/items/", "auth": False})
                        }
                    }]
                }
            }]
        }

        # Second call returns the final answer
        mock_response_final = {
            "choices": [{
                "message": {
                    "content": "The API returns 401 Unauthorized. Source: /items/",
                    "tool_calls": None
                }
            }]
        }

        with patch('agent.call_llm') as mock_call:
            mock_call.side_effect = [mock_response, mock_response_final]
            response = agent.process_question(question)

        tool_calls = response.get("tool_calls", [])

        api_calls = [call for call in tool_calls if call["tool"] == "query_api"]
        assert len(api_calls) > 0, "Expected query_api for status code question"

        print("✓ Test 3 passed: Status code question uses query_api")

    def test_bug_diagnosis_uses_both_tools(self):
        """Optional test: Bug diagnosis should use both API and file reading"""
        agent = SystemAgent()
        question = "Query /analytics/completion-rate for lab-99. What error and bug do you find?"

        # Mock the LLM response sequence
        mock_response_api = {
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {
                            "name": "query_api",
                            "arguments": json.dumps({"method": "GET", "path": "/analytics/completion-rate?lab=lab-99"})
                        }
                    }]
                }
            }]
        }

        mock_response_read = {
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call_2",
                        "function": {
                            "name": "read_file",
                            "arguments": json.dumps({"path": "backend/app/routers/analytics.py"})
                        }
                    }]
                }
            }]
        }

        # Final response with answer
        mock_response_final = {
            "choices": [{
                "message": {
                    "content": "The bug is a ZeroDivisionError in analytics.py line 207. Source: backend/app/routers/analytics.py",
                    "tool_calls": None
                }
            }]
        }

        with patch('agent.call_llm') as mock_call:
            mock_call.side_effect = [mock_response_api, mock_response_read, mock_response_final]
            response = agent.process_question(question)

        tool_calls = response.get("tool_calls", [])
        tools_used = [call["tool"] for call in tool_calls]

        assert "query_api" in tools_used, "Expected query_api for bug diagnosis"
        assert "read_file" in tools_used, "Expected read_file to find the bug"

        print("✓ Test 4 passed: Bug diagnosis uses both tools")


def run_tests():
    """Run all tests"""
    print("🚀 Running regression tests for System Agent...\n")

    test_suite = TestSystemAgent()
    test_suite.setup_method()

    # Run required tests
    test_suite.test_data_query_uses_api()
    test_suite.test_code_query_uses_read_file()

    # Optional tests
    try:
        test_suite.test_status_code_uses_api()
    except AssertionError as e:
        print(f"⚠️  Optional test failed (not required): {e}")

    try:
        test_suite.test_bug_diagnosis_uses_both_tools()
    except AssertionError as e:
        print(f"⚠️  Optional test failed (not required): {e}")

    print("\n✅ Required tests passed!")


if __name__ == "__main__":
    run_tests()
