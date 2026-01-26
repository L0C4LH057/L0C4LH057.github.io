#!/usr/bin/env python3
"""Execute the extraction script."""

import subprocess
import sys

# Run the simple extraction script
result = subprocess.run(
    [sys.executable, "extract_simple.py"],
    capture_output=True,
    text=True,
    encoding='utf-8'
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)

# Read and display the result
try:
    with open('./posts/atom-of-thought-the-token-efficiency-revolution-in-llm-reasoning_simple.md', 'r', encoding='utf-8') as f:
        content = f.read()
        print("\n" + "="*80)
        print("EXTRACTED MARKDOWN:")
        print("="*80)
        print(content)
except FileNotFoundError:
    print("Output file not found")