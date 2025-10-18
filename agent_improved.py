import os
import json
import re
import subprocess
import time
import requests
from pathlib import Path
from typing import List, Dict, Union
from openai import OpenAI
from google.generativeai.types import GenerationConfig
import google.generativeai as genai

# Define types for better code clarity
ContentDataType = Dict[str, Union[str, List[str]]]

class BlogPostAgent:
    """An AI agent to generate and publish blog posts."""

    def __init__(self, config_path: str = "blog_config.json"):
        """Initialize the agent with configuration and prompts."""
        self.config = self.load_config(config_path)
        self.create_directories(self.config)
        self.create_l0c4lh057_template()
        
        # Initialize the API client for text generation
        if self.config.get("gemini_api_key"):
            print("Configured to use Google Gemini for text generation.")
            genai.configure(api_key=self.config["gemini_api_key"])
            self.client = genai
            self.model_name = self.config.get("llm_model", "gemini-1.5-flash")
        elif self.config.get("openai_api_key"):
            print("Configured to use OpenAI for text generation.")
            self.client = OpenAI(api_key=self.config["openai_api_key"])
            self.model_name = self.config.get("llm_model", "gpt-4o")
        else:
            raise ValueError("No valid API key found in config. Please check 'openai_api_key' or 'gemini_api_key'.")
            
        # The image client has been updated to use ModelsLab
        if self.config.get("image_generation_enabled", False):
            self.modelslab_api_key = self.config.get("modelslab_api_key")
            if not self.modelslab_api_key:
                print("Warning: image generation is enabled but no ModelsLab key was found. Skipping image generation.")

        self.prompt_template = self.load_prompt_template()

    def load_config(self, path: str) -> dict:
        """Load configuration from a JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Config file not found at {path}")
            exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in config file at {path}")
            exit(1)

    def create_directories(self, config: dict):
        """Create necessary directories if they don't exist."""
        for directory_key in ["blog_directory", "images_directory", "template_file"]:
            dir_path = Path(config[directory_key]).parent if directory_key == "template_file" else Path(config[directory_key])
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {dir_path}")

    def load_prompt_template(self, path: str = "prompts/prompt_template.txt") -> str:
        """Load the prompt template from a file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: Prompt template not found at {path}")
            exit(1)

    def create_l0c4lh057_template(self):
        """Create a default HTML template if one doesn't exist."""
        template_path = Path(self.config["template_file"])
        if not template_path.exists():
            default_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}}</title>
    <style>
        body { font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: auto; padding: 20px; }
        .inline-image { max-width: 100%; height: auto; display: block; margin: 20px auto; }
        h1, h2 { color: #333; }
    </style>
    {{CUSTOM_STYLES}}
</head>
<body>
    <h1>{{TITLE}}</h1>
    <p><em>{{SUBTITLE}}</em></p>
    <p>{{DATE}}</p>
    <div>
        {{CONTENT}}
    </div>
    <footer>
        <p>Tags: {{TAGS}}</p>
    </footer>
</body>
</html>"""
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(default_template)
            print(f"Created default template at {template_path}")

    def generate_content(self, topic: str, additional_context: str = "") -> ContentDataType:
        """Generate blog post content using an AI model."""
        try:
            full_prompt = f"Topic: {topic}\nAdditional Context: {additional_context}\n\n{self.prompt_template}"

            if self.config.get("gemini_api_key"):
                # Use Google's API call for Gemini
                response = self.client.GenerativeModel(self.model_name).generate_content(
                    full_prompt,
                    generation_config=GenerationConfig(
                        temperature=0.7,
                    )
                )
                content_text = response.text.strip()
            else:
                # Use OpenAI's API call
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.prompt_template},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.7
                )
                content_text = response.choices[0].message.content.strip()

            # Clean and parse the JSON response
            content_json = content_text.strip('`').strip().lstrip('json').strip()
            content_data = json.loads(content_json)
            return content_data

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from AI response: {e}")
            print("Raw response text:")
            print(content_text)
            return {
                "title": f"Error: Could not generate content for '{topic}'",
                "subtitle": "There was an issue processing the request. Please try again.",
                "tags": ["error", "api-failure"],
                "content": "<p>Apologies, but the AI was unable to generate a valid response. This may be a temporary issue. Please try again later.</p>",
                "image_suggestions": []
            }
        except Exception as e:
            print(f"Error generating content: {e}")
            return {
                "title": f"Error: An unexpected issue occurred with '{topic}'",
                "subtitle": "An unexpected error was encountered. Please check the logs.",
                "tags": ["error", "unexpected-failure"],
                "content": f"<p>An unexpected error occurred: {e}.</p>",
                "image_suggestions": []
            }

    def create_slug(self, title: str) -> str:
        """Create a URL-friendly slug from the post title."""
        title = title.lower()
        title = re.sub(r'[^a-z0-9\s-]', '', title)
        title = re.sub(r'\s+', '-', title)
        return title

    def generate_images_stable_diffusion(self, image_descriptions: List[str], post_slug: str) -> List[str]:
        """Generate images using ModelsLab and save them."""
        generated_images = []
        if not self.modelslab_api_key:
            print("ModelsLab API key not found. Skipping image generation.")
            return []
            
        # Correct ModelsLab API Endpoint (this was the source of a previous error)
        API_URL = "https://modelslab.com/api/v6/images/text2img"
        headers = {
            "key": self.modelslab_api_key,
            "Content-Type": "application/json"
        }
        
        for i, description in enumerate(image_descriptions[:self.config["max_images_per_post"]]):
            try:
                print(f"Generating image {i+1}: {description}...")
                
                payload = {
                    "key": self.modelslab_api_key,
                    "model_id": "flux",
                    "prompt": description,
                    "samples": "1",
                    "negative_prompt": "(worst quality:2), (low quality:2), (normal quality:2), (jpeg artifacts), (blurry), (duplicate), (morbid), (mutilated), (out of frame), (extra limbs), (bad anatomy), (disfigured), (deformed), (cross-eye), (glitch), (oversaturated), (overexposed), (underexposed), (bad proportions), (bad hands), (bad feet), (cloned face), (long neck), (missing arms), (missing legs), (extra fingers), (fused fingers), (poorly drawn hands), (poorly drawn face), (mutation), (deformed eyes), watermark, text, logo, signature, grainy, tiling, censored, nsfw, ugly, blurry eyes, noisy image, bad lighting, unnatural skin, asymmetry",
                    "width": "768",
                    "height": "1024",
                    "clip_skip": "1",
                    "enhance_prompt": "yes",
                    "guidance_scale": "7.5",
                    "safety_checker": "yes"
                }
                
                response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                
                result = response.json()
                if result['status'] == 'success' and result['output']:
                    image_url = result['output'][0]
                    
                    # Download the image from the URL
                    img_response = requests.get(image_url, timeout=60)
                    img_response.raise_for_status()
                    
                    image_name = f"{post_slug}_{i+1}.jpg"
                    image_path = Path(self.config["images_directory"]) / image_name
                    
                    with open(image_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    generated_images.append(image_name)
                    print(f"Generated and downloaded: {image_name}")
                else:
                    print(f"API returned a non-success status: {result['status']}")
                    
            except requests.exceptions.RequestException as e:
                print(f"Error during ModelsLab API call for image {i+1}: {e}")
                
            # Add a small delay to avoid hitting rate limits
            time.sleep(2)
                
        return generated_images

    def load_template(self) -> str:
        """Load the HTML template file."""
        template_path = Path(self.config["template_file"])
        if not template_path.exists():
            self.create_l0c4lh057_template()
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def replace_template_placeholders(self, template: str, content_data: ContentDataType, images: List[str], post_slug: str) -> str:
        """Replace placeholders in the template with generated content."""
        template = template.replace("{{TITLE}}", content_data.get("title", "No Title"))
        template = template.replace("{{SUBTITLE}}", content_data.get("subtitle", "No Subtitle"))
        template = template.replace("{{DATE}}", time.strftime("%B %d, %Y"))
        template = template.replace("{{TAGS}}", ", ".join(content_data.get("tags", [])))
        
        template = template.replace("{{AUTHOR_NAME}}", self.config.get("author_name", "L0C4LH057"))
        template = template.replace("{{DESCRIPTION}}", content_data.get("subtitle", "A newly generated blog post."))
        template = template.replace("{{BLOG_URL}}", self.config.get("blog_url", ""))
        template = template.replace("{{SLUG}}", post_slug)
        template = template.replace("{{CUSTOM_STYLES}}", content_data.get("custom_css_styles", ""))

        if images:
            template = template.replace("{{FEATURED_IMAGE}}", images[0])
            template = template.replace("{{FEATURED_IMAGE_ALT}}", content_data.get("title", "Featured Image"))
        else:
            template = template.replace("{{FEATURED_IMAGE}}", "")
            template = template.replace("{{FEATURED_IMAGE_ALT}}", "")
        
        content = content_data.get("content", "")
        
        # Logic to insert images into the content
        if len(images) > 0:
            content = f'<img src="../images/{images[0]}" alt="Featured image for {content_data["title"]}" class="inline-image"> \n{content}'

        if len(images) > 1:
            h2_pattern = re.compile(r'(<h2>.*?</h2>)', re.DOTALL)
            match = h2_pattern.search(content)
            if match:
                content = content.replace(match.group(1), f'{match.group(1)}\n<img src="../images/{images[1]}" alt="Supporting illustration for {content_data["title"]}" class="inline-image">')

        if len(images) > 2:
            paragraphs = content.split('</p>')
            mid_point = len(paragraphs) // 2
            if mid_point > 0:
                paragraphs.insert(mid_point, f'\n<img src="../images/{images[2]}" alt="Supporting illustration for {content_data["title"]}" class="inline-image">')
                content = '</p>'.join(paragraphs) + '</p>'
        
        template = template.replace("{{CONTENT}}", content)
        
        return template

    def save_post(self, content: str, post_slug: str) -> str:
        """Save the generated post to a file"""
        filename = f"{post_slug}.html"
        filepath = Path(self.config["blog_directory"]) / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Post saved: {filepath}")
        return str(filepath)
    
    def commit_and_push(self, files: List[str], commit_message: str):
        """Commit and push changes to GitHub"""
        if not self.config["auto_commit"]:
            print("Auto-commit disabled. Manual git operations required.")
            return
        
        try:
            original_dir = os.getcwd()
            os.chdir(self.config["github_repo_path"])
            
            for file in files:
                subprocess.run(["git", "add", file], check=True)
            
            result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if not result.stdout.strip():
                print("ℹ️  No changes to commit.")
                return
            
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            subprocess.run(["git", "push"], check=True)
            
            print(f"Successfully committed and pushed: {commit_message}")
            
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
            print(f"Error output: {e.stderr}")
        except Exception as e:
            print(f"Git operation failed: {e}")
        finally:
            os.chdir(original_dir)
            
    def _extract_json_from_response(self, text: str) -> str:
        """Helper function to extract a single JSON object from a string."""
        # This regex looks for a string that starts with a brace '{' and ends with a brace '}',
        # being as non-greedy as possible (`.*?`), and accounts for multi-line JSON.
        # It also handles optional markdown code fences around the JSON.
        json_match = re.search(r'```(?:json)?\s*(\{.*?})\s*```|(\{.*?})', text, re.DOTALL)
        
        if json_match:
            # The regex returns a tuple, so we check both capture groups
            if json_match.group(1):
                return json_match.group(1)
            else:
                return json_match.group(2)
        else:
            raise ValueError("No valid JSON object found in the LLM response.")

    def refine_content_with_llm(self, markdown_content: str) -> Dict[str, str]:
        """Uses the LLM to refine and format markdown content into HTML with custom CSS."""
        prompt = f"""
        You are an expert at converting markdown content into a clean, semantic, and well-structured HTML snippet. You also have a keen eye for design and can generate custom CSS to make the content look great.

        Your task is to take the following markdown text and return a JSON object with two fields: `html_content` and `custom_css_styles`.

        **Instructions for `html_content`:**
        1.  Ensure all headers (`#`, `##`, `###`) are converted to `<h1>`, `<h2>`, `<h3>` tags.
        2.  Convert paragraphs of text into `<p>` tags.
        3.  Convert lists (`-`, `*`) into `<ul>` (unordered list) or `<ol>` (ordered list) with `<li>` tags.
        4.  Crucially, convert any markdown tables into correct HTML `<table>`, `<thead>`, `<tbody>`, `<tr>`, and `<td>` tags.
        5.  Convert all bold (`**text**`) and italic (`*text*`) text to `<strong>` and `<em>` tags respectively.
        6.  Do not include `<html>`, `<head>`, or `<body>` tags. Only return the content that would go inside the main post `<div>`.
        7.  Ensure all links (`[text](url)`) are converted to `<a>` tags.
        8.  Do not add any additional text or commentary. Just provide the final, cleaned HTML snippet.

        **Instructions for `custom_css_styles`:**
        1.  Generate a `<style>` block containing custom CSS rules.
        2.  Target specific elements within the post content (e.g., `<h2>`, `<table>`, `.highlight`).
        3.  Add unique styles like colors, fonts, or spacing to make the content look great.
        4.  Avoid repeating generic styles that might already exist in the main site's stylesheet.
        5.  Return the entire `<style>` block. If no custom styles are needed, return an empty string.

        **Markdown Content to Convert:**
        {markdown_content}
        
        **Your Final Output (JSON object only, without any markdown or code blocks):**
        """
        try:
            if self.config.get("gemini_api_key"):
                response = self.client.GenerativeModel(self.model_name).generate_content(prompt)
                content_text = response.text.strip()
            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that converts markdown to HTML and generates custom CSS."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                content_text = response.choices[0].message.content.strip()
            
            # Use the new helper function to extract the JSON string
            json_string = self._extract_json_from_response(content_text)
            
            data = json.loads(json_string)
            return data
            
        except Exception as e:
            print(f"Error refining content with LLM: {e}")
            return {
                "html_content": markdown_content,
                "custom_css_styles": ""
            }

    def process_prewritten_content(self, file_path: str) -> ContentDataType:
        """Process a pre-written file, extract images, and return content data."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # The title is the first line
            title = lines[0].strip() if len(lines) > 0 else "Untitled Post"
            
            # Use a more flexible regex to extract image prompts and get the lines they are on
            image_placeholder_pattern = re.compile(r'{{image:\s*["\'](.*?)["\']\s*}}', re.DOTALL)
            processed_lines = []
            image_prompts = []
            
            for line in lines[1:]:  # Start after the title line
                match = image_placeholder_pattern.search(line)
                if match:
                    image_prompts.append(match.group(1))
                else:
                    processed_lines.append(line)
            
            # The subtitle is the first image prompt
            subtitle = image_prompts[0] if image_prompts else ""
            
            # Join the remaining lines into a single string for LLM processing
            processed_content = "".join(processed_lines).strip()
            
            llm_response = self.refine_content_with_llm(processed_content)
            html_content = llm_response.get("html_content", "")
            custom_css_styles = llm_response.get("custom_css_styles", "")
            
            return {
                "title": title,
                "subtitle": subtitle,
                "tags": ["pre-written", "review"],
                "content": html_content,
                "image_suggestions": image_prompts,
                "custom_css_styles": custom_css_styles
            }
        except FileNotFoundError:
            print(f"Error: Pre-written file not found at {file_path}")
            return None
        except Exception as e:
            print(f"An error occurred while processing the file: {e}")
            return None

    def create_post(self, topic: str = "", additional_context: str = "", auto_publish: bool = True, prewritten_file_path: str = None) -> Dict:
        """Main method to create a complete blog post"""
        images = []
        if prewritten_file_path:
            print(f"Processing pre-written post from: {prewritten_file_path}")
            content_data = self.process_prewritten_content(prewritten_file_path)
            if not content_data:
                return {}
            
            post_slug = self.create_slug(content_data.get("title"))
            print(f"Post slug: {post_slug}")
            
            if content_data.get("image_suggestions") and self.config.get("image_generation_enabled"):
                print("Generating images from pre-written prompts using ModelsLab...")
                images = self.generate_images_stable_diffusion(content_data["image_suggestions"], post_slug)
            else:
                print("Skipping image generation.")
                
            processed_content = content_data["content"]
            # Insert images into content
            for img_name in images:
                processed_content = processed_content.replace('{{IMAGE_PLACEHOLDER}}', f'<img src="../images/{img_name}" alt="{content_data["title"]}" class="inline-image">', 1)
            content_data["content"] = processed_content
            
        else:
            print(f"Creating blog post about: {topic}")
            print("🤖 Generating content with AI...")
            content_data = self.generate_content(topic, additional_context)
            post_slug = self.create_slug(content_data.get("title", topic))
            print(f"Post slug: {post_slug}")
            
            if content_data.get("image_suggestions") and self.config.get("image_generation_enabled"):
                print("Generating images using ModelsLab...")
                images = self.generate_images_stable_diffusion(content_data["image_suggestions"], post_slug)
            else:
                print("Skipping image generation.")
        
        print("Processing template...")
        template = self.load_template()
        final_content = self.replace_template_placeholders(template, content_data, images, post_slug)
        
        post_file = self.save_post(final_content, post_slug)
        
        if auto_publish:
            files_to_commit = [str(Path(self.config["blog_directory"]) / Path(post_file).name)]
            if images:
                files_to_commit.extend([str(Path(self.config["images_directory"]) / img) for img in images])
            commit_message = f"Add new blog post: {content_data['title']}"
            self.commit_and_push(files_to_commit, commit_message)
        
        print(f"\n🎉 Blog post created successfully!")
        print(f"Title: {content_data['title']}")
        print(f"File: {post_file}")
        print(f"🔗 Slug: {post_slug}")
        print(f"🖼️  Images: {len(images)} generated")
        
        if auto_publish:
            print(f"🌐 Live at: {self.config.get('blog_url', 'N/A')}/posts/{post_slug}.html")
        
        return {
            "title": content_data["title"],
            "subtitle": content_data.get("subtitle", ""),
            "file": post_file,
            "slug": post_slug,
            "images": images,
            "tags": content_data.get("tags", []),
            "url": f"{self.config.get('blog_url', 'N/A')}/posts/{post_slug}.html"
        }

# Usage example and CLI integration
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        file_path = " ".join(sys.argv[1:])
        if os.path.exists(file_path):
            try:
                agent = BlogPostAgent()
                result = agent.create_post(prewritten_file_path=file_path, auto_publish=False)
                
                print("\n----------------------------------------")
                print("Post created from file! Review it locally:")
                print(f"1. Open your terminal in the directory: {agent.config['github_repo_path']}")
                print(f"2. Run the command: `python3 -m http.server 5501`")
                print(f"3. Open your browser and navigate to: http://localhost:5501/posts/{result['slug']}.html")
                print("----------------------------------------")
            except (ValueError, FileNotFoundError) as e:
                print(f"Initialization failed: {e}")
                sys.exit(1)
        else:
            print(f"Error: File not found at {file_path}")
            sys.exit(1)
            
    else:
        print("🤖 L0C4LH057 Blog AI Agent")
        print("=" * 40)
        
        try:
            agent = BlogPostAgent()
        except (ValueError, FileNotFoundError) as e:
            print(f"Error initializing agent: {e}")
            sys.exit(1)

        mode_choice = input("Would you like to (1) create a new post with AI or (2) use a pre-written file? (1/2): ").strip()

        if mode_choice == "1":
            topic = input("\nEnter your blog post topic: ").strip()
            if not topic:
                print("Topic cannot be empty!")
                sys.exit(1)
            context = input("Additional context (optional): ").strip()
            
            try:
                result = agent.create_post(topic, context, auto_publish=False)
                
                print("\n----------------------------------------")
                print("Post created successfully! Review it locally:")
                print(f"1. Open your terminal in the directory: {agent.config['github_repo_path']}")
                print(f"2. Run the command: `python3 -m http.server 5501`")
                print(f"3. Open your browser and navigate to: http://localhost:5501/posts/{result['slug']}.html")
                print("----------------------------------------")
                
            except Exception as e:
                print(f"Error creating post: {e}")

        elif mode_choice == "2":
            file_path = input("\nEnter the path to your pre-written file: ").strip()
            if not file_path:
                print("File path cannot be empty!")
                sys.exit(1)
            
            try:
                result = agent.create_post(prewritten_file_path=file_path, auto_publish=False)
                
                print("\n----------------------------------------")
                print("Post created from file! Review it locally:")
                print(f"1. Open your terminal in the directory: {agent.config['github_repo_path']}")
                print(f"2. Run the command: `python3 -m http.server 5501`")
                print(f"3. Open your browser and navigate to: http://localhost:5501/posts/{result['slug']}.html")
                print("----------------------------------------")
            except Exception as e:
                print(f"Error creating post: {e}")
        else:
            print("Invalid choice. Please run the script again and choose '1' or '2'.")
            sys.exit(1)
