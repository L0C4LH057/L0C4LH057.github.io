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
        
        # Create/Overwrite the template with your SPECIFIC custom HTML
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
            raise ValueError("No valid API key found in config.")
            
        # Initialize image generation clients
        self.image_generation_enabled = self.config.get("image_generation_enabled", False)
        if self.image_generation_enabled:
            self.falai_api_key = self.config.get("falai_api_key")
            if not self.falai_api_key:
                print("Warning: image generation enabled but fal.ai key missing. Skipping.")
                self.image_generation_enabled = False

        self.prompt_template = self.load_prompt_template()

    def load_config(self, path: str) -> dict:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f" Error loading config: {e}")
            exit(1)

    def create_directories(self, config: dict):
        for directory_key in ["blog_directory", "images_directory", "template_file"]:
            dir_path = Path(config[directory_key]).parent if directory_key == "template_file" else Path(config[directory_key])
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)

    def load_prompt_template(self, path: str = "prompts/prompt_template.txt") -> str:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "Write a blog post."

    def create_l0c4lh057_template(self):
        """
        Creates the HTML template file using the EXACT code provided by the user.
        """
        template_path = Path(self.config["template_file"])
        
        # This is the exact template provided in the prompt
        custom_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}} | {{AUTHOR_NAME}}</title>
    <meta name="description" content="{{DESCRIPTION}}">
    <meta property="og:type" content="article">
    <meta name="robots" content="index, follow">
    <meta property="og:title" content="{{TITLE}}">
    <meta property="og:description" content="{{DESCRIPTION}}">
    <meta property="og:image" content="{{BLOG_URL}}/images/{{FEATURED_IMAGE}}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:image" content="{{BLOG_URL}}/images/{{FEATURED_IMAGE}}">
    <meta property="og:url" content="{{BLOG_URL}}/posts/{{SLUG}}.html">
    <meta name="twitter:title" content="{{TITLE}}">
    <meta name="twitter:description" content="{{DESCRIPTION}}">
    
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        /* Your exact CSS styles from the original template */
        :root {
            --primary: #2c3e50;
            --secondary: #34495e;
            --accent: #3498db;
            --light-gray: #f5f7fa;
            --medium-gray: #e1e5eb;
            --dark-gray: #7f8c8d;
            --text: #2c3e50;
            --text-light: #95a5a6;
            --white: #ffffff;
            --shadow: 0 4px 16px rgba(44, 62, 80, 0.10);
            --border-radius: 14px;
            --transition: 0.3s cubic-bezier(.4,2,.6,1);
            --font-main: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            font-family: var(--font-main);
            background: linear-gradient(120deg, var(--light-gray) 60%, #fdecea 100%);
            color: var(--text);
            line-height: 1.7;
            font-size: 1.08rem;
            margin: 0;
            padding: 0;
            min-height: 100vh;
        }

        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 1.2rem;
        }

        header {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: var(--white);
            padding: 2.5rem 0 2rem 0;
            margin-bottom: 2.5rem;
            box-shadow: var(--shadow);
            position: relative;
            border-radius: 0 0 24px 24px;
        }

        .header-content {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            position: relative;
            z-index: 2;
        }

        .profile-container {
            width: 140px;
            height: 140px;
            border-radius: 50%;
            border: 4px solid var(--white);
            overflow: hidden;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        .profile-image {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .blog-title {
            font-size: 3.0rem;
            font-weight: 800;
            margin-bottom: 0.3rem;
            letter-spacing: 0px;
            text-shadow: 0 2px 8px rgba(44,62,80,0.08);
        }

        .blog-subtitle {
            font-size: 1.1rem;
            font-weight: 400;
            opacity: 0.92;
            margin-bottom: 1.5rem;
            color: #e1e5eb;
        }

        nav {
            width: 100%;
            max-width: 600px;
            margin-top: 0.5rem;
        }

        .nav-links {
            display: flex;
            justify-content: center;
            list-style: none;
            gap: 1.2rem;
            padding: 0;
            flex-wrap: wrap;
        }

        .nav-links a {
            color: var(--white);
            text-decoration: none;
            font-size: 1.08rem;
            font-weight: 600;
            padding: 0.5rem 1.1rem;
            border-radius: var(--border-radius);
            transition: background var(--transition), color var(--transition);
            letter-spacing: 0.02em;
        }

        .nav-links a:hover,
        .nav-links a.active {
            background-color: rgba(255,255,255,0.18);
            color: #fff;
        }

        /* Post Content */
        .post-content {
            background: var(--white);
            border-radius: var(--border-radius);
            padding: 3rem;
            box-shadow: var(--shadow);
            margin-bottom: 4rem;
        }

        .post-header {
            text-align: center;
            margin-bottom: 3rem;
        }

        .post-title {
            font-size: 2.3rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--primary);
            line-height: 1.3;
        }

        .post-subtitle {
            font-size: 1.2rem;
            color: var(--dark-gray);
            margin-bottom: 1.5rem;
            font-weight: 400;
        }

        .post-meta {
            display: flex;
            justify-content: center;
            gap: 1.2rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .meta-item {
            background: var(--light-gray);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.98rem;
            display: flex;
            align-items: center;
        }

        .meta-item i {
            margin-right: 5px;
            color: var(--accent);
        }

        .post-cover {
            width: 70%;
            height: auto;
            border-radius: var(--border-radius);
            margin-bottom: 2rem;
            box-shadow: var(--shadow);
            max-height: 590px;
            object-fit: cover;
            display: block;
            margin-left: auto;
            margin-right: auto;
        }

        .inline-image {
            width: 70%;
            display: block;
            margin: 2.5rem auto;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            max-height: 500px;
            object-fit: cover;
        }

        .share-buttons {
            text-align: center;
            margin: 1.5rem 0;
        }

        .share-buttons button,
        .share-buttons a {
            font-size: 1rem;
        }

        .post-body p {
            margin-bottom: 1.5rem;
            line-height: 1.7;
            font-size: 1.08rem;
        }

        .post-body h2 {
            font-size: 1.8rem;
            font-weight: 700;
            margin: 3rem 0 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--medium-gray);
            position: relative;
            color: var(--primary);
        }

        .post-body h2::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 60px;
            height: 2px;
            background-color: var(--accent);
        }

        .post-body h3 {
            font-size: 1.4rem;
            font-weight: 600;
            margin: 2rem 0 1rem;
            color: var(--primary);
        }

        .post-body a {
            color: var(--accent);
            text-decoration: none;
            border-bottom: 1px dotted var(--accent);
            transition: color 0.2s, border-bottom-color 0.2s;
        }

        .post-body a:hover {
            color: var(--primary);
            border-bottom-color: var(--primary);
        }

        .post-body ul, .post-body ol {
            margin-bottom: 1.5rem;
            padding-left: 1.5rem;
        }

        .post-body li {
            margin-bottom: 0.8rem;
            line-height: 1.6;
        }

        .highlight-box {
            background: rgba(52, 152, 219, 0.1);
            border-left: 4px solid var(--accent);
            padding: 1.2rem;
            margin: 2rem 0;
            border-radius: 0 var(--border-radius) var(--border-radius) 0;
        }

        footer {
            background: var(--primary);
            color: var(--white);
            padding: 2.2rem 0 1.2rem 0;
            margin-top: 3rem;
            border-radius: 24px 24px 0 0;
        }

        .footer-content {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 2rem;
        }

        .footer-section {
            flex: 1;
            min-width: 180px;
            margin-bottom: 1.2rem;
            padding-right: 1.2rem;
        }

        .footer-title {
            font-size: 1.15rem;
            margin-bottom: 1.1rem;
            position: relative;
            padding-bottom: 0.4rem;
            font-weight: 700;
        }

        .footer-title::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 32px;
            height: 2px;
            background-color: var(--accent);
            border-radius: 2px;
        }

        .footer-section p {
            font-size: 1rem;
            color: rgba(255,255,255,0.85);
        }

        .footer-links {
            list-style: none;
            padding: 0;
        }

        .footer-links li {
            margin-bottom: 0.7rem;
        }

        .footer-links a {
            color: rgba(255,255,255,0.85);
            text-decoration: none;
            transition: color var(--transition);
            font-size: 1rem;
        }

        .footer-links a:hover {
            color: var(--accent);
        }

        .social-links {
            display: flex;
            gap: 0.8rem;
            margin-top: 0.7rem;
        }

        .social-links a {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 36px;
            height: 36px;
            background: rgba(255,255,255,0.13);
            border-radius: 50%;
            color: var(--white);
            text-decoration: none;
            font-size: 18px;
            transition: background var(--transition), transform var(--transition);
        }

        .social-links a:hover {
            background: var(--accent);
            transform: translateY(-3px) scale(1.08);
        }

        .copyright {
            text-align: center;
            padding-top: 1.2rem;
            margin-top: 1.2rem;
            border-top: 1px solid rgba(255,255,255,0.13);
            color: rgba(255,255,255,0.7);
            font-size: 0.95rem;
        }

        /* Additional CSS for content elements */
        .scenario {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 1rem 1.5rem;
            border-radius: var(--border-radius);
            margin: 1.5rem 0;
            font-style: italic;
        }
        
        .scenario .highlight {
            font-style: normal;
        }

        .post-body .highlight {
            font-weight: 600;
            color: var(--accent);
        }

        .cta-box {
            background: var(--primary);
            color: var(--white);
            padding: 1.5rem;
            border-radius: var(--border-radius);
            margin: 3rem 0;
            text-align: center;
        }

        .cta-box h3 {
            color: var(--white);
            margin-bottom: 1rem;
        }

        .cta-box p a {
            color: var(--white);
            text-decoration: underline;
        }

        .cta-box p a:hover {
            color: var(--accent);
            border-bottom-color: var(--accent);
        }
        @media (max-width: 480px) {
        .nav-links {
            flex-direction: column;
            gap: 0.5rem;
            align-items: center;
        }
        .nav-links a {
            width: calc(100% - 2.2rem);
            text-align: center;
            padding: 0.6rem 1.1rem;
        }
    }

        @media (max-width: 700px) {
            .container {
                padding: 0 0.3rem;
            }
            .post-content {
                padding: 0.7rem 0.3rem;
            }
            .post-header {
                margin-bottom: 1.5rem;
            }
            .post-title {
                font-size: 1.5rem;
            }
            .post-subtitle {
                font-size: 1rem;
            }
            .post-cover, .inline-image {
                width: 100%;
                max-height: 300px;
            }
            .author-bio {
                flex-direction: column;
                text-align: center;
            }
            .author-bio .bio-image {
                margin-bottom: 0.5rem;
            }
            .related-posts ul {
                grid-template-columns: 1fr;
            }
            .footer-content {
                flex-direction: column;
                align-items: flex-start;
                gap: 1.5rem;
            }
            .footer-section {
                min-width: 0;
                padding-right: 0;
                width: 100%;
            }
        }

        @media (max-width: 480px) {
            .profile-container {
                width: 70px;
                height: 70px;
            }
            .blog-title {
                font-size: 1.25rem;
            }
            .blog-subtitle {
                font-size: 0.98rem;
            }
            .post-title {
                font-size: 1.2rem;
            }
            .post-subtitle {
                font-size: 0.9rem;
            }
            .footer-title {
                font-size: 0.98rem;
            }
            .footer-links a {
                font-size: 0.93rem;
            }
            .copyright {
                font-size: 0.85rem;
            }
            .post-content {
                padding: 0.5rem 0.1rem;
            }
            .post-header {
                margin-bottom: 1rem;
            }
            .post-meta {
                gap: 0.3rem;
                font-size: 0.9rem;
            }
            .post-cover, .inline-image {
                max-height: 200px;
                width: 100%;
            }
            .related-posts ul {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 1100px) {
            .container {
                max-width: 98vw;
                padding: 0 0.5rem;
            }
            .post-content {
                padding: 1.5rem;
            }
            .post-cover, .inline-image {
                max-height: 400px;
                width: 90%;
            }
        }

        @media (max-width: 900px) {
            .footer-content {
                flex-direction: column;
                align-items: flex-start;
                gap: 1.5rem;
            }
            .footer-section {
                min-width: 0;
                padding-right: 0;
                width: 100%;
            }
        }
        @media (max-width: 480px) {
            .footer-content {
                gap: 1rem;
            }
            .footer-section {
                font-size: 0.95rem;
            }
            .footer-title {
                font-size: 1rem;
            }
        }
        @media (max-width: 1100px) {
            .container {
                max-width: 98vw;
                padding: 0 0.5rem;
            }
            .post-content {
                padding: 1.5rem;
            }
            .post-cover, .inline-image {
                max-height: 400px;
                width: 90%;
            }
        }

        @media (max-width: 900px) {
            .footer-content {
                flex-direction: column;
                gap: 1.2rem;
            }
            .footer-section {
                min-width: 120px;
                padding-right: 0;
            }
        }

        @media (max-width: 700px) {
            .profile-container {
                width: 70px;
                height: 70px;
            }
            .blog-title {
                font-size: 1.25rem;
            }
            .blog-subtitle {
                font-size: 0.98rem;
            }
            .post-title {
                font-size: 1.5rem;
            }
            .post-subtitle {
                font-size: 1rem;
            }
            .post-content {
                padding: 0.7rem 0.3rem;
            }
            .post-header {
                margin-bottom: 1.5rem;
            }
            .post-meta {
                gap: 0.5rem;
                font-size: 0.93rem;
            }
            .post-cover, .inline-image {
                max-height: 400px;
                width: 100%;
            }
            .highlight-box {
                padding: 0.7rem 0.7rem 0.7rem 1rem;
            }
            .cta-box {
                padding: 1rem;
            }
            .author-bio {
                flex-direction: column;
                text-align: center;
            }
            .author-bio .bio-image {
                margin-bottom: 0.5rem;
            }
            .related-posts h2::before,
            .related-posts h2::after {
                width: 20%;
                left: 0;
                right: 0;
                margin: auto;
            }
            .terminal-code {
                padding: 1rem;
                font-size: 0.85rem;
            }
        }

        @media (max-width: 480px) {
            .profile-container {
                width: 100px;
                height: 100px;
                margin-bottom: 0.7rem;
            }
            .blog-title {
                font-size: 2rem;
            }
            .blog-subtitle {
                font-size: 0.85rem;
            }
            .post-title {
                font-size: 1.2rem;
            }
            .post-subtitle {
                font-size: 0.9rem;
            }
            .footer-title {
                font-size: 0.98rem;
            }
            .footer-links a {
                font-size: 0.93rem;
            }
            .copyright {
                font-size: 0.85rem;
            }
            .post-content {
                padding: 0.5rem 0.1rem;
            }
            .post-header {
                margin-bottom: 1rem;
            }
            .post-meta {
                gap: 0.3rem;
                font-size: 0.9rem;
            }
            .post-cover, .inline-image {
                max-height: 350px;
                width: 100%;
            }
            .related-posts ul {
                grid-template-columns: 1fr;
            }
        }

        /* New styles for comments section */
        .comments-section {
            margin-top: 2rem;
            background: #fff;
            padding: 1.2rem;
            border-radius: 12px;
            box-shadow: 0 6px 18px rgba(44,62,80,0.06);
        }

        .comments-section h3 {
            margin-top: 0;
            margin-bottom: 0.5rem;
            color: var(--primary);
        }

        #commentsList {
            margin-bottom: 1rem;
            font-size: 0.98rem;
            color: var(--dark-gray);
        }

        #commentForm {
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
        }

        #commenterName,
        #commentText {
            padding: 0.6rem;
            border-radius: 8px;
            border: 1px solid var(--medium-gray);
        }

        #submitComment {
            background: var(--accent);
            color: #fff;
            border: none;
            padding: 0.6rem 1rem;
            border-radius: 8px;
            cursor: pointer;
        }

        small {
            color: var(--text-light);
        }

    </style>
    {{CUSTOM_STYLES}}
</head>
<body>
    <header>
        <div class="container">
            <div class="header-content">
                <div class="profile-container">
                    <img src="../images/profile.jpg" alt="{{AUTHOR_NAME}}" class="profile-image">
                </div>
                
                <h1 class="blog-title"><span id="typed-title"></span><span class="typed-cursor">|</span></h1>
                <p class="blog-subtitle">My thoughts on Hacking, AI, Security, and more.</p>
                <nav>
                    <ul class="nav-links">
                        <li><a href="../index.html" class="active">Posts</a></li>
                        <li><a href="../whoami.html">Whoami</a></li>
                        <li><a href="../write-ups.html">Write Ups</a></li>
                        <li><a href="../tools.html">Tools</a></li>
                    </ul>
                </nav>
            </div>
        </div>
    </header>

    <div class="container">
        <div class="post-content">
            <div class="post-header">
                <h1 class="post-title">{{TITLE}}</h1>
                <p class="post-subtitle">{{SUBTITLE}}</p>
                <div class="post-meta">
                    <div class="meta-item">
                        <i class="fas fa-calendar-alt"></i> Published: {{DATE}}
                    </div>
                    <div class="meta-item">
                        <i class="fas fa-tags"></i> {{TAGS}}
                    </div>
                </div>
                <img src="../images/{{FEATURED_IMAGE}}" alt="{{FEATURED_IMAGE_ALT}}" class="post-cover">
            </div>
            <div class="share-buttons" style="text-align:center; margin: 1.5rem 0;">
                <button id="nativeShareBtn" style="background: var(--accent); color: #fff; border: none; border-radius: 6px; padding: 0.6rem 1.2rem; font-size: 1rem; cursor: pointer; margin-bottom: 0.7rem;">
                    <i class="fas fa-share-alt"></i> Share This Post
                </button>
                <div style="margin-top: 0.7rem;">
                    <a href="#" id="twitterShare" title="Share on Twitter" style="margin:0 8px; color: #1da1f2;"><i class="fab fa-twitter fa-lg"></i></a>
                    <a href="#" id="facebookShare" title="Share on Facebook" style="margin:0 8px; color: #1877f3;"><i class="fab fa-facebook fa-lg"></i></a>
                    <a href="#" id="linkedinShare" title="Share on LinkedIn" style="margin:0 8px; color: #0077b5;"><i class="fab fa-linkedin fa-lg"></i></a>
                    <a href="#" id="whatsappShare" title="Share on WhatsApp" style="margin:0 8px; color: #25d366;"><i class="fab fa-whatsapp fa-lg"></i></a>
                    <a href="#" id="copyLink" title="Copy Link" style="margin:0 8px; color: #555;"><i class="fas fa-link fa-lg"></i></a>
                </div>
            </div>
            <div class="post-body">
                {{CONTENT}}
            </div>

            <div class="comments-section" style="margin-top:2rem; background: #fff; padding:1.2rem; border-radius:12px; box-shadow: 0 6px 18px rgba(44,62,80,0.06);">
                <h3 style="margin-top:0; margin-bottom:0.5rem; color:var(--primary);">Comments</h3>
                <div id="commentsList" style="margin-bottom:1rem; font-size:0.98rem; color:var(--dark-gray);">
                    Loading comments...
                </div>

                <form id="commentForm" style="display:flex; flex-direction:column; gap:0.6rem;">
                    <input id="commenterName" type="text" placeholder="Your name (optional)" style="padding:0.6rem; border-radius:8px; border:1px solid var(--medium-gray);">
                    <textarea id="commentText" rows="4" placeholder="Share your thoughts..." required style="padding:0.6rem; border-radius:8px; border:1px solid var(--medium-gray); resize:vertical;"></textarea>
                    <div style="display:flex; gap:0.6rem; align-items:center;">
                        <button id="submitComment" type="submit" style="background:var(--accent); color:#fff; border:none; padding:0.6rem 1rem; border-radius:8px; cursor:pointer;">Post Comment</button>
                        <small style="color:var(--text-light);">Be respectful — comments are public.</small>
                    </div>
                </form>
            </div>
            <p style="text-align: center; margin-top: 2rem;">
                <a href="../index.html" style="color: var(--accent); text-decoration: none; font-weight: 500;">← Back to Blog</a>
            </p>
        </div>
    </div>

    <footer>
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <h4 class="footer-title">{{AUTHOR_NAME}}</h4>
                    <p>Cybersecurity researcher and enthusiast. Exploring the depths of ethical hacking, AI security, and modern defensive strategies. Sharing insights from the digital front lines.</p>
                </div>
                <div class="footer-section">
                    <h4 class="footer-title">Quick Links</h4>   
                    <ul class="footer-links">
                        <li><a href="../index.html">Posts</a></li>
                        <li><a href="../whoami.html">Whoami</a></li>
                        <li><a href="../tools.html">Tools</a></li>
                        <li><a href="#">Privacy Policy</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h4 class="footer-title">Connect</h4>
                    <div class="social-links">
                        <a href="https://x.com/bashirkabirz" target="_blank" title="Twitter"><i class="fab fa-twitter"></i></a>
                        <a href="https://github.com/L0C4LH057" target="_blank" title="GitHub"><i class="fab fa-github"></i></a>
                        <a href="https://www.linkedin.com/in/bashir-kabir-zarewa-18b67718a" target="_blank" title="LinkedIn"><i class="fab fa-linkedin"></i></a>
                    </div>
                </div>
            </div>
            <div class="copyright">
                &copy; <span id="copyright-year"></span> {{AUTHOR_NAME}}. All Rights Reserved. Opinions are my own.
            </div>
        </div>
    </footer>

    <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-database.js"></script>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const titleText = "Bashir Kabir Zarewa";
            const typedTitle = document.getElementById('typed-title');
            const cursor = document.querySelector('.typed-cursor');
            let i = 0;

            function typeWriter() {
                if (i <= titleText.length) {
                    typedTitle.textContent = titleText.slice(0, i);
                    i++;
                    setTimeout(typeWriter, 120);
                } else {
                    cursor.style.display = 'none';
                }
            }
            typeWriter();
        });

        document.addEventListener('DOMContentLoaded', function() {
            // Sharing logic
            const postUrl = window.location.href;
            const postTitle = document.querySelector('.post-title').innerText;

            const twitterShare = document.getElementById('twitterShare');
            twitterShare.href = `https://twitter.com/intent/tweet?url=${encodeURIComponent(postUrl)}&text=${encodeURIComponent(postTitle)}`;
            twitterShare.target = '_blank';

            const facebookShare = document.getElementById('facebookShare');
            facebookShare.href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(postUrl)}`;
            facebookShare.target = '_blank';

            const linkedinShare = document.getElementById('linkedinShare');
            linkedinShare.href = `https://www.linkedin.com/shareArticle?mini=true&url=${encodeURIComponent(postUrl)}&title=${encodeURIComponent(postTitle)}&summary=${encodeURIComponent(document.querySelector('.post-subtitle').innerText)}&source=${encodeURIComponent(window.location.origin)}`;
            linkedinShare.target = '_blank';

            const whatsappShare = document.getElementById('whatsappShare');
            whatsappShare.href = `https://api.whatsapp.com/send?text=${encodeURIComponent(postTitle + " " + postUrl)}`;
            whatsappShare.target = '_blank';

            const copyLink = document.getElementById('copyLink');
            copyLink.addEventListener('click', function(e) {
                e.preventDefault();
                navigator.clipboard.writeText(postUrl).then(() => {
                    alert('Link copied to clipboard!');
                });
            });

            // Firebase config (use your own config)
            const firebaseConfig = {
                apiKey: "AIzaSyAM6IO689VRqYn7FS_gYTjpFTwMvB4um5Y",
                authDomain: "personalblog-e8d0d.firebaseapp.com",
                databaseURL: "https://personalblog-e8d0d-default-rtdb.europe-west1.firebasedatabase.app",
                projectId: "personalblog-e8d0d",
                storageBucket: "personalblog-e8d0d.appspot.com",
                messagingSenderId: "746191305731",
                appId: "1:746191305731:web:b2802db970e04979fe2236"
            };
            // Initialize Firebase only if not already initialized
            if (!firebase.apps.length) {
                firebase.initializeApp(firebaseConfig);
            }
            const db = firebase.database();

            // --- Upvote logic (existing) ---
            const upvoteBtn = document.getElementById('upvoteBtn');
            const upvoteCount = document.getElementById('upvoteCount');
            const upvotedKey = 'ai-kids-upvoted-global';

            // Listen for upvote count changes
            db.ref('upvotes/ai-kids').on('value', (snapshot) => {
                const count = snapshot.val() || 0;
                if (upvoteCount) upvoteCount.textContent = count;
            });

            // Check if user already upvoted
            if (upvoteBtn && localStorage.getItem(upvotedKey) === 'true') {
                upvoteBtn.disabled = true;
                upvoteBtn.style.opacity = 0.7;
            }

            // Upvote logic
            if (upvoteBtn) {
                upvoteBtn.addEventListener('click', function() {
                    if (localStorage.getItem(upvotedKey) !== 'true') {
                        const upvoteRef = db.ref('upvotes/ai-kids');
                        upvoteRef.transaction(function(current) {
                            return (current || 0) + 1;
                        }, function(error, committed) {
                            if (committed && !error) {
                                localStorage.setItem(upvotedKey, 'true');
                                upvoteBtn.disabled = true;
                                upvoteBtn.style.opacity = 0.7;
                            }
                        });
                    }
                });
            }

            const nativeShareBtn = document.getElementById('nativeShareBtn');
            if (navigator.share) {
                if (nativeShareBtn) {
                    nativeShareBtn.addEventListener('click', async () => {
                        try {
                            await navigator.share({
                                title: postTitle,
                                text: document.querySelector('.post-subtitle').innerText,
                                url: postUrl,
                            });
                        } catch (err) {
                            console.error("Share failed:", err.message);
                        }
                    });
                }
            } else {
                if (nativeShareBtn) nativeShareBtn.style.display = 'none';
            }

            // --- Comments logic (new) ---
            // Try to use the template slug; fallback to deriving from URL when empty (preview)
            let postSlug = "{{SLUG}}";
            if (!postSlug || postSlug.trim() === "") {
                // derive a slug from URL as fallback
                const pathParts = window.location.pathname.split('/');
                const last = pathParts[pathParts.length - 1] || pathParts[pathParts.length - 2] || '';
                postSlug = last.replace('.html','') || 'unknown-post';
            }

            const commentsListEl = document.getElementById('commentsList');
            const commentForm = document.getElementById('commentForm');
            const commenterNameEl = document.getElementById('commenterName');
            const commentTextEl = document.getElementById('commentText');

            const commentsRef = db.ref(`comments/${postSlug}`);

            // Render comments (simple, XSS-safe by using textContent)
            function renderComments(snapshot) {
                const data = snapshot.val();
                commentsListEl.innerHTML = '';
                if (!data) {
                    commentsListEl.textContent = 'No comments yet. Be the first to leave a thought!';
                    return;
                }
                // Sort comments by timestamp ascending
                const items = Object.keys(data).map(key => ({ id: key, ...data[key] }));
                items.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));

                items.forEach(item => {
                    const wrapper = document.createElement('div');
                    wrapper.style.borderTop = '1px solid var(--medium-gray)';
                    wrapper.style.padding = '0.6rem 0';
                    const header = document.createElement('div');
                    header.style.fontSize = '0.95rem';
                    header.style.color = 'var(--text)';
                    header.style.fontWeight = '600';
                    header.textContent = item.name ? item.name : 'Anonymous';
                    const meta = document.createElement('div');
                    meta.style.fontSize = '0.8rem';
                    meta.style.color = 'var(--text-light)';
                    const date = new Date(item.timestamp || Date.now());
                    meta.textContent = date.toLocaleString();
                    const body = document.createElement('div');
                    body.style.marginTop = '0.4rem';
                    body.style.color = 'var(--text)';
                    // Use textContent to avoid HTML injection
                    body.textContent = item.text;

                    wrapper.appendChild(header);
                    wrapper.appendChild(meta);
                    wrapper.appendChild(body);
                    commentsListEl.appendChild(wrapper);
                });
            }

            // Listen for realtime updates
            commentsRef.on('value', snapshot => {
                renderComments(snapshot);
            }, err => {
                console.error('Failed to load comments:', err);
                if (commentsListEl) commentsListEl.textContent = 'Failed to load comments.';
            });

            // Submit a comment
            if (commentForm) {
                commentForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const name = (commenterNameEl && commenterNameEl.value.trim()) || '';
                    const text = (commentTextEl && commentTextEl.value.trim()) || '';
                    if (!text) return alert('Please enter a comment.');

                    const commentObj = {
                        name: name,
                        text: text,
                        timestamp: Date.now()
                        // optional: add moderation flag, ip hash, etc.
                    };

                    commentsRef.push(commentObj)
                        .then(() => {
                            if (commentTextEl) commentTextEl.value = '';
                            if (commenterNameEl) commenterNameEl.value = '';
                        })
                        .catch(err => {
                            console.error('Error posting comment:', err);
                            alert('Could not post comment. Please try again later.');
                        });
                });
            }
        });
    </script>
</body>
</html>"""
        
        # Write the template to file
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(custom_template)
        print(f"Updated template at {template_path} with custom design.")

    def _extract_json_from_response(self, text: str) -> str:
        json_match = re.search(r'```(?:json)?\s*(\{.*?})\s*```|(\{.*?})', text, re.DOTALL)
        if json_match:
            return json_match.group(1) or json_match.group(2)
        else:
            raise ValueError("No valid JSON object found in the LLM response.")

    def generate_content(self, topic: str, additional_context: str = "") -> ContentDataType:
        try:
            # Strict no emoji instruction
            full_prompt = f"Topic: {topic}\nAdditional Context: {additional_context}\n\n{self.prompt_template}\n\nIMPORTANT: Do NOT include emojis in the blog post content or title."

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
                        {"role": "system", "content": self.prompt_template + " Do not use emojis."},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.7
                )
                content_text = response.choices[0].message.content.strip()

            content_json = self._extract_json_from_response(content_text)
            return json.loads(content_json)

        except Exception as e:
            print(f" Error generating content: {e}")
            return {
                "title": f"Error generating {topic}",
                "subtitle": "Error",
                "tags": [],
                "content": f"<p>Error: {e}</p>",
                "image_suggestions": []
            }

    def refine_content_with_feedback(self, current_content: dict, feedback: str) -> ContentDataType:
        print(" Incorporating your feedback... Please wait.")
        prompt = f"""
        You are an AI blog post editor.
        STRICT RULE: Do NOT add emojis. Remove any existing emojis if found.
        USER FEEDBACK: "{feedback}"
        CURRENT JSON: {json.dumps(current_content, indent=2)}
        Return the full, updated JSON object.
        """
        try:
            if self.config.get("gemini_api_key"):
                model = self.client.GenerativeModel(self.model_name)
                response = model.generate_content(prompt)
                content_text = response.text.strip()
            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                content_text = response.choices[0].message.content.strip()

            json_string = self._extract_json_from_response(content_text)
            updated_data = json.loads(json_string)
            print(" Content updated based on your feedback.")
            return updated_data
        except Exception as e:
            print(f" Error refining content: {e}")
            return current_content 

    def create_slug(self, title: str) -> str:
        title = title.lower()
        title = re.sub(r'[^a-z0-9\s-]', '', title)
        title = re.sub(r'\s+', '-', title)
        return title.strip('-')

    def generate_images_fal_ai(self, image_descriptions: List[str], post_slug: str) -> List[str]:
        generated_images = []
        if not self.falai_api_key:
            print(" fal.ai API key not found. Skipping image generation.")
            return []
            
        model_id = self.config.get("fal_model_id", "fal-ai/fast-nano-sdxl-lightning")
        API_URL = f"https://queue.fal.ai/models/{model_id}"
        headers = {"Authorization": f"Key {self.falai_api_key}", "Content-Type": "application/json"}
        
        for i, description in enumerate(image_descriptions[:self.config.get("max_images_per_post", 3)]):
            try:
                print(f" Generating image {i+1}...")
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
            except Exception as e:
                print(f" Error during fal.ai API call: {e}")
                time.sleep(1)
                
        return generated_images

    def load_template(self) -> str:
        template_path = Path(self.config["template_file"])
        if not template_path.exists():
            self.create_l0c4lh057_template()
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def replace_template_placeholders(self, template: str, content_data: ContentDataType, images: List[str], post_slug: str) -> str:
        """Replace placeholders matching the new template's structure."""
        template = template.replace("{{TITLE}}", content_data.get("title", "No Title"))
        template = template.replace("{{SUBTITLE}}", content_data.get("subtitle", ""))
        # The new template uses DESCRIPTION meta tag, usually same as subtitle
        template = template.replace("{{DESCRIPTION}}", content_data.get("subtitle", ""))
        template = template.replace("{{DATE}}", time.strftime("%B %d, %Y"))
        
        # Handle Tags: The new template expects text inside the tags div
        tags = content_data.get("tags", [])
        tags_str = ", ".join(tags)
        template = template.replace("{{TAGS}}", tags_str)
        
        template = template.replace("{{AUTHOR_NAME}}", self.config.get("author_name", "Bashir Kabir Zarewa"))
        template = template.replace("{{BLOG_URL}}", self.config.get("blog_url", "https://yourblog.com"))
        template = template.replace("{{SLUG}}", post_slug)
        template = template.replace("{{CUSTOM_STYLES}}", content_data.get("custom_css_styles", ""))

        # Handle Featured Image
        if images:
            # The template already has <img src="../images/{{FEATURED_IMAGE}}" ...>
            # So we just provide the filename
            template = template.replace("{{FEATURED_IMAGE}}", images[0])
            template = template.replace("{{FEATURED_IMAGE_ALT}}", content_data.get("title", "Featured Image"))
        else:
            template = template.replace("{{FEATURED_IMAGE}}", "default_cover.jpg") # Fallback
            template = template.replace("{{FEATURED_IMAGE_ALT}}", "Cover Image")
        
        content = content_data.get("content", "")
        
        # Insert extra images into content if they exist
        remaining_images = images[1:]
        if remaining_images:
            paragraphs = content.split('</p>')
            step = max(1, len(paragraphs) // (len(remaining_images) + 1))
            for i, img_file in enumerate(remaining_images):
                insert_idx = (i + 1) * step
                if insert_idx < len(paragraphs):
                    # Matches the new template's image class
                    img_html = f'<img src="../images/{img_file}" alt="Blog image" class="inline-image">'
                    paragraphs.insert(insert_idx, img_html)
            content = "</p>".join(paragraphs)

        template = template.replace("{{CONTENT}}", content)
        return template

    def save_post(self, content: str, post_slug: str) -> str:
        filename = f"{post_slug}.html"
        filepath = Path(self.config["blog_directory"]) / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f" Post saved: {filepath}")
        return str(filepath)
    
    def commit_and_push(self, files: List[str], commit_message: str):
        if not self.config.get("auto_commit", False):
            print(" Auto-commit disabled.")
            return
        try:
            repo_path = self.config["github_repo_path"]
            repo_path_obj = Path(repo_path)
            relative_files = [str(Path(file).relative_to(repo_path_obj)) for file in files]
            subprocess.run(["git", "-C", repo_path, "add"] + relative_files, check=True)
            status_result = subprocess.run(["git", "-C", repo_path, "status", "--porcelain"], capture_output=True, text=True)
            if not status_result.stdout.strip():
                print(" No changes to commit.")
                return
            subprocess.run(["git", "-C", repo_path, "commit", "-m", commit_message], check=True)
            subprocess.run(["git", "-C", repo_path, "push"], check=True)
            print(f" Committed and pushed: {commit_message}")
        except Exception as e:
            print(f" Git error: {e}")

    def process_prewritten_content(self, file_path: str) -> ContentDataType:
        """
        OPTION 2: Process pre-written file.
        Instruction: Parse content inside user's template.html.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            print(" Parsing Markdown file...")
            prompt = f"""
            You are a professional web publisher. 
            Transform the following raw Markdown text into a Structured JSON object.
            
            THE RULES:
            1. **No Emojis**: Do not include any emojis.
            2. **HTML Formatting**: Convert the main body content into HTML compatible with the user's template.
               - Use <h2> for section headers.
               - Use <div class="highlight-box"> for key takeaways/blockquotes.
               - Use <p> for paragraphs.
               - Use <div class="terminal-code"> or <pre><code> for code snippets.
            3. **Title/Subtitle**: Extract from the first lines.
            4. **Images**: If you see {{image: description}}, add to 'image_suggestions'.
            
            INPUT TEXT:
            ---
            {content}
            ---

            Return JSON format:
            {{
                "title": "...",
                "subtitle": "...",
                "content": "...",
                "tags": ["tag1", "tag2"],
                "image_suggestions": ["..."]
            }}
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
            data["is_prewritten"] = True 
            return data

        except Exception as e:
            print(f" Error processing file: {e}")
            return None

    def preview_post(self, content_data: ContentDataType, post_slug: str) -> str:
        template = self.load_template()
        # Create preview (no images yet)
        preview_content = self.replace_template_placeholders(template, content_data, [], post_slug)
        preview_filename = f"{post_slug}_preview.html"
        preview_filepath = Path(self.config.get("blog_directory", "posts")) / preview_filename
        with open(preview_filepath, 'w', encoding='utf-8') as f:
            f.write(preview_content)
        return str(preview_filepath)

    def create_post(self, topic: str = "", additional_context: str = "", prewritten_file_path: str = None):
        # --- 1. Initial Content Generation ---
        if prewritten_file_path:
            print(f" Processing file: {prewritten_file_path}")
            content_data = self.process_prewritten_content(prewritten_file_path)
        else:
            print(f" Creating AI post: {topic}")
            content_data = self.generate_content(topic, additional_context)

        if not content_data or "title" not in content_data:
            print(" Failed to generate content.")
            return {}
            
        post_slug = self.create_slug(content_data.get("title", topic or "untitled"))

        # --- 2. Approval Loop ---
        while True:
            preview_file = self.preview_post(content_data, post_slug)
            print("\n" + "="*50)
            print(f" PREVIEW: {preview_file}")
            print("="*50)
            
            user_input = input("\nType 'approve' or provide feedback:\n> ").strip()

            if user_input.lower() == 'approve':
                print("\n Approved!")
                break
            elif not user_input:
                print(" Please provide input.")
            else:
                content_data = self.refine_content_with_feedback(content_data, user_input)

        # --- 3. Image Generation ---
        images = []
        if self.image_generation_enabled:
            image_descriptions = content_data.get("image_suggestions", [])
            if image_descriptions:
                images = self.generate_images_fal_ai(image_descriptions, post_slug)
            else:
                print(" No image suggestions found.")
        
        # --- 4. Finalize ---
        template = self.load_template()
        final_content = self.replace_template_placeholders(template, content_data, images, post_slug)
        post_file = self.save_post(final_content, post_slug)
        
        files_to_commit = [post_file]
        if images:
            image_dir = self.config["images_directory"]
            files_to_commit.extend([str(Path(image_dir) / img) for img in images])
        
        commit_message = f"Add blog post: {content_data['title']}"
        self.commit_and_push(files_to_commit, commit_message)
        
        final_url = f"{self.config.get('blog_url', 'N/A')}/posts/{post_slug}.html"
        print("\n" + "=" * 20)
        print(f" DONE: {final_url}")
        print("=" * 20)
        
        return {"title": content_data["title"], "file": post_file}

if __name__ == "__main__":
    import sys
    try:
        agent = BlogPostAgent()
    except Exception as e:
        print(f" Init failed: {e}")
        sys.exit(1)
        
    if len(sys.argv) > 1:
        file_path = " ".join(sys.argv[1:])
        if os.path.exists(file_path):
            agent.create_post(prewritten_file_path=file_path)
        else:
            print(f" File not found: {file_path}")
            sys.exit(1)
    else:
        print("\n Blog AI Agent")
        mode = input(" (1) AI Post or (2) File? (1/2): ").strip()
        if mode == "1":
            topic = input(" Topic: ").strip()
            if topic: agent.create_post(topic, input(" Context: "))
        elif mode == "2":
            path = input(" File path: ").strip()
            if os.path.exists(path): agent.create_post(prewritten_file_path=path)
            else: print(" File not found.")
