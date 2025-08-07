"""
Universal PDF Generator
======================

A comprehensive PDF generation utility that can convert any text content 
to properly formatted, viewable PDF documents using reportlab.

This module provides a foolproof solution for creating real binary PDFs
instead of text files with .pdf extensions.
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
import re
from typing import Dict, List, Optional, Union
import os


class UniversalPDFGenerator:
    """Universal PDF generator that can handle various content types"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for different content types"""
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
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'UniversalSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            textColor=HexColor('#7f8c8d'),
            alignment=1
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
        
        # Section heading style (keeping for compatibility)
        self.section_style = ParagraphStyle(
            'UniversalSection',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=15,
            textColor=HexColor('#3498db'),
            fontName='Helvetica-Bold',
            leftIndent=0
        )
        
        # Priority/Important style
        self.priority_style = ParagraphStyle(
            'UniversalPriority',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            textColor=HexColor('#e74c3c'),
            leftIndent=0
        )
        
        # Content style
        self.content_style = ParagraphStyle(
            'UniversalContent',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            textColor=HexColor('#2c3e50'),
            alignment=0  # Left alignment
        )
        
        # Metadata style
        self.metadata_style = ParagraphStyle(
            'UniversalMetadata',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=5,
            textColor=HexColor('#95a5a6'),
            leftIndent=20
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
        
        # Code block styles
        self.code_style = ParagraphStyle(
            'CodeStyle',
            parent=self.styles['Code'],
            fontSize=10,
            fontName='Courier',
            textColor=HexColor('#2c3e50'),
            backgroundColor=HexColor('#f8f9fa'),
            leftIndent=20,
            rightIndent=20,
            spaceBefore=8,
            spaceAfter=8,
            borderWidth=1,
            borderColor=HexColor('#e9ecef'),
            borderPadding=10
        )
        
        self.inline_code_style = ParagraphStyle(
            'InlineCodeStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Courier',
            textColor=HexColor('#e74c3c'),
            backgroundColor=HexColor('#f8f9fa')
        )
    
    def create_pdf(self, 
                  title: str,
                  content: Union[str, List[Dict], Dict],
                  output_path: str,
                  subtitle: Optional[str] = None,
                  metadata: Optional[Dict] = None) -> bool:
        """
        Create a PDF from various content types
        
        Args:
            title: Main title for the PDF
            content: Content to include (text, list of items, or structured data)
            output_path: Where to save the PDF file
            subtitle: Optional subtitle
            metadata: Optional metadata (author, date, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            story = []
            
            # Add title
            story.append(Paragraph(title, self.title_style))
            
            # Add subtitle if provided
            if subtitle:
                story.append(Paragraph(subtitle, self.subtitle_style))
            
            story.append(Spacer(1, 20))
            
            # Process content based on type
            if isinstance(content, str):
                story.extend(self._process_text_content(content))
            elif isinstance(content, list):
                story.extend(self._process_list_content(content))
            elif isinstance(content, dict):
                story.extend(self._process_dict_content(content))
            
            # Add metadata if provided
            if metadata:
                story.extend(self._add_metadata(metadata))
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"❌ PDF generation error: {e}")
            return False
    
    def _process_text_content(self, content: str) -> List:
        """Enhanced text content processing with improved formatting"""
        story = []
        
        # Fix overall sentence spacing first
        content = self._fix_sentence_spacing(content)
        
        # Pre-process plain text content to add structure
        content = self._enhance_plain_text_structure(content)
        
        # Clean markdown
        content = self._clean_markdown(content)
        
        # Split into logical blocks
        blocks = re.split(r'\n\s*\n', content)
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
                
            # Detect and format code blocks
            if self._is_code_block(block):
                story.extend(self._format_code_block(block))
                story.append(Spacer(1, 8))
                
            # Detect and format headings
            elif self._is_heading(block):
                story.append(self._format_heading(block))
                story.append(Spacer(1, 6))
                
            # Detect and format lists
            elif self._is_list(block):
                story.extend(self._format_list(block))
                story.append(Spacer(1, 8))
                
            # Regular paragraph
            else:
                # Apply inline code formatting
                block = self._format_inline_code(block)
                # Apply LaTeX math formatting if needed
                block = self._format_math_symbols(block)
                story.append(Paragraph(block, self.content_style))
                story.append(Spacer(1, 8))
        
        return story
    
    def _process_list_content(self, content: List[Dict]) -> List:
        """Process list of structured content items"""
        story = []
        
        for i, item in enumerate(content, 1):
            # Add item number/priority if available
            if 'priority' in item:
                story.append(Paragraph(f"{item['priority']} - Item {i}", self.priority_style))
            else:
                story.append(Paragraph(f"Item {i}", self.priority_style))
            
            # Add title if available
            if 'title' in item:
                story.append(Paragraph(f"<b>{item['title']}</b>", self.section_style))
            
            # Add metadata fields
            for field in ['date', 'source', 'sources']:
                if field in item:
                    story.append(Paragraph(f"<b>{field.title()}:</b> {item[field]}", self.metadata_style))
            
            # Add main content fields
            for field in ['details', 'content', 'description', 'analysis']:
                if field in item:
                    clean_text = self._clean_markdown(str(item[field]))
                    story.append(Paragraph(f"<b>{field.title()}:</b> {clean_text}", self.content_style))
                    story.append(Spacer(1, 5))
            
            story.append(Spacer(1, 15))
        
        return story
    
    def _process_dict_content(self, content: Dict) -> List:
        """Process dictionary content"""
        story = []
        
        for key, value in content.items():
            if isinstance(value, str):
                story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", self.content_style))
            elif isinstance(value, list):
                story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b>", self.content_style))
                for item in value:
                    story.append(Paragraph(f"• {item}", self.content_style))
            story.append(Spacer(1, 8))
        
        return story
    
    def _clean_markdown(self, text: str) -> str:
        """Enhanced markdown cleaning for PDF with HTML and markdown support"""
        if not text:
            return ""
        
        # FIRST: Check if this is HTML content and convert it
        if '<html>' in text.lower() or '<body>' in text.lower() or text.strip().startswith('<'):
            text = self._convert_html_to_text(text)
        
        # First pass: Handle block-level elements
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                processed_lines.append('')
                continue
                
            # Handle headers (convert to bold + size increase simulation)
            if line.startswith('#### '):
                text_content = line[5:].strip()
                processed_lines.append(f'<b><font size="12">{text_content}</font></b>')
            elif line.startswith('### '):
                text_content = line[4:].strip()
                processed_lines.append(f'<b><font size="14">{text_content}</font></b>')
            elif line.startswith('## '):
                text_content = line[3:].strip()
                processed_lines.append(f'<b><font size="16">{text_content}</font></b>')
            elif line.startswith('# '):
                text_content = line[2:].strip()
                processed_lines.append(f'<b><font size="18">{text_content}</font></b>')
            
            # Handle bullet lists
            elif line.startswith('- ') or line.startswith('* ') or line.startswith('+ '):
                text_content = line[2:].strip()
                processed_lines.append(f'• {text_content}')
            
            # Handle numbered lists  
            elif re.match(r'^\d+\.\s+', line):
                # Keep numbered list as-is but clean the content
                processed_lines.append(line)
            
            # Handle blockquotes
            elif line.startswith('> '):
                text_content = line[2:].strip()
                processed_lines.append(f'<i>"{text_content}"</i>')
            
            # Handle code blocks (simple detection)
            elif line.startswith('```') or line.startswith('~~~'):
                processed_lines.append('')  # Skip code block markers
            elif line.startswith('    ') or line.startswith('\t'):
                # Indented code
                processed_lines.append(f'<font name="Courier">{line.strip()}</font>')
            
            # Handle horizontal rules
            elif line.startswith('---') or line.startswith('***'):
                processed_lines.append('─' * 40)
            
            else:
                # Regular line - process inline formatting
                processed_lines.append(line)
        
        # Rejoin the lines
        text = '\n'.join(processed_lines)
        
        # Second pass: Handle inline formatting
        # Bold - **text** or __text__
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
        
        # Italic - *text* or _text_ (but avoid interfering with bold)
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', text)
        text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'<i>\1</i>', text)
        
        # Code - `text`
        text = re.sub(r'`([^`]+?)`', r'<font name="Courier">\1</font>', text)
        
        # Links - [text](url) -> just show text
        text = re.sub(r'\[([^\]]+?)\]\([^)]+?\)', r'\1', text)
        
        # Clean up markdown table remnants (basic cleanup)
        text = re.sub(r'\|([^|]+)\|', r'\1', text)  # Remove table pipes
        text = re.sub(r'^[\s\-|:]+$', '', text, flags=re.MULTILINE)  # Remove table separators
        
        # Clean up special characters that might cause reportlab issues
        text = text.replace('&', '&amp;')
        
        # Escape < and > but preserve our formatting tags
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        
        # Restore our formatting tags
        text = re.sub(r'&lt;(/?(?:b|i|font[^&]*))&gt;', r'<\1>', text)
        
        # Clean up excessive whitespace while preserving paragraph breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Max 2 consecutive newlines
        text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)  # Trim lines
        
        return text.strip()
    
    def _convert_html_to_text(self, html_content: str) -> str:
        """Convert HTML content to clean text suitable for PDF generation"""
        # Remove HTML doctype, html, head, body tags
        html_content = re.sub(r'<!DOCTYPE[^>]*>', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'</?html[^>]*>', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<head>.*?</head>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        html_content = re.sub(r'</?body[^>]*>', '', html_content, flags=re.IGNORECASE)
        
        # Convert HTML headers to markdown-style headers
        html_content = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', html_content, flags=re.IGNORECASE | re.DOTALL)
        html_content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1', html_content, flags=re.IGNORECASE | re.DOTALL)
        html_content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1', html_content, flags=re.IGNORECASE | re.DOTALL)
        html_content = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1', html_content, flags=re.IGNORECASE | re.DOTALL)
        html_content = re.sub(r'<h5[^>]*>(.*?)</h5>', r'##### \1', html_content, flags=re.IGNORECASE | re.DOTALL)
        html_content = re.sub(r'<h6[^>]*>(.*?)</h6>', r'###### \1', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert paragraphs (add double newlines for proper spacing)
        html_content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert line breaks
        html_content = re.sub(r'<br[^>]*/?>', '\n', html_content, flags=re.IGNORECASE)
        
        # Convert bold and italic
        html_content = re.sub(r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**', html_content, flags=re.IGNORECASE | re.DOTALL)
        html_content = re.sub(r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert lists
        html_content = re.sub(r'<ul[^>]*>', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'</ul>', '\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<ol[^>]*>', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'</ol>', '\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<li[^>]*>(.*?)</li>', r'• \1\n', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert blockquotes
        html_content = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'> \1\n', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert code blocks
        html_content = re.sub(r'<pre[^>]*>(.*?)</pre>', r'```\n\1\n```\n', html_content, flags=re.IGNORECASE | re.DOTALL)
        html_content = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove all remaining HTML tags
        html_content = re.sub(r'<[^>]+>', '', html_content)
        
        # Clean up HTML entities
        html_content = html_content.replace('&nbsp;', ' ')
        html_content = html_content.replace('&amp;', '&')
        html_content = html_content.replace('&lt;', '<')
        html_content = html_content.replace('&gt;', '>')
        html_content = html_content.replace('&quot;', '"')
        html_content = html_content.replace('&#39;', "'")
        
        # Clean up excessive whitespace
        html_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', html_content)
        html_content = re.sub(r'^\s+|\s+$', '', html_content, flags=re.MULTILINE)
        
        return html_content.strip()
    
    def _enhance_plain_text_structure(self, content: str) -> str:
        """Enhance plain text content with proper structure for PDFs"""
        if not content:
            return content
        
        lines = content.split('\n')
        enhanced_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                enhanced_lines.append('')
                continue
            
            # Skip name and contact info from being headings
            if self._is_contact_info(line, i, lines):
                enhanced_lines.append(line)
                
            # Detect section headings (common resume sections)
            elif self._is_resume_heading(line):
                enhanced_lines.append('')  # Add space before heading
                enhanced_lines.append(f'## {line}')
                enhanced_lines.append('')  # Add space after heading
                
            # Detect bullet points (lines starting with •, -, or special chars)
            elif line.startswith(('•', '▪', '◦', '∙')) or re.match(r'^[▪•]\s', line):
                # Already a bullet, keep as is
                enhanced_lines.append(f'- {line[1:].strip()}')
                
            # Detect implicit bullet points (lines that should be bullets)
            elif self._should_be_bullet(line, lines, i):
                enhanced_lines.append(f'- {line}')
                
            # Detect job titles/positions (lines with dates)
            elif self._is_job_title_line(line):
                enhanced_lines.append('')
                enhanced_lines.append(f'### {line}')
                
            # Regular line
            else:
                enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)
    
    def _is_contact_info(self, line: str, index: int, all_lines: List[str]) -> bool:
        """Detect contact information that shouldn't be treated as headings"""
        # First few lines are likely name and contact
        if index < 5:
            # Phone numbers
            if re.search(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', line):
                return True
            # Email addresses
            if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line):
                return True
            # Names (first line and short)
            if index == 0 and len(line.split()) <= 3 and not line.endswith(':'):
                return True
        return False
    
    def _is_resume_heading(self, line: str) -> bool:
        """Detect if a line is a resume section heading"""
        line_upper = line.upper().strip()
        resume_headings = [
            'PROFESSIONAL SUMMARY', 'SUMMARY', 'OBJECTIVE',
            'PROFESSIONAL EXPERIENCE', 'EXPERIENCE', 'WORK EXPERIENCE',
            'EDUCATION', 'SKILLS', 'SKILLS & EXPERTISE', 'TECHNICAL SKILLS',
            'CERTIFICATIONS', 'PROJECTS', 'MAJOR PROJECTS', 'ACHIEVEMENTS',
            'VOLUNTEER EXPERIENCE', 'VOLUNTEER', 'INTERESTS', 'HOBBIES',
            'AREAS OF EXCELLENCE', 'CORE COMPETENCIES', 'PUBLICATIONS',
            'ARTICLES AND BLOGS', 'CONTACT', 'CONTACT INFORMATION'
        ]
        
        # Exact match or contains match
        for heading in resume_headings:
            if line_upper == heading or heading in line_upper:
                return True
        
        # Pattern-based detection for standalone lines that look like headings
        if (len(line.split()) <= 4 and 
            (line.isupper() or line.istitle()) and 
            len(line) > 8 and  # Increased minimum length
            ':' not in line and
            not re.match(r'^\d', line) and
            not re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$', line)):
            return True
            
        return False
    
    def _should_be_bullet(self, line: str, all_lines: List[str], index: int) -> bool:
        """Detect if a line should be formatted as a bullet point"""
        # Skip if already has bullet markers
        if line.startswith(('•', '-', '*', '▪', '◦')):
            return False
            
        # Skip headings, long paragraphs, and dates
        if (len(line) > 80 or 
            self._is_resume_heading(line) or 
            self._is_job_title_line(line) or
            re.search(r'\b\d{4}\b', line)):
            return False
            
        # Look for skill/competency lists - be more conservative
        if index > 0:
            prev_line = all_lines[index - 1].strip()
            
            # Only make bullets if previous line was clearly a heading with colon or "are:"
            if (prev_line.endswith(':') or prev_line.endswith('are:')) and \
               len(line.split()) <= 8 and \
               not line.endswith('.') and \
               line[0].isupper() and \
               len(line) < 60:
                return True
        
        return False
    
    def _is_job_title_line(self, line: str) -> bool:
        """Detect job title/position lines"""
        # Look for patterns like "Title at Company" or lines with date ranges
        date_patterns = [
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
            r'\b\d{4}\s*-\s*\d{4}\b',
            r'\b\d{4}\s*–\s*\d{4}\b',
            r'\b\d{4}\s*to\s*\d{4}\b',
            r'\b\d{4}\s*-\s*Present\b',
            r'\b\d{1,2}/\d{4}\s*-\s*\d{1,2}/\d{4}\b'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
                
        # Look for job title patterns
        job_patterns = [
            r'\b(Manager|Director|Lead|Senior|Executive|Developer|Engineer|Analyst|Specialist)\b.*\bat\b',
            r'\b(Co-Founder|Founder|CEO|CTO|VP|President)\b',
        ]
        
        for pattern in job_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
                
        return False
    
    def _add_metadata(self, metadata: Dict) -> List:
        """Add simple footer with timestamp only"""
        story = []
        # Only add a simple timestamp if metadata is provided
        if metadata:
            story.append(Spacer(1, 30))
            # Simple single line timestamp
            timestamp = datetime.now().strftime('%B %d, %Y')
            story.append(Paragraph(f"{timestamp}", self.metadata_style))
        
        return story
    
    def _fix_sentence_spacing(self, text: str) -> str:
        """Fix sentence spacing issues"""
        # Ensure proper space after sentence-ending punctuation
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        # Fix common spacing issues
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'([.!?])\s*([a-z])', r'\1 \2', text)  # Space after punctuation
        
        return text.strip()
    
    def _is_heading(self, text: str) -> bool:
        """Detect if text is a heading"""
        text = text.strip()
        
        # Check for markdown headers first
        if re.match(r'^#{1,6}\s+', text):
            return True
        
        # Check for common heading patterns
        heading_patterns = [
            r'^[A-Z][A-Za-z\s]+:$',  # "Professional Summary:"
            r'^\*\*.*\*\*$',  # **Bold text**
        ]
        
        for pattern in heading_patterns:
            if re.match(pattern, text):
                return True
        
        # Enhanced resume heading detection
        if self._is_resume_heading(text):
            return True
        
        # Check if it's a short line that looks like a heading
        words = text.split()
        if len(words) <= 6 and len(text) < 60 and (text.isupper() or text.istitle()):
            return True
            
        return False
    
    def _format_heading(self, text: str):
        """Format text as a heading with appropriate style"""
        # Clean markdown formatting
        text = re.sub(r'^\*\*(.*)\*\*$', r'\1', text)
        text = re.sub(r'^#{1,6}\s+', '', text)
        text = text.strip()
        
        # Determine heading level based on context
        if text.isupper() or len(text.split()) <= 3:
            return Paragraph(f"<b>{text}</b>", self.heading1_style)
        else:
            return Paragraph(f"<b>{text}</b>", self.heading2_style)
    
    def _is_list(self, text: str) -> bool:
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
        
        # For resume content, be more aggressive about detecting lists
        # Even a single bullet point should be treated as a list
        return list_count >= 1
    
    def _format_list(self, text: str) -> List:
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
    
    def _format_math_symbols(self, text: str) -> str:
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
    
    def _is_code_block(self, text: str) -> bool:
        """Detect if text is a code block"""
        text = text.strip()
        
        # Detect various code block patterns
        code_patterns = [
            r'^```[\w]*\n.*\n```$',  # Markdown code blocks
            r'^`{3,}.*`{3,}$',       # Triple backticks
            r'^\s{4,}.*',            # Indented code (4+ spaces)
            r'^\t.*',                # Tab-indented code
        ]
        
        for pattern in code_patterns:
            if re.match(pattern, text, re.DOTALL | re.MULTILINE):
                return True
                
        # Check for high density of code-like characters
        code_chars = len(re.findall(r'[{}();=\[\]<>/\\]', text))
        if len(text) > 20 and code_chars / len(text) > 0.15:
            return True
            
        return False
    
    def _format_code_block(self, text: str) -> List:
        """Format code block for PDF"""
        story = []
        
        # Clean markdown code block markers
        text = re.sub(r'^```[\w]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        
        # Split into lines and preserve formatting
        lines = text.split('\n')
        code_content = []
        
        for line in lines:
            # Preserve indentation and special characters
            if line.strip():
                code_content.append(line)
            else:
                code_content.append(' ')  # Preserve empty lines
        
        # Create code block paragraph
        code_text = '\n'.join(code_content)
        story.append(Paragraph(f'<font name="Courier">{code_text}</font>', self.code_style))
        
        return story
    
    def _format_inline_code(self, text: str) -> str:
        """Format inline code snippets"""
        # Replace `code` with formatted version
        text = re.sub(r'`([^`]+)`', r'<font name="Courier" color="#e74c3c">\1</font>', text)
        return text


# Convenience functions for easy use
def create_pdf_from_text(title: str, content: str, output_path: str, subtitle: str = None) -> bool:
    """Create PDF from plain text content"""
    generator = UniversalPDFGenerator()
    return generator.create_pdf(title, content, output_path, subtitle)


def create_pdf_from_news(title: str, news_items: List[Dict], output_path: str) -> bool:
    """Create PDF from news items with priority sorting"""
    generator = UniversalPDFGenerator()
    
    # Sort by priority if available
    if news_items and 'priority' in news_items[0]:
        priority_order = {'🔴': 0, '🟡': 1, '🔵': 2, 'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        news_items.sort(key=lambda x: priority_order.get(x.get('priority', '').split()[0], 99))
    
    # No metadata per user requirements - remove all tool references and metadata
    return generator.create_pdf(title, news_items, output_path, 
                               subtitle="Comprehensive Analysis Report", 
                               metadata=None)


def create_pdf_from_stock_analysis(title: str, analysis_data: Dict, output_path: str) -> bool:
    """Create PDF from stock analysis data"""
    generator = UniversalPDFGenerator()
    
    # No metadata per user requirements - remove all tool references and metadata
    return generator.create_pdf(title, analysis_data, output_path,
                               subtitle="Investment Analysis & Recommendations",
                               metadata=None)


# Test function
if __name__ == "__main__":
    # Test the universal PDF generator
    test_content = """# Test Document
    
## This is a test section

This is regular content with **bold text** and *italic text*.

### Subsection

More content here with `code formatting`.

**Important Note**: This is a bold paragraph.
"""
    
    success = create_pdf_from_text("Test PDF", test_content, "/tmp/test_universal.pdf")
    print(f"Test PDF creation: {'✅ Success' if success else '❌ Failed'}")