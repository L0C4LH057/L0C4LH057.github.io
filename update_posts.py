#!/usr/bin/env python3
import os
import re
import copy
import shutil
from bs4 import BeautifulSoup

# Configuration
TEMPLATE_PATH = 'template.html'
POSTS_DIR = 'posts'
WRITEUPS_DIR = 'writeups'
AUTHOR_NAME = 'Bashir Kabir Zarewa'
BLOG_URL = 'https://L0C4LH057.github.io'

def load_template():
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Template file not found at {TEMPLATE_PATH}")
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        return f.read()

def process_file(file_path, template_content):
    print(f"Processing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    if not html_content.strip():
        print(f"  -> Skipping empty file.")
        return None
        
    soup = BeautifulSoup(html_content, 'html.parser')
    folder_name = os.path.basename(os.path.dirname(file_path))
    slug = os.path.splitext(os.path.basename(file_path))[0]
    
    # 1. Check if standard post by looking for .post-body or #postBody
    post_body_el = soup.find(class_='post-body') or soup.find(id='postBody')
    is_standard = post_body_el is not None
    
    if is_standard:
        # Extract title
        post_title_el = soup.find(class_='post-title')
        if post_title_el:
            title = post_title_el.get_text().strip()
        else:
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else ""
            if " | " in title:
                title = title.split(" | ")[0].strip()
                
        # Extract subtitle
        subtitle_el = soup.find(class_='post-subtitle')
        subtitle = subtitle_el.get_text().strip() if subtitle_el else ""
        
        # Extract description
        desc_meta = soup.find('meta', attrs={'name': 'description'})
        description = desc_meta.get('content', '').strip() if desc_meta else subtitle
        if not description:
            description = title
            
        # Extract date from meta-items
        date = ""
        meta_items = soup.find_all(class_='meta-item')
        for item in meta_items:
            if item.find(class_='fa-calendar-alt') or 'published' in item.get_text().lower() or 'date' in item.get_text().lower():
                date_text = item.get_text().strip()
                # Strip out labels
                for prefix in ["Published:", "Published", "Date:", "Date"]:
                    if date_text.startswith(prefix):
                        date_text = date_text[len(prefix):].strip()
                date = date_text
                break
                
        if not date:
            # Sibling or parent fallback
            calendar_icon = soup.find(class_='fa-calendar-alt')
            if calendar_icon:
                parent = calendar_icon.parent
                if parent:
                    date_text = parent.get_text().strip()
                    for prefix in ["Published:", "Published", "Date:", "Date"]:
                        if date_text.startswith(prefix):
                            date_text = date_text[len(prefix):].strip()
                    date = date_text
                    
        if not date:
            date = "July 16, 2025" # Fallback
            
        # Extract tags
        tags = ""
        for item in meta_items:
            if item.find(class_='fa-tags'):
                tags_text = item.get_text().strip()
                if tags_text.startswith("Tags:"):
                    tags_text = tags_text[5:].strip()
                elif tags_text.startswith("Tags"):
                    tags_text = tags_text[4:].strip()
                tags = tags_text
                break
                
        if not tags:
            tags_icon = soup.find(class_='fa-tags')
            if tags_icon:
                parent = tags_icon.parent
                if parent:
                    tags_text = parent.get_text().strip()
                    if tags_text.startswith("Tags:"):
                        tags_text = tags_text[5:].strip()
                    tags = tags_text
                    
        if not tags:
            tags = "Security, Technology"
            
        # Extract cover image
        cover_img_el = soup.find(class_='post-cover')
        if cover_img_el:
            img_src = cover_img_el.get('src', '')
            img_alt = cover_img_el.get('alt', '')
            featured_image = os.path.basename(img_src)
            featured_image_alt = img_alt if img_alt else title
        else:
            featured_image = "default_cover.jpg"
            featured_image_alt = title
            
        # Clean up unwanted elements inside the post-body (e.g. old share buttons, old upvote, old comments)
        for unwanted in post_body_el.find_all(class_=['share-buttons', 'engagement-bar', 'comments-section', 'audio-player']):
            unwanted.decompose()
            
        # Extract citations if present, and remove from body
        citations_el = soup.find(class_='citations')
        citations_html = ""
        if citations_el:
            citations_html = "".join([str(child) for child in citations_el.children])
            citations_el.decompose()
            
        # Get final body content inner HTML
        content = "".join([str(child) for child in post_body_el.children])
        
        # Add citations if extracted
        if citations_html:
            content += f'\n<div class="citations" style="margin-top: 3rem; border-top: 1px dashed var(--border); padding-top: 2rem;">\n<h3>References</h3>\n<ul>\n{citations_html}\n</ul>\n</div>'
            
        custom_styles = []
        custom_scripts = []
        
    else:
        # 2. Interactive custom tools (sdes.html, des.html, des-demo.html, infographic.html)
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else "Interactive Walkthrough"
        
        # Try to find subtitle/description
        subtitle = ""
        desc_el = soup.find('p', class_='text-center') or soup.find('p')
        if desc_el:
            subtitle = desc_el.get_text().strip()[:150]
        if not subtitle:
            subtitle = "Step-by-step cryptographic calculator and visual guide."
            
        description = subtitle
        date = "October 2025"
        tags = "Interactive, Cryptography, Education"
        featured_image = "default_cover.jpg"
        featured_image_alt = title
        
        # Extract all styles and scripts
        custom_styles = []
        for style in soup.find_all('style'):
            custom_styles.append(str(style))
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href', '')
            if 'font-awesome' in href or 'cdnjs.cloudflare.com/ajax/libs/font-awesome' in href:
                continue
            custom_styles.append(str(link))
        for link in soup.find_all('link'):
            if link.get('rel') and 'preconnect' in link.get('rel'):
                custom_styles.append(str(link))
                
        custom_scripts = []
        for script in soup.find_all('script'):
            src = script.get('src', '')
            # Skip old firebase
            if 'firebase' in src or 'firebaseConfig' in (script.string or ''):
                continue
            custom_scripts.append(str(script))
            
        # Extract body content (exclude scripts since we inject them at the bottom)
        body_el = soup.find('body')
        if body_el:
            body_clone = copy.copy(body_el)
            for s in body_clone.find_all('script'):
                s.decompose()
            # Also clean up any navigation backlinks since we have our nav
            for back_link in body_clone.find_all('a'):
                text = back_link.get_text().lower()
                if 'goto' in text or 'back to' in text:
                    back_link.decompose()
            content = "".join([str(child) for child in body_clone.children])
        else:
            content = html_content

    # 3. Perform substitutions in template_content
    output_html = template_content
    output_html = output_html.replace('{{TITLE}}', title)
    output_html = output_html.replace('{{AUTHOR_NAME}}', AUTHOR_NAME)
    output_html = output_html.replace('{{DESCRIPTION}}', description)
    output_html = output_html.replace('{{SUBTITLE}}', subtitle)
    output_html = output_html.replace('{{DATE}}', date)
    output_html = output_html.replace('{{TAGS}}', tags)
    output_html = output_html.replace('{{FEATURED_IMAGE}}', featured_image)
    output_html = output_html.replace('{{FEATURED_IMAGE_ALT}}', featured_image_alt)
    output_html = output_html.replace('{{SLUG}}', slug)
    
    # Replace content placeholder
    output_html = output_html.replace('{{CONTENT}}', content)
    
    # Adapt paths
    output_html = output_html.replace('{{BLOG_URL}}/posts/{{SLUG}}.html', f'{{{{BLOG_URL}}}}/{folder_name}/{slug}.html')
    output_html = output_html.replace('{{BLOG_URL}}', BLOG_URL)
    
    # Inject custom styling and scripts for interactive pages
    if not is_standard:
        styles_str = "\n".join(custom_styles)
        scripts_str = "\n".join(custom_scripts)
        output_html = output_html.replace('</head>', f'{styles_str}\n</head>')
        output_html = output_html.replace('</body>', f'{scripts_str}\n</body>')
        
    # 4. Save to original file path
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(output_html)
        
    print(f"  -> Successfully updated: {file_path} ({'Standard' if is_standard else 'Interactive'})")
    return {
        'slug': slug,
        'title': title,
        'folder': folder_name,
        'date': date
    }

def main():
    print("Starting Blog Posts Refactoring Script...")
    
    # Copy generated images from brain folder to local images/ folder
    brain_dir = '/home/localhost/.gemini/antigravity-cli/brain/02f57fb9-7404-4ae2-928e-6b7e466a22c2'
    images_mapping = {
        'intentional_life_cover_1779452123464.png': 'images/intentional_life_cover.png',
        'three_questions_1779452144766.png': 'images/three_questions.png',
        'six_domains_1779452170041.png': 'images/six_domains.png'
    }
    for src_name, dst_path in images_mapping.items():
        src_path = os.path.join(brain_dir, src_name)
        if os.path.exists(src_path):
            try:
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
                print(f"Copied {src_name} to {dst_path}")
            except Exception as e:
                print(f"Warning: Failed to copy {src_name}: {e}")
        else:
            print(f"Warning: Source image not found at {src_path}")

    try:
        template_content = load_template()
    except Exception as e:
        print(f"Error loading template: {e}")
        return
        
    processed_count = 0
    post_metadata_list = []
    
    # Process files in posts/
    if os.path.exists(POSTS_DIR):
        for filename in os.listdir(POSTS_DIR):
            if filename.endswith('.html'):
                # Skip template if it happens to be here
                if filename == 'template.html' or filename == 'new_thinker.html':
                    continue
                file_path = os.path.join(POSTS_DIR, filename)
                meta = process_file(file_path, template_content)
                if meta:
                    processed_count += 1
                    post_metadata_list.append(meta)
                    
    # Process files in writeups/
    if os.path.exists(WRITEUPS_DIR):
        for filename in os.listdir(WRITEUPS_DIR):
            if filename.endswith('.html'):
                file_path = os.path.join(WRITEUPS_DIR, filename)
                meta = process_file(file_path, template_content)
                if meta:
                    processed_count += 1
                    post_metadata_list.append(meta)
                    
    # Write metadata index for the dashboard
    import json
    with open('posts-index.json', 'w', encoding='utf-8') as f:
        json.dump(post_metadata_list, f, indent=2)
    print(f"Generated posts-index.json with {len(post_metadata_list)} items.")
                    
    print(f"\nCompleted! Successfully refactored {processed_count} blog post / write-up pages.")

if __name__ == '__main__':
    main()
