# langgraph_agent.py (Final Version)
import os
import json
import re
import subprocess
import time
from pathlib import Path
from typing import List, Dict, TypedDict, Union, Optional

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage

# Google Cloud imports
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from langchain_google_vertexai import ChatVertexAI # <-- IMPORTANT IMPORT

# Define types for better code clarity
ContentDataType = Dict[str, Union[str, List[str]]]

# Define the state for our LangGraph.
class GraphState(TypedDict):
    topic: str
    post_data: ContentDataType
    post_slug: str
    image_prompts: List[str]
    image_paths: List[str]
    preview_file_path: str
    final_post_path: str
    revision_feedback: Optional[str] = None
    error: Optional[str] = None

class BlogAgent:
    """A multi-agent system for generating and publishing blog posts using LangGraph."""

    # (Inside the BlogAgent class)

# --- Replace the entire __init__ method with this one ---
    def __init__(self, config_path: str = "blog_config.json"):
        """Initialize the agent, loading configuration and setting up the graph."""
        self.config = self._load_config(config_path)
        self._create_directories()

        # --- THIS BLOCK SWITCHES BACK TO THE GEMINI API KEY ---
        from langchain_google_genai import ChatGoogleGenerativeAI
        self.llm = ChatGoogleGenerativeAI(
            model=self.config.get("llm_model", "gemini-1.5-flash-latest"),
            google_api_key=self.config["gemini_api_key"],
            temperature=0.7,
            convert_system_message_to_human=True # Important for this library
        )
        # --------------------------------------------------------
        
        # This part for Imagen image generation remains the same
        if self.config.get("gcp_project_id") and self.config.get("image_generation_enabled"):
            try:
                vertexai.init(project=self.config["gcp_project_id"], location=self.config["gcp_location"])
                self.image_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
                print("✅ Configured to use Google Imagen for image generation.")
            except Exception as e:
                print(f"⚠️ Warning: Could not initialize Vertex AI for images. Error: {e}")
                self.image_model = None
        else:
            self.image_model = None

        self.workflow = self._build_graph()

        
    def _load_config(self, path: str) -> dict:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"❌ Error loading config file at {path}: {e}")

    def _create_directories(self):
        for key in ["blog_directory", "images_directory"]:
            dir_path = Path(self.config[key])
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"📂 Created directory: {dir_path}")

    # =========================================================================
    #  AGENT NODES
    # =========================================================================

    def content_generation_node(self, state: GraphState) -> Dict[str, Union[ContentDataType, str]]:
        print("--- 🧠 AGENT: Content Generation ---")
        topic = state["topic"]
        prompt_template = self._load_prompt_template()
        # Simple placeholder replacement for audience persona
        final_prompt_template = prompt_template.replace("[AUDIENCE_PERSONA]", "a curious tech enthusiast")
        full_prompt = f"Topic: {topic}\n\n{final_prompt_template}"

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are an expert blog post writer. Your output must be a single, valid JSON object."),
                HumanMessage(content=full_prompt)
            ])
            
            content_json = self._extract_json_from_response(response.content)
            post_data = json.loads(content_json)
            post_slug = self._create_slug(post_data.get("title", topic))
            
            return {"post_data": post_data, "post_slug": post_slug, "error": None}
        except Exception as e:
            error_message = f"Failed to generate content: {e}"
            print(f"❌ {error_message}")
            return {"error": error_message}

    def revision_node(self, state: GraphState) -> Dict[str, ContentDataType]:
        print("--- ✍️ AGENT: Content Revision ---")
        # (This node remains unchanged)
        post_data = state["post_data"]
        feedback = state["revision_feedback"]
        prompt = f"""
        You are an expert blog editor. A user has provided feedback on a blog post draft.
        Your task is to revise the 'content' part of the provided JSON based on the feedback.
        Return the complete, revised JSON object.

        **Original Post Data (JSON):**
        {json.dumps(post_data, indent=2)}

        **User Feedback for Revision:**
        "{feedback}"

        Now, provide the revised and complete JSON object for the blog post.
        """
        try:
            response = self.llm.invoke([
                SystemMessage(content="You are an expert blog editor. Your output must be a single, valid JSON object."),
                HumanMessage(content=prompt)
            ])
            content_json = self._extract_json_from_response(response.content)
            revised_data = json.loads(content_json)
            return {"post_data": revised_data, "revision_feedback": None}
        except Exception as e:
            return {"error": f"Failed to revise content: {e}"}

    def image_generation_node(self, state: GraphState) -> Dict[str, Union[List[str], str]]:
        print("--- 🎨 AGENT: Image Generation ---")
        # (This node remains unchanged)
        if not self.config.get("image_generation_enabled") or not self.image_model:
            print("⏭️ Skipping image generation (disabled or not initialized).")
            return {"image_paths": []}
        post_data = state["post_data"]
        post_slug = state["post_slug"]
        prompts = post_data.get("image_suggestions", [])
        if not prompts:
            print("No image suggestions found. Skipping image generation.")
            return {"image_paths": []}
        return {"image_paths": self._generate_with_imagen(prompts, post_slug)}

    def preview_generation_node(self, state: GraphState) -> Dict[str, str]:
        print("--- 📄 AGENT: Preview Generation ---")
        # (This node remains unchanged)
        post_data = state["post_data"]
        post_slug = state["post_slug"]
        template_str = self._load_template()
        preview_html = template_str.replace("{{TITLE}}", post_data.get("title", "No Title"))
        preview_html = preview_html.replace("{{SUBTITLE}}", post_data.get("subtitle", ""))
        preview_html = preview_html.replace("{{DATE}}", time.strftime("%B %d, %Y"))
        preview_html = preview_html.replace("{{TAGS}}", ", ".join(post_data.get("tags", [])))
        preview_html = preview_html.replace("{{CONTENT}}", post_data.get("content", ""))
        preview_html = preview_html.replace("{{CUSTOM_STYLES}}", post_data.get("custom_css_styles", ""))
        preview_html = preview_html.replace("{{FEATURED_IMAGE}}", "placeholder.jpg")
        preview_html = preview_html.replace("{{FEATURED_IMAGE_ALT}}", "Image will be generated here")
        filepath = Path(self.config["blog_directory"]) / f"{post_slug}_preview.html"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(preview_html)
        return {"preview_file_path": str(filepath)}

    def final_assembly_node(self, state: GraphState) -> Dict[str, str]:
        print("--- 🧩 AGENT: Final Assembly ---")
        # (This node remains unchanged)
        post_data = state["post_data"]
        post_slug = state["post_slug"]
        image_paths = state["image_paths"]
        template_str = self._load_template()
        final_html = self._replace_template_placeholders(template_str, post_data, image_paths, post_slug)
        filepath = Path(self.config["blog_directory"]) / f"{post_slug}.html"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final_html)
        return {"final_post_path": str(filepath)}

    def publish_node(self, state: GraphState):
        print("--- 🚀 AGENT: Publishing ---")
        # (This node remains unchanged)
        if not self.config.get("auto_commit"):
            print("Auto-commit is disabled. Manual git operations required.")
            return
        final_post_path = state["final_post_path"]
        image_paths = state["image_paths"]
        post_data = state["post_data"]
        files_to_commit = [final_post_path]
        for img_path in image_paths:
            files_to_commit.append(str(Path(self.config["images_directory"]) / Path(img_path).name))
        commit_message = f"Add new blog post: {post_data.get('title', 'New Post')}"
        try:
            repo_path = self.config["github_repo_path"]
            subprocess.run(["git", "-C", repo_path, "add"] + files_to_commit, check=True)
            subprocess.run(["git", "-C", repo_path, "commit", "-m", commit_message], check=True)
            subprocess.run(["git", "-C", repo_path, "push"], check=True)
            print(f"✅ Successfully committed and pushed: {commit_message}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Git operation failed: {e}")

    # =========================================================================
    #  HELPER & UTILITY METHODS (Unchanged)
    # =========================================================================
    def _generate_with_imagen(self, prompts: List[str], post_slug: str) -> List[str]:
        image_paths = []
        for i, prompt in enumerate(prompts[:self.config["max_images_per_post"]]):
            try:
                print(f"🎨 Generating image {i+1} with Imagen: {prompt}...")
                response = self.image_model.generate_images(prompt=prompt, number_of_images=1, aspect_ratio="3:4")
                image_name = f"{post_slug}_{i+1}.png"
                image_path = Path(self.config["images_directory"]) / image_name
                response.images[0].save(location=str(image_path))
                image_paths.append(image_name)
                print(f"✅ Generated and saved: {image_name}")
                time.sleep(2)
            except Exception as e:
                print(f"❌ Error during Imagen API call for image {i+1}: {e}")
        return image_paths

    def _replace_template_placeholders(self, template: str, data: ContentDataType, images: List[str], slug: str) -> str:
        template = template.replace("{{TITLE}}", data.get("title", "No Title"))
        template = template.replace("{{SUBTITLE}}", data.get("subtitle", ""))
        template = template.replace("{{DATE}}", time.strftime("%B %d, %Y"))
        template = template.replace("{{TAGS}}", ", ".join(data.get("tags", [])))
        template = template.replace("{{CONTENT}}", data.get("content", ""))
        template = template.replace("{{CUSTOM_STYLES}}", data.get("custom_css_styles", ""))
        template = template.replace("{{AUTHOR_NAME}}", self.config.get("author_name", "Author"))
        template = template.replace("{{DESCRIPTION}}", data.get("subtitle", "A new blog post."))
        template = template.replace("{{BLOG_URL}}", self.config.get("blog_url", ""))
        template = template.replace("{{SLUG}}", slug)
        if images:
            featured_image = images[0]
            template = template.replace("{{FEATURED_IMAGE}}", featured_image)
            template = template.replace("{{FEATURED_IMAGE_ALT}}", data.get("title", "Featured Image"))
        else:
            template = template.replace("{{FEATURED_IMAGE}}", "")
            template = template.replace("{{FEATURED_IMAGE_ALT}}", "")
        return template

    def _create_slug(self, title: str) -> str:
        title = title.lower()
        title = re.sub(r'[^a-z0-9\s-]', '', title)
        title = re.sub(r'\s+', '-', title)
        return title.strip('-')

    def _load_prompt_template(self, path: str = "prompts/prompt_template.txt") -> str:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise ValueError(f"Prompt template not found at {path}")

    def _load_template(self, key: str = "template_file") -> str:
        path = self.config[key]
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise ValueError(f"HTML template not found at {path}")
    
    def _extract_json_from_response(self, text: str) -> str:
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        return text.strip()

    # =========================================================================
    #  CONDITIONAL EDGES
    # =========================================================================
    
    def should_revise_edge(self, state: GraphState) -> str:
        print("--- 🤔 HUMAN-IN-THE-LOOP: Checking for Feedback ---")
        if state.get("revision_feedback"):
            print("Feedback received. Routing to revision agent.")
            return "revise_content"
        else:
            print("Content approved. Proceeding to image generation.")
            return "generate_images"

    # =========================================================================
    #  GRAPH CONSTRUCTION (With error handling)
    # =========================================================================

    def _build_graph(self):
        workflow = StateGraph(GraphState)
        workflow.add_node("content_generator", self.content_generation_node)
        workflow.add_node("reviser", self.revision_node)
        workflow.add_node("image_generator", self.image_generation_node)
        workflow.add_node("preview_generator", self.preview_generation_node)
        workflow.add_node("final_assembler", self.final_assembly_node)
        workflow.add_node("publisher", self.publish_node)

        workflow.set_entry_point("content_generator")
        workflow.add_edge("publisher", END)
        workflow.add_conditional_edges(
            "content_generator",
            lambda state: "preview_generator" if not state.get("error") else END,
            {"preview_generator": "preview_generator", END: END}
        )
        workflow.add_edge("reviser", "preview_generator")
        workflow.add_conditional_edges(
            "preview_generator",
            self.should_revise_edge,
            {"revise_content": "reviser", "generate_images": "image_generator"}
        )
        workflow.add_edge("image_generator", "final_assembler")
        workflow.add_edge("final_assembler", "publisher")
        return workflow.compile(checkpointer=MemorySaver())


# =========================================================================
#  MAIN EXECUTION BLOCK (Improved to handle failure)
# =========================================================================
if __name__ == "__main__":
    try:
        agent = BlogAgent()
        topic = input("📝 Enter your blog post topic: ").strip()
        if not topic:
            print("❌ Topic cannot be empty!")
        else:
            thread_config = {"configurable": {"thread_id": "main_thread"}}
            initial_input = {"topic": topic}
            current_state = None
            for event in agent.workflow.stream(initial_input, thread_config, stream_mode="values"):
                current_state = event

            if not current_state or not current_state.get('preview_file_path'):
                print("\n❌ The agent failed to generate content. Please check the error messages above.")
                if current_state and current_state.get('error'):
                    print(f"   Error details: {current_state['error']}")
            else:
                while True:
                    preview_path = current_state.get('preview_file_path')
                    print("\n" + "="*50)
                    print("HUMAN REVIEW REQUIRED")
                    print(f"✅ Preview generated at: {preview_path}")
                    print("Please review the file. What would you like to do?")
                    print("  - Type 'approve' to continue to publishing.")
                    print("  - Or, type your feedback to revise the content.")
                    print("="*50)
                    
                    feedback = input("> ").strip()
                    if feedback.lower() == 'approve':
                        print("✅ Approved! Continuing workflow...")
                        for event in agent.workflow.stream(None, thread_config, stream_mode="values"):
                             current_state = event
                        break
                    else:
                        print("🔄 Revising content with your feedback...")
                        for event in agent.workflow.stream({"revision_feedback": feedback}, thread_config, stream_mode="values"):
                            current_state = event
                
                print("\n🎉 Blog post workflow completed successfully!")
                final_path = current_state.get('final_post_path')
                if final_path:
                    print(f"📰 Final post saved at: {final_path}")

    except (ValueError, FileNotFoundError) as e:
        print(f"❌ Initialization failed: {e}")