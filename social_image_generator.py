#!/usr/bin/env python3
"""
Social Media Image Generator
Generates social media images using GPT-Image-1
"""

import os
import base64
import time
from typing import List
from openai import OpenAI
import dotenv
from flow_parser import UserAction

dotenv.load_dotenv()


class SocialImageGenerator:
    """Generates social media images using GPT-Image-1"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
    
    def generate_image(self, actions: List[UserAction], flow_name: str) -> str:
        """Generate social media image and return filename"""
        prompt = self._create_prompt(actions, flow_name)
        
        response = self.client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            quality="high",
            background="auto",
            output_format="png",
            moderation="auto",
            n=1
        )
        
        # Save image
        image_bytes = base64.b64decode(response.data[0].b64_json)
        filename = f"social_media_{int(time.time())}.png"
        
        with open(filename, "wb") as f:
            f.write(image_bytes)
        
        return filename
    
    def _create_prompt(self, actions: List[UserAction], flow_name: str) -> str:
        """Create GPT-Image-1 prompt for social media image"""
        # Analyze actions to determine key elements
        has_search = any(action.action_type == 'search' for action in actions)
        has_product = any(action.action_type == 'select_product' for action in actions)
        has_colors = any(action.action_type == 'select_option' for action in actions)
        has_cart = any(action.action_type == 'add_to_cart' for action in actions)
        
        elements = []
        if has_search:
            elements.append("search interface with magnifying glass")
        if has_product:
            elements.append("sleek scooter or mobility device")
        if has_colors:
            elements.append("color customization options (blue, pink)")
        if has_cart:
            elements.append("shopping cart icon")
        
        return f"""Create a vibrant social media image for "{flow_name}".

Design requirements:
- Modern, clean design with bright gradient background
- Professional but approachable style
- Square format optimized for social media
- Bold title text overlay: "{flow_name}"

Include these elements:
{chr(10).join(f"- {element}" for element in elements)}
- Target branding (red bullseye logo, red/white colors)
- Clean retail/e-commerce aesthetic

Style: Modern flat design, tutorial/guide appearance, highly shareable, engaging visual hierarchy."""