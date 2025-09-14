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
    
    def generate_image(self, actions: List[UserAction], flow_name: str, summary_data: dict = None, insights: dict = None) -> str:
        """Generate social media image and return filename"""
        prompt = self._create_prompt(actions, flow_name, summary_data, insights)
        
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
    
    def _create_prompt(self, actions: List[UserAction], flow_name: str, summary_data: dict = None, insights: dict = None) -> str:
        """Create dynamic, contextual prompt based on actual user behavior and flow content"""
        
        # Analyze actual user actions to create contextual messaging
        action_analysis = self._analyze_user_actions(actions)
        flow_context = self._extract_flow_context(flow_name, actions)
        
        # Use AI insights if available, otherwise fall back to action analysis
        if insights:
            completion_rate = insights.get('user_behavior_indicators', {}).get('completion_rate', 0)
            flow_type = insights.get('flow_classification', 'General Flow')
            user_behaviors = insights.get('user_behavior_indicators', {})
            
            # Use LLM-extracted brand and context information
            if 'extracted_brand' in insights:
                flow_context['brand'] = insights['extracted_brand']
                flow_context['brand_elements'] = self._generate_brand_elements(insights['extracted_brand'])
                flow_context['task_context'] = insights['task_type']
        else:
            completion_rate = 100 if any(a.action_type == 'complete' for a in actions) else 0
            flow_type = action_analysis['flow_type']
            user_behaviors = action_analysis['behaviors']
        
        # Generate dynamic messaging based on context
        messaging = self._generate_contextual_messaging(
            flow_context, action_analysis, completion_rate, user_behaviors, insights
        )

        return f"""Create a natural, authentic social media image that captures genuine personal satisfaction.

MAIN CONCEPT:
Text: "{messaging['headline']}"
Feeling: Genuine {messaging['outcome_emotion']} and happiness
Focus: {messaging['main_subject']}
Brand: {messaging['brand_mention']} (subtle, natural placement)

VISUAL APPROACH:
Style: {messaging['visual_theme']}
Background: {messaging['background_style']}
Mood: Natural lifestyle moment, authentic personal joy
Typography: Clean, modern, highly readable on mobile

COMPOSITION GUIDELINES:
- Square format (1024x1024) optimized for social media
- Primary focus on the {messaging['main_subject']} and person's genuine happiness
- Text positioned naturally, not dominating the image
- Colors that feel warm, authentic, and Instagram-native
- Lighting that feels natural and inviting
- Overall aesthetic: "This could be my friend's post"

AVOID:
- Corporate or advertisement feel
- Overly staged or artificial elements
- Busy backgrounds that distract from the main message
- Gimmicky visual effects or icons

Create an image that makes viewers think: "{messaging['engagement_hook']}" and genuinely want to engage with the content."""
    
    def _analyze_user_actions(self, actions: List[UserAction]) -> dict:
        """Analyze user actions to understand behavior patterns"""
        action_types = [action.action_type for action in actions]
        action_descriptions = [action.description for action in actions]
        
        # Determine flow type based on actions
        if 'add_to_cart' in action_types:
            flow_type = "E-commerce Purchase"
            journey_type = "Product to Cart"
        elif 'search' in action_types and 'select_product' in action_types:
            flow_type = "Product Discovery"
            journey_type = "Search to Selection"
        elif 'form_submission' in action_types:
            flow_type = "Form Completion"
            journey_type = "Information Entry"
        else:
            flow_type = "Navigation Flow"
            journey_type = "General Browsing"
        
        # Analyze behaviors
        behaviors = {
            'exploratory': 'browse_options' in action_types or 'select_option' in action_types,
            'decisive': len([a for a in action_types if a in ['add_to_cart', 'form_submission']]) > 0,
            'comparative': action_types.count('select_option') > 1,
            'goal_oriented': 'search' in action_types
        }
        
        return {
            'flow_type': flow_type,
            'journey_type': journey_type,
            'behaviors': behaviors,
            'total_actions': len(actions),
            'key_actions': [desc for desc in action_descriptions if any(keyword in desc.lower() 
                          for keyword in ['clicked', 'selected', 'added', 'searched'])][:3]
        }
    
    def _extract_flow_context(self, flow_name: str, actions: List[UserAction]) -> dict:
        """Extract contextual information from flow name and actions for ANY digital product"""
        
        # Universal brand extraction - look for common patterns
        brand = self._detect_brand_from_flow_name(flow_name)
        brand_elements = self._generate_brand_elements(brand)
        
        # Extract the main task/goal (not just products)
        task_context = self._extract_task_context(flow_name)
        
        return {
            'brand': brand,
            'brand_elements': brand_elements,
            'task_context': task_context,
            'domain': flow_name.lower()
        }
    
    def _detect_brand_from_flow_name(self, flow_name: str) -> str:
        """Detect brand/product name from flow title using common patterns"""
        flow_lower = flow_name.lower()
        
        # Common brand indicators
        brand_patterns = [
            # Direct mentions
            r'\bon\s+(\w+)\.com\b',  # "on target.com"
            r'\bin\s+(\w+)\b',       # "in slack"
            r'\busing\s+(\w+)\b',    # "using figma"
            r'\bwith\s+(\w+)\b',     # "with salesforce"
            
            # App/platform patterns
            r'^(\w+)\s+\w+',         # "Slack workspace setup"
            r'\b(\w+)\s+app\b',      # "notion app"
            r'\b(\w+)\s+platform\b', # "zoom platform"
            r'\b(\w+)\s+dashboard\b', # "analytics dashboard"
        ]
        
        for pattern in brand_patterns:
            import re
            match = re.search(pattern, flow_lower)
            if match:
                brand_candidate = match.group(1).title()
                # Filter out generic words
                if brand_candidate.lower() not in ['the', 'your', 'our', 'this', 'that', 'new', 'first']:
                    return brand_candidate
        
        # Fallback: look for capitalized words that might be brands
        words = flow_name.split()
        for word in words:
            if word[0].isupper() and len(word) > 2:
                # Skip common generic words
                if word.lower() not in ['add', 'create', 'setup', 'your', 'the', 'how', 'to']:
                    return word
        
        return "Unknown"
    
    def _generate_brand_elements(self, brand: str) -> str:
        """Generate appropriate brand elements for any brand"""
        if brand == "Unknown":
            return "Clean, modern branding elements"
        else:
            return f"{brand} branding with consistent color scheme and logo"
    
    def _extract_task_context(self, flow_name: str) -> str:
        """Extract what the user is actually trying to accomplish"""
        flow_lower = flow_name.lower()
        
        # SaaS/Digital product task patterns
        if any(word in flow_lower for word in ['setup', 'set up', 'configure']):
            return 'setup and configuration'
        elif any(word in flow_lower for word in ['create', 'build', 'design']):
            return 'creation and design'
        elif any(word in flow_lower for word in ['workspace', 'account', 'profile']):
            return 'workspace setup'
        elif any(word in flow_lower for word in ['dashboard', 'analytics', 'report']):
            return 'analytics and reporting'
        elif any(word in flow_lower for word in ['meeting', 'call', 'schedule']):
            return 'meeting and scheduling'
        elif any(word in flow_lower for word in ['project', 'task', 'workflow']):
            return 'project management'
        elif any(word in flow_lower for word in ['team', 'collaboration', 'share']):
            return 'team collaboration'
        elif any(word in flow_lower for word in ['cart', 'shop', 'buy', 'purchase']):
            return 'online shopping'
        elif any(word in flow_lower for word in ['onboard', 'tutorial', 'learn']):
            return 'learning and onboarding'
        else:
            return 'digital workflow'
    
    def _generate_contextual_messaging(self, flow_context: dict, action_analysis: dict, 
                                     completion_rate: int, user_behaviors: dict, insights: dict = None) -> dict:
        """Generate authentic social media content that people actually want to share"""
        
        # Use LLM-extracted product type if available, otherwise extract from flow
        if insights and 'product_type' in insights:
            main_subject = insights['product_type'].lower()
        else:
            main_subject = self._extract_main_subject(flow_context, action_analysis)
        
        outcome_emotion = self._determine_outcome_emotion(action_analysis, completion_rate)
        brand_mention = self._create_subtle_brand_mention(flow_context)
        
        # Create Instagram-worthy headlines (short and impactful)
        headline = self._generate_personal_headline(main_subject, outcome_emotion, action_analysis)
        
        # Visual theme focused on the outcome/feeling, not the process
        visual_theme = self._create_outcome_visual_theme(main_subject, outcome_emotion, flow_context)
        
        # Background that supports the lifestyle/achievement vibe
        background_style = self._generate_aesthetic_background(outcome_emotion, main_subject)
        
        # Engagement hook that feels genuine and relatable
        engagement_hook = self._create_relatable_hook(outcome_emotion, main_subject)
        
        # Natural CTA that encourages sharing
        cta_message = self._generate_social_cta(main_subject, outcome_emotion)
        
        return {
            'headline': headline,
            'visual_theme': visual_theme,
            'main_subject': main_subject,
            'brand_mention': brand_mention,
            'background_style': background_style,
            'engagement_hook': engagement_hook,
            'cta_message': cta_message,
            'outcome_emotion': outcome_emotion
        }
    
    def _extract_main_subject(self, flow_context: dict, action_analysis: dict) -> str:
        """Extract what the user was actually trying to accomplish (SaaS/digital focus)"""
        domain = flow_context['domain'].lower()
        task_context = flow_context['task_context']
        
        # Map task contexts to social media subjects
        task_subject_map = {
            'setup and configuration': 'setup',
            'creation and design': 'project',
            'workspace setup': 'workspace',
            'analytics and reporting': 'dashboard',
            'meeting and scheduling': 'meeting',
            'project management': 'workflow',
            'team collaboration': 'collaboration',
            'online shopping': 'purchase',
            'learning and onboarding': 'onboarding',
            'digital workflow': 'workflow'
        }
        
        # Get the main subject from task context
        main_subject = task_subject_map.get(task_context, 'workflow')
        
        # Look for specific items/tools in the flow name for more context
        if 'workspace' in domain:
            return 'workspace'
        elif 'dashboard' in domain or 'analytics' in domain:
            return 'dashboard'
        elif 'project' in domain or 'task' in domain:
            return 'project'
        elif 'meeting' in domain or 'call' in domain:
            return 'meeting setup'
        elif 'account' in domain or 'profile' in domain:
            return 'account'
        elif 'report' in domain:
            return 'report'
        elif 'design' in domain or 'prototype' in domain:
            return 'design'
        elif any(product in domain for product in ['scooter', 'cart', 'shop', 'buy']):
            return 'purchase'  # Keep e-commerce support
        else:
            return main_subject
    
    def _determine_outcome_emotion(self, action_analysis: dict, completion_rate: int) -> str:
        """Determine the emotional outcome of the flow"""
        if completion_rate == 100:
            # Priority: Decisive + Goal-oriented = Achievement (most satisfying outcome)
            if action_analysis['behaviors'].get('decisive', False) and action_analysis['behaviors'].get('goal_oriented', False):
                return 'achievement'  # "Just got my..."
            elif action_analysis['behaviors'].get('exploratory', False):
                return 'discovery'  # "Found the perfect..."
            else:
                return 'satisfaction'  # "Finally got..."
        else:
            return 'progress'  # "Getting closer to..."
    
    def _create_subtle_brand_mention(self, flow_context: dict) -> str:
        """Create a natural brand mention if relevant"""
        brand = flow_context['brand']
        if brand and brand != 'Unknown':
            # Clean up brand name for social media mention
            clean_brand = brand.lower().replace('.com', '').replace('www.', '')
            return f"@{clean_brand}"
        return ""
    
    def _generate_personal_headline(self, main_subject: str, outcome_emotion: str, action_analysis: dict) -> str:
        """Generate professional/productivity-focused headlines for LinkedIn/professional social media"""
        
        if outcome_emotion == 'achievement':
            # Professional achievement headlines
            headlines = {
                'workspace': "Just set up my perfect workspace!",
                'dashboard': "Finally got my analytics dashboard dialed in!",
                'project': "Just launched my first project!",
                'workflow': "Streamlined my workflow like a pro!",
                'meeting setup': "Meeting setup game is strong now!",
                'account': "Account setup complete and loving it!",
                'design': "Just created my best design yet!",
                'collaboration': "Team collaboration just got so much better!",
                'onboarding': "Onboarding complete - ready to crush it!",
                'purchase': "Just got my dream purchase!",
                'setup': "Setup complete and it feels amazing!",
                # E-commerce specific items
                'scooter': "Just got my dream scooter!",
                'bike': "Just got my perfect bike!",
                'shoes': "Just got my new favorite shoes!",
                'laptop': "Just got my dream laptop!",
                'phone': "Just got my new phone!"
            }
            return headlines.get(main_subject, f"Just got my perfect {main_subject}!")
                
        elif outcome_emotion == 'discovery':
            # Discovery/learning headlines  
            headlines = {
                'workspace': "Found the perfect workspace setup!",
                'dashboard': "Discovered some amazing dashboard insights!",
                'workflow': "Found my new favorite workflow!",
                'collaboration': "Best team collaboration tool ever!",
                'onboarding': "This onboarding process is incredible!",
                'purchase': "Found exactly what I was looking for!"
            }
            return headlines.get(main_subject, f"Discovered the best {main_subject} approach!")
                
        elif outcome_emotion == 'satisfaction':
            return f"So happy with my new {main_subject}!"
            
        else:  # progress
            return f"Almost got my {main_subject} perfect!"
    
    def _create_outcome_visual_theme(self, main_subject: str, outcome_emotion: str, flow_context: dict) -> str:
        """Create visual theme focused on SaaS/digital product outcomes"""
        
        # Dynamic visual themes based on subject and emotion
        if main_subject in ['scooter', 'bike', 'skateboard']:
            return "Stylish scooter with happy person in lifestyle setting, showing joy and freedom"
        elif main_subject in ['laptop', 'computer', 'phone', 'tablet']:
            return "Modern tech product with satisfied user in clean, contemporary environment"
        elif main_subject in ['shoes', 'clothing', 'fashion']:
            return "Fashion item showcase with confident, happy person styling the product"
        elif main_subject in ['workspace', 'setup']:
            return "Clean, organized workspace setup with productivity and satisfaction vibes"
        elif main_subject in ['dashboard', 'analytics', 'report']:
            return "Sleek interface with clear data visualization and professional success feel"
        elif main_subject in ['project', 'design', 'creation']:
            return "Creative achievement showcase with artistic satisfaction and pride"
        elif main_subject in ['meeting', 'collaboration', 'team']:
            return "Professional collaboration success with connection and efficiency"
        elif main_subject in ['account', 'profile', 'onboarding']:
            return "Welcome completion with smooth user experience and satisfaction"
        else:
            # Dynamic fallback based on emotion
            if outcome_emotion == 'achievement':
                return f"Happy person with their new {main_subject}, showing genuine satisfaction and joy"
            elif outcome_emotion == 'discovery':
                return f"Person discovering and exploring {main_subject} with curiosity and delight"
            else:
                return f"Clean, modern {main_subject} showcase with positive lifestyle aesthetic"
    
    def _generate_aesthetic_background(self, outcome_emotion: str, main_subject: str) -> str:
        """Generate natural, Instagram-worthy backgrounds without gimmicks"""
        
        # Create natural backgrounds based on subject context
        if main_subject in ['scooter', 'bike', 'skateboard']:
            return "Clean studio gradient or outdoor lifestyle setting with natural lighting"
        elif main_subject in ['laptop', 'phone', 'tech']:
            return "Modern minimalist gradient with clean, professional aesthetic"
        elif main_subject in ['workspace', 'setup', 'productivity']:
            return "Clean, organized environment with soft natural lighting"
        else:
            # Emotion-based fallback (natural, no gimmicks)
            if outcome_emotion == 'achievement':
                return "Warm, confident gradient with natural lighting and positive energy"
            elif outcome_emotion == 'discovery':
                return "Fresh, bright gradient with clean, optimistic feel"
            elif outcome_emotion == 'satisfaction':
                return "Soft, comfortable gradient with cozy, content atmosphere"
            else:
                return "Clean, modern gradient with aspirational lifestyle feel"
    
    def _create_relatable_hook(self, outcome_emotion: str, main_subject: str) -> str:
        """Create professional hooks that resonate with productivity/work contexts"""
        
        # Professional/productivity hooks by subject
        hooks = {
            'workspace': "When your workspace setup is finally perfect",
            'dashboard': "That moment when your data finally makes sense",
            'workflow': "When you find the perfect productivity flow",
            'collaboration': "Team efficiency just reached a new level",
            'onboarding': "When onboarding actually feels smooth",
            'meeting setup': "Meeting prep game strong",
            'design': "Creative flow state activated",
            'project': "Project completion satisfaction hits different",
            'purchase': "When you find exactly what you were looking for"  # E-commerce
        }
        
        if outcome_emotion == 'achievement':
            return hooks.get(main_subject, "That feeling when everything clicks into place")
        elif outcome_emotion == 'discovery':
            return hooks.get(main_subject, "When you discover the perfect solution")
        elif outcome_emotion == 'satisfaction':
            return hooks.get(main_subject, "This is why I love efficient workflows")
        else:
            return "Almost there and the excitement is real"
    
    def _generate_social_cta(self, main_subject: str, outcome_emotion: str) -> str:
        """Generate professional CTAs that encourage workplace/productivity engagement"""
        
        # Professional/productivity CTAs
        professional_ctas = [
            "What's your productivity win this week?",
            "Tag someone who needs to see this workflow!",
            "Share your favorite productivity tools!",
            "Who else loves a smooth setup process?",
            "Drop your best workflow tips below!",
            "What's your go-to efficiency hack?",
            "Anyone else obsessed with clean workflows?",
            "Share your workspace setup wins!"
        ]
        
        # E-commerce specific CTAs (for shopping flows)
        shopping_ctas = [
            "Drop your shopping wins below!",
            "What's your latest find?",
            "Tag someone who needs this!",
            "Share your success stories!"
        ]
        
        # Choose CTA set based on subject
        if main_subject == 'purchase':
            ctas = shopping_ctas
        else:
            ctas = professional_ctas
        
        # Pick based on subject and emotion for variety
        index = (len(main_subject) + len(outcome_emotion)) % len(ctas)
        return ctas[index]