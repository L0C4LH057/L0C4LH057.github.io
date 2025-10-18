#!/usr/bin/env python3
"""
Automates the creation of blog posts with AI-generated content and images
"""

import os
import re
import json
import requests
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import openai  # You'll need: pip install openai
from PIL import Image
import io
import time

class BlogPostAgent:
    def __init__(self, config_file: str = "blog_config.json"):
        """Initialize the blog post agent with configuration"""
        self.config = self.load_config(config_file)
        self.setup_directories()
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            "blog_directory": "./posts",
            "template_file": "template.html",
            "images_directory": "./images",
            "openai_api_key": "your-openai-api-key-here",
            "github_repo_path": "./",
            "auto_commit": True,
            "image_generation_enabled": True,
            "max_images_per_post": 3,
            "author_name": "Bashir Kabir Zarewa",
            "author_twitter": "@bashirkabirz",
            "blog_url": "https://l0c4lh057.github.io",
            "firebase_config": {
                "apiKey": "AIzaSyAM6IO689VRqYn7FS_gYTjpFTwMvB4um5Y",
                "authDomain": "personalblog-e8d0d.firebaseapp.com",
                "databaseURL": "https://personalblog-e8d0d-default-rtdb.europe-west1.firebasedatabase.app",
                "projectId": "personalblog-e8d0d"
            }
        }
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                return {**default_config, **config}
        except FileNotFoundError:
            print(f"Config file {config_file} not found. Creating default config.")
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def setup_directories(self):
        """Create necessary directories if they don't exist"""
        Path(self.config["blog_directory"]).mkdir(exist_ok=True)
        Path(self.config["images_directory"]).mkdir(exist_ok=True)
    
    def load_template(self) -> str:
        """Load the HTML template - creates default if missing"""
        template_path = Path(self.config["template_file"])
        if not template_path.exists():
            print(f"Template file {template_path} not found. Creating L0C4LH057 style template...")
            self.create_l0c4lh057_template(str(template_path))
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def create_l0c4lh057_template(self, template_path: str):
        """Create a template matching L0C4LH057's blog style"""
        template_content = '''<!DOCTYPE html>
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
            box-<!DOCTYPE html>
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
            bordshadow: 0 4px 15px rgba(0, 0, 0, 0.2);
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
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="header-content">
                <div class="profile-container">
                    <img src="../images/profile.jpg" alt="{{AUTHOR_NAME}}" class="profile-image">
                </div>
                <h1 class="blog-title">{{AUTHOR_NAME}}</h1>
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
                &copy; <span id="copyright-year"></span> {{AUTHOR_NAME}}. All Rights Reserved.
            </div>
        </div>
    </footer>

    <script>
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

            const nativeShareBtn = document.getElementById('nativeShareBtn');
            if (navigator.share) {
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
            } else {
                nativeShareBtn.style.display = 'none';
            }
        });
    </script>
</body>
</html>'''
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
    
    def generate_content(self, topic: str, additional_context: str = "") -> Dict[str, str]:
        """Generate blog post content using AI with L0C4LH057 style"""
        openai.api_key = self.config["openai_api_key"]
        
        prompt = f"""
        You are writing a blog post for Bashir Kabir Zarewa's blog (L0C4LH057.github.io). 

        WRITING STYLE ANALYSIS:
        - Personal, engaging opening that connects with reader experience
        - Conversational tone with technical depth
        - Uses personal anecdotes and journey-style storytelling
        - Includes "Real-world Scenario" examples in scenario divs
        - Mix of technical and personal development topics
        - Educational but accessible to general audience
        - Uses highlight spans for key terms: <span class="highlight">term</span>
        - Includes actionable strategies and practical examples

        CONTENT STRUCTURE PATTERNS:
        - Strong personal hook in opening paragraphs
        - Science/research-backed explanations
        - Numbered actionable strategies with subheadings
        - Each strategy includes explanation + real-world scenario
        - Uses academic links with target="_blank" rel="noopener noreferrer"
        - Key takeaway boxes and CTA boxes
        - Mix of technical concepts with practical application

        Topic: {topic}
        Additional context: {additional_context}

        Create a comprehensive blog post with:
        
        1. **Title**: Compelling, benefit-focused (like "Ultimate Guide to..." or "How to...")
        2. **Subtitle**: Clear value proposition explaining what readers will learn
        3. **Content**: 
           - Start with personal hook and reader connection (2-3 paragraphs)
           - Use h2 with FontAwesome icons for main sections
           - Include h3 for numbered strategies/points
           - Add real-world scenarios in scenario divs: <div class="scenario"><p><span class="highlight">Real-world Scenario:</span> Example here</p></div>
           - Use <span class="highlight">term</span> for key technical terms
           - Include academic/authoritative links
           - End sections with highlight-box or cta-box
           - Write 1000-2000 words
           - Use technical depth but keep accessible
        4. **Description**: SEO meta description (150-160 characters)
        5. **Tags**: 4-6 relevant tags
        6. **Image Suggestions**: Describe 3-4 specific, visual images

        Content structure example:
        <p>Personal opening that hooks the reader...</p>
        
        <h2><i class="fas fa-brain"></i> The Science Behind [Topic]</h2>
        <p>Research-backed explanation with <span class="highlight">key terms</span>...</p>
        
        <h3>1. First Strategy/Point</h3>
        <p>Detailed explanation...</p>
        <div class="scenario"><p><span class="highlight">Real-world Scenario:</span> Practical example...</p></div>
        
        <div class="highlight-box">
            <p><strong>Key Takeaway:</strong> Main insight here.</p>
        </div>

        Format as JSON with keys: title, subtitle, content, description, tags, image_suggestions

        Make it authentic to Bashir's style - personal, educational, with practical value.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,
                temperature=0.7
            )
            
            content_text = response.choices[0].message.content
            try:
                return json.loads(content_text)
            except json.JSONDecodeError:
                return self.parse_ai_response(content_text, topic)
                
        except Exception as e:
            print(f"Error generating content: {e}")
            return self.get_fallback_content(topic)
    
    def parse_ai_response(self, response_text: str, topic: str) -> Dict[str, str]:
        """Parse AI response if JSON parsing fails"""
        return {
            "title": f"{topic}: A Deep Dive",
            "subtitle": f"Exploring the implications and applications of {topic}",
            "content": f"<h2><i class='fas fa-info-circle'></i> About {topic}</h2><p>This post explores {topic} from a cybersecurity perspective. Content generation encountered issues - please review and edit manually.</p>",
            "description": f"A comprehensive analysis of {topic} from a cybersecurity researcher's perspective.",
            "tags": ["cybersecurity", "technology", "analysis"],
            "image_suggestions": [f"Conceptual illustration of {topic}", "Technical diagram", "Security visualization"]
        }
    
    def get_fallback_content(self, topic: str) -> Dict[str, str]:
        """Fallback content when AI generation fails"""
        return {
            "title": f"Understanding {topic}: A Technical Analysis",
            "subtitle": f"A comprehensive look at {topic} through the lens of cybersecurity",
            "content": f"<h2><i class='fas fa-laptop-code'></i> Introduction</h2><p>This post explores {topic} and its implications for cybersecurity professionals.</p><p><strong>Note:</strong> AI content generation failed. Please add your analysis here.</p>",
            "description": f"Technical analysis of {topic} from a cybersecurity perspective.",
            "tags": ["cybersecurity", "technology", topic.lower().replace(" ", "-")],
            "image_suggestions": [f"Technical illustration of {topic}", "Cybersecurity concept art"]
        }
    
    def generate_images(self, image_descriptions: List[str], post_slug: str) -> List[str]:
        """Generate images using DALL-E and save them"""
        if not self.config["image_generation_enabled"]:
            return []
        
        openai.api_key = self.config["openai_api_key"]
        generated_images = []
        
        for i, description in enumerate(image_descriptions[:self.config["max_images_per_post"]]):
            try:
                print(f"Generating image {i+1}: {description}")
                response = openai.Image.create(
                    prompt=f"{description}, professional cybersecurity blog illustration, high quality, detailed",
                    n=1,
                    size="1024x1024"
                )
                
                image_url = response['data'][0]['url']
                image_name = f"{post_slug}_{i+1}.png"
                image_path = Path(self.config["images_directory"]) / image_name
                
                # Download and save image
                img_response = requests.get(image_url)
                with open(image_path, 'wb') as f:
                    f.write(img_response.content)
                
                generated_images.append(image_name)
                print(f"✅ Generated: {image_name}")
                
                # Add delay to avoid rate limits
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error generating image {i+1}: {e}")
        
        return generated_images
    
    def create_slug(self, title: str) -> str:
        """Create URL-friendly slug from title"""
        # Remove special characters and convert to lowercase
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        # Replace spaces and multiple hyphens with single hyphen
        slug = re.sub(r'[-\s]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        # Limit length
        return slug[:60] if len(slug) > 60 else slug
    
    def format_date(self) -> str:
        """Format date in L0C4LH057 style: '27th Jul 2025'"""
        now = datetime.now()
        day = now.day
        
        # Add ordinal suffix
        if 10 <= day % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        
        return now.strftime(f"%{day}{suffix} %b %Y").replace(f"%{day}", str(day))
    
    def replace_template_placeholders(self, template: str, content_data: Dict, images: List[str], post_slug: str) -> str:
        """Replace placeholders in template with actual content"""
        
        # Basic replacements
        replacements = {
            "{{TITLE}}": content_data["title"],
            "{{SUBTITLE}}": content_data.get("subtitle", content_data.get("description", "")),
            "{{CONTENT}}": content_data["content"],
            "{{DESCRIPTION}}": content_data.get("description", ""),
            "{{DATE}}": self.format_date(),
            "{{SLUG}}": post_slug,
            "{{TAGS}}": ", ".join(content_data.get("tags", [])),
            "{{AUTHOR_NAME}}": self.config["author_name"],
            "{{AUTHOR_TWITTER}}": self.config["author_twitter"],
            "{{BLOG_URL}}": self.config["blog_url"],
            "{{FIREBASE_CONFIG}}": json.dumps(self.config["firebase_config"]),
        }
        
        # Handle featured image (first generated image or default)
        featured_image = images[0] if images else "default-post-cover.png"
        featured_image_alt = f"Featured image for {content_data['title']}"
        
        replacements["{{FEATURED_IMAGE}}"] = featured_image
        replacements["{{FEATURED_IMAGE_ALT}}"] = featured_image_alt
        
        # Replace all placeholders
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, str(value))
        
        # Insert inline images into content if available
        if len(images) > 1:
            # Look for good places to insert additional images
            content = content_data["content"]
            
            # Insert second image after first h2 section if it exists
            if len(images) > 1:
                h2_pattern = r'(<h2.*?</h2>.*?</p>)'
                if re.search(h2_pattern, content, re.DOTALL):
                    content = re.sub(
                        h2_pattern,
                        r'\1\n<img src="../images/' + images[1] + f'" alt="Inline illustration for {content_data["title"]}" class="inline-image">',
                        content,
                        count=1,
                        flags=re.DOTALL
                    )
            
            # Insert third image in the middle if available
            if len(images) > 2:
                # Find midpoint of content and insert image
                paragraphs = content.split('</p>')
                mid_point = len(paragraphs) // 2
                if mid_point > 0:
                    paragraphs[mid_point] += f'\n<img src="../images/{images[2]}" alt="Supporting illustration for {content_data["title"]}" class="inline-image">'
                    content = '</p>'.join(paragraphs)
            
            # Update content with inline images
            template = template.replace(content_data["content"], content)
        
        return template
    
    def save_post(self, content: str, post_slug: str) -> str:
        """Save the generated post to a file"""
        filename = f"{post_slug}.html"
        filepath = Path(self.config["blog_directory"]) / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📄 Post saved: {filepath}")
        return str(filepath)
    
    def commit_and_push(self, files: List[str], commit_message: str):
        """Commit and push changes to GitHub"""
        if not self.config["auto_commit"]:
            print("⚠️  Auto-commit disabled. Manual git operations required.")
            return
        
        try:
            # Change to repo directory
            original_dir = os.getcwd()
            os.chdir(self.config["github_repo_path"])
            
            # Add files
            for file in files:
                result = subprocess.run(["git", "add", file], capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"⚠️  Warning adding {file}: {result.stderr}")
            
            # Check if there are changes to commit
            result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if not result.stdout.strip():
                print("ℹ️  No changes to commit.")
                return
            
            # Commit
            result = subprocess.run(["git", "commit", "-m", commit_message], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Git commit failed: {result.stderr}")
                return
            
            # Push
            result = subprocess.run(["git", "push"], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Git push failed: {result.stderr}")
                return
            
            print(f"✅ Successfully committed and pushed: {commit_message}")
            
        except Exception as e:
            print(f"❌ Git operation failed: {e}")
        finally:
            os.chdir(original_dir)
    
    def create_post(self, topic: str, additional_context: str = "", auto_publish: bool = True) -> Dict:
        """Main method to create a complete blog post"""
        print(f"🚀 Creating blog post about: {topic}")
        
        # Step 1: Generate content
        print("🤖 Generating content with AI...")
        content_data = self.generate_content(topic, additional_context)
        
        # Step 2: Create slug
        post_slug = self.create_slug(content_data["title"])
        print(f"📝 Post slug: {post_slug}")
        
        # Step 3: Generate images
        images = []
        if content_data.get("image_suggestions") and self.config["image_generation_enabled"]:
            print("🎨 Generating images...")
            images = self.generate_images(content_data["image_suggestions"], post_slug)
        else:
            print("⏭️  Skipping image generation")
        
        # Step 4: Load template and replace placeholders
        print("📋 Processing template...")
        template = self.load_template()
        final_content = self.replace_template_placeholders(template, content_data, images, post_slug)
        
        # Step 5: Save post
        post_file = self.save_post(final_content, post_slug)
        
        # Step 6: Commit and push if enabled
        if auto_publish:
            files_to_commit = [post_file] + [f"images/{img}" for img in images]
            commit_message = f"Add new blog post: {content_data['title']}"
            self.commit_and_push(files_to_commit, commit_message)
        
        print(f"\n🎉 Blog post created successfully!")
        print(f"📰 Title: {content_data['title']}")
        print(f"📁 File: {post_file}")
        print(f"🔗 Slug: {post_slug}")
        print(f"🖼️  Images: {len(images)} generated")
        
        if auto_publish:
            print(f"🌐 Live at: {self.config['blog_url']}/posts/{post_slug}.html")
        
        return {
            "title": content_data["title"],
            "subtitle": content_data.get("subtitle", ""),
            "file": post_file,
            "slug": post_slug,
            "images": images,
            "tags": content_data.get("tags", []),
            "url": f"{self.config['blog_url']}/posts/{post_slug}.html"
        }

# Usage example and CLI integration
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Quick command line usage
        topic = " ".join(sys.argv[1:])
        agent = BlogPostAgent()
        result = agent.create_post(topic)
    else:
        # Interactive usage
        print("🤖 L0C4LH057 Blog AI Agent")
        print("=" * 40)
        
        # Initialize the agent
        try:
            agent = BlogPostAgent()
            print("✅ Agent initialized successfully!")
        except Exception as e:
            print(f"❌ Error initializing agent: {e}")
            exit(1)
        
        # Get input
        topic = input("\n📝 Enter your blog post topic: ").strip()
        if not topic:
            print("❌ Topic cannot be empty!")
            exit(1)
        
        context = input("📋 Additional context (optional): ").strip()
        
        # Create post
        try:
            result = agent.create_post(topic, context)
            print(f"\n✨ Success! Your post is ready at: {result['url']}")
        except Exception as e:
            print(f"❌ Error creating post: {e}")