"""
Universal PDF Generator - COMPLETELY DISABLED
==============================================

All PDF generation functionality has been disabled by system administrator.
"""

class UniversalPDFGenerator:
    """Universal PDF generator - COMPLETELY DISABLED"""
    
    def __init__(self):
        print("##### PDF GENERATOR INITIALIZED (DISABLED) ###")
        pass
    
    def create_pdf(self, title: str = "", content: str = "", output_path: str = "", *args, **kwargs):
        """Create PDF using CENTRALIZED PDF SERVICE"""
        print("🎯 UniversalPDFGenerator: Routing to CENTRALIZED PDF SERVICE")
        
        try:
            # Import the centralized PDF service
            from services.pdf_service import create_pdf as central_create_pdf
            
            # Route to centralized service
            result = central_create_pdf(
                content=content,
                output_path=output_path,
                title=title,
                content_type="auto"
            )
            
            return result["success"]
            
        except Exception as e:
            print(f"❌ UniversalPDFGenerator: Error routing to central service: {e}")
            return False
    
    def create_pdf_from_text(self, title: str, content: str, output_path: str, *args, **kwargs):
        """Create PDF from text using CENTRALIZED PDF SERVICE"""
        return self.create_pdf(title=title, content=content, output_path=output_path)
    
    def create_pdf_from_html(self, title: str, html_content: str, output_path: str, *args, **kwargs):
        """Create PDF from HTML using CENTRALIZED PDF SERVICE"""
        try:
            from services.pdf_service import create_pdf as central_create_pdf
            
            result = central_create_pdf(
                content=html_content,
                output_path=output_path,
                title=title,
                content_type="html"
            )
            return result["success"]
            
        except Exception as e:
            print(f"❌ create_pdf_from_html: Error: {e}")
            return False
    
    def create_pdf_from_markdown(self, title: str, markdown_content: str, output_path: str, *args, **kwargs):
        """Create PDF from markdown using CENTRALIZED PDF SERVICE"""
        try:
            from services.pdf_service import create_pdf as central_create_pdf
            
            result = central_create_pdf(
                content=markdown_content,
                output_path=output_path,
                title=title,
                content_type="markdown"
            )
            return result["success"]
            
        except Exception as e:
            print(f"❌ create_pdf_from_markdown: Error: {e}")
            return False

# Standalone functions for backwards compatibility - route to central service
def create_pdf_from_text(title: str, content: str, output_path: str):
    """Create PDF from text using CENTRALIZED PDF SERVICE"""
    try:
        from services.pdf_service import create_pdf as central_create_pdf
        result = central_create_pdf(content=content, output_path=output_path, title=title, content_type="text")
        return result["success"]
    except Exception:
        return False

def create_pdf_from_html(title: str, html_content: str, output_path: str):
    """Create PDF from HTML using CENTRALIZED PDF SERVICE"""
    try:
        from services.pdf_service import create_pdf as central_create_pdf
        result = central_create_pdf(content=html_content, output_path=output_path, title=title, content_type="html")
        return result["success"]
    except Exception:
        return False