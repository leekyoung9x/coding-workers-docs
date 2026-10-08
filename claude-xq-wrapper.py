#!/usr/bin/env python3
"""
Claude Code wrapper qua XQ API
Giả lập Claude CLI -p mode, gọi XQ API trực tiếp
"""
import sys
import json
import argparse
import subprocess
from pathlib import Path

XQ_API_KEY = "sk-_4XS1wddWY7uzWx6v93WHj9FM-apXbj87VE0zXKzo9U"
XQ_ENDPOINT = "https://xqapi.com/v1/messages"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--print", dest="prompt", help="Prompt (print mode)")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Model name")
    parser.add_argument("--max-turns", type=int, default=10, help="Max turns (ignored in wrapper)")
    parser.add_argument("--allowedTools", help="Allowed tools (ignored in wrapper)")
    parser.add_argument("--output-format", default="json", choices=["json", "text"])
    parser.add_argument("--dangerously-skip-permissions", action="store_true")
    parser.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--max-budget-usd", type=float, help="Budget limit (ignored)")
    
    args, unknown = parser.parse_known_args()
    
    if not args.prompt:
        print(json.dumps({"error": "No prompt provided. Use -p 'your task'"}))
        sys.exit(1)
    
    # Map model names
    model_map = {
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-6",
        "haiku": "claude-haiku-5-5",
        "claude-sonnet-4-6": "claude-sonnet-4-6",
        "claude-opus-4-6": "claude-opus-4-6",
        "claude-haiku-5-5": "claude-haiku-5-5",
    }
    model = model_map.get(args.model, "claude-sonnet-4-6")
    
    # Build request payload
    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": args.prompt}]
    }
    
    # Call XQ API via curl
    curl_cmd = [
        "curl", "-s", "-X", "POST", XQ_ENDPOINT,
        "-H", f"x-api-key: {XQ_API_KEY}",
        "-H", "content-type: application/json",
        "-H", "anthropic-version: 2023-06-01",
        "-d", json.dumps(payload)
    ]
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=120)
        response = json.loads(result.stdout)
        
        # Extract text
        text_content = ""
        if "content" in response and isinstance(response["content"], list):
            for block in response["content"]:
                if block.get("type") == "text":
                    text_content += block.get("text", "")
        
        # Build Claude Code-like JSON response
        output = {
            "type": "result",
            "subtype": "success",
            "result": text_content,
            "session_id": response.get("id", "unknown"),
            "num_turns": 1,
            "total_cost_usd": 0.0,
            "usage": response.get("usage", {}),
            "modelUsage": {model: {"costUSD": 0.0}},
            "stop_reason": response.get("stop_reason", "end_turn"),
            "terminal_reason": "completed"
        }
        
        if args.output_format == "json":
            print(json.dumps(output, ensure_ascii=False))
        else:
            print(text_content)
        
    except subprocess.TimeoutExpired:
        error_out = {
            "type": "result",
            "subtype": "error_timeout",
            "result": "Request timeout after 120s",
            "is_error": True
        }
        print(json.dumps(error_out))
        sys.exit(1)
    except Exception as e:
        error_out = {
            "type": "result",
            "subtype": "error",
            "result": f"Wrapper error: {str(e)}",
            "is_error": True
        }
        print(json.dumps(error_out))
        sys.exit(1)


if __name__ == "__main__":
    main()
