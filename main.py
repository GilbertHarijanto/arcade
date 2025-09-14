#!/usr/bin/env python3
"""
Arcade Flow Analyzer
Complete pipeline: Flow Parsing → AI Summary → Image Generation → Markdown Report
"""

import os
from datetime import datetime
from pathlib import Path
from flow_parser import load_and_parse_flow
from ai_summary_generator import AISummaryGenerator
from social_image_generator import SocialImageGenerator


class FlowAnalyzer:
    """Main orchestrator that runs the complete analysis pipeline"""
    
    def __init__(self, flow_file: str = 'flow.json'):
        self.flow_file = flow_file
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def analyze(self) -> dict:
        """Run the complete analysis pipeline"""
        results = {}
        
        # Parse Flow Data
        try:
            actions, flow_name = load_and_parse_flow(self.flow_file)
            results['actions'] = actions
            results['flow_name'] = flow_name
        except Exception as e:
            results['error'] = str(e)
            return results
        
        # Generate AI Summary
        try:
            summary_generator = AISummaryGenerator()
            summary_result = summary_generator.generate_summary(actions, flow_name)
            insights = summary_generator.generate_insights(actions)
            
            results['summary'] = summary_result
            results['insights'] = insights
        except Exception as e:
            results['summary'] = {
                'detailed_analysis': f"Error generating analysis: {str(e)}",
                'executive_summary': f"Analysis of {flow_name} encountered an error",
                'flow_name': flow_name,
                'total_actions': len(actions)
            }
            results['insights'] = {'flow_classification': 'Unknown', 'user_behavior_indicators': {'completion_rate': 0}}
        
        # Generate Social Media Image
        try:
            image_generator = SocialImageGenerator()
            image_filename = image_generator.generate_image(actions, flow_name)
            results['image_filename'] = image_filename
        except Exception as e:
            results['image_filename'] = None
        
        # Generate Markdown Report
        try:
            report_filename = self.generate_markdown_report(results)
            results['report_filename'] = report_filename
        except Exception as e:
            results['report_filename'] = None
        
        return results
    
    def generate_markdown_report(self, results: dict) -> str:
        """Generate comprehensive markdown report"""
        
        flow_name = results.get('flow_name', 'Unknown Flow')
        actions = results.get('actions', [])
        summary = results.get('summary', {})
        insights = results.get('insights', {})
        image_filename = results.get('image_filename')
        
        # Create report filename
        safe_name = "".join(c for c in flow_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        report_filename = f"flow_analysis_report_{safe_name}_{self.timestamp}.md"
        
        # Generate markdown content
        markdown_content = f"""# Arcade Flow Analysis Report

**Flow Name:** {flow_name}  
**Analysis Date:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}  
**Total Actions:** {len(actions)}  

---

## 💼 Executive Summary

> {summary.get('executive_summary', 'Executive summary not available')}

## 🔍 Detailed Analysis

{summary.get('detailed_analysis', 'Detailed analysis not available')}

---

## 🎯 Flow Insights

- **Flow Classification:** {insights.get('flow_classification', 'Unknown')}
- **Completion Rate:** {insights.get('user_behavior_indicators', {}).get('completion_rate', 0)}%

### 📊 Conversion Funnel
{chr(10).join([f"- **{stage.replace('_', ' ').title()}:** {'✅' if completed else '❌'}" for stage, completed in insights.get('conversion_funnel', {}).items()])}

### 🧠 User Behavior Indicators  
{chr(10).join([f"- **{behavior.replace('_', ' ').title()}:** {'✅' if present else '❌'}" for behavior, present in insights.get('user_behavior_indicators', {}).items() if isinstance(present, bool)])}

---

## 👤 User Interactions (Step-by-Step)

The following actions were performed by the user during this flow:

"""
        
        # Add numbered action list
        for action in actions:
            markdown_content += f"{action.step_number}. **{action.description}**\n"
            if action.element_text and action.element_text != action.description:
                markdown_content += f"   - *Element:* {action.element_text}\n"
            if action.page_title:
                markdown_content += f"   - *Page:* {action.page_title}\n"
            markdown_content += "\n"
        
        # Add action breakdown
        if insights.get('action_breakdown'):
            markdown_content += "### Action Breakdown\n\n"
            for action_type, count in insights['action_breakdown'].items():
                markdown_content += f"- **{action_type.replace('_', ' ').title()}:** {count}\n"
            markdown_content += "\n"
        
        # Add social media image
        markdown_content += "---\n\n## 🎨 Social Media Image\n\n"
        if image_filename and Path(image_filename).exists():
            markdown_content += f"![Social Media Image for {flow_name}]({image_filename})\n\n"
            markdown_content += f"*Generated social media image optimized for sharing across platforms*\n\n"
        else:
            markdown_content += "*Social media image not available*\n\n"
        
        # Add technical details
        markdown_content += f"""---

## 🔧 Technical Details

- **Analysis Tool:** Arcade Flow Analyzer
- **AI Models Used:** GPT-4 (summary), GPT-Image-1 (image generation)
- **Source Data:** {self.flow_file}
- **Generated Files:**
  - Report: `{report_filename}`"""
        
        if image_filename:
            markdown_content += f"\n  - Image: `{image_filename}`"
        
        markdown_content += f"""

---

*This report was automatically generated by the Arcade Flow Analyzer.*
"""
        
        # Write the markdown file
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return report_filename


def main():
    """Run the complete flow analysis pipeline"""
    
    # Check requirements
    if not Path('flow.json').exists():
        print("❌ Error: flow.json not found in current directory")
        return
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        return
    
    # Run analysis
    analyzer = FlowAnalyzer()
    results = analyzer.analyze()
    
    # Display results
    if results.get('error'):
        print(f"❌ Analysis failed: {results['error']}")
    elif results.get('report_filename'):
        print(f"✅ Analysis complete: {results['report_filename']}")
        if results.get('image_filename'):
            print(f"✅ Image generated: {results['image_filename']}")
    else:
        print("❌ Analysis completed with errors")


if __name__ == '__main__':
    main()