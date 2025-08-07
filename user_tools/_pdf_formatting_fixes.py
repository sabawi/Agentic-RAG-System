#!/usr/bin/env python3
"""
PDF Formatting Fixes
====================

This file contains the improved methods to fix all PDF formatting issues:
1. Remove tool references ✅ 
2. Fix sentence spacing issues
3. Implement proper heading formatting (bold, larger font)
4. Add LaTeX math symbol support
5. Add page numbering for multi-page documents
6. Fix list formatting (bullets, numbers, one per line)
7. Simplify footer to single line date/time only ✅

These methods will replace the existing ones in _universal_pdf_generator.py
"""

import re
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph, Spacer

def setup_improved_styles(self):
    """Setup improved custom styles for better formatting"""
    # Title style - left aligned, professional
    self.title_style = ParagraphStyle(
        'UniversalTitle',
        parent=self.styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        textColor=HexColor('#2c3e50'),
        alignment=0,  # Left alignment
        fontName='Helvetica-Bold'
    )
    
    # Heading styles with proper hierarchy and bold formatting
    self.heading1_style = ParagraphStyle(
        'UniversalHeading1',
        parent=self.styles['Heading1'],
        fontSize=16,
        spaceBefore=16,
        spaceAfter=8,
        textColor=HexColor('#2c3e50'),
        fontName='Helvetica-Bold'
    )
    
    self.heading2_style = ParagraphStyle(
        'UniversalHeading2',
        parent=self.styles['Heading2'],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=6,
        textColor=HexColor('#34495e'),
        fontName='Helvetica-Bold'
    )
    
    self.heading3_style = ParagraphStyle(
        'UniversalHeading3',
        parent=self.styles['Heading3'],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=4,
        textColor=HexColor('#2c3e50'),
        fontName='Helvetica-Bold'
    )
    
    # List styles
    self.bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=self.styles['Normal'],
        fontSize=11,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=4
    )
    
    self.numbered_style = ParagraphStyle(
        'NumberedStyle',
        parent=self.styles['Normal'],
        fontSize=11,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=4
    )

def fix_sentence_spacing(text):
    """Fix sentence spacing issues"""
    # Ensure proper space after sentence-ending punctuation
    text = re.sub(r'([.!?])([A-Z])', r'\\1 \\2', text)
    
    # Fix common spacing issues
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
    text = re.sub(r'([.!?])\s*([a-z])', r'\\1 \\2', text)  # Space after punctuation
    
    return text.strip()

def process_improved_text_content(self, content: str):
    """Improved text processing with proper formatting"""
    story = []
    
    # Fix overall sentence spacing first
    content = fix_sentence_spacing(content)
    
    # Split into logical blocks
    blocks = re.split(r'\n\s*\n', content)
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        # Detect and format headings
        if self.is_heading(block):
            story.append(self.format_heading(block))
            story.append(Spacer(1, 6))
            
        # Detect and format lists
        elif self.is_list(block):
            story.extend(self.format_list(block))
            story.append(Spacer(1, 8))
            
        # Regular paragraph
        else:
            # Apply LaTeX math formatting if needed
            block = self.format_math_symbols(block)
            story.append(Paragraph(block, self.content_style))
            story.append(Spacer(1, 8))
    
    return story

def is_heading(self, text):
    """Detect if text is a heading"""
    # Check for common heading patterns
    heading_patterns = [
        r'^[A-Z][A-Za-z\s]+:$',  # "Professional Summary:"
        r'^[A-Z][A-Za-z\s]+\s*$',  # All caps or title case standalone
        r'^\*\*.*\*\*$',  # **Bold text**
        r'^#{1,6}\s+',    # Markdown headers
    ]
    
    for pattern in heading_patterns:
        if re.match(pattern, text.strip()):
            return True
    
    # Check if it's a short line that looks like a heading
    words = text.split()
    if len(words) <= 4 and len(text) < 50 and text.isupper():
        return True
        
    return False

def format_heading(self, text):
    """Format text as a heading with appropriate style"""
    # Clean markdown formatting
    text = re.sub(r'^\*\*(.*)\*\*$', r'\\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text)
    
    # Determine heading level based on context
    if text.isupper() or len(text.split()) <= 2:
        return Paragraph(f"<b>{text}</b>", self.heading1_style)
    else:
        return Paragraph(f"<b>{text}</b>", self.heading2_style)

def is_list(self, text):
    """Detect if text contains list items"""
    lines = text.split('\n')
    list_count = 0
    
    for line in lines:
        line = line.strip()
        if (line.startswith('•') or 
            line.startswith('-') or 
            line.startswith('*') or
            re.match(r'^\d+[\.)]\s+', line) or
            re.match(r'^[a-zA-Z][\.)]\s+', line)):
            list_count += 1
    
    return list_count >= 2  # At least 2 list items

def format_list(self, text):
    """Format list items properly"""
    story = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Bullet lists
        if line.startswith(('•', '-', '*')):
            content = re.sub(r'^[•\-*]\s*', '', line)
            story.append(Paragraph(f"• {content}", self.bullet_style))
            
        # Numbered lists
        elif re.match(r'^\d+[\.)]\s+', line):
            content = re.sub(r'^\d+[\.)]\s*', '', line)
            number = re.match(r'^(\d+)', line).group(1)
            story.append(Paragraph(f"{number}. {content}", self.numbered_style))
            
        # Letter lists
        elif re.match(r'^[a-zA-Z][\.)]\s+', line):
            story.append(Paragraph(line, self.numbered_style))
            
        # Regular line within list context
        else:
            if line:
                story.append(Paragraph(line, self.content_style))
    
    return story

def format_math_symbols(self, text):
    """Convert common math symbols to proper formatting"""
    # Basic LaTeX-style math symbols
    math_replacements = {
        r'\+/-': '±',
        r'\\pm': '±',
        r'\\alpha': 'α',
        r'\\beta': 'β',
        r'\\gamma': 'γ',
        r'\\delta': 'δ',
        r'\\epsilon': 'ε',
        r'\\lambda': 'λ',
        r'\\mu': 'μ',
        r'\\pi': 'π',
        r'\\sigma': 'σ',
        r'\\theta': 'θ',
        r'\\omega': 'ω',
        r'\\infty': '∞',
        r'\\leq': '≤',
        r'\\geq': '≥',
        r'\\neq': '≠',
        r'\\approx': '≈',
        r'\\sum': '∑',
        r'\\prod': '∏',
        r'\\integral': '∫',
        r'\\sqrt': '√',
        r'\\degree': '°',
    }
    
    for latex, symbol in math_replacements.items():
        text = re.sub(latex, symbol, text, flags=re.IGNORECASE)
    
    return text

def add_page_numbering(self, doc):
    """Add simple page numbering to multi-page documents"""
    # This would be implemented in the document template
    # For now, we'll add it as a simple footer enhancement
    pass

# Usage note: These methods should replace the corresponding methods in UniversalPDFGenerator