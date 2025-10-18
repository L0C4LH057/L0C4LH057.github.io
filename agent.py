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
            
        # Initialize a separate client for image generation (must be OpenAI)
        if self.config.get("image_generation_enabled", False) and self.config.get("openai_api_key"):
            self.image_client = OpenAI(api_key=self.config["openai_api_key"])
        else:
            self.image_client = None

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
                print(f"📂 Created directory: {dir_path}")

    def load_prompt_template(self, path: str = "prompts/prompt_template.txt") -> str:
        """Load the prompt template from a file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ Error: Prompt template not found at {path}")
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

    def generate_images(self, image_descriptions: List[str], post_slug: str) -> List[str]:
        """Generate images using DALL-E and save them."""
        # Check if a dedicated image client is available
        if not self.image_client:
            return []
        
        generated_images = []
        style_template = "futuristic sci-fi anime style, vector illustration, vibrant colors, clean lines, professional blog art, digital painting, no text"

        for i, description in enumerate(image_descriptions[:self.config["max_images_per_post"]]):
            try:
                print(f"Generating image {i+1}: {description}")
                prompt = f"{description}, {style_template}"

                response = self.image_client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    n=1,
                    size="1024x1024",
                    response_format="url"
                )
                
                image_url = response.data[0].url
                image_name = f"{post_slug}_{i+1}.png"
                image_path = Path(self.config["images_directory"]) / image_name
                
                img_response = requests.get(image_url, timeout=30)
                if img_response.status_code == 200:
                    with open(image_path, 'wb') as f:
                        f.write(img_response.content)
                    generated_images.append(image_name)
                    print(f"✅ Generated: {image_name}")
                else:
                    print(f"Failed to download image from URL. Status code: {img_response.status_code}")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"Error generating image {i+1}: {e}")
                
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
                print("No changes to commit.")
                return
            
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            subprocess.run(["git", "push"], check=True)
            
            print(f"✅ Successfully committed and pushed: {commit_message}")
            
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
            print(f"Error output: {e.stderr}")
        except Exception as e:
            print(f"Git operation failed: {e}")
        finally:
            os.chdir(original_dir)
    
    def create_post(self, topic: str, additional_context: str = "", auto_publish: bool = True) -> Dict:
        """Main method to create a complete blog post"""
        print(f"Creating blog post about: {topic}")
        
        print("🤖 Generating content with AI...")
        content_data = self.generate_content(topic, additional_context)
        
        post_slug = self.create_slug(content_data.get("title", topic))
        print(f"Post slug: {post_slug}")
        
        images = []
        if content_data.get("image_suggestions") and self.config.get("image_generation_enabled"):
            print("Generating images...")
            images = self.generate_images(content_data["image_suggestions"], post_slug)
        else:
            print("Skipping image generation")
        
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
        
        print(f"\nBlog post created successfully!")
        print(f"Title: {content_data['title']}")
        print(f"File: {post_file}")
        print(f"Slug: {post_slug}")
        print(f"Images: {len(images)} generated")
        
        if auto_publish:
            print(f"Live at: {self.config.get('blog_url', 'N/A')}/posts/{post_slug}.html")
        
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
        topic = " ".join(sys.argv[1:])
        try:
            agent = BlogPostAgent()
            # Pass auto_publish=False to prevent automatic git commit
            result = agent.create_post(topic, auto_publish=False)
            
            # Print instructions for local review
            print("\n----------------------------------------")
            print("✅ Post created successfully! Review it locally:")
            print(f"1. Open your terminal in the directory: {agent.config['github_repo_path']}")
            print(f"2. Run the command: `python3 -m http.server 5501`")
            print(f"3. Open your browser and navigate to: http://localhost:5501/posts/{result['slug']}.html")
            print("----------------------------------------")
            
        except (ValueError, FileNotFoundError) as e:
            print(f"Initialization failed: {e}")
            sys.exit(1)
    else:
        print("🤖 L0C4LH057 Blog AI Agent")
        print("=" * 40)
        
        try:
            agent = BlogPostAgent()
        except (ValueError, FileNotFoundError) as e:
            print(f"Error initializing agent: {e}")
            sys.exit(1)
        
        topic = input("\nEnter your blog post topic: ").strip()
        if not topic:
            print("Topic cannot be empty!")
            sys.exit(1)
        
        context = input("Additional context (optional): ").strip()
        
        try:
            # Pass auto_publish=False to prevent automatic git commit
            result = agent.create_post(topic, context, auto_publish=False)
            
            # Print instructions for local review
            print("\n----------------------------------------")
            print("Post created successfully! Review it locally:")
            print(f"1. Open your terminal in the directory: {agent.config['github_repo_path']}")
            print(f"2. Run the command: `python3 -m http.server 5501`")
            print(f"3. Open your browser and navigate to: http://localhost:5501/posts/{result['slug']}.html")
            print("----------------------------------------")
            
        except Exception as e:
            print(f"Error creating post: {e}")