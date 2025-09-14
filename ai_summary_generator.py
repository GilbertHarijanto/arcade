#!/usr/bin/env python3
"""
AI Summary Generator
Creates insightful, actionable summaries of user flows using GPT
"""

import os
from typing import List
from openai import OpenAI
import dotenv
from flow_parser import UserAction

dotenv.load_dotenv()


class AISummaryGenerator:
    """Generates insightful, actionable summaries using GPT"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
    
    def generate_summary(self, actions: List[UserAction], flow_name: str) -> dict:
        """Generate insightful, actionable summary from user actions"""
        
        action_context = self._build_action_context(actions)
        
        system_prompt = """You are a UX/UI analyst and business intelligence expert. Your job is to analyze user flow data and provide actionable insights that help product teams improve their applications.

When analyzing user flows, focus on:
1. USER BEHAVIOR PATTERNS - What the user's actions reveal about their mindset and preferences
2. UX/UI INSIGHTS - How the interface design influenced user behavior
3. BUSINESS INTELLIGENCE - Conversion patterns, friction points, success indicators
4. ACTIONABLE RECOMMENDATIONS - Specific suggestions for improvement

Write your analysis in a professional, insightful tone that provides value to product managers, UX designers, and developers. Avoid simply retelling what happened - instead, explain WHY it happened and what it means."""

        user_prompt = f"""Analyze this user flow: "{flow_name}"

DETAILED USER ACTIONS:
{action_context}

Provide an insightful analysis covering:

1. **User Journey Analysis**: What was the user's primary goal and how effectively did they achieve it?

2. **Behavioral Insights**: What do the user's actions reveal about their decision-making process, preferences, and pain points?

3. **UX/UI Performance**: How well did the interface design support the user's goals? Identify successful design elements and potential friction points.

4. **Business Impact**: What does this flow tell us about conversion potential, user engagement, and business outcomes?

5. **Key Takeaways**: 3-4 specific, actionable insights that product teams should consider.

Keep the analysis concise but insightful (3-4 paragraphs total). Focus on insights that would be valuable to product teams."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            detailed_analysis = response.choices[0].message.content.strip()
            
            # Generate executive summary
            exec_summary_prompt = f"""Based on this user flow analysis for "{flow_name}":

{detailed_analysis}

Create a concise executive summary (1-2 sentences) that captures the most important business outcome and user behavior insight."""

            exec_response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a business analyst creating executive summaries."},
                    {"role": "user", "content": exec_summary_prompt}
                ],
                max_tokens=100,
                temperature=0.2
            )
            
            executive_summary = exec_response.choices[0].message.content.strip()
            
            return {
                "detailed_analysis": detailed_analysis,
                "executive_summary": executive_summary,
                "flow_name": flow_name,
                "total_actions": len(actions)
            }
            
        except Exception as e:
            return {
                "detailed_analysis": f"Error generating analysis: {str(e)}",
                "executive_summary": f"Analysis of {flow_name} encountered an error",
                "flow_name": flow_name,
                "total_actions": len(actions)
            }
    
    def _build_action_context(self, actions: List[UserAction]) -> str:
        """Build rich context for each action to help GPT understand user behavior"""
        context_lines = []
        
        for action in actions:
            context = f"{action.step_number}. {action.description}"
            
            # Add behavioral context clues
            if action.action_type == 'search':
                context += " [INTENT: Product discovery initiated]"
            elif action.action_type == 'type':
                context += f" [SEARCH QUERY: '{action.element_text}' - specific product interest]"
            elif action.action_type == 'select_product':
                context += " [CONVERSION: Moved from browse to product focus]"
            elif action.action_type == 'select_option':
                context += " [DECISION: Made customization choice]"
            elif action.action_type == 'browse_options':
                context += " [EXPLORATION: Comparing alternatives before deciding]"
            elif action.action_type == 'add_to_cart':
                context += " [CONVERSION: Purchase intent confirmed]"
            elif action.action_type == 'decline_option':
                context += " [PRICE SENSITIVITY: Rejected additional cost]"
            elif action.action_type == 'navigate_cart':
                context += " [VERIFICATION: Confirming purchase decision]"
            elif action.action_type == 'complete':
                context += " [SUCCESS: Flow completed successfully]"
                
            context_lines.append(context)
        
        return "\n".join(context_lines)
    
    def generate_insights(self, actions: List[UserAction]) -> dict:
        """Generate enhanced insights with UX/business focus"""
        
        action_types = {}
        for action in actions:
            action_types[action.action_type] = action_types.get(action.action_type, 0) + 1
        
        # Pattern detection
        has_search = any(action.action_type == 'search' for action in actions)
        has_customization = any(action.action_type in ['select_option', 'browse_options'] for action in actions)
        has_purchase = any(action.action_type == 'add_to_cart' for action in actions)
        completed = any(action.action_type == 'complete' for action in actions)
        declined_upsell = any(action.action_type == 'decline_option' for action in actions)
        
        # Calculate conversion metrics
        search_to_product = has_search and any(action.action_type == 'select_product' for action in actions)
        product_to_cart = any(action.action_type == 'select_product' for action in actions) and has_purchase
        
        insights = {
            "action_breakdown": action_types,
            "conversion_funnel": {
                "search_initiated": has_search,
                "product_selected": search_to_product,
                "customization_explored": has_customization,
                "cart_conversion": product_to_cart,
                "flow_completed": completed
            },
            "user_behavior_indicators": {
                "price_conscious": declined_upsell,
                "exploration_oriented": has_customization,
                "goal_oriented": search_to_product and product_to_cart,
                "completion_rate": 100 if completed else 0
            },
            "flow_classification": self._classify_flow_type(has_search, has_customization, has_purchase, completed)
        }
        
        return insights
    
    def _classify_flow_type(self, has_search: bool, has_customization: bool, has_purchase: bool, completed: bool) -> str:
        """Enhanced flow classification with business context"""
        if completed and has_purchase:
            if has_customization:
                return "Successful E-commerce Conversion with Product Customization"
            else:
                return "Successful E-commerce Conversion"
        elif has_purchase:
            return "E-commerce Conversion (Incomplete)"
        elif has_search and has_customization:
            return "Product Research with Customization Exploration"
        elif has_search:
            return "Product Discovery Flow"
        else:
            return "General Navigation Flow"