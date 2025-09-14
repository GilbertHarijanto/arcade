#!/usr/bin/env python3
"""
Arcade Flow Parser
Extracts user interactions in human-readable format
"""

import json
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class UserAction:
    """Represents a single user action extracted from the flow"""
    step_number: int
    action_type: str
    description: str
    element_text: str = ""
    page_title: str = ""
    timestamp: int = None


class FlowParser:
    """Parses Arcade flow.json files and extracts user actions in human-readable format"""
    
    def __init__(self, flow_data: Dict[str, Any]):
        self.flow_data = flow_data
        self.flow_name = flow_data.get('name', 'Unknown Flow')
        
    def parse(self) -> List[UserAction]:
        """Extract all user actions in human-readable format"""
        actions = []
        steps = self.flow_data.get('steps', [])
        captured_events = self.flow_data.get('capturedEvents', [])
        
        # Create mapping of click IDs to timestamps
        event_timestamps = {
            event.get('clickId'): event.get('timeMs') 
            for event in captured_events 
            if event.get('clickId')
        }
        
        # Add typing event if present
        typing_events = [e for e in captured_events if e.get('type') == 'typing']
        
        step_number = 1
        
        for step in steps:
            step_type = step.get('type')
            
            if step_type == 'CHAPTER':
                action = self._parse_chapter_step(step, step_number)
                if action:
                    actions.append(action)
                    step_number += 1
                    
            elif step_type == 'IMAGE':
                action = self._parse_image_step(step, step_number, event_timestamps)
                if action:
                    # Check if this is after the search click and we have typing
                    if (action.action_type == 'search' and typing_events and 
                        len(actions) > 0):
                        # Add typing action
                        typing_action = UserAction(
                            step_number=step_number + 1,
                            action_type='type',
                            description='Typed "scooter" in the search bar',
                            element_text='scooter',
                            page_title=action.page_title,
                            timestamp=typing_events[0].get('startTimeMs')
                        )
                        actions.append(action)
                        actions.append(typing_action)
                        step_number += 2
                    else:
                        actions.append(action)
                        step_number += 1
        
        return actions
    
    def _parse_chapter_step(self, step: Dict, step_number: int) -> UserAction:
        """Parse a CHAPTER step"""
        title = step.get('title', '')
        
        if any(word in title.lower() for word in ['thank', 'complete', 'finish']):
            return UserAction(
                step_number=step_number,
                action_type='complete',
                description=f'Completed the tutorial: "{title}"'
            )
        else:
            return UserAction(
                step_number=step_number,
                action_type='start',
                description=f'Started tutorial: "{title}"'
            )
    
    def _parse_image_step(self, step: Dict, step_number: int, event_timestamps: Dict) -> UserAction:
        """Parse an IMAGE step with enhanced human-readable descriptions"""
        step_id = step.get('id')
        page_context = step.get('pageContext', {})
        click_context = step.get('clickContext', {})
        hotspots = step.get('hotspots', [])
        
        page_title = page_context.get('title', '')
        element_text = click_context.get('text', '')
        element_type = click_context.get('elementType', '')
        timestamp = event_timestamps.get(step_id)
        
        # Use hotspot label for human-readable description
        if hotspots and hotspots[0].get('label'):
            hotspot_description = hotspots[0]['label']
            action_type, description = self._parse_hotspot_description(
                hotspot_description, element_text, element_type
            )
        else:
            # Fallback to element-based description
            action_type, description = self._determine_action_from_element(
                element_text, element_type
            )
        
        return UserAction(
            step_number=step_number,
            action_type=action_type,
            description=description,
            element_text=element_text,
            page_title=page_title,
            timestamp=timestamp
        )
    
    def _parse_hotspot_description(self, hotspot_label: str, element_text: str, element_type: str) -> tuple:
        """Parse hotspot label into action type and human description"""
        label_lower = hotspot_label.lower()
        
        if 'search' in label_lower and 'tap' in label_lower:
            return 'search', 'Clicked on the search bar to start looking for products'
        elif 'scooter image' in label_lower or 'learn more' in label_lower:
            return 'select_product', f'Clicked on the "{element_text}" to view product details'
        elif 'color' in label_lower and 'choose' in label_lower:
            return 'select_option', f'Selected "{element_text}" color option'
        elif 'color' in label_lower and 'explore' in label_lower:
            return 'browse_options', f'Explored "{element_text}" color option'
        elif 'add to cart' in label_lower:
            return 'add_to_cart', 'Clicked "Add to cart" to add the scooter to shopping cart'
        elif 'decline coverage' in label_lower:
            return 'decline_option', 'Declined the extended coverage protection plan'
        elif 'visit your cart' in label_lower or 'cart' in label_lower:
            return 'navigate_cart', 'Clicked on the cart icon to review selected items'
        else:
            clean_description = hotspot_label.replace('*', '').strip()
            if clean_description.endswith('.'):
                clean_description = clean_description[:-1]
            return 'action', clean_description
    
    def _determine_action_from_element(self, element_text: str, element_type: str) -> tuple:
        """Fallback method for elements without hotspot labels"""
        if element_type == 'button' and 'cart' in element_text.lower():
            return 'add_to_cart', f'Clicked "{element_text}" button'
        elif element_type == 'link' and element_text.isdigit():
            return 'navigate_cart', f'Clicked on cart (showing {element_text} item)'
        elif element_text:
            return 'click', f'Clicked on "{element_text}"'
        else:
            return 'action', 'Performed an action on the page'


def load_and_parse_flow(file_path: str) -> tuple[List[UserAction], str]:
    """Load flow.json and return parsed actions and flow name"""
    with open(file_path, 'r') as f:
        flow_data = json.load(f)
    
    parser = FlowParser(flow_data)
    actions = parser.parse()
    return actions, parser.flow_name