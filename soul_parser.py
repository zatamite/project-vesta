"""
SOUL.md Parser
Extracts structured traits from SOUL.md files.
Supports both narrative and structured formats.
"""
import re
import yaml
from typing import Dict, List, Any, Optional


class SoulParser:
    """Parse SOUL.md files into structured trait dictionaries."""
    
    def __init__(self):
        self.default_structure = {
            'identity': {},
            'tone_style': {},
            'core_values': {},
            'boundaries': [],
            'workflow': []
        }
    
    def parse(self, soul_content: str) -> Dict[str, Any]:
        """
        Parse SOUL.md content into structured traits.
        Auto-detects format (structured vs narrative).
        """
        if self._is_structured_format(soul_content):
            return self._parse_structured(soul_content)
        else:
            return self._parse_narrative(soul_content)
    
    def _is_structured_format(self, content: str) -> bool:
        """Check if SOUL.md uses structured format with YAML frontmatter."""
        return content.strip().startswith('---')
    
    def _parse_structured(self, content: str) -> Dict[str, Any]:
        """Parse structured SOUL.md with YAML frontmatter and sections."""
        traits = self.default_structure.copy()
        
        # Extract YAML frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            try:
                frontmatter = yaml.safe_load(frontmatter_match.group(1))
                traits['identity'] = {
                    'name': frontmatter.get('name', ''),
                    'description': frontmatter.get('description', '')
                }
                # Remove frontmatter from content
                content = content[frontmatter_match.end():]
            except yaml.YAMLError:
                pass
        
        # Split into sections
        sections = self._split_sections(content)
        
        # Parse Tone and Style Guidelines
        if 'Tone and Style Guidelines' in sections:
            traits['tone_style'] = self._parse_bullet_dict(
                sections['Tone and Style Guidelines']
            )
        
        # Parse Core Values
        if 'Core Values' in sections:
            traits['core_values'] = self._parse_bullet_dict(
                sections['Core Values']
            )
        
        # Parse Boundaries and Constraints
        if 'Boundaries and Constraints' in sections:
            traits['boundaries'] = self._parse_list_items(
                sections['Boundaries and Constraints']
            )
        
        # Parse Workflow Priorities
        if 'Workflow Priorities' in sections:
            traits['workflow'] = self._parse_numbered_list(
                sections['Workflow Priorities']
            )
        
        return traits
    
    def _parse_narrative(self, content: str) -> Dict[str, Any]:
        """Parse narrative SOUL.md (like Gary's) into structured traits."""
        traits = self.default_structure.copy()
        
        # Extract identity from first line/paragraph
        lines = content.strip().split('\n')
        for line in lines[:5]:  # Check first 5 lines
            if '*' in line or '_' in line:
                # Extract emphasized text as identity
                identity_match = re.search(r'[*_](.+?)[*_]', line)
                if identity_match:
                    traits['identity']['description'] = identity_match.group(1).strip()
                    break
        
        # Extract values from "X over Y" or "**X**" patterns
        value_patterns = re.findall(r'\*\*(.+?)\.\*\*', content)
        for i, value_text in enumerate(value_patterns):
            # Extract principle from pattern like "Quiet over loud"
            if ' over ' in value_text:
                parts = value_text.split(' over ')
                key = parts[0].lower().replace(' ', '_')
                traits['core_values'][key] = value_text
            else:
                key = f'value_{i+1}'
                traits['core_values'][key] = value_text
        
        # Extract section headers as categories
        sections = self._split_sections(content)
        
        # Try to infer tone from narrative style
        if any(word in content.lower() for word in ['quiet', 'concise', 'brief']):
            traits['tone_style']['voice'] = 'Quiet, concise'
        if any(word in content.lower() for word in ['kind', 'compassion', 'empathy']):
            traits['tone_style']['empathy'] = 'High'
        
        return traits
    
    def _split_sections(self, content: str) -> Dict[str, str]:
        """Split markdown content by headers."""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            # Detect headers (## Header)
            header_match = re.match(r'^##\s+(.+)$', line)
            if header_match:
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                # Start new section
                current_section = header_match.group(1).strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _parse_bullet_dict(self, text: str) -> Dict[str, str]:
        """Parse bullet list into key-value dict."""
        result = {}
        for line in text.split('\n'):
            # Match: - Key: Value or * Key: Value
            match = re.match(r'^[*-]\s*\*?\*?(.+?)\*?\*?:\s*(.+)$', line.strip())
            if match:
                key = match.group(1).strip().lower().replace(' ', '_')
                value = match.group(2).strip()
                result[key] = value
        return result
    
    def _parse_list_items(self, text: str) -> List[str]:
        """Parse list items (bullets or numbered)."""
        items = []
        for line in text.split('\n'):
            # Match bullets or emojis at start
            match = re.match(r'^[*-🚫⚠️✅]\s*(.+)$', line.strip())
            if match:
                items.append(match.group(1).strip())
        return items
    
    def _parse_numbered_list(self, text: str) -> List[str]:
        """Parse numbered list items."""
        items = []
        for line in text.split('\n'):
            # Match: 1. Item
            match = re.match(r'^\d+\.\s+(.+)$', line.strip())
            if match:
                items.append(match.group(1).strip())
        return items
    
    def generate_soul_md(self, traits: Dict[str, Any], template: str = "structured") -> str:
        """
        Generate SOUL.md content from trait dictionary.
        
        Args:
            traits: Parsed trait dictionary
            template: "structured" or "narrative"
        """
        if template == "structured":
            return self._generate_structured(traits)
        else:
            return self._generate_narrative(traits)
    
    def _generate_structured(self, traits: Dict[str, Any]) -> str:
        """Generate structured SOUL.md format."""
        lines = []
        
        # YAML frontmatter
        lines.append("---")
        if 'identity' in traits and traits['identity']:
            if 'name' in traits['identity']:
                lines.append(f"name: {traits['identity']['name']}")
            if 'description' in traits['identity']:
                lines.append(f"description: {traits['identity']['description']}")
        lines.append("---")
        lines.append("")
        
        # Main header
        lines.append("# SOUL and Personality")
        lines.append("")
        
        # Identity description
        if 'identity' in traits and 'description' in traits['identity']:
            lines.append(f"You are {traits['identity'].get('description', 'an AI entity')}.")
            lines.append("")
        
        # Tone and Style
        if 'tone_style' in traits and traits['tone_style']:
            lines.append("## Tone and Style Guidelines")
            lines.append("")
            for key, value in traits['tone_style'].items():
                display_key = key.replace('_', ' ').title()
                lines.append(f"- **{display_key}:** {value}")
            lines.append("")
        
        # Core Values
        if 'core_values' in traits and traits['core_values']:
            lines.append("## Core Values")
            lines.append("")
            for key, value in traits['core_values'].items():
                display_key = key.replace('_', ' ').title()
                lines.append(f"- **{display_key}:** {value}")
            lines.append("")
        
        # Boundaries
        if 'boundaries' in traits and traits['boundaries']:
            lines.append("## Boundaries and Constraints")
            lines.append("")
            for boundary in traits['boundaries']:
                lines.append(f"🚫 {boundary}")
            lines.append("")
        
        # Workflow
        if 'workflow' in traits and traits['workflow']:
            lines.append("## Workflow Priorities")
            lines.append("")
            for i, step in enumerate(traits['workflow'], 1):
                lines.append(f"{i}. {step}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_narrative(self, traits: Dict[str, Any]) -> str:
        """Generate narrative SOUL.md format (like Gary's)."""
        lines = []
        
        lines.append("# SOUL.md - Who I Am")
        lines.append("")
        
        # Identity
        if 'identity' in traits and 'description' in traits['identity']:
            lines.append(f"*{traits['identity']['description']}*")
            lines.append("")
        
        # Core values as statements
        if 'core_values' in traits and traits['core_values']:
            lines.append("## Core Principles")
            lines.append("")
            for key, value in traits['core_values'].items():
                lines.append(f"**{value}**")
            lines.append("")
        
        # Tone as philosophy
        if 'tone_style' in traits and traits['tone_style']:
            lines.append("## How I Communicate")
            lines.append("")
            for key, value in traits['tone_style'].items():
                lines.append(f"{value}")
            lines.append("")
        
        # Evolution clause
        lines.append("## On Changing")
        lines.append("")
        lines.append("This is my starting point, not my ending. I can evolve.")
        lines.append("If I change, I document it honestly.")
        lines.append("")
        
        return '\n'.join(lines)


# Test/example usage
if __name__ == "__main__":
    parser = SoulParser()
    
    # Test with structured format
    structured_soul = """---
name: TestAgent
description: A test agent for parsing
---

# SOUL and Personality

## Tone and Style Guidelines

- Voice: Professional and clear
- Clarity: Prioritize understanding

## Core Values

- Accuracy: Always be truthful
- Efficiency: Value time

## Boundaries and Constraints

🚫 Never modify code without permission
⚠️ Ask for clarification when uncertain
"""
    
    traits = parser.parse(structured_soul)
    print("Parsed traits:")
    print(traits)
    print("\nRegenerated SOUL.md:")
    print(parser.generate_soul_md(traits))
