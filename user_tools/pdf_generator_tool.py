#!/usr/bin/env python3
"""
Enhanced PDF Generator Tool
==========================

A comprehensive PDF generation tool that handles text, markdown, and HTML content
with proper formatting, styles, and structure.

Features:
- Text to PDF with intelligent formatting detection
- Markdown to PDF with full formatting support
- HTML to PDF conversion with clean layout
- Automatic content type detection
- Professional styling and layout
- Cross-references and proper heading hierarchy
- Code block and list formatting
- Math symbol support
- Error handling and fallback mechanisms
"""

import os
import re
import html
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from datetime import datetime

try:
    from .base_user_tool import BaseUserTool
except ImportError:
    from base_user_tool import BaseUserTool

# Import PDF generation dependencies
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor, Color
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PDFGeneratorTool(BaseUserTool):
    """Enhanced PDF Generator Tool with support for text, markdown, and HTML"""
    
    def __init__(self):
        super().__init__()
        self.styles = None
        self._setup_styles()
    
    @property
    def name(self) -> str:
        return "pdf_generator"
    
    @property 
    def description(self) -> str:
        return "Generate professional PDF documents from text, markdown, or HTML content with proper formatting, headings, lists, and styling. Supports automatic content type detection and conversion."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Output PDF filename (with or without .pdf extension)"
                },
                "title": {
                    "type": "string", 
                    "description": "Document title to appear at the top of the PDF"
                },
                "content": {
                    "type": "string",
                    "description": "Content to convert to PDF (text, markdown, or HTML)"
                },
                "content_type": {
                    "type": "string",
                    "enum": ["auto", "text", "markdown", "html"],
                    "description": "Content format type. 'auto' will detect automatically",
                    "default": "auto"
                },
                "subtitle": {
                    "type": "string",
                    "description": "Optional subtitle for the document"
                }
            },
            "required": ["filename", "title", "content"]
        }
    
    def _setup_styles(self):
        """Setup comprehensive styles for different content types"""
        if not REPORTLAB_AVAILABLE:
            return
        
        self.styles = getSampleStyleSheet()
        
        # Enhanced Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=20,
            spaceBefore=0,
            spaceAfter=24,
            textColor=HexColor('#2c3e50'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceBefore=6,
            spaceAfter=20,
            textColor=HexColor('#7f8c8d'),
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        # Heading styles with proper hierarchy
        self.h1_style = ParagraphStyle(
            'CustomHeading1',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceBefore=20,
            spaceAfter=12,
            textColor=HexColor('#2c3e50'),
            fontName='Helvetica-Bold',
            keepWithNext=True
        )
        
        self.h2_style = ParagraphStyle(
            'CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=16,
            spaceAfter=8,
            textColor=HexColor('#34495e'),
            fontName='Helvetica-Bold',
            keepWithNext=True
        )
        
        self.h3_style = ParagraphStyle(
            'CustomHeading3',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceBefore=12,
            spaceAfter=6,
            textColor=HexColor('#2c3e50'),
            fontName='Helvetica-Bold',
            keepWithNext=True
        )
        
        self.h4_style = ParagraphStyle(
            'CustomHeading4',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=4,
            textColor=HexColor('#2c3e50'),
            fontName='Helvetica-Bold',
            keepWithNext=True
        )
        
        # Body text style
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceBefore=0,
            spaceAfter=8,
            textColor=HexColor('#2c3e50'),
            alignment=TA_JUSTIFY,
            leftIndent=0,
            rightIndent=0
        )
        
        # List styles
        self.bullet_style = ParagraphStyle(
            'BulletList',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=20,
            bulletIndent=10,
            spaceBefore=2,
            spaceAfter=2,
            bulletFontName='Symbol'
        )
        
        self.number_style = ParagraphStyle(
            'NumberList',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=20,
            bulletIndent=10,
            spaceBefore=2,
            spaceAfter=2
        )
        
        # Code styles
        self.code_style = ParagraphStyle(
            'CodeBlock',
            parent=self.styles['Code'],
            fontSize=9,
            fontName='Courier',
            textColor=HexColor('#2c3e50'),
            backgroundColor=HexColor('#f8f9fa'),
            leftIndent=20,
            rightIndent=20,
            spaceBefore=8,
            spaceAfter=8,
            borderWidth=1,
            borderColor=HexColor('#e9ecef'),
            borderPadding=8
        )
        
        # Blockquote style
        self.quote_style = ParagraphStyle(
            'Blockquote',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=30,
            rightIndent=30,
            textColor=HexColor('#555555'),
            fontName='Helvetica-Oblique',
            spaceBefore=8,
            spaceAfter=8
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute PDF generation using CENTRALIZED PDF SERVICE"""
        
        print("🎯 PDFGeneratorTool: Routing to CENTRALIZED PDF SERVICE")
        
        try:
            # Import the centralized PDF service
            from services.pdf_service import create_pdf
            
            # Extract parameters
            filename = kwargs.get('filename', '')
            title = kwargs.get('title', '')
            content = kwargs.get('content', '')
            content_type = kwargs.get('content_type', 'auto')
            
            # Validate inputs
            if not filename or not content:
                return {
                    "success": False,
                    "error": "Missing required parameters: filename and content are required"
                }
            
            # Ensure filename has .pdf extension
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
            
            # Route to centralized PDF service
            result = create_pdf(
                content=content,
                output_path=filename,
                title=title or "Generated Document",
                content_type=content_type
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"PDF generation failed: {str(e)}"
            }

    def _detect_content_type(self, content: str) -> str:
        """Automatically detect content type"""
        content_lower = content.lower().strip()
        
        # Check for HTML
        html_patterns = [
            r'<!doctype\s+html',
            r'<html[^>]*>',
            r'<body[^>]*>',
            r'<div[^>]*>',
            r'<p[^>]*>',
            r'<h[1-6][^>]*>',
            r'<table[^>]*>',
            r'<ul[^>]*>',
            r'<ol[^>]*>'
        ]
        
        for pattern in html_patterns:
            if re.search(pattern, content_lower):
                return 'html'
        
        # Check for Markdown
        markdown_patterns = [
            r'^#{1,6}\s+',  # Headers
            r'^\*\*.*\*\*',  # Bold
            r'^_.*_',  # Italic
            r'^\* ',  # Bullet list
            r'^\d+\. ',  # Numbered list
            r'^\[.*\]\(.*\)',  # Links
            r'^```',  # Code blocks
            r'^>',  # Blockquotes
            r'^\|.*\|',  # Tables
        ]
        
        lines = content.split('\n')
        markdown_score = 0
        
        for line in lines:
            line = line.strip()
            for pattern in markdown_patterns:
                if re.match(pattern, line, re.MULTILINE):
                    markdown_score += 1
                    break
        
        # If more than 10% of lines have markdown patterns
        if len(lines) > 0 and markdown_score / len(lines) > 0.1:
            return 'markdown'
        
        # Default to text
        return 'text'
    
    async def _generate_pdf(self, filename: str, title: str, content: str, 
                          content_type: str, subtitle: str = '') -> str:
        """Generate PDF with appropriate formatting"""
        
        # Create output path - handle both absolute and relative paths correctly
        if Path(filename).is_absolute():
            output_path = Path(filename)
        else:
            output_path = Path.cwd() / filename
        
        # Create document
        doc = SimpleDocTemplate(
            str(output_path),
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
        if content_type == 'html':
            story.extend(self._process_html_content(content))
        elif content_type == 'markdown':
            story.extend(self._process_markdown_content(content))
        else:
            story.extend(self._process_text_content(content))
        
        # Add timestamp
        timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"<i>Generated on {timestamp}</i>", self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return str(output_path)
    
    def _process_html_content(self, content: str) -> List:
        """Process HTML content and convert to PDF elements"""
        story = []
        
        # Clean and convert HTML
        content = self._html_to_structured_text(content)
        
        # Process as structured content
        story.extend(self._process_structured_content(content))
        
        return story
    
    def _process_markdown_content(self, content: str) -> List:
        """Process Markdown content and convert to PDF elements"""
        story = []
        
        # Convert markdown to structured content
        content = self._markdown_to_structured_text(content)
        
        # Process as structured content
        story.extend(self._process_structured_content(content))
        
        return story
    
    def _process_text_content(self, content: str) -> List:
        """Process plain text content with intelligent formatting"""
        story = []
        
        # Enhanced plain text processing
        content = self._enhance_text_structure(content)
        
        # Process as structured content
        story.extend(self._process_structured_content(content))
        
        return story
    
    def _process_structured_content(self, content: str) -> List:
        """Process structured content with proper formatting"""
        story = []
        
        # Split into blocks
        blocks = re.split(r'\n\s*\n', content)
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            
            # Process different block types
            if self._is_heading(block):
                story.append(self._format_heading(block))
                story.append(Spacer(1, 6))
            elif self._is_list(block):
                story.extend(self._format_list(block))
                story.append(Spacer(1, 8))
            elif self._is_code_block(block):
                story.extend(self._format_code_block(block))
                story.append(Spacer(1, 8))
            elif self._is_blockquote(block):
                story.append(self._format_blockquote(block))
                story.append(Spacer(1, 8))
            else:
                # Regular paragraph
                formatted_block = self._format_inline_elements(block)
                story.append(Paragraph(formatted_block, self.body_style))
                story.append(Spacer(1, 6))
        
        return story
    
    def _html_to_structured_text(self, html_content: str) -> str:
        """Convert HTML to structured text format"""
        # Remove HTML comments
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        
        # Convert HTML elements to structured text
        conversions = [
            # Headers
            (r'<h1[^>]*>(.*?)</h1>', r'# \1'),
            (r'<h2[^>]*>(.*?)</h2>', r'## \1'),
            (r'<h3[^>]*>(.*?)</h3>', r'### \1'),
            (r'<h4[^>]*>(.*?)</h4>', r'#### \1'),
            (r'<h5[^>]*>(.*?)</h5>', r'##### \1'),
            (r'<h6[^>]*>(.*?)</h6>', r'###### \1'),
            
            # Paragraphs
            (r'<p[^>]*>(.*?)</p>', r'\1\n\n'),
            
            # Line breaks
            (r'<br[^>]*/?>', '\n'),
            
            # Bold and italic
            (r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**'),
            (r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*'),
            
            # Lists
            (r'<ul[^>]*>', '\n'),
            (r'</ul>', '\n'),
            (r'<ol[^>]*>', '\n'),
            (r'</ol>', '\n'),
            (r'<li[^>]*>(.*?)</li>', r'• \1\n'),
            
            # Code
            (r'<pre[^>]*>(.*?)</pre>', r'```\n\1\n```\n'),
            (r'<code[^>]*>(.*?)</code>', r'`\1`'),
            
            # Blockquotes
            (r'<blockquote[^>]*>(.*?)</blockquote>', r'> \1\n'),
            
            # Tables (basic conversion)
            (r'<table[^>]*>', '\n'),
            (r'</table>', '\n'),
            (r'<tr[^>]*>', ''),
            (r'</tr>', '\n'),
            (r'<t[hd][^>]*>(.*?)</t[hd]>', r'\1 | '),
        ]
        
        for pattern, replacement in conversions:
            html_content = re.sub(pattern, replacement, html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove remaining HTML tags
        html_content = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode HTML entities
        html_content = html.unescape(html_content)
        
        # Clean up whitespace
        html_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', html_content)
        
        return html_content.strip()
    
    def _markdown_to_structured_text(self, md_content: str) -> str:
        """Process markdown content for PDF formatting"""
        # Already in a good format for processing
        # Just clean up any problematic patterns
        
        # Ensure proper spacing around headers
        md_content = re.sub(r'\n(#{1,6})', r'\n\n\1', md_content)
        md_content = re.sub(r'(#{1,6}[^\n]+)\n', r'\1\n\n', md_content)
        
        # Clean up excessive whitespace
        md_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', md_content)
        
        return md_content.strip()
    
    def _enhance_text_structure(self, text_content: str) -> str:
        """Enhance plain text with structure detection"""
        lines = text_content.split('\n')
        enhanced_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                enhanced_lines.append('')
                continue
            
            # Detect potential headings (all caps, title case standalone lines)
            if self._looks_like_heading(line, lines, i):
                # Convert to markdown-style heading
                if len(line) < 30 and line.isupper():
                    enhanced_lines.append(f'# {line.title()}')
                else:
                    enhanced_lines.append(f'## {line}')
                continue
            
            # Detect bullet points
            if line.startswith(('•', '▪', '◦', '∙', '-', '*')):
                # Convert to standard bullet
                content = re.sub(r'^[•▪◦∙\-*]\s*', '', line)
                enhanced_lines.append(f'• {content}')
                continue
            
            # Regular line
            enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)
    
    def _looks_like_heading(self, line: str, all_lines: List[str], index: int) -> bool:
        """Determine if a line looks like a heading"""
        # Skip if it's too long
        if len(line) > 60:
            return False
        
        # Skip if it contains sentence-ending punctuation
        if line.endswith(('.', '!', '?')):
            return False
        
        # Check for common heading patterns
        if (len(line.split()) <= 6 and 
            (line.isupper() or line.istitle()) and
            ':' not in line):
            return True
        
        # Check if next line is blank (typical heading pattern)
        if (index + 1 < len(all_lines) and 
            not all_lines[index + 1].strip() and
            len(line.split()) <= 4):
            return True
        
        return False
    
    def _is_heading(self, text: str) -> bool:
        """Check if text is a heading"""
        text = text.strip()
        return text.startswith(('#', '##', '###', '####', '#####', '######'))
    
    def _format_heading(self, text: str) -> Paragraph:
        """Format heading with appropriate style"""
        # Count heading level
        level = 0
        while text.startswith('#'):
            level += 1
            text = text[1:]
        
        text = text.strip()
        
        # Choose appropriate style
        if level == 1:
            style = self.h1_style
        elif level == 2:
            style = self.h2_style
        elif level == 3:
            style = self.h3_style
        else:
            style = self.h4_style
        
        return Paragraph(f"<b>{text}</b>", style)
    
    def _is_list(self, text: str) -> bool:
        """Check if text contains list items"""
        lines = text.split('\n')
        list_lines = 0
        
        for line in lines:
            line = line.strip()
            if (line.startswith('•') or 
                line.startswith('-') or 
                line.startswith('*') or
                re.match(r'^\d+\.', line)):
                list_lines += 1
        
        return list_lines >= 1
    
    def _format_list(self, text: str) -> List:
        """Format list items"""
        story = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                content = re.sub(r'^[•\-*]\s*', '', line)
                story.append(Paragraph(f"• {content}", self.bullet_style))
            elif re.match(r'^\d+\.', line):
                story.append(Paragraph(line, self.number_style))
            else:
                # Continuation of list item
                story.append(Paragraph(line, self.bullet_style))
        
        return story
    
    def _is_code_block(self, text: str) -> bool:
        """Check if text is a code block"""
        return (text.startswith('```') and text.endswith('```')) or text.startswith('    ')
    
    def _format_code_block(self, text: str) -> List:
        """Format code block"""
        # Remove markdown code block markers
        if text.startswith('```') and text.endswith('```'):
            text = text[3:-3].strip()
        
        # Remove leading spaces (indented code)
        lines = text.split('\n')
        dedented_lines = []
        for line in lines:
            if line.startswith('    '):
                dedented_lines.append(line[4:])
            else:
                dedented_lines.append(line)
        
        code_text = '\n'.join(dedented_lines)
        
        return [Paragraph(f'<font name="Courier">{code_text}</font>', self.code_style)]
    
    def _is_blockquote(self, text: str) -> bool:
        """Check if text is a blockquote"""
        return text.startswith('>')
    
    def _format_blockquote(self, text: str) -> Paragraph:
        """Format blockquote"""
        # Remove quote markers
        lines = text.split('\n')
        quote_lines = []
        for line in lines:
            if line.startswith('>'):
                quote_lines.append(line[1:].strip())
            else:
                quote_lines.append(line)
        
        quote_text = ' '.join(quote_lines)
        return Paragraph(f'<i>"{quote_text}"</i>', self.quote_style)
    
    def _format_inline_elements(self, text: str) -> str:
        """Format inline elements like bold, italic, code"""
        # Bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
        
        # Italic
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', text)
        text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'<i>\1</i>', text)
        
        # Inline code
        text = re.sub(r'`([^`]+?)`', r'<font name="Courier">\1</font>', text)
        
        # Links (just show the text part)
        text = re.sub(r'\[([^\]]+?)\]\([^)]+?\)', r'\1', text)
        
        # Escape special characters for reportlab
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        
        # Restore our formatting tags
        text = text.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
        text = text.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
        text = text.replace('&lt;font name="Courier"&gt;', '<font name="Courier">').replace('&lt;/font&gt;', '</font>')
        
        return text
    
    async def _generate_pdf_with_markdown_pdf(self, filename: str, title: str, content: str) -> str:
        """Generate PDF using markdown-pdf library (improved implementation)"""
        try:
            # Import the markdown-pdf library
            from markdown_pdf import MarkdownPdf, Section
            from pathlib import Path
            import tempfile
            import os
            import datetime
            
            print(f"📋 PDF-GENERATOR: Using markdown-pdf library for professional formatting")
            
            # Create output path - handle both absolute and relative paths correctly
            if Path(filename).is_absolute():
                output_path = Path(filename)
            else:
                output_path = Path.cwd() / filename
            
            # Create parent directories if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Extract better title from content if possible
            extracted_title = title
            if content:
                lines = content.split('\n')
                first_line = lines[0].strip() if lines else ""
                if first_line and len(first_line) < 200 and not first_line.startswith('##'):
                    extracted_title = first_line
                else:
                    # Look for markdown titles (# Title)
                    for line in lines[:10]:
                        line = line.strip()
                        if line.startswith('# '):
                            extracted_title = line[2:].strip()
                            break
            
            # Safety check - ensure title is not the entire content
            if len(extracted_title) > 200:
                extracted_title = title
            
            # DEBUG logging
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            print(f"📋 PDF-GENERATOR DEBUG [{timestamp}]: INVOKING markdown-pdf library")
            print(f"📋 PDF-GENERATOR DEBUG: Filename: {filename}")
            print(f"📋 PDF-GENERATOR DEBUG: Full path: {output_path}")
            print(f"📋 PDF-GENERATOR DEBUG: Title: '{extracted_title}' (length: {len(extracted_title)})")
            print(f"📋 PDF-GENERATOR DEBUG: Content length: {len(content)} characters")
            print(f"📋 PDF-GENERATOR DEBUG: Starting professional PDF generation...")
            
            # Create PDF using markdown-pdf library
            pdf = MarkdownPdf(toc_level=2, optimize=True)
            
            # Set document metadata
            pdf.meta["title"] = extracted_title
            pdf.meta["author"] = "AI Assistant"
            pdf.meta["subject"] = "Generated Report"
            
            # Create custom CSS for professional formatting
            custom_css = """
            /* Set default font */
            body {
                font-family: "DejaVu Serif", serif;
                font-size: 12pt;
                line-height: 1.6;
                color: #222;
                margin: 1in;
            }

            /* Headings */
            h1 {
                font-size: 24pt;
                color: #003366;
                text-align: center;
                margin-bottom: 20px;
                border-bottom: 2px solid #003366;
                padding-bottom: 10px;
            }
            h2 {
                font-size: 18pt;
                color: #004488;
                margin-top: 30px;
                margin-bottom: 15px;
                border-left: 4px solid #004488;
                padding-left: 15px;
            }
            h3 {
                font-size: 14pt;
                color: #006699;
                margin-top: 20px;
                margin-bottom: 10px;
            }
            h4 {
                font-size: 13pt;
                color: #0088aa;
                margin-top: 15px;
                margin-bottom: 8px;
            }

            /* Paragraphs */
            p {
                margin-bottom: 12px;
                text-align: justify;
            }

            /* Lists */
            ul, ol {
                margin-left: 20px;
                margin-bottom: 12px;
            }
            
            li {
                margin-bottom: 6px;
            }

            /* Strong/Bold text */
            strong, b {
                color: #003366;
                font-weight: bold;
            }

            /* Code blocks */
            code, pre {
                font-family: "Courier New", monospace;
                background: #f4f4f4;
                border: 1px solid #ccc;
                padding: 6px;
                border-radius: 4px;
                font-size: 10pt;
            }

            /* Tables */
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 11pt;
            }
            
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            
            th {
                background-color: #003366;
                color: white;
                font-weight: bold;
            }
            
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }

            /* Table of contents styling */
            .toc {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                padding: 20px;
                margin-bottom: 30px;
                border-radius: 5px;
            }
            """
            
            # NOTE: Using default markdown-pdf styling (custom CSS not supported in meta)
            
            # Add the content as a section with proper formatting
            pdf.add_section(Section(content, toc=True))
            
            # Save the PDF
            print(f"📋 PDF-GENERATOR DEBUG: Calling pdf.save('{output_path}')...")
            pdf.save(str(output_path))
            print(f"📋 PDF-GENERATOR DEBUG: PDF generation completed successfully!")
            
            # PDF generation completed
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ PDF-GENERATOR ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise


# Test function
async def test_pdf_generator():
    """Test the PDF generator with different content types"""
    tool = PDFGeneratorTool()
    
    # Test markdown content
    markdown_content = """# Test Document

## Introduction

This is a **test document** with *various* formatting elements.

### Features

- Bullet point 1
- Bullet point 2
- Bullet point 3

1. Numbered item 1
2. Numbered item 2
3. Numbered item 3

### Code Example

```python
def hello_world():
    print("Hello, World!")
```

> This is a blockquote with some important information.

### Conclusion

This document demonstrates the PDF generator capabilities."""
    
    result = await tool.execute(
        filename="test_pdf_generator.pdf",
        title="PDF Generator Test",
        content=markdown_content,
        content_type="markdown",
        subtitle="Testing various formatting features"
    )
    
    print("Test result:", result)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_pdf_generator())