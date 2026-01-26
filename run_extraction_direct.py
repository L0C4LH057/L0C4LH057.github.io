#!/usr/bin/env python3
"""
Direct extraction of markdown from HTML file.
This is a simplified version that extracts and converts the content.
"""

import re
import html
from typing import Optional

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Decode HTML entities
    text = html.unescape(text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def extract_post_body(html_content: str) -> Optional[str]:
    """Extract content from post-body div."""
    # Look for post-body div
    pattern = r'<div[^>]*class="[^"]*post-body[^"]*"[^>]*>(.*?)</div>'
    match = re.search(pattern, html_content, re.DOTALL)
    
    if match:
        return match.group(1)
    return None

def html_to_markdown(html_content: str) -> str:
    """Convert HTML content to markdown."""
    if not html_content:
        return ""
    
    # Remove script and style tags
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
    
    # Convert highlight boxes
    def convert_highlight_box(match):
        content = match.group(1)
        content = clean_text(content)
        content = re.sub(r'<[^>]+>', '', content)
        return f"> **Note:** {content}\n\n"
    
    html_content = re.sub(
        r'<div[^>]*class="[^"]*highlight-box[^"]*"[^>]*>(.*?)</div>',
        convert_highlight_box,
        html_content,
        flags=re.DOTALL
    )
    
    # Convert tables
    def convert_table(match):
        table_html = match.group(0)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
        if not rows:
            return ""
        
        markdown_rows = []
        for i, row in enumerate(rows):
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
            if not cells:
                continue
            
            cleaned_cells = []
            for cell in cells:
                cell_clean = re.sub(r'<[^>]+>', '', cell)
                cell_clean = clean_text(cell_clean)
                cleaned_cells.append(cell_clean)
            
            markdown_row = "| " + " | ".join(cleaned_cells) + " |"
            markdown_rows.append(markdown_row)
            
            if i == 0:
                separator = "| " + " | ".join(["---"] * len(cleaned_cells)) + " |"
                markdown_rows.append(separator)
        
        return "\n".join(markdown_rows) + "\n\n"
    
    html_content = re.sub(
        r'<table[^>]*>.*?</table>',
        convert_table,
        html_content,
        flags=re.DOTALL
    )
    
    # Convert code blocks
    def convert_code_block(match):
        code = match.group(1)
        code = html.unescape(code)
        code = code.strip()
        lang_match = re.search(r'class="[^"]*language-([^"\s]+)', match.group(0) or '')
        language = lang_match.group(1) if lang_match else ''
        return f"```{language}\n{code}\n```\n\n"
    
    html_content = re.sub(
        r'<pre[^>]*><code[^>]*>(.*?)</code></pre>',
        convert_code_block,
        html_content,
        flags=re.DOTALL
    )
    
    # Convert headings
    for level in range(1, 7):
        def convert_heading(match, l=level):
            content = match.group(1)
            content = clean_text(content)
            return f"{'#' * l} {content}\n\n"
        
        html_content = re.sub(
            rf'<h{level}[^>]*>(.*?)</h{level}>',
            convert_heading,
            html_content,
            flags=re.DOTALL
        )
    
    # Convert paragraphs
    def convert_paragraph(match):
        content = match.group(1)
        content = clean_text(content)
        return f"{content}\n\n"
    
    html_content = re.sub(
        r'<p[^>]*>(.*?)</p>',
        convert_paragraph,
        html_content,
        flags=re.DOTALL
    )
    
    # Convert lists
    def convert_unordered_list(match):
        list_html = match.group(1)
        items = re.findall(r'<li[^>]*>(.*?)</li>', list_html, re.DOTALL)
        if not items:
            return ""
        
        markdown_items = []
        for item in items:
            item_clean = clean_text(item)
            item_clean = re.sub(r'<[^>]+>', '', item_clean)
            markdown_items.append(f"* {item_clean}")
        
        return '\n'.join(markdown_items) + '\n\n'
    
    def convert_ordered_list(match):
        list_html = match.group(1)
        items = re.findall(r'<li[^>]*>(.*?)</li>', list_html, re.DOTALL)
        if not items:
            return ""
        
        markdown_items = []
        for i, item in enumerate(items, 1):
            item_clean = clean_text(item)
            item_clean = re.sub(r'<[^>]+>', '', item_clean)
            markdown_items.append(f"{i}. {item_clean}")
        
        return '\n'.join(markdown_items) + '\n\n'
    
    html_content = re.sub(
        r'<ul[^>]*>(.*?)</ul>',
        convert_unordered_list,
        html_content,
        flags=re.DOTALL
    )
    
    html_content = re.sub(
        r'<ol[^>]*>(.*?)</ol>',
        convert_ordered_list,
        html_content,
        flags=re.DOTALL
    )
    
    # Convert strong/bold
    def convert_strong(match):
        content = match.group(2)
        content = clean_text(content)
        return f"**{content}**"
    
    html_content = re.sub(
        r'<(strong|b)[^>]*>(.*?)</\1>',
        convert_strong,
        html_content,
        flags=re.DOTALL
    )
    
    # Convert links
    def convert_link(match):
        href = match.group(1)
        text = match.group(2) or href
        text = clean_text(text)
        return f"[{text}]({href})"
    
    html_content = re.sub(
        r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
        convert_link,
        html_content,
        flags=re.DOTALL
    )
    
    # Remove any remaining HTML tags
    html_content = re.sub(r'<[^>]+>', '', html_content)
    
    # Clean up whitespace
    html_content = re.sub(r'\n\s*\n\s*\n', '\n\n', html_content)
    html_content = re.sub(r'^\s+|\s+$', '', html_content, flags=re.MULTILINE)
    
    return html_content

def main():
    """Main function."""
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
        markdown_content = html_to_markdown(post_body)
        
        # Extract title and subtitle
        title_match = re.search(r'<h1[^>]*class="post-title"[^>]*>(.*?)</h1>', html_content, re.DOTALL)
        subtitle_match = re.search(r'<p[^>]*class="post-subtitle"[^>]*>(.*?)</p>', html_content, re.DOTALL)
        
        title = clean_text(title_match.group(1)) if title_match else "Atom of Thought: The Token Efficiency Revolution in LLM Reasoning"
        subtitle = clean_text(subtitle_match.group(1)) if subtitle_match else "How a new reasoning paradigm is reducing LLM costs by 70-90% while improving accuracy"
        
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
        
        # Display first part
        print("\n" + "="*80)
        print("EXTRACTED MARKDOWN CONTENT (first 3000 chars):")
        print("="*80)
        print(final_markdown[:3000])
        if len(final_markdown) > 3000:
            print(f"\n... (truncated, total length: {len(final_markdown)} characters)")
        
    except FileNotFoundError:
        print("Error: HTML file not found")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()