#!/usr/bin/env python3
"""
Final extraction of blog post content to markdown.
"""

import re
import html
from typing import List, Tuple

def clean_html_text(text: str) -> str:
    """Clean HTML text by removing tags and normalizing."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_post_content(html_file_path: str) -> Tuple[str, str, str]:
    """Extract title, subtitle, and post body from HTML file."""
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Extract title
    title_match = re.search(r'<h1[^>]*class="post-title"[^>]*>(.*?)</h1>', html_content, re.DOTALL)
    title = clean_html_text(title_match.group(1)) if title_match else "Atom of Thought: The Token Efficiency Revolution in LLM Reasoning"
    
    # Extract subtitle
    subtitle_match = re.search(r'<p[^>]*class="post-subtitle"[^>]*>(.*?)</p>', html_content, re.DOTALL)
    subtitle = clean_html_text(subtitle_match.group(1)) if subtitle_match else "How a new reasoning paradigm is reducing LLM costs by 70-90% while improving accuracy"
    
    # Extract post body
    post_body_match = re.search(r'<div[^>]*class="[^"]*post-body[^"]*"[^>]*>(.*?)</div>', html_content, re.DOTALL)
    if not post_body_match:
        raise ValueError("Could not find post body content")
    
    post_body = post_body_match.group(1)
    
    return title, subtitle, post_body

def convert_html_to_markdown(html_content: str) -> str:
    """Convert HTML content to markdown format."""
    # Remove script and style tags
    html_content = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL)
    
    # Process in stages
    markdown_parts = []
    
    # Split by lines for easier processing
    lines = html_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Handle headings
        heading_match = re.match(r'<h([2-3])[^>]*>(.*?)</h\1>', line)
        if heading_match:
            level = int(heading_match.group(1))
            content = clean_html_text(heading_match.group(2))
            markdown_parts.append(f"{'#' * level} {content}\n")
            i += 1
            continue
        
        # Handle paragraphs
        if line.startswith('<p>') or '<p ' in line:
            # Extract paragraph content
            para_content = line
            # Handle multi-line paragraphs
            while i + 1 < len(lines) and not lines[i + 1].strip().startswith(('<p', '<h', '<div', '<ul', '<ol', '<table', '<pre')):
                i += 1
                para_content += ' ' + lines[i].strip()
            
            # Clean the paragraph
            para_text = clean_html_text(para_content)
            
            # Apply markdown formatting
            # Bold
            para_text = re.sub(r'\*\*(.*?)\*\*', r'**\1**', para_text)
            # Italic
            para_text = re.sub(r'\*(.*?)\*', r'*\1*', para_text)
            # Code
            para_text = re.sub(r'`(.*?)`', r'`\1`', para_text)
            
            markdown_parts.append(f"{para_text}\n")
            i += 1
            continue
        
        # Handle unordered lists
        if '<ul>' in line or line.startswith('<li>') or '<li ' in line:
            list_items = []
            # Collect all list items
            while i < len(lines) and ('<li>' in lines[i] or '<li ' in lines[i]):
                li_match = re.search(r'<li[^>]*>(.*?)</li>', lines[i], re.DOTALL)
                if li_match:
                    item_content = clean_html_text(li_match.group(1))
                    list_items.append(f"* {item_content}")
                i += 1
            
            if list_items:
                markdown_parts.append('\n'.join(list_items) + '\n')
            continue
        
        # Handle ordered lists
        if '<ol>' in line:
            # Skip the opening ol tag
            i += 1
            list_items = []
            item_num = 1
            
            # Collect all list items
            while i < len(lines) and ('<li>' in lines[i] or '<li ' in lines[i]):
                li_match = re.search(r'<li[^>]*>(.*?)</li>', lines[i], re.DOTALL)
                if li_match:
                    item_content = clean_html_text(li_match.group(1))
                    list_items.append(f"{item_num}. {item_content}")
                    item_num += 1
                i += 1
            
            if list_items:
                markdown_parts.append('\n'.join(list_items) + '\n')
            continue
        
        # Handle code blocks
        if '<pre>' in line or '<code>' in line:
            # Find the end of the code block
            code_start = i
            while i < len(lines) and ('</pre>' not in lines[i] and '</code>' not in lines[i]):
                i += 1
            
            code_block = '\n'.join(lines[code_start:i+1])
            # Extract code
            code_match = re.search(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', code_block, re.DOTALL)
            if code_match:
                code = code_match.group(1)
                code = html.unescape(code.strip())
                markdown_parts.append(f"```\n{code}\n```\n")
            
            i += 1
            continue
        
        # Handle highlight boxes
        if 'highlight-box' in line:
            # Extract highlight box content
            box_content = line
            while i + 1 < len(lines) and '</div>' not in lines[i]:
                i += 1
                box_content += ' ' + lines[i].strip()
            
            # Extract text from highlight box
            box_text = clean_html_text(box_content)
            markdown_parts.append(f"> **Note:** {box_text}\n")
            i += 1
            continue
        
        # Handle tables - simplified approach
        if '<table' in line:
            table_lines = [line]
            while i + 1 < len(lines) and '</table>' not in lines[i]:
                i += 1
                table_lines.append(lines[i])
            
            table_html = '\n'.join(table_lines)
            
            # Extract rows
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
            if rows:
                table_markdown = []
                for row_idx, row in enumerate(rows):
                    # Extract cells
                    cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
                    if cells:
                        cleaned_cells = [clean_html_text(cell) for cell in cells]
                        table_markdown.append('| ' + ' | '.join(cleaned_cells) + ' |')
                        
                        # Add separator after header
                        if row_idx == 0:
                            table_markdown.append('| ' + ' | '.join(['---'] * len(cleaned_cells)) + ' |')
                
                if table_markdown:
                    markdown_parts.append('\n'.join(table_markdown) + '\n')
            
            i += 1
            continue
        
        i += 1
    
    # Join all parts
    markdown = '\n'.join(markdown_parts)
    
    # Clean up extra newlines
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    
    return markdown

def main():
    """Main function."""
    try:
        html_file = "./posts/atom-of-thought-the-token-efficiency-revolution-in-llm-reasoning_preview.html"
        
        # Extract content
        title, subtitle, post_body = extract_post_content(html_file)
        
        # Convert to markdown
        markdown_content = convert_html_to_markdown(post_body)
        
        # Create final markdown document
        final_markdown = f"""# {title}

{subtitle}

---

{markdown_content}
"""
        
        # Write to file
        output_file = "./posts/atom-of-thought-the-token-efficiency-revolution-in-llm-reasoning_clean.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_markdown)
        
        print(f"Successfully extracted markdown to: {output_file}")
        print(f"Title: {title}")
        print(f"Subtitle: {subtitle}")
        print(f"Markdown length: {len(final_markdown)} characters")
        
        # Display preview
        print("\n" + "="*80)
        print("PREVIEW (first 2500 characters):")
        print("="*80)
        print(final_markdown[:2500])
        
        if len(final_markdown) > 2500:
            print(f"\n... (truncated, total: {len(final_markdown)} characters)")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()