#!/usr/bin/env python3
"""
Simple extraction of markdown from HTML file.
"""

import re
import html

def clean_text(text):
    """Clean text by removing HTML tags and normalizing whitespace."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_and_convert():
    """Extract post body and convert to markdown."""
    try:
        # Read HTML file
        with open('./posts/atom-of-thought-the-token-efficiency-revolution-in-llm-reasoning_preview.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extract post body
        post_body_match = re.search(r'<div[^>]*class="[^"]*post-body[^"]*"[^>]*>(.*?)</div>', html_content, re.DOTALL)
        if not post_body_match:
            print("Could not find post body")
            return
        
        post_body = post_body_match.group(1)
        
        # Extract title and subtitle
        title_match = re.search(r'<h1[^>]*class="post-title"[^>]*>(.*?)</h1>', html_content, re.DOTALL)
        subtitle_match = re.search(r'<p[^>]*class="post-subtitle"[^>]*>(.*?)</p>', html_content, re.DOTALL)
        
        title = clean_text(title_match.group(1)) if title_match else "Atom of Thought: The Token Efficiency Revolution in LLM Reasoning"
        subtitle = clean_text(subtitle_match.group(1)) if subtitle_match else "How a new reasoning paradigm is reducing LLM costs by 70-90% while improving accuracy"
        
        # Start building markdown
        markdown_lines = [f"# {title}", "", subtitle, "", "---", ""]
        
        # Process the post body
        lines = post_body.split('\n')
        in_code_block = False
        in_table = False
        table_rows = []
        
        for line in lines:
            line = line.strip()
            
            # Handle code blocks
            if '<pre>' in line or '<code>' in line:
                in_code_block = True
                # Extract code
                code_match = re.search(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', line, re.DOTALL)
                if code_match:
                    code = code_match.group(1)
                    code = html.unescape(code)
                    markdown_lines.append(f"```\n{code}\n```")
                continue
            
            if in_code_block and ('</pre>' in line or '</code>' in line):
                in_code_block = False
                continue
            
            if in_code_block:
                # Keep code as-is
                markdown_lines.append(line)
                continue
            
            # Handle tables
            if '<table' in line:
                in_table = True
                table_rows = []
                continue
            
            if in_table and '</table>' in line:
                in_table = False
                # Convert table to markdown
                if table_rows:
                    # Assume first row is header
                    header = table_rows[0]
                    markdown_lines.append(f"| {' | '.join(header)} |")
                    markdown_lines.append(f"| {' | '.join(['---'] * len(header))} |")
                    for row in table_rows[1:]:
                        markdown_lines.append(f"| {' | '.join(row)} |")
                    markdown_lines.append("")
                continue
            
            if in_table:
                # Extract table cells
                cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', line)
                if cells:
                    cleaned_cells = [clean_text(cell) for cell in cells]
                    table_rows.append(cleaned_cells)
                continue
            
            # Handle headings
            for i in range(1, 4):
                heading_match = re.match(rf'<h{i}[^>]*>(.*?)</h{i}>', line)
                if heading_match:
                    content = clean_text(heading_match.group(1))
                    markdown_lines.append(f"{'#' * i} {content}")
                    markdown_lines.append("")
                    break
            else:
                # Handle paragraphs
                if '<p>' in line:
                    para_match = re.search(r'<p[^>]*>(.*?)</p>', line, re.DOTALL)
                    if para_match:
                        content = clean_text(para_match.group(1))
                        # Handle bold text
                        content = re.sub(r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**', content)
                        # Handle italic text
                        content = re.sub(r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*', content)
                        # Handle links
                        content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', content)
                        markdown_lines.append(content)
                        markdown_lines.append("")
                
                # Handle lists
                elif '<li>' in line:
                    li_match = re.search(r'<li[^>]*>(.*?)</li>', line, re.DOTALL)
                    if li_match:
                        content = clean_text(li_match.group(1))
                        # Check if it's in an ordered list
                        if '<ol>' in lines[max(0, lines.index(line)-5):lines.index(line)]:
                            # Find the index
                            list_start = max(0, lines.index(line)-5)
                            list_context = '\n'.join(lines[list_start:lines.index(line)+1])
                            ol_match = re.search(r'<ol[^>]*>', list_context)
                            if ol_match:
                                # Count previous li tags in this ol
                                prev_lis = re.findall(r'<li[^>]*>', list_context[:list_context.rfind('<li')])
                                number = len(prev_lis) + 1
                                markdown_lines.append(f"{number}. {content}")
                            else:
                                markdown_lines.append(f"* {content}")
                        else:
                            markdown_lines.append(f"* {content}")
        
        # Join all lines
        final_markdown = '\n'.join(markdown_lines)
        
        # Write to file
        output_file = "./posts/atom-of-thought-the-token-efficiency-revolution-in-llm-reasoning_simple.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_markdown)
        
        print(f"Successfully created: {output_file}")
        print(f"Length: {len(final_markdown)} characters")
        
        # Show preview
        print("\n" + "="*80)
        print("PREVIEW (first 2000 chars):")
        print("="*80)
        print(final_markdown[:2000])
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extract_and_convert()