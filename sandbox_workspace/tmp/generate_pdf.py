#!/usr/bin/env python3
"""
Auto-generated PDF converter script
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import textwrap

def create_pdf():
    try:
        # Read the text file
        with open("/home/sabawi/Development/flaskserver/sandbox_workspace/middle_east_news_analysis_2025-08-05_05-17.pdf", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Create PDF
        doc = SimpleDocTemplate("/home/sabawi/Development/flaskserver/sandbox_workspace/middle_east_news_analysis_2025-08-05_05-17.pdf", pagesize=letter,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        story = []
        
        # Add title
        title = "middle_east_news_analysis_2025-08-05_05-17".replace("_", " ").title()
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        
        for para in paragraphs:
            if para.strip():
                # Wrap long lines
                wrapped_lines = []
                for line in para.split('\n'):
                    if len(line) > 80:
                        wrapped_lines.extend(textwrap.wrap(line, width=80))
                    else:
                        wrapped_lines.append(line)
                
                para_text = ' '.join(wrapped_lines)
                story.append(Paragraph(para_text, styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        print("✅ PDF created successfully!")
        print(f"📄 Output: /home/sabawi/Development/flaskserver/sandbox_workspace/middle_east_news_analysis_2025-08-05_05-17.pdf")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Try: pip install reportlab")
        return False
    except Exception as e:
        print(f"❌ PDF creation error: {e}")
        return False

if __name__ == "__main__":
    success = create_pdf()
    exit(0 if success else 1)
