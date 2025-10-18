import os
import json
import re
import subprocess
import time
import requests
from pathlib import Path
from typing import List, Dict, Union, Tuple
from openai import OpenAI
from google.generativeai.types import GenerationConfig
import google.generativeai as genai

# Define types for better code clarity
ContentDataType = Dict[str, Union[str, List[str], bool]]

class BlogPostAgent:
    """An AI agent to generate and publish blog posts with an interactive approval workflow."""

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
            self.model_name = self.config.get("llm_model", "models/gemini-2.5-flash")
        elif self.config.get("openai_api_key"):
            print("Configured to use OpenAI for text generation.")
            self.client = OpenAI(api_key=self.config["openai_api_key"])
            self.model_name = self.config.get("llm_model", "gpt-4o")
        else:
            raise ValueError("No valid API key found in config. Please check 'openai_api_key' or 'gemini_api_key'.")
            
        # Initialize image generation clients
        self.image_generation_enabled = self.config.get("image_generation_enabled", False)
        if self.image_generation_enabled:
            self.falai_api_key = self.config.get("falai_api_key")
            if not self.falai_api_key:
                print("Warning: image generation is enabled but fal.ai API key was not found. Skipping image generation.")
                self.image_generation_enabled = False

        self.prompt_template = self.load_prompt_template()
        self.image_placeholders = []  # Store user-specified image positions

    def load_config(self, path: str) -> dict:
        """Load configuration from a JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f" Error: Config file not found at {path}")
            exit(1)
        except json.JSONDecodeError:
            print(f" Error: Invalid JSON in config file at {path}")
            exit(1)

    def create_directories(self, config: dict):
        """Create necessary directories if they don't exist."""
        for directory_key in ["blog_directory", "images_directory", "template_file"]:
            dir_path = Path(config[directory_key]).parent if directory_key == "template_file" else Path(config[directory_key])
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f" Created directory: {dir_path}")

    def load_prompt_template(self, path: str = "prompts/prompt_template.txt") -> str:
        """Load the prompt template from a file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f" Error: Prompt template not found at {path}")
            exit(1)

    def create_l0c4lh057_template(self):
        """Create a default HTML template if one doesn't exist."""
        template_path = Path(self.config["template_file"])
        if not template_path.exists():
            default_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
    <title>{{TITLE}}</title>
    <style>
        body { font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: auto; padding: 20px; }
        .inline-image { max-width: 100%; height: auto; display: block; margin: 20px auto; }
        h1, h2 { color: #333; }
        .image-placeholder { 
            border: 2px dashed #ccc; 
            padding: 20px; 
            margin: 20px 0; 
            text-align: center; 
            color: #666; 
            background-color: #f9f9f9;
        }
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
            
    def _extract_json_from_response(self, text: str) -> str:
        """Helper function to extract a single JSON object from a string."""
        json_match = re.search(r'```(?:json)?\s*(\{.*?})\s*```|(\{.*?})', text, re.DOTALL)
        if json_match:
            return json_match.group(1) or json_match.group(2)
        else:
            raise ValueError("No valid JSON object found in the LLM response.")

    def generate_content(self, topic: str, additional_context: str = "") -> ContentDataType:
        """Generate blog post content using an AI model."""
        try:
            full_prompt = f"Topic: {topic}\nAdditional Context: {additional_context}\n\n{self.prompt_template}"

            if self.config.get("gemini_api_key"):
                model = self.client.GenerativeModel(self.model_name)
                response = model.generate_content(
                    full_prompt,
                    generation_config=GenerationConfig(temperature=0.7)
                )
                content_text = response.text.strip()
            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.prompt_template},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.7
                )
                content_text = response.choices[0].message.content.strip()

            content_json = self._extract_json_from_response(content_text)
            return json.loads(content_json)

        except (json.JSONDecodeError, ValueError) as e:
            print(f" Error decoding JSON from AI response: {e}")
            print(f"Raw response was:\n---\n{content_text}\n---")
            return {
                "title": f"Error: Could not generate content for '{topic}'",
                "subtitle": "There was an issue processing the request.",
                "tags": ["error"],
                "content": "<p>Apologies, the AI was unable to generate a valid response.</p>",
                "image_suggestions": []
            }
        except Exception as e:
            print(f" Error generating content: {e}")
            return {
                "title": f"Error: An unexpected issue occurred for '{topic}'",
                "subtitle": "An unexpected error was encountered.",
                "tags": ["error"],
                "content": f"<p>An unexpected error occurred: {e}.</p>",
                "image_suggestions": []
            }
            
    def refine_content_with_feedback(self, current_content: dict, feedback: str) -> ContentDataType:
        """Uses the LLM to refine content based on user feedback."""
        print("🤖 Incorporating your feedback... Please wait.")
        prompt = f"""
        You are an AI blog post editor. A user has provided feedback on a blog post.
        Your task is to update the blog post's JSON data based on the user's feedback.
        You MUST return the complete, updated JSON object and nothing else.
        Ensure the JSON is valid and maintains the original schema.

        USER FEEDBACK:
        "{feedback}"

        CURRENT BLOG POST JSON:
        {json.dumps(current_content, indent=2)}

        Return the full, updated JSON object now.
        """
        try:
            if self.config.get("gemini_api_key"):
                model = self.client.GenerativeModel(self.model_name)
                response = model.generate_content(prompt)
                content_text = response.text.strip()
            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are an AI blog post editor."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                content_text = response.choices[0].message.content.strip()

            json_string = self._extract_json_from_response(content_text)
            updated_data = json.loads(json_string)
            print(" Content updated based on your feedback.")
            return updated_data
        except Exception as e:
            print(f" Error refining content with LLM: {e}")
            print("Could not apply changes. Please try rephrasing your feedback or try again.")
            return current_content # Return original content on failure


    def create_slug(self, title: str) -> str:
        """Create a URL-friendly slug from the post title."""
        title = title.lower()
        title = re.sub(r'[^a-z0-9\s-]', '', title)
        title = re.sub(r'\s+', '-', title)
        return title.strip('-')

    def generate_images_fal_ai(self, image_descriptions: List[str], post_slug: str) -> List[str]:
        """Generate images using fal.ai and save them."""
        generated_images = []
        if not self.falai_api_key:
            print(" fal.ai API key not found. Skipping image generation.")
            return []
            
        # Use nano-banana model, configurable via blog_config.json
        model_id = self.config.get("fal_model_id", "fal-ai/fast-nano-sdxl-lightning")
        API_URL = f"https://queue.fal.ai/models/{model_id}"
        headers = {
            "Authorization": f"Key {self.falai_api_key}",
            "Content-Type": "application/json"
        }
        
        for i, description in enumerate(image_descriptions[:self.config.get("max_images_per_post", 3)]):
            try:
                print(f" Generating image {i+1} ('{description[:50]}...')...")
                
                payload = {"prompt": description}
                
                response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
                response.raise_for_status()
                result = response.json()
                
                if 'images' in result and result['images']:
                    image_url = result['images'][0]['url']
                    
                    img_response = requests.get(image_url, timeout=60)
                    img_response.raise_for_status()
                    
                    image_name = f"{post_slug}_{i+1}.jpg"
                    image_path = Path(self.config["images_directory"]) / image_name
                    
                    with open(image_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    generated_images.append(image_name)
                    print(f" Downloaded image: {image_name}")
                else:
                    print(f" API did not return an image. Response: {result}")
                    
            except requests.exceptions.RequestException as e:
                print(f" Error during fal.ai API call for image {i+1}: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response Body: {e.response.text}")
                
            time.sleep(1)
                
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
        
        # Insert images at user-specified positions
        if self.image_placeholders:
            paragraphs = content.split('</p>')
            # Create a copy to iterate over while modifying the list
            temp_placeholders = sorted(self.image_placeholders, key=lambda x: x[0], reverse=True)
            
            for i, (pos, description) in enumerate(temp_placeholders):
                # Find the correct image index (since placeholders are reversed)
                img_index = len(images) - 1 - i
                if img_index >= 0:
                    img_tag = f'<img src="../images/{images[img_index]}" alt="{description}" class="inline-image">'
                    if pos < len(paragraphs):
                        paragraphs.insert(pos + 1, img_tag)
                    else:
                        paragraphs.append(img_tag)
            content = ''.join(paragraphs)

        template = template.replace("{{CONTENT}}", content)
        return template

    def save_post(self, content: str, post_slug: str) -> str:
        """Save the generated post to a file"""
        filename = f"{post_slug}.html"
        filepath = Path(self.config["blog_directory"]) / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f" Post saved: {filepath}")
        return str(filepath)
    
    def commit_and_push(self, files: List[str], commit_message: str):
        """Commit and push changes to GitHub"""
        if not self.config.get("auto_commit", False):
            print("  Auto-commit disabled. Manual git operations required.")
            return
        
        try:
            repo_path = self.config["github_repo_path"]
            print(f" Pushing changes to repo at {repo_path}...")
            
            # Use Path for robust file path handling relative to the repo
            repo_path_obj = Path(repo_path)
            relative_files = [str(Path(file).relative_to(repo_path_obj)) for file in files]
            
            # Git operations
            subprocess.run(["git", "-C", repo_path, "add"] + relative_files, check=True)
            
            status_result = subprocess.run(["git", "-C", repo_path, "status", "--porcelain"], capture_output=True, text=True)
            if not status_result.stdout.strip():
                print("ℹ  No changes to commit.")
                return
            
            subprocess.run(["git", "-C", repo_path, "commit", "-m", commit_message], check=True)
            subprocess.run(["git", "-C", repo_path, "push"], check=True)
            
            print(f" Successfully committed and pushed: {commit_message}")
            
        except subprocess.CalledProcessError as e:
            print(f" Git operation failed: {e}")
            print(f"Stderr: {e.stderr}")
        except Exception as e:
            print(f" An unexpected error occurred during git operation: {e}")

    def process_prewritten_content(self, file_path: str) -> ContentDataType:
        """Process a pre-written file, extract images, and return content data."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            prompt = f"""
            You are an expert at converting markdown into a structured JSON object for a blog.
            The user has provided the following text. The first line is the title.
            Any lines formatted like `{{{{image: 'description goes here'}}}}` are image prompts.
            The first image prompt should be used as the subtitle. The rest of the text is the main content.

            Your task is to convert this into the specified JSON format.
            - Extract the title.
            - Extract all image prompts. Use the first for the subtitle.
            - Convert the main content from Markdown to clean HTML.
            - Generate 5 relevant tags.

            Here is the content:
            ---
            {content}
            ---

            Return ONLY the JSON object.
            """
            
            if self.config.get("gemini_api_key"):
                model = self.client.GenerativeModel(self.model_name)
                response = model.generate_content(prompt)
                content_text = response.text.strip()
            else:
                 response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5
                )
                 content_text = response.choices[0].message.content.strip()
            
            json_string = self._extract_json_from_response(content_text)
            data = json.loads(json_string)
            data["is_prewritten"] = True # Add flag for workflow
            return data

        except Exception as e:
            print(f"❌ An error occurred while processing the file: {e}")
            return None

    def preview_post(self, content_data: ContentDataType, post_slug: str) -> str:
        """Generate a preview of the post without images."""
        template = self.load_template()
        
        # Create a preview with placeholders for images
        preview_content = template.replace("{{TITLE}}", content_data.get("title", "No Title"))
        preview_content = preview_content.replace("{{SUBTITLE}}", content_data.get("subtitle", "No Subtitle"))
        preview_content = preview_content.replace("{{DATE}}", time.strftime("%B %d, %Y"))
        preview_content = preview_content.replace("{{TAGS}}", ", ".join(content_data.get("tags", [])))
        
        # Replace other placeholders to avoid breaking the template
        preview_content = preview_content.replace("{{AUTHOR_NAME}}", self.config.get("author_name", "L0C4LH057"))
        preview_content = preview_content.replace("{{DESCRIPTION}}", content_data.get("subtitle", "A newly generated blog post."))
        preview_content = preview_content.replace("{{BLOG_URL}}", self.config.get("blog_url", ""))
        preview_content = preview_content.replace("{{SLUG}}", post_slug)
        preview_content = preview_content.replace("{{CUSTOM_STYLES}}", content_data.get("custom_css_styles", ""))
        preview_content = preview_content.replace("{{FEATURED_IMAGE}}", "")
        preview_content = preview_content.replace("{{FEATURED_IMAGE_ALT}}", "")
        
        content_with_placeholders = content_data.get("content", "")
        num_images = len(content_data.get("image_suggestions", []))
        if num_images > 0:
            placeholder_html = f'<div class="image-placeholder">Featured image will be placed here. ({num_images -1} other images suggested)</div>'
            content_with_placeholders = placeholder_html + content_with_placeholders
        
        preview_content = preview_content.replace("{{CONTENT}}", content_with_placeholders)
        
        preview_filename = f"{post_slug}_preview.html"
        preview_filepath = Path(self.config.get("blog_directory", "posts")) / preview_filename
        
        with open(preview_filepath, 'w', encoding='utf-8') as f:
            f.write(preview_content)
        
        return str(preview_filepath)

    def get_image_descriptions_for_positions(self, content_data: ContentDataType, positions: List[int]) -> List[str]:
        # This function remains largely the same as in the original code
        pass # Implementation from original file goes here

    def create_post(self, topic: str = "", additional_context: str = "", prewritten_file_path: str = None):
        """Main method to create a complete blog post with an approval workflow."""
        
        # --- 1. Initial Content Generation ---
        if prewritten_file_path:
            print(f"🚀 Processing pre-written post from: {prewritten_file_path}")
            content_data = self.process_prewritten_content(prewritten_file_path)
        else:
            print(f"🚀 Creating new blog post about: {topic}")
            content_data = self.generate_content(topic, additional_context)

        if not content_data or "title" not in content_data:
            print("❌ Failed to generate initial content. Aborting.")
            return {}
            
        post_slug = self.create_slug(content_data.get("title", topic or "untitled"))
        print(f"📝 Post slug created: {post_slug}")

        # --- 2. Approval Loop ---
        while True:
            preview_file = self.preview_post(content_data, post_slug)
            print("\n" + "="*50)
            print(f"👀 PREVIEW READY: Please open this file to review -> {preview_file}")
            print("="*50)
            
            user_input = input("\nType 'approve' to finalize, or provide feedback for changes:\n> ").strip()

            if user_input.lower() == 'approve':
                print("\n✅ Post approved! Proceeding to final steps...")
                break
            elif not user_input:
                print("⚠️ No input received. Please provide feedback or type 'approve'.")
            else:
                content_data = self.refine_content_with_feedback(content_data, user_input)

        # --- 3. Post-Approval Image Generation ---
        images = []
        if self.image_generation_enabled:
            image_descriptions = content_data.get("image_suggestions", [])
            if image_descriptions:
                images = self.generate_images_fal_ai(image_descriptions, post_slug)
            else:
                print("⏭️ No image suggestions found in content. Skipping image generation.")
        else:
            print("⏭️ Image generation is disabled in config. Skipping.")

        # --- 4. Finalize and Publish ---
        print("📋 Processing final template...")
        template = self.load_template()
        final_content = self.replace_template_placeholders(template, content_data, images, post_slug)
        
        post_file = self.save_post(final_content, post_slug)
        
        files_to_commit = [post_file]
        if images:
            image_dir = self.config["images_directory"]
            files_to_commit.extend([str(Path(image_dir) / img) for img in images])
        
        commit_message = f"Add blog post: {content_data['title']}"
        self.commit_and_push(files_to_commit, commit_message)
        
        # --- 5. Completion ---
        final_url = f"{self.config.get('blog_url', 'N/A')}/posts/{post_slug}.html"
        print("\n" + "🎉" * 20)
        print("Blog post created and published successfully!")
        print(f"📰 Title: {content_data['title']}")
        print(f"📁 File: {post_file}")
        print(f"🖼️  Images: {len(images)} generated")
        if self.config.get("auto_commit", False):
            print(f"🌐 Live at: {final_url}")
        print("🎉" * 20)
        
        return {
            "title": content_data["title"],
            "file": post_file,
            "slug": post_slug,
            "images": images,
            "url": final_url
        }

# Usage example and CLI integration
if __name__ == "__main__":
    import sys
    
    try:
        agent = BlogPostAgent()
    except (ValueError, FileNotFoundError) as e:
        print(f"❌ Initialization failed: {e}")
        sys.exit(1)
        
    if len(sys.argv) > 1:
        file_path = " ".join(sys.argv[1:])
        if os.path.exists(file_path):
            agent.create_post(prewritten_file_path=file_path)
        else:
            print(f"❌ Error: File not found at {file_path}")
            sys.exit(1)
            
    else:
        print("\n🤖 L0C4LH057 Blog AI Agent")
        print("=" * 40)
        
        mode_choice = input("Would you like to (1) create a new post with AI or (2) use a pre-written file? (1/2): ").strip()

        if mode_choice == "1":
            topic = input("\n📝 Enter your blog post topic: ").strip()
            if not topic:
                print("❌ Topic cannot be empty!")
                sys.exit(1)
            context = input("📋 Additional context (optional): ").strip()
            agent.create_post(topic, context)

        elif mode_choice == "2":
            file_path = input("\n📁 Enter the path to your pre-written file: ").strip()
            if not os.path.exists(file_path):
                print(f"❌ File not found at '{file_path}'!")
                sys.exit(1)
            agent.create_post(prewritten_file_path=file_path)

        else:
            print("❌ Invalid choice. Please run the script again and choose '1' or '2'.")
            sys.exit(1)