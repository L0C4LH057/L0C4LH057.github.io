#!/usr/bin/env python3
"""
Extract blog post content from HTML and convert to clean markdown format.
Focuses on extracting content from <div class="post-body"> tags.
"""

import re
from typing import Optional, List, Dict, Tuple
import html
from dataclasses import dataclass


@dataclass
class MarkdownConverter:
    """Convert HTML content to clean markdown format."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        # Decode HTML entities
        text = html.unescape(text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    @staticmethod
    def convert_heading(match: re.Match, level: int) -> str:
        """Convert HTML heading to markdown."""
        content = match.group(1)
        content = MarkdownConverter.clean_text(content)
        return f"{'#' * level} {content}\n\n"
    
    @staticmethod
    def convert_paragraph(match: re.Match) -> str:
        """Convert HTML paragraph to markdown."""
        content = match.group(1)
        content = MarkdownConverter.clean_text(content)
        return f"{content}\n\n"
    
    @staticmethod
    def convert_list_item(match: re.Match, is_ordered: bool = False) -> str:
        """Convert HTML list item to markdown."""
        content = match.group(1)
        content = MarkdownConverter.clean_text(content)
        # Remove any nested <li> tags that might have been captured
        content = re.sub(r'<li[^>]*>.*?</li>', '', content)
        return f"* {content}\n"
    
    @staticmethod
    def convert_ordered_list_item(match: re.Match, counter: int) -> str:
        """Convert HTML ordered list item to markdown."""
        content = match.group(1)
        content = MarkdownConverter.clean_text(content)
        # Remove any nested <li> tags that might have been captured
        content = re.sub(r'<li[^>]*>.*?</li>', '', content)
        return f"{counter}. {content}\n"
    
    @staticmethod
    def convert_code_block(match: re.Match) -> str:
        """Convert HTML code block to markdown."""
        code = match.group(1)
        # Clean the code
        code = html.unescape(code)
        code = code.strip()
        # Check for language class
        lang_match = re.search(r'class="[^"]*language-([^"\s]+)', match.group(0) or '')
        language = lang_match.group(1) if lang_match else ''
        return f"```{language}\n{code}\n```\n\n"
    
    @staticmethod
    def convert_inline_code(match: re.Match) -> str:
        """Convert HTML inline code to markdown."""
        code = match.group(1)
        code = html.unescape(code)
        code = code.strip()
        return f"`{code}`"
    
    @staticmethod
    def convert_strong(match: re.Match) -> str:
        """Convert HTML strong/bold to markdown."""
        content = match.group(1)
        content = MarkdownConverter.clean_text(content)
        return f"**{content}**"
    
    @staticmethod
    def convert_em(match: re.Match) -> str:
        """Convert HTML emphasis/italic to markdown."""
        content = match.group(1)
        content = MarkdownConverter.clean_text(content)
        return f"*{content}*"
    
    @staticmethod
    def convert_link(match: re.Match) -> str:
        """Convert HTML link to markdown."""
        href = match.group(1)
        text = match.group(2) or href
        text = MarkdownConverter.clean_text(text)
        return f"[{text}]({href})"
    
    @staticmethod
    def convert_blockquote(match: re.Match) -> str:
        """Convert HTML blockquote to markdown."""
        content = match.group(1)
        content = MarkdownConverter.clean_text(content)
        # Split into lines and add > to each line
        lines = content.split('\n')
        quoted_lines = [f"> {line.strip()}" for line in lines if line.strip()]
        return '\n'.join(quoted_lines) + '\n\n'
    
    @staticmethod
    def convert_table(match: re.Match) -> str:
        """Convert HTML table to markdown."""
        table_html = match.group(0)
        
        # Extract table rows
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
        if not rows:
            return ""
        
        markdown_rows = []
        
        for i, row in enumerate(rows):
            # Extract cells
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
            if not cells:
                continue
            
            # Clean cell content
            cleaned_cells = []
            for cell in cells:
                # Remove any HTML tags from cell content
                cell_clean = re.sub(r'<[^>]+>', '', cell)
                cell_clean = MarkdownConverter.clean_text(cell_clean)
                cleaned_cells.append(cell_clean)
            
            # Create markdown row
            markdown_row = "| " + " | ".join(cleaned_cells) + " |"
            markdown_rows.append(markdown_row)
            
            # Add separator after header row
            if i == 0:
                separator = "| " + " | ".join(["---"] * len(cleaned_cells)) + " |"
                markdown_rows.append(separator)
        
        return "\n".join(markdown_rows) + "\n\n"
    
    @staticmethod
    def convert_highlight_box(match: re.Match) -> str:
        """Convert highlight box to markdown blockquote."""
        content = match.group(1)
        content = MarkdownConverter.clean_text(content)
        # Remove any HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        return f"> **Note:** {content}\n\n"
    
    @staticmethod
    def html_to_markdown(html_content: str) -> str:
        """Convert HTML content to markdown."""
        if not html_content:
            return ""
        
        # Remove script and style tags
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Convert highlight boxes first (special handling)
        html_content = re.sub(
            r'<div[^>]*class="[^"]*highlight-box[^"]*"[^>]*>(.*?)</div>',
            lambda m: MarkdownConverter.convert_highlight_box(m),
            html_content,
            flags=re.DOTALL
        )
        
        # Convert tables
        html_content = re.sub(
            r'<table[^>]*>.*?</table>',
            lambda m: MarkdownConverter.convert_table(m),
            html_content,
            flags=re.DOTALL
        )
        
        # Convert code blocks
        html_content = re.sub(
            r'<pre[^>]*><code[^>]*>(.*?)</code></pre>',
            lambda m: MarkdownConverter.convert_code_block(m),
            html_content,
            flags=re.DOTALL
        )
        
        # Convert inline code
        html_content = re.sub(
            r'<code[^>]*>(.*?)</code>',
            lambda m: MarkdownConverter.convert_inline_code(m),
            html_content
        )
        
        # Convert headings
        for level in range(1, 7):
            html_content = re.sub(
                rf'<h{level}[^>]*>(.*?)</h{level}>',
                lambda m, l=level: MarkdownConverter.convert_heading(m, l),
                html_content,
                flags=re.DOTALL
            )
        
        # Convert blockquotes
        html_content = re.sub(
            r'<blockquote[^>]*>(.*?)</blockquote>',
            lambda m: MarkdownConverter.convert_blockquote(m),
            html_content,
            flags=re.DOTALL
        )
        
        # Convert unordered lists
        html_content = re.sub(
            r'<ul[^>]*>(.*?)</ul>',
            lambda m: MarkdownConverter._convert_unordered_list(m.group(1)),
            html_content,
            flags=re.DOTALL
        )
        
        # Convert ordered lists
        html_content = re.sub(
            r'<ol[^>]*>(.*?)</ol>',
            lambda m: MarkdownConverter._convert_ordered_list(m.group(1)),
            html_content,
            flags=re.DOTALL
        )
        
        # Convert paragraphs
        html_content = re.sub(
            r'<p[^>]*>(.*?)</p>',
            lambda m: MarkdownConverter.convert_paragraph(m),
            html_content,
            flags=re.DOTALL
        )
        
        # Convert strong/bold
        html_content = re.sub(
            r'<(strong|b)[^>]*>(.*?)</\1>',
            lambda m: MarkdownConverter.convert_strong(m),
            html_content,
            flags=re.DOTALL
        )
        
        # Convert emphasis/italic
        html_content = re.sub(
            r'<(em|i)[^>]*>(.*?)</\1>',
            lambda m: MarkdownConverter.convert_em(m),
            html_content,
            flags=re.DOTALL
        )
        
        # Convert links
        html_content = re.sub(
            r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            lambda m: MarkdownConverter.convert_link(m),
            html_content,
            flags=re.DOTALL
        )
        
        # Remove any remaining HTML tags
        html_content = re.sub(r'<[^>]+>', '', html_content)
        
        # Clean up whitespace
        html_content = re.sub(r'\n\s*\n\s*\n', '\n\n', html_content)
        html_content = re.sub(r'^\s+|\s+$', '', html_content, flags=re.MULTILINE)
        
        return html_content
    
    @staticmethod
    def _convert_unordered_list(html_content: str) -> str:
        """Convert unordered list HTML to markdown."""
        items = re.findall(r'<li[^>]*>(.*?)</li>', html_content, re.DOTALL)
        if not items:
            return ""
        
        markdown_items = []
        for item in items:
            # Clean the item content
            item_clean = MarkdownConverter.clean_text(item)
            # Remove any nested list HTML that might remain
            item_clean = re.sub(r'<[^>]+>', '', item_clean)
            markdown_items.append(f"* {item_clean}")
        
        return '\n'.join(markdown_items) + '\n\n'
    
    @staticmethod
    def _convert_ordered_list(html_content: str) -> str:
        """Convert ordered list HTML to markdown."""
        items = re.findall(r'<li[^>]*>(.*?)</li>', html_content, re.DOTALL)
        if not items:
            return ""
        
        markdown_items = []
        for i, item in enumerate(items, 1):
            # Clean the item content
            item_clean = MarkdownConverter.clean_text(item)
            # Remove any nested list HTML that might remain
            item_clean = re.sub(r'<[^>]+>', '', item_clean)
            markdown_items.append(f"{i}. {item_clean}")
        
        return '\n'.join(markdown_items) + '\n\n'


def extract_post_body(html_content: str) -> Optional[str]:
    """Extract content from post-body div."""
    # Look for post-body div
    pattern = r'<div[^>]*class="[^"]*post-body[^"]*"[^>]*>(.*?)</div>'
    match = re.search(pattern, html_content, re.DOTALL)
    
    if match:
        return match.group(1)
    
    # Try alternative patterns
    patterns = [
        r'<div[^>]*id="postBody"[^>]*>(.*?)</div>',
        r'<article[^>]*>(.*?)</article>',
        r'<main[^>]*>(.*?)</main>',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.DOTALL)
        if match:
            return match.group(1)
    
    return None


def main():
    """Main function to extract and convert blog post."""
    try:
        # Read the HTML file
        with open('./posts/atom-of-thought-the-token-efficiency-revolution-in-llm-reasoning_preview.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extract post body
        post_body = extract_post_body(html_content)
        
        if not post_body:
            print("Error: Could not find post body content")
            return
        
        # Convert to markdown
        converter = MarkdownConverter()
        markdown_content = converter.html_to_markdown(post_body)
        
        # Add title and metadata
        title_match = re.search(r'<h1[^>]*class="post-title"[^>]*>(.*?)</h1>', html_content, re.DOTALL)
        subtitle_match = re.search(r'<p[^>]*class="post-subtitle"[^>]*>(.*?)</p>', html_content, re.DOTALL)
        
        title = converter.clean_text(title_match.group(1)) if title_match else "Atom of Thought: The Token Efficiency Revolution in LLM Reasoning"
        subtitle = converter.clean_text(subtitle_match.group(1)) if subtitle_match else "How a new reasoning paradigm is reducing LLM costs by 70-90% while improving accuracy"
        
        # Create final markdown
        final_markdown = f"""# {title}

{subtitle}

---

{markdown_content}
"""
        
        # Write to file
        output_file = "./posts/atom-of-thought-the-token-efficiency-revolution-in-llm-reasoning.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_markdown)
        
        print(f"Successfully extracted and converted to markdown: {output_file}")
        print(f"Markdown length: {len(final_markdown)} characters")
        
    except FileNotFoundError:
        print("Error: HTML file not found")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()