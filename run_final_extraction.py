#!/usr/bin/env python3
"""Run the final extraction script."""

import subprocess
import sys

# Run the extraction
result = subprocess.run(
    [sys.executable, "extract_markdown_final.py"],
    capture_output=True,
    text=True,
    encoding='utf-8'
)

print("Output:")
print(result.stdout)

if result.stderr:
    print("\nErrors:")
    print(result.stderr)

# Read the output file
try:
    with open('./posts/atom-of-thought-the-token-efficiency-revolution-in-llm-reasoning_clean.md', 'r', encoding='utf-8') as f:
        content = f.read()
        print("\n" + "="*80)
        print("FULL EXTRACTED MARKDOWN:")
        print("="*80)
        print(content)
except FileNotFoundError:
    print("Output file not found")