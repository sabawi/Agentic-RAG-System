#!/usr/bin/env python3
"""
Centralized PDF Service - Single Entry Point for ALL PDF Operations
==================================================================

This is the ONLY place in the codebase that handles PDF creation, conversion,
and generation. All other tools and services MUST use this service.

Uses: markdown-pdf library exclusively for consistent formatting.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class CentralizedPDFService:
    """
    The ONE AND ONLY PDF service for the entire codebase.
    All PDF operations must go through this service.
    """
    
    def __init__(self):
        """Initialize the centralized PDF service"""
        self.service_name = "CentralizedPDFService"
        print(f"🎯 {self.service_name}: Initialized as THE ONLY PDF service")
        
        # Check if WeasyPrint is available (supports CSS @page rules)
        try:
            import weasyprint
            import markdown
            self.weasyprint_available = True
            self.markdown_pdf_available = False  # Disable old library
            print(f"✅ {self.service_name}: WeasyPrint library loaded successfully (supports CSS @page)")
        except ImportError:
            # Fallback to markdown-pdf
            try:
                from markdown_pdf import MarkdownPdf, Section
                self.markdown_pdf_available = True
                self.weasyprint_available = False
                print(f"⚠️ {self.service_name}: Using markdown-pdf (limited CSS support)")
            except ImportError as e:
                self.markdown_pdf_available = False
                self.weasyprint_available = False
                print(f"❌ {self.service_name}: No PDF libraries available: {e}")
    
    def create_pdf(self, 
                   content: str,
                   output_path: str,
                   title: str = "Document",
                   content_type: str = "auto") -> Dict[str, Any]:
        """
        THE SINGLE ENTRY POINT for all PDF creation in the entire codebase.
        
        Args:
            content: The content to convert to PDF
            output_path: Where to save the PDF file
            title: Document title
            content_type: auto, text, markdown, html
            
        Returns:
            Dict with success status and details
        """
        
        print(f"🎯 {self.service_name}: PDF CREATION REQUEST RECEIVED")
        print(f"   📄 Title: {title}")
        print(f"   📁 Output: {output_path}")
        print(f"   📝 Content Type: {content_type}")
        print(f"   📏 Content Length: {len(content)} chars")
        
        # Check if service is available
        if not self.weasyprint_available and not self.markdown_pdf_available:
            error_msg = "No PDF library available. Install WeasyPrint with: pip install weasyprint"
            print(f"❌ {self.service_name}: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "service": self.service_name
            }
        
        try:
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Auto-detect content type if needed
            if content_type == "auto":
                content_type = self._detect_content_type(content)
                print(f"🔍 {self.service_name}: Auto-detected content type: {content_type}")
            
            # Use WeasyPrint if available (supports CSS @page), otherwise fallback
            if self.weasyprint_available:
                # Convert content to markdown format for consistent processing
                markdown_content = self._normalize_to_markdown(content, content_type)
                
                result = self._create_pdf_with_weasyprint(
                    markdown_content=markdown_content,
                    output_path=output_path,
                    title=title
                )
            else:
                # Fallback to markdown-pdf (limited CSS support)
                markdown_content = self._normalize_to_markdown(content, content_type)
                
                result = self._create_pdf_with_markdown_pdf(
                    markdown_content=markdown_content,
                    output_path=output_path,
                    title=title
                )
            
            if result["success"]:
                print(f"✅ {self.service_name}: PDF created successfully at {output_path}")
                return {
                    "success": True,
                    "file_path": output_path,
                    "title": self._format_title(title),
                    "size_bytes": os.path.getsize(output_path) if os.path.exists(output_path) else 0,
                    "service": self.service_name,
                    "library": "markdown-pdf"
                }
            else:
                print(f"❌ {self.service_name}: PDF creation failed: {result.get('error')}")
                return result
                
        except Exception as e:
            error_msg = f"PDF creation failed: {str(e)}"
            print(f"❌ {self.service_name}: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "service": self.service_name
            }
    
    def _detect_content_type(self, content: str) -> str:
        """Auto-detect the content type"""
        content_lower = content.lower().strip()
        
        # Check for HTML
        if any(pattern in content_lower for pattern in ['<html', '<!doctype', '<div>', '<p>', '<body>']):
            return "html"
        
        # Check for Markdown
        if any(pattern in content for pattern in ['# ', '## ', '### ', '**', '*', '- ', '1. ', '`']):
            return "markdown"
        
        # Default to text
        return "text"
    
    def _normalize_to_markdown(self, content: str, content_type: str) -> str:
        """Convert all content types to markdown for consistent processing"""
        
        if content_type == "markdown":
            return content
        
        elif content_type == "html":
            return self._html_to_markdown(content)
        
        elif content_type == "text":
            return self._text_to_markdown(content)
        
        else:
            # Fallback: treat as text
            return self._text_to_markdown(content)
    
    def _html_to_markdown(self, html_content: str) -> str:
        """Convert HTML to markdown"""
        import re
        
        # Simple HTML to markdown conversion
        # This is basic - you might want to use a proper HTML parser for complex HTML
        markdown = html_content
        
        # Convert headers
        markdown = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', markdown, flags=re.IGNORECASE | re.DOTALL)
        markdown = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1', markdown, flags=re.IGNORECASE | re.DOTALL)
        markdown = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1', markdown, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert paragraphs
        markdown = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', markdown, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert bold and italic
        markdown = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', markdown, flags=re.IGNORECASE | re.DOTALL)
        markdown = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', markdown, flags=re.IGNORECASE | re.DOTALL)
        
        # Convert lists
        markdown = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1', markdown, flags=re.IGNORECASE | re.DOTALL)
        markdown = re.sub(r'<ul[^>]*>(.*?)</ul>', r'\1', markdown, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove other HTML tags
        markdown = re.sub(r'<[^>]+>', '', markdown)
        
        # Clean up whitespace
        markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)
        
        return markdown.strip()
    
    def _text_to_markdown(self, text_content: str) -> str:
        """Convert plain text to markdown with basic formatting"""
        lines = text_content.split('\n')
        markdown_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                markdown_lines.append('')
                continue
            
            # Detect headers (lines that are all caps or end with colons)
            if line.isupper() and len(line.split()) <= 8:
                markdown_lines.append(f'## {line.title()}')
            elif line.endswith(':') and len(line.split()) <= 8:
                markdown_lines.append(f'### {line[:-1]}')
            # Detect bullet points
            elif line.startswith(('- ', '* ', '• ')):
                markdown_lines.append(line)
            elif line.startswith(tuple('0123456789')) and ('. ' in line or ') ' in line):
                markdown_lines.append(line)
            else:
                # Regular paragraph
                markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)
    
    def _create_pdf_with_markdown_pdf(self, 
                                      markdown_content: str,
                                      output_path: str,
                                      title: str) -> Dict[str, Any]:
        """Create PDF using markdown-pdf library with external CSS styling"""
        
        try:
            from markdown_pdf import MarkdownPdf, Section
            
            print(f"🔧 {self.service_name}: Using markdown-pdf library for PDF generation")
            
            # Locate the CSS file in config directory
            css_file_path = self._get_css_file_path()
            
            # Create PDF instance
            pdf = MarkdownPdf(toc_level=2, optimize=True)
            
            # Set metadata with formatted title
            pdf.meta["title"] = self._format_title(title)
            pdf.meta["author"] = "AI Assistant"
            pdf.meta["subject"] = "Generated Document"
            pdf.meta["creator"] = self.service_name
            pdf.meta["producer"] = "markdown-pdf"
            
            # Apply external CSS styling if available
            if css_file_path and os.path.exists(css_file_path):
                # Read CSS content and apply it directly
                with open(css_file_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                
                # Apply CSS through the correct method
                pdf.stylesheet = css_content
                print(f"🎨 {self.service_name}: Applied CSS styling from {css_file_path}")
                css_applied = True
            else:
                print(f"⚠️ {self.service_name}: CSS file not found at {css_file_path}, using default styling")
                css_applied = False
            
            # Prepare content with metadata for CSS - proper date formatting
            now = datetime.now()
            day_suffix = "th" if 4 <= now.day <= 20 or 24 <= now.day <= 30 else ["st", "nd", "rd"][now.day % 10 - 1]
            current_date = now.strftime(f'%b. {now.day}{day_suffix}, %Y - %-I:%M %p')
            
            # Format title for display (replace underscores, capitalize)
            formatted_title = self._format_title(title)
            
            # Add HTML wrapper with metadata for CSS attribute selectors
            enhanced_content = f'''<div data-title="{formatted_title}" data-date="{current_date}">

{markdown_content}

</div>'''
            
            # Add content as section
            pdf.add_section(Section(enhanced_content, toc=True))
            
            # Generate PDF
            pdf.save(str(output_path))
            
            return {
                "success": True,
                "message": f"PDF created using {self.service_name} with markdown-pdf library and external CSS",
                "css_applied": css_applied
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"markdown-pdf generation failed: {str(e)}",
                "service": self.service_name
            }
    
    def _format_title(self, title: str) -> str:
        """
        Format title by replacing underscores with spaces and capitalizing words
        
        Args:
            title: Raw title that may contain underscores
            
        Returns:
            Formatted title with proper capitalization and spacing
        """
        # Replace underscores with spaces
        formatted = title.replace('_', ' ')
        
        # Capitalize each word (title case)
        formatted = formatted.title()
        
        return formatted
    
    def _get_css_file_path(self) -> str:
        """Get the path to the external CSS file"""
        try:
            # Get the project root directory
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            css_path = os.path.join(current_dir, "config", "pdf_styles.css")
            
            print(f"🎨 {self.service_name}: Looking for CSS at {css_path}")
            return css_path
            
        except Exception as e:
            print(f"⚠️ {self.service_name}: Error locating CSS file: {e}")
            return None

    def _create_pdf_with_weasyprint(self, 
                                   markdown_content: str,
                                   output_path: str,
                                   title: str) -> Dict[str, Any]:
        """Create PDF using WeasyPrint (supports full CSS @page rules)"""
        
        try:
            import weasyprint
            import markdown
            from datetime import datetime
            
            print(f"🔧 {self.service_name}: Using WeasyPrint for PDF generation (full CSS @page support)")
            
            # Convert markdown to HTML
            md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc'])
            html_body = md.convert(markdown_content)
            
            # Get CSS content
            css_content = ""
            css_file_path = self._get_css_file_path()
            if css_file_path and os.path.exists(css_file_path):
                with open(css_file_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                print(f"🎨 {self.service_name}: Applied CSS styling from {css_file_path}")
                css_applied = True
            else:
                print(f"⚠️ {self.service_name}: CSS file not found, using default styling")
                css_applied = False
            
            # Create complete HTML document with metadata - proper date formatting
            now = datetime.now()
            day_suffix = "th" if 4 <= now.day <= 20 or 24 <= now.day <= 30 else ["st", "nd", "rd"][now.day % 10 - 1]
            current_date = now.strftime(f'%b. {now.day}{day_suffix}, %Y - %-I:%M %p')
            
            # Format title for display (replace underscores, capitalize)
            formatted_title = self._format_title(title)
            
            html_document = f"""<!DOCTYPE html>
<html lang="en" data-title="{formatted_title}" data-date="{current_date}">
<head>
    <meta charset="UTF-8">
    <title>{formatted_title}</title>
    <style>
    {css_content}
    </style>
</head>
<body>
    <h1>{formatted_title}</h1>
    {html_body}
</body>
</html>"""
            
            # Generate PDF with WeasyPrint
            html_doc = weasyprint.HTML(string=html_document)
            html_doc.write_pdf(output_path)
            
            return {
                "success": True,
                "message": f"PDF created using {self.service_name} with WeasyPrint and full CSS @page support",
                "css_applied": css_applied,
                "library": "WeasyPrint"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"WeasyPrint PDF generation failed: {str(e)}",
                "service": self.service_name
            }


# Global singleton instance - THE ONLY PDF SERVICE
_pdf_service_instance = None

def get_pdf_service() -> CentralizedPDFService:
    """
    Get the singleton PDF service instance.
    This ensures ONLY ONE PDF service exists in the entire application.
    """
    global _pdf_service_instance
    
    if _pdf_service_instance is None:
        _pdf_service_instance = CentralizedPDFService()
        print("🎯 PDF SERVICE: Singleton instance created - this is THE ONLY PDF service")
    
    return _pdf_service_instance


def create_pdf(content: str, 
               output_path: str,
               title: str = "Document",
               content_type: str = "auto") -> Dict[str, Any]:
    """
    Global function for ALL PDF creation in the codebase.
    This is the ONLY function that should be imported and used by other modules.
    
    Usage:
        from services.pdf_service import create_pdf
        result = create_pdf(content="# Hello World", output_path="/path/to/file.pdf")
    """
    service = get_pdf_service()
    return service.create_pdf(
        content=content,
        output_path=output_path,
        title=title,
        content_type=content_type
    )


# Prevent direct execution - this is a service module
if __name__ == "__main__":
    print("🚫 This is a service module - import and use create_pdf() function")
    print("   Example: from services.pdf_service import create_pdf")