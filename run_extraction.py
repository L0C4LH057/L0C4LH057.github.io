#!/usr/bin/env python3
"""Run the markdown extraction script."""

import subprocess
import sys

def main():
    """Run the extraction script."""
    try:
        result = subprocess.run(
            [sys.executable, "extract_markdown.py"],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        print("Output:", result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        # Read and display the extracted markdown
        try:
            with open('./posts/atom-of-thought-the-token-efficiency-revolution-in-llm-reasoning.md', 'r', encoding='utf-8') as f:
                markdown_content = f.read()
                print("\n" + "="*80)
                print("EXTRACTED MARKDOWN CONTENT:")
                print("="*80)
                print(markdown_content[:2000] + "..." if len(markdown_content) > 2000 else markdown_content)
                if len(markdown_content) > 2000:
                    print(f"\n... (truncated, total length: {len(markdown_content)} characters)")
        except FileNotFoundError:
            print("Markdown file not created yet")
            
    except Exception as e:
        print(f"Error running extraction: {str(e)}")

if __name__ == "__main__":
    main()