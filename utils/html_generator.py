"""
Shared HTML Generation Utility
Provides unified HTML report generation for all tools
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup  # Requires: pip install beautifulsoup4


class HTMLReportGenerator:
    """Unified HTML report generator using shared templates"""

    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.template_path = self.template_dir / "html_report_template.html"
        self._template_cache = None

    def _load_template(self) -> str:
        """Load HTML template from file with caching"""
        if self._template_cache is None:
            try:
                if not self.template_path.exists():
                    raise FileNotFoundError(f"Template not found: {self.template_path}")
                with open(self.template_path, 'r', encoding='utf-8') as f:
                    self._template_cache = f.read()
            except Exception:
                # Fallback to embedded template
                self._template_cache = self._get_fallback_template()
        return self._template_cache

    def _get_fallback_template(self) -> str:
        """Fallback template if external file fails"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>{{TITLE}}</title>
<style>
body {
  font-family: Arial, Helvetica, sans-serif;
  font-size: 14px;
  line-height: 1.4;
  color: #333;
  background-color: #f4f6f8;
  margin: 0;
  padding: 0;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
}
.container {
  max-width: 600px;
  margin: 20px auto;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 20px;
}
.header {
  background-color: #4a90e2;
  color: #fff;
  text-align: center;
  padding: 16px;
  border-radius: 4px;
}
.header h1 {
  font-size: 20px;
  margin: 0;
  line-height: 1.2;
}
.header p {
  margin: 6px 0 0;
  font-size: 13px;
  line-height: 1.3;
}
h2 {
  font-size: 16px;
  margin-top: 24px;
  margin-bottom: 8px;
  border-bottom: 2px solid #4a90e2;
  padding-bottom: 4px;
}
h3 {
  font-size: 15px;
  margin: 18px 0 6px;
}
p {
  margin: 8px 0;
  text-align: justify;
}
ul { padding-left: 18px; margin: 8px 0; }
li { margin-bottom: 6px; }
.metric {
  background-color: #f1f3f5;
  border-left: 4px solid #4a90e2;
  padding: 8px 12px;
  border-radius: 4px;
  margin: 6px 0;
}
.news-item {
  background-color: #fafafa;
  border: 1px solid #ddd;
  padding: 12px;
  border-radius: 4px;
  margin: 12px 0;
}
.recommendation {
  background-color: #28a745;
  color: white;
  padding: 14px;
  border-radius: 5px;
  text-align: center;
  font-weight: bold;
  margin: 20px 0;
}
.warning {
  background-color: #fff3cd;
  border: 1px solid #ffeeba;
  color: #856404;
  padding: 12px;
  border-radius: 4px;
  margin: 16px 0;
}
.timestamp {
  background-color: #eee;
  color: #666;
  text-align: center;
  font-size: 12px;
  font-style: italic;
  padding: 10px;
  margin-top: 20px;
  border-radius: 4px;
}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{{HEADER_TITLE}}</h1>
    <p>{{HEADER_SUBTITLE}}</p>
  </div>
  <div class="content">
    {{CONTENT}}
    {{DISCLAIMER}}
    <div class="timestamp">{{TIMESTAMP}}</div>
  </div>
</div>
</body>
</html>"""

    def _clean_html_content(self, html: str) -> str:
        """Remove <pre><code> wrappers and invalid nesting while preserving HTML entities"""
        import html as html_module
        
        soup = BeautifulSoup(html, 'html.parser')

        # Unwrap <pre> and <code>, preserve text or inner HTML
        for pre in soup.find_all("pre"):
            pre.unwrap()
        for code in soup.find_all("code"):
            code.unwrap()

        # Remove <p> wrapping block elements like <h1>-<h3>
        for tag in soup.find_all(['h1', 'h2', 'h3', 'ul', 'ol']):
            parent = tag.parent
            if parent.name == 'p':
                parent.unwrap()

        # Note: Removed aggressive HTML escaping that was breaking formatted content
        # BeautifulSoup handles entities correctly, no need to re-escape everything

        return str(soup)

    def _convert_markdown_to_html(self, markdown_text: str) -> str:
        """Convert basic markdown syntax to HTML"""
        import re

        html = markdown_text

        # Convert headers (must be done before other conversions)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Convert links [text](url) to <a href="url">text</a>
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

        # Convert bold **text** to <strong>text</strong>
        html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)

        # Convert italic *text* to <em>text</em>
        html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)

        # Convert bullet lists - → <li>
        lines = html.split('\n')
        in_list = False
        result = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- ') or stripped.startswith('* '):
                if not in_list:
                    result.append('<ul>')
                    in_list = True
                result.append(f'<li>{stripped[2:]}</li>')
            else:
                if in_list:
                    result.append('</ul>')
                    in_list = False
                result.append(line)

        if in_list:
            result.append('</ul>')

        html = '\n'.join(result)

        # Convert paragraphs (double newlines) to <p> tags
        # But don't wrap block elements
        paragraphs = html.split('\n\n')
        formatted_paras = []
        for para in paragraphs:
            para = para.strip()
            if para:
                # Check if it's already a block element
                if para.startswith(('<h1>', '<h2>', '<h3>', '<ul>', '<ol>', '<div>')):
                    formatted_paras.append(para)
                else:
                    # Regular paragraph - wrap in <p> and convert single newlines to <br>
                    para = para.replace('\n', '<br>')
                    formatted_paras.append(f'<p>{para}</p>')

        return '\n'.join(formatted_paras)

    def generate_html_report(
        self,
        content: str,
        title: str = "Report",
        header_title: str = "Analysis Report",
        header_subtitle: str = "",
        include_disclaimer: bool = True,
        custom_timestamp: Optional[str] = None
    ) -> str:
        """Generate clean HTML report using shared template"""
        try:
            template = self._load_template()

            # 🔧 FIX: Normalize special Unicode characters that cause encoding issues in email clients
            # Replace en-dash (U+2013) and em-dash (U+2014) with regular hyphen
            content = content.replace('\u2013', '-')  # en-dash → hyphen
            content = content.replace('\u2014', '-')  # em-dash → hyphen
            content = content.replace('\u2026', '...')  # ellipsis → three dots

            # 🔧 FIX: Detect and convert markdown to HTML
            # Check if content looks like markdown (has ## headers, [](links), etc.)
            has_markdown_headers = '##' in content or '###' in content
            has_markdown_links = '](' in content
            has_markdown_formatting = '**' in content or content.count('*') > 2
            has_markdown_lists = '\n- ' in content or '\n* ' in content

            is_markdown = has_markdown_headers or has_markdown_links or has_markdown_formatting or has_markdown_lists

            if is_markdown:
                # Convert markdown to HTML
                content = self._convert_markdown_to_html(content)
            elif not ('<' in content and '>' in content):
                # Plain text - convert newlines to paragraphs
                import html as html_module
                paragraphs = content.strip().split('\n\n')
                formatted_content = ""
                for para in paragraphs:
                    if para.strip():
                        # Escape HTML entities and convert single newlines to <br>
                        escaped_para = html_module.escape(para.strip())
                        escaped_para = escaped_para.replace('\n', '<br>')
                        formatted_content += f"<p>{escaped_para}</p>\n"
                content = formatted_content

            # Clean content (only for HTML content)
            content = self._clean_html_content(content)

            # Prepare disclaimer
            disclaimer = ""
            if include_disclaimer:
                disclaimer = """
                <div class="warning">
                    <strong>⚠️ Important Disclaimer:</strong>
                    This analysis is for informational purposes only and should not be considered financial advice.
                    Always consult qualified financial professionals before making investment decisions.
                </div>
                """

            # Prepare timestamp
            timestamp = custom_timestamp or f"{datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}"

            # Replace placeholders with properly escaped content
            import html as html_module
            html_document = template.replace("{{TITLE}}", html_module.escape(title, quote=True))
            html_document = html_document.replace("{{HEADER_TITLE}}", html_module.escape(header_title, quote=True))
            html_document = html_document.replace("{{HEADER_SUBTITLE}}", html_module.escape(header_subtitle, quote=True))
            html_document = html_document.replace("{{CONTENT}}", html_module.escape(content, quote=True))
            html_document = html_document.replace("{{DISCLAIMER}}", disclaimer)
            html_document = html_document.replace("{{TIMESTAMP}}", timestamp)

            return html_document

        except Exception as e:
            return f"""<!DOCTYPE html>
<html>
<head><title>{title}</title></head>
<body>
    <h1>{header_title}</h1>
    <div>{content}</div>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><em>Error in template processing: {str(e)}</em></p>
</body>
</html>"""

    def is_already_html(self, content: str) -> bool:
        """Check if content is already complete HTML"""
        content_lower = content.strip().lower()
        return content_lower.startswith('<!doctype html') or content_lower.startswith('<html>')


# Singleton instance for global use
html_generator = HTMLReportGenerator()


def create_html_report(
    content: str,
    title: str = "Report",
    header_title: str = "Analysis Report",
    header_subtitle: str = "",
    include_disclaimer: bool = True,
    custom_timestamp: Optional[str] = None
) -> str:
    """Convenience wrapper for generating HTML reports"""
    return html_generator.generate_html_report(
        content=content,
        title=title,
        header_title=header_title,
        header_subtitle=header_subtitle,
        include_disclaimer=include_disclaimer,
        custom_timestamp=custom_timestamp
    )
