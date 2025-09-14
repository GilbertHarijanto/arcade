#!/usr/bin/env python3
"""
Arcade Flow Parser
Extracts meaningful user actions from flow.json data
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class UserAction:
    """Represents a single user action extracted from the flow"""
    step_number: int
    action_type: str  # 'click', 'type', 'scroll', 'navigate'
    description: str  # Human-readable description
    element_text: Optional[str] = None
    element_type: Optional[str] = None
    page_url: Optional[str] = None
    page_title: Optional[str] = None
    timestamp: Optional[int] = None
    css_selector: Optional[str] = None
    hotspot_label: Optional[str] = None
    raw_data: Optional[Dict] = None


class FlowParser:
    """Parses Arcade flow.json files and extracts user actions"""
    
    def __init__(self, flow_data: Dict[str, Any]):
        self.flow_data = flow_data
        self.actions: List[UserAction] = []
        self.flow_name = flow_data.get('name', 'Unknown Flow')
        
    def parse(self) -> List[UserAction]:
        """Main parsing method that extracts all user actions"""
        print(f"Parsing flow: {self.flow_name}")
        
        # Get steps and captured events
        steps = self.flow_data.get('steps', [])
        captured_events = self.flow_data.get('capturedEvents', [])
        
        # Create a mapping of click IDs to captured events
        event_map = {event.get('clickId'): event for event in captured_events if event.get('clickId')}
        
        step_number = 0
        for step in steps:
            step_type = step.get('type')
            
            if step_type == 'CHAPTER':
                # Chapter steps are introductory/concluding screens
                action = self._parse_chapter_step(step, step_number)
                if action:
                    self.actions.append(action)
                    step_number += 1
                    
            elif step_type == 'IMAGE':
                # Image steps contain the actual user interactions
                action = self._parse_image_step(step, event_map, step_number)
                if action:
                    self.actions.append(action)
                    step_number += 1
                    
            elif step_type == 'VIDEO':
                # Video steps show transitions - we can note them but they're not user actions
                continue
                
        return self.actions
    
    def _parse_chapter_step(self, step: Dict, step_number: int) -> Optional[UserAction]:
        """Parse a CHAPTER step (intro/outro screens)"""
        title = step.get('title', '')
        subtitle = step.get('subtitle', '')
        
        if 'thank you' in title.lower() or 'conclusion' in title.lower():
            return UserAction(
                step_number=step_number,
                action_type='navigate',
                description=f"Reached end screen: {title}",
                raw_data=step
            )
        else:
            return UserAction(
                step_number=step_number,
                action_type='navigate',
                description=f"Started flow: {title}",
                raw_data=step
            )
    
    def _parse_image_step(self, step: Dict, event_map: Dict, step_number: int) -> Optional[UserAction]:
        """Parse an IMAGE step that contains user interaction data"""
        step_id = step.get('id')
        page_context = step.get('pageContext', {})
        click_context = step.get('clickContext', {})
        hotspots = step.get('hotspots', [])
        
        # Get page information
        page_url = page_context.get('url', '')
        page_title = page_context.get('title', '')
        
        # Get click information
        element_text = click_context.get('text', '')
        element_type = click_context.get('elementType', '')
        css_selector = click_context.get('cssSelector', '')
        
        # Get human-readable description from hotspot
        hotspot_label = ''
        if hotspots and len(hotspots) > 0:
            hotspot_label = hotspots[0].get('label', '')
        
        # Get timing information from captured events
        timestamp = None
        if step_id in event_map:
            timestamp = event_map[step_id].get('timeMs')
        
        # Determine action type and create description
        action_type, description = self._determine_action_type_and_description(
            element_text, element_type, hotspot_label, page_url
        )
        
        return UserAction(
            step_number=step_number,
            action_type=action_type,
            description=description,
            element_text=element_text,
            element_type=element_type,
            page_url=page_url,
            page_title=page_title,
            timestamp=timestamp,
            css_selector=css_selector,
            hotspot_label=hotspot_label,
            raw_data=step
        )
    
    def _determine_action_type_and_description(self, element_text: str, element_type: str, 
                                             hotspot_label: str, page_url: str) -> tuple[str, str]:
        """Determine the action type and create a human-readable description"""
        
        # Use hotspot label as primary description source (it's human-written)
        if hotspot_label:
            base_description = hotspot_label
        else:
            base_description = f"Clicked on {element_text}" if element_text else "Performed action"
        
        # Determine action type based on element and context
        if element_type == 'button':
            if 'cart' in element_text.lower():
                return 'add_to_cart', f"Added item to cart by clicking '{element_text}'"
            elif 'search' in element_text.lower():
                return 'search', f"Initiated search by clicking '{element_text}'"
            else:
                return 'click', f"Clicked button '{element_text}'"
                
        elif element_type == 'image':
            if 'scooter' in element_text.lower():
                return 'select_product', f"Selected product: {element_text}"
            elif element_text in ['Blue', 'Pink', 'Red', 'Black']:  # Color selection
                return 'select_option', f"Selected color option: {element_text}"
            else:
                return 'click', f"Clicked image: {element_text}"
                
        elif element_type == 'other' and 'search' in element_text.lower():
            return 'search', "Clicked on search bar to start searching"
            
        elif element_type == 'link':
            if 'cart' in page_url or element_text == '1':  # Cart icon with item count
                return 'navigate', "Navigated to shopping cart"
            else:
                return 'navigate', f"Clicked link: {element_text}"
        
        # Default case
        return 'click', base_description
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics about the parsed actions"""
        action_types = {}
        for action in self.actions:
            action_type = action.action_type
            action_types[action_type] = action_types.get(action_type, 0) + 1
        
        return {
            'flow_name': self.flow_name,
            'total_actions': len(self.actions),
            'action_types': action_types,
            'first_action_time': self.actions[0].timestamp if self.actions else None,
            'last_action_time': self.actions[-1].timestamp if self.actions else None
        }
    
    def to_json(self) -> str:
        """Export actions to JSON format"""
        return json.dumps([asdict(action) for action in self.actions], indent=2)
    
    def to_markdown(self) -> str:
        """Export actions to markdown format"""
        lines = [f"# User Actions for {self.flow_name}\n"]
        
        for i, action in enumerate(self.actions, 1):
            lines.append(f"## Step {i}: {action.description}")
            lines.append(f"- **Action Type:** {action.action_type}")
            
            if action.page_url:
                lines.append(f"- **Page:** {action.page_title} ({action.page_url})")
            
            if action.element_text:
                lines.append(f"- **Element:** {action.element_text} ({action.element_type})")
            
            if action.timestamp:
                dt = datetime.fromtimestamp(action.timestamp / 1000)
                lines.append(f"- **Time:** {dt.strftime('%H:%M:%S')}")
            
            lines.append("")  # Empty line between actions
        
        return "\n".join(lines)


def main():
    """Test the parser with the flow.json file"""
    flow_file = Path(__file__).parent / 'flow.json'
    
    if not flow_file.exists():
        print(f"Error: {flow_file} not found")
        return
    
    # Load and parse the flow data
    with open(flow_file, 'r') as f:
        flow_data = json.load(f)
    
    parser = FlowParser(flow_data)
    actions = parser.parse()
    
    # Print summary
    stats = parser.get_summary_stats()
    print(f"\n=== PARSING SUMMARY ===")
    print(f"Flow Name: {stats['flow_name']}")
    print(f"Total Actions: {stats['total_actions']}")
    print(f"Action Types: {stats['action_types']}")
    
    # Print actions
    print(f"\n=== EXTRACTED ACTIONS ===")
    for i, action in enumerate(actions, 1):
        print(f"{i}. {action.description}")
        if action.page_url:
            print(f"   Page: {action.page_title}")
        if action.element_text and action.element_type:
            print(f"   Element: {action.element_text} ({action.element_type})")
        print()
    
    # Save results
    output_file = Path(__file__).parent / 'parsed_actions.json'
    with open(output_file, 'w') as f:
        f.write(parser.to_json())
    print(f"Results saved to {output_file}")
    
    # Save markdown
    md_file = Path(__file__).parent / 'parsed_actions.md'
    with open(md_file, 'w') as f:
        f.write(parser.to_markdown())
    print(f"Markdown report saved to {md_file}")


if __name__ == '__main__':
    main()
