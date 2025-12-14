"""
Minimal one-call smoke test to verify OpenAI API access.

Usage:
  export OPENAI_API_KEY=your_key
  uv run python scripts/openai_smoke.py --model gpt-4o-mini
"""
import argparse
import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path for local execution.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm.client import OpenAIClient


def main():
    parser = argparse.ArgumentParser(description="OpenAI API smoke test (single call).")
    parser.add_argument("--model", default="gpt-4o-mini", help="Model name to test.")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY before running this script.")

    client = OpenAIClient(api_key=api_key, model=args.model)
    prompt = "Say a short greeting with exactly 3 words."
    resp = client.chat(prompt, max_retries=1)
    print("Response:", resp)


if __name__ == "__main__":
    main()
